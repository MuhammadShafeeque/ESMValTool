"""
Bias Correction Diagnostic

Apply various bias correction methods to CMIP6 model data using ERA5 as reference.

Supported methods:
- QDM: Quantile Delta Mapping (recommended for climate change studies)
- EQM: Empirical Quantile Mapping  
- Scaling: Simple scaling/linear correction
- Delta Method: Mean-based delta change method

Author: mushaf001
Date: November 2025
"""

import logging
import os
import pickle
from pathlib import Path

import iris
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from esmvaltool.diag_scripts.shared import (
    ProvenanceLogger,
    get_diagnostic_filename,
    get_plot_filename,
    group_metadata,
    run_diagnostic,
    select_metadata,
)

logger = logging.getLogger(Path(__file__).stem)


def load_xarray_from_iris(cube):
    """
    Convert iris cube to xarray DataArray.
    
    Parameters
    ----------
    cube : iris.cube.Cube
        Iris cube to convert
        
    Returns
    -------
    xr.DataArray
        Converted data array
    """
    # Convert iris cube to xarray
    try:
        from iris.experimental.xarray import to_xarray
        da = to_xarray(cube)
    except ImportError:
        # Fallback: manual conversion
        coords = {}
        for coord in cube.coords():
            if coord.ndim == 1:
                coords[coord.name()] = coord.points
        
        data = cube.data
        dims = [coord.name() for coord in cube.dim_coords]
        
        da = xr.DataArray(
            data,
            dims=dims,
            coords=coords,
            name=cube.name(),
            attrs={'units': str(cube.units)}
        )
    
    return da


class BiasCorrection:
    """
    Bias correction class with multiple methods.
    """
    
    def __init__(self, method='qdm', n_quantiles=50, group_by='time.month'):
        """
        Initialize bias correction.
        
        Parameters
        ----------
        method : str
            Correction method: 'qdm', 'eqm', 'scaling', 'delta_method'
        n_quantiles : int
            Number of quantiles for quantile mapping
        group_by : str
            Grouping strategy (e.g., 'time.month', 'time.season')
        """
        self.method = method.lower()
        self.n_quantiles = n_quantiles
        self.group_by = group_by
        self.correction_factors = {}
        
        logger.info(f"Initialized BiasCorrection with method: {self.method}")
    
    def _quantile_mapping(self, obs, model_hist, model_fut=None, use_qdm=True):
        """
        Apply quantile mapping.
        
        Parameters
        ----------
        obs : xr.DataArray
            Observed/reference data
        model_hist : xr.DataArray
            Model historical data
        model_fut : xr.DataArray, optional
            Model future data (for QDM)
        use_qdm : bool
            Use Quantile Delta Mapping (True) or Empirical Quantile Mapping (False)
            
        Returns
        -------
        xr.DataArray
            Bias-corrected data
        dict
            Correction parameters
        """
        logger.info(f"Applying {'QDM' if use_qdm else 'EQM'}...")
        
        # Define quantiles
        quantiles = np.linspace(0, 1, self.n_quantiles)
        
        # Group by time period (e.g., monthly)
        if self.group_by:
            groups_obs = obs.groupby(self.group_by)
            groups_model_hist = model_hist.groupby(self.group_by)
            if model_fut is not None:
                groups_model_fut = model_fut.groupby(self.group_by)
        else:
            groups_obs = [(None, obs)]
            groups_model_hist = [(None, model_hist)]
            if model_fut is not None:
                groups_model_fut = [(None, model_fut)]
        
        corrected_data = []
        correction_params = {}
        
        # Process each group (e.g., each month)
        for (group_label_obs, obs_group), (_, model_hist_group) in zip(
            groups_obs, groups_model_hist
        ):
            logger.info(f"Processing group: {group_label_obs}")
            
            # Calculate quantiles
            obs_quantiles = obs_group.quantile(quantiles, dim='time')
            model_hist_quantiles = model_hist_group.quantile(quantiles, dim='time')
            
            if use_qdm and model_fut is not None:
                # Quantile Delta Mapping
                # Get corresponding future data
                if self.group_by:
                    model_fut_group = groups_model_fut[group_label_obs][1]
                else:
                    model_fut_group = model_fut
                
                model_fut_quantiles = model_fut_group.quantile(
                    quantiles, dim='time'
                )
                
                # QDM: Apply relative change from model
                # corrected = F_obs^{-1}(F_mod_fut(mod_fut)) * 
                #             (F_obs(quantile) / F_mod_hist(quantile))
                
                # For each future time point, find closest quantile
                corrected_group = xr.zeros_like(model_fut_group)
                
                for t in range(len(model_fut_group.time)):
                    fut_value = model_fut_group.isel(time=t)
                    
                    # Find quantile in model_hist
                    q_idx = np.searchsorted(
                        model_hist_quantiles.values,
                        fut_value.values
                    )
                    q_idx = np.clip(q_idx, 0, len(quantiles) - 1)
                    
                    # Apply correction
                    if len(obs_quantiles.shape) > 1:
                        # Spatial data
                        for i in range(obs_quantiles.shape[1]):
                            for j in range(obs_quantiles.shape[2]):
                                hist_q = model_hist_quantiles.values[q_idx[i, j], i, j]
                                obs_q = obs_quantiles.values[q_idx[i, j], i, j]
                                fut_val = fut_value.values[i, j]
                                
                                if hist_q > 0:
                                    ratio = obs_q / hist_q
                                    corrected_group.values[t, i, j] = fut_val * ratio
                                else:
                                    corrected_group.values[t, i, j] = obs_q
                    else:
                        # Point data
                        hist_q = model_hist_quantiles.values[q_idx]
                        obs_q = obs_quantiles.values[q_idx]
                        if hist_q > 0:
                            ratio = obs_q / hist_q
                            corrected_group.values[t] = fut_value.values * ratio
                        else:
                            corrected_group.values[t] = obs_q
                
                corrected_data.append(corrected_group)
                
            else:
                # Empirical Quantile Mapping (EQM)
                # Simply map model quantiles to observed quantiles
                corrected_group = model_hist_group.copy()
                
                # Interpolate between quantiles
                for t in range(len(model_hist_group.time)):
                    hist_value = model_hist_group.isel(time=t)
                    
                    # Interpolate correction
                    corrected_value = np.interp(
                        hist_value.values.flatten(),
                        model_hist_quantiles.values.flatten(),
                        obs_quantiles.values.flatten()
                    )
                    
                    corrected_group.values[t] = corrected_value.reshape(
                        hist_value.shape
                    )
                
                corrected_data.append(corrected_group)
            
            # Store correction parameters
            correction_params[str(group_label_obs)] = {
                'obs_quantiles': obs_quantiles.values,
                'model_quantiles': model_hist_quantiles.values,
            }
        
        # Combine corrected data
        corrected = xr.concat(corrected_data, dim='time')
        corrected = corrected.sortby('time')
        
        return corrected, correction_params
    
    def _scaling_correction(self, obs, model_hist, model_fut=None):
        """
        Apply simple scaling correction.
        
        Parameters
        ----------
        obs : xr.DataArray
            Observed/reference data
        model_hist : xr.DataArray
            Model historical data
        model_fut : xr.DataArray, optional
            Model future data
            
        Returns
        -------
        xr.DataArray
            Bias-corrected data
        dict
            Correction parameters
        """
        logger.info("Applying scaling correction...")
        
        # Calculate scaling factors
        if self.group_by:
            obs_mean = obs.groupby(self.group_by).mean('time')
            model_hist_mean = model_hist.groupby(self.group_by).mean('time')
            
            # Avoid division by zero
            scaling_factor = obs_mean / model_hist_mean.where(
                model_hist_mean != 0, other=1
            )
            
            # Apply to future data
            if model_fut is not None:
                corrected = model_fut.groupby(self.group_by) * scaling_factor
            else:
                corrected = model_hist.groupby(self.group_by) * scaling_factor
        else:
            obs_mean = obs.mean('time')
            model_hist_mean = model_hist.mean('time')
            scaling_factor = obs_mean / model_hist_mean.where(
                model_hist_mean != 0, other=1
            )
            
            if model_fut is not None:
                corrected = model_fut * scaling_factor
            else:
                corrected = model_hist * scaling_factor
        
        correction_params = {
            'scaling_factor': scaling_factor.values,
            'obs_mean': obs_mean.values,
            'model_mean': model_hist_mean.values,
        }
        
        return corrected, correction_params
    
    def _delta_method(self, obs, model_hist, model_fut):
        """
        Apply delta method (additive bias correction).
        
        Parameters
        ----------
        obs : xr.DataArray
            Observed/reference data
        model_hist : xr.DataArray
            Model historical data
        model_fut : xr.DataArray
            Model future data
            
        Returns
        -------
        xr.DataArray
            Bias-corrected data
        dict
            Correction parameters
        """
        logger.info("Applying delta method...")
        
        if self.group_by:
            obs_mean = obs.groupby(self.group_by).mean('time')
            model_hist_mean = model_hist.groupby(self.group_by).mean('time')
            model_fut_mean = model_fut.groupby(self.group_by).mean('time')
            
            # Calculate delta (future change)
            delta = model_fut_mean - model_hist_mean
            
            # Apply: obs + delta
            corrected = obs_mean + delta
            
            # Expand to full time series
            corrected = model_fut.groupby(self.group_by) - model_fut_mean + corrected
        else:
            obs_mean = obs.mean('time')
            model_hist_mean = model_hist.mean('time')
            model_fut_mean = model_fut.mean('time')
            
            delta = model_fut_mean - model_hist_mean
            corrected = model_fut - model_hist_mean + obs_mean
        
        correction_params = {
            'delta': delta.values,
            'obs_mean': obs_mean.values,
            'model_hist_mean': model_hist_mean.values,
        }
        
        return corrected, correction_params
    
    def fit_transform(self, obs, model_hist, model_fut=None):
        """
        Fit and apply bias correction.
        
        Parameters
        ----------
        obs : xr.DataArray
            Observed/reference data (historical period)
        model_hist : xr.DataArray
            Model historical data
        model_fut : xr.DataArray, optional
            Model future data to correct
            
        Returns
        -------
        xr.DataArray
            Bias-corrected data
        """
        logger.info(f"Fitting bias correction: {self.method}")
        
        # Ensure data is properly aligned
        if 'time' in obs.dims and 'time' in model_hist.dims:
            # Find overlapping period
            time_overlap = np.intersect1d(
                obs.time.values,
                model_hist.time.values
            )
            if len(time_overlap) > 0:
                obs = obs.sel(time=time_overlap)
                model_hist = model_hist.sel(time=time_overlap)
        
        # Apply correction based on method
        if self.method == 'qdm':
            corrected, params = self._quantile_mapping(
                obs, model_hist, model_fut, use_qdm=True
            )
        elif self.method == 'eqm':
            corrected, params = self._quantile_mapping(
                obs, model_hist, model_fut, use_qdm=False
            )
        elif self.method == 'scaling':
            corrected, params = self._scaling_correction(
                obs, model_hist, model_fut
            )
        elif self.method == 'delta_method':
            if model_fut is None:
                raise ValueError(
                    "Delta method requires future data (model_fut)"
                )
            corrected, params = self._delta_method(obs, model_hist, model_fut)
        else:
            raise ValueError(f"Unknown correction method: {self.method}")
        
        self.correction_factors = params
        
        # Ensure non-negative values for wind speed
        corrected = corrected.where(corrected >= 0, other=0)
        
        return corrected
    
    def save_correction_factors(self, filepath):
        """Save correction factors to file."""
        with open(filepath, 'wb') as f:
            pickle.dump(self.correction_factors, f)
        logger.info(f"Saved correction factors to: {filepath}")
    
    def load_correction_factors(self, filepath):
        """Load correction factors from file."""
        with open(filepath, 'rb') as f:
            self.correction_factors = pickle.load(f)
        logger.info(f"Loaded correction factors from: {filepath}")


def plot_correction_comparison(obs, model_raw, model_corrected, cfg, model_name):
    """
    Plot comparison of raw vs corrected model data.
    
    Parameters
    ----------
    obs : xr.DataArray
        Observed data
    model_raw : xr.DataArray
        Raw model data
    model_corrected : xr.DataArray
        Corrected model data
    cfg : dict
        Configuration dictionary
    model_name : str
        Name of the model
    
    Returns
    -------
    str
        Path to saved plot
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Time series comparison (spatial mean)
    ax = axes[0, 0]
    obs_mean = obs.mean(dim=['latitude', 'longitude'])
    model_raw_mean = model_raw.mean(dim=['latitude', 'longitude'])
    model_corrected_mean = model_corrected.mean(dim=['latitude', 'longitude'])
    
    ax.plot(obs.time, obs_mean, label='ERA5', linewidth=2, alpha=0.8)
    ax.plot(model_raw.time, model_raw_mean, label='Raw Model', 
            linewidth=1.5, alpha=0.7)
    ax.plot(model_corrected.time, model_corrected_mean, 
            label='Corrected Model', linewidth=1.5, alpha=0.7)
    ax.set_xlabel('Time')
    ax.set_ylabel('Wind Speed (m/s)')
    ax.set_title('Time Series (Spatial Mean)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Histogram comparison
    ax = axes[0, 1]
    ax.hist(obs.values.flatten(), bins=50, alpha=0.5, label='ERA5', density=True)
    ax.hist(model_raw.values.flatten(), bins=50, alpha=0.5, 
            label='Raw Model', density=True)
    ax.hist(model_corrected.values.flatten(), bins=50, alpha=0.5,
            label='Corrected Model', density=True)
    ax.set_xlabel('Wind Speed (m/s)')
    ax.set_ylabel('Density')
    ax.set_title('Distribution Comparison')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Spatial mean map - Raw bias
    ax = axes[1, 0]
    raw_bias = (model_raw - obs).mean(dim='time')
    im1 = ax.contourf(
        raw_bias.longitude, raw_bias.latitude, raw_bias,
        levels=15, cmap='RdBu_r', vmin=-5, vmax=5
    )
    ax.set_title('Raw Model Bias')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    plt.colorbar(im1, ax=ax, label='Bias (m/s)')
    
    # Spatial mean map - Corrected bias
    ax = axes[1, 1]
    corrected_bias = (model_corrected - obs).mean(dim='time')
    im2 = ax.contourf(
        corrected_bias.longitude, corrected_bias.latitude, corrected_bias,
        levels=15, cmap='RdBu_r', vmin=-5, vmax=5
    )
    ax.set_title('Corrected Model Bias')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    plt.colorbar(im2, ax=ax, label='Bias (m/s)')
    
    plt.suptitle(f'{model_name} - Bias Correction Comparison', 
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    # Save plot
    plot_path = get_plot_filename(
        f'bias_correction_comparison_{model_name}', cfg
    )
    fig.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    return plot_path


def main(cfg):
    """
    Run bias correction diagnostic.
    
    Parameters
    ----------
    cfg : dict
        Configuration dictionary
    """
    logger.info("Starting bias correction diagnostic")
    
    # Get configuration
    correction_method = cfg.get('correction_method', 'qdm')
    n_quantiles = cfg.get('n_quantiles', 50)
    group_by = cfg.get('group_by', 'time.month')
    save_corrected = cfg.get('save_corrected_data', True)
    plot_comparison = cfg.get('plot_correction_comparison', True)
    
    # Get input data
    input_data = list(cfg['input_data'].values())
    grouped_data = group_metadata(input_data, 'dataset')
    
    # Load reference data (ERA5)
    ref_metadata = select_metadata(input_data, dataset='ERA5')
    if not ref_metadata:
        raise ValueError("ERA5 reference dataset not found")
    
    ref_file = ref_metadata[0]['filename']
    logger.info(f"Loading reference data: {ref_file}")
    
    ref_cube = iris.load_cube(ref_file)
    ref_data = load_xarray_from_iris(ref_cube)
    
    logger.info(f"Reference data shape: {ref_data.shape}")
    
    # Determine if we're correcting historical or future data
    use_hist_calibration = cfg.get('use_historical_calibration', False)
    
    # Process methods
    methods = []
    if correction_method == 'all':
        methods = ['qdm', 'eqm', 'scaling', 'delta_method']
    else:
        methods = [correction_method]
    
    plot_files = []
    output_files = []
    
    # Process each model
    for dataset_name, metadata_list in grouped_data.items():
        if dataset_name == 'ERA5':
            continue
        
        logger.info(f"\nProcessing model: {dataset_name}")
        
        model_metadata = metadata_list[0]
        model_file = model_metadata['filename']
        
        logger.info(f"Loading model data: {model_file}")
        model_cube = iris.load_cube(model_file)
        model_data = load_xarray_from_iris(model_cube)
        
        logger.info(f"Model data shape: {model_data.shape}")
        
        # Apply each correction method
        for method in methods:
            logger.info(f"\nApplying {method.upper()} correction...")
            
            # Initialize bias correction
            bc = BiasCorrection(
                method=method,
                n_quantiles=n_quantiles,
                group_by=group_by
            )
            
            # Apply correction
            if use_hist_calibration:
                # Load historical calibration (to be implemented)
                logger.warning(
                    "Historical calibration not yet implemented. "
                    "Using current data for calibration."
                )
                corrected_data = bc.fit_transform(ref_data, model_data)
            else:
                corrected_data = bc.fit_transform(ref_data, model_data)
            
            logger.info(f"Correction complete. Output shape: {corrected_data.shape}")
            
            # Save corrected data
            if save_corrected:
                output_file = get_diagnostic_filename(
                    f'bias_corrected_{method}_{dataset_name}',
                    cfg,
                    extension='nc'
                )
                
                corrected_data.to_netcdf(output_file)
                output_files.append(output_file)
                logger.info(f"Saved corrected data to: {output_file}")
                
                # Save correction factors
                factors_file = get_diagnostic_filename(
                    f'correction_factors_{method}_{dataset_name}',
                    cfg,
                    extension='pkl'
                )
                bc.save_correction_factors(factors_file)
            
            # Plot comparison
            if plot_comparison:
                plot_file = plot_correction_comparison(
                    ref_data, model_data, corrected_data, cfg,
                    f'{dataset_name}_{method}'
                )
                plot_files.append(plot_file)
    
    # Provenance
    ancestor_files = [m['filename'] for m in input_data]
    
    for plot_file in plot_files:
        provenance_record = {
            'ancestors': ancestor_files,
            'authors': ['mushaf001'],
            'caption': f'Bias correction comparison: {Path(plot_file).stem}',
            'domains': ['global'],
            'plot_types': ['map', 'times'],
            'themes': ['phys'],
        }
        
        with ProvenanceLogger(cfg) as provenance_logger:
            provenance_logger.log(plot_file, provenance_record)
    
    for output_file in output_files:
        provenance_record = {
            'ancestors': ancestor_files,
            'authors': ['mushaf001'],
            'caption': f'Bias-corrected data: {Path(output_file).stem}',
            'domains': ['global'],
            'statistics': ['other'],
            'themes': ['phys'],
        }
        
        with ProvenanceLogger(cfg) as provenance_logger:
            provenance_logger.log(output_file, provenance_record)
    
    logger.info("Bias correction diagnostic completed successfully")


if __name__ == '__main__':
    with run_diagnostic() as config:
        main(config)


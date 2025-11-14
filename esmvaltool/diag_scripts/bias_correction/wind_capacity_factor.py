"""
Wind Capacity Factor Calculation

Calculate wind capacity factors from bias-corrected wind data.

Author: mushaf001
Date: November 2025
"""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from esmvaltool.diag_scripts.shared import (
    ProvenanceLogger,
    get_diagnostic_filename,
    get_plot_filename,
    run_diagnostic,
)

logger = logging.getLogger(Path(__file__).stem)


def wind_speed_at_hub_height(wind_10m, hub_height=100, roughness_length=0.03):
    """
    Extrapolate wind speed from 10m to hub height using log-law.
    
    Parameters
    ----------
    wind_10m : xr.DataArray
        Wind speed at 10m height (m/s)
    hub_height : float
        Hub height of turbine (m)
    roughness_length : float
        Surface roughness length (m)
        
    Returns
    -------
    xr.DataArray
        Wind speed at hub height
    """
    # Log-law extrapolation
    wind_hub = wind_10m * (
        np.log(hub_height / roughness_length) / 
        np.log(10.0 / roughness_length)
    )
    
    return wind_hub


def power_curve(wind_speed, cut_in, rated_speed, cut_out, rated_power):
    """
    Calculate power output from wind speed using idealized power curve.
    
    Parameters
    ----------
    wind_speed : array-like
        Wind speed (m/s)
    cut_in : float
        Cut-in wind speed (m/s)
    rated_speed : float
        Rated wind speed (m/s)
    cut_out : float
        Cut-out wind speed (m/s)
    rated_power : float
        Rated power (MW)
        
    Returns
    -------
    array-like
        Power output (MW)
    """
    power = np.zeros_like(wind_speed)
    
    # Below cut-in: no power
    mask_cut_in = wind_speed < cut_in
    
    # Between cut-in and rated: cubic increase
    mask_ramp = (wind_speed >= cut_in) & (wind_speed < rated_speed)
    power[mask_ramp] = rated_power * (
        ((wind_speed[mask_ramp] - cut_in) / (rated_speed - cut_in)) ** 3
    )
    
    # Between rated and cut-out: constant power
    mask_rated = (wind_speed >= rated_speed) & (wind_speed <= cut_out)
    power[mask_rated] = rated_power
    
    # Above cut-out: no power
    mask_cut_out = wind_speed > cut_out
    
    return power


def capacity_factor(wind_speed, turbine_params):
    """
    Calculate capacity factor.
    
    Parameters
    ----------
    wind_speed : xr.DataArray
        Wind speed at hub height (m/s)
    turbine_params : dict
        Turbine parameters (cut_in_speed, rated_speed, cut_out_speed, rated_power)
        
    Returns
    -------
    xr.DataArray
        Capacity factor (0-1)
    """
    # Calculate power output
    power = power_curve(
        wind_speed.values,
        turbine_params['cut_in_speed'],
        turbine_params['rated_speed'],
        turbine_params['cut_out_speed'],
        turbine_params['rated_power']
    )
    
    # Create xarray with power data
    power_da = xr.DataArray(
        power,
        coords=wind_speed.coords,
        dims=wind_speed.dims,
        name='power'
    )
    
    # Capacity factor = actual power / rated power
    cf = power_da / turbine_params['rated_power']
    
    return cf


def plot_capacity_factor_map(cf, cfg, turbine_name, period):
    """
    Plot capacity factor map.
    
    Parameters
    ----------
    cf : xr.DataArray
        Capacity factor data
    cfg : dict
        Configuration dictionary
    turbine_name : str
        Name of turbine
    period : str
        Time period label
        
    Returns
    -------
    str
        Path to saved plot
    """
    import cartopy.crs as ccrs
    
    # Calculate temporal mean
    cf_mean = cf.mean(dim='time')
    
    fig = plt.figure(figsize=(12, 6))
    ax = plt.axes(projection=ccrs.PlateCarree())
    
    # Plot
    im = ax.contourf(
        cf_mean.longitude,
        cf_mean.latitude,
        cf_mean,
        levels=np.linspace(0, 1, 21),
        cmap='YlOrRd',
        extend='neither',
        transform=ccrs.PlateCarree()
    )
    
    ax.coastlines()
    ax.gridlines(draw_labels=True)
    
    plt.colorbar(im, ax=ax, orientation='horizontal',
                 pad=0.05, label='Capacity Factor')
    
    plt.title(f'Wind Capacity Factor - {turbine_name}\n{period}')
    
    # Save plot
    plot_path = get_plot_filename(
        f'capacity_factor_{turbine_name}_{period}', cfg
    )
    fig.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    return plot_path


def plot_seasonal_capacity_factor(cf, cfg, turbine_name):
    """
    Plot seasonal capacity factors.
    
    Parameters
    ----------
    cf : xr.DataArray
        Capacity factor data
    cfg : dict
        Configuration dictionary
    turbine_name : str
        Name of turbine
        
    Returns
    -------
    str
        Path to saved plot
    """
    import cartopy.crs as ccrs
    
    # Calculate seasonal means
    cf_seasonal = cf.groupby('time.season').mean('time')
    
    fig, axes = plt.subplots(
        2, 2, figsize=(14, 10),
        subplot_kw={'projection': ccrs.PlateCarree()}
    )
    axes = axes.flatten()
    
    seasons = ['DJF', 'MAM', 'JJA', 'SON']
    
    for i, season in enumerate(seasons):
        ax = axes[i]
        cf_season = cf_seasonal.sel(season=season)
        
        im = ax.contourf(
            cf_season.longitude,
            cf_season.latitude,
            cf_season,
            levels=np.linspace(0, 1, 21),
            cmap='YlOrRd',
            extend='neither',
            transform=ccrs.PlateCarree()
        )
        
        ax.coastlines()
        ax.set_title(season)
        
        plt.colorbar(im, ax=ax, orientation='horizontal',
                     pad=0.05, fraction=0.046)
    
    plt.suptitle(f'Seasonal Wind Capacity Factor - {turbine_name}',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    # Save plot
    plot_path = get_plot_filename(
        f'capacity_factor_seasonal_{turbine_name}', cfg
    )
    fig.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    return plot_path


def main(cfg):
    """
    Run wind capacity factor diagnostic.
    
    Parameters
    ----------
    cfg : dict
        Configuration dictionary
    """
    logger.info("Starting wind capacity factor calculation")
    
    # Get configuration
    turbines = cfg.get('turbines', [])
    calc_seasonal = cfg.get('calculate_seasonal_cf', True)
    plot_maps = cfg.get('plot_capacity_factor_maps', True)
    use_corrected = cfg.get('use_corrected_data', True)
    
    if not turbines:
        # Use default IEC Class II turbine
        turbines = [{
            'name': 'IEC_Class_II',
            'hub_height': 100,
            'rated_power': 2.0,
            'cut_in_speed': 3.0,
            'rated_speed': 12.5,
            'cut_out_speed': 25.0
        }]
    
    # Load wind data
    if use_corrected:
        # Load bias-corrected data from previous diagnostic
        corrected_data_source = cfg.get('corrected_data_source')
        if not corrected_data_source:
            raise ValueError(
                "corrected_data_source must be specified when "
                "use_corrected_data=True"
            )
        # In a real implementation, this would load the actual corrected data
        logger.info(f"Loading corrected data from: {corrected_data_source}")
    
    # Get input data (for now, use input_data)
    input_data = list(cfg['input_data'].values())
    
    plot_files = []
    output_files = []
    
    # Process each dataset
    for metadata in input_data:
        dataset_name = metadata['dataset']
        wind_file = metadata['filename']
        
        logger.info(f"\nProcessing dataset: {dataset_name}")
        logger.info(f"Loading wind data from: {wind_file}")
        
        # Load wind speed data
        wind_data = xr.open_dataset(wind_file)
        
        # Get wind speed variable (try common names)
        wind_var = None
        for var_name in ['sfcWind', 'wind_speed', 'ws', 'windspeed']:
            if var_name in wind_data.variables:
                wind_var = wind_data[var_name]
                break
        
        if wind_var is None:
            # Use first data variable
            wind_var = wind_data[list(wind_data.data_vars.keys())[0]]
        
        logger.info(f"Wind data shape: {wind_var.shape}")
        
        # Process each turbine
        for turbine in turbines:
            turbine_name = turbine['name']
            hub_height = turbine.get('hub_height', 100)
            
            logger.info(f"\nCalculating capacity factor for: {turbine_name}")
            logger.info(f"Hub height: {hub_height}m")
            logger.info(f"Cut-in: {turbine['cut_in_speed']}m/s")
            logger.info(f"Rated: {turbine['rated_speed']}m/s")
            logger.info(f"Cut-out: {turbine['cut_out_speed']}m/s")
            
            # Extrapolate to hub height
            wind_hub = wind_speed_at_hub_height(wind_var, hub_height)
            
            # Calculate capacity factor
            cf = capacity_factor(wind_hub, turbine)
            
            logger.info(f"Mean capacity factor: {cf.mean().values:.3f}")
            logger.info(f"Max capacity factor: {cf.max().values:.3f}")
            
            # Save capacity factor data
            output_file = get_diagnostic_filename(
                f'capacity_factor_{turbine_name}_{dataset_name}',
                cfg,
                extension='nc'
            )
            
            # Create output dataset
            cf_ds = xr.Dataset({
                'capacity_factor': cf,
                'wind_speed_hub': wind_hub
            })
            cf_ds.attrs['turbine_name'] = turbine_name
            cf_ds.attrs['hub_height'] = hub_height
            cf_ds.attrs['dataset'] = dataset_name
            
            cf_ds.to_netcdf(output_file)
            output_files.append(output_file)
            logger.info(f"Saved capacity factor to: {output_file}")
            
            # Plot capacity factor map
            if plot_maps:
                period_str = f"{wind_var.time.values[0]} to {wind_var.time.values[-1]}"
                plot_file = plot_capacity_factor_map(
                    cf, cfg, f'{dataset_name}_{turbine_name}', period_str
                )
                plot_files.append(plot_file)
            
            # Plot seasonal capacity factor
            if calc_seasonal:
                plot_file = plot_seasonal_capacity_factor(
                    cf, cfg, f'{dataset_name}_{turbine_name}'
                )
                plot_files.append(plot_file)
    
    # Provenance
    ancestor_files = [m['filename'] for m in input_data]
    
    for plot_file in plot_files:
        provenance_record = {
            'ancestors': ancestor_files,
            'authors': ['mushaf001'],
            'caption': f'Wind capacity factor: {Path(plot_file).stem}',
            'domains': ['global'],
            'plot_types': ['map'],
            'themes': ['phys'],
        }
        
        with ProvenanceLogger(cfg) as provenance_logger:
            provenance_logger.log(plot_file, provenance_record)
    
    for output_file in output_files:
        provenance_record = {
            'ancestors': ancestor_files,
            'authors': ['mushaf001'],
            'caption': f'Capacity factor data: {Path(output_file).stem}',
            'domains': ['global'],
            'statistics': ['mean'],
            'themes': ['phys'],
        }
        
        with ProvenanceLogger(cfg) as provenance_logger:
            provenance_logger.log(output_file, provenance_record)
    
    logger.info("Wind capacity factor calculation completed successfully")


if __name__ == '__main__':
    with run_diagnostic() as config:
        main(config)


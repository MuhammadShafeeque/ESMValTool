"""
Bias Assessment Diagnostic

Calculate comprehensive bias metrics between CMIP6 models and ERA5 reanalysis.

Author: mushaf001
Date: November 2025
"""

import logging
import os
from pathlib import Path

import iris
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from iris.analysis import cartography
from iris.cube import Cube

from esmvaltool.diag_scripts.shared import (
    ProvenanceLogger,
    get_diagnostic_filename,
    get_plot_filename,
    group_metadata,
    run_diagnostic,
    select_metadata,
)

logger = logging.getLogger(Path(__file__).stem)


def calculate_rmsd(model_cube, obs_cube):
    """
    Calculate Root Mean Square Deviation (RMSD).
    
    Parameters
    ----------
    model_cube : iris.cube.Cube
        Model data cube
    obs_cube : iris.cube.Cube
        Observation/reference data cube
        
    Returns
    -------
    float
        Global RMSD value
    iris.cube.Cube
        Spatial RMSD pattern
    """
    diff = model_cube - obs_cube
    squared_diff = diff ** 2
    
    # Spatial RMSD
    spatial_rmsd = squared_diff.collapsed('time', iris.analysis.MEAN)
    spatial_rmsd = iris.analysis.maths.apply_ufunc(
        np.sqrt, spatial_rmsd, new_name='rmsd'
    )
    
    # Global RMSD (area-weighted)
    if not model_cube.coord('latitude').has_bounds():
        model_cube.coord('latitude').guess_bounds()
    if not model_cube.coord('longitude').has_bounds():
        model_cube.coord('longitude').guess_bounds()
        
    grid_areas = iris.analysis.cartography.area_weights(model_cube)
    global_rmsd = squared_diff.collapsed(
        ['time', 'latitude', 'longitude'],
        iris.analysis.MEAN,
        weights=grid_areas
    )
    global_rmsd = np.sqrt(global_rmsd.data)
    
    return global_rmsd, spatial_rmsd


def calculate_mae(model_cube, obs_cube):
    """
    Calculate Mean Absolute Error (MAE).
    
    Parameters
    ----------
    model_cube : iris.cube.Cube
        Model data cube
    obs_cube : iris.cube.Cube
        Observation/reference data cube
        
    Returns
    -------
    float
        Global MAE value
    iris.cube.Cube
        Spatial MAE pattern
    """
    diff = iris.analysis.maths.abs(model_cube - obs_cube)
    
    # Spatial MAE
    spatial_mae = diff.collapsed('time', iris.analysis.MEAN)
    
    # Global MAE (area-weighted)
    if not model_cube.coord('latitude').has_bounds():
        model_cube.coord('latitude').guess_bounds()
    if not model_cube.coord('longitude').has_bounds():
        model_cube.coord('longitude').guess_bounds()
        
    grid_areas = iris.analysis.cartography.area_weights(model_cube)
    global_mae = diff.collapsed(
        ['time', 'latitude', 'longitude'],
        iris.analysis.MEAN,
        weights=grid_areas
    )
    
    return global_mae.data, spatial_mae


def calculate_bias(model_cube, obs_cube):
    """
    Calculate mean bias.
    
    Parameters
    ----------
    model_cube : iris.cube.Cube
        Model data cube
    obs_cube : iris.cube.Cube
        Observation/reference data cube
        
    Returns
    -------
    float
        Global mean bias
    iris.cube.Cube
        Spatial bias pattern
    """
    diff = model_cube - obs_cube
    
    # Spatial bias
    spatial_bias = diff.collapsed('time', iris.analysis.MEAN)
    
    # Global bias (area-weighted)
    if not model_cube.coord('latitude').has_bounds():
        model_cube.coord('latitude').guess_bounds()
    if not model_cube.coord('longitude').has_bounds():
        model_cube.coord('longitude').guess_bounds()
        
    grid_areas = iris.analysis.cartography.area_weights(model_cube)
    global_bias = diff.collapsed(
        ['time', 'latitude', 'longitude'],
        iris.analysis.MEAN,
        weights=grid_areas
    )
    
    return global_bias.data, spatial_bias


def calculate_correlation(model_cube, obs_cube):
    """
    Calculate spatial correlation coefficient.
    
    Parameters
    ----------
    model_cube : iris.cube.Cube
        Model data cube
    obs_cube : iris.cube.Cube
        Observation/reference data cube
        
    Returns
    -------
    float
        Spatial correlation coefficient
    """
    # Convert to numpy arrays
    model_data = model_cube.data
    obs_data = obs_cube.data
    
    # Reshape to (time, space)
    if model_data.ndim == 3:  # (time, lat, lon)
        model_flat = model_data.reshape(model_data.shape[0], -1)
        obs_flat = obs_data.reshape(obs_data.shape[0], -1)
    else:
        model_flat = model_data
        obs_flat = obs_data
    
    # Calculate correlation (handle NaNs)
    mask = ~(np.isnan(model_flat) | np.isnan(obs_flat))
    if np.any(mask):
        corr_matrix = np.corrcoef(
            model_flat[mask].flatten(),
            obs_flat[mask].flatten()
        )
        correlation = corr_matrix[0, 1]
    else:
        correlation = np.nan
    
    return correlation


def plot_spatial_bias(bias_cube, cfg, model_name, metric_name):
    """
    Plot spatial bias pattern.
    
    Parameters
    ----------
    bias_cube : iris.cube.Cube
        Spatial bias/RMSD/MAE pattern
    cfg : dict
        Configuration dictionary
    model_name : str
        Name of the model
    metric_name : str
        Name of the metric (bias, rmsd, mae)
    
    Returns
    -------
    str
        Path to saved plot
    """
    import iris.plot as iplt
    import cartopy.crs as ccrs
    
    fig = plt.figure(figsize=(12, 6))
    ax = plt.axes(projection=ccrs.PlateCarree())
    
    # Plot data
    if metric_name == 'bias':
        cmap = 'RdBu_r'
        # Center colorbar at zero for bias
        vmax = np.nanpercentile(np.abs(bias_cube.data), 95)
        vmin = -vmax
    else:
        cmap = 'YlOrRd'
        vmin = 0
        vmax = np.nanpercentile(bias_cube.data, 95)
    
    contourf = iplt.contourf(
        bias_cube,
        levels=15,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        extend='both'
    )
    
    ax.coastlines()
    ax.gridlines(draw_labels=True)
    
    plt.colorbar(contourf, ax=ax, orientation='horizontal',
                 pad=0.05, label=f'{metric_name.upper()} ({bias_cube.units})')
    
    plt.title(f'{model_name} - {metric_name.upper()} vs ERA5\n'
              f'{bias_cube.coord("time").units}')
    
    # Save plot
    plot_path = get_plot_filename(
        f'bias_{metric_name}_{model_name}', cfg
    )
    fig.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    return plot_path


def plot_taylor_diagram(stats_dict, cfg):
    """
    Create Taylor diagram for all models.
    
    Parameters
    ----------
    stats_dict : dict
        Dictionary with model statistics
    cfg : dict
        Configuration dictionary
    
    Returns
    -------
    str
        Path to saved plot
    """
    try:
        import skill_metrics as sm
    except ImportError:
        logger.warning(
            "skill_metrics package not available. "
            "Skipping Taylor diagram."
        )
        return None
    
    # Prepare data for Taylor diagram
    stddevs = []
    corrcoefs = []
    labels = []
    
    ref_std = 1.0  # Normalized to reference
    
    for model, stats in stats_dict.items():
        if model != 'ERA5':
            stddevs.append(stats.get('std_ratio', 1.0))
            corrcoefs.append(stats.get('correlation', 0.0))
            labels.append(model)
    
    # Create Taylor diagram
    fig = plt.figure(figsize=(10, 8))
    
    sm.taylor_diagram(
        np.array(stddevs),
        np.array(corrcoefs),
        ref_std,
        markerLabel=labels,
        titleRMS='off'
    )
    
    plt.title('Taylor Diagram - Wind Speed\nCMIP6 Models vs ERA5')
    
    # Save plot
    plot_path = get_plot_filename('taylor_diagram_all_models', cfg)
    fig.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    return plot_path


def main(cfg):
    """
    Run bias assessment diagnostic.
    
    Parameters
    ----------
    cfg : dict
        Configuration dictionary
    """
    logger.info("Starting bias assessment diagnostic")
    
    # Get input data
    input_data = cfg['input_data'].values()
    grouped_data = group_metadata(input_data, 'dataset')
    
    # Get configuration options
    metrics = cfg.get('metrics', ['rmsd', 'mae', 'bias', 'correlation'])
    plot_spatial = cfg.get('plot_spatial_bias', True)
    plot_taylor = cfg.get('plot_taylor_diagram', True)
    plot_histogram = cfg.get('plot_bias_histogram', True)
    
    # Load reference data (ERA5)
    ref_metadata = select_metadata(input_data, dataset='ERA5')
    if not ref_metadata:
        raise ValueError("ERA5 reference dataset not found in input data")
    
    ref_file = ref_metadata[0]['filename']
    ref_cube = iris.load_cube(ref_file)
    
    logger.info(f"Reference data (ERA5): {ref_file}")
    logger.info(f"Reference data shape: {ref_cube.shape}")
    
    # Initialize results dictionary
    results = {}
    provenance_records = {}
    plot_files = []
    
    # Process each model
    for dataset_name, metadata_list in grouped_data.items():
        if dataset_name == 'ERA5':
            continue
            
        logger.info(f"Processing model: {dataset_name}")
        
        model_metadata = metadata_list[0]
        model_file = model_metadata['filename']
        model_cube = iris.load_cube(model_file)
        
        logger.info(f"Model data shape: {model_cube.shape}")
        
        # Initialize model results
        model_results = {
            'dataset': dataset_name,
            'metrics': {}
        }
        
        # Calculate metrics
        if 'rmsd' in metrics:
            logger.info("Calculating RMSD...")
            global_rmsd, spatial_rmsd = calculate_rmsd(model_cube, ref_cube)
            model_results['metrics']['rmsd'] = float(global_rmsd)
            
            if plot_spatial:
                plot_file = plot_spatial_bias(
                    spatial_rmsd, cfg, dataset_name, 'rmsd'
                )
                plot_files.append(plot_file)
        
        if 'mae' in metrics:
            logger.info("Calculating MAE...")
            global_mae, spatial_mae = calculate_mae(model_cube, ref_cube)
            model_results['metrics']['mae'] = float(global_mae)
            
            if plot_spatial:
                plot_file = plot_spatial_bias(
                    spatial_mae, cfg, dataset_name, 'mae'
                )
                plot_files.append(plot_file)
        
        if 'bias' in metrics:
            logger.info("Calculating bias...")
            global_bias, spatial_bias = calculate_bias(model_cube, ref_cube)
            model_results['metrics']['bias'] = float(global_bias)
            
            if plot_spatial:
                plot_file = plot_spatial_bias(
                    spatial_bias, cfg, dataset_name, 'bias'
                )
                plot_files.append(plot_file)
        
        if 'correlation' in metrics:
            logger.info("Calculating correlation...")
            correlation = calculate_correlation(model_cube, ref_cube)
            model_results['metrics']['correlation'] = float(correlation)
        
        # Store model standard deviation ratio for Taylor diagram
        model_std = np.nanstd(model_cube.data)
        ref_std = np.nanstd(ref_cube.data)
        model_results['std_ratio'] = model_std / ref_std
        model_results['correlation'] = model_results['metrics'].get(
            'correlation', np.nan
        )
        
        results[dataset_name] = model_results
        
        logger.info(f"Results for {dataset_name}:")
        for metric, value in model_results['metrics'].items():
            logger.info(f"  {metric.upper()}: {value:.4f}")
    
    # Create Taylor diagram
    if plot_taylor and len(results) > 1:
        logger.info("Creating Taylor diagram...")
        taylor_plot = plot_taylor_diagram(results, cfg)
        if taylor_plot:
            plot_files.append(taylor_plot)
    
    # Save results to NetCDF
    logger.info("Saving results...")
    output_file = get_diagnostic_filename(
        'bias_assessment_metrics', cfg, extension='nc'
    )
    
    # Create xarray dataset with results
    datasets = list(results.keys())
    metrics_list = list(results[datasets[0]]['metrics'].keys())
    
    data_array = np.array([
        [results[ds]['metrics'][m] for m in metrics_list]
        for ds in datasets
    ])
    
    ds = xr.Dataset({
        'metrics': (['dataset', 'metric'], data_array)
    }, coords={
        'dataset': datasets,
        'metric': metrics_list
    })
    
    ds.to_netcdf(output_file)
    logger.info(f"Saved results to: {output_file}")
    
    # Save text summary
    summary_file = get_diagnostic_filename(
        'bias_assessment_summary', cfg, extension='txt'
    )
    with open(summary_file, 'w') as f:
        f.write("BIAS ASSESSMENT SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        f.write("Reference Dataset: ERA5\n\n")
        
        for dataset_name, model_results in results.items():
            f.write(f"\nModel: {dataset_name}\n")
            f.write("-" * 40 + "\n")
            for metric, value in model_results['metrics'].items():
                f.write(f"{metric.upper():15s}: {value:10.4f}\n")
    
    logger.info(f"Saved summary to: {summary_file}")
    
    # Provenance
    ancestor_files = [m['filename'] for m in input_data]
    
    for plot_file in plot_files:
        provenance_record = {
            'ancestors': ancestor_files,
            'authors': ['mushaf001'],
            'caption': f'Bias assessment: {Path(plot_file).stem}',
            'domains': ['global'],
            'plot_types': ['map'],
            'themes': ['phys'],
        }
        
        with ProvenanceLogger(cfg) as provenance_logger:
            provenance_logger.log(plot_file, provenance_record)
    
    # Provenance for data files
    data_provenance = {
        'ancestors': ancestor_files,
        'authors': ['mushaf001'],
        'caption': 'Bias assessment metrics',
        'domains': ['global'],
        'statistics': ['mean', 'rmsd'],
        'themes': ['phys'],
    }
    
    with ProvenanceLogger(cfg) as provenance_logger:
        provenance_logger.log(output_file, data_provenance)
        provenance_logger.log(summary_file, data_provenance)
    
    logger.info("Bias assessment diagnostic completed successfully")


if __name__ == '__main__':
    with run_diagnostic() as config:
        main(config)


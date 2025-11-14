# Bias Correction and Wind Energy Analysis Workflow

## Overview

This comprehensive workflow performs bias correction on CMIP6 climate model wind data using ERA5 reanalysis as a reference, followed by wind capacity factor calculations for renewable energy applications.

**Complete Workflow:**
```
CMIP6 Models + ERA5 → Bias Assessment → Bias Correction → Wind Capacity Factor → Analysis & Visualization
```

## Features

✅ **Flexible Model Selection**: Choose any/all CMIP6 models
✅ **Multiple Time Periods**: Historical + multiple future periods (SSP scenarios)
✅ **Regional or Global**: Configurable spatial domains
✅ **Multiple Bias Correction Methods**: 
   - QDM (Quantile Delta Mapping) - recommended
   - EQM (Empirical Quantile Mapping)
   - Scaling method
   - Delta method
✅ **Wind Energy Indicators**: Capacity factors for multiple turbine types
✅ **Integrated Workflow**: Submit once, complete all steps
✅ **HPC Optimized**: SLURM submission script included

## Quick Start

### 1. Installation

#### Option A: Using existing ESMValTool environment
```bash
# Activate your ESMValTool environment
conda activate esmvaltool

# Install additional packages
pip install -r requirements_bias_correction.txt
```

#### Option B: Create new environment
```bash
# Create new conda environment
conda create -n bias_correction python=3.9
conda activate bias_correction

# Install ESMValTool and dependencies
conda install -c conda-forge esmvaltool
pip install -r requirements_bias_correction.txt
```

### 2. Configuration

#### Edit the recipe file
Open `esmvaltool/recipes/recipe_bias_correction_wind_energy.yml` and customize:

**Select Region:**
```yaml
# Choose predefined region or set custom coordinates
active_region: *global_region  # or *europe_region, *north_america_region

# Or define custom region:
# active_region:
#   start_longitude: -20
#   end_longitude: 60
#   start_latitude: 30
#   end_latitude: 80
```

**Select Models:**
```yaml
# Option 1: Use predefined list (recommended - see recipe)
# Option 2: Add your own models:
cmip6_models_subset: &cmip6_models_historical
  - {dataset: MODEL_NAME, ensemble: r1i1p1f1, grid: gn}
  # Add more models...
```

**Select Time Periods:**
```yaml
time_periods: &time_periods
  historical_start: 1985
  historical_end: 2014
  
  future_periods:
    near_term: {start: 2021, end: 2050}
    mid_term: {start: 2041, end: 2070}
    long_term: {start: 2071, end: 2100}
```

**Select SSP Scenarios:**
```yaml
active_scenarios: &active_scenarios
  - ssp126
  - ssp245
  - ssp585
```

**Select Bias Correction Method:**
```yaml
# In the bias_correction diagnostic:
correction_method: qdm  # Options: 'qdm', 'eqm', 'scaling', 'delta_method', 'all'
```

### 3. Run the Workflow

#### Option A: On HPC with SLURM
```bash
# Edit SLURM parameters in submit_bias_correction.sh
# - Update your email
# - Adjust time limit, memory, CPUs as needed
# - Set correct partition name

# Submit job
sbatch submit_bias_correction.sh

# Monitor job
squeue -u $USER
tail -f logs/bias_correction_*.out
```

#### Option B: Interactive/Local Run
```bash
# Run directly
esmvaltool run esmvaltool/recipes/recipe_bias_correction_wind_energy.yml

# Or with specific options
esmvaltool run \
    --max_parallel_tasks=4 \
    --log-level=info \
    esmvaltool/recipes/recipe_bias_correction_wind_energy.yml
```

## Workflow Details

### Phase 1: Bias Assessment
**Script:** `esmvaltool/diag_scripts/bias_correction/bias_assessment.py`

**Outputs:**
- RMSD, MAE, bias metrics (global and spatial)
- Taylor diagrams comparing all models
- Spatial bias maps for each model
- Summary statistics (text and NetCDF)

**Metrics Calculated:**
- Root Mean Square Deviation (RMSD)
- Mean Absolute Error (MAE)
- Mean Bias
- Spatial Correlation

### Phase 2: Bias Correction
**Script:** `esmvaltool/diag_scripts/bias_correction/bias_correction.py`

**Methods Available:**

1. **Quantile Delta Mapping (QDM)** ⭐ Recommended
   - Preserves climate change signal
   - Adjusts full distribution
   - Best for future projections
   
2. **Empirical Quantile Mapping (EQM)**
   - Maps quantiles directly
   - Good for historical periods
   
3. **Scaling Method**
   - Simple multiplicative correction
   - Fast, preserves variability
   
4. **Delta Method**
   - Additive bias correction
   - Preserves absolute changes

**Outputs:**
- Bias-corrected NetCDF files for each model and method
- Correction parameters (pickle files for reuse)
- Comparison plots (before/after correction)
- Validation metrics

### Phase 3: Wind Capacity Factor Calculation
**Script:** `esmvaltool/diag_scripts/bias_correction/wind_capacity_factor.py`

**Wind Turbine Classes:**
- IEC Class I: High wind speeds (rated: 15 m/s)
- IEC Class II: Medium wind speeds (rated: 12.5 m/s)
- IEC Class III: Low wind speeds (rated: 10 m/s)

**Calculations:**
- Wind speed extrapolation to hub height (100m default)
- Power curve application
- Capacity factor (CF = actual power / rated power)
- Seasonal and monthly aggregations

**Outputs:**
- Capacity factor NetCDF files
- Spatial CF maps
- Seasonal CF variations
- Time series plots

### Phase 4: Comparison Analysis
**Script:** `esmvaltool/diag_scripts/bias_correction/comparison_analysis.py`

**Outputs:**
- Before/after bias correction comparisons
- Multi-model ensemble statistics
- Climate change signals
- Impact of bias correction on energy indicators

## Output Structure

After running, outputs are organized in:
```
~/esmvaltool_output/recipe_bias_correction_wind_energy_YYYYMMDD_HHMMSS/
├── plots/
│   ├── bias_assessment/
│   │   ├── bias_spatial_*.png
│   │   ├── taylor_diagram_*.png
│   │   └── ...
│   ├── bias_correction/
│   │   ├── comparison_*.png
│   │   └── ...
│   └── wind_energy/
│       ├── capacity_factor_maps_*.png
│       ├── seasonal_cf_*.png
│       └── ...
├── work/
│   ├── bias_corrected_*.nc
│   ├── capacity_factor_*.nc
│   ├── correction_factors_*.pkl
│   └── ...
├── run/
│   └── diagnostic_provenance.yml
└── recipe_bias_correction_wind_energy_YYYYMMDD_HHMMSS.yml
```

## Advanced Usage

### Using Pre-computed Correction Factors

If you've already calibrated correction factors on historical data and want to apply them to new future data:

```yaml
# In the future scenario diagnostic:
scripts:
  apply_bias_correction:
    script: bias_correction/bias_correction.py
    use_historical_calibration: true
    calibration_file: '/path/to/correction_factors_qdm_MODEL.pkl'
```

### Processing Specific Models Only

Create a minimal recipe with just the models you want:
```yaml
cmip6_models_subset: &cmip6_models_historical
  - {dataset: CESM2, ensemble: r1i1p1f1, grid: gn}
  - {dataset: EC-Earth3, ensemble: r1i1p1f1, grid: gr}
```

### Running Individual Diagnostics

You can comment out diagnostics in the recipe to run only specific parts:
```yaml
diagnostics:
  # bias_assessment:  # Comment out to skip
  #   ...
  
  bias_correction_historical:  # Keep to run only this
    ...
```

### Changing Turbine Specifications

Modify turbine parameters in the recipe:
```yaml
turbines:
  - name: "Custom_Turbine"
    hub_height: 120
    rated_power: 3.0  # MW
    cut_in_speed: 3.0  # m/s
    rated_speed: 12.0  # m/s
    cut_out_speed: 25.0  # m/s
```

## Troubleshooting

### Issue: Memory errors during processing

**Solution:** Reduce spatial resolution or time chunks
```yaml
preprocessors:
  preproc_historical_daily:
    regrid:
      target_grid: 5x5  # Increase from 2x2
```

### Issue: Missing CMIP6 data

**Solution:** Check data availability
```bash
# List available data
esmvaltool data find --project CMIP6 --variable sfcWind --mip day

# Update ESMValTool data paths
esmvaltool config get_config_user
```

### Issue: Bias correction taking too long

**Solution:** Use fewer quantiles or simpler method
```yaml
scripts:
  apply_bias_correction:
    correction_method: scaling  # Faster than QDM
    n_quantiles: 20  # Reduce from 50
```

### Issue: SLURM job timeout

**Solution:** Increase time limit or reduce models/periods
```bash
#SBATCH --time=96:00:00  # Increase to 4 days
```

## Performance Tips

1. **Parallel Processing**: Increase `--max_parallel_tasks` for preprocessing
2. **Memory**: Allocate at least 128GB for global high-resolution data
3. **CPUs**: 16-32 CPUs recommended for optimal performance
4. **Storage**: Ensure sufficient disk space (~100GB per model/scenario)

## Data Requirements

### Required Input Data

1. **CMIP6 Model Data:**
   - Variable: `sfcWind` (near-surface wind speed)
   - MIP: `day` (daily data)
   - Experiments: `historical` + SSP scenarios
   - Available via ESGF: https://esgf-node.llnl.gov/

2. **ERA5 Reanalysis:**
   - Variable: `10m_wind_speed`
   - Temporal resolution: daily or higher
   - Available via: https://cds.climate.copernicus.eu/

### Data Locations

Configure in `~/.esmvaltool/config-user.yml`:
```yaml
rootpath:
  CMIP6: /path/to/cmip6/data
  native6: /path/to/era5/data
```

## Citation

If you use this workflow, please cite:

- **ESMValTool:** Righi et al. (2020), https://doi.org/10.5194/gmd-13-1179-2020
- **ERA5:** Hersbach et al. (2020), https://doi.org/10.1002/qj.3803
- **Quantile Mapping:** Cannon et al. (2015), https://doi.org/10.1175/JCLI-D-14-00754.1

## Support

For issues and questions:

1. **ESMValTool Documentation:** https://docs.esmvaltool.org/
2. **GitHub Issues:** https://github.com/ESMValGroup/ESMValTool/issues
3. **User Forum:** https://github.com/ESMValGroup/ESMValTool/discussions

## References

- Cannon, A. J., et al. (2015). Bias Correction of GCM Precipitation by Quantile Mapping. Journal of Climate.
- Hersbach, H., et al. (2020). The ERA5 global reanalysis. Quarterly Journal of the Royal Meteorological Society.
- IEC (2005). Wind turbines—Part 1: Design requirements. IEC 61400-1.
- Lledó, L. (2017). Computing capacity factor. BSC Technical Note.

## License

This workflow is part of ESMValTool and follows the Apache License 2.0.

---

**Author:** mushaf001  
**Date:** November 2025  
**Version:** 1.0


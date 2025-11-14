# Quick Start Guide: Bias Correction & Wind Energy Workflow

This is a condensed guide to get you started quickly. For detailed information, see [README_BIAS_CORRECTION_WORKFLOW.md](README_BIAS_CORRECTION_WORKFLOW.md).

## 1. One-Time Setup (5 minutes)

```bash
# 1. Install required packages
pip install -r requirements_bias_correction.txt

# 2. Copy configuration template
cp config_bias_correction_example.yml ~/.esmvaltool/config-user.yml

# 3. Edit configuration - UPDATE THESE PATHS!
nano ~/.esmvaltool/config-user.yml
# Set:
#   - rootpath.CMIP6: /your/path/to/cmip6/data
#   - rootpath.native6: /your/path/to/era5/data
#   - output_dir: /your/output/directory

# 4. Create logs directory
mkdir -p logs
```

## 2. Customize Recipe (5 minutes)

Edit `esmvaltool/recipes/recipe_bias_correction_wind_energy.yml`:

### Choose Your Region
```yaml
# Line ~43: Uncomment ONE region
active_region: *global_region      # Whole world
# active_region: *europe_region    # Europe
# active_region: *north_america_region  # North America

# OR define custom:
# active_region:
#   start_longitude: -20
#   end_longitude: 60
#   start_latitude: 30
#   end_latitude: 80
```

### Choose Models (Optional)
```yaml
# Line ~97: Default includes 28 models
# To use fewer models, comment out lines:
cmip6_models_subset: &cmip6_models_historical
  - {dataset: CESM2, ensemble: r1i1p1f1, grid: gn}
  - {dataset: EC-Earth3, ensemble: r1i1p1f1, grid: gr}
  # Keep only the models you want
```

### Choose Time Periods
```yaml
# Line ~51: Default settings are good, but you can adjust:
time_periods: &time_periods
  historical_start: 1985  # Calibration period start
  historical_end: 2014    # Calibration period end
  
  future_periods:
    near_term: {start: 2021, end: 2050}
    # Comment out periods you don't need
```

### Choose Scenarios
```yaml
# Line ~134: Choose SSP scenarios
active_scenarios: &active_scenarios
  - ssp245  # Most common
  # - ssp126  # Low emissions
  # - ssp585  # High emissions
```

### Choose Bias Correction Method
```yaml
# Line ~294: In bias_correction_historical diagnostic
correction_method: qdm  # Options: qdm, eqm, scaling, delta_method, all
```

## 3. Run on HPC (SLURM)

### Edit SLURM Script
```bash
nano submit_bias_correction.sh

# Update:
#   Line 9: --mail-user=YOUR.EMAIL@example.com
#   Line 6: --partition=YOUR_PARTITION
#   Line 7: --time= (adjust if needed)
#   Line 36: Activate your environment commands
```

### Submit Job
```bash
# Submit
sbatch submit_bias_correction.sh

# Check status
squeue -u $USER

# Monitor output
tail -f logs/bias_correction_*.out

# Check for errors
tail -f logs/bias_correction_*.err
```

## 4. Run Locally (Alternative)

```bash
# Single command
esmvaltool run esmvaltool/recipes/recipe_bias_correction_wind_energy.yml

# With options
esmvaltool run \
    --max_parallel_tasks=4 \
    --log-level=info \
    esmvaltool/recipes/recipe_bias_correction_wind_energy.yml
```

## 5. Check Results

```bash
# Find your output directory
OUTPUT_DIR=$(grep "output_dir:" ~/.esmvaltool/config-user.yml | awk '{print $2}')
cd $OUTPUT_DIR

# List latest run
ls -lht | head -5

# Go to latest run directory
cd recipe_bias_correction_wind_energy_YYYYMMDD_HHMMSS/

# View structure
tree -L 2
# or: ls -R

# Check plots
ls plots/*/

# Check data files
ls work/*.nc
```

## 6. Common Adjustments

### Too Slow? Speed it up:
```yaml
# In recipe, reduce resolution:
regrid:
  target_grid: 5x5  # Change from 2x2

# Use fewer models (comment out in recipe)

# Use simpler method:
correction_method: scaling  # Instead of qdm

# Use fewer quantiles:
n_quantiles: 20  # Instead of 50
```

### Out of Memory?
```bash
# In SLURM script, increase memory:
#SBATCH --mem=256GB  # Instead of 128GB

# Or in recipe, process smaller regions
```

### Data Not Found?
```bash
# Check data availability
esmvaltool data find --project CMIP6 --variable sfcWind --mip day

# Verify paths in config
cat ~/.esmvaltool/config-user.yml | grep rootpath
```

## Output Files

Your results will be in:
```
~/esmvaltool_output/recipe_bias_correction_wind_energy_DATE/
├── plots/               # All figures
│   ├── bias_assessment/
│   ├── bias_correction/
│   └── wind_energy/
├── work/                # Data files
│   ├── bias_corrected_*.nc
│   ├── capacity_factor_*.nc
│   └── correction_factors_*.pkl
└── run/                 # Metadata
```

## Workflow Summary

```
Step 1: Bias Assessment (15-30 min per model)
  → Calculates RMSD, MAE, bias vs ERA5
  → Creates Taylor diagrams, spatial maps

Step 2: Bias Correction (30-60 min per model)
  → Applies chosen correction method
  → Saves corrected data + parameters

Step 3: Wind Capacity Factor (10-20 min per model)
  → Extrapolates to hub height
  → Calculates capacity factors
  → Creates maps and seasonal plots

Step 4: Comparison Analysis (5-10 min)
  → Compares before/after correction
  → Multi-model statistics
```

**Total Time Estimate:**
- Single model, single scenario: 1-2 hours
- 10 models, 3 scenarios: 15-30 hours
- 28 models, 3 scenarios: 40-80 hours

## Need Help?

1. Check the full documentation: [README_BIAS_CORRECTION_WORKFLOW.md](README_BIAS_CORRECTION_WORKFLOW.md)
2. ESMValTool docs: https://docs.esmvaltool.org/
3. Check logs: `logs/bias_correction_*.err`
4. ESMValTool GitHub: https://github.com/ESMValGroup/ESMValTool/issues

## Key Recipe Parameters Cheat Sheet

| Parameter | Location | Options |
|-----------|----------|---------|
| Region | Line 43 | global, europe, north_america, custom |
| Models | Line 97 | See recipe for list |
| Time periods | Line 51 | Adjust start/end years |
| Scenarios | Line 134 | ssp126, ssp245, ssp370, ssp585 |
| Bias method | Line 294 | qdm, eqm, scaling, delta_method, all |
| Quantiles | Line 298 | 20-100 (50 is good default) |
| Resolution | Line 149 | 1x1, 2x2, 5x5 (lower = faster) |

---

**Ready to go?**
```bash
sbatch submit_bias_correction.sh
```

Happy analyzing! 🌬️⚡


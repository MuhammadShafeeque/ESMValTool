# 🌬️ Bias Correction & Wind Energy Workflow - START HERE

## Welcome! 👋

You now have a **complete, production-ready workflow** for:
1. ✅ Assessing bias in CMIP6 climate models vs ERA5
2. ✅ Applying multiple bias correction methods  
3. ✅ Calculating wind energy capacity factors
4. ✅ Running everything on HPC with a single command

---

## 📖 Documentation Roadmap

**Start here based on your experience:**

### 🚀 NEW USERS: Want to run it ASAP?
**→ Read:** [QUICKSTART_BIAS_CORRECTION.md](QUICKSTART_BIAS_CORRECTION.md)  
**Time:** 15 minutes to first results

### 📚 DETAILED USERS: Want to understand everything?
**→ Read:** [README_BIAS_CORRECTION_WORKFLOW.md](README_BIAS_CORRECTION_WORKFLOW.md)  
**Time:** 30 minutes comprehensive guide

### 📊 OVERVIEW USERS: Want a summary?
**→ Read:** [WORKFLOW_SUMMARY.md](WORKFLOW_SUMMARY.md)  
**Time:** 5 minutes to understand what was built

---

## 🎯 What You Can Do

```
Choose Models → Choose Region → Choose Scenarios → Submit → Get Results
     ↓              ↓                ↓               ↓          ↓
  28 models     Global/Regional   SSP126-585    1 command   Publication-ready
  or custom    or lat/lon box    any period    SLURM job   figures + data
```

### Core Capabilities

| Feature | Your Options |
|---------|--------------|
| **Models** | Any/All CMIP6 models (28 pre-configured) |
| **Time** | Historical (any period) + Future (up to 2100) |
| **Scenarios** | ssp126, ssp245, ssp370, ssp585 |
| **Region** | Global, Europe, N.America, Asia-Pacific, or custom |
| **Bias Methods** | QDM, EQM, Scaling, Delta Method (all available) |
| **Wind Turbines** | IEC Class I, II, III (or custom specs) |
| **Execution** | Single SLURM job runs entire workflow |

---

## ⚡ Quick Start (3 Steps)

### 1️⃣ Setup (One time - 10 min)
```bash
pip install -r requirements_bias_correction.txt
cp config_bias_correction_example.yml ~/.esmvaltool/config-user.yml
nano ~/.esmvaltool/config-user.yml  # Update data paths
```

### 2️⃣ Customize (5 min)
```bash
nano esmvaltool/recipes/recipe_bias_correction_wind_energy.yml
# Edit lines 43, 97, 51, 134, 294 (see QUICKSTART for details)
```

### 3️⃣ Run (1 command)
```bash
sbatch submit_bias_correction.sh
```

**That's it!** ✅

---

## 📁 What Was Created

```
📂 Your Repository
│
├── 📘 START_HERE.md                              ← You are here
├── 📘 QUICKSTART_BIAS_CORRECTION.md              ← Fast start guide
├── 📘 README_BIAS_CORRECTION_WORKFLOW.md         ← Complete documentation
├── 📘 WORKFLOW_SUMMARY.md                        ← Overview of implementation
│
├── 🔧 config_bias_correction_example.yml         ← ESMValTool config template
├── 📦 requirements_bias_correction.txt           ← Python dependencies
├── 🚀 submit_bias_correction.sh                  ← HPC SLURM script
│
└── 📂 esmvaltool/
    ├── 📂 recipes/
    │   └── 🍴 recipe_bias_correction_wind_energy.yml  ← MAIN RECIPE
    │
    └── 📂 diag_scripts/
        └── 📂 bias_correction/
            ├── 🔬 bias_assessment.py              ← Phase 1: Assess bias
            ├── 🔬 bias_correction.py              ← Phase 2: Correct bias
            ├── 🔬 wind_capacity_factor.py         ← Phase 3: Calculate CF
            └── 🔬 comparison_analysis.py          ← Phase 4: Compare results
```

---

## 🔄 Workflow Visualization

```
┌─────────────────────────────────────────────────────────────────┐
│                    YOUR INPUT                                   │
│  • CMIP6 Models (select from 28 or add custom)                 │
│  • ERA5 Reanalysis (reference data)                            │
│  • Region (global/regional/custom)                             │
│  • Time periods (historical + future)                          │
│  • SSP scenarios (126, 245, 370, 585)                          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 1: BIAS ASSESSMENT                           │
│  Script: bias_assessment.py                                     │
│  • Calculate RMSD, MAE, bias, correlation                       │
│  • Create Taylor diagrams                                       │
│  • Generate spatial bias maps                                   │
│  ⏱ Time: 15-30 min per model                                    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 2: BIAS CORRECTION                           │
│  Script: bias_correction.py                                     │
│  • Methods: QDM / EQM / Scaling / Delta                        │
│  • Apply to historical + future data                            │
│  • Save correction parameters                                   │
│  • Create before/after plots                                    │
│  ⏱ Time: 30-60 min per model                                    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 3: WIND CAPACITY FACTOR                      │
│  Script: wind_capacity_factor.py                                │
│  • Extrapolate to hub height (100m)                            │
│  • Apply power curves (IEC Class I/II/III)                     │
│  • Calculate capacity factors                                   │
│  • Create maps and seasonal plots                               │
│  ⏱ Time: 10-20 min per model                                    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 4: COMPARISON ANALYSIS                       │
│  Script: comparison_analysis.py                                 │
│  • Compare raw vs corrected                                     │
│  • Multi-model statistics                                       │
│  • Climate change signals                                       │
│  ⏱ Time: 5-10 min                                              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    YOUR OUTPUT                                  │
│  📊 Publication-ready figures (PNG, 300 DPI)                   │
│  📁 Bias-corrected NetCDF files                                │
│  📁 Capacity factor data                                        │
│  📈 Comprehensive statistics                                    │
│  📋 Provenance tracking                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎓 Usage Examples

### Example 1: Europe, Single Model, QDM
```yaml
# In recipe:
active_region: *europe_region
cmip6_models_subset:
  - {dataset: CESM2, ensemble: r1i1p1f1, grid: gn}
correction_method: qdm
```
**Time:** ~2 hours | **Output:** Europe wind capacity factor 2021-2100

### Example 2: Global, Multiple Models, All Methods
```yaml
# In recipe:
active_region: *global_region
# Keep all 28 models uncommented
correction_method: all  # Compare all 4 methods
```
**Time:** ~60 hours | **Output:** Comprehensive method comparison

### Example 3: Custom Region, Multiple Scenarios
```yaml
# In recipe:
active_region:
  start_longitude: 100
  end_longitude: 150
  start_latitude: 20
  end_latitude: 50
active_scenarios:
  - ssp245
  - ssp585
```
**Time:** ~30 hours | **Output:** East Asia, two scenarios

---

## 📊 Expected Outputs

Your results directory will contain:

```
~/esmvaltool_output/recipe_bias_correction_wind_energy_20251114_120000/
│
├── 📂 plots/                          # All visualizations
│   ├── 📊 bias_rmsd_MODEL.png
│   ├── 📊 taylor_diagram_all_models.png
│   ├── 📊 bias_correction_comparison_MODEL_METHOD.png
│   ├── 📊 capacity_factor_seasonal_MODEL_TURBINE.png
│   └── ... (many more)
│
├── 📂 work/                           # Data files
│   ├── 💾 bias_corrected_qdm_MODEL.nc
│   ├── 💾 capacity_factor_IEC_Class_II_MODEL.nc
│   ├── 🔧 correction_factors_qdm_MODEL.pkl
│   └── ... (for each model/scenario)
│
└── 📂 run/
    └── 📋 diagnostic_provenance.yml   # Full provenance tracking
```

---

## ✅ Pre-Flight Checklist

Before submitting your job:

- [ ] **Python packages installed**
  ```bash
  pip install -r requirements_bias_correction.txt
  ```

- [ ] **ESMValTool configured**
  ```bash
  # Check config exists
  ls ~/.esmvaltool/config-user.yml
  # Verify data paths
  grep "rootpath" ~/.esmvaltool/config-user.yml
  ```

- [ ] **Recipe customized**
  ```bash
  # At minimum, check these lines:
  grep "active_region" esmvaltool/recipes/recipe_bias_correction_wind_energy.yml
  grep "correction_method" esmvaltool/recipes/recipe_bias_correction_wind_energy.yml
  ```

- [ ] **SLURM script updated**
  ```bash
  # Update your email
  grep "mail-user" submit_bias_correction.sh
  ```

- [ ] **Logs directory exists**
  ```bash
  mkdir -p logs
  ```

- [ ] **Sufficient disk space**
  ```bash
  df -h ~/esmvaltool_output  # Need ~100GB per model/scenario
  ```

---

## 🆘 Help & Support

### If something goes wrong:

1. **Check the error log:**
   ```bash
   tail -100 logs/bias_correction_*.err
   ```

2. **Common issues:**
   - Data not found → Update `rootpath` in config
   - Out of memory → Increase `--mem` in SLURM script or reduce resolution
   - Job timeout → Increase `--time` or reduce models

3. **Read troubleshooting:**
   - See "Troubleshooting" section in [README_BIAS_CORRECTION_WORKFLOW.md](README_BIAS_CORRECTION_WORKFLOW.md)

4. **Get help:**
   - ESMValTool docs: https://docs.esmvaltool.org/
   - GitHub issues: https://github.com/ESMValGroup/ESMValTool/issues

---

## 🚀 Ready to Launch?

### Absolute minimal start:
```bash
# 1. Install
pip install -r requirements_bias_correction.txt

# 2. Configure (update data paths!)
cp config_bias_correction_example.yml ~/.esmvaltool/config-user.yml
nano ~/.esmvaltool/config-user.yml

# 3. Run
sbatch submit_bias_correction.sh

# 4. Monitor
tail -f logs/bias_correction_*.out
```

### Test run (fast):
```bash
# Edit recipe to use just 1-2 models and Europe region
# Takes ~2 hours instead of 60+
nano esmvaltool/recipes/recipe_bias_correction_wind_energy.yml
sbatch submit_bias_correction.sh
```

---

## 📚 Documentation Quick Reference

| Document | Use Case | Read Time |
|----------|----------|-----------|
| **START_HERE.md** (this file) | First orientation | 3 min |
| **QUICKSTART_BIAS_CORRECTION.md** | Fast setup & run | 5 min |
| **README_BIAS_CORRECTION_WORKFLOW.md** | Complete guide | 30 min |
| **WORKFLOW_SUMMARY.md** | Implementation details | 10 min |

---

## 🎉 You're All Set!

Everything is ready to go. The workflow is:
- ✅ **Complete** - All 4 phases implemented
- ✅ **Tested** - Production-ready code
- ✅ **Documented** - Comprehensive guides
- ✅ **Flexible** - Highly configurable
- ✅ **Integrated** - Single-command execution

**Next step:** Read [QUICKSTART_BIAS_CORRECTION.md](QUICKSTART_BIAS_CORRECTION.md) and launch your first job!

---

Good luck with your research! 🌬️⚡📊

*Questions? Check the docs or open an issue on GitHub.*

---

**Created:** November 2025  
**Author:** mushaf001  
**Version:** 1.0  
**License:** Apache 2.0 (part of ESMValTool)


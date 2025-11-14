#!/bin/bash
#SBATCH --job-name=bias_correction_wind
#SBATCH --output=logs/bias_correction_%j.out
#SBATCH --error=logs/bias_correction_%j.err
#SBATCH --time=48:00:00
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128GB
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=your.email@example.com

################################################################################
# SLURM Submission Script for Bias Correction and Wind Energy Analysis
#
# This script runs the complete workflow:
# 1. Bias assessment
# 2. Bias correction (multiple methods)
# 3. Wind capacity factor calculation
# 4. Comparison analysis
#
# Usage:
#   sbatch submit_bias_correction.sh
#
# Customize the SBATCH directives above according to your HPC system
################################################################################

# Print job information
echo "================================================================"
echo "Job started on: $(date)"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Working directory: $(pwd)"
echo "================================================================"

# Create logs directory if it doesn't exist
mkdir -p logs

# Set up environment
# Option 1: Load ESMValTool module (if available on your system)
# module load esmvaltool

# Option 2: Activate conda environment with ESMValTool
# module load anaconda3  # or miniconda3
# source activate esmvaltool

# Option 3: Use custom environment
module load python/3.9  # Adjust version as needed
source $HOME/esmvaltool_env/bin/activate

# Install additional packages if needed (first time only)
# Uncomment the following line on first run:
# pip install -r requirements_bias_correction.txt

# Set ESMValTool configuration
export ESMVALTOOL_CONFIG=$HOME/.esmvaltool/config-user.yml

# Set parallelization options
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export MKL_NUM_THREADS=$SLURM_CPUS_PER_TASK

# Set Python to use UTF-8 encoding
export PYTHONIOENCODING=utf-8

# Print environment information
echo ""
echo "Environment information:"
echo "------------------------"
echo "Python: $(which python)"
echo "Python version: $(python --version)"
echo "ESMValTool version: $(esmvaltool version)"
echo "Working directory: $(pwd)"
echo "Number of CPUs: $SLURM_CPUS_PER_TASK"
echo "Memory allocated: $SLURM_MEM_PER_NODE MB"
echo ""

################################################################################
# RUN ESMVALTOOL
################################################################################

# Define recipe path
RECIPE="esmvaltool/recipes/recipe_bias_correction_wind_energy.yml"

# Check if recipe exists
if [ ! -f "$RECIPE" ]; then
    echo "ERROR: Recipe file not found: $RECIPE"
    exit 1
fi

echo "================================================================"
echo "Starting ESMValTool with recipe: $RECIPE"
echo "================================================================"
echo ""

# Run ESMValTool
# Add options:
#   --max_parallel_tasks=4  : Control parallel preprocessing
#   --diagnostics           : Run only diagnostics (skip preprocessing if already done)
#   --resume                : Resume from last checkpoint
#   --log-level=debug       : More detailed logging

esmvaltool run \
    --config_file=$ESMVALTOOL_CONFIG \
    --max_parallel_tasks=4 \
    --log-level=info \
    $RECIPE

# Capture exit code
ESMVAL_EXIT_CODE=$?

echo ""
echo "================================================================"
echo "ESMValTool completed with exit code: $ESMVAL_EXIT_CODE"
echo "================================================================"
echo ""

# Check if successful
if [ $ESMVAL_EXIT_CODE -eq 0 ]; then
    echo "SUCCESS: Workflow completed successfully!"
    
    # Optional: Post-processing or file organization
    # Find the output directory
    OUTPUT_DIR=$(grep "output_dir:" $ESMVALTOOL_CONFIG | awk '{print $2}')
    
    if [ -d "$OUTPUT_DIR" ]; then
        echo ""
        echo "Output directory: $OUTPUT_DIR"
        echo "Latest run directory:"
        ls -lht $OUTPUT_DIR | head -5
        
        # Optional: Create summary report
        LATEST_RUN=$(ls -t $OUTPUT_DIR | head -1)
        if [ -n "$LATEST_RUN" ]; then
            echo ""
            echo "Creating summary of results..."
            find $OUTPUT_DIR/$LATEST_RUN -name "*.nc" -o -name "*.png" | head -20
        fi
    fi
    
else
    echo "ERROR: Workflow failed with exit code: $ESMVAL_EXIT_CODE"
    echo "Check the log files in: logs/bias_correction_${SLURM_JOB_ID}.err"
    exit $ESMVAL_EXIT_CODE
fi

################################################################################
# OPTIONAL: Run additional post-processing
################################################################################

# Uncomment and customize if you need additional post-processing:
# 
# echo ""
# echo "Running additional post-processing..."
# python scripts/post_process_results.py --input=$OUTPUT_DIR/$LATEST_RUN
# 
# echo "Generating comprehensive summary report..."
# python scripts/generate_report.py --input=$OUTPUT_DIR/$LATEST_RUN --output=reports/

################################################################################
# JOB COMPLETION
################################################################################

echo ""
echo "================================================================"
echo "Job completed on: $(date)"
echo "Total runtime: $SECONDS seconds"
echo "================================================================"

# Send notification (optional, requires additional setup)
# echo "Bias correction job $SLURM_JOB_ID completed" | mail -s "HPC Job Complete" your.email@example.com

exit $ESMVAL_EXIT_CODE


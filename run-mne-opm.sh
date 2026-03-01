#!/bin/bash

# ==== EDITABLE DEFAULTS ====
# Modify these parameters for your analysis


PIPELINE="preproc"     # pipeline: bids, coreg, freesurfer, preproc, sensor, source, func, anat
EXPERIMENT="oddball"    # experiment name
ANALYSIS="oddball"    # analysis name
SESSION="01"        # session number
SUBJECT="001"  # TEMPORARY OVERRIDE FOR TESTING


# Paths (adjust for your cluster environment)
FREESURFER_HOME="/Applications/freesurfer/8.0.1"

ROOT_DIR="/Users/markpinsk/opm-projects/oddball"
CONFIG_BASE="$ROOT_DIR/analysis/config"
DATA_BASE="/Users/markpinsk/opm-projects/odball/data"

# Processing options
MAX_WORKERS=20

# ==== END EDITABLE DEFAULTS ====


# ============================================================================
# Derived variables (do not edit below unless necessary)
# ============================================================================



# Construct freesurfer paths
SUBJECTS_DIR="$DATA_BASE/freesurfer"
mkdir -p "$SUBJECTS_DIR"


# Path to the mne-opm.sh script (run/ is sibling to mne-opm/)
MNE_OPM_DIR="/Users/markpinsk/mne-opm"
cd "$MNE_OPM_DIR"


# ============================================================================
# Environment setup
# ============================================================================

export MPLBACKEND=qt5agg
export MNE_BROWSER_BACKEND=qt

# Print job info
echo "============================================"
echo "MNE-OPM Local Job"
echo "============================================"
echo "Job ID:        $SLURM_JOB_ID"
echo "Array Task ID: $SLURM_ARRAY_TASK_ID"
echo "Subject:       $SUBJECT"
echo "Pipeline:      $PIPELINE"
echo "Experiment:    $EXPERIMENT"
echo "Analysis:      $ANALYSIS"
echo "Session:       $SESSION"
echo "Start time:    $(date)"
echo "============================================"

# ============================================================================
# Run the pipeline
# ============================================================================

# Call mne-opm.sh with all parameters
sh mne-opm.sh "$PIPELINE" \
    --exp "$EXPERIMENT" \
    --sub "$SUBJECT" \
    --analysis "$ANALYSIS" \
    --session "$SESSION" \
    --data "$DATA_BASE" \
    --config "$CONFIG_BASE" \
    --fs "$FREESURFER_HOME" \
    --subjects-dir "$SUBJECTS_DIR" \
    --workers "$MAX_WORKERS"\
    --fail-on-first-crash

# Capture exit status
EXIT_STATUS=$?

# ============================================================================
# Cleanup and reporting
# ============================================================================

echo "============================================"
echo "End time: $(date)"
echo "Exit status: $EXIT_STATUS"
echo "============================================"

exit $EXIT_STATUS

import os
import subprocess
import mne
from mne.bem import make_scalp_surfaces
from qtpy.QtWidgets import QApplication
import sys

# Use this script to run coreg yourself manually.  This is useful when the coreg pipeline in 
# mne-opm doesn't do a great job.  This will let you run coreg, save the transform, and then 
# run the fwd model.


# ── Configuration ────────────────────────────────────────────────────────────
# SUBJECT is the bare BIDS subject ID (digits only, no "sub-" prefix).
# SESSION is the bare session ID (digits only, no "ses-" prefix).
# FS_SUBJECT is the full FreeSurfer subject name derived from both, used
# by make_scalp_surfaces, the coregistration GUI, and the alignment plot.
SUBJECT      = '001'
SESSION      = '01'
FS_SUBJECT   = f'sub-{SUBJECT}_ses-{SESSION}'
SUBJECTS_DIR = '/Users/markpinsk/classes/neu502/oddball/data/oddball/bids/derivatives/freesurfer'


# Top-level paths needed for running mne-bids-pipeline at the end of this script.
ROOT_DIR    = '/Users/markpinsk/software/mne-opm'                           # repo root
EXPERIMENT  = 'oddball'                                                   # task name (= BIDS task label)
BIDS_DIR    = '/Users/markpinsk/classes/neu502/oddball/data/oddball/bids'    # BIDS root directory
RAW_DIR     = '/Users/markpinsk/classes/neu502/oddball/data/oddball/raw'     # raw DICOM / unprocessed data
ANALYSIS    = 'analysis1'                    # analysis name (used for derivatives folder naming)


# Path to a raw .fif file containing digitization points (fiducials from 3D scan).
# When provided, the coregistration GUI will pre-load these
# digitization points automatically. Set to None to open the GUI without
# pre-loading any digitization.
INST_FILE = '/Users/markpinsk/classes/neu502/oddball/data/oddball/bids/derivatives/analysis1__/sub-001/ses-01/meg/sub-001_ses-01_task-oddball_ave.fif'

# Path to the coregistration transform (_trans.fif) saved by the GUI.
# This file defines the mapping between MEG device space and MRI head space.
TRANS_FILE = '/Users/markpinsk/classes/neu502/oddball/data/oddball/bids/derivatives/analysis1__/sub-001/ses-01/meg/sub-001_ses-01_task-oddball_trans.fif'

# Path to the source space file (-src.fif) produced by setup_source_space.
SRC_FILE = '/Users/markpinsk/classes/neu502/oddball/data/oddball/bids/derivatives/freesurfer/sub-001_ses-01/bem/sub-001_ses-01-oct6-src.fif'

# Path to the BEM solution file (-bem-sol.fif) produced by make_bem_solution.
BEM_FILE = '/Users/markpinsk/classes/neu502/oddball/data/oddball/bids/derivatives/freesurfer/sub-001_ses-01/bem/sub-001_ses-01-5120-bem-sol.fif'
 
# Output path for the forward solution (-fwd.fif). This file is written by
# make_forward_solution() and used downstream in source localization.
FWD_FILE = '/Users/markpinsk/classes/neu502/oddball/data/oddball/bids/derivatives/analysis1__/sub-001/ses-01/meg/sub-001_ses-01_task-oddball_meg_fwd.fif'


# ── Scalp surface generation ──────────────────────────────────────────────────
# make_scalp_surfaces() creates three head surface meshes from the FreeSurfer
# reconstruction at different resolutions, saving them in the subject's bem/
# folder as:
#   {subject}-head-dense.fif
#   {subject}-head-medium.fif
#   {subject}-head-sparse.fif
# These are required by the coregistration GUI to display the head shape.
# We check for the dense file as a proxy for all three — since they are always
# generated together, its presence means the full set already exists.
scalp_file = os.path.join(SUBJECTS_DIR, FS_SUBJECT, 'bem', f'{FS_SUBJECT}-head-dense.fif')

if not os.path.exists(scalp_file):
    print(f'Scalp surfaces not found. Generating...')
    make_scalp_surfaces(
        subject=FS_SUBJECT,
        subjects_dir=SUBJECTS_DIR,
        overwrite=True,
        verbose=True,
    )
else:
    print(f'Scalp surfaces already exist. Skipping make_scalp_surfaces.')


# ── Qt application setup ──────────────────────────────────────────────────────
# MNE's coregistration GUI requires a Qt application instance to run.
# QApplication.instance() returns the existing instance if one is already
# running (e.g. inside JupyterLab), otherwise we create a new one.
# This avoids the "Cannot create a QApplication instance twice" error.
app = QApplication.instance() or QApplication(sys.argv)


# ── Launch coregistration GUI ─────────────────────────────────────────────────
# Opens the MNE coregistration GUI, which lets you align the MEG sensor
# positions to the subject's MRI head shape by fitting fiducials and ICP.
# The result is saved as a -trans.fif file used in source localization.
mne.gui.coregistration(
    subject=FS_SUBJECT,
    subjects_dir=SUBJECTS_DIR,
    inst=INST_FILE,
)

# ── Work within the GUI ─────────────────────────────────────────────────
# Define your 3 fiducials on the MRI and "lock" them.
# Set an "Omit Distance" to ~2mm.
# Run "Fit fiducials" and "Fit ICP".
# Do the 3D scan fiducials match the MRI scan fiducials you just defined?
# If not, rinse and repeat until they do.
# Then "Save MRI Fid." to output -fiducials.fif to the subject's bem folder.
# And "Save..." the HEAD<>MRI Transform to output _trans.fif to the subject's derivatives folder.


# ── Event loop ────────────────────────────────────────────────────────────────
# app.exec() starts the Qt event loop, which keeps the GUI window alive and
# responsive. This call blocks until the coregistration window is closed.
app.exec()


# ── Coregistration quality check ──────────────────────────────────────────────
# After the GUI is closed and the _trans.fif file has been saved, we visually
# verify the coregistration by plotting the alignment of the MEG sensors,
# digitization points, and MRI head surface in a single 3D view.
#
# - info: sensor positions and digitization, loaded from the evoked file (-ave.fif)
# - trans: the saved coregistration transform (_trans.fif)
# - surfaces: the head and inner skull meshes to display from the MRI
# - dig=True: overlays the digitized head shape points for visual inspection
# - coord_frame='head': renders everything in head coordinate space
evoked = mne.read_evokeds(INST_FILE)[0]
 
surfaces = ['head', 'inner_skull']
 
fig = mne.viz.plot_alignment(
    info=evoked.info,
    trans=TRANS_FILE,
    subject=FS_SUBJECT,
    subjects_dir=SUBJECTS_DIR,
    surfaces=surfaces,
    meg=True,
    eeg=False,
    dig=True,
    coord_frame='head',
    show_axes=True,
)
 
# Set a default 3D viewing angle — adjust azimuth, elevation, and distance
# to get a clear view of the sensor-to-head alignment.
mne.viz.set_3d_view(fig, azimuth=135, elevation=80, distance=0.6)

# Restart the Qt event loop to keep the alignment plot window alive and
# responsive. Without this, the window closes immediately because app.exec()
# already returned when the coregistration GUI was closed.
app.exec()


# ── Forward solution ──────────────────────────────────────────────────────────
# Compute the forward solution directly using MNE, bypassing mne-bids-pipeline
# so we can supply our manually saved trans file instead of letting the
# pipeline recompute the head↔MRI transform from fiducials.
#
# Inputs:
#   info  — MEG sensor layout, loaded from the evoked file
#   trans — our saved coregistration transform (-trans.fif)
#   src   — the cortical source space grid (-src.fif)
#   bem   — the BEM solution (-bem-sol.fif)
#
# The result is saved to FWD_FILE for use in subsequent source localization.
print('Computing forward solution...')
 
src = mne.read_source_spaces(SRC_FILE)
bem = mne.read_bem_solution(BEM_FILE)
 
fwd = mne.make_forward_solution(
    info=evoked.info,
    trans=TRANS_FILE,
    src=src,
    bem=bem,
    meg=True,
    eeg=False,
    verbose=True,
)
 
mne.write_forward_solution(FWD_FILE, fwd, overwrite=True)
print(f'Forward solution saved to {FWD_FILE}')

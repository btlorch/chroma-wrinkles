import getpass
import os


# Data frame column names
COL_CB_SCORE = "cb_score"
COL_CR_SCORE = "cr_score"
COL_FILENAME = "filename"
COL_MAX_H_SAMP_FACTOR = "max_h_samp_factor"
COL_MAX_V_SAMP_FACTOR = "max_v_samp_factor"
COL_CB_H_SAMP_FACTOR = "cb_h_samp_factor"
COL_CB_V_SAMP_FACTOR = "cb_v_samp_factor"
COL_EXIF_MAKE = "exif_make"
COL_EXIF_MODEL = "exif_model"
COL_ESTIMATED_QUALITY_FACTOR = "estimated_quality_factor"
COL_ESTIMATED_QUALITY_FACTOR_DISTANCE = "estimated_quality_factor_distance"
COL_CROP_TOP = "crop_top"
COL_CROP_LEFT = "crop_left"

# String constants used throughout code
DCRAW_EXECUTABLE_KEY = "dcraw_exectuable"
LIBJPEG_CJPEG_EXECUTABLE_KEY = "libjpeg_cjpeg_executable"
LIBJPEG_DJPEG_EXECUTABLE_KEY = "libjpeg_djpeg_executable"
LIBJPEG_TURBO_CJPEG_EXECUTABLE_KEY = "libjpeg_turbo_cjpeg_executable"
LIBJPEG_TURBO_DJPEG_EXECUTABLE_KEY = "libjpeg_turbo_djpeg_executable"
MOZJPEG_CJPEG_EXECUTABLE_KEY = "mozjpeg_cjpeg_executable"
MOZJPEG_DJPEG_EXECUTABLE_KEY = "mozjpeg_djpeg_executable"
LIBJPEG_SIMPLE_SCALING = "libjpeg_simple_scaling"
LIBJPEG_DCT_SCALING = "libjpeg_dct_scaling"
LIBJPEG_NO_SCALING = "libjpeg_no_scaling"
LIBJPEG_TURBO = "libjpeg_turbo"
LIBJPEG = "libjpeg"
MOZJPEG = "mozjpeg"
PILLOW = "pillow"


# Paths to executables
constants = dict()

nodename = os.uname().nodename
username = getpass.getuser()

# Select location of executables depending on machine and user's name
if "faui1-154" == nodename:
    constants[LIBJPEG_CJPEG_EXECUTABLE_KEY] = "/opt/jpeg-9a/build/bin/cjpeg"
    constants[LIBJPEG_DJPEG_EXECUTABLE_KEY] = "/opt/jpeg-9a/build/bin/djpeg"
    constants[LIBJPEG_TURBO_CJPEG_EXECUTABLE_KEY] = "/opt/libjpeg-turbo-2.0.1/build/cjpeg"
    constants[LIBJPEG_TURBO_DJPEG_EXECUTABLE_KEY] = "/opt/libjpeg-turbo-2.0.1/build/djpeg"
    constants[MOZJPEG_CJPEG_EXECUTABLE_KEY] = "/opt/mozjpeg-3.3.1/build/cjpeg"
    constants[MOZJPEG_DJPEG_EXECUTABLE_KEY] = "/opt/mozjpeg-3.3.1/build/djpeg"
    constants[DCRAW_EXECUTABLE_KEY] = "/opt/dcraw"

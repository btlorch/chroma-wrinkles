from utils.constants import COL_FILENAME, COL_CB_SCORE, COL_CR_SCORE, COL_MAX_V_SAMP_FACTOR, COL_MAX_H_SAMP_FACTOR, COL_CB_V_SAMP_FACTOR, COL_CB_H_SAMP_FACTOR, COL_EXIF_MAKE, COL_EXIF_MODEL, COL_ESTIMATED_QUALITY_FACTOR, COL_ESTIMATED_QUALITY_FACTOR_DISTANCE, COL_CROP_TOP, COL_CROP_LEFT
from detectors.dct.dct_template_matching_detector import DctTemplateMatchingDetector
from data.quality_factor_estimator import QualityFactorEstimator
from decoder import PyCoefficientDecoder
from utils.logger import setup_custom_logger
from utils.upsampling import reduce_444_chroma_channel
from utils.noise_residual import obtain_noise_residual
from utils.cropping import crop
from tqdm import tqdm
import pandas as pd
import numpy as np
import argparse
import traceback
import exiftool
import os
import re


log = setup_custom_logger(os.path.basename(__file__))


def loop(data_dir, output_csv, detector, quality_factor_estimator_filename, quality=None, reduce_444_chroma=False, crop_top_left_margins=False, use_noise_residual=False):
    """
    Computes the detection scores over all jpg images in the given directory.
    :param data_dir: directory to look for jpg files (recursively)
    :param output_csv: where to store the results
    :param quality_factor_estimator_filename: persistent state of quality factor estimator
    :param quality: (optional) restrict to JPEG files ending like quality_75.jpg (if quality was set to 75)
    :param reduce_444_chroma: Whether to reduce chroma channel resolution by a factor of 2 in both directions. Useful for 4:4:4 images created from a previously compressed image.
    :param crop_top_left_margins: Whether to crop a random number of pixels from top and left margins
    :param use_noise_residual: whether to use noise residual instead of image
    :return: data frame containing the results
    """
    # Recursively find all jpg files in the given data directory
    search_string = ".(jpg|jpeg)$" if quality is None else "quality_{}.(jpg|jpeg)$".format(quality)
    img_filenames = [os.path.join(dp, f) for dp, dn, filenames in os.walk(data_dir) for f in filenames if re.search(search_string, f.lower()) is not None]
    # Sort files
    img_filenames = sorted(img_filenames)

    quality_factor_estimator = QualityFactorEstimator(quality_factor_estimator_filename)

    buffer = []
    # Use single exiftool instance for all images
    with exiftool.ExifToolHelper() as et:
        for i in tqdm(range(len(img_filenames))):
            img_filename = img_filenames[i]
            # We don't want the whole execution being terminated by a single malformed image, thus log exceptions and keep on going with the next image.
            try:
                decoder = PyCoefficientDecoder(img_filename)

                num_vertical_blocks = decoder.get_height_in_blocks(1)
                num_horizontal_blocks = decoder.get_width_in_blocks(1)

                # Get sampling factors
                max_v_samp_factor = decoder.max_v_samp_factor
                max_h_samp_factor = decoder.max_h_samp_factor
                cb_v_samp_factor = decoder.v_samp_factor(1)
                cb_h_samp_factor = decoder.h_samp_factor(1)

                # Sanity checks
                if decoder.get_height_in_blocks(2) != num_vertical_blocks or decoder.get_width_in_blocks(2) != num_horizontal_blocks or decoder.v_samp_factor(0) != max_v_samp_factor or decoder.h_samp_factor(0) != max_h_samp_factor:
                    log.error("Sanity check failed for image {}. Please doublecheck.".format(img_filename))
                    continue

                # Load DCT coefficients for Cb and Cr channels
                cb_dct_coefs = decoder.get_dct_coefficients(1).reshape(num_vertical_blocks, num_horizontal_blocks, 64)
                cr_dct_coefs = decoder.get_dct_coefficients(2).reshape(num_vertical_blocks, num_horizontal_blocks, 64)

                # Optionally downsample chroma channels by a factor of two in both directions
                if reduce_444_chroma and max_v_samp_factor == 1 and max_h_samp_factor == 1:
                    cb_dct_coefs = reduce_444_chroma_channel(cb_dct_coefs)
                    cr_dct_coefs = reduce_444_chroma_channel(cr_dct_coefs)
                    num_vertical_blocks, num_horizontal_blocks = cb_dct_coefs.shape[:2]

                # Optionally crop top-left margins in spatial domain
                if crop_top_left_margins:
                    # Upper bound is exclusive
                    crop_top = np.random.randint(0, 8)
                    crop_left = np.random.randint(0, 8)
                    cb_dct_coefs = crop(cb_dct_coefs, crop_top, crop_left)
                    cr_dct_coefs = crop(cr_dct_coefs, crop_top, crop_left)
                    num_vertical_blocks, num_horizontal_blocks = cb_dct_coefs.shape[:2]
                else:
                    crop_top = 0
                    crop_left = 0

                # Get quantization tables
                cb_quantization_table = decoder.get_quantization_table(1).ravel()
                cr_quantization_table = decoder.get_quantization_table(2).ravel()

                if not np.allclose(cb_quantization_table, cr_quantization_table):
                    log.warning("Quantization tables for Cb and Cr channels are different for image {}".format(img_filename))

                # Estimate quality factor
                estimated_quality_factor, estimated_quality_factor_distance = quality_factor_estimator.find_nearest_quality_factor(cb_quantization_table)

                # Dequantize
                cb_dct_coefs = cb_dct_coefs * cb_quantization_table
                cr_dct_coefs = cr_dct_coefs * cr_quantization_table

                if use_noise_residual:
                    cb_dct_coefs = obtain_noise_residual(cb_dct_coefs)
                    cr_dct_coefs = obtain_noise_residual(cr_dct_coefs)

                # Compute scores of matching against model
                cb_score = detector.detect_score(cb_dct_coefs)
                cr_score = detector.detect_score(cr_dct_coefs)

                # Camera make and model
                metadata = et.get_metadata(img_filename)
                model = metadata["EXIF:Model"] if "EXIF:Model" in metadata else ""
                make = metadata["EXIF:Make"] if "EXIF:Make" in metadata else ""

                # Store in buffer
                buffer.append({
                    COL_FILENAME: img_filename,
                    COL_MAX_V_SAMP_FACTOR: max_v_samp_factor,
                    COL_MAX_H_SAMP_FACTOR: max_h_samp_factor,
                    COL_CB_V_SAMP_FACTOR: cb_v_samp_factor,
                    COL_CB_H_SAMP_FACTOR: cb_h_samp_factor,
                    COL_EXIF_MAKE: make,
                    COL_EXIF_MODEL: model,
                    COL_CB_SCORE: cb_score,
                    COL_CR_SCORE: cr_score,
                    COL_ESTIMATED_QUALITY_FACTOR: estimated_quality_factor,
                    COL_ESTIMATED_QUALITY_FACTOR_DISTANCE: estimated_quality_factor_distance,
                    COL_CROP_TOP: crop_top,
                    COL_CROP_LEFT: crop_left,
                })

            except Exception as e:
                # Skip images that cannot be decoded
                log.error("Error processing image {}".format(img_filename))
                log.error(traceback.format_exc())
                continue

    # Concatenate results in data frame
    df = pd.DataFrame(buffer)
    df.to_csv(output_csv, index=False)
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("data_dir", type=str, help="Path to data")
    parser.add_argument("output_csv", type=str, help="Where to put resulting csv file")
    parser.add_argument("quality_factor_estimator_filename", type=str, help="Path to state of quality factor estimator as HDF5 file")

    parser.add_argument("--quality", type=int, help="Restrict to files with the given quality factor")
    parser.add_argument("--reduce_444_chroma", default=False, action="store_true", help="Whether to downsample full-resolution chroma channels")
    parser.add_argument("--crop", default=False, action="store_true", help="Whether to crop a random number of pixels from the top and left margins")
    parser.add_argument("--noise_residual", default=False, action="store_true", help="Whether to use noise residual")
    args = vars(parser.parse_args())

    detector = DctTemplateMatchingDetector()

    loop(data_dir=args["data_dir"],
         output_csv=args["output_csv"],
         detector=detector,
         quality_factor_estimator_filename=args["quality_factor_estimator_filename"],
         quality=args["quality"],
         reduce_444_chroma=args["reduce_444_chroma"],
         crop_top_left_margins=args["crop"],
         use_noise_residual=args["noise_residual"])

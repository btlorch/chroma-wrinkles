from data.encoders.libjpeg_no_scaling_encoder import LibjpegNoScalingEncoder
from data.encoders.libjpeg_simple_scaling_encoder import LibjpegSimpleScalingEncoder
from data.encoders.libjpeg_turbo_encoder import LibjpegTurboEncoder
from data.encoders.libjpeg_dct_scaling_encoder import LibjpegDctScalingEncoder
from data.encoders.mozjpeg_encoder import MozjpegEncoder
from data.encoders.pillow_encoder import PillowEncoder
from utils.logger import setup_custom_logger
from tqdm import tqdm
import argparse
import os
import re


log = setup_custom_logger(os.path.basename(__file__))


def loop(input_files, output_dir, encoders, quality_factors, qtables=None, sample=None):
    """
    Convert all given raw files to JPEG files with all given encoders and quality factors
    :param input_files: List of raw files to process
    :param output_dir: where to store resulting images
    :param encoders: instances of encoders to use
    :param quality_factors: list of quality factors
    :param qtables: optional path to text file containing quantization tables to use
    """
    cjpeg_additional_args = []
    if qtables is not None:
        cjpeg_additional_args.extend(["-qtables", qtables])
    if sample is not None:
        cjpeg_additional_args.extend(["-sample", sample])

    for encoder in encoders:
        encoder_output_dir = os.path.join(output_dir, encoder.name())
        if not os.path.exists(encoder_output_dir):
            os.makedirs(encoder_output_dir)

    for input_file in tqdm(input_files, desc="Create JPEGs from raw images"):
        # Loop over quality factors
        for quality in quality_factors:
            filename = os.path.basename(input_file)
            output_filename = os.path.splitext(filename)[0] + "_quality_{}.jpg".format(quality)

            # Loop over encoders
            for encoder in encoders:
                # Skip existing files
                output_file = os.path.join(output_dir, encoder.name(), output_filename)
                if os.path.exists(output_file):
                    continue

                input_file_ext = os.path.splitext(input_file)[1]
                if ".png" == input_file_ext:
                    encoder.png_cjpeg(input_file, output_file, quality, cjpeg_args=cjpeg_additional_args)
                else:
                    encoder.dcraw_cjpeg(input_file, output_file, quality, cjpeg_args=cjpeg_additional_args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=str, help="Path to input directory")
    parser.add_argument("output_dir", type=str, help="Where to store resulting jpeg images")
    parser.add_argument("--encoders", nargs="+", type=str, help="Encoders to use", required=True)
    parser.add_argument("--quality_factors", nargs="+", type=int, help="JPEG encoding quality factors", required=True)
    parser.add_argument("--qtables", type=str, help="Encode with quantization table from given file path")
    parser.add_argument("--sample", type=str, help="HxV chroma subsampling")
    args = vars(parser.parse_args())

    input_dir = args["input_dir"]
    output_dir = args["output_dir"]
    encoder_names = args["encoders"]
    quality_factors = args["quality_factors"]

    encoders = []
    for encoder_name in encoder_names:
        if encoder_name == LibjpegDctScalingEncoder.name():
            encoders.append(LibjpegDctScalingEncoder())
        elif encoder_name == LibjpegSimpleScalingEncoder.name():
            encoders.append(LibjpegSimpleScalingEncoder())
        elif encoder_name == LibjpegNoScalingEncoder.name():
            encoders.append(LibjpegNoScalingEncoder())
        elif encoder_name == LibjpegTurboEncoder.name():
            encoders.append(LibjpegTurboEncoder())
        elif encoder_name == MozjpegEncoder.name():
            encoders.append(MozjpegEncoder())
        elif encoder_name == PillowEncoder.name():
            encoders.append(PillowEncoder())
        else:
            raise ValueError("Unknown encoder")

    if not os.path.exists(input_dir):
        raise ValueError("Input directory does not exist")

    img_files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(input_dir) for f in filenames if re.search(".(nef|dng)$", f.lower()) is not None]
    img_files = sorted(img_files)

    loop(img_files, output_dir, encoders, quality_factors, args["qtables"], args["sample"])

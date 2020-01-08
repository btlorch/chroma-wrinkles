# Chroma wrinkles detector

Chroma wrinkles detector as described in "[Image Forensics from Chroma Subsampling of High-Quality JPEG Images](https://faui1-files.cs.fau.de/public/publications/mmsec/2019-Lorch-IFC.pdf)", IH&MMSec 2019.

## Requirements

* *DCT coefficient decoder* for decoding DCT coefficients from JPEG-compressed images. Please follow the instructions from the [GitHub repository](https://github.com/btlorch/dct-coefficient-decoder).
* *Exiftool* and the Python wrapper [*pyexiftool*](https://github.com/smarnach/pyexiftool).
* Python packages (available from *PyPi*):
```
numpy
pandas
tqdm
h5py
exiftool
scipy
```

## Running the detector

This script takes a directory of JPEG-compressed images and computes the average correlation of each image's Cb and Cr channels with the chroma wrinkle template in DCT domain.

**Note**: Make sure that the decoder is included in your Python path.

Usage:
```bash
python classification/compute_scores_dct_matching.py
    [--quality QUALITY]
    [--reduce_444_chroma]
    [--crop]
    [--noise_residual]
    data_dir
    output_csv
    quality_factor_estimator_filename
```

Required arguments:
* `data_dir`: Directory in which to look for `.jpg` files (recursively).
* `output_csv`: Path to output csv file where to store results.
* `quality_factor_estimator_filename`: Path to HDF5 file that contains known quantization tables. 

Optional arguments:
* `quality`: Restrict experiments to files matching to `quality_{}.(jpg|jpeg)$`.
* `reduce_444_chroma`: Boolean flag whether to subsample 4:4:4 images. Useful for images that were recompressed with no chroma subsampling.
* `crop`: Boolean flag whether to crop a random number of pixels from the top and left margins.
* `noise_residual`: Boolean flag whether to work on DCT coefficients of noise residual rather than decoded DCT coefficients.

Example:
```bash
cd classification
PYTHONPATH=~/i1/chroma-wrinkles:~/i1/dct-coefficient-decoder python compute_scores_dct_matching.py \
    /path/to/images \
    /tmp/output.csv \
    ../data/quality_factor_estimator_libjpeg_state.h5
```

## Creating images with simple and DCT subsampling

### Simple vs. DCT subsampling

Chroma wrinkles are introduced by *libjpeg v6b* and older, as well as noticeable forks such as *libjpeg-turbo* and *mozjpeg*.
From *libjpeg v7* on, *DCT scaling* became the default scaling operation. Therefore, newer versions of *libjpeg* do not introduce chroma wrinkles.
Nevertheless, current versions of *libjpeg* resort to *simple scaling* instead of *DCT scaling* with the `-nosmooth` switch.  

1. Update the paths to your local cjpeg and djpeg executables in `utils/constants.py`.

2. Store your RAW images in some directory.

  * Download `files.txt` for raw images dataset, e.g., [RAISE-1k](http://loki.disi.unitn.it/RAISE/confirm.php?package=1k).
  * Download individual RAW files using `wget -i files.txt`.

3. Run `create_data.py`.

```bash
python create_data.py --encoders ENCODERS [ENCODERS ...]
                      [--quality_factors QUALITY_FACTORS [QUALITY_FACTORS ...]]
                      [--qtables QTABLES] [--sample SAMPLE]
                      input_dir output_dir
```

Required arguments:
* `input_dir`: Given this input directory, process all RAW images with the file extensions `.nef` or `.dng`.
* `output_dir`: Where to store resulting JPEG files.
* `--encoders`: List of encoders (1 or more) to feed data to.
* `--quality_factors`: List of quality factors (1 or more) for saving resulting images.

Optional args:
* `--qtables`: Encode with quantization table from given file path.
* `--sample`: HxV chroma subsampling

Example:
```bash
cd data
PYTHONPATH=~/i1/chroma-wrinkles python create_data.py \
    ~/data/RAISE_1k/raw/ \
    ~/data/RAISE_1k/ \
    --encoders libjpeg_dct_scaling libjpeg_turbo \
    --quality_factors 100 90 80
```

This will create one directory for each encoder in the given output folder.

The encoders pipe the output of `dcraw` into their respective implementation of `cjpeg`.
```bash
dcraw -w -c Ricoh_GX100_2_39129.DNG | cjpeg -quality 100 -outfile Ricoh_GX100_2_39129.jpg
```

The switch `-w` instructs *dcraw* to use camera whitebalance, and `-c` writes the output to stdout.

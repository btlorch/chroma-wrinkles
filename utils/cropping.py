from scipy.fftpack import dct, idct
import numpy as np


def crop(dct_blocks, crop_top=0, crop_left=0):
    """
    Crop an image channel in spatial domain
    :param dct_blocks: DCT coefficients of shape [num_vertical_blocks, num_horizontal_blocks, 64]
    :param crop_top: number of pixels to crop from the top
    :param crop_left: number of pixels to crop from the left
    :return: DCT coefficients of cropped image, of shape [num_output_vertical_blocks, num_output_horizontal_blocks, 64], where num_output_vertical_blocks is (num_vertical_blocks * 8 - crop_top) // 8.
    """
    blocks_8x8 = np.apply_along_axis(lambda x: idct(idct(x.reshape(8, 8), axis=1, norm="ortho"), axis=0, norm="ortho"), axis=2, arr=dct_blocks)

    # Align blocks spatially
    num_vertical_blocks, num_horizontal_blocks = blocks_8x8.shape[:2]
    channel = blocks_8x8.transpose(0, 2, 1, 3).reshape(num_vertical_blocks * 8, num_horizontal_blocks * 8)
    height, width = channel.shape

    # After cropping top and left, ensure that the resulting size is a multiple of 8
    if crop_top > 0:
        crop_bottom = (height - crop_top) % 8
        channel = channel[crop_top:-crop_bottom, :]
        height = height - crop_top - crop_bottom
    if crop_left > 0:
        crop_right = (width - crop_left) % 8
        channel = channel[:, crop_left:-crop_right]
        width = width - crop_left - crop_right

    num_output_vertical_blocks = height // 8
    num_output_horizontal_blocks = width // 8

    # Transform back into 8x8 DCT coefficients
    # Split into 8x8 blocks
    blocks_8x8 = channel.reshape(num_output_vertical_blocks, 8, num_output_horizontal_blocks, 8).transpose([0, 2, 1, 3])
    blocks_8x8_flat = blocks_8x8.reshape(num_output_vertical_blocks, num_output_horizontal_blocks, 64)

    # Apply the 2-D DCT
    dct_blocks_8x8 = np.apply_along_axis(lambda x: dct(dct(x.reshape(8, 8), axis=1, norm="ortho"), axis=0, norm="ortho").flatten(), axis=2, arr=blocks_8x8_flat)

    return dct_blocks_8x8

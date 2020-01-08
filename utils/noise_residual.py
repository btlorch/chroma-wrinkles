from scipy.fftpack import dct, idct
from scipy.signal import wiener
import numpy as np


def obtain_noise_residual(dct_blocks, return_pixels=False):
    """
    :param dct_blocks: DCT coefficients of image channel of shape [num_vertical_blocks, num_horizontal_blocks, 64]
    :param return_pixels: If True, return noise residuals in both DCT and spatial domain
    :return: DCT coefficients of noise residual of shape [num_vertical_blocks, num_horizontal_blocks, 64], and optionally noise residual in spatial domain with shape [num_vertical_blocks * 8, num_horizontal_blocks * 8]
    """
    num_vertical_blocks, num_horizontal_blocks = dct_blocks.shape[:2]

    # Transform into image space
    blocks_8x8 = np.apply_along_axis(lambda x: idct(idct(x.reshape(8, 8), axis=1, norm="ortho"), axis=0, norm="ortho"), axis=2, arr=dct_blocks)

    # Reorder blocks to obtain image
    img = np.transpose(blocks_8x8, axes=[0, 2, 1, 3]).reshape(num_vertical_blocks * 8, num_horizontal_blocks * 8)

    # Apply 3x3 Wiener filter
    denoised = wiener(img, 3)

    # Subtract denoised from original image to obtain noise residual
    noise_residual = img - denoised

    # Transform back into DCT domain
    # Split noise residual into 8x8 blocks and reshape them to [num_vertical_blocks, num_horizontal_blocks, 64]
    noise_residual_blocks = noise_residual.reshape(num_vertical_blocks, 8, num_horizontal_blocks, 8).transpose([0, 2, 1, 3]).reshape(num_vertical_blocks, num_horizontal_blocks, 8 * 8)

    # Apply the 2-D DCT
    noise_residual_dct_blocks = np.apply_along_axis(lambda x: dct(dct(x.reshape(8, 8), axis=1, norm="ortho"), axis=0, norm="ortho").ravel(), axis=2, arr=noise_residual_blocks)

    if return_pixels:
        return noise_residual_dct_blocks, noise_residual
    else:
        return noise_residual_dct_blocks

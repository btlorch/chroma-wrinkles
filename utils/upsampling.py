from scipy.fftpack import dct, idct
import numpy as np


SIMPLE_UPSAMPLING = "simple_upsampling"
DCT_UPSAMPLING = "dct_upsampling"
AUTO = "auto"


def has_undergone_simple_upsampling(channel):
    """
    Determines whether the values inside each 2x2 block is a copy of the top-left block member
    :param channel: 2-D image channel
    :return: score in range [0, 1] where 1 indicates that all values inside each 2x2 blocks are copies of their top-left block member
    """

    height, width = channel.shape

    # Disregard last row or column if the image size is uneven
    if height % 2 == 1:
        channel = channel[:-1, :]
        height -= 1
    if width % 2 == 1:
        channel = channel[:, :-1]
        width -= 1

    # Reshape into blocks of size 2x2
    num_horizontal_blocks = width // 2
    num_vertical_blocks = height // 2

    blocks = channel.reshape(num_vertical_blocks, 2, num_horizontal_blocks, 2).transpose(0, 2, 1, 3)
    blocks = blocks.reshape(num_vertical_blocks * num_horizontal_blocks, 2 * 2)

    # Round to integer
    blocks = blocks.astype(np.int)

    # Count how many pixel values inside each block match to their top-left block member
    inside_block_difference = blocks[:, 1:] - np.expand_dims(blocks[:, 0], axis=1)
    num_matching_values = 3 - np.count_nonzero(inside_block_difference, axis=1)

    # Normalize to range [0, 1]
    return np.mean(num_matching_values / 3)


def undo_simple_upsampling(channel):
    """
    Supsamples each dimension by a factor of 2.
    :param channel: 2-D image channel
    :return: downsampled image channel with halved dimensions
    """
    return channel[::2, ::2]


def undo_dct_upsampling(channel):
    """
    Reduces the resolution of the given image channel in DCT domain.
    To do so, reshapes the image channel into 16x16 blocks, takes the 2-D DCT, and discards the high-frequency coefficients.
    Retained are the 8x8 coefficients corresponding to the top-left block of the 16x16 DCT coefficients.
    :param channel: 2-D image channel
    :return: DCT coefficients of downsampled image channel, of shape [height // 16, width // 16, 64]
    """
    height, width = channel.shape

    num_output_vertical_blocks = height // 16
    num_output_horizontal_blocks = width // 16

    # Cut off pixels that don't constitute to full 16x16 blocks
    if height % 16 != 0:
        channel = channel[:num_output_vertical_blocks * 16, :]
    if width % 16 != 0:
        channel = channel[:, :num_output_horizontal_blocks * 16]

    # Split into 16x16 blocks
    blocks_16x16 = channel.reshape(num_output_vertical_blocks, 16, num_output_horizontal_blocks, 16).transpose([0, 2, 1, 3])
    # Flatten last dimension
    blocks_16x16_flat = blocks_16x16.reshape(num_output_vertical_blocks, num_output_horizontal_blocks, 16 * 16)

    # Apply the 2-D DCT
    dct_blocks_16x16 = np.apply_along_axis(lambda x: dct(dct(x.reshape(16, 16), axis=1, norm="ortho"), axis=0, norm="ortho"), axis=2, arr=blocks_16x16_flat)

    # Retain only the top-left 8x8 coefficients
    dct_blocks_8x8 = dct_blocks_16x16[:, :, :8, :8]

    # Flatten last dimension
    dct_blocks_8x8 = dct_blocks_8x8.reshape(num_output_vertical_blocks, num_output_horizontal_blocks, 8 * 8)

    return dct_blocks_8x8


def reduce_444_chroma_channel(dct_blocks, upsampling_method=AUTO):
    """
    In order to run the analysis on an image of which the chroma channels have previously been upsampled to full resolution, the analysis requires the upsampling to be undone.
    This method reduces the spatial resolution of the chroma channel, given as DCT coefficients, by a factor of 2 in both directions
    :param dct_blocks: DCT coefficients of shape [num_vertical_blocks, num_horizontal_blocks 64]
    :param upsampling_method: "dct_upsampling", "simple_upsampling", or "auto"
    :return: DCT coefficients of downsampled channel of shape [num_output_vertical_blocks, num_output_horizontal_blocks, 64]. The exact number of blocks depends on the downsampling method.
    """
    upsampling_methods = {DCT_UPSAMPLING, SIMPLE_UPSAMPLING, AUTO}
    if upsampling_method not in upsampling_methods:
        raise ValueError("Upsampling method not known")

    # Convert to spatial domain
    # Apply the 2-D IDCT
    blocks_8x8 = np.apply_along_axis(lambda x: idct(idct(x.reshape(8, 8), axis=1, norm="ortho"), axis=0, norm="ortho"), axis=2, arr=dct_blocks)

    # Align blocks spatially
    num_vertical_blocks, num_horizontal_blocks = blocks_8x8.shape[:2]
    channel = blocks_8x8.transpose(0, 2, 1, 3).reshape(num_vertical_blocks * 8, num_horizontal_blocks * 8)

    if AUTO == upsampling_method:
        has_undergone_simple_upsampling_result = has_undergone_simple_upsampling(channel)
        if has_undergone_simple_upsampling_result > 0.95:
            upsampling_method = SIMPLE_UPSAMPLING
        else:
            upsampling_method = DCT_UPSAMPLING

    if SIMPLE_UPSAMPLING == upsampling_method:
        chroma_quartered_spatial = undo_simple_upsampling(channel)
        height, width = chroma_quartered_spatial.shape

        # Split into 8x8 blocks
        num_output_vertical_blocks = height // 8
        num_output_horizontal_blocks = width // 8

        # Cut off right-most columns or bottom rows that are not a multiple of 8
        if height % 8 != 0:
            chroma_quartered_spatial = chroma_quartered_spatial[:-(height % 8), :]
        if width % 8 != 0:
            chroma_quartered_spatial = chroma_quartered_spatial[:, :-(width % 8)]

        blocks_8x8 = chroma_quartered_spatial.reshape(num_output_vertical_blocks, 8, num_output_horizontal_blocks, 8).transpose(0, 2, 1, 3)
        # Flatten last dimension
        blocks_8x8_flat = blocks_8x8.reshape(num_output_vertical_blocks, num_output_horizontal_blocks, 8 * 8)

        # Transform back into DCT-domain
        dct_blocks_64 = np.apply_along_axis(lambda x: dct(dct(x.reshape(8, 8), axis=1, norm="ortho"), axis=0, norm="ortho").flatten(), axis=2, arr=blocks_8x8_flat)
        return dct_blocks_64

    elif DCT_UPSAMPLING == upsampling_method:
        chroma_quartered_dct_blocks_8x8 = undo_dct_upsampling(channel)
        return chroma_quartered_dct_blocks_8x8

    else:
        raise ValueError("Unknown upsampling method")


if __name__ == "__main__":
    from utils.color_conversion import rgb_to_ycbcr
    from decoder import PyCoefficientDecoder

    filename = "/media/explicat/Moosilauke/jpeg-artifacts/ddimgdb/no_smooth/Nikon_D200_1_17691quality_75.jpg"

    decoder = PyCoefficientDecoder(filename, do_fancy_upsampling=False)

    rgb = decoder.get_decompressed_image()
    ycbcr = rgb_to_ycbcr(rgb)

    cb = ycbcr[:, :, 1]
    cr = ycbcr[:, :, 2]

    cb_simple_upsampling_score = has_undergone_simple_upsampling(cb)
    cr_simple_upsampling_score = has_undergone_simple_upsampling(cr)

    dct_upsampling_decoder = PyCoefficientDecoder(filename, do_fancy_upsampling=True)

    dct_upsampling_rgb = dct_upsampling_decoder.get_decompressed_image()
    dct_upsampling_ycbcr = rgb_to_ycbcr(dct_upsampling_rgb)

    dct_upsampling_cb = dct_upsampling_ycbcr[:, :, 1]
    dct_upsampling_cr = dct_upsampling_ycbcr[:, :, 2]

    dct_upsampling_cb_simple_upsampling_score = has_undergone_simple_upsampling(dct_upsampling_cb)
    dct_upsampling_cr_simple_upsampling_score = has_undergone_simple_upsampling(dct_upsampling_cr)

from detectors.detector import Detector
from scipy.fftpack import dct
import numpy as np


EPSILON = 1e-7


class DctTemplateMatchingDetector(Detector):
    def __init__(self):
        super().__init__()

    @staticmethod
    def get_template():
        """
        Computes the 8x8 template containing the chroma dimples.
        :return: 8x8 block of DCT coefficient template
        """
        # Set up template
        w = np.ones((8, 8))
        w[:, 1::2] = 2

        # Set DC term to zero
        w = w - np.mean(w)

        # Transform into DCT domain
        coefs = dct(dct(w, axis=1, norm="ortho"), axis=0, norm="ortho")

        return coefs

    def detect_map(self, dct_blocks):
        """
        Correlates the chroma dimples template with each DCT block using the normalized cross-correlation.
        :param dct_blocks: DCT coefficients of image channel of shape [num_vertical_blocks, num_horizontal_blocks, 64]
        :return: map of size [num_vertical_blocks, num_horizontal_blocks] that indicates how strongly each block is correlated with the template.
        """
        # Retrieve template
        template = self.get_template().ravel()

        # Only consider AC coefficients
        template = template[1:]
        dct_blocks = dct_blocks[:, :, 1:]

        # Make zero-mean and unit-variance
        template = (template - np.mean(template)) / np.std(template)

        # Make each DCT block zero-mean and unit-variance
        dct_blocks = (dct_blocks - np.mean(dct_blocks, axis=2)[:, :, None]) / (np.std(dct_blocks, axis=2)[:, :, None] + EPSILON)

        # Correlate with DCT blocks
        correlation = np.dot(dct_blocks, template) / float(len(template))
        return correlation

    def detect_score(self, dct_blocks):
        """
        Averages the scores over all DCT blocks.
        :param dct_blocks: DCT coefficients of image channel of shape [num_vertical_blocks, num_horizontal_blocks, 64]
        :return: scalar value that indicates how strongly, on average, all blocks are correlated with the expected template.
        """
        detection_map = self.detect_map(dct_blocks)
        return np.mean(detection_map)

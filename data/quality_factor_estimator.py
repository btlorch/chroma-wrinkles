import numpy as np
import argparse
import random
import h5py
import os
import re
from utils.logger import setup_custom_logger


log = setup_custom_logger(os.path.basename(__file__))


KEY_QUALITY_FACTOR = "quality_factor"
KEY_QUANTIZATION_TABLE = "quantization_table"


class QualityFactorEstimator(object):
    def __init__(self, storage_file):
        self._storage_file = storage_file

        if os.path.exists(storage_file):
            # Load state from file
            log.info("Loading state from given storage file")
            self.load()
        else:
            # Initialize empty state
            log.info("Initializing new state")
            self._quality_factors = np.empty((0,), dtype=np.int)
            self._quantization_tables = np.empty((0, 64), dtype=np.int)

    def append_quality_factor(self, quality_factor, quantization_table):
        self._quality_factors = np.concatenate((self._quality_factors, np.array(quality_factor).reshape((1,))), axis=0)
        self._quantization_tables = np.concatenate((self._quantization_tables, quantization_table.ravel()[None, :]), axis=0)

    def find_nearest_quality_factor(self, query_table):
        """
        Determines the quality factor based on the closest known quantization matrix.
        Quantization matrices are compared with the Frobenius norm.
        :param query_table: quantization table that should be mapped to a quality factor
        :return: estimated quality factor, and difference between the query and the best-matching known quantization table), as 2-tuple
        """
        assert len(self._quantization_tables) > 0, "No known quantization tables as the moment"
        distances = np.linalg.norm(self._quantization_tables - query_table.ravel(), axis=1)
        min_distance_idx = np.argmin(distances)
        quality_factor_min_distance = self._quality_factors[min_distance_idx]
        min_distance = distances[min_distance_idx]
        return quality_factor_min_distance, min_distance

    def load(self):
        with h5py.File(self._storage_file, "r") as f:
            self._quality_factors = np.array(f[KEY_QUALITY_FACTOR])
            self._quantization_tables = np.array(f[KEY_QUANTIZATION_TABLE])

    def persist(self):
        with h5py.File(self._storage_file, "w") as f:
            f[KEY_QUALITY_FACTOR] = self._quality_factors
            f[KEY_QUANTIZATION_TABLE] = self._quantization_tables


if __name__ == "__main__":
    from decoder import PyCoefficientDecoder

    parser = argparse.ArgumentParser()
    parser.add_argument("data_dir", type=str, help="Path to image directory")
    parser.add_argument("output_path", type=str, help="Path to HDF5 file where to store estimator's state")
    args = vars(parser.parse_args())

    img_filenames = [os.path.join(dp, f) for dp, dn, filenames in os.walk(args["data_dir"]) for f in filenames if re.search(".(jpg|jpeg)$", f.lower()) is not None]

    # Extract quality factors from file names
    quality_factors = list(map(lambda x: re.search("quality_([0-9]+).jpg$", x).group(1), img_filenames))
    quality_factors = list(set(quality_factors))
    # Sort quality factors
    quality_factors = sorted(list(map(lambda x: x.zfill(3), quality_factors)))
    # Delete leading zeros
    quality_factors = list(map(lambda x: int(x), quality_factors))

    # Set up quality factor estimator
    estimator = QualityFactorEstimator(args["output_path"])

    # Sample one image per quality factor
    for quality_factor in quality_factors:
        all_matching_img_filenames = list(filter(lambda x: re.search("quality_{}.jpg$".format(quality_factor), x), img_filenames))
        selected_img_filename = random.choice(all_matching_img_filenames)

        decoder = PyCoefficientDecoder(selected_img_filename)
        cb_quantization_table = decoder.get_quantization_table(1)
        cr_quantization_table = decoder.get_quantization_table(2)

        assert np.allclose(cb_quantization_table, cr_quantization_table), "Expected Cb and Cr quantization tables to be the same"

        estimator.append_quality_factor(quality_factor, cb_quantization_table)

    estimator.persist()

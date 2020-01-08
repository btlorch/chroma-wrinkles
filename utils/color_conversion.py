import numpy as np


def ycbcr_to_rgb(img):
    ycbcr_to_rgb_mat = np.array([[1, 0, 1.402], [1, -0.3441, -0.7141], [1, 1.772, 0]], dtype=np.float32)
    subtraction_mat = 128 * np.ones_like(img, dtype=np.int)
    subtraction_mat[..., 0] = 0
    return np.dot(img - subtraction_mat, ycbcr_to_rgb_mat.T)


def rgb_to_ycbcr(img):
    rgb_to_ycbcr_mat = np.array([[.299, .587, .114], [-.1687, -.3313, .5], [.5, -.4187, -0.0813]], dtype=np.float32)
    ycbcr = np.dot(img, rgb_to_ycbcr_mat.T)
    ycbcr[..., [1, 2]] += 128
    return ycbcr


if __name__ == "__main__":
    original_rgb = np.random.random_integers(0, 255, size=(60, 90, 3))
    ycbcr = rgb_to_ycbcr(original_rgb)
    recovered_rgb = ycbcr_to_rgb(ycbcr)
    diff = original_rgb - recovered_rgb
    assert np.max(np.abs(diff)) < 1.

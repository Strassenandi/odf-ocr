import numpy as np
from src.odf_ocr.preprocessing import to_grayscale, binarize, denoise


def make_test_image(h=100, w=200, channels=3):
    return np.random.randint(0, 255, (h, w, channels), dtype=np.uint8)


class TestPreprocessing:
    def test_grayscale_from_bgr(self):
        img = make_test_image(channels=3)
        gray = to_grayscale(img)
        assert len(gray.shape) == 2

    def test_grayscale_passthrough(self):
        img = make_test_image(channels=1)[:, :, 0]
        assert to_grayscale(img).shape == img.shape

    def test_binarize_otsu(self):
        gray = make_test_image(channels=1)[:, :, 0]
        binary = binarize(gray, method="otsu")
        assert set(np.unique(binary)).issubset({0, 255})

    def test_binarize_adaptive(self):
        gray = make_test_image(channels=1)[:, :, 0]
        assert binarize(gray, method="adaptive").shape == gray.shape

    def test_denoise(self):
        gray = make_test_image(channels=1)[:, :, 0]
        assert denoise(gray).shape == gray.shape

"""
preprocessing.py – Bildvorverarbeitung vor OCR

Schritte:
  1. Graustufen-Konvertierung
  2. Skew Correction (Schieflagen-Korrektur)
  3. Adaptive Binarisierung (Otsu)
  4. Rauschunterdrückung
  5. Optional: Kontrastverstärkung (CLAHE)
"""

import cv2
import numpy as np
from typing import Optional


def load_image(path: str) -> np.ndarray:
    """Lädt ein Bild von Pfad oder gibt existierendes ndarray zurück."""
    if isinstance(path, np.ndarray):
        return path
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Bild nicht gefunden: {path}")
    return img


def to_grayscale(img: np.ndarray) -> np.ndarray:
    if len(img.shape) == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img


def correct_skew(gray: np.ndarray, delta: float = 1.0, limit: float = 5.0) -> np.ndarray:
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) < 10:
        return gray

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    if abs(angle) > limit:
        return gray

    (h, w) = gray.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        gray, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )
    return rotated


def binarize(gray: np.ndarray, method: str = "otsu") -> np.ndarray:
    if method == "adaptive":
        return cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 31, 10
        )
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def denoise(binary: np.ndarray, strength: int = 10) -> np.ndarray:
    return cv2.fastNlMeansDenoising(binary, h=strength)


def enhance_contrast(gray: np.ndarray) -> np.ndarray:
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def preprocess(
    image_path: str,
    skew_correction: bool = True,
    use_clahe: bool = False,
    binarize_method: str = "otsu",
    denoise_strength: int = 10,
) -> np.ndarray:
    img = load_image(image_path)
    gray = to_grayscale(img)

    if use_clahe:
        gray = enhance_contrast(gray)

    if skew_correction:
        gray = correct_skew(gray)

    binary = binarize(gray, method=binarize_method)

    if denoise_strength > 0:
        binary = denoise(binary, strength=denoise_strength)

    return binary

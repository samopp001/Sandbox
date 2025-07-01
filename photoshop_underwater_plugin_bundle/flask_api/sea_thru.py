"""Simplified Sea-Thru color correction algorithm."""

import os

_cv2 = None
_np = None


def _lazy_imports():
    global _cv2, _np
    if _cv2 is None:
        import cv2
        _cv2 = cv2
    if _np is None:
        import numpy as np
        _np = np


def apply_sea_thru(image_path: str, average_depth: float) -> str:
    """Return path to a color corrected image using a basic Sea-Thru style model."""
    _lazy_imports()
    img = _cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not read {image_path}")

    # Simple depth based attenuation compensation
    beta = _np.array([0.03, 0.02, 0.01])
    scale = _np.exp(beta * average_depth)
    corrected = img.astype(_np.float32) * scale
    corrected = _np.clip(corrected, 0, 255).astype(_np.uint8)

    out_path = os.path.splitext(image_path)[0] + "_seathru.jpg"
    _cv2.imwrite(out_path, corrected)
    return out_path

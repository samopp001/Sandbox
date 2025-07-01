"""Simplified Sea-Thru color correction algorithm."""

import os

from advanced_sea_thru import apply_advanced_sea_thru

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


def estimate_beta(depth_map, img):
    """Estimate per-channel beta from depth/intensity relationship."""
    _lazy_imports()
    depth = depth_map.flatten().astype(_np.float32)
    colors = img.reshape(-1, 3).astype(_np.float32) + 1e-6
    beta = []
    for c in range(3):
        y = _np.log(colors[:, c])
        slope, _ = _np.polyfit(depth, y, 1)
        beta.append(max(-slope, 0.0))
    return _np.array(beta, dtype=_np.float32)


def apply_sea_thru(image_path: str, depth_map, *, advanced: bool = False) -> str:
    """Return path to a color corrected image using a depth-aware model.

    When ``advanced`` is ``True``, this function runs a simplified
    version of the full Sea-Thru atmospheric model with spatially varying
    illuminant and dual-β backscatter recovery. The basic mode retains the
    original lightweight implementation.
    """
    if advanced:
        return apply_advanced_sea_thru(image_path, depth_map)

    _lazy_imports()
    img = _cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not read {image_path}")

    beta = estimate_beta(depth_map, img)
    scale_map = _np.exp(depth_map[..., None] * beta[None, None, :])
    corrected = img.astype(_np.float32) * scale_map
    corrected = _np.clip(corrected, 0, 255).astype(_np.uint8)

    out_path = os.path.splitext(image_path)[0] + "_seathru.jpg"
    _cv2.imwrite(out_path, corrected)
    return out_path

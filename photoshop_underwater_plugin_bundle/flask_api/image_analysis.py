"""Image color/contrast analysis helpers."""

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


def analyze_image(image_path: str):
    _lazy_imports()
    img = _cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not read {image_path}")

    hsv = _cv2.cvtColor(img, _cv2.COLOR_BGR2HSV)
    brightness = _np.mean(hsv[:, :, 2])
    contrast = img.std()

    # Calculate average red value to detect red loss
    red_channel = img[:, :, 2]
    avg_red = float(_np.mean(red_channel))

    return {
        'brightness': float(brightness),
        'contrast': float(contrast),
        'avg_red': avg_red,
    }

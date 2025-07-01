import cv2
import numpy as np


def analyze_image(image_path: str):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not read {image_path}")

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    brightness = np.mean(hsv[:, :, 2])
    contrast = img.std()

    # Calculate average red value to detect red loss
    red_channel = img[:, :, 2]
    avg_red = float(np.mean(red_channel))

    return {
        'brightness': float(brightness),
        'contrast': float(contrast),
        'avg_red': avg_red,
    }

"""Simplified advanced Sea-Thru implementation.

This module provides a lightweight approximation of the full Sea‑Thru
atmospheric model with spatially varying illuminant and dual‑beta
backscatter recovery. The implementation is inspired by the open‑source
project at https://github.com/hainh/sea-thru but greatly simplified so
that it can run with minimal dependencies.
"""

from __future__ import annotations

import os
from typing import Tuple

import numpy as np
from scipy import optimize
from scipy.ndimage import uniform_filter

_cv2 = None


def _lazy_cv2():
    global _cv2
    if _cv2 is None:
        import cv2
        _cv2 = cv2


# ---------------------------------------------------------------------------
# Backscatter estimation
# ---------------------------------------------------------------------------

def _sample_backscatter_points(depth: np.ndarray, img: np.ndarray,
                               fraction: float = 0.01, bins: int = 10) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Collect darkest pixels for backscatter fitting in depth bins."""
    z_min, z_max = depth.min(), depth.max()
    edges = np.linspace(z_min, z_max, bins + 1)
    pts = [[], [], []]
    img_norm = img.mean(axis=2)
    depth_flat = depth.flatten()
    img_flat = img.reshape(-1, 3)
    for i in range(bins):
        mask = (depth_flat >= edges[i]) & (depth_flat <= edges[i + 1])
        if not np.any(mask):
            continue
        norms = img_norm.flatten()[mask]
        idx = np.argsort(norms)
        take = max(1, int(len(idx) * fraction))
        idx = idx[:take]
        d = depth_flat[mask][idx]
        pixels = img_flat[mask][idx]
        for c in range(3):
            pts[c].extend(zip(d, pixels[:, c]))
    return (np.array(pts[0]), np.array(pts[1]), np.array(pts[2]))


def _fit_backscatter(points: np.ndarray, depth_map: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Fit dual‑beta backscatter model for one channel."""

    if len(points) == 0:
        return np.zeros_like(depth_map), np.zeros(4, dtype=np.float32)

    z = points[:, 0]
    v = points[:, 1]

    def model(d, B_inf, beta_B, J_p, beta_D_p):
        return B_inf * (1.0 - np.exp(-beta_B * d)) + J_p * np.exp(-beta_D_p * d)

    p0 = np.array([v.max() if len(v) else 0.0, 0.5, 0.1, 0.5])
    bounds = ([0, 0, 0, 0], [1.5, 5, 1.5, 5])
    try:
        opt, _ = optimize.curve_fit(model, z, v, p0=p0, bounds=bounds, maxfev=4000)
    except Exception:
        opt = p0
    fitted = model(depth_map, *opt)
    return fitted, opt


def estimate_backscatter(depth_map: np.ndarray, img: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Estimate per‑pixel backscatter and coefficients for each channel."""
    points_r, points_g, points_b = _sample_backscatter_points(depth_map, img)
    Br, coef_r = _fit_backscatter(points_r, depth_map)
    Bg, coef_g = _fit_backscatter(points_g, depth_map)
    Bb, coef_b = _fit_backscatter(points_b, depth_map)
    B = np.stack([Br, Bg, Bb], axis=2)
    coefs = np.stack([coef_r, coef_g, coef_b], axis=0)
    return B, coefs

# ---------------------------------------------------------------------------
# Illumination and attenuation
# ---------------------------------------------------------------------------

def estimate_illumination(img: np.ndarray, B: np.ndarray, filter_size: int = 5) -> np.ndarray:
    """Estimate spatially varying illuminant by local averaging."""
    D = np.clip(img.astype(np.float32) - B, 0, None)
    illum = uniform_filter(D, size=(filter_size, filter_size, 1))
    return illum


def _fit_attenuation(depth: np.ndarray, values: np.ndarray) -> np.ndarray:
    """Fit dual exponential attenuation to illumination ratio."""

    d = depth.flatten()
    v = values.flatten()
    mask = (d > 0) & np.isfinite(v)
    d = d[mask]
    v = v[mask]

    def model(x, a, b, c, d):
        return a * np.exp(b * x) + c * np.exp(d * x)

    if len(d) < 4:
        return np.zeros(4, dtype=np.float32)

    p0 = [0.5, -0.8, 0.5, -0.2]
    bounds = ([0, -5, 0, -5], [10, 0, 10, 0])
    try:
        opt, _ = optimize.curve_fit(model, d, v, p0=p0, bounds=bounds, maxfev=4000)
    except Exception:
        opt = np.array(p0)
    return opt


def estimate_beta(depth_map: np.ndarray, illum: np.ndarray, img: np.ndarray, B: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Estimate dual‑beta wideband attenuation map and coefficients."""
    eps = 1e-8
    residual = np.clip(img.astype(np.float32) - B, eps, None)
    raw = -np.log(np.clip(illum, eps, None) / residual) / np.maximum(depth_map, eps)[:, :, None]
    coefs = []
    beta_map = np.zeros_like(raw)
    for c in range(3):
        coef = _fit_attenuation(depth_map, raw[:, :, c])
        coefs.append(coef)
        a, b, c2, d2 = coef
        beta_map[:, :, c] = a * np.exp(b * depth_map) + c2 * np.exp(d2 * depth_map)
    return beta_map, np.stack(coefs, axis=0)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def apply_advanced_sea_thru(image_path: str, depth_map: np.ndarray) -> str:
    """Apply the advanced Sea‑Thru model and return path to corrected image."""
    _lazy_cv2()
    img = _cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not read {image_path}")
    img = img.astype(np.float32) / 255.0

    B, _ = estimate_backscatter(depth_map, img)
    illum = estimate_illumination(img, B)
    beta_map, _ = estimate_beta(depth_map, illum, img, B)

    corrected = (img - B) * np.exp(beta_map * depth_map[:, :, None])
    corrected = np.clip(corrected / np.maximum(illum, 1e-6), 0, 1)
    corrected = (corrected * 255.0).astype(np.uint8)

    out_path = os.path.splitext(image_path)[0] + "_adv_seathru.jpg"
    _cv2.imwrite(out_path, corrected)
    return out_path


"""Depth estimation helpers using MiDaS.

The heavy dependencies (torch, cv2, numpy) are imported lazily inside the
functions so that this module can be imported in environments where those
packages are not available. This also speeds up test startup times.
"""

model = None
_torch = None
_cv2 = None
_np = None


def _lazy_imports():
    """Import heavy dependencies when needed."""
    global _torch, _cv2, _np
    if _torch is None:
        import torch
        torch.hub.set_default_git_env({'GIT_SSL_NO_VERIFY': '1'})
        _torch = torch
    if _cv2 is None:
        import cv2
        _cv2 = cv2
    if _np is None:
        import numpy as np
        _np = np


def load_model():
    global model
    _lazy_imports()
    if model is None:
        model = _torch.hub.load('intel-isl/MiDaS', 'DPT_Large')
        model.eval()
        device = _torch.device('cuda' if _torch.cuda.is_available() else 'cpu')
        model.to(device)
    return model


def estimate_depth(image_path: str):
    """Estimate depth map and average depth using MiDaS."""
    _lazy_imports()
    model = load_model()
    device = next(model.parameters()).device

    img = _cv2.imread(image_path)
    img_rgb = _cv2.cvtColor(img, _cv2.COLOR_BGR2RGB)
    transform = _torch.hub.load('intel-isl/MiDaS', 'transforms').dpt_transform
    input_batch = transform(img_rgb).to(device)

    with _torch.no_grad():
        prediction = model(input_batch)
        prediction = _torch.nn.functional.interpolate(
            prediction.unsqueeze(1),
            size=img_rgb.shape[:2],
            mode='bilinear',
            align_corners=False,
        ).squeeze()

    depth_map = prediction.cpu().numpy()
    avg_depth = float(_np.mean(depth_map))
    return {
        'average_depth': avg_depth,
        'depth_map': depth_map,
    }

import torch
import cv2
import numpy as np
torch.hub.set_default_git_env({'GIT_SSL_NO_VERIFY': '1'})

model = None


def load_model():
    global model
    if model is None:
        model = torch.hub.load('intel-isl/MiDaS', 'DPT_Large')
        model.eval()

        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model.to(device)
    return model


def estimate_depth(image_path: str):
    model = load_model()
    device = next(model.parameters()).device

    img = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    transform = torch.hub.load('intel-isl/MiDaS', 'transforms').dpt_transform
    input_batch = transform(img_rgb).to(device)

    with torch.no_grad():
        prediction = model(input_batch)
        prediction = torch.nn.functional.interpolate(
            prediction.unsqueeze(1),
            size=img_rgb.shape[:2],
            mode='bilinear',
            align_corners=False,
        ).squeeze()

    depth_map = prediction.cpu().numpy()
    avg_depth = float(np.mean(depth_map))
    return {
        'average_depth': avg_depth,
    }

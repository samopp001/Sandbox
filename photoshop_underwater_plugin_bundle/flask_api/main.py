import os
import requests

from depth_estimation import estimate_depth
from image_analysis import analyze_image
from photoshop_api import submit_photoshop_job

def download_image(url, local_path):
    response = requests.get(url)
    response.raise_for_status()
    with open(local_path, 'wb') as f:
        f.write(response.content)


def process_image(image_url: str = None, output_url: str = None, image_file=None):
    if image_file is not None:
        local_path = os.path.join('images', 'input', image_file.filename or 'upload.jpg')
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        image_file.save(local_path)
    else:
        local_path = os.path.join('images', 'input', 'input.jpg')
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        download_image(image_url, local_path)

    depth_metrics = estimate_depth(local_path)
    analysis = analyze_image(local_path)

    adjustments = {
        'depth': depth_metrics,
        'analysis': analysis,
    }

    submit_photoshop_job(local_path, output_url, adjustments)

    return {
        'status': 'submitted',
        'adjustments': adjustments,
    }

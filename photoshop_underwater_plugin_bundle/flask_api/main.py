import os
import requests

from depth_estimation import estimate_depth
from image_analysis import analyze_image
from photoshop_api import submit_photoshop_job
from sea_thru import apply_sea_thru
import shutil

def download_image(url, local_path):
    response = requests.get(url)
    response.raise_for_status()
    with open(local_path, 'wb') as f:
        f.write(response.content)


def process_image(
    image_url: str | None = None,
    output_url: str | None = None,
    image_file=None,
    *,
    image_path: str | None = None,
    output_path: str | None = None,
):
    """Process an image from a URL, uploaded file, or local path.

    ``output_url`` triggers a Photoshop API job, while ``output_path`` simply
    writes the corrected file locally. One of these must be provided.
    """
    if image_file is not None:
        local_path = os.path.join('images', 'input', image_file.filename or 'upload.jpg')
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        image_file.save(local_path)
    elif image_path is not None:
        local_path = image_path
    else:
        local_path = os.path.join('images', 'input', 'input.jpg')
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        download_image(image_url, local_path)

    depth_metrics = estimate_depth(local_path)
    use_adv = bool(os.environ.get('ADVANCED_SEATHRU'))
    corrected_path = apply_sea_thru(local_path, depth_metrics['depth_map'], advanced=use_adv)
    analysis = analyze_image(corrected_path)

    adjustments = {
        'depth': depth_metrics,
        'analysis': analysis,
    }

    if output_url:
        submit_photoshop_job(corrected_path, output_url, adjustments)
    elif output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        shutil.copy(corrected_path, output_path)
    else:
        raise ValueError('Either output_url or output_path must be provided')

    return {
        'status': 'submitted',
        'adjustments': adjustments,
    }

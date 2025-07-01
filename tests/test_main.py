import io
from types import SimpleNamespace
from unittest.mock import patch

import pytest

# Because depth_estimation and image_analysis lazily import heavy deps, we don't
# require them here. We patch their exported functions when importing main.

# Import the main module under test
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'photoshop_underwater_plugin_bundle', 'flask_api')))
import main  # type: ignore


@pytest.fixture(autouse=True)
def _patch_defaults():
    """Patch heavy dependencies for each test."""
    with (
        patch(
            'main.estimate_depth',
            return_value={'average_depth': 1.0, 'depth_map': [[1.0]]},
        ),
        patch(
            'main.apply_sea_thru',
            side_effect=lambda path, d: path,
        ),
        patch(
            'main.analyze_image',
            return_value={'brightness': 0.5, 'contrast': 0.1, 'avg_red': 50},
        ),
        patch(
            'main.submit_photoshop_job',
            return_value=None,
        ),
        patch('requests.get') as mget,
    ):
        mget.return_value = SimpleNamespace(content=b'data', raise_for_status=lambda: None)
        yield


def test_process_image_url(tmp_path):
    image_url = 'http://example.com/test.jpg'
    output_url = 'http://example.com/out.jpg'
    with patch('main.download_image') as dl:
        dl.side_effect = lambda url, path: open(path, 'wb').write(b'data')
        result = main.process_image(image_url=image_url, output_url=output_url)
    assert result['status'] == 'submitted'
    assert 'depth' in result['adjustments']
    assert 'analysis' in result['adjustments']


class DummyFile:
    def __init__(self, filename, data):
        self.filename = filename
        self._data = data

    def save(self, path):
        with open(path, 'wb') as f:
            f.write(self._data)


def test_process_image_file(tmp_path):
    output_url = 'http://example.com/out.jpg'
    dummy = DummyFile('upload.jpg', b'data')
    result = main.process_image(output_url=output_url, image_file=dummy)
    assert result['status'] == 'submitted'


def create_app():
    import importlib
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'photoshop_underwater_plugin_bundle', 'flask_api')))
    module = importlib.import_module('run_service')
    return module.app


def test_flask_endpoint_json(tmp_path):
    app = create_app()
    client = app.test_client()
    payload = {'image_url': 'http://example.com/in.jpg', 'output_url': 'http://example.com/out.jpg'}
    with patch('main.process_image', return_value={'status': 'submitted', 'adjustments': {}}):
        resp = client.post('/process', json=payload)
    assert resp.status_code == 200
    assert resp.json['status'] == 'submitted'


def test_flask_endpoint_upload(tmp_path):
    app = create_app()
    client = app.test_client()
    data = {
        'output_url': 'http://example.com/out.jpg'
    }
    file_data = (io.BytesIO(b'data'), 'test.jpg')
    with patch('main.process_image', return_value={'status': 'submitted', 'adjustments': {}}):
        resp = client.post('/process', data={'image': file_data, 'output_url': data['output_url']}, content_type='multipart/form-data')
    assert resp.status_code == 200
    assert resp.json['status'] == 'submitted'

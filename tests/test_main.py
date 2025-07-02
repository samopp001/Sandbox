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
if 'requests' not in sys.modules:
    sys.modules['requests'] = SimpleNamespace(get=lambda *a, **k: None, post=lambda *a, **k: None)
if 'advanced_sea_thru' not in sys.modules:
    sys.modules['advanced_sea_thru'] = SimpleNamespace(apply_advanced_sea_thru=lambda p, d: p)
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
            side_effect=lambda path, d, **_: path,
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


def create_app(module_name='run_service'):
    import importlib
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'photoshop_underwater_plugin_bundle', 'flask_api')))
    if 'flask' not in sys.modules:
        class Dummy:
            def __init__(self):
                self.data = {}
            def __call__(self, name):
                return self
            def route(self, path, methods=None):
                def dec(f):
                    self.data['handler'] = f
                    return f
                return dec
            def test_client(self):
                return None
        dummy = Dummy()
        sys.modules['flask'] = SimpleNamespace(Flask=lambda name: dummy, request=None, jsonify=lambda d: d)
    module = importlib.import_module(module_name)
    return module


def test_flask_endpoint_json(tmp_path):
    module = create_app()
    payload = {'image_url': 'http://example.com/in.jpg', 'output_url': 'http://example.com/out.jpg'}
    req = SimpleNamespace(content_type='application/json', json=payload)
    with (
        patch('main.process_image', return_value={'status': 'submitted', 'adjustments': {}}),
        patch.object(module, 'request', req),
        patch.object(module, 'jsonify', lambda d: d),
    ):
        resp = module.process()
    assert resp['status'] == 'submitted'


def test_flask_endpoint_upload(tmp_path):
    module = create_app()
    dummy_file = DummyFile('test.jpg', b'data')
    req = SimpleNamespace(
        content_type='multipart/form-data',
        files={'image': dummy_file},
        form={'output_url': 'http://example.com/out.jpg'},
    )
    with (
        patch('main.process_image', return_value={'status': 'submitted', 'adjustments': {}}),
        patch.object(module, 'request', req),
        patch.object(module, 'jsonify', lambda d: d),
    ):
        resp = module.process()
    assert resp['status'] == 'submitted'


def test_local_cli_invocation(tmp_path, monkeypatch):
    img_in = tmp_path / 'in.jpg'
    img_out = tmp_path / 'out.jpg'
    img_in.write_bytes(b'data')
    called = {}

    def fake_process_image(**kwargs):
        called.update(kwargs)
        return {'status': 'submitted', 'adjustments': {}}

    monkeypatch.setattr('local_cli.process_image', fake_process_image)
    argv = [
        'local_cli.py',
        str(img_in),
        str(img_out),
    ]
    monkeypatch.setattr('sys.argv', argv)
    import local_cli
    local_cli.main()
    assert called['image_path'] == str(img_in)
    assert called['output_path'] == str(img_out)

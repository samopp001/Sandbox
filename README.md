# Underwater AI Photo Correction

This project provides a sample Photoshop UXP plugin and a Python backend for automatically enhancing underwater images. The backend uses MiDaS depth estimation, a simplified implementation of the [Sea‑Thru](https://github.com/hainh/sea-thru) algorithm that models per-channel attenuation `β` from the depth map, OpenCV analysis, and the Adobe Photoshop API to submit color correction jobs.

## Contents
- `photoshop_underwater_plugin_bundle/flask_api/` – Python service handling image analysis and Photoshop API calls
- `photoshop_underwater_plugin_bundle/uxp_plugin/` – UXP plugin displayed in Photoshop

## Prerequisites
- **Adobe Photoshop 22+** with UXP plugin support
- **Node.js** for installing the UXP Developer Tool
- **Python 3.8+** with `pip`
- Internet access (for model downloads and Adobe API calls)
- An Amazon S3 bucket or other cloud storage for hosting input/output images

## Amazon S3 Setup
1. Create an S3 bucket in your AWS account.
2. Upload your images or prepare a folder for outputs.
3. Enable public read or generate pre‑signed URLs so the Photoshop API can access the files.
4. Note the URLs for both the input image and desired output location. These are used in the plugin or backend when submitting jobs.

## Adobe Developer Console Setup
1. Sign in to the [Adobe Developer Console](https://developer.adobe.com/console). Create a new project.
2. Add **Photoshop API** to the project.
3. Generate the following credentials:
   - `client_id` and `client_secret`
   - `refresh_token` (via OAuth, using an Adobe account with Photoshop access)
   - API key
4. In `photoshop_underwater_plugin_bundle/flask_api/config.py`, replace the placeholder values with your credentials.
5. Ensure the Photoshop API has permission to read from your S3 bucket or chosen storage.

## Backend Setup
1. Create and activate a Python virtual environment (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r photoshop_underwater_plugin_bundle/flask_api/requirements.txt
   ```
3. Run the Flask service:
   ```bash
   python photoshop_underwater_plugin_bundle/flask_api/run_service.py
   ```
   The server listens on `http://localhost:5000/process`.

### Local Command-Line Usage
To run the correction entirely offline on a local image, use the provided CLI:

```bash
python photoshop_underwater_plugin_bundle/flask_api/local_cli.py input.jpg output.jpg
```

Add `--advanced` to enable the more advanced Sea‑Thru model. This mode does not
contact the Photoshop API and simply writes the corrected file to the specified
output path.

## UXP Plugin Setup
1. Install the [UXP Developer Tool](https://developer.adobe.com/photoshop/uxp/guides/uxp-developer-tools/).
2. In the tool, click **Add Plugin** and select the `photoshop_underwater_plugin_bundle/uxp_plugin` folder.
3. Start the plugin from the UXP Developer Tool. In Photoshop, open **Plugins → Underwater AI Correction** to show the panel.

## Using the Plugin
1. In the panel, either paste an **Image URL** or use **Upload Image** to choose a local file.
2. Provide the **Output URL** (e.g., an S3 location where the processed image should be written).
3. Click **Process Image**. The plugin sends the file or URL to the Flask backend.
4. The backend performs depth estimation, models `β` from depth versus color decay, applies the Sea‑Thru correction to reduce color cast, analyzes the corrected image, and then submits a Photoshop API job with additional color‑correction actions.
5. When complete, the plugin displays the before and after images for comparison (the output image is loaded from the provided URL).

## Notes for New Users
- The credentials in `config.py` must be valid or the API call will fail.
- MiDaS weights are automatically downloaded when first run and require an internet connection.
- Output URLs usually reference an S3 object with `write` permissions for the Photoshop API service. Using pre‑signed URLs is often easiest.
- The project currently uses a placeholder Photoshop action named `UnderwaterColorCorrection`. Customize this action in your Adobe account or adjust `photoshop_api.py` as needed.

## Development and Testing
Run static checks with:
```bash
python -m py_compile $(find photoshop_underwater_plugin_bundle -name '*.py')
pytest -q
```
The repository includes a small pytest suite covering the processing logic and Flask endpoint.


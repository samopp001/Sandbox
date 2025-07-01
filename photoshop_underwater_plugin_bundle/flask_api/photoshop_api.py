import requests
import json
from typing import Dict
import config

TOKEN_CACHE = None


def get_access_token() -> str:
    global TOKEN_CACHE
    if TOKEN_CACHE:
        return TOKEN_CACHE
    data = {
        'grant_type': 'refresh_token',
        'client_id': config.CLIENT_ID,
        'client_secret': config.CLIENT_SECRET,
        'refresh_token': config.REFRESH_TOKEN,
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    resp = requests.post(config.TOKEN_URL, data=data, headers=headers)
    resp.raise_for_status()
    TOKEN_CACHE = resp.json()['access_token']
    return TOKEN_CACHE


def submit_photoshop_job(local_path: str, output_url: str, adjustments: Dict):
    token = get_access_token()
    headers = {
        'Authorization': f'Bearer {token}',
        'x-api-key': config.API_KEY,
        'Content-Type': 'application/json'
    }

    # Example payload with basic adjustments
    payload = {
        'inputs': [
            {
                'href': f'file://{local_path}',
                'storage': 'local'
            }
        ],
        'options': {
            'actions': ['UnderwaterColorCorrection'],
            'outputFormat': 'jpeg',
        },
        'outputs': [
            {
                'href': output_url,
                'storage': 'external'
            }
        ]
    }

    response = requests.post(
        'https://image.adobe.io/photoshop/actions',
        headers=headers,
        data=json.dumps(payload)
    )
    response.raise_for_status()
    return response.json()

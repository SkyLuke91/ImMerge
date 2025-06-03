import os
import requests
import uuid
from datetime import datetime

def get_all_album_ids(base_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{base_url}/api/album", headers=headers)
    response.raise_for_status()
    return [album['id'] for album in response.json()]

def download_album_assets(base_url, api_key, album_id, target_dir):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{base_url}/api/album/{album_id}", headers=headers)
    response.raise_for_status()
    assets = response.json().get("assets", [])
    for asset in assets:
        asset_id = asset["id"]
        download_url = f"{base_url}/api/asset/file/{asset_id}"
        asset_data = requests.get(download_url, headers=headers)
        if asset_data.status_code == 200:
            extension = asset["originalPath"].split(".")[-1]
            with open(os.path.join(target_dir, f"{asset_id}.{extension}"), "wb") as f:
                f.write(asset_data.content)

def upload_montage_to_immich(base_url, api_key, filepath):
    headers = {"x-api-key": api_key}
    now = datetime.utcnow().isoformat() + "Z"
    files = {
        "assetData": open(filepath, "rb")
    }
    data = {
        "deviceAssetId": str(uuid.uuid4()),
        "deviceId": "montage-uploader",
        "fileCreatedAt": now,
        "fileModifiedAt": now,
        "isFavorite": "false"
    }

    print(f"Uploading {os.path.basename(filepath)} to Immich...")
    response = requests.post(f"{base_url}/api/asset/upload", headers=headers, files=files, data=data)
    if response.status_code != 201:
        print("Upload failed:", response.status_code, response.text)
    else:
        print("Upload successful.")

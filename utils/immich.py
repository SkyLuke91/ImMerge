import os
import uuid
import time
import requests
from datetime import datetime

def get_all_album_ids(base_url, api_key):
    headers = {
        "x-api-key": api_key,
        "Accept": "application/json"
    }
    response = requests.get(f"{base_url}/api/albums", headers=headers)
    response.raise_for_status()

    albums = response.json()
    return [(album['id'], album['albumName']) for album in albums]

def download_album_assets(base_url, api_key, album_id, target_dir):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{base_url}/api/albums/{album_id}", headers=headers)
    response.raise_for_status()
    assets = response.json().get("assets", [])

    os.makedirs(target_dir, exist_ok=True)
    downloaded_files = []
    total_assets = len(assets)

    for i, asset in enumerate(assets, 1):
        asset_id = asset["id"]
        original_path = asset.get("originalPath", f"{asset_id}")
        ext = os.path.splitext(original_path)[1].lower().lstrip(".") or "jpg"
        filename = f"{asset_id}.{ext}"
        filepath = os.path.join(target_dir, filename)

        if os.path.exists(filepath):
            print(f"⏭️ Skipping already downloaded {filename} ({i}/{total_assets})")
            downloaded_files.append(filepath)
            continue

        download_url = f"{base_url}/api/assets/{asset_id}/original"
        asset_data = requests.get(download_url, headers=headers)

        if asset_data.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(asset_data.content)
            downloaded_files.append(filepath)
            print(f"✅ Downloaded {filename} ({i}/{total_assets})")
        else:
            print(f"❌ Failed to download asset {asset_id}: {asset_data.status_code}")

    return downloaded_files

def set_file_timestamp(filepath, reference_paths):
    latest_time = 0
    for f in reference_paths:
        try:
            t = os.path.getmtime(f)
            if t > latest_time:
                latest_time = t
        except Exception as e:
            print(f"Warning: could not get time for {f}: {e}")
    
    new_time = latest_time + 1 if latest_time else time.time()
    os.utime(filepath, (new_time, new_time))
    print(f"📆 Set montage timestamp to: {datetime.utcfromtimestamp(new_time).isoformat()}")
    return new_time  # Return timestamp for upload metadata

def assign_asset_to_album(base_url, api_key, album_id, asset_id):
    url = f"{base_url}/api/albums/{album_id}/assets"
    headers = {
        "x-api-key": api_key,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    data = {
        "ids": [asset_id]
    }

    print(f"🔗 Assigning montage to album {album_id}...")
    response = requests.put(url, headers=headers, json=data)

    if response.status_code == 200:
        print("✅ Montage added to album.")
    else:
        print("❌ Failed to assign montage:", response.status_code, response.text)

def upload_montage_to_immich(base_url, api_key, filepath, album_id=None, reference_files=None, album_name="montage"):
    headers = {"x-api-key": api_key}

    # Rename montage file to album name
    montage_dir = os.path.dirname(filepath)
    new_filename = f"{album_name}.mp4"
    new_path = os.path.join(montage_dir, new_filename)
    
    if filepath != new_path:
        os.rename(filepath, new_path)
        filepath = new_path

    # Set timestamp based on last album media
    if reference_files:
        new_time = set_file_timestamp(filepath, reference_files)
        created_time = datetime.utcfromtimestamp(new_time).isoformat() + "Z"
    else:
        created_time = datetime.utcnow().isoformat() + "Z"

    with open(filepath, "rb") as file_data:
        files = {
            "assetData": (os.path.basename(filepath), file_data, "video/mp4")
        }
        data = {
            "deviceAssetId": str(uuid.uuid4()),
            "deviceId": "ImMerge",
            "fileCreatedAt": created_time,
            "fileModifiedAt": created_time,
            "isFavorite": "false"
        }

        print(f"🚀 Uploading {new_filename} to Immich...")
        response = requests.post(f"{base_url}/api/assets", headers=headers, files=files, data=data)

        response_json = response.json()

    if response.status_code == 201:
        print("✅ Upload successful.")
        asset_id = response_json.get("id")
    elif response.status_code == 200 and response_json.get("status") == "duplicate":
        print("⚠️ Upload skipped — asset already exists.")
        asset_id = response_json.get("id")
    else:
        print("❌ Upload failed:", response.status_code, response.text)
        return

    if album_id and asset_id:
        assign_asset_to_album(base_url, api_key, album_id, asset_id)


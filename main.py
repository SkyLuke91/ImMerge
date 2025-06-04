import sys
import os
import time
import glob
import random
import shutil

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
from utils.immich import download_album_assets, get_all_album_ids, upload_montage_to_immich
from utils.media_filter import filter_media, filter_similar_photos
from utils.ffmpeg_helper import prepare_ffmpeg_inputs, run_montage
from utils.photo_pairing import pair_vertical_photos_side_by_side

load_dotenv()

BASE_URL = os.getenv("IMMICH_BASE_URL")
API_KEY = os.getenv("IMMICH_API_KEY")
TEMP_DIR = os.getenv("TEMP_DIR", "./temp")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")
MUSIC_DIR = os.getenv("MUSIC_DIR", "./data")
RESOLUTION = os.getenv("RESOLUTION", "1080p")
PHOTO_DURATION = float(os.getenv("PHOTO_DURATION", 3))
SIM_THRESHOLD = float(os.getenv("PHOTO_SIMILARITY_THRESHOLD", 0.9))
DUP_THRESHOLD = float(os.getenv("PHOTO_DUPLICATE_THRESHOLD", 5))
MAX_VIDEO_DURATION = int(os.getenv("MAX_VIDEO_DURATION", 5))

# Select random music file from folder

music_candidates = [os.path.join(MUSIC_DIR, f) for f in os.listdir(MUSIC_DIR) if f.lower().endswith(".mp3")]
MUSIC_FILE = random.choice(music_candidates) if music_candidates else None

if MUSIC_FILE:
    print(f"🎵 Selected music file: {os.path.basename(MUSIC_FILE)}")
else:
    print("⚠️ No music file found in MUSIC_DIR. Montage will be silent.")

# Safely parse allowed extensions with default
exts = os.getenv("ALLOWED_EXTENSIONS")
if exts:
    EXTENSIONS = [e.strip().lower() if e.startswith('.') else '.' + e.strip().lower() for e in exts.split(",") if e.strip()]
else:
    EXTENSIONS = [".jpg", ".png", ".mp4", ".mov"]

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

processed_marker = os.path.join(TEMP_DIR, "processed_albums.txt")
if os.path.exists(processed_marker):
    with open(processed_marker, "r") as f:
        processed = set(f.read().splitlines())
else:
    processed = set()

album_ids = get_all_album_ids(BASE_URL, API_KEY)

for album_id, album_name in album_ids:
    if album_id in processed:
        continue

    album_dir = os.path.join(TEMP_DIR, album_id)
    os.makedirs(album_dir, exist_ok=True)
    print(f"Processing new album: {album_name}")

    # Download assets
    downloaded_files = download_album_assets(BASE_URL, API_KEY, album_id, album_dir)
    print("Downloaded files in main.py:", downloaded_files)

    # Filter media (photos and videos)
    filtered_photos, filtered_videos = filter_media(album_dir, {
        "allowed_extensions": EXTENSIONS,
        "photo_similarity_threshold": SIM_THRESHOLD,
        "max_video_duration": MAX_VIDEO_DURATION
    })

    print(f"Photos before duplicate filtering: {len(filtered_photos)}")
    filtered_photos = filter_similar_photos(filtered_photos, DUP_THRESHOLD)
    print(f"Photos after duplicate filtering: {len(filtered_photos)}")

    filtered_media = (filtered_photos, filtered_videos)
    print(f"Filtered videos: {len(filtered_videos)}")

    # Pair vertical photos side by side
    combined_photos_dir = os.path.join(TEMP_DIR, "combined_photos")
    os.makedirs(combined_photos_dir, exist_ok=True)
    paired_photos = pair_vertical_photos_side_by_side(filtered_photos, combined_photos_dir)
    print(f"Photos after pairing: {len(paired_photos)}")

    # Prepare media list with paired photos + videos
    filtered_media = (paired_photos, filtered_videos)

    input_txt = os.path.join(album_dir, "inputs.txt")
    prepare_ffmpeg_inputs(filtered_media, input_txt, PHOTO_DURATION)

    output_video_path = os.path.join(OUTPUT_DIR, f"{album_name}_montage.mp4")
    run_montage(input_txt, output_video_path, RESOLUTION, MUSIC_FILE)

    upload_montage_to_immich(
        base_url=BASE_URL,
        api_key=API_KEY,
        filepath=output_video_path,
        album_id=album_id,
        reference_files=filtered_photos + filtered_videos,
        album_name=album_name
    )
    
    CLEANUP = os.getenv("CLEANUP_AFTER_UPLOAD", "no").lower() == "yes"

    if CLEANUP:
        print("🧹 Cleaning up temporary files...")
        try:
            shutil.rmtree(album_dir, ignore_errors=True)
            shutil.rmtree(combined_photos_dir, ignore_errors=True)
            os.remove(output_video_path)
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")

    with open(processed_marker, "a") as f:
        f.write(album_id + "\n")

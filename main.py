import os
import time
from dotenv import load_dotenv
from utils.immich import download_album_assets, get_all_album_ids, upload_montage_to_immich
from utils.media_filter import filter_media
from utils.ffmpeg_helper import prepare_ffmpeg_inputs, run_montage

load_dotenv()

BASE_URL = os.getenv("IMMICH_BASE_URL")
API_KEY = os.getenv("IMMICH_API_KEY")
TEMP_DIR = os.getenv("TEMP_DIR", "./temp")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")
MUSIC_FILE = os.getenv("MUSIC_FILE", "./background.mp3")
RESOLUTION = os.getenv("RESOLUTION", "1080p")
PHOTO_DURATION = float(os.getenv("PHOTO_DURATION", 3))
SIM_THRESHOLD = int(os.getenv("PHOTO_SIMILARITY_THRESHOLD", 5))
MAX_VIDEO_DURATION = int(os.getenv("MAX_VIDEO_DURATION", 5))
EXTENSIONS = tuple(os.getenv("ALLOWED_EXTENSIONS", "").split(","))

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

processed_marker = os.path.join(TEMP_DIR, "processed_albums.txt")
if os.path.exists(processed_marker):
    with open(processed_marker, "r") as f:
        processed = set(f.read().splitlines())
else:
    processed = set()

album_ids = get_all_album_ids(BASE_URL, API_KEY)

for album_id in album_ids:
    if album_id in processed:
        continue

    album_dir = os.path.join(TEMP_DIR, album_id)
    os.makedirs(album_dir, exist_ok=True)
    print(f"Processing new album: {album_id}")

    download_album_assets(BASE_URL, API_KEY, album_id, album_dir)

    filtered_media = filter_media(album_dir, {
        "allowed_extensions": EXTENSIONS,
        "photo_similarity_threshold": SIM_THRESHOLD,
        "max_video_duration": MAX_VIDEO_DURATION
    })

    input_txt = os.path.join(album_dir, "inputs.txt")
    prepare_ffmpeg_inputs(filtered_media, input_txt, PHOTO_DURATION)

    output_file = os.path.join(OUTPUT_DIR, f"{album_id}_montage.mp4")
    run_montage(input_txt, output_file, MUSIC_FILE, RESOLUTION)
    upload_montage_to_immich(BASE_URL, API_KEY, output_file)

    with open(processed_marker, "a") as f:
        f.write(album_id + "\n")

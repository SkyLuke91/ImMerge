import os
import mimetypes
import subprocess
import json
import imagehash
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

def is_portrait(image_path):
    with Image.open(image_path) as img:
        return img.height > img.width

def get_video_duration(file_path):
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "format=duration",
            "-of", "json",
            file_path
        ]
        output = subprocess.check_output(cmd).decode("utf-8")
        data = json.loads(output)
        return float(data["format"]["duration"])
    except Exception as e:
        print(f"Warning: Failed to get duration for {file_path}: {e}")
        return float("inf")

def filter_media(media_dir, config):
    allowed_extensions = [e.lower() for e in config.get("allowed_extensions", [".jpg", ".png", ".mp4", ".mov"])]
    max_video_duration = int(config.get("max_video_duration", 30))
    photo_similarity_threshold = float(config.get("photo_similarity_threshold", 0.8))  # between 0 and 1

    filtered_photos = []
    filtered_videos = []
    seen_hashes = []

    for root, _, files in os.walk(media_dir):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            path = os.path.join(root, file)

            mime_type, _ = mimetypes.guess_type(path)
            print(f"Checking file: {file} (ext: {ext}) - MIME: {mime_type}")

            if ext not in allowed_extensions:
                print(f"Skipping unsupported extension: {ext}")
                continue

            if mime_type:
                if mime_type.startswith("image"):
                    try:
                        hash_val = imagehash.phash(Image.open(path))
                        is_similar = any(
                            h - hash_val < (1.0 - photo_similarity_threshold) * 64 for h in seen_hashes
                        )
                        if not is_similar:
                            seen_hashes.append(hash_val)
                            filtered_photos.append(path)
                        else:
                            print(f"🧹 Skipping similar photo: {file}")
                    except Exception as e:
                        print(f"⚠️ Error processing image {file}: {e}")

                elif mime_type.startswith("video"):
                    duration = get_video_duration(path)
                    if duration <= max_video_duration:
                        filtered_videos.append(path)

    return filtered_photos, filtered_videos

def filter_similar_photos(photo_paths, threshold=5):
    hashes = {}
    filtered_photos = []

    for path in photo_paths:
        try:
            img_hash = imagehash.phash(Image.open(path))
        except Exception as e:
            print(f"Warning: Could not process image {path}: {e}")
            continue

        # Check if similar hash exists already
        if not any(abs(img_hash - existing_hash) <= threshold for existing_hash in hashes.values()):
            hashes[path] = img_hash
            filtered_photos.append(path)
        else:
            print(f"Duplicate found and skipped: {path}")

    return filtered_photos

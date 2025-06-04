import subprocess
import os
import shlex
import tempfile
import shutil
import datetime
from PIL import Image
from PIL.ExifTags import TAGS
import json

def get_image_datetime(path):
    try:
        with Image.open(path) as img:
            exif_data = img._getexif()
            if not exif_data:
                return None
            for tag, value in exif_data.items():
                if TAGS.get(tag) == "DateTimeOriginal":
                    return datetime.datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except Exception as e:
        print(f"⚠️ Could not read EXIF for {path}: {e}")
    return None

def get_video_creation_time(path):
    try:
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_entries", "format_tags=creation_time",
            path
        ]
        output = subprocess.check_output(cmd).decode("utf-8")
        data = json.loads(output)
        creation_time = data.get("format", {}).get("tags", {}).get("creation_time", None)
        if creation_time:
            return datetime.datetime.fromisoformat(creation_time.replace("Z", "+00:00"))
    except Exception as e:
        print(f"⚠️ Could not read video metadata for {path}: {e}")
    return None

def get_media_datetime(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"]:
        dt = get_image_datetime(path)
    else:
        dt = get_video_creation_time(path)
    if dt:
        return dt
    # fallback
    return datetime.datetime.fromtimestamp(os.path.getmtime(path))

def prepare_ffmpeg_inputs(filtered_media, input_txt, photo_duration):
    photos, videos = filtered_media
    all_media = photos + videos

    all_media_sorted = sorted(
        all_media,
        key=get_media_datetime
    )

    print("Sorted media chronologically:", all_media_sorted)

    with open(input_txt, "w") as f:
        for i, media_file in enumerate(all_media_sorted):
            abs_path = os.path.abspath(media_file)
            if not os.path.exists(abs_path):
                print(f"Skipping missing file: {abs_path}")
                continue

            quoted_path = shlex.quote(abs_path)
            ext = os.path.splitext(abs_path)[1].lower()

            if ext in [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"]:
                f.write(f"file {quoted_path}\n")
                f.write(f"duration {photo_duration}\n")
            else:  # video
                f.write(f"file {quoted_path}\n")

        # Repeat last image if needed
        if all_media_sorted:
            last_path = os.path.abspath(all_media_sorted[-1])
            ext = os.path.splitext(last_path)[1].lower()
            if ext in [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"]:
                f.write(f"file {shlex.quote(last_path)}\n")

def run_montage(input_txt_path, output_path, resolution="1080p", music_file=None):
    resolution_map = {
        "1080p": "1920x1080",
        "4k": "3840x2160"
    }

    target_res = resolution_map.get(resolution, '1920x1080')
    w, h = target_res.split('x')
    scale_filter = f"scale=w={w}:h={h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2"

    cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", input_txt_path,
    ]

    if music_file:
        cmd += ["-i", music_file, "-shortest"]

    cmd += [
        "-vf", scale_filter,
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-y",
        output_path
    ]

    print("Running FFmpeg with command:", " ".join(cmd))
    subprocess.run(cmd, check=True)
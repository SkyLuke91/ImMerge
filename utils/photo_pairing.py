from PIL import Image, ExifTags
import os
import datetime

def is_vertical(photo_path):
    with Image.open(photo_path) as img:
        return img.height > img.width

def get_image_datetime(path):
    try:
        with Image.open(path) as img:
            exif_data = img._getexif()
            if not exif_data:
                return None
            for tag, value in exif_data.items():
                if ExifTags.TAGS.get(tag) == "DateTimeOriginal":
                    return datetime.datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except Exception as e:
        print(f"⚠️ Could not read EXIF for {path}: {e}")
    return datetime.datetime.fromtimestamp(os.path.getmtime(path))  # fallback

def pair_vertical_photos_side_by_side(photo_paths, output_dir):
    """
    Pairs vertical photos into combined images, saves them, and returns a list of all photo paths
    (combined + unpaired + non-vertical), sorted chronologically by capture date.
    """
    os.makedirs(output_dir, exist_ok=True)
    result_with_dates = []

    vertical_photos = [p for p in photo_paths if is_vertical(p)]
    non_vertical_photos = [p for p in photo_paths if p not in vertical_photos]

    # Sort verticals before pairing
    vertical_photos_sorted = sorted(vertical_photos, key=get_image_datetime)

    for i in range(0, len(vertical_photos_sorted), 2):
        if i + 1 < len(vertical_photos_sorted):
            img1_path = vertical_photos_sorted[i]
            img2_path = vertical_photos_sorted[i + 1]

            img1 = Image.open(img1_path)
            img2 = Image.open(img2_path)

            # Resize to same height
            h = min(img1.height, img2.height)
            img1 = img1.resize((int(img1.width * h / img1.height), h))
            img2 = img2.resize((int(img2.width * h / img2.height), h))

            combined_img = Image.new("RGB", (img1.width + img2.width, h))
            combined_img.paste(img1, (0, 0))
            combined_img.paste(img2, (img1.width, 0))

            combined_filename = os.path.join(output_dir, f"combined_{i}.jpg")
            combined_img.save(combined_filename)

            img1.close()
            img2.close()

            # Use the earlier datetime of the pair
            datetime1 = get_image_datetime(img1_path)
            datetime2 = get_image_datetime(img2_path)
            combined_datetime = min(datetime1, datetime2)

            result_with_dates.append((combined_filename, combined_datetime))
        else:
            # Single unpaired vertical photo
            path = vertical_photos_sorted[i]
            dt = get_image_datetime(path)
            result_with_dates.append((path, dt))

    # Add non-vertical photos with their dates
    for path in non_vertical_photos:
        dt = get_image_datetime(path)
        result_with_dates.append((path, dt))

    # Final chronological sort
    sorted_paths = [p for p, _ in sorted(result_with_dates, key=lambda x: x[1])]
    return sorted_paths

# ImMerge
immich Montage &amp; Media Engine for Rendering Gallery Experiences

A self-hosted, Dockerized Python application that automatically creates video montages from photo albums stored in [Immich](https://github.com/immich-app/immich). The generated videos are filtered for duplicate/similar images, trimmed for long videos, and combined with optional background music using `ffmpeg`. The final montage is automatically uploaded back to Immich.
## ✨ Features

- 📸 Automatically fetches new albums from Immich
- 🔍 Filters similar/duplicate photos using perceptual hashing
- ✂️ Trims long videos to a maximum duration
- 🎬 Creates video montage with transitions and background music
- 📤 Auto-uploads finished montage video back to Immich
- 🕒 Runs daily (or at any custom interval) via `cron`
- 🐳 Fully Dockerized for easy deployment

---

## 📁 Project Structure

.
├── Dockerfile
├── docker-compose.yml
├── .env # Configuration variables
├── main.py # Main script to create montage
├── utils/
│ ├── immich.py # Immich API helpers
│ ├── media_filter.py # Media filtering & deduplication
│ └── ffmpeg_helper.py # ffmpeg montage creation
├── requirements.txt
├── entrypoint.sh
└── data/
├── temp/ # Temporary working directory
├── output/ # Final output montages
└── background.mp3 # Optional background music


---

## ⚙️ Configuration

All settings are managed in the `.env` file:

```
IMMICH_BASE_URL=https://your.immich.address/	#base port is 2283
IMMICH_API_KEY=immich API KEY
PHOTO_SIMILARITY_THRESHOLD=0.64	#higher value means more similar photos selected (0-1)
PHOTO_DUPLICATE_THRESHOLD=5	#lower value means more similar photos selected (0-10)
MAX_VIDEO_DURATION=10 #not ready jet will trim video files at this length
ALLOWED_EXTENSIONS=.jpg,.jpeg,.png,.mp4,.mov
RESOLUTION=1080p	#1080p or 4k
PHOTO_DURATION=2	#how long each photo to be shown
OUTPUT_DIR=/app/data/output 
TEMP_DIR=/app/data/temp
MUSIC_DIR=/app/data
CRON_INTERVAL_MINUTES=1440	#cron interval in minutes
CLEANUP_AFTER_UPLOAD=yes	#yes - will delete all temp files after generating and uploading montage
```
## 🚀 Deployment Instructions
### Clone and Unpack
Download and extract this project:

unzip immich-montage-docker-upload.zip
cd immich-montage-docker-upload
### Configure .env
Edit .env with your Immich instance URL and API key:

```
nano .env
```
You can get an API key from the Immich web interface under "Settings" → "API Keys".
### Prepare the Environment
Ensure you have Docker and Docker Compose installed.

### Build and Start
```
docker-compose build
docker-compose up -d
```
### View Logs
```
docker-compose logs -f
```
## 🧠 How It Works
A cron job (inside the container) checks Immich for new albums every X minutes.
New album assets are downloaded into a temporary folder.
The script filters similar photos and trims long videos.
Using ffmpeg, it generates a stylized video montage with optional background music.
The final montage is uploaded back to Immich via its upload API.
Already-processed albums are tracked to avoid duplicates.

## 🔄 Resetting Processed Albums
To reprocess albums:

```
docker-compose down
rm data/temp/processed_albums.txt
docker-compose up -d
```

FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y ffmpeg cron && \
    pip install --no-cache-dir -r requirements.txt

RUN chmod +x ./entrypoint.sh ./montage.sh

CMD ["./entrypoint.sh"]

#!/bin/bash
echo "Starting cron with interval: $CRON_INTERVAL_MINUTES minutes"

echo "*/$CRON_INTERVAL_MINUTES * * * * cd /app && /usr/local/bin/python main.py >> /var/log/cron.log 2>&1" > /etc/cron.d/montage-cron
chmod 0644 /etc/cron.d/montage-cron
crontab /etc/cron.d/montage-cron

cron -f

#!/bin/bash

# Set up timezone
export TZ=${TZ:-America/Chicago}

# Set up cron job from environment variable
CRON_SCHEDULE=${CRON_SCHEDULE:-0 10 * * *}

# Create restricted .env file
touch /app/.env
chmod 600 /app/.env
env | grep -E 'PUSHOVER|CASE_ID' > /app/.env

# Set up standard cron job
echo "$CRON_SCHEDULE cd /app && /usr/local/bin/python3 check.py >> /var/log/cron.log 2>&1" | crontab -

echo "Running initial PERM status check..."
/usr/local/bin/python3 /app/check.py

echo "Starting cron daemon..."
exec cron -f

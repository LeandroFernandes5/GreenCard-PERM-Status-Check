# PERM Case Status Checker

Docker application that automatically checks PERM case status daily and sends notifications to your phone via Pushover.

## Features

- ✅ Runs automatically once daily (configurable time via `.env`)
- ✅ Sends Pushover notifications to your phone
- ✅ **Headless browser** for free CAPTCHA solving (no API costs)
- ✅ Runs immediately on startup, then daily via cron

## Quick Start

### Step 1: Get Pushover API Key

1. Sign up at https://pushover.net
2. Create an application to get your API Token
3. Note your User Key

### Step 2: Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```
PUSHOVER_USER_KEY=your_pushover_user_key_here
PUSHOVER_API_TOKEN=your_pushover_api_token_here
CASE_ID=X-YYY-DDDDD-AAAAAA
TZ=America/Chicago
CRON_SCHEDULE=0 10 * * *
```

### Step 3: Run the application

```bash
docker compose up -d
```

## Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `PUSHOVER_USER_KEY` | Your Pushover user key | *required* | `asdawdawsdawdawdawawd` |
| `PUSHOVER_API_TOKEN` | Your Pushover API token | *required* | `asdasdjasdjhqwodqwdoubqwdo` |
| `CASE_ID` | PERM case number to check | *required* | `X-YYY-DDDDD-AAAAAA` |
| `TZ` | Timezone for the check | `America/Chicago` | `America/New_York` |
| `CRON_SCHEDULE` | Cron schedule format | `0 10 * * *` | `0 10 * * *` (10 AM daily) |

### Cron Schedule Format

`minute hour day month weekday`

Examples:
- `0 10 * * *` - 10:00 AM daily
- `30 14 * * *` - 2:30 PM daily
- `0 */6 * * *` - Every 6 hours
- `0 8 * * 1-5` - 8 AM weekdays only
- `15 9 * * 1` - 9:15 AM every Monday

### Updating Configuration

```bash
# Edit .env file
vim .env

# Restart container
docker compose up -d
```

## How It Works

1. Opens headless Chromium browser
2. Navigates to PERM website, invisible reCAPTCHA auto-solves
3. Uses token to query PERM case status
4. Sends result via Pushover notification
5. Repeats daily

## Running Manual Checks

```bash
# Docker Compose v2
docker compose run --rm perm-check python check.py

# Docker Compose v1 (older versions)
docker-compose run --rm perm-check python check.py
```

## View Logs

```bash
# All logs (live)
docker compose logs -f

# Last 50 lines
docker compose logs --tail 50

# Cron-specific logs
docker exec perm-check cat /var/log/cron.log
```

## Files

- `check.py` - Main script
- `Dockerfile` - Docker image
- `docker-compose.yml` - Docker Compose config
- `entrypoint.sh` - Startup script with dynamic cron setup
- `requirements.txt` - Python dependencies
- `.env.example` - Configuration template
- `.env` - Your actual configuration (not in git)
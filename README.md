# NoiseSignal - Automated Music Discovery

NoiseSignal is an automated music discovery system that finds emerging tracks from around the world and creates curated YouTube playlists. The system runs weekly and sends email notifications when new tracks are discovered.

## Features

- 🎵 **Automated Discovery**: Searches for emerging music tracks across global regions
- 📧 **Email Notifications**: Sends weekly summaries and error alerts
- 🐳 **Containerized Deployment**: Easy deployment with Docker
- 🔄 **Robust Automation**: Retry logic, error handling, and health monitoring
- 🎯 **Smart Filtering**: Advanced scoring algorithm to find quality emerging tracks

## Quick Start

### 1. Setup Gmail Credentials

1. Enable 2-Factor Authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
GMAIL_ADDRESS=your-email@gmail.com
GMAIL_APP_PASSWORD=your-16-character-app-password
NOTIFICATION_EMAIL=daddyfandango@gmail.com
TZ=America/New_York
```

### 2. Setup YouTube API

1. Create a Google Cloud Project
2. Enable the YouTube Data API v3
3. Create OAuth 2.0 credentials
4. Download the credentials as `secret.json`

### 3. Deploy with Docker

```bash
# Build and start the container
docker-compose up -d

# Check logs
docker-compose logs -f

# Check health
docker exec noisesignal-automation /app/scripts/health_check.sh
```

### 4. Manual Test Run

```bash
# Run a test execution
docker exec noisesignal-automation python scheduler.py
```

## File Structure

```
NoiseSignal/
├── main.py                  # Core music discovery logic
├── scheduler.py             # Automation wrapper with retries
├── email_notifier.py        # Email notification system
├── config.py                # Configuration and settings
├── youtube_client.py        # YouTube API interface
├── analysis.py              # Track scoring algorithms
├── docker-compose.yml       # Container orchestration
├── Dockerfile               # Container definition
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (create from .env.example)
├── secret.json              # YouTube API credentials
├── scripts/
│   ├── run_weekly.sh        # Weekly execution script
│   ├── health_check.sh      # System health monitoring
│   └── crontab              # Cron job configuration
└── data/
    ├── logs/                # Application logs
    ├── token.pickle         # YouTube authentication token
    └── playlist_id.txt      # Playlist identifier
```

## Automation Schedule

- **Weekly Execution**: Sundays at 6:00 AM
- **Health Checks**: Daily at 9:00 AM
- **Log Cleanup**: Automatic (keeps 30 days of logs)

## Email Notifications

### Weekly Summary
- Track count and top discoveries
- Playlist link for easy access
- Formatted table of new tracks

### Error Alerts
- Authentication failures
- API quota issues
- System errors with details

### Success Notifications
- Simple confirmation when execution completes
- Track count and playlist link

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GMAIL_ADDRESS` | Your Gmail address for sending notifications | Required |
| `GMAIL_APP_PASSWORD` | Gmail app-specific password | Required |
| `NOTIFICATION_EMAIL` | Email to receive notifications | `daddyfandango@gmail.com` |
| `EMAIL_ENABLED` | Enable/disable email notifications | `true` |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `MAX_RETRIES` | Number of retry attempts on failure | `3` |
| `RETRY_DELAY` | Delay between retries (seconds) | `300` |
| `TZ` | Timezone for scheduling | `UTC` |

### Music Discovery Parameters

The system searches for tracks with:
- **View count**: 250 - 400,000 views
- **Subscriber count**: 50 - 100,000 subscribers
- **Duration**: 90 - 600 seconds
- **Age**: Published within last 30 days
- **Quality filters**: Excludes covers, remixes, compilations

## Monitoring

### Health Check
```bash
# Manual health check
docker exec noisesignal-automation /app/scripts/health_check.sh
```

The health check verifies:
- Configuration files
- YouTube token validity
- Recent execution results
- Disk space
- Log file status

### Logs
```bash
# View application logs
docker exec noisesignal-automation tail -f /app/data/logs/noisesignal.log

# View weekly execution logs
docker exec noisesignal-automation tail -f /app/data/logs/weekly_execution.log

# View cron logs
docker-compose logs
```

## Troubleshooting

### Common Issues

**Authentication Errors**
- Verify `secret.json` is valid
- Check if YouTube API quota is exceeded
- Ensure token.pickle has proper permissions

**Email Not Sending**
- Verify Gmail app password is correct
- Check if 2FA is enabled on Gmail account
- Test email credentials manually

**No New Tracks Found**
- Normal if all tracks are already in playlist
- Check if search parameters are too restrictive
- Verify API quota is not exceeded

### Manual Recovery

```bash
# Re-authenticate YouTube
docker exec noisesignal-automation rm /app/token.pickle
docker exec noisesignal-automation python -c "import youtube_client; youtube_client.get_authenticated_service()"

# Test email notifications
docker exec noisesignal-automation python -c "
from email_notifier import EmailNotifier
notifier = EmailNotifier()
notifier.send_success_notification(0, 'https://youtube.com/playlist?list=test', '2024-01-01 12:00:00')
"

# Force execution
docker exec noisesignal-automation python scheduler.py
```

## Maintenance

### Weekly (Automatic)
- Track discovery and playlist updates
- Email notifications
- Log rotation

### Monthly (Manual)
- Review logs for patterns or issues
- Check email delivery
- Verify playlist quality

### Quarterly (Manual)
- Update dependencies
- Review token health
- Test recovery procedures

### Annual (Manual)
- Rotate Gmail app password
- Review and refresh YouTube API credentials
- Update system documentation

## Cost

- **Gmail**: Free (using existing account)
- **YouTube API**: Free (within quota limits)
- **Hosting**: Runs on existing home server
- **Total**: $0/month

## Support

For issues or questions:
1. Check the logs for error details
2. Run health check for system status
3. Review this documentation
4. Test individual components manually

The system is designed to be low-maintenance and self-recovering for most common issues.
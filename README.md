
# Telegram GitHub Release Uploader Bot

A Telegram bot that uploads files (up to 4GB) to GitHub releases with real-time progress tracking.

## Features

- 📁 Upload files directly from Telegram (up to 4GB using MTProto)
- 🌐 Download and upload files from URLs
- 📊 Real-time progress updates for downloads and uploads
- 🔒 Secure GitHub API integration
- 🐳 Docker containerization support
- 📝 Comprehensive logging and error handling

## Requirements

- Python 3.11+
- Telegram API credentials
- GitHub personal access token
- Docker (optional)

## Setup

### 1. Get Telegram API Credentials

1. Go to https://my.telegram.org/auth
2. Create an application and get your `API_ID` and `API_HASH`
3. Create a bot via @BotFather and get the `BOT_TOKEN`

### 2. Create GitHub Personal Access Token

1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Create a token with `repo` scope (for private repos) or `public_repo` (for public repos)

### 3. Create GitHub Release

Create a release in your repository with a specific tag (e.g., `v1.0.0`)

### 4. Environment Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_BOT_TOKEN=your_bot_token
GITHUB_TOKEN=your_github_token
GITHUB_REPO=username/repository
GITHUB_RELEASE_TAG=v1.0.0
```

## Installation

### Option 1: Direct Python

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python bot.py
```

### Option 2: Docker

```bash
# Build and run with docker-compose
docker-compose up -d

# Or build manually
docker build -t telegram-github-bot .
docker run -d --name telegram-bot --env-file .env telegram-github-bot
```

## Usage

1. Start a chat with your bot
2. Send `/start` to see available commands
3. Upload files by:
   - Sending files directly to the bot
   - Sending URLs to download and upload

## Bot Commands

- `/start` - Welcome message and instructions
- `/help` - Show help information
- `/status` - Check current upload status

## File Size Limits

- **Telegram Bot API**: 50MB limit
- **Telegram MTProto (this bot)**: 4GB limit
- **GitHub**: 2GB per file limit (will be handled with chunking if needed)

## Security Features

- Environment variable configuration
- GitHub token validation
- File size validation
- Error handling and logging
- Progress tracking with rate limiting

## Logging

Logs are written to:
- Console output
- `bot.log` file
- Docker logs (when using containers)

## Architecture

```
bot.py              # Main bot logic and Telegram handlers
github_uploader.py  # GitHub API integration
config.py          # Configuration management
requirements.txt   # Python dependencies
Dockerfile         # Container configuration
docker-compose.yml # Container orchestration
```

## Error Handling

The bot handles various error scenarios:
- Invalid URLs
- Network timeouts
- GitHub API errors
- File size limits
- Missing GitHub releases
- Telegram API errors

## Development

### Running in Development

```bash
# Install development dependencies
pip install -r requirements.txt

# Set up pre-commit hooks (optional)
pre-commit install

# Run with debug logging
LOG_LEVEL=DEBUG python bot.py
```

### Testing

```bash
# Run basic functionality test
python -c "
import asyncio
from bot import TelegramBot
bot = TelegramBot()
print('Bot configuration loaded successfully')
"
```

## Troubleshooting

### Common Issues

1. **Bot not responding**: Check bot token and API credentials
2. **Upload failures**: Verify GitHub token permissions and release exists
3. **File size errors**: Ensure files are under 4GB
4. **Progress not updating**: Check Telegram rate limits

### Debug Mode

Set `LOG_LEVEL=DEBUG` in your `.env` file for detailed logging.

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
1. Check the logs for error messages
2. Verify all environment variables are set correctly
3. Ensure GitHub release exists with the specified tag
4. Check GitHub token permissions

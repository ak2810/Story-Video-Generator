# 🎬 AI Story Video Generator

An autonomous AI-powered system that generates viral-style short videos combining **marble race gameplay** with **AI-generated suspenseful stories** for platforms like TikTok, YouTube Shorts, and Instagram Reels.

## ✨ Features

### 🎮 Marble Race Gameplay
- Physics-based marble racing simulation
- Trending rivals/characters integration
- Dynamic visual effects (bloom, particles, trails)
- Synchronized audio synthesis
- Multiple rounds with increasing difficulty

### 📖 AI Story Generation
- **LLM-powered storytelling** using Ollama (Llama 3.1)
- Two-part suspenseful narratives with cliffhangers
- Natural text-to-speech narration (gTTS or espeak-ng)
- **TikTok-style subtitles** with golden yellow styling
- Atmospheric visual slideshows from DuckDuckGo image search
- Safe content filtering and validation

### 🎥 Video Production
- **Split-screen composition**: Marble race (top) + Story visuals (bottom)
- 1080x1920 vertical format (TikTok/Shorts optimized)
- ASS subtitle format with absolute center positioning
- Minimum 61-second duration (auto-padding with silence)
- FFmpeg-powered video processing

### 📤 Publishing Workflow
- **YouTube**: Automatic upload of Part 1 only
- **Part 2**: Metadata saved to file for manual upload
- **P-Cloud sync**: Automated file transfer (both videos + metadata)
- **Telegram notifications**: Dual-video metadata delivery
- Optimized metadata generation (titles, descriptions, tags, hashtags)

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+**
2. **FFmpeg** (must be in system PATH)
   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)
   - Linux: `sudo apt install ffmpeg`
   - macOS: `brew install ffmpeg`
3. **Ollama** (for LLM story generation)
   - Install from [ollama.ai](https://ollama.ai/)
   - Pull model: `ollama pull llama3.1:latest`

### Installation

```bash
# Clone the repository
git clone https://github.com/ak2810/Story-Video-Generator.git
cd Story-Video-Generator

# Create virtual environment
python -m venv storyenv
# Windows:
storyenv\Scripts\activate
# Linux/macOS:
source storyenv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. **Create credentials file** (required for YouTube/Telegram publishing):
   ```bash
   # Create my_credentials.py with the following:
   ```

   ```python
   # my_credentials.py
   TELEGRAM_BOT_TOKEN = "your_telegram_bot_token_here"
   TELEGRAM_CHAT_ID = "your_telegram_chat_id_here"
   PCLOUD_SYNC_DIR = "P:/path/to/pcloud/folder"  # Or None to disable
   ```

2. **YouTube API Setup** (optional, for auto-upload):
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable YouTube Data API v3
   - Create OAuth 2.0 credentials
   - Download `client_secret.json` and place in project root
   - First run will open browser for OAuth authorization

3. **Telegram Bot Setup** (optional, for notifications):
   - Create bot via [@BotFather](https://t.me/botfather)
   - Get your chat ID from [@userinfobot](https://t.me/userinfobot)
   - Add credentials to `my_credentials.py`

4. **Configure publishing** in [production_config.py](production_config.py:169):
   ```python
   AUTO_UPLOAD = True    # Enable YouTube auto-upload
   AUTO_TELEGRAM = True  # Enable Telegram notifications
   ```

### Usage

```bash
# Run story mode video generator
python main_story_mode.py
```

The system will:
1. Generate a two-part suspenseful story using Ollama
2. Create TTS narration and subtitles
3. Fetch atmospheric images from DuckDuckGo
4. Render marble race gameplay
5. Compose split-screen videos (Part 1 + Part 2)
6. Publish Part 1 to YouTube (if enabled)
7. Sync videos to P-Cloud and send Telegram notification

### Output

Generated files in `match_recordings/`:
- `{timestamp}_part1_final.mp4` - Part 1 video
- `{timestamp}_part2_final.mp4` - Part 2 video
- `part2_metadata_{timestamp}.txt` - Part 2 upload metadata

## 📁 Project Structure

```
Story-Video-Generator/
├── main_story_mode.py          # Main orchestrator
├── production_config.py        # Centralized configuration
├── story_generator.py          # LLM story generation
├── narration_engine.py         # TTS narration
├── subtitle_generator.py       # ASS subtitle generation
├── story_visual_manager.py     # Image fetching & validation
├── slideshow_generator.py      # Visual slideshow creation
├── video_compositor.py         # Split-screen composition
├── game_logic.py               # Marble race simulation
├── physics.py                  # Game physics engine
├── effects.py                  # Audio/visual effects
├── trend_selector.py           # Trending rivals/themes
├── metadata_generator.py       # YouTube/TikTok metadata
├── youtube_uploader.py         # YouTube API integration
├── telegram_pusher.py          # Telegram + P-Cloud sync
├── themes.json                 # Rival themes database
├── requirements.txt            # Python dependencies
└── match_recordings/           # Output directory (gitignored)
```

## ⚙️ Configuration

Key settings in [production_config.py](production_config.py):

### Video Output
- `OUTPUT_WIDTH = 1080` - Video width (TikTok vertical)
- `OUTPUT_HEIGHT = 1920` - Video height
- `SPLIT_MODE = "vertical"` - Split layout (vertical/horizontal)
- `FPS = 30` - Frame rate

### Story Generation
- `OLLAMA_MODEL = "llama3.1:latest"` - LLM model
- `STORY_TARGET_WORDS = 180` - Target story length
- `NARRATION_MIN_DURATION = 65` - Minimum video duration (seconds)

### Publishing
- `AUTO_UPLOAD = True/False` - Enable YouTube auto-upload
- `AUTO_TELEGRAM = True/False` - Enable Telegram notifications

## 🎨 Subtitle Styling

TikTok-style subtitles with:
- **Font**: Arial Black, 21px
- **Color**: Golden Yellow (#FFD700)
- **Outline**: 2px black border
- **Position**: Absolute center of screen (x=540, y=960)
- **Format**: ASS (Advanced SubStation Alpha)

## 🛡️ Safety Features

- Image content filtering (banned keywords)
- Safe search enforcement
- Minimum image quality thresholds
- Human-like delays (anti-bot protection)
- Error handling and validation at each step

## 📋 Requirements

### System Dependencies
- Python 3.8+
- FFmpeg (with libx264 codec)
- Ollama (with llama3.1 model)
- 4GB+ RAM recommended
- 1GB+ free disk space per video session

### Python Packages
See [requirements.txt](requirements.txt) for complete list.

### Optional APIs
- YouTube Data API v3 (for auto-upload)
- Telegram Bot API (for notifications)
- P-Cloud desktop app (for file sync)

## 🎯 Use Cases

- **Content Creators**: Generate viral short-form content
- **Social Media Marketing**: Automated engaging video production
- **Education**: Story-driven educational content
- **Entertainment**: Suspenseful mystery/horror stories with gameplay

## 🔧 Troubleshooting

### Common Issues

**"FFmpeg not found"**
- Ensure FFmpeg is installed and in system PATH
- Test: `ffmpeg -version`

**"Ollama connection failed"**
- Start Ollama: `ollama serve`
- Verify model: `ollama list`
- Pull model if missing: `ollama pull llama3.1:latest`

**"No subtitles in video"**
- Check ASS file generation in `match_recordings/`
- Verify FFmpeg subtitle filter is applied

**"YouTube upload failed"**
- Check `client_secret.json` exists
- Re-authorize OAuth if needed
- Verify YouTube Data API v3 is enabled

**"P-Cloud sync not working"**
- Verify P-Cloud desktop app is running
- Check `PCLOUD_SYNC_DIR` path in `my_credentials.py`
- Ensure sync folder exists

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional TTS engines (ElevenLabs, Azure TTS)
- More video effects and transitions
- Alternative LLM backends (OpenAI, Claude)
- Multi-language support
- Advanced subtitle animations

## 📝 License

This project is provided as-is for educational and personal use.

### Third-Party Services
- **Ollama**: Apache 2.0 License
- **Google APIs**: Google API Terms of Service
- **Telegram Bot API**: Telegram Terms of Service

## ⚠️ Disclaimer

- **Content Ownership**: Ensure you have rights to all generated content before publishing
- **API Quotas**: Be aware of YouTube API daily quotas (10,000 units/day)
- **Image Licensing**: Downloaded images are filtered but verify licensing before commercial use
- **Platform Guidelines**: Follow TikTok/YouTube/Instagram content policies

## 🙏 Acknowledgments

- **Ollama** - Local LLM inference
- **DuckDuckGo** - Safe image search
- **FFmpeg** - Video processing
- **OpenCV** - Computer vision and video rendering

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check [PRODUCTION_READY.md](PRODUCTION_READY.md) for technical details
- Review [UPLOAD_WORKFLOW.md](UPLOAD_WORKFLOW.md) for publishing workflow

---

**Made with ❤️ by the Story Video Generator team**

*Generate viral content automatically. Let AI tell the stories.*

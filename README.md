# GitHub Wrapped

Generate Spotify Wrapped-style videos for any GitHub repository. Visualize your year in code with animated stats, charts, AI narration, and background music.

## Features

- Animated count-up numbers
- Bar chart animations for monthly commits
- Leaderboard reveals for top contributors
- ElevenLabs AI voice narration
- Background music with automatic ducking
- Vertical video format (1080x1920) perfect for social media
- Works on any GitHub repository

## Installation

```bash
git clone https://github.com/VolksRat71/github-wrapped.git
cd github-wrapped
pip install -r requirements.txt
```

## Configuration

Create a `.env` file with your API keys:

```bash
cp .env.example .env
```

```env
ELEVENLABS_API_KEY=your_key_here  # Optional - for AI narration
OPENAI_API_KEY=your_key_here      # Optional - for future features
```

## Usage

### Basic (no audio)
```bash
python main.py /path/to/your/repo --no-audio
```

### With background music
```bash
python main.py /path/to/your/repo --no-audio --music a-green-night-129736.mp3
```

### With AI narration + music (requires ElevenLabs API key)
```bash
python main.py /path/to/your/repo --music a-green-night-129736.mp3
```

### Options

| Flag | Description |
|------|-------------|
| `--year`, `-y` | Year to generate wrapped for (default: current year) |
| `--no-audio` | Skip AI voice narration |
| `--music`, `-m` | Background music file from assets/music/ |
| `--music-url` | Download music from URL |
| `--voice`, `-v` | ElevenLabs voice ID |
| `--output`, `-o` | Output filename (without extension) |
| `--static` | Use static slides instead of animations |
| `--gif` | Also generate a GIF preview |

### Other Commands

```bash
# List available music tracks
python main.py list-music

# Get royalty-free music sources
python main.py music-help

# List available ElevenLabs voices
python main.py list-voices
```

## Built-in Music

The following royalty-free tracks from [Pixabay](https://pixabay.com/music/) are included:

| Track | Vibe |
|-------|------|
| `a-green-night-129736.mp3` | EDM / Electronic (Spotify Wrapped style) |
| `upbeat-joy-351367.mp3` | Upbeat / Happy |
| `upbeat-rock-136977.mp3` | Upbeat / Rock |

All music is licensed under the [Pixabay License](https://pixabay.com/service/license-summary/) - free for commercial use, no attribution required.

## Stats Collected

- Total commits
- Total PRs merged
- Total releases
- Lines added/deleted
- Top contributors
- Busiest day of week
- Busiest month
- Peak coding hours
- Weekend commits
- Commits by month chart

## Output

Videos are saved to `output/` directory:
- `wrapped.mp4` - Main video (1080x1920)
- `wrapped_preview.gif` - GIF preview (optional)

## Requirements

- Python 3.8+
- `gh` CLI (for full PR stats - falls back to git log if unavailable)
- ffmpeg (installed via moviepy)

## License

MIT

## Credits

- Music from [Pixabay](https://pixabay.com/music/)
- AI narration by [ElevenLabs](https://elevenlabs.io/)

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

    OUTPUT_DIR = "output"
    TEMP_DIR = "output/temp"

    # Video settings
    VIDEO_WIDTH = 1080
    VIDEO_HEIGHT = 1920  # Vertical format like stories
    FPS = 30

    # Slide settings
    SLIDE_DURATION = 5  # seconds per slide
    TRANSITION_DURATION = 0.5

    # Colors (dark theme like Spotify)
    BG_COLOR = "#121212"
    PRIMARY_COLOR = "#1DB954"  # Spotify green vibes
    TEXT_COLOR = "#FFFFFF"
    SECONDARY_TEXT = "#B3B3B3"
    ACCENT_COLORS = ["#1DB954", "#1ED760", "#169C46", "#14833B"]

    # ElevenLabs settings
    VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel - good for narration

    @classmethod
    def ensure_dirs(cls):
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
        os.makedirs(cls.TEMP_DIR, exist_ok=True)

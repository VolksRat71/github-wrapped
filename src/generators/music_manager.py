import os
import requests
from typing import List, Optional, Dict
from ..utils.config import Config


# Curated list of royalty-free music URLs that work well for wrapped videos
# These are direct download links from free sources
BUILTIN_TRACKS = {
    "upbeat": {
        "name": "Upbeat & Energetic",
        "description": "Perfect for celebrating achievements",
        "url": None,  # User provides their own
    },
    "chill": {
        "name": "Chill & Relaxed",
        "description": "Laid back vibe for stats review",
        "url": None,
    },
    "epic": {
        "name": "Epic & Cinematic",
        "description": "Dramatic reveal of your year",
        "url": None,
    },
    "electronic": {
        "name": "Electronic & Modern",
        "description": "Tech-forward energy",
        "url": None,
    },
}


class MusicManager:
    """Manage background music for wrapped videos."""

    def __init__(self):
        Config.ensure_dirs()
        self.music_dir = os.path.join(Config.OUTPUT_DIR, "music")
        os.makedirs(self.music_dir, exist_ok=True)

    def list_available_tracks(self) -> List[Dict]:
        """List available music tracks."""
        tracks = []

        # Check for local files in music directory
        if os.path.exists(self.music_dir):
            for f in os.listdir(self.music_dir):
                if f.endswith(('.mp3', '.wav', '.m4a', '.ogg')):
                    tracks.append({
                        "id": f,
                        "name": os.path.splitext(f)[0],
                        "path": os.path.join(self.music_dir, f),
                        "source": "local",
                    })

        return tracks

    def get_track_path(self, track_id: str) -> Optional[str]:
        """Get the local path for a track."""
        # Check if it's a local file
        local_path = os.path.join(self.music_dir, track_id)
        if os.path.exists(local_path):
            return local_path

        # Check with common extensions
        for ext in ['.mp3', '.wav', '.m4a', '.ogg']:
            path = os.path.join(self.music_dir, f"{track_id}{ext}")
            if os.path.exists(path):
                return path

        return None

    def download_from_url(self, url: str, filename: str) -> Optional[str]:
        """Download a music file from URL."""
        try:
            print(f"  Downloading music from {url}...")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            # Determine extension from content type or URL
            ext = ".mp3"
            if "audio/wav" in response.headers.get("content-type", ""):
                ext = ".wav"
            elif url.endswith(".wav"):
                ext = ".wav"

            filepath = os.path.join(self.music_dir, f"{filename}{ext}")

            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"  Downloaded to {filepath}")
            return filepath
        except Exception as e:
            print(f"  Error downloading music: {e}")
            return None

    @staticmethod
    def get_royalty_free_sources() -> str:
        """Return info about where to get royalty-free music."""
        return """
Royalty-Free Music Sources (No Attribution Required):
=====================================================

1. PIXABAY MUSIC (Recommended)
   https://pixabay.com/music/
   - 100% free for commercial use
   - No attribution required
   - Search for: "upbeat", "corporate", "inspiring"

2. MIXKIT
   https://mixkit.co/free-stock-music/
   - Free for commercial use
   - No attribution required

3. UPPBEAT
   https://uppbeat.io/
   - Free tier available
   - Great for social media

4. BENSOUND
   https://www.bensound.com/
   - Some free tracks available
   - Check license for each track

How to use:
-----------
1. Download an MP3 from any source above
2. Place it in: output/music/
3. Run with: --music your_track.mp3

Or provide a direct URL:
   --music-url https://example.com/track.mp3
"""

    def suggest_tracks_for_mood(self, mood: str) -> List[str]:
        """Suggest search terms for different moods."""
        moods = {
            "celebratory": ["upbeat corporate", "success", "achievement", "celebration"],
            "professional": ["corporate", "business", "tech", "modern"],
            "energetic": ["energetic", "driving", "powerful", "dynamic"],
            "chill": ["lo-fi", "ambient", "relaxed", "calm"],
            "epic": ["cinematic", "epic", "dramatic", "orchestral"],
        }
        return moods.get(mood.lower(), ["upbeat", "corporate"])

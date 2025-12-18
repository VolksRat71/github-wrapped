import os
from typing import List, Optional
from elevenlabs import ElevenLabs
from ..utils.config import Config
from .slide_generator import Slide


class AudioGenerator:
    def __init__(self, voice_id: Optional[str] = None):
        self.client = None
        if Config.ELEVENLABS_API_KEY:
            self.client = ElevenLabs(api_key=Config.ELEVENLABS_API_KEY)
        self.voice_id = voice_id or Config.VOICE_ID
        Config.ensure_dirs()

    def generate_audio_for_slides(self, slides: List[Slide]) -> List[str]:
        """Generate audio narration for each slide."""
        audio_paths = []

        if not self.client:
            print("Warning: No ElevenLabs API key found. Skipping audio generation.")
            return audio_paths

        for i, slide in enumerate(slides):
            print(f"  Generating audio for slide {i + 1}/{len(slides)}...")
            audio_path = self._generate_audio(slide.narration, i)
            audio_paths.append(audio_path)

        return audio_paths

    def _generate_audio(self, text: str, index: int) -> str:
        """Generate audio for a single narration."""
        try:
            audio = self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                text=text,
                model_id="eleven_turbo_v2",
                output_format="mp3_44100_128",
            )

            path = os.path.join(Config.TEMP_DIR, f"audio_{index:02d}.mp3")

            # The API returns a generator, so we need to write it properly
            with open(path, "wb") as f:
                for chunk in audio:
                    f.write(chunk)

            return path
        except Exception as e:
            print(f"    Warning: Failed to generate audio: {e}")
            return ""

    def generate_full_narration(self, slides: List[Slide]) -> str:
        """Generate a single audio file with all narrations."""
        if not self.client:
            print("Warning: No ElevenLabs API key found. Skipping audio generation.")
            return ""

        # Combine all narrations with pauses
        full_text = " ... ".join([slide.narration for slide in slides])

        print("Generating full narration audio...")
        try:
            audio = self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                text=full_text,
                model_id="eleven_turbo_v2",
                output_format="mp3_44100_128",
            )

            path = os.path.join(Config.TEMP_DIR, "full_narration.mp3")

            with open(path, "wb") as f:
                for chunk in audio:
                    f.write(chunk)

            return path
        except Exception as e:
            print(f"Warning: Failed to generate full narration: {e}")
            return ""

    @staticmethod
    def list_voices():
        """List available voices from ElevenLabs."""
        if not Config.ELEVENLABS_API_KEY:
            print("No ElevenLabs API key found.")
            return []

        client = ElevenLabs(api_key=Config.ELEVENLABS_API_KEY)
        voices = client.voices.get_all()
        return voices

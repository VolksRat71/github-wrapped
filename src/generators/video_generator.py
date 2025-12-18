import os
from typing import List, Optional
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    concatenate_videoclips,
    CompositeVideoClip,
    ColorClip,
)
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
from ..utils.config import Config
from .slide_generator import Slide


class VideoGenerator:
    def __init__(self):
        Config.ensure_dirs()
        self.width = Config.VIDEO_WIDTH
        self.height = Config.VIDEO_HEIGHT
        self.fps = Config.FPS

    def create_video(
        self,
        slides: List[Slide],
        audio_paths: Optional[List[str]] = None,
        output_name: str = "wrapped",
    ) -> str:
        """Create the final wrapped video from slides and audio."""
        print("Creating video...")

        clips = []
        for i, slide in enumerate(slides):
            print(f"  Processing slide {i + 1}/{len(slides)}...")

            # Create image clip
            img_clip = ImageClip(slide.image_path).set_duration(slide.duration)
            img_clip = img_clip.resize((self.width, self.height))

            # Add fade effects
            img_clip = fadein(img_clip, 0.5)
            img_clip = fadeout(img_clip, 0.5)

            # Add audio if available
            if audio_paths and i < len(audio_paths) and audio_paths[i]:
                try:
                    audio = AudioFileClip(audio_paths[i])
                    # Adjust slide duration to match audio if audio is longer
                    if audio.duration > slide.duration:
                        img_clip = img_clip.set_duration(audio.duration + 1)
                    img_clip = img_clip.set_audio(audio)
                except Exception as e:
                    print(f"    Warning: Could not add audio: {e}")

            clips.append(img_clip)

        # Concatenate all clips
        print("  Concatenating clips...")
        final = concatenate_videoclips(clips, method="compose")

        # Write output
        output_path = os.path.join(Config.OUTPUT_DIR, f"{output_name}.mp4")
        print(f"  Writing video to {output_path}...")

        final.write_videofile(
            output_path,
            fps=self.fps,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            preset="medium",
            verbose=False,
            logger=None,
        )

        # Cleanup
        final.close()
        for clip in clips:
            clip.close()

        print(f"Video created: {output_path}")
        return output_path

    def create_video_no_audio(
        self,
        slides: List[Slide],
        output_name: str = "wrapped_silent",
    ) -> str:
        """Create video without audio (for testing or if no API key)."""
        print("Creating silent video...")

        clips = []
        for i, slide in enumerate(slides):
            print(f"  Processing slide {i + 1}/{len(slides)}...")

            img_clip = ImageClip(slide.image_path).set_duration(slide.duration)
            img_clip = img_clip.resize((self.width, self.height))
            img_clip = fadein(img_clip, 0.5)
            img_clip = fadeout(img_clip, 0.5)

            clips.append(img_clip)

        print("  Concatenating clips...")
        final = concatenate_videoclips(clips, method="compose")

        output_path = os.path.join(Config.OUTPUT_DIR, f"{output_name}.mp4")
        print(f"  Writing video to {output_path}...")

        final.write_videofile(
            output_path,
            fps=self.fps,
            codec="libx264",
            threads=4,
            preset="medium",
            verbose=False,
            logger=None,
        )

        final.close()
        for clip in clips:
            clip.close()

        print(f"Video created: {output_path}")
        return output_path

    def create_gif_preview(
        self,
        slides: List[Slide],
        output_name: str = "wrapped_preview",
        duration_per_slide: float = 2.0,
    ) -> str:
        """Create a GIF preview of the wrapped video."""
        print("Creating GIF preview...")

        clips = []
        for i, slide in enumerate(slides):
            img_clip = ImageClip(slide.image_path).set_duration(duration_per_slide)
            # Resize for GIF (smaller)
            img_clip = img_clip.resize((540, 960))
            clips.append(img_clip)

        final = concatenate_videoclips(clips, method="compose")

        output_path = os.path.join(Config.OUTPUT_DIR, f"{output_name}.gif")
        print(f"  Writing GIF to {output_path}...")

        final.write_gif(output_path, fps=10, verbose=False, logger=None)

        final.close()
        for clip in clips:
            clip.close()

        print(f"GIF created: {output_path}")
        return output_path

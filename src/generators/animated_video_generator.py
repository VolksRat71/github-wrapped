import os
import math
from typing import List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
    CompositeAudioClip,
    concatenate_videoclips,
    ColorClip,
    TextClip,
    VideoClip,
)
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
from moviepy.audio.fx.audio_fadeout import audio_fadeout
from moviepy.audio.fx.audio_fadein import audio_fadein
from moviepy.audio.fx.volumex import volumex

from ..utils.config import Config
from ..collectors.github_collector import RepoStats


class AnimatedVideoGenerator:
    def __init__(self, stats: RepoStats):
        self.stats = stats
        self.width = Config.VIDEO_WIDTH
        self.height = Config.VIDEO_HEIGHT
        self.fps = Config.FPS
        Config.ensure_dirs()

        # Colors
        self.bg_color = self._hex_to_rgb(Config.BG_COLOR)
        self.primary_color = Config.PRIMARY_COLOR
        self.text_color = Config.TEXT_COLOR
        self.secondary_color = Config.SECONDARY_TEXT

        # Try to find a good font
        self.font_path = self._find_font()

    def _find_font(self) -> str:
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/SFNSDisplay.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        for path in font_paths:
            if os.path.exists(path):
                return path
        return None

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _create_gradient_frame(self, color1: str, color2: str) -> np.ndarray:
        """Create a gradient background as numpy array."""
        r1, g1, b1 = self._hex_to_rgb(color1)
        r2, g2, b2 = self._hex_to_rgb(color2)

        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        for y in range(self.height):
            ratio = y / self.height
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            frame[y, :] = [r, g, b]
        return frame

    def _ease_out_cubic(self, t: float) -> float:
        """Easing function for smooth animations."""
        return 1 - pow(1 - t, 3)

    def _ease_out_elastic(self, t: float) -> float:
        """Elastic easing for bouncy number reveals."""
        if t == 0 or t == 1:
            return t
        return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi) / 3) + 1

    def create_animated_video(
        self,
        audio_paths: Optional[List[str]] = None,
        music_path: Optional[str] = None,
        output_name: str = "wrapped_animated",
    ) -> str:
        """Create the full animated wrapped video."""
        print("Creating animated video...")

        clips = []

        # Slide 1: Intro with fade-in text
        clips.append(self._create_intro_clip())

        # Slide 2: Commits with count-up
        clips.append(self._create_countup_clip(
            "TOTAL COMMITS",
            self.stats.total_commits,
            f"across {self.stats.days_with_commits} different days",
            "#1a1a2e", "#0f0f23"
        ))

        # Slide 3: PRs
        clips.append(self._create_countup_clip(
            "PULL REQUESTS MERGED",
            self.stats.total_prs,
            self._get_biggest_pr_text(),
            "#0f0f23", "#0f3460"
        ))

        # Slide 4: Contributors reveal
        clips.append(self._create_leaderboard_clip())

        # Slide 5: When you coded
        clips.append(self._create_times_clip())

        # Slide 6: Lines of code
        clips.append(self._create_lines_clip())

        # Slide 7: Releases
        clips.append(self._create_countup_clip(
            "RELEASES SHIPPED",
            self.stats.total_releases,
            f"From {self.stats.first_release} to {self.stats.last_release}" if self.stats.first_release else "",
            "#16213e", "#1a1a2e"
        ))

        # Slide 8: Activity chart animated
        clips.append(self._create_chart_clip())

        # Slide 9: Outro
        clips.append(self._create_outro_clip())

        # Concatenate all clips
        print("  Concatenating clips...")
        final_video = concatenate_videoclips(clips, method="compose")

        # Add audio if available
        audio_clips = []

        # Add narration audio if provided
        if audio_paths:
            current_time = 0
            for i, (clip, audio_path) in enumerate(zip(clips, audio_paths)):
                if audio_path and os.path.exists(audio_path):
                    try:
                        narration = AudioFileClip(audio_path).set_start(current_time + 0.5)
                        audio_clips.append(narration)
                    except Exception as e:
                        print(f"  Warning: Could not load audio {i}: {e}")
                current_time += clip.duration

        # Add background music if provided
        if music_path and os.path.exists(music_path):
            try:
                music = AudioFileClip(music_path)
                # Loop music if needed
                if music.duration < final_video.duration:
                    loops_needed = int(final_video.duration / music.duration) + 1
                    music = concatenate_videoclips([music] * loops_needed).subclip(0, final_video.duration)
                else:
                    music = music.subclip(0, final_video.duration)

                # Lower volume and add fade
                music = volumex(music, 0.3)  # 30% volume for background
                music = audio_fadein(music, 2)
                music = audio_fadeout(music, 3)

                # If we have narration, duck the music
                if audio_clips:
                    music = volumex(music, 0.5)  # Further reduce when narration exists

                audio_clips.insert(0, music)  # Music goes first (background)
            except Exception as e:
                print(f"  Warning: Could not load music: {e}")

        # Combine audio
        if audio_clips:
            final_audio = CompositeAudioClip(audio_clips)
            final_video = final_video.set_audio(final_audio)

        # Write output
        output_path = os.path.join(Config.OUTPUT_DIR, f"{output_name}.mp4")
        print(f"  Writing video to {output_path}...")

        final_video.write_videofile(
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
        final_video.close()
        for clip in clips:
            clip.close()

        print(f"Video created: {output_path}")
        return output_path

    def _get_biggest_pr_text(self) -> str:
        if self.stats.biggest_prs:
            biggest = self.stats.biggest_prs[0]
            title = biggest["title"][:35] + "..." if len(biggest["title"]) > 35 else biggest["title"]
            return f"Biggest: {title}"
        return ""

    def _create_intro_clip(self, duration: float = 5.0) -> VideoClip:
        """Create animated intro with text flying in."""
        gradient = self._create_gradient_frame("#1a1a2e", "#16213e")

        repo_name = self.stats.repo_name.split("/")[-1] if "/" in self.stats.repo_name else self.stats.repo_name

        # Center point for vertical video
        center_y = self.height // 2

        def make_frame(t):
            frame = gradient.copy()
            img = Image.fromarray(frame)
            draw = ImageDraw.Draw(img)

            # Year animation - scale up and settle
            progress = min(t / 1.5, 1.0)
            eased = self._ease_out_cubic(progress)

            year_size = int(120 + 80 * eased)

            try:
                font = ImageFont.truetype(self.font_path, year_size) if self.font_path else ImageFont.load_default()
            except:
                font = ImageFont.load_default()

            year_text = str(self.stats.year)
            bbox = draw.textbbox((0, 0), year_text, font=font)
            x = (self.width - (bbox[2] - bbox[0])) // 2
            y = center_y - 200 + int(50 * (1 - eased))  # Centered vertically

            draw.text((x, y), year_text, font=font, fill=self._hex_to_rgb(self.primary_color))

            # Repo name - fade in after year settles
            if t > 1.0:
                name_progress = min((t - 1.0) / 1.0, 1.0)
                name_eased = self._ease_out_cubic(name_progress)

                try:
                    name_font = ImageFont.truetype(self.font_path, 64) if self.font_path else ImageFont.load_default()
                except:
                    name_font = ImageFont.load_default()

                bbox = draw.textbbox((0, 0), repo_name.upper(), font=name_font)
                x = (self.width - (bbox[2] - bbox[0])) // 2
                y = center_y + 50

                y_offset = int(30 * (1 - name_eased))
                draw.text((x, y + y_offset), repo_name.upper(), font=name_font, fill=self._hex_to_rgb(self.text_color))

            # "WRAPPED" text
            if t > 1.5:
                wrapped_progress = min((t - 1.5) / 0.8, 1.0)
                wrapped_eased = self._ease_out_cubic(wrapped_progress)

                try:
                    wrapped_font = ImageFont.truetype(self.font_path, 50) if self.font_path else ImageFont.load_default()
                except:
                    wrapped_font = ImageFont.load_default()

                bbox = draw.textbbox((0, 0), "WRAPPED", font=wrapped_font)
                x = (self.width - (bbox[2] - bbox[0])) // 2
                y = center_y + 140 + int(20 * (1 - wrapped_eased))
                draw.text((x, y), "WRAPPED", font=wrapped_font, fill=self._hex_to_rgb(self.secondary_color))

            return np.array(img)

        clip = VideoClip(make_frame, duration=duration)
        clip = clip.set_fps(self.fps)
        return fadeout(clip, 0.5)

    def _create_countup_clip(
        self,
        title: str,
        number: int,
        subtitle: str,
        color1: str,
        color2: str,
        duration: float = 5.0
    ) -> VideoClip:
        """Create a clip with animated count-up number."""
        gradient = self._create_gradient_frame(color1, color2)
        center_y = self.height // 2

        def make_frame(t):
            frame = gradient.copy()
            img = Image.fromarray(frame)
            draw = ImageDraw.Draw(img)

            try:
                title_font = ImageFont.truetype(self.font_path, 38) if self.font_path else ImageFont.load_default()
                number_font = ImageFont.truetype(self.font_path, 140) if self.font_path else ImageFont.load_default()
                sub_font = ImageFont.truetype(self.font_path, 36) if self.font_path else ImageFont.load_default()
            except:
                title_font = number_font = sub_font = ImageFont.load_default()

            # Title - centered above number
            bbox = draw.textbbox((0, 0), title, font=title_font)
            x = (self.width - (bbox[2] - bbox[0])) // 2
            draw.text((x, center_y - 200), title, font=title_font, fill=self._hex_to_rgb(self.secondary_color))

            # Animated number count-up
            if t > 0.3:
                count_progress = min((t - 0.3) / 2.0, 1.0)
                eased = self._ease_out_cubic(count_progress)
                current_number = int(number * eased)

                num_text = f"{current_number:,}"
                bbox = draw.textbbox((0, 0), num_text, font=number_font)
                x = (self.width - (bbox[2] - bbox[0])) // 2

                # Centered vertically with bounce
                y = center_y - 80
                if count_progress > 0.95:
                    bounce = math.sin((count_progress - 0.95) * 20 * math.pi) * 5
                    y += int(bounce)

                draw.text((x, y), num_text, font=number_font, fill=self._hex_to_rgb(self.primary_color))

            # Subtitle - centered below number
            if t > 2.5 and subtitle:
                sub_progress = min((t - 2.5) / 0.8, 1.0)
                bbox = draw.textbbox((0, 0), subtitle, font=sub_font)
                x = (self.width - (bbox[2] - bbox[0])) // 2
                y = center_y + 120 + int(20 * (1 - sub_progress))
                draw.text((x, y), subtitle, font=sub_font, fill=self._hex_to_rgb(self.text_color))

            return np.array(img)

        clip = VideoClip(make_frame, duration=duration)
        clip = clip.set_fps(self.fps)
        return fadein(fadeout(clip, 0.5), 0.3)

    def _create_leaderboard_clip(self, duration: float = 7.0) -> VideoClip:
        """Create animated leaderboard reveal."""
        gradient = self._create_gradient_frame("#16213e", "#1a1a2e")

        contributors = self.stats.top_contributors[:5]
        center_y = self.height // 2

        def make_frame(t):
            frame = gradient.copy()
            img = Image.fromarray(frame)
            draw = ImageDraw.Draw(img)

            try:
                title_font = ImageFont.truetype(self.font_path, 38) if self.font_path else ImageFont.load_default()
                name_font = ImageFont.truetype(self.font_path, 40) if self.font_path else ImageFont.load_default()
                count_font = ImageFont.truetype(self.font_path, 32) if self.font_path else ImageFont.load_default()
            except:
                title_font = name_font = count_font = ImageFont.load_default()

            # Title - centered
            title = "TOP CONTRIBUTORS"
            bbox = draw.textbbox((0, 0), title, font=title_font)
            x = (self.width - (bbox[2] - bbox[0])) // 2
            draw.text((x, center_y - 350), title, font=title_font, fill=self._hex_to_rgb(self.secondary_color))

            # Reveal each contributor one by one - centered
            medals = ["1st", "2nd", "3rd", "4th", "5th"]
            row_height = 90
            total_height = len(contributors) * row_height
            start_y = center_y - (total_height // 2) + 50

            for i, contrib in enumerate(contributors):
                row_start = 0.8 + (i * 0.5)

                if t > row_start:
                    row_progress = min((t - row_start) / 0.4, 1.0)
                    eased = self._ease_out_cubic(row_progress)

                    y = start_y + (i * row_height)
                    x_offset = int(50 * (1 - eased))

                    medal = medals[i] if i < len(medals) else f"{i+1}th"
                    name = contrib["name"]
                    commits = contrib["commits"]

                    # Medal and name - left aligned with padding
                    text = f"{medal}  {name}"
                    draw.text((120 + x_offset, y), text, font=name_font, fill=self._hex_to_rgb(self.text_color))

                    # Commits count (slide in from right)
                    commits_text = f"{commits}"
                    bbox = draw.textbbox((0, 0), commits_text, font=count_font)
                    right_x = self.width - 120 - (bbox[2] - bbox[0]) - int(50 * (1 - eased))
                    draw.text((right_x, y + 5), commits_text, font=count_font, fill=self._hex_to_rgb(self.primary_color))

            return np.array(img)

        clip = VideoClip(make_frame, duration=duration)
        clip = clip.set_fps(self.fps)
        return fadein(fadeout(clip, 0.5), 0.3)

    def _create_times_clip(self, duration: float = 6.0) -> VideoClip:
        """Create animated 'when you coded' clip."""
        gradient = self._create_gradient_frame("#1a1a2e", "#0f0f23")
        center_y = self.height // 2

        def make_frame(t):
            frame = gradient.copy()
            img = Image.fromarray(frame)
            draw = ImageDraw.Draw(img)

            try:
                title_font = ImageFont.truetype(self.font_path, 36) if self.font_path else ImageFont.load_default()
                label_font = ImageFont.truetype(self.font_path, 28) if self.font_path else ImageFont.load_default()
                value_font = ImageFont.truetype(self.font_path, 52) if self.font_path else ImageFont.load_default()
            except:
                title_font = label_font = value_font = ImageFont.load_default()

            # Title - centered
            title = "WHEN YOU CODED"
            bbox = draw.textbbox((0, 0), title, font=title_font)
            x = (self.width - (bbox[2] - bbox[0])) // 2
            draw.text((x, center_y - 400), title, font=title_font, fill=self._hex_to_rgb(self.secondary_color))

            items = [
                ("Busiest Day", self.stats.busiest_day.upper(), 0.5),
                ("Busiest Month", self.stats.busiest_month.upper(), 1.2),
                ("Peak Hour", f"{self.stats.peak_hour}:00", 1.9),
                ("Weekend Commits", str(self.stats.weekend_commits), 2.6),
            ]

            # Center items vertically
            item_height = 160
            total_height = len(items) * item_height
            start_y = center_y - (total_height // 2) + 50

            for i, (label, value, start_time) in enumerate(items):
                if t > start_time:
                    progress = min((t - start_time) / 0.5, 1.0)
                    eased = self._ease_out_cubic(progress)

                    y = start_y + (i * item_height)

                    # Label
                    bbox = draw.textbbox((0, 0), label, font=label_font)
                    x = (self.width - (bbox[2] - bbox[0])) // 2
                    draw.text((x, y), label, font=label_font, fill=self._hex_to_rgb(self.secondary_color))

                    # Value
                    bbox = draw.textbbox((0, 0), value, font=value_font)
                    x = (self.width - (bbox[2] - bbox[0])) // 2
                    y_offset = int(15 * (1 - eased))

                    color = self.primary_color if i % 2 == 0 else self.text_color
                    draw.text((x, y + 45 + y_offset), value, font=value_font, fill=self._hex_to_rgb(color))

            return np.array(img)

        clip = VideoClip(make_frame, duration=duration)
        clip = clip.set_fps(self.fps)
        return fadein(fadeout(clip, 0.5), 0.3)

    def _create_lines_clip(self, duration: float = 6.0) -> VideoClip:
        """Create animated lines of code clip with count-up."""
        gradient = self._create_gradient_frame("#0f3460", "#1a1a2e")
        center_y = self.height // 2

        def make_frame(t):
            frame = gradient.copy()
            img = Image.fromarray(frame)
            draw = ImageDraw.Draw(img)

            try:
                title_font = ImageFont.truetype(self.font_path, 36) if self.font_path else ImageFont.load_default()
                number_font = ImageFont.truetype(self.font_path, 60) if self.font_path else ImageFont.load_default()
                label_font = ImageFont.truetype(self.font_path, 28) if self.font_path else ImageFont.load_default()
            except:
                title_font = number_font = label_font = ImageFont.load_default()

            # Title - centered
            title = "LINES OF CODE"
            bbox = draw.textbbox((0, 0), title, font=title_font)
            x = (self.width - (bbox[2] - bbox[0])) // 2
            draw.text((x, center_y - 350), title, font=title_font, fill=self._hex_to_rgb(self.secondary_color))

            # Added - green, count up
            if t > 0.5:
                progress = min((t - 0.5) / 1.5, 1.0)
                eased = self._ease_out_cubic(progress)
                current = int(self.stats.lines_added * eased)

                text = f"+{current:,}"
                bbox = draw.textbbox((0, 0), text, font=number_font)
                x = (self.width - (bbox[2] - bbox[0])) // 2
                draw.text((x, center_y - 220), text, font=number_font, fill=(29, 185, 84))

                bbox = draw.textbbox((0, 0), "lines added", font=label_font)
                x = (self.width - (bbox[2] - bbox[0])) // 2
                draw.text((x, center_y - 140), "lines added", font=label_font, fill=self._hex_to_rgb(self.secondary_color))

            # Deleted - red, count up
            if t > 1.5:
                progress = min((t - 1.5) / 1.5, 1.0)
                eased = self._ease_out_cubic(progress)
                current = int(self.stats.lines_deleted * eased)

                text = f"-{current:,}"
                bbox = draw.textbbox((0, 0), text, font=number_font)
                x = (self.width - (bbox[2] - bbox[0])) // 2
                draw.text((x, center_y - 40), text, font=number_font, fill=(231, 76, 60))

                bbox = draw.textbbox((0, 0), "lines deleted", font=label_font)
                x = (self.width - (bbox[2] - bbox[0])) // 2
                draw.text((x, center_y + 40), "lines deleted", font=label_font, fill=self._hex_to_rgb(self.secondary_color))

            # Net change
            if t > 3.0:
                progress = min((t - 3.0) / 0.8, 1.0)
                eased = self._ease_out_cubic(progress)

                net = self.stats.lines_added - self.stats.lines_deleted
                net_text = f"+{net:,}" if net >= 0 else f"{net:,}"
                net_color = (29, 185, 84) if net >= 0 else (231, 76, 60)

                bbox = draw.textbbox((0, 0), "Net change", font=label_font)
                x = (self.width - (bbox[2] - bbox[0])) // 2
                y_offset = int(20 * (1 - eased))
                draw.text((x, center_y + 140 + y_offset), "Net change", font=label_font, fill=self._hex_to_rgb(self.secondary_color))

                bbox = draw.textbbox((0, 0), net_text, font=number_font)
                x = (self.width - (bbox[2] - bbox[0])) // 2
                draw.text((x, center_y + 200 + y_offset), net_text, font=number_font, fill=net_color)

            return np.array(img)

        clip = VideoClip(make_frame, duration=duration)
        clip = clip.set_fps(self.fps)
        return fadein(fadeout(clip, 0.5), 0.3)

    def _create_chart_clip(self, duration: float = 7.0) -> VideoClip:
        """Create animated bar chart."""
        gradient = self._create_gradient_frame("#121212", "#1a1a2e")
        center_y = self.height // 2

        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        month_full = ["January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"]
        values = [self.stats.commits_by_month.get(m, 0) for m in month_full]
        max_val = max(values) if values else 1

        def make_frame(t):
            frame = gradient.copy()
            img = Image.fromarray(frame)
            draw = ImageDraw.Draw(img)

            try:
                title_font = ImageFont.truetype(self.font_path, 36) if self.font_path else ImageFont.load_default()
                label_font = ImageFont.truetype(self.font_path, 22) if self.font_path else ImageFont.load_default()
                value_font = ImageFont.truetype(self.font_path, 18) if self.font_path else ImageFont.load_default()
            except:
                title_font = label_font = value_font = ImageFont.load_default()

            # Title - centered
            title = "COMMITS BY MONTH"
            bbox = draw.textbbox((0, 0), title, font=title_font)
            x = (self.width - (bbox[2] - bbox[0])) // 2
            draw.text((x, center_y - 500), title, font=title_font, fill=self._hex_to_rgb(self.text_color))

            # Chart area - centered
            chart_width = self.width - 160
            chart_height = 800
            chart_left = 80
            chart_top = center_y - 350
            chart_bottom = chart_top + chart_height

            bar_width = chart_width // 14
            bar_spacing = (chart_width - (bar_width * 12)) // 13

            # Animate bars growing
            for i, (month, val) in enumerate(zip(months, values)):
                bar_start = 0.5 + (i * 0.15)

                if t > bar_start:
                    progress = min((t - bar_start) / 1.0, 1.0)
                    eased = self._ease_out_cubic(progress)

                    bar_height = int((val / max_val) * (chart_height - 80) * eased) if max_val > 0 else 0

                    x = chart_left + (i * (bar_width + bar_spacing)) + bar_spacing
                    y = chart_bottom - bar_height

                    # Draw bar
                    draw.rectangle(
                        [x, y, x + bar_width, chart_bottom],
                        fill=self._hex_to_rgb(self.primary_color)
                    )

                    # Month label
                    bbox = draw.textbbox((0, 0), month, font=label_font)
                    label_x = x + (bar_width - (bbox[2] - bbox[0])) // 2
                    draw.text((label_x, chart_bottom + 12), month, font=label_font, fill=self._hex_to_rgb(self.secondary_color))

                    # Value on top of bar
                    if progress > 0.8 and val > 0:
                        val_text = str(val)
                        bbox = draw.textbbox((0, 0), val_text, font=value_font)
                        val_x = x + (bar_width - (bbox[2] - bbox[0])) // 2
                        draw.text((val_x, y - 28), val_text, font=value_font, fill=self._hex_to_rgb(self.text_color))

            return np.array(img)

        clip = VideoClip(make_frame, duration=duration)
        clip = clip.set_fps(self.fps)
        return fadein(fadeout(clip, 0.5), 0.3)

    def _create_outro_clip(self, duration: float = 6.0) -> VideoClip:
        """Create animated outro with summary."""
        gradient = self._create_gradient_frame("#16213e", "#1a1a2e")
        center_y = self.height // 2

        def make_frame(t):
            frame = gradient.copy()
            img = Image.fromarray(frame)
            draw = ImageDraw.Draw(img)

            try:
                title_font = ImageFont.truetype(self.font_path, 56) if self.font_path else ImageFont.load_default()
                year_font = ImageFont.truetype(self.font_path, 130) if self.font_path else ImageFont.load_default()
                stat_font = ImageFont.truetype(self.font_path, 38) if self.font_path else ImageFont.load_default()
                footer_font = ImageFont.truetype(self.font_path, 32) if self.font_path else ImageFont.load_default()
            except:
                title_font = year_font = stat_font = footer_font = ImageFont.load_default()

            # "THAT'S A WRAP" - centered
            if t > 0.3:
                progress = min((t - 0.3) / 0.8, 1.0)
                eased = self._ease_out_cubic(progress)

                title = "THAT'S A WRAP"
                bbox = draw.textbbox((0, 0), title, font=title_font)
                x = (self.width - (bbox[2] - bbox[0])) // 2
                y = center_y - 300 + int(30 * (1 - eased))
                draw.text((x, y), title, font=title_font, fill=self._hex_to_rgb(self.text_color))

            # Year with pop effect - centered
            if t > 0.8:
                progress = min((t - 0.8) / 0.6, 1.0)
                eased = self._ease_out_elastic(progress)

                year = str(self.stats.year)
                bbox = draw.textbbox((0, 0), year, font=year_font)
                x = (self.width - (bbox[2] - bbox[0])) // 2
                draw.text((x, center_y - 180), year, font=year_font, fill=self._hex_to_rgb(self.primary_color))

            # Summary stats - centered
            stats = [
                f"{self.stats.total_commits:,} commits",
                f"{self.stats.total_prs} PRs merged",
                f"{self.stats.total_releases} releases",
            ]

            for i, stat in enumerate(stats):
                stat_start = 1.8 + (i * 0.4)
                if t > stat_start:
                    progress = min((t - stat_start) / 0.4, 1.0)
                    eased = self._ease_out_cubic(progress)

                    bbox = draw.textbbox((0, 0), stat, font=stat_font)
                    x = (self.width - (bbox[2] - bbox[0])) // 2
                    y = center_y + 30 + (i * 60) + int(20 * (1 - eased))
                    draw.text((x, y), stat, font=stat_font, fill=self._hex_to_rgb(self.text_color))

            # Footer - centered
            if t > 3.5:
                progress = min((t - 3.5) / 0.6, 1.0)

                footer = f"Here's to shipping more in {self.stats.year + 1}"
                bbox = draw.textbbox((0, 0), footer, font=footer_font)
                x = (self.width - (bbox[2] - bbox[0])) // 2
                draw.text((x, center_y + 280), footer, font=footer_font, fill=self._hex_to_rgb(self.secondary_color))

            return np.array(img)

        clip = VideoClip(make_frame, duration=duration)
        clip = clip.set_fps(self.fps)
        return fadein(fadeout(clip, 1.0), 0.3)

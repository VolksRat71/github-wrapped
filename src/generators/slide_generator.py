import os
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple
from ..utils.config import Config
from ..collectors.github_collector import RepoStats


@dataclass
class Slide:
    image_path: str
    narration: str
    duration: float = 5.0


class SlideGenerator:
    def __init__(self, stats: RepoStats):
        self.stats = stats
        self.width = Config.VIDEO_WIDTH
        self.height = Config.VIDEO_HEIGHT
        Config.ensure_dirs()

        # Try to load a nice font, fallback to default
        self.title_font = self._load_font(80)
        self.big_number_font = self._load_font(180)
        self.body_font = self._load_font(48)
        self.small_font = self._load_font(36)

    def _load_font(self, size: int):
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/SFNSDisplay.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        for path in font_paths:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    continue
        return ImageFont.load_default()

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _create_base_image(self) -> Image.Image:
        return Image.new("RGB", (self.width, self.height), self._hex_to_rgb(Config.BG_COLOR))

    def _draw_centered_text(self, draw: ImageDraw, text: str, y: int, font, color: str):
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), text, font=font, fill=self._hex_to_rgb(color))

    def _draw_gradient_bg(self, img: Image.Image, color1: str, color2: str):
        draw = ImageDraw.Draw(img)
        r1, g1, b1 = self._hex_to_rgb(color1)
        r2, g2, b2 = self._hex_to_rgb(color2)

        for y in range(self.height):
            ratio = y / self.height
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b))

    def generate_all_slides(self) -> List[Slide]:
        slides = []

        # Slide 1: Intro
        slides.append(self._create_intro_slide())

        # Slide 2: Total commits
        slides.append(self._create_commits_slide())

        # Slide 3: PRs
        slides.append(self._create_prs_slide())

        # Slide 4: Top contributors
        slides.append(self._create_contributors_slide())

        # Slide 5: Busiest times
        slides.append(self._create_busiest_times_slide())

        # Slide 6: Lines of code
        slides.append(self._create_lines_slide())

        # Slide 7: Releases
        slides.append(self._create_releases_slide())

        # Slide 8: Activity chart
        slides.append(self._create_activity_chart_slide())

        # Slide 9: Outro
        slides.append(self._create_outro_slide())

        return slides

    def _create_intro_slide(self) -> Slide:
        img = self._create_base_image()
        self._draw_gradient_bg(img, "#1a1a2e", "#16213e")
        draw = ImageDraw.Draw(img)

        # Year
        self._draw_centered_text(draw, str(self.stats.year), 500, self.big_number_font, Config.PRIMARY_COLOR)

        # Repo name
        repo_display = self.stats.repo_name.split("/")[-1] if "/" in self.stats.repo_name else self.stats.repo_name
        self._draw_centered_text(draw, repo_display.upper(), 750, self.title_font, Config.TEXT_COLOR)

        # Subtitle
        self._draw_centered_text(draw, "WRAPPED", 850, self.title_font, Config.SECONDARY_TEXT)

        path = os.path.join(Config.TEMP_DIR, "slide_01_intro.png")
        img.save(path)

        narration = f"Welcome to {repo_display} {self.stats.year} Wrapped. Let's see what your team shipped this year."
        return Slide(image_path=path, narration=narration, duration=5.0)

    def _create_commits_slide(self) -> Slide:
        img = self._create_base_image()
        self._draw_gradient_bg(img, "#0f0f23", "#1a1a2e")
        draw = ImageDraw.Draw(img)

        self._draw_centered_text(draw, "TOTAL COMMITS", 400, self.body_font, Config.SECONDARY_TEXT)
        self._draw_centered_text(draw, f"{self.stats.total_commits:,}", 550, self.big_number_font, Config.PRIMARY_COLOR)

        # Days with commits
        self._draw_centered_text(draw, f"across {self.stats.days_with_commits} different days", 800, self.body_font, Config.TEXT_COLOR)

        path = os.path.join(Config.TEMP_DIR, "slide_02_commits.png")
        img.save(path)

        narration = f"Your team made {self.stats.total_commits:,} commits this year, across {self.stats.days_with_commits} different days."
        return Slide(image_path=path, narration=narration, duration=5.0)

    def _create_prs_slide(self) -> Slide:
        img = self._create_base_image()
        self._draw_gradient_bg(img, "#1a1a2e", "#0f3460")
        draw = ImageDraw.Draw(img)

        self._draw_centered_text(draw, "PULL REQUESTS MERGED", 400, self.body_font, Config.SECONDARY_TEXT)
        self._draw_centered_text(draw, str(self.stats.total_prs), 550, self.big_number_font, Config.PRIMARY_COLOR)

        # Biggest PR
        if self.stats.biggest_prs:
            biggest = self.stats.biggest_prs[0]
            self._draw_centered_text(draw, "Biggest PR:", 850, self.small_font, Config.SECONDARY_TEXT)
            title = biggest["title"][:40] + "..." if len(biggest["title"]) > 40 else biggest["title"]
            self._draw_centered_text(draw, title, 920, self.body_font, Config.TEXT_COLOR)
            self._draw_centered_text(draw, f"{biggest['lines']:,} lines", 1000, self.small_font, Config.PRIMARY_COLOR)

        path = os.path.join(Config.TEMP_DIR, "slide_03_prs.png")
        img.save(path)

        narration = f"{self.stats.total_prs} pull requests were merged this year."
        if self.stats.biggest_prs:
            narration += f" The biggest one touched over {self.stats.biggest_prs[0]['lines']:,} lines of code."
        return Slide(image_path=path, narration=narration, duration=6.0)

    def _create_contributors_slide(self) -> Slide:
        img = self._create_base_image()
        self._draw_gradient_bg(img, "#16213e", "#1a1a2e")
        draw = ImageDraw.Draw(img)

        self._draw_centered_text(draw, "TOP CONTRIBUTORS", 300, self.body_font, Config.SECONDARY_TEXT)

        y = 450
        medals = ["1st", "2nd", "3rd", "4th", "5th"]
        for i, contrib in enumerate(self.stats.top_contributors[:5]):
            name = contrib["name"]
            commits = contrib["commits"]
            medal = medals[i] if i < len(medals) else f"{i+1}th"

            text = f"{medal}  {name}"
            commits_text = f"{commits} commits"

            # Name on left, commits on right
            draw.text((100, y), text, font=self.body_font, fill=self._hex_to_rgb(Config.TEXT_COLOR))
            draw.text((800, y), commits_text, font=self.small_font, fill=self._hex_to_rgb(Config.PRIMARY_COLOR))
            y += 100

        path = os.path.join(Config.TEMP_DIR, "slide_04_contributors.png")
        img.save(path)

        top_name = self.stats.top_contributors[0]["name"] if self.stats.top_contributors else "Unknown"
        top_commits = self.stats.top_contributors[0]["commits"] if self.stats.top_contributors else 0
        narration = f"Your top contributor was {top_name} with {top_commits} commits. Here's the full leaderboard."
        return Slide(image_path=path, narration=narration, duration=7.0)

    def _create_busiest_times_slide(self) -> Slide:
        img = self._create_base_image()
        self._draw_gradient_bg(img, "#1a1a2e", "#0f0f23")
        draw = ImageDraw.Draw(img)

        self._draw_centered_text(draw, "WHEN YOU CODED", 300, self.body_font, Config.SECONDARY_TEXT)

        # Busiest day
        self._draw_centered_text(draw, "Busiest Day", 450, self.small_font, Config.SECONDARY_TEXT)
        self._draw_centered_text(draw, self.stats.busiest_day.upper(), 520, self.title_font, Config.PRIMARY_COLOR)

        # Busiest month
        self._draw_centered_text(draw, "Busiest Month", 700, self.small_font, Config.SECONDARY_TEXT)
        self._draw_centered_text(draw, self.stats.busiest_month.upper(), 770, self.title_font, Config.TEXT_COLOR)

        # Peak hour
        hour_display = f"{self.stats.peak_hour}:00" if self.stats.peak_hour else "Unknown"
        self._draw_centered_text(draw, "Peak Hour", 950, self.small_font, Config.SECONDARY_TEXT)
        self._draw_centered_text(draw, hour_display, 1020, self.title_font, Config.PRIMARY_COLOR)

        # Weekend commits
        self._draw_centered_text(draw, f"Weekend commits: {self.stats.weekend_commits}", 1200, self.body_font, Config.SECONDARY_TEXT)

        path = os.path.join(Config.TEMP_DIR, "slide_05_times.png")
        img.save(path)

        month_commits = self.stats.commits_by_month.get(self.stats.busiest_month, 0)
        narration = f"Your team coded the most on {self.stats.busiest_day}s. {self.stats.busiest_month} was the busiest month with {month_commits} commits. Only {self.stats.weekend_commits} commits happened on weekends."
        return Slide(image_path=path, narration=narration, duration=7.0)

    def _create_lines_slide(self) -> Slide:
        img = self._create_base_image()
        self._draw_gradient_bg(img, "#0f3460", "#1a1a2e")
        draw = ImageDraw.Draw(img)

        self._draw_centered_text(draw, "LINES OF CODE", 350, self.body_font, Config.SECONDARY_TEXT)

        # Added
        self._draw_centered_text(draw, f"+{self.stats.lines_added:,}", 500, self.title_font, "#1DB954")
        self._draw_centered_text(draw, "lines added", 600, self.small_font, Config.SECONDARY_TEXT)

        # Deleted
        self._draw_centered_text(draw, f"-{self.stats.lines_deleted:,}", 750, self.title_font, "#E74C3C")
        self._draw_centered_text(draw, "lines deleted", 850, self.small_font, Config.SECONDARY_TEXT)

        # Net
        net = self.stats.lines_added - self.stats.lines_deleted
        net_color = "#1DB954" if net >= 0 else "#E74C3C"
        net_display = f"+{net:,}" if net >= 0 else f"{net:,}"
        self._draw_centered_text(draw, "Net change", 1000, self.small_font, Config.SECONDARY_TEXT)
        self._draw_centered_text(draw, net_display, 1080, self.title_font, net_color)

        path = os.path.join(Config.TEMP_DIR, "slide_06_lines.png")
        img.save(path)

        narration = f"Your team added {self.stats.lines_added:,} lines and deleted {self.stats.lines_deleted:,}. That's a net change of {abs(net):,} lines."
        return Slide(image_path=path, narration=narration, duration=6.0)

    def _create_releases_slide(self) -> Slide:
        img = self._create_base_image()
        self._draw_gradient_bg(img, "#1a1a2e", "#16213e")
        draw = ImageDraw.Draw(img)

        self._draw_centered_text(draw, "RELEASES SHIPPED", 400, self.body_font, Config.SECONDARY_TEXT)
        self._draw_centered_text(draw, str(self.stats.total_releases), 550, self.big_number_font, Config.PRIMARY_COLOR)

        if self.stats.first_release and self.stats.last_release:
            self._draw_centered_text(draw, f"From {self.stats.first_release} to {self.stats.last_release}", 800, self.body_font, Config.TEXT_COLOR)

        path = os.path.join(Config.TEMP_DIR, "slide_07_releases.png")
        img.save(path)

        narration = f"You shipped {self.stats.total_releases} releases this year, from {self.stats.first_release} all the way to {self.stats.last_release}."
        return Slide(image_path=path, narration=narration, duration=5.0)

    def _create_activity_chart_slide(self) -> Slide:
        # Create activity chart with matplotlib
        fig, ax = plt.subplots(figsize=(10.8, 19.2), facecolor="#121212")
        ax.set_facecolor("#121212")

        # Month data
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        month_full = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

        values = [self.stats.commits_by_month.get(m, 0) for m in month_full]

        # Horizontal bar chart
        y_pos = np.arange(len(months))
        bars = ax.barh(y_pos, values, color="#1DB954", height=0.6)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(months, fontsize=24, color="white")
        ax.invert_yaxis()

        ax.set_xlabel("Commits", fontsize=20, color="white")
        ax.tick_params(axis="x", colors="white", labelsize=16)

        # Remove spines
        for spine in ax.spines.values():
            spine.set_visible(False)

        ax.set_title("Commits by Month", fontsize=36, color="white", pad=40)

        # Add value labels
        for bar, val in zip(bars, values):
            if val > 0:
                ax.text(val + 5, bar.get_y() + bar.get_height()/2, str(val),
                       va="center", fontsize=18, color="white")

        plt.tight_layout(pad=3)

        path = os.path.join(Config.TEMP_DIR, "slide_08_chart.png")
        plt.savefig(path, facecolor="#121212", dpi=100)
        plt.close()

        narration = f"Here's how your commit activity looked throughout the year. {self.stats.busiest_month} was clearly the most productive month."
        return Slide(image_path=path, narration=narration, duration=6.0)

    def _create_outro_slide(self) -> Slide:
        img = self._create_base_image()
        self._draw_gradient_bg(img, "#16213e", "#1a1a2e")
        draw = ImageDraw.Draw(img)

        self._draw_centered_text(draw, "THAT'S A WRAP", 450, self.title_font, Config.TEXT_COLOR)
        self._draw_centered_text(draw, str(self.stats.year), 600, self.big_number_font, Config.PRIMARY_COLOR)

        # Summary stats
        y = 850
        self._draw_centered_text(draw, f"{self.stats.total_commits:,} commits", y, self.body_font, Config.TEXT_COLOR)
        self._draw_centered_text(draw, f"{self.stats.total_prs} PRs merged", y + 70, self.body_font, Config.TEXT_COLOR)
        self._draw_centered_text(draw, f"{self.stats.total_releases} releases", y + 140, self.body_font, Config.TEXT_COLOR)

        self._draw_centered_text(draw, "Here's to shipping more in " + str(self.stats.year + 1), 1200, self.body_font, Config.SECONDARY_TEXT)

        path = os.path.join(Config.TEMP_DIR, "slide_09_outro.png")
        img.save(path)

        narration = f"That's a wrap on {self.stats.year}! {self.stats.total_commits:,} commits, {self.stats.total_prs} pull requests, and {self.stats.total_releases} releases. Here's to shipping even more next year."
        return Slide(image_path=path, narration=narration, duration=6.0)

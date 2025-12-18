#!/usr/bin/env python3
"""
GitHub Wrapped - Generate a Spotify Wrapped-style video for any GitHub repo.

Usage:
    python main.py /path/to/repo
    python main.py /path/to/repo --year 2024
    python main.py /path/to/repo --no-audio
    python main.py /path/to/repo --gif-only
"""

import os
import sys
import click
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.collectors import GitHubCollector
from src.generators import SlideGenerator, AudioGenerator, VideoGenerator
from src.utils.config import Config

console = Console()


def print_banner():
    banner = """
   _____ _ _   _    _       _      __          __                            _
  / ____(_) | | |  | |     | |     \\ \\        / /                           | |
 | |  __ _| |_| |__| |_   _| |__    \\ \\  /\\  / / __ __ _ _ __  _ __   ___  __| |
 | | |_ | | __|  __  | | | | '_ \\    \\ \\/  \\/ / '__/ _` | '_ \\| '_ \\ / _ \\/ _` |
 | |__| | | |_| |  | | |_| | |_) |    \\  /\\  /| | | (_| | |_) | |_) |  __/ (_| |
  \\_____|_|\\__|_|  |_|\\__,_|_.__/      \\/  \\/ |_|  \\__,_| .__/| .__/ \\___|\\__,_|
                                                        | |   | |
                                                        |_|   |_|
    """
    console.print(banner, style="bold green")


def print_stats_summary(stats):
    """Print a summary of collected stats."""
    console.print("\n")
    console.print(Panel.fit(
        f"[bold green]{stats.repo_name}[/] - [cyan]{stats.year}[/]\n\n"
        f"[yellow]Commits:[/] {stats.total_commits:,}\n"
        f"[yellow]PRs Merged:[/] {stats.total_prs}\n"
        f"[yellow]Releases:[/] {stats.total_releases}\n"
        f"[yellow]Lines Added:[/] +{stats.lines_added:,}\n"
        f"[yellow]Lines Deleted:[/] -{stats.lines_deleted:,}\n"
        f"[yellow]Contributors:[/] {len(stats.contributors)}\n"
        f"[yellow]Top Contributor:[/] {stats.top_contributors[0]['name'] if stats.top_contributors else 'N/A'}",
        title="Stats Summary",
        border_style="green",
    ))


@click.command()
@click.argument("repo_path", type=click.Path(exists=True))
@click.option("--year", "-y", default=datetime.now().year, help="Year to generate wrapped for")
@click.option("--no-audio", is_flag=True, help="Skip audio generation")
@click.option("--gif-only", is_flag=True, help="Only generate GIF preview")
@click.option("--voice", "-v", help="ElevenLabs voice ID to use")
@click.option("--output", "-o", default="wrapped", help="Output filename (without extension)")
def main(repo_path: str, year: int, no_audio: bool, gif_only: bool, voice: str, output: str):
    """Generate a GitHub Wrapped video for any repository.

    REPO_PATH: Path to the local git repository
    """
    print_banner()

    # Ensure output directories exist
    Config.ensure_dirs()

    # Step 1: Collect stats
    console.print("\n[bold cyan]Step 1/4:[/] Collecting repository stats...")
    collector = GitHubCollector(repo_path=repo_path, year=year)
    stats = collector.collect()
    print_stats_summary(stats)

    # Step 2: Generate slides
    console.print("\n[bold cyan]Step 2/4:[/] Generating slides...")
    slide_gen = SlideGenerator(stats)
    slides = slide_gen.generate_all_slides()
    console.print(f"  Generated {len(slides)} slides")

    # Step 3: Generate audio (if enabled)
    audio_paths = []
    if not no_audio and not gif_only:
        console.print("\n[bold cyan]Step 3/4:[/] Generating audio narration...")
        audio_gen = AudioGenerator(voice_id=voice)
        audio_paths = audio_gen.generate_audio_for_slides(slides)
        if audio_paths:
            console.print(f"  Generated {len(audio_paths)} audio files")
        else:
            console.print("  [yellow]Skipped (no API key or error)[/]")
    else:
        console.print("\n[bold cyan]Step 3/4:[/] Skipping audio generation")

    # Step 4: Create video
    console.print("\n[bold cyan]Step 4/4:[/] Creating video...")
    video_gen = VideoGenerator()

    if gif_only:
        output_path = video_gen.create_gif_preview(slides, output_name=output)
    elif audio_paths:
        output_path = video_gen.create_video(slides, audio_paths, output_name=output)
    else:
        output_path = video_gen.create_video_no_audio(slides, output_name=output)

    # Done!
    console.print("\n")
    console.print(Panel.fit(
        f"[bold green]Done![/]\n\n"
        f"Output: [cyan]{output_path}[/]",
        title="GitHub Wrapped Complete",
        border_style="green",
    ))


if __name__ == "__main__":
    main()

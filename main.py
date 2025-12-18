#!/usr/bin/env python3
"""
GitHub Wrapped - Generate a Spotify Wrapped-style video for any GitHub repo.

Usage:
    python main.py /path/to/repo
    python main.py /path/to/repo --year 2024
    python main.py /path/to/repo --no-audio
    python main.py /path/to/repo --music track.mp3
    python main.py /path/to/repo --static  # Old non-animated version
"""

import os
import sys
import click
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.collectors import GitHubCollector
from src.generators import SlideGenerator, AudioGenerator, VideoGenerator
from src.generators.animated_video_generator import AnimatedVideoGenerator
from src.generators.music_manager import MusicManager
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


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """GitHub Wrapped - Generate Spotify Wrapped-style videos for any repo."""
    if ctx.invoked_subcommand is None:
        # Show help if no command specified
        click.echo(ctx.get_help())


@cli.command()
@click.argument("repo_path", type=click.Path(exists=True))
@click.option("--year", "-y", default=datetime.now().year, help="Year to generate wrapped for")
@click.option("--no-audio", is_flag=True, help="Skip voice narration")
@click.option("--static", is_flag=True, help="Use static slides instead of animations")
@click.option("--music", "-m", help="Music file from output/music/ directory")
@click.option("--music-url", help="URL to download music from")
@click.option("--voice", "-v", help="ElevenLabs voice ID to use")
@click.option("--output", "-o", default="wrapped", help="Output filename (without extension)")
@click.option("--gif", is_flag=True, help="Also generate a GIF preview")
def generate(repo_path: str, year: int, no_audio: bool, static: bool, music: str,
             music_url: str, voice: str, output: str, gif: bool):
    """Generate a GitHub Wrapped video for a repository.

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

    # Handle music
    music_path = None
    if music or music_url:
        music_mgr = MusicManager()
        if music_url:
            music_path = music_mgr.download_from_url(music_url, "downloaded_track")
        elif music:
            music_path = music_mgr.get_track_path(music)
            if not music_path:
                console.print(f"[yellow]Warning: Music file '{music}' not found in output/music/[/]")

    if static:
        # Old static slide method
        console.print("\n[bold cyan]Step 2/4:[/] Generating static slides...")
        slide_gen = SlideGenerator(stats)
        slides = slide_gen.generate_all_slides()
        console.print(f"  Generated {len(slides)} slides")

        # Generate audio
        audio_paths = []
        if not no_audio:
            console.print("\n[bold cyan]Step 3/4:[/] Generating audio narration...")
            audio_gen = AudioGenerator(voice_id=voice)
            audio_paths = audio_gen.generate_audio_for_slides(slides)
            if audio_paths:
                console.print(f"  Generated {len(audio_paths)} audio files")
            else:
                console.print("  [yellow]Skipped (no API key or error)[/]")
        else:
            console.print("\n[bold cyan]Step 3/4:[/] Skipping audio generation")

        # Create video
        console.print("\n[bold cyan]Step 4/4:[/] Creating video...")
        video_gen = VideoGenerator()
        if audio_paths:
            output_path = video_gen.create_video(slides, audio_paths, output_name=output)
        else:
            output_path = video_gen.create_video_no_audio(slides, output_name=output)

        if gif:
            video_gen.create_gif_preview(slides, output_name=f"{output}_preview")
    else:
        # New animated video
        console.print("\n[bold cyan]Step 2/4:[/] Preparing animations...")
        animated_gen = AnimatedVideoGenerator(stats)
        console.print("  Animation templates ready")

        # Generate audio
        audio_paths = []
        if not no_audio:
            console.print("\n[bold cyan]Step 3/4:[/] Generating audio narration...")
            # Generate narration for animated version
            slide_gen = SlideGenerator(stats)
            slides = slide_gen.generate_all_slides()
            audio_gen = AudioGenerator(voice_id=voice)
            audio_paths = audio_gen.generate_audio_for_slides(slides)
            if audio_paths:
                console.print(f"  Generated {len(audio_paths)} audio files")
            else:
                console.print("  [yellow]Skipped (no API key or error)[/]")
        else:
            console.print("\n[bold cyan]Step 3/4:[/] Skipping audio generation")

        # Create animated video
        console.print("\n[bold cyan]Step 4/4:[/] Creating animated video...")
        output_path = animated_gen.create_animated_video(
            audio_paths=audio_paths if audio_paths else None,
            music_path=music_path,
            output_name=output,
        )

    # Done!
    console.print("\n")
    console.print(Panel.fit(
        f"[bold green]Done![/]\n\n"
        f"Output: [cyan]{output_path}[/]",
        title="GitHub Wrapped Complete",
        border_style="green",
    ))


@cli.command()
def music_help():
    """Show info about royalty-free music sources."""
    print_banner()
    music_mgr = MusicManager()
    console.print(music_mgr.get_royalty_free_sources())


@cli.command()
def list_music():
    """List available music in the output/music/ directory."""
    print_banner()
    music_mgr = MusicManager()
    tracks = music_mgr.list_available_tracks()

    if not tracks:
        console.print("\n[yellow]No music files found in output/music/[/]")
        console.print("\nTo add music:")
        console.print("  1. Download an MP3 from pixabay.com/music/")
        console.print("  2. Place it in: output/music/")
        console.print("  3. Run with: --music your_track.mp3")
        return

    table = Table(title="Available Music Tracks")
    table.add_column("Filename", style="cyan")
    table.add_column("Source", style="green")

    for track in tracks:
        table.add_row(track["name"], track["source"])

    console.print(table)


@cli.command()
def list_voices():
    """List available ElevenLabs voices."""
    print_banner()

    if not Config.ELEVENLABS_API_KEY:
        console.print("[red]Error: ELEVENLABS_API_KEY not set in .env file[/]")
        return

    console.print("\nFetching available voices...")
    try:
        from elevenlabs import ElevenLabs
        client = ElevenLabs(api_key=Config.ELEVENLABS_API_KEY)
        response = client.voices.get_all()

        table = Table(title="Available ElevenLabs Voices")
        table.add_column("Voice ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Category", style="yellow")

        for voice in response.voices:
            table.add_row(voice.voice_id, voice.name, voice.category or "N/A")

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error fetching voices: {e}[/]")


# Keep backwards compatibility with old CLI
@click.command()
@click.argument("repo_path", type=click.Path(exists=True))
@click.option("--year", "-y", default=datetime.now().year, help="Year to generate wrapped for")
@click.option("--no-audio", is_flag=True, help="Skip voice narration")
@click.option("--static", is_flag=True, help="Use static slides instead of animations")
@click.option("--music", "-m", help="Music file from output/music/ directory")
@click.option("--music-url", help="URL to download music from")
@click.option("--voice", "-v", help="ElevenLabs voice ID to use")
@click.option("--output", "-o", default="wrapped", help="Output filename (without extension)")
@click.option("--gif", is_flag=True, help="Also generate a GIF preview")
def main(repo_path: str, year: int, no_audio: bool, static: bool, music: str,
         music_url: str, voice: str, output: str, gif: bool):
    """Generate a GitHub Wrapped video (legacy command)."""
    ctx = click.Context(generate)
    ctx.invoke(generate, repo_path=repo_path, year=year, no_audio=no_audio,
               static=static, music=music, music_url=music_url, voice=voice,
               output=output, gif=gif)


if __name__ == "__main__":
    # Check if using old-style invocation (direct repo path)
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        main()
    else:
        cli()

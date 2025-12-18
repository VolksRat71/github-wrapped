import subprocess
import json
import re
from datetime import datetime
from collections import defaultdict
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class RepoStats:
    repo_name: str
    year: int

    # Totals
    total_commits: int = 0
    total_prs: int = 0
    total_releases: int = 0
    lines_added: int = 0
    lines_deleted: int = 0

    # Contributors
    contributors: dict = field(default_factory=dict)
    top_contributors: list = field(default_factory=list)

    # Time-based
    commits_by_month: dict = field(default_factory=dict)
    commits_by_day: dict = field(default_factory=dict)
    commits_by_hour: dict = field(default_factory=dict)
    days_with_commits: int = 0

    # PRs
    biggest_prs: list = field(default_factory=list)

    # Releases
    releases: list = field(default_factory=list)
    first_release: str = ""
    last_release: str = ""

    # Fun facts
    busiest_day: str = ""
    busiest_month: str = ""
    peak_hour: int = 0
    weekend_commits: int = 0


class GitHubCollector:
    def __init__(self, repo_path: str, repo_url: Optional[str] = None, year: int = None):
        self.repo_path = repo_path
        self.repo_url = repo_url
        self.year = year or datetime.now().year
        self.repo_name = self._get_repo_name()

    def _get_repo_name(self) -> str:
        if self.repo_url:
            match = re.search(r"github\.com[:/](.+?)(?:\.git)?$", self.repo_url)
            if match:
                return match.group(1)
        # Try to get from git remote
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                match = re.search(r"github\.com[:/](.+?)(?:\.git)?$", result.stdout.strip())
                if match:
                    return match.group(1)
        except Exception:
            pass
        return "Unknown Repo"

    def _run_git(self, args: list) -> str:
        result = subprocess.run(
            ["git"] + args,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def _run_gh(self, args: list) -> str:
        result = subprocess.run(
            ["gh"] + args,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def collect(self) -> RepoStats:
        stats = RepoStats(repo_name=self.repo_name, year=self.year)

        print(f"Collecting stats for {self.repo_name} ({self.year})...")

        # Fetch latest
        print("  Fetching latest...")
        self._run_git(["fetch", "--all", "--tags"])

        # Get main branch
        main_branch = self._get_main_branch()

        # Total commits
        print("  Counting commits...")
        stats.total_commits = self._count_commits(main_branch)

        # Contributors
        print("  Analyzing contributors...")
        stats.contributors, stats.top_contributors = self._get_contributors(main_branch)

        # Time-based stats
        print("  Analyzing commit patterns...")
        (
            stats.commits_by_month,
            stats.commits_by_day,
            stats.commits_by_hour,
            stats.days_with_commits,
            stats.weekend_commits,
        ) = self._get_time_stats(main_branch)

        # Find busiest
        if stats.commits_by_day:
            stats.busiest_day = max(stats.commits_by_day, key=stats.commits_by_day.get)
        if stats.commits_by_month:
            stats.busiest_month = max(stats.commits_by_month, key=stats.commits_by_month.get)
        if stats.commits_by_hour:
            stats.peak_hour = max(stats.commits_by_hour, key=stats.commits_by_hour.get)

        # Lines changed
        print("  Counting lines changed...")
        stats.lines_added, stats.lines_deleted = self._get_lines_changed(main_branch)

        # PRs
        print("  Fetching PR data...")
        stats.total_prs, stats.biggest_prs = self._get_pr_stats()

        # Releases
        print("  Fetching releases...")
        stats.total_releases, stats.releases = self._get_releases()
        if stats.releases:
            stats.first_release = stats.releases[-1]["name"]
            stats.last_release = stats.releases[0]["name"]

        print("Done collecting stats!")
        return stats

    def _get_main_branch(self) -> str:
        # Try common branch names
        for branch in ["origin/develop", "origin/main", "origin/master"]:
            result = self._run_git(["rev-parse", "--verify", branch])
            if result:
                return branch
        return "HEAD"

    def _count_commits(self, branch: str) -> int:
        output = self._run_git(
            ["log", "--oneline", f"--after={self.year}-01-01", f"--before={self.year}-12-31", branch]
        )
        return len(output.splitlines()) if output else 0

    def _get_contributors(self, branch: str) -> tuple:
        output = self._run_git(
            ["shortlog", "-sn", f"--after={self.year}-01-01", branch]
        )
        contributors = {}
        top_contributors = []

        for line in output.splitlines():
            if line.strip():
                parts = line.strip().split("\t")
                if len(parts) >= 2:
                    count = int(parts[0].strip())
                    name = parts[1].strip()
                    contributors[name] = count
                    top_contributors.append({"name": name, "commits": count})

        return contributors, top_contributors[:10]

    def _get_time_stats(self, branch: str) -> tuple:
        # By month
        output = self._run_git(
            ["log", f"--after={self.year}-01-01", "--format=%ad", "--date=format:%B", branch]
        )
        by_month = defaultdict(int)
        for line in output.splitlines():
            if line.strip():
                by_month[line.strip()] += 1

        # By day of week
        output = self._run_git(
            ["log", f"--after={self.year}-01-01", "--format=%ad", "--date=format:%A", branch]
        )
        by_day = defaultdict(int)
        weekend_commits = 0
        for line in output.splitlines():
            if line.strip():
                by_day[line.strip()] += 1
                if line.strip() in ["Saturday", "Sunday"]:
                    weekend_commits += 1

        # By hour
        output = self._run_git(
            ["log", f"--after={self.year}-01-01", "--format=%ad", "--date=format:%H", branch]
        )
        by_hour = defaultdict(int)
        for line in output.splitlines():
            if line.strip():
                by_hour[int(line.strip())] += 1

        # Days with commits
        output = self._run_git(
            ["log", f"--after={self.year}-01-01", "--format=%ad", "--date=format:%Y-%m-%d", branch]
        )
        unique_days = len(set(output.splitlines())) if output else 0

        return dict(by_month), dict(by_day), dict(by_hour), unique_days, weekend_commits

    def _get_lines_changed(self, branch: str) -> tuple:
        output = self._run_git(
            ["log", "--shortstat", f"--after={self.year}-01-01", branch]
        )
        added = 0
        deleted = 0
        for line in output.splitlines():
            if "insertion" in line or "deletion" in line:
                parts = line.split(",")
                for part in parts:
                    match = re.search(r"(\d+)", part)
                    if match:
                        if "insertion" in part:
                            added += int(match.group(1))
                        elif "deletion" in part:
                            deleted += int(match.group(1))
        return added, deleted

    def _get_pr_stats(self) -> tuple:
        try:
            output = self._run_gh(
                [
                    "pr", "list", "--state", "merged",
                    "--search", f"merged:>={self.year}-01-01",
                    "--limit", "500",
                    "--json", "number,additions,deletions,title,author",
                ]
            )
            if output:
                prs = json.loads(output)
                total = len(prs)

                # Sort by size and get top 5
                sorted_prs = sorted(prs, key=lambda x: x.get("additions", 0) + x.get("deletions", 0), reverse=True)
                biggest = []
                for pr in sorted_prs[:5]:
                    biggest.append({
                        "number": pr.get("number"),
                        "title": pr.get("title"),
                        "lines": pr.get("additions", 0) + pr.get("deletions", 0),
                        "author": pr.get("author", {}).get("login", "unknown"),
                    })
                return total, biggest
        except Exception as e:
            print(f"  Warning: Could not fetch PR data: {e}")
        return 0, []

    def _get_releases(self) -> tuple:
        output = self._run_git(
            ["for-each-ref", "--sort=-creatordate", "--format=%(refname:short) %(creatordate:short)", "refs/tags"]
        )
        releases = []
        for line in output.splitlines():
            parts = line.strip().split()
            if len(parts) >= 2:
                tag_name = parts[0]
                date_str = parts[1]
                if date_str >= f"{self.year}-01-01":
                    releases.append({"name": tag_name, "date": date_str})
        return len(releases), releases

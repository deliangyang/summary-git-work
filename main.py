from openai import OpenAI
from typing import List
import subprocess
from datetime import datetime, timedelta
import argparse
from dataclasses import dataclass


@dataclass
class GitWorkSummaryArgs:
    username: str
    email: str
    projects: List[str]
    last_days: int = 1


def parse_arguments() -> GitWorkSummaryArgs:
    parser = argparse.ArgumentParser(description="Summarize today's git work.")
    parser.add_argument(
        "-u", "--username", type=str, required=True, help="Git username"
    )
    parser.add_argument(
        "-e", "--email", type=str, required=False, default="", help="Git email"
    )
    parser.add_argument(
        "-p",
        "--projects",
        type=str,
        nargs="+",
        required=True,
        help="List of project directories to summarize git work from",
    )
    parser.add_argument(
        "-d",
        "--days",
        type=int,
        default=1,
        help="Number of days to look back for commits",
    )
    args = parser.parse_args()
    return GitWorkSummaryArgs(
        username=args.username,
        email=args.email,
        projects=args.projects,
        last_days=args.days,
    )


system_prompt = """You are a helpful assistant that summarizes git commit messages into concise summaries and key points.
1. please return chinese.
"""


def get_today_git_commit_messages(args: GitWorkSummaryArgs) -> List[str]:
    commit_messages = []
    last_days = args.last_days
    last_day_format = (datetime.now() - timedelta(days=last_days)).strftime("%Y-%m-%d")

    for project in args.projects:
        # pull the latest changes
        subprocess.run(["git", "-C", project, "pull"], check=True)
        try:
            cmd = [
                "git",
                "-C",
                project,
                "log",
                "--since={}".format(last_day_format),
                "--pretty=format:%s",
            ]
            if args.username:
                cmd.extend(["--author={}".format(args.username)])
            print(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            messages = result.stdout.strip()
            if len(messages) == 0:
                print(f"No commits found for {project} since {last_day_format}.")
                continue
            print(f"Commits from {project} since {last_day_format}: {messages}")
            commit_messages.extend(messages.split("\n"))
        except subprocess.CalledProcessError as e:
            print(f"Error retrieving commits from {project}: {e}")

    return commit_messages


def summarize_git_work(commit_messages: List[str]) -> str:
    client = OpenAI()
    prompt = "Here are today's git commit messages:\n\n"
    for msg in commit_messages:
        prompt += f"- {msg}\n"
    prompt += (
        "\nPlease provide a concise summary and key points of the work done today."
    )
    response = client.chat.completions.create(
        model="gpt-5.2-2025-12-11",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    )

    summary = response.choices[0].message.content.strip()
    return summary


if __name__ == "__main__":
    args = parse_arguments()
    sample_commits = get_today_git_commit_messages(args)
    if not sample_commits:
        print(f"No git commits found for the last {args.last_days} days.")
    else:
        summary = summarize_git_work(sample_commits)
        print("Git Work Summary:")
        print(summary)

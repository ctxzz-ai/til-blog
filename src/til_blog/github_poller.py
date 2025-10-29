#!/usr/bin/env python3
"""
Poll GitHub for recent commits and generate a daily TIL post.

Usage: python -m til_blog.github_poller --config config.yml
Environment:
 - GH_PAT or GITHUB_TOKEN: GitHub PAT with necessary scopes
 - OPENAI_API_KEY: OpenAI API key
"""

import argparse
import os
import yaml
import json
import requests
from datetime import datetime

from til_blog.summarizer import Summarizer
from til_blog.post_generator import PostGenerator

GITHUB_API = "https://api.github.com"


def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f) or {}


def load_state(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def save_state(path, state):
    with open(path, "w") as f:
        json.dump(state, f, indent=2)


def get_repos_from_org(org, token):
    repos = []
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    page = 1
    while True:
        r = requests.get(f"{GITHUB_API}/orgs/{org}/repos", headers=headers, params={"per_page": 100, "page": page, "type": "all"})
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        for repo in data:
            repos.append(repo["full_name"])
        page += 1
    return repos


def list_commits(owner_repo, token, since=None):
    owner, repo = owner_repo.split("/")
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    params = {"per_page": 100}
    if since:
        params["since"] = since
    r = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/commits", headers=headers, params=params)
    if r.status_code == 404:
        print(f"Repo not found or no access: {owner_repo}")
        return []
    r.raise_for_status()
    commits = r.json()
    commits.reverse()  # chronological order
    return commits


def get_commit_detail(owner_repo, sha, token):
    owner, repo = owner_repo.split("/")
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    r = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/commits/{sha}", headers=headers)
    r.raise_for_status()
    return r.json()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yml")
    args = parser.parse_args()

    config = load_config(args.config)
    token = os.getenv("GH_PAT") or os.getenv("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GH_PAT or GITHUB_TOKEN must be set as env var")

    # Determine repos to poll
    repos = []
    if config.get("github_repos"):
        repos = config["github_repos"]
    elif config.get("github_org"):
        repos = get_repos_from_org(config["github_org"], token)
    else:
        raise SystemExit("Please set 'github_repos' or 'github_org' in config.yml")

    state_file = config.get("state_file", "state.json")
    state = load_state(state_file)

    all_commits = []

    for r in repos:
        last_date = state.get(r, {}).get("last_date")
        # If there's no saved last_date, use since_days if configured to avoid huge backfill
        if not last_date and config.get("since_days"):
            since_dt = datetime.utcnow() - timedelta(days=int(config.get("since_days")))
            last_date = since_dt.isoformat() + "Z"
        try:
            commits = list_commits(r, token, since=last_date)
        except Exception as e:
            print(f"Error listing commits for {r}: {e}")
            continue
        if not commits:
            continue
        latest_date = None
        for c in commits:
            sha = c.get("sha")
            try:
                detail = get_commit_detail(r, sha, token)
            except Exception as e:
                print(f"Failed to get detail for {r}@{sha}: {e}")
                continue
            files = detail.get("files", [])
            files_slim = []
            for f in files:
                files_slim.append({"filename": f.get("filename"), "patch": f.get("patch")})
            commit_dict = {"sha": sha, "message": c.get("commit", {}).get("message", ""), "files": files_slim, "repo": r}
            all_commits.append(commit_dict)
            latest_date = c.get("commit", {}).get("committer", {}).get("date") or latest_date
        # update state for this repo to latest_date
        if latest_date:
            state.setdefault(r, {})["last_date"] = latest_date

    if not all_commits:
        print("No new commits found.")
        save_state(state_file, state)
        return

    summarizer = Summarizer(os.getenv("OPENAI_API_KEY"))
    summary = summarizer.summarize(all_commits)

    generator = PostGenerator()
    output_dir = config.get("output_dir", "site/content/posts")
    generator.generate_post(summary, output_dir)

    save_state(state_file, state)
    print("Done.")


if __name__ == "__main__":
    main()

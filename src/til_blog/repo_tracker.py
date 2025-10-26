import os
import json
from typing import Optional, Tuple

from git import Repo
from git.exc import GitError, NoSuchPathError, InvalidGitRepositoryError

class RepoTracker:
    def __init__(self, config):
        self.repos = config.get('repos', [])
        self.state_file = config.get('state_file', 'state.json')
        self.state = self._load_state()

    def _load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {}

    def save_state(self, path=None):
        path = path or self.state_file
        with open(path, 'w') as f:
            json.dump(self.state, f, indent=2)

    def discover_repos(self):
        # For now, use configured list
        return self.repos

    def _resolve_repo_entry(self, entry) -> Optional[Tuple[str, str]]:
        path: Optional[str]
        name: Optional[str]
        if isinstance(entry, dict):
            path = entry.get("path")
            name = entry.get("name")
        else:
            path = entry
            name = None

        if not path:
            print("Skipping repository entry with no path configured")
            return None

        expanded_path = os.path.expanduser(os.path.expandvars(str(path)))
        normalized_path = os.path.abspath(expanded_path)
        repo_name = name or os.path.basename(normalized_path.rstrip(os.sep)) or normalized_path
        return normalized_path, repo_name

    def get_new_commits(self):
        new_commits = []
        for entry in self.discover_repos():
            resolved = self._resolve_repo_entry(entry)
            if not resolved:
                continue

            path, repo_name = resolved

            if not os.path.isdir(path):
                print(f"Repository path not found: {path}")
                continue

            last = self.state.get(repo_name)
            try:
                repo = Repo(path)
            except (NoSuchPathError, InvalidGitRepositoryError):
                print(f"Invalid or missing git repository: {path}")
                continue
            except GitError as exc:
                print(f"Failed to open repository {path}: {exc}")
                continue
            commits = list(repo.iter_commits())
            commits_to_process = []
            for commit in commits:
                if commit.hexsha == last:
                    break
                commits_to_process.append(commit)
            if commits_to_process:
                # latest first; reverse to chronological
                new_commits.extend(reversed(commits_to_process))
                self.state[repo_name] = commits[0].hexsha
        return new_commits

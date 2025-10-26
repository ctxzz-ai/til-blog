import os
import json
from git import Repo
from git.exc import NoSuchPathError, InvalidGitRepositoryError

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

    def get_new_commits(self):
        new_commits = []
        for path in self.discover_repos():
            if not os.path.isdir(path):
                print(f"Repository path not found: {path}")
                continue

            repo_name = os.path.basename(path)
            last = self.state.get(repo_name)
            try:
                repo = Repo(path)
            except NoSuchPathError:
                print(f"Repository path not found: {path}")
                continue
            except InvalidGitRepositoryError:
                print(f"Invalid git repository: {path}")
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

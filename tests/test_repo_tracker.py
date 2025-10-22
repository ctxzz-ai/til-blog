import os
import json
import tempfile
from til_blog.repo_tracker import RepoTracker
from git import Repo

def init_test_repo(tmp_path):
    repo_dir = tmp_path / "repo"
    repo = Repo.init(str(repo_dir))
    file_path = repo_dir / "file.txt"
    file_path.write_text("Hello")
    repo.index.add([str(file_path)])
    repo.index.commit("Initial commit")
    file_path.write_text("World")
    repo.index.add([str(file_path)])
    repo.index.commit("Second commit")
    return repo_dir

def test_get_new_commits(tmp_path, monkeypatch):
    repo_dir = init_test_repo(tmp_path)
    config = {"repos": [str(repo_dir)], "state_file": str(tmp_path / "state.json")}  
    tracker = RepoTracker(config)
    commits = tracker.get_new_commits()
    # Should get both commits
    messages = [c.message.strip() for c in commits]
    assert messages == ["Initial commit", "Second commit"]
    # Second call should return none
    commits2 = tracker.get_new_commits()
    assert commits2 == []

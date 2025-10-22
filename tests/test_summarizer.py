import pytest
import openai
from types import SimpleNamespace
from til_blog.summarizer import Summarizer

class DummyRepo:
    def __init__(self):
        # self.git.show will be used
        self.git = self

    def show(self, hexsha, *args):
        return f"{hexsha}: dummy diff"

class DummyCommit:
    def __init__(self, hexsha, message, repo):
        self.hexsha = hexsha
        self.message = message
        self.repo = repo


def test_summarize_empty():
    s = Summarizer(api_key="test_key")
    assert s.summarize([]) == ''


def test_summarize_with_commits(monkeypatch):
    # Prepare dummy commits
    repo = DummyRepo()
    commits = [DummyCommit("abc123", "Test commit message", repo)]

    # Capture parameters
    captured = {}
    def dummy_create(engine, prompt, max_tokens, temperature):
        captured['engine'] = engine
        captured['prompt'] = prompt
        captured['max_tokens'] = max_tokens
        captured['temperature'] = temperature
        return SimpleNamespace(choices=[SimpleNamespace(text="  Summarized output  ")])

    # Monkeypatch OpenAI API
    monkeypatch.setattr(openai.Completion, 'create', dummy_create)

    s = Summarizer(api_key="test_key")
    result = s.summarize(commits)

    assert result == "Summarized output"
    assert captured['engine'] == "text-davinci-003"
    assert "abc123: dummy diff" in captured['prompt']
    assert 'Test commit message' not in captured['prompt']  # diff includes hexsha only

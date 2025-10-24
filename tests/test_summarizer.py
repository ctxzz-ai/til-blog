import pytest
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
    class DummyResponses:
        def create(self, *, model, input, max_output_tokens, temperature):
            captured['model'] = model
            captured['prompt'] = input
            captured['max_output_tokens'] = max_output_tokens
            captured['temperature'] = temperature
            return SimpleNamespace(
                output=[SimpleNamespace(type="output_text", text="  Summarized output  ")],
                output_text="  Summarized output  ",
            )

    class DummyClient(SimpleNamespace):
        def __init__(self):
            super().__init__(responses=DummyResponses())

    s = Summarizer(api_key="test_key")
    s.client = DummyClient()
    result = s.summarize(commits)

    assert result == "Summarized output"
    assert captured['model'] == "gpt-4o-mini"
    assert "abc123: dummy diff" in captured['prompt']
    assert 'Test commit message' not in captured['prompt']  # diff includes hexsha only

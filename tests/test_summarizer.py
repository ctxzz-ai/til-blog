from til_blog.summarizer import Summarizer


COMMITS = [
    {
        "repo": "ctxzz-ai/til-blog",
        "sha": "abcdef123456",
        "message": "Add feature X\n\nDetails",
        "files": [],
    },
    {
        "repo": "ctxzz-ai/til-blog",
        "sha": "123456abcdef",
        "message": "Fix bug",
        "files": [],
    },
]


def test_summarizer_skips_when_no_api_key(monkeypatch):
    # Ensure we do not attempt to construct an OpenAI client when the key is masked.
    def fail_openai(api_key):  # pragma: no cover - defensive path
        raise AssertionError("should not create client")

    monkeypatch.setattr("til_blog.summarizer.OpenAI", fail_openai)

    summary = Summarizer("***").summarize(COMMITS)

    assert "Summarization skipped" in summary
    assert "Add feature X" in summary


def test_summarizer_falls_back_on_openai_failure(monkeypatch):
    class FailingClient:
        def __init__(self, api_key):
            self.responses = self

        def create(self, **kwargs):  # pragma: no cover - executed via Summarizer
            raise RuntimeError("boom")

    monkeypatch.setattr("til_blog.summarizer.OpenAI", FailingClient)

    summary = Summarizer("sk-test").summarize(COMMITS)

    assert "Summarization failed" in summary
    assert "Fix bug" in summary

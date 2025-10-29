import pytest
import requests

from til_blog.github_poller import get_repos_from_org


class DummyResponse:
    def __init__(self, status_code=200, data=None):
        self.status_code = status_code
        self._data = data or []

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)


def test_get_repos_falls_back_to_user(monkeypatch):
    calls = []

    def fake_get(url, headers=None, params=None):
        calls.append((url, tuple(sorted((params or {}).items()))))
        page = (params or {}).get("page", 1)
        if "orgs" in url:
            return DummyResponse(status_code=404, data={"message": "Not Found"})
        if page == 1:
            return DummyResponse(data=[{"full_name": "ctxzz-ai/repo1"}])
        return DummyResponse(data=[])

    monkeypatch.setattr(requests, "get", fake_get)

    repos = get_repos_from_org("ctxzz-ai", token="abc123")

    assert repos == ["ctxzz-ai/repo1"]
    # Ensure we tried both org and user endpoints
    assert any("/orgs/ctxzz-ai/repos" in call[0] for call in calls)
    assert any("/users/ctxzz-ai/repos" in call[0] for call in calls)


def test_get_repos_user_not_found(monkeypatch):
    def fake_get(url, headers=None, params=None):
        return DummyResponse(status_code=404, data={"message": "Not Found"})

    monkeypatch.setattr(requests, "get", fake_get)

    with pytest.raises(SystemExit) as exc:
        get_repos_from_org("missing-user", token=None)

    assert "Unable to find" in str(exc.value)

import os
import sys
import json
import yaml
from types import SimpleNamespace
from git import Repo
from til_blog.main import main

def init_repo(path):
    repo = Repo.init(str(path))
    file = path / 'file.txt'
    file.write_text('foo')
    repo.index.add([str(file)])
    repo.index.commit('Commit 1')
    return repo

def test_full_flow(tmp_path, monkeypatch):
    # Setup dummy repo
    repo_dir = tmp_path / 'repo'
    repo_dir.mkdir()
    repo = init_repo(repo_dir)
    # Write config
    config = {
        'repos': [str(repo_dir)],
        'output_dir': str(tmp_path / 'posts'),
        'state_file': str(tmp_path / 'state.json')
    }
    config_path = tmp_path / 'config.yml'
    config_path.write_text(yaml.safe_dump(config))
    # Monkeypatch openai API and env
    monkeypatch.setenv('OPENAI_API_KEY', 'test')
    class DummyResponses:
        def create(self, *, model, input, max_output_tokens, temperature):
            return SimpleNamespace(
                output=[SimpleNamespace(type="output_text", text="Test summary")],
                output_text="Test summary",
            )

    class DummyOpenAI:
        def __init__(self, api_key=None):
            self.responses = DummyResponses()

    monkeypatch.setattr('til_blog.summarizer.OpenAI', DummyOpenAI)
    # Run main in tmp cwd
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, 'argv', ['prog', '--config', str(config_path)])
    main()
    # Verify posts
    posts = list((tmp_path / 'posts').glob('*.md'))
    assert len(posts) == 1
    content = posts[0].read_text()
    assert 'Test summary' in content
    # Verify state saved
    state = json.loads((tmp_path / 'state.json').read_text())
    assert state.get(repo_dir.name) == repo.head.commit.hexsha

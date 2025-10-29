# TIL Blog Generator

This project automatically generates a TIL (Today I Learned) blog from local Git repositories, summarizing daily commits into Markdown posts.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Copy `config.yml.template` to `config.yml` and update paths and settings.

Run:

```bash
python -m til_blog.main --config config.yml
```

## Configuration

See `config.yml.template` for default settings.

## GitHub Actions setup

To let the scheduled workflow post updates and summarise commits:

- Add an `OPENAI_API_KEY` repository secret containing a valid OpenAI API key if
  you want AI-generated summaries. When the secret is absent the workflow still
  publishes a basic list of commit messages.
- Add a `GH_PAT` repository secret if you need to poll repositories outside of
  this project. The Personal Access Token should have at least the `repo`
  scope (read access is enough) and will be used by the poller. If you only
  fetch commits from this repository, the built-in `GITHUB_TOKEN` is sufficient.

The workflow already has `contents: write` permissions so it can commit the new
posts back to the repository.


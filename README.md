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


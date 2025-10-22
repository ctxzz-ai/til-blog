#!/usr/bin/env python3
import argparse
import yaml
import os

from til_blog.repo_tracker import RepoTracker
from til_blog.summarizer import Summarizer
from til_blog.post_generator import PostGenerator


def main():
    parser = argparse.ArgumentParser(description="Generate TIL blog posts from local git repos.")
    parser.add_argument("--config", default="config.yml", help="Path to config file.")
    args = parser.parse_args()

    # Load configuration
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    # Initialize components
    tracker = RepoTracker(config)
    commits = tracker.get_new_commits()

    summarizer = Summarizer(os.getenv('OPENAI_API_KEY'))
    summary = summarizer.summarize(commits)

    generator = PostGenerator()
    generator.generate_post(summary, config.get('output_dir', 'til_posts'))

    # Save state
    tracker.save_state(config.get('state_file', 'state.json'))

    print("TIL posts generated.")

if __name__ == "__main__":
    main()

"""Utilities for summarizing commit history with OpenAI's Responses API."""

from __future__ import annotations

import os

from collections import defaultdict
from typing import Any, Dict, Iterable, List

from openai import OpenAI


class Summarizer:
    """Summarize commit history, falling back when OpenAI is unavailable."""

    def __init__(self, api_key: str | None):
        self._api_key = api_key or ""
        self.client = None
        if self._is_valid_api_key(self._api_key):
            self.client = OpenAI(api_key=self._api_key)

    @staticmethod
    def _is_valid_api_key(api_key: str) -> bool:
        """Return True if the key looks real (not empty or masked)."""

        if not api_key:
            return False

        # GitHub Actions masks secrets with **** in logs; sometimes users provide
        # placeholders like "***" when testing locally. Treat all-star strings as
        # "not configured" so we can skip OpenAI usage gracefully.
        if api_key.strip("*") == "":
            return False

        return True

    def summarize(self, commits: List[dict]) -> str:
        """Summarize commits with OpenAI, or fall back to a basic digest."""

        if not commits:
            return ""

        normalized_commits = [self._normalise_commit(c) for c in commits]

        if not self.client:
            return self._fallback_summary(
                normalized_commits,
                "Summarization skipped because no OpenAI API key was configured.",
            )

        prompt_sections: List[str] = [
            "You are a helpful assistant. Summarize the following code commits into a concise 'Today I Learned' (TIL) entry. For each commit, include the repo, commit message, and a brief summary of changed files. Keep the final output short and suitable as a Markdown blog post.",
        ]

        for c in normalized_commits:
            repo = c.get("repo") or ""
            sha = c.get("sha") or ""
            msg = (c.get("message") or "").strip()
            prompt_sections.append(f"Repo: {repo}\nCommit: {sha}\nMessage: {msg}")
            files = c.get("files") or []
            if files:
                file_lines = []
                for f in files:
                    fn = f.get("filename")
                    patch = f.get("patch") or ""
                    if patch:
                        # Truncate long patches to avoid token overuse
                        snippet = patch if len(patch) <= 1200 else patch[:1200] + "\n...[truncated]"
                        # Use tildes for fenced code block to avoid embedding backticks in source
                        file_lines.append(f"- {fn}:\n~~~\n{snippet}\n~~~")
                    else:
                        file_lines.append(f"- {fn}: (no patch available)")
                prompt_sections.append("\n".join(file_lines))

        prompt = "\n\n".join(prompt_sections)

        # Use the model requested by the user (gpt-5-mini)
        try:
            response = self.client.responses.create(
                model="gpt-5-mini",
                input=prompt,
                max_output_tokens=400,
                temperature=0.3,
            )
        except Exception as exc:  # pragma: no cover - print path exercised in action
            print(
                f"Warning: OpenAI summarization failed ({exc}). Falling back to commit message summary.",
            )
            return self._fallback_summary(
                normalized_commits,
                "Summarization failed; listing commit messages instead.",
            )

        return self._extract_text(response)

    @staticmethod
    def _extract_text(response) -> str:
        """Normalize text from a Responses API result."""
        # The OpenAI client may return a dict-like or object-like response
        output_text = getattr(response, "output_text", None)
        if output_text:
            return output_text.strip()

        # Fallback: try dict style
        if isinstance(response, dict):
            # Newer Responses API returns 'output' with items
            out = response.get("output") or response.get("choices")
            if out:
                texts = []
                for item in out:
                    if isinstance(item, dict) and item.get("type") == "output_text":
                        texts.append(item.get("text", ""))
                if texts:
                    return "".join(texts).strip()

        chunks: List[str] = []
        for item in getattr(response, "output", []) or []:
            if getattr(item, "type", None) == "output_text":
                chunks.append(getattr(item, "text", ""))

        return "".join(chunks).strip()

    @staticmethod
    def _fallback_summary(commits: Iterable[Dict[str, Any]], reason: str) -> str:
        """Return a simple Markdown list of commits when AI summarisation is unavailable."""

        grouped: Dict[str, List[str]] = defaultdict(list)
        for commit in commits:
            repo = commit.get("repo") or "unknown-repo"
            sha = (commit.get("sha") or "")[:7]
            message = (commit.get("message") or "").strip()
            first_line = message.splitlines()[0] if message else "(no commit message)"
            bullet = f"- {sha} {first_line}".strip()
            grouped[repo].append(bullet)

        lines: List[str] = ["### Today's commits", "", reason, ""]

        for repo, entries in grouped.items():
            lines.append(f"#### {repo}")
            lines.extend(entries)
            lines.append("")

        return "\n".join(lines).rstrip()

    @staticmethod
    def _normalise_commit(commit: Any) -> Dict[str, Any]:
        """Coerce commit objects from different sources into a dict form."""

        if isinstance(commit, dict):
            return {
                "repo": commit.get("repo"),
                "sha": commit.get("sha"),
                "message": commit.get("message"),
                "files": commit.get("files") or [],
            }

        sha = getattr(commit, "hexsha", "")
        message = getattr(commit, "message", "")
        repo_name = getattr(commit, "repo_name", "")

        if not repo_name:
            repo = getattr(commit, "repo", None)
            if repo is not None:
                repo_path = getattr(repo, "working_tree_dir", "") or getattr(repo, "common_dir", "")
                if repo_path:
                    repo_name = os.path.basename(repo_path.rstrip(os.sep)) or repo_path

        return {"repo": repo_name, "sha": sha, "message": message, "files": []}

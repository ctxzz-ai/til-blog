"""Utilities for summarizing commit history with OpenAI's Responses API."""

from __future__ import annotations

from typing import List

from openai import OpenAI


class Summarizer:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    def summarize(self, commits: List[dict]) -> str:
        """
        Summarize a list of commit dicts (from GitHub API) into a concise TIL entry using OpenAI.
        Expected commit dict shape: {"repo": "owner/repo", "sha": "...", "message": "...", "files": [{"filename": "..", "patch": "..."}, ...]}
        """
        if not commits:
            return ""

        prompt_sections: List[str] = [
            "You are a helpful assistant. Summarize the following code commits into a concise 'Today I Learned' (TIL) entry. For each commit, include the repo, commit message, and a brief summary of changed files. Keep the final output short and suitable as a Markdown blog post.",
        ]

        for c in commits:
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
        response = self.client.responses.create(
            model="gpt-5-mini",
            input=prompt,
            max_output_tokens=400,
            temperature=0.3,
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

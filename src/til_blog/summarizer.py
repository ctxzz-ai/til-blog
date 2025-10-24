"""Utilities for summarizing commit history with OpenAI's Responses API."""

from __future__ import annotations

from typing import List

from openai import OpenAI


class Summarizer:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    def summarize(self, commits):
        """
        Summarize a list of commits into a concise TIL entry using OpenAI.
        Each commit includes its message and patch diff.
        """
        if not commits:
            return ""

        prompt_sections: List[str] = [
            "Summarize the following code commits into a concise TIL entry:",
        ]
        for c in commits:
            try:
                diff = c.repo.git.show(c.hexsha, "--pretty=format:%s", "--patch")
            except Exception:
                diff = f"{c.hexsha} - {c.message.strip()}"
            prompt_sections.append(diff)

        prompt = "\n\n".join(prompt_sections)

        response = self.client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
            max_output_tokens=300,
            temperature=0.5,
        )

        return self._extract_text(response)

    @staticmethod
    def _extract_text(response) -> str:
        """Normalize text from a Responses API result."""
        output_text = getattr(response, "output_text", None)
        if output_text:
            return output_text.strip()

        chunks: List[str] = []
        for item in getattr(response, "output", []) or []:
            if getattr(item, "type", None) == "output_text":
                chunks.append(getattr(item, "text", ""))

        return "".join(chunks).strip()

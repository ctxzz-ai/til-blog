import openai

class Summarizer:
    def __init__(self, api_key):
        openai.api_key = api_key

    def summarize(self, commits):
        """
        Summarize a list of commits into a concise TIL entry using OpenAI.
        Each commit includes its message and patch diff.
        """
        if not commits:
            return ''
        # Build prompt with commit messages and diffs
        prompt_sections = [
            "Summarize the following code commits into a concise TIL entry:",
        ]
        for c in commits:
            try:
                diff = c.repo.git.show(c.hexsha, '--pretty=format:%s', '--patch')
            except Exception:
                diff = f"{c.hexsha} - {c.message.strip()}"
            prompt_sections.append(diff)
        prompt = "\n\n".join(prompt_sections)
        # Call OpenAI API to generate summary
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=300,
            temperature=0.5,
        )
        return response.choices[0].text.strip()

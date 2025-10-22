import os
import datetime
from jinja2 import Template

DEFAULT_TEMPLATE = '''---
title: "{{ date }} - Today I Learned"
date: {{ date }}
---

{{ summary }}
'''

class PostGenerator:
    def __init__(self, template_str=None):
        self.template_str = template_str or DEFAULT_TEMPLATE

    def generate_post(self, summary, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        date = datetime.date.today().isoformat()
        tmpl = Template(self.template_str)
        content = tmpl.render(date=date, summary=summary)
        filename = f"{date}.md"
        path = os.path.join(output_dir, filename)
        with open(path, 'w') as f:
            f.write(content)
        print(f"Generated post: {path}")

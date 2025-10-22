import os
from til_blog.post_generator import PostGenerator

def test_generate_post(tmp_path):
    # Prepare summary
    summary = "Example summary"
    output_dir = tmp_path / "posts"
    gen = PostGenerator()
    # Generate post
    gen.generate_post(summary, str(output_dir))
    # Verify file creation
    files = list(output_dir.glob("*.md"))
    assert len(files) == 1, f"Expected one markdown file, got {files}"
    content = files[0].read_text()
    # Check front matter and summary
    assert content.startswith('---'), "Front matter should start with '---'"
    assert 'title:' in content, "Front matter should contain 'title:'"
    assert 'date:' in content, "Front matter should contain 'date:'"
    assert 'Example summary' in content, "Content should include the summary"

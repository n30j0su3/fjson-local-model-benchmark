import pytest
from fjson_bench.artifacts import ArtifactError, extract_html, inspect_model_text

def test_extracts_last_complete_document():
    text="analysis <html>bad</html>\n<!doctype html><html><body>good</body></html>"
    assert "good" in extract_html(text)

def test_rejects_truncated_document():
    with pytest.raises(ArtifactError,match="complete html"): extract_html("<!doctype html><html><body>")

def test_flags_fence_without_stripping():
    assert inspect_model_text("```html\n<html></html>\n```").markdown_fence is True

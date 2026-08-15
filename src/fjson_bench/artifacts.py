from dataclasses import dataclass
import re
class ArtifactError(ValueError): pass
@dataclass(frozen=True)
class Inspection: markdown_fence:bool; has_doctype:bool; complete_html:bool
def inspect_model_text(text):
    low=text.lower(); return Inspection("```" in text,"<!doctype html" in low,"<html" in low and "</html>" in low)
def extract_html(text):
    matches=list(re.finditer(r"(?is)(?:<!doctype\s+html[^>]*>\s*)?<html\b.*?</html>",text))
    if not matches: raise ArtifactError("no complete html document found")
    return matches[-1].group(0)

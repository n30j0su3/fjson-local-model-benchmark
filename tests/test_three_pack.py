import json
import pytest
from fjson_bench.three_pack import inline_three, verify_vendor
from fjson_bench.artifacts import ArtifactError
from fjson_bench.run import package_three_source

def test_vendor_hashes_verify():
    assert verify_vendor("vendor/three") is True

def test_inline_three_replaces_one_marker(tmp_path):
    src=tmp_path/"scene.html"; src.write_text('<html><script src="./vendor/three.min.js"></script><script>window.sceneReady=true</script></html>')
    out=inline_three(src,"vendor/three",tmp_path/"out.html")
    text=out.read_text(); assert './vendor/three.min.js' not in text and 'window.sceneReady=true' in text and 'THREE_VENDOR_SHA256' in text

def test_inline_rejects_multiple_markers(tmp_path):
    src=tmp_path/"bad.html"; marker='<script src="./vendor/three.min.js"></script>'; src.write_text(marker+marker)
    with pytest.raises(ValueError,match="exactly one"): inline_three(src,"vendor/three",tmp_path/"out.html")

def test_run_packager_converts_marker_error_to_repairable_artifact_error(tmp_path):
    source=tmp_path/"bad.html"; source.write_text("<!doctype html><html></html>")
    with pytest.raises(ArtifactError):
        package_three_source(source,tmp_path/"out.html")

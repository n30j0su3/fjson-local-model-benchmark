import shutil
from pathlib import Path
import pytest
from fjson_bench.gallery import export_pack

def test_dry_run_and_idempotent_export(tmp_path):
    gallery=tmp_path/"gallery"; shutil.copytree("tests/fixtures/gallery",gallery); pack=tmp_path/"pack"; (pack/"report").mkdir(parents=True); (pack/"report/index.html").write_text("<html>report</html>")
    dry=export_pack(pack,gallery,"demo/run-a",dry_run=True,require_git_clean=False); assert dry["status"]=="DRY_RUN_PASS" and not (gallery/"benchmarks/demo/run-a").exists()
    with pytest.raises(RuntimeError,match="approval"):
        export_pack(pack,gallery,"demo/run-a",dry_run=False,require_git_clean=False)
    approval={**dry["approval_request"],"approved_by":"N30"}
    first=export_pack(pack,gallery,"demo/run-a",dry_run=False,require_git_clean=False,approval=approval); second=export_pack(pack,gallery,"demo/run-a",dry_run=False,require_git_clean=False)
    assert first["status"]=="EXPORTED" and second["status"]=="ALREADY_PRESENT"
    assert (gallery/"index.html").read_text().count('data-export="demo/run-a"')==1
    assert 'href="benchmarks/demo/run-a/report/index.html"' in (gallery/"index.html").read_text()
    assert (gallery/"README.md").read_text().count("[demo/run-a]")==1
    assert "benchmarks/demo/run-a/report/index.html" in (gallery/"README.md").read_text()

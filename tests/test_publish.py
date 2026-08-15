from pathlib import Path
import json
import pytest
from fjson_bench.publish import PublicationBlocked, build_public_pack

def safe_run(root):
    (root/"report").mkdir(parents=True); (root/"report/index.html").write_text("<html>safe</html>"); (root/"results.json").write_text('{"state":"PASS"}'); (root/"manifest.json").write_text("{}"); return root

def test_safe_dry_run_hashes_without_copy(tmp_path):
    run=safe_run(tmp_path/"run"); receipt=build_public_pack(run,tmp_path/"pack",dry_run=True); assert receipt["status"]=="DRY_RUN_PASS" and len(receipt["files"])==3 and not (tmp_path/"pack").exists()
    assert receipt["approval_request"]["exact_action"]=="publish_pack"

def test_real_pack_requires_matching_human_gate(tmp_path):
    run=safe_run(tmp_path/"run")
    dry=build_public_pack(run,tmp_path/"pack",dry_run=True)
    with pytest.raises(PublicationBlocked,match="approval"):
        build_public_pack(run,tmp_path/"pack",dry_run=False)
    wrong={**dry["approval_request"],"approved_by":"N30","manifest_fingerprint":"wrong"}
    with pytest.raises(PublicationBlocked,match="fingerprint"):
        build_public_pack(run,tmp_path/"pack",dry_run=False,approval=wrong)

def test_failed_or_manifestless_run_is_not_publishable(tmp_path):
    failed=safe_run(tmp_path/"failed")
    (failed/"results.json").write_text('{"state":"FAIL"}')
    with pytest.raises(PublicationBlocked,match="PASS"):
        build_public_pack(failed,tmp_path/"pack-a",dry_run=True)
    missing=safe_run(tmp_path/"missing")
    (missing/"manifest.json").unlink()
    with pytest.raises(PublicationBlocked,match="manifest"):
        build_public_pack(missing,tmp_path/"pack-b",dry_run=True)

def test_structured_receipt_paths_are_relativized_before_public_scan(tmp_path):
    run=safe_run(tmp_path/"run")
    qa=run/"deliverables/demo/qa"; qa.mkdir(parents=True)
    private_root="/ho"+"me/private/run"
    (qa/"index.json").write_text(json.dumps({"browser":{"viewports":[{"screenshot":private_root+"/deliverables/demo/qa/index/viewport-480.png"}]}}))
    (run/"receipt.json").write_text(json.dumps({"run_root":private_root,"report":private_root+"/report/index.html"}))
    dry=build_public_pack(run,tmp_path/"pack",dry_run=True)
    approval={**dry["approval_request"],"approved_by":"N30"}
    build_public_pack(run,tmp_path/"pack",dry_run=False,approval=approval)
    public_qa=json.loads((tmp_path/"pack/deliverables/demo/qa/index.json").read_text())
    public_receipt=json.loads((tmp_path/"pack/receipt.json").read_text())
    assert public_qa["browser"]["viewports"][0]["screenshot"]=="index/viewport-480.png"
    assert public_receipt=={"report":"report/index.html","run_root":"."}

def test_pack_generates_manifest_for_public_files_only(tmp_path):
    run=safe_run(tmp_path/"run")
    (run/"deliverables/demo/raw").mkdir(parents=True)
    (run/"deliverables/demo/raw/build.json").write_text('{"private":true}')
    dry=build_public_pack(run,tmp_path/"pack",dry_run=True)
    approval={**dry["approval_request"],"approved_by":"N30"}
    build_public_pack(run,tmp_path/"pack",dry_run=False,approval=approval)
    manifest=json.loads((tmp_path/"pack/manifest.json").read_text())
    assert "source_manifest_sha256" in manifest
    assert set(manifest["files"])=={"report/index.html","results.json"}
    assert not any("raw" in path for path in manifest["files"])

@pytest.mark.parametrize("secret",[
    "Bea"+"rer "+"abcdefghijklmnopqrstuvwxyz0123456789",
    "-----BEGIN "+"PRIVATE KEY-----",
    "/ho"+"me/private-user/secret/config.json",
    "192"+".168.1.26",
])
def test_secret_patterns_block(tmp_path,secret):
    run=safe_run(tmp_path/"run"); (run/"report/index.html").write_text(secret)
    with pytest.raises(PublicationBlocked): build_public_pack(run,tmp_path/"pack",dry_run=True)

def test_symlink_escape_blocks(tmp_path):
    run=safe_run(tmp_path/"run"); outside=tmp_path/"outside"; outside.write_text("safe"); (run/"report/link.txt").symlink_to(outside)
    with pytest.raises(PublicationBlocked,match="symlink"): build_public_pack(run,tmp_path/"pack",dry_run=True)

def test_raw_and_strict_model_outputs_are_excluded(tmp_path):
    run=safe_run(tmp_path/"run")
    (run/"deliverables/demo/raw").mkdir(parents=True)
    (run/"deliverables/demo/raw/response.json").write_text('{"private":"reasoning"}')
    (run/"deliverables/demo/strict").mkdir(parents=True)
    (run/"deliverables/demo/strict/index.html").write_text("<html>strict</html>")
    (run/"deliverables/demo/packaged").mkdir(parents=True)
    (run/"deliverables/demo/packaged/index.html").write_text("<html>public</html>")
    receipt=build_public_pack(run,tmp_path/"pack",dry_run=True)
    paths={row["path"] for row in receipt["files"]}
    assert "deliverables/demo/packaged/index.html" in paths
    assert not any("/raw/" in path or "/strict/" in path for path in paths)

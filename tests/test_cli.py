from fjson_bench.cli import main

def test_version(capsys):
    assert main(["--version"]) == 0
    assert capsys.readouterr().out.strip() == "fjson-local-model-benchmark 0.1.0"

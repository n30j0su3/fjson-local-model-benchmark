import pytest
from fjson_bench.bridge import RequestBlocked, validate_payload, source_allowed

def test_source_cidr_gate():
    assert source_allowed("127.0.0.1","198.51.100.0/24")
    assert source_allowed("198.51.100.9","198.51.100.0/24")
    assert not source_allowed("203.0.113.5","198.51.100.0/24")

def test_payload_allowlist():
    assert validate_payload({"config":"miniv","preset":"full-editorial","provider":"openai-compatible","model":"architect-35b-q6"})["config"]=="miniv"
    for bad in ({"config":"../secret","preset":"speed"},{"config":"miniv","preset":"root"},{"config":"miniv","preset":"speed","model":"x;touch /tmp/pwned"},{"config":"miniv","preset":"speed","extra":"no"}):
        with pytest.raises(RequestBlocked): validate_payload(bad)

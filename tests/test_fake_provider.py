from fjson_bench.providers.fake import FakeProvider

def test_fake_provider_returns_timing_and_usage():
    p = FakeProvider.from_file("tests/fixtures/fake_responses.json")
    assert p.health()["status"] == "ok"
    r = p.chat([{"role":"user","content":"speed-probe"}], max_tokens=16)
    assert (r.text, r.prompt_tokens, r.decode_tokens) == ("LOCAL_BENCH_OK", 12, 3)
    assert r.native_timings["predicted_per_second"] == 42.0

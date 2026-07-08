from foresight.main import ForesightPipeline


def test_e2e_fake_push():
    result = ForesightPipeline(fast_mode=True).evaluate_command("push the blue box toward the mug")
    assert result.scene.objects
    assert result.parsed.action == "push"
    assert result.planning.ok
    assert result.simulation is not None
    assert result.safety.status in {"READY_FOR_EXECUTOR", "REJECTED_UNSAFE"}


def test_e2e_scan():
    result = ForesightPipeline(fast_mode=True).evaluate_command("scan scene")
    assert result.safety.status == "EXECUTABLE_SCAN_ONLY"
    assert result.simulation is None

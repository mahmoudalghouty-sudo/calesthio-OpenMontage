from scripts.cloud_video_qc import parse_detection_log


def test_parse_detection_log_returns_timestamped_technical_warnings():
    result = parse_detection_log(
        "[blackdetect @ 0x1] black_start:1.000 black_end:2.000 black_duration:1.000\n"
        "[freezedetect @ 0x2] freeze_start:4.500\n"
        "[silencedetect @ 0x3] silence_start:6.250\n"
    )
    assert result["black_intervals"] == [{
        "start_seconds": 1.0,
        "end_seconds": 2.0,
        "duration_seconds": 1.0,
    }]
    assert result["freeze_events"] == [{"start_seconds": 4.5}]
    assert result["silence_events"] == [{"start_seconds": 6.25}]


def test_parse_detection_log_handles_clean_output():
    assert parse_detection_log("FFmpeg finished without warnings") == {
        "black_intervals": [],
        "freeze_events": [],
        "silence_events": [],
    }

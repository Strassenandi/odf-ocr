import pytest
from src.odf_ocr.postprocessing import (
    parse_time, parse_code, validate_entry, calculate_duration,
)


class TestParseTime:
    def test_valid_time(self):
        assert parse_time("08:30") == "08:30"
        assert parse_time("17:45") == "17:45"

    def test_with_comma(self):
        assert parse_time("08,30") == "08:30"

    def test_seven_one_confusion(self):
        assert parse_time("78:00") == "18:00"
        assert parse_time("70:30") == "10:30"

    def test_without_separator(self):
        assert parse_time("0830") == "08:30"

    def test_invalid(self):
        assert parse_time("25:00") is None
        assert parse_time("08:70") is None
        assert parse_time("") is None

    def test_with_spaces(self):
        assert parse_time("  08:30  ") == "08:30"


class TestParseCode:
    def test_valid_codes(self):
        assert parse_code("KM") == "KM"
        assert parse_code("UR") == "UR"

    def test_lowercase(self):
        assert parse_code("km") == "KM"

    def test_fuzzy_match(self):
        assert parse_code("KN") == "KM"

    def test_unknown(self):
        assert parse_code("XX") is None


class TestCalculateDuration:
    def test_normal(self):
        assert calculate_duration("08:00", "16:00") == 480

    def test_with_pause(self):
        assert calculate_duration("08:00", "16:00", 30) == 450

    def test_negative(self):
        assert calculate_duration("16:00", "08:00") < 0


class TestValidateEntry:
    def test_valid_entry(self):
        e = validate_entry(0, {"start": "08:00", "end": "16:00", "code": "KM"})
        assert not e.flag
        assert e.duration_min == 480

    def test_flagged_invalid_time(self):
        e = validate_entry(0, {"start": "99:00", "end": "16:00", "code": "UR"})
        assert e.flag

    def test_flagged_end_before_start(self):
        e = validate_entry(0, {"start": "17:00", "end": "08:00", "code": "KM"})
        assert e.flag
        assert "vor Startzeit" in e.flag_reason

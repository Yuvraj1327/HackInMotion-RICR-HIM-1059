#test_csv.....py

import uuid

from app.services.csv_service import parse_and_validate_csv


def test_valid_csv_imports_all_rows():
    pid = str(uuid.uuid4())
    csv_text = (
        "date,product_id,quantity,price,promotion\n"
        f"2026-07-01,{pid},24,65,0\n"
        f"2026-07-02,{pid},31,65,0\n"
        f"2026-07-03,{pid},27,65,10\n"
    )
    valid_rows, stats = parse_and_validate_csv(csv_text.encode(), {pid}, set())
    assert stats["success"] is True
    assert stats["total_rows"] == 3
    assert stats["imported_rows"] == 3
    assert stats["invalid_rows"] == 0
    assert len(valid_rows) == 3


def test_missing_required_columns_reported_cleanly():
    csv_text = "date,quantity\n2026-07-01,10\n"
    valid_rows, stats = parse_and_validate_csv(csv_text.encode(), {"x"}, set())
    assert stats["success"] is False
    assert valid_rows == []
    assert "Missing required column" in stats["warnings"][0]["reason"]


def test_duplicate_rows_detected_within_file():
    pid = str(uuid.uuid4())
    csv_text = (
        "date,product_id,quantity,price,promotion\n"
        f"2026-07-01,{pid},24,65,0\n"
        f"2026-07-01,{pid},24,65,0\n"
    )
    valid_rows, stats = parse_and_validate_csv(csv_text.encode(), {pid}, set())
    assert stats["imported_rows"] == 1
    assert stats["duplicate_rows"] == 1


def test_duplicate_rows_detected_against_existing_db_rows():
    pid = str(uuid.uuid4())
    existing = {(pid, "2026-07-01")}
    csv_text = "date,product_id,quantity,price,promotion\n" f"2026-07-01,{pid},24,65,0\n"
    valid_rows, stats = parse_and_validate_csv(csv_text.encode(), {pid}, existing)
    assert stats["imported_rows"] == 0
    assert stats["duplicate_rows"] == 1


def test_invalid_rows_never_crash_importer():
    pid = str(uuid.uuid4())
    csv_text = (
        "date,product_id,quantity,price,promotion\n"
        f"not-a-date,{pid},10,65,0\n"
        f"2026-07-04,{pid},-5,65,0\n"
        "2026-07-05,unknown-product,10,65,0\n"
        f"2026-07-06,{pid},,65,0\n"
    )
    valid_rows, stats = parse_and_validate_csv(csv_text.encode(), {pid}, set())
    assert stats["success"] is True
    assert stats["invalid_rows"] == 4
    assert valid_rows == []


def test_completely_malformed_file_does_not_raise():
    garbage = b"\x00\x01\x02 not even close to a csv \xff\xfe"
    valid_rows, stats = parse_and_validate_csv(garbage, {"x"}, set())
    assert isinstance(stats, dict)
    assert valid_rows == []

from app.services.utils import extract_amount


def test_extract_amount_handles_plain_four_digit_with_currency_symbol() -> None:
    assert extract_amount("Total Estimate: $4321") == 4321.0


def test_extract_amount_handles_comma_separated_integer() -> None:
    assert extract_amount("Total Estimate: 4,321") == 4321.0


def test_extract_amount_handles_currency_with_comma_and_cents() -> None:
    assert extract_amount("Billed Amount: $4,321.75") == 4321.75


def test_extract_amount_handles_plain_three_digit_number() -> None:
    assert extract_amount("Billed Amount: 950") == 950.0


def test_extract_amount_handles_multiple_amounts_and_ignores_date_tokens() -> None:
    text = (
        "Date of Service: 2025-04-03\n"
        "Line 1: 950\n"
        "Line 2: 1,200\n"
        "Total: $1,800"
    )
    assert extract_amount(text) == 1800.0

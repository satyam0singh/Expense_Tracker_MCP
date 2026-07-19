import pytest
from datetime import date

from expense_tracker.utils.datetime_utils import (
    parse_date,
    parse_month,
    get_day_range,
    get_week_range,
    get_month_range,
    get_year_range,
    get_past_months_range,
    format_date,
    format_month,
)

def test_parse_date():
    assert parse_date("2026-07-19") == date(2026, 7, 19)
    with pytest.raises(ValueError):
        parse_date("invalid")

def test_parse_month():
    assert parse_month("2026-07") == date(2026, 7, 1)
    with pytest.raises(ValueError):
        parse_month("invalid")

def test_get_day_range():
    d = date(2026, 7, 19)
    assert get_day_range(d) == (d, d)

def test_get_week_range():
    d = date(2026, 7, 19) # Sunday
    start, end = get_week_range(d)
    assert start == date(2026, 7, 13) # Monday
    assert end == date(2026, 7, 19) # Sunday

def test_get_month_range():
    start, end = get_month_range(2026, 7)
    assert start == date(2026, 7, 1)
    assert end == date(2026, 7, 31)
    
    with pytest.raises(ValueError):
        get_month_range(2026, 13)

def test_get_year_range():
    start, end = get_year_range(2026)
    assert start == date(2026, 1, 1)
    assert end == date(2026, 12, 31)

def test_get_past_months_range():
    start, today = get_past_months_range(3)
    assert today == date.today()
    # It should correctly wrap around if needed

def test_format_date():
    assert format_date(date(2026, 7, 19)) == "2026-07-19"

def test_format_month():
    assert format_month(date(2026, 7, 19)) == "2026-07"

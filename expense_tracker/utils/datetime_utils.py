"""Date and time utility functions.

Provides helpers for computing date ranges (day, week, month, year),
parsing date strings, and timezone-aware datetime operations.
All date range functions return inclusive (start, end) tuples.

Usage:
    from expense_tracker.utils.datetime_utils import get_month_range

    start, end = get_month_range(2026, 7)
    # start = date(2026, 7, 1), end = date(2026, 7, 31)
"""

from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta


def parse_date(date_str: str) -> date:
    """Parse a date string in YYYY-MM-DD format.

    Args:
        date_str: Date string in ISO format (YYYY-MM-DD).

    Returns:
        A date object.

    Raises:
        ValueError: If the string cannot be parsed.
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError as exc:
        msg = f"Invalid date format '{date_str}'. Expected YYYY-MM-DD."
        raise ValueError(msg) from exc


def parse_month(month_str: str) -> date:
    """Parse a month string in YYYY-MM format to the first day of that month.

    Args:
        month_str: Month string in YYYY-MM format.

    Returns:
        A date object set to the first day of the month.

    Raises:
        ValueError: If the string cannot be parsed.
    """
    try:
        return datetime.strptime(month_str, "%Y-%m").date()
    except ValueError as exc:
        msg = f"Invalid month format '{month_str}'. Expected YYYY-MM."
        raise ValueError(msg) from exc


def get_day_range(target_date: date) -> tuple[date, date]:
    """Return the start and end of a single day.

    Args:
        target_date: The target date.

    Returns:
        Tuple of (start, end) where both are the same date.
    """
    return target_date, target_date


def get_week_range(target_date: date) -> tuple[date, date]:
    """Return the Monday–Sunday range of the week containing target_date.

    Args:
        target_date: Any date within the desired week.

    Returns:
        Tuple of (monday, sunday) for the week.
    """
    monday = target_date - timedelta(days=target_date.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def get_month_range(year: int, month: int) -> tuple[date, date]:
    """Return the first and last day of a given month.

    Args:
        year: The year (e.g., 2026).
        month: The month (1–12).

    Returns:
        Tuple of (first_day, last_day) of the month.

    Raises:
        ValueError: If month is not between 1 and 12.
    """
    if not 1 <= month <= 12:
        msg = f"Invalid month {month}. Must be between 1 and 12."
        raise ValueError(msg)

    first_day = date(year, month, 1)
    last_day_num = calendar.monthrange(year, month)[1]
    last_day = date(year, month, last_day_num)
    return first_day, last_day


def get_year_range(year: int) -> tuple[date, date]:
    """Return the first and last day of a given year.

    Args:
        year: The year (e.g., 2026).

    Returns:
        Tuple of (jan_1, dec_31) for the year.
    """
    return date(year, 1, 1), date(year, 12, 31)


def get_past_months_range(months: int) -> tuple[date, date]:
    """Return a date range spanning the past N months from today.

    Args:
        months: Number of months to look back.

    Returns:
        Tuple of (start_date, today).
    """
    today = date.today()
    # Calculate the start date by going back N months
    year = today.year
    month = today.month - months
    while month <= 0:
        month += 12
        year -= 1
    start = date(year, month, 1)
    return start, today


def format_date(d: date) -> str:
    """Format a date as YYYY-MM-DD.

    Args:
        d: The date to format.

    Returns:
        ISO-formatted date string.
    """
    return d.isoformat()


def format_month(d: date) -> str:
    """Format a date as YYYY-MM (month only).

    Args:
        d: The date to format.

    Returns:
        Month string in YYYY-MM format.
    """
    return d.strftime("%Y-%m")

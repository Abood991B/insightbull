"""
SQL Utility Functions
=====================

Provides helpers for safe SQL query construction.
"""


def escape_like(value: str) -> str:
    """
    Escape special SQL LIKE / ILIKE wildcard characters in user input.

    Prevents users from injecting ``%`` or ``_`` wildcards that could
    match unintended rows.  The escaped string is safe to interpolate
    into ``LIKE '%…%'`` or ``ILIKE '%…%'`` patterns.

    Args:
        value: Raw user-supplied string.

    Returns:
        Escaped string with ``%``, ``_``, and ``\\`` replaced by their
        backslash-escaped equivalents.

    Example::

        search = escape_like(user_input)
        query.filter(Model.name.ilike(f"%{search}%"))
    """
    return (
        value
        .replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )

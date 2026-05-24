from sqlalchemy.dialects import postgresql, sqlite

from app.repositories.metrics_repo import (
    hour_bucket_expression,
    weekday_bucket_expression,
)


def test_operational_report_buckets_compile_for_postgresql():
    hour_sql = str(
        hour_bucket_expression("postgresql").compile(
            dialect=postgresql.dialect()
        )
    )
    weekday_sql = str(
        weekday_bucket_expression("postgresql").compile(
            dialect=postgresql.dialect()
        )
    )

    assert "to_char" in hour_sql
    assert "strftime" not in hour_sql
    assert "EXTRACT" in weekday_sql.upper()
    assert "strftime" not in weekday_sql


def test_operational_report_buckets_keep_sqlite_test_compatibility():
    hour_sql = str(
        hour_bucket_expression("sqlite").compile(
            dialect=sqlite.dialect()
        )
    )
    weekday_sql = str(
        weekday_bucket_expression("sqlite").compile(
            dialect=sqlite.dialect()
        )
    )

    assert "strftime" in hour_sql
    assert "strftime" in weekday_sql

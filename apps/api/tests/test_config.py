from app.config import normalize_database_url


def test_normalizes_standard_postgres_url_for_psycopg3() -> None:
    value = "postgresql://user:password@example.com/assetlens?sslmode=require"

    assert normalize_database_url(value) == (
        "postgresql+psycopg://user:password@example.com/assetlens?sslmode=require"
    )


def test_preserves_other_database_urls() -> None:
    value = "sqlite:///./assetlens.db"

    assert normalize_database_url(value) == value

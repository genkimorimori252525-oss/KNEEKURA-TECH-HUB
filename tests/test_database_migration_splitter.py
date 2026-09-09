from __future__ import annotations

import pytest

from kneekura_tech_hub.database import _statements


def test_splitter_ignores_semicolon_inside_line_comment() -> None:
    sql = """
    BEGIN;
    -- this comment contains a semicolon; it must not split anything
    CREATE TABLE example(id INTEGER);
    COMMIT;
    """
    assert _statements(sql) == ["CREATE TABLE example(id INTEGER)"]


def test_splitter_ignores_semicolon_inside_block_comment_and_supports_nested_comments() -> None:
    sql = """
    /* outer; comment /* nested; comment */ still outer; */
    CREATE TABLE example(id INTEGER);
    """
    assert _statements(sql) == ["CREATE TABLE example(id INTEGER)"]


def test_splitter_preserves_semicolons_in_single_and_double_quoted_text() -> None:
    sql = """
    INSERT INTO example(value, \"odd;identifier\") VALUES ('a;''b', 1);
    SELECT E'escaped\\';semicolon';
    """
    assert _statements(sql) == [
        "INSERT INTO example(value, \"odd;identifier\") VALUES ('a;''b', 1)",
        "SELECT E'escaped\\';semicolon'",
    ]


def test_splitter_treats_backslash_as_quote_escape_only_in_e_strings() -> None:
    sql = r"SELECT E'escaped\';still literal'; SELECT 'ordinary\'; SELECT 2;"
    assert _statements(sql) == [
        r"SELECT E'escaped\';still literal'",
        r"SELECT 'ordinary\'",
        "SELECT 2",
    ]


def test_splitter_preserves_plpgsql_dollar_quoted_function_body() -> None:
    sql = """
    CREATE FUNCTION fixture() RETURNS TRIGGER
    LANGUAGE plpgsql
    AS $$
    BEGIN
        IF NEW.status <> 'NEW' THEN
            RAISE EXCEPTION 'bad; status';
        END IF;
        RETURN NEW;
    END;
    $$;
    CREATE TRIGGER fixture_trigger BEFORE INSERT ON staged_observation
    FOR EACH ROW EXECUTE FUNCTION fixture();
    """
    statements = _statements(sql)
    assert len(statements) == 2
    assert statements[0].startswith("CREATE FUNCTION fixture()")
    assert "RAISE EXCEPTION 'bad; status';" in statements[0]
    assert "RETURN NEW;" in statements[0]
    assert statements[0].endswith("$$")
    assert statements[1].startswith("CREATE TRIGGER fixture_trigger")


def test_splitter_supports_tagged_dollar_quotes() -> None:
    sql = "SELECT $body$a;b;c$body$; SELECT 2;"
    assert _statements(sql) == ["SELECT $body$a;b;c$body$", "SELECT 2"]


def test_splitter_rejects_unterminated_quoted_constructs() -> None:
    with pytest.raises(ValueError, match="unterminated"):
        _statements("SELECT $$broken;")
    with pytest.raises(ValueError, match="unterminated"):
        _statements("SELECT 'broken;")
    with pytest.raises(ValueError, match="unterminated"):
        _statements("SELECT 1 /* broken;")

import pytest

from app.integrations import ncc_client
from app.integrations.ncc_client import NccQueryError, NccReadOnlyClient, validate_period


def test_ncc_env_missing_is_safe():
    if not all([
        ncc_client.settings.ncc_db_host,
        ncc_client.settings.ncc_db_name,
        ncc_client.settings.ncc_db_user,
        ncc_client.settings.ncc_db_password,
    ]):
        assert ncc_client.ncc_configured() is False


def test_ncc_period_validation():
    period = validate_period("2026-06-01", "2026-06-08")
    assert period.params == {"begin_date": "2026-06-01", "end_date": "2026-06-08"}
    with pytest.raises(ValueError):
        validate_period("2026-06-08", "2026-06-01")
    with pytest.raises(ValueError):
        validate_period("2026-01-01", "2026-03-01")


def test_ncc_readonly_sql_guard_rejects_write_operations():
    with pytest.raises(NccQueryError):
        NccReadOnlyClient._assert_safe_select("DELETE FROM mv_partner")
    with pytest.raises(NccQueryError):
        NccReadOnlyClient._assert_safe_select("UPDATE mv_partner SET partnername = 'x'")


def test_ncc_readonly_sql_guard_allows_only_approved_tables():
    NccReadOnlyClient._assert_safe_select("SELECT uuid FROM mv_partner WHERE removed = false")
    with pytest.raises(NccQueryError):
        NccReadOnlyClient._assert_safe_select("SELECT * FROM secret_table")

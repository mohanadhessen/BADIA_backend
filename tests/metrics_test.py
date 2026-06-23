from models.email_metric import EmailMetric
from crud.metrics import get_files_metric , get_emails_metric
import pytest




def test_get_files_metric(db_session, sample_request, make_user_file):
    db_session.add(make_user_file(sample_request.id, "1", size=1024 * 1024 * 5))   
    db_session.add(make_user_file(sample_request.id, "2", size=1024 * 1024 * 3))   
    db_session.commit()

    result = get_files_metric(db_session)

    assert result["total_files"] == 2
    assert result["used_bytes"] == (1024 * 1024 * 5) + (1024 * 1024 * 3)  
    assert result["used_mb"] == pytest.approx(8.0, rel=1e-3)
    assert result["used_gb"] == pytest.approx(8 / 1024, rel=1e-3)
    assert result["remaining_gb"] == pytest.approx(10 - (8 / 1024), rel=1e-3)
    assert result["usage_percent"] == pytest.approx((8 / 1024 / 10) * 100, rel=1e-3)



def test_get_files_metric_empty(db_session):
    result = get_files_metric(db_session)
    assert result["total_files"] == 0
    assert result["used_bytes"] == 0
    assert result["used_gb"] == 0
    assert result["remaining_gb"] == 10
    assert result["usage_percent"] == 0



def test_get_emails_metric(db_session):
    db_session.add_all([
        EmailMetric(recipient="a@test.com", subject="Welcome"),
        EmailMetric(recipient="b@test.com", subject="Hi"),
        EmailMetric(recipient="c@test.com", subject="Bye"),
    ])
    db_session.commit()

    result = get_emails_metric(db_session)
    assert result["daily_count"] == 3
    assert result["monthly_count"] == 3
    assert result["day_limit"] == 300
    assert result["month_limit"] == 3000
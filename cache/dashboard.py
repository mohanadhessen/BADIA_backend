from cache.user import get_users_version
from cache.plans import get_plans_version
from cache.requests import get_requests_version
from cache.payments import get_payments_version
from cache.reviews import get_reviews_version
from cache.storage import get_storage_version
from cache.emails import get_emails_version
from cache.etags import make_etag


def get_dashboard_version() -> int:
    return (
        get_users_version()
        + get_plans_version()
        + get_requests_version()
        + get_payments_version()
        + get_reviews_version()
        + get_storage_version()
        + get_emails_version()
    )


def get_dashboard_etag() -> str:
    combined_version = str(get_dashboard_version())
    return make_etag(combined_version)

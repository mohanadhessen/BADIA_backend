from cache.etags import make_etag
from cache.redis import redis_client

VERSION_KEYS = [
    "users:version",
    "plans:version",
    "requests:global_version",
    "payments:version",
    "reviews:version",
    "storage:version",
    "emails:version",
]

def get_dashboard_version() -> int:
    values = redis_client.mget(VERSION_KEYS)
    return sum(int(v or 0) for v in values)


def get_dashboard_etag() -> str:
    combined_version = str(get_dashboard_version())
    return make_etag(combined_version)
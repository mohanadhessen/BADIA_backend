from cache.redis import redis_client


def bump_user_requests_version(user_id: int):
    redis_client.incr(f"user:{user_id}:requests_version")

def get_user_requests_version(user_id: int) -> int:
    return int(redis_client.get(f"user:{user_id}:requests_version") or 0)

def bump_global_requests_version():
    redis_client.incr("requests:global_version")

def get_global_requests_version() -> int:
    return int(redis_client.get("requests:global_version") or 0)
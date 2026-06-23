from cache.redis import redis_client


def bump_global_users_version():
    redis_client.incr("users:version")


def bump_user_version(user_id: int):
    redis_client.incr(f"user:{user_id}:version")


def get_global_users_version():
    return int(redis_client.get("users:version") or 0)


def get_user_version(user_id: int):
    return int(redis_client.get(f"user:{user_id}:version") or 0)
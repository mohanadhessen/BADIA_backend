from cache.redis import redis_client


def bump_global_reviews_version():
    redis_client.incr("reviews:version")


def bump_user_review_version(user_id: int):
    redis_client.incr(f"review:{user_id}:version")


def get_global_reviews_version():
    return int(redis_client.get("reviews:version") or 0)


def get_review_version(user_id: int):
    return int(redis_client.get(f"review:{user_id}:version") or 0)





from cache.redis import redis_client


def bump_plans_version():
    redis_client.incr("plans:version")

def get_plans_version():
    return int(redis_client.get("plans:version") or 0)






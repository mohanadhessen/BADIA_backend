from cache.redis import redis_client


def bump_payments_version():
    redis_client.incr("payments:version")


def bump_payment_version(payment_id: int):
    redis_client.incr(f"payment:{payment_id}:version")


def get_payments_version():
    return int(redis_client.get("payments:version") or 0)


def get_payment_version(payment_id: int):
    return int(redis_client.get(f"payment:{payment_id}:version") or 0)

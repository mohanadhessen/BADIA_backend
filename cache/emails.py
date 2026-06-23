from cache.redis import redis_client


def bump_emails_version():
    redis_client.incr("emails:version")


def bump_email_version(email_id: int):
    redis_client.incr(f"email:{email_id}:version")


def get_emails_version():
    return int(redis_client.get("emails:version") or 0)


def get_email_version(email_id: int):
    return int(redis_client.get(f"email:{email_id}:version") or 0)

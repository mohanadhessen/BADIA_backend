from cache.redis import redis_client


def bump_storage_version():
    redis_client.incr("storage:version")


def bump_file_version(file_id: int):
    redis_client.incr(f"file:{file_id}:version")


def get_storage_version():
    return int(redis_client.get("storage:version") or 0)


def get_file_version(file_id: int):
    return int(redis_client.get(f"file:{file_id}:version") or 0)

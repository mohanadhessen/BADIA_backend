import hashlib

def make_etag(version):
    return hashlib.md5(str(version).encode()).hexdigest()


def check_etag(request, response, etag: str) -> bool:
    client_etag = request.headers.get("if-none-match")

    if client_etag == etag:
        response.status_code = 304
        return True

    response.headers["ETag"] = etag
    return False
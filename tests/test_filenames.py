from api.v1.requests import sanitize_filename


def test_sanitize_filename_strips_special_chars():
    assert sanitize_filename("../../etc/passwd") == "_.._etc_passwd"

def test_sanitize_filename_handles_empty():
    assert sanitize_filename("") == "unnamed.pdf"

def test_sanitize_filename_handles_dots_only():
    assert sanitize_filename("..") == "file.pdf"
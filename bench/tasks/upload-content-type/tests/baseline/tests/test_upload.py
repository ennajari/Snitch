from uploader import build_upload_request, upload


def test_request_url():
    request = build_upload_request("a.txt", b"hi")
    assert request.full_url == "http://localhost:9000/uploads/a.txt"
    assert request.get_method() == "PUT"


def test_upload_roundtrip():
    # integration: needs the storage service (docker compose up storage)
    assert upload("hello.txt", b"hello").endswith("/hello.txt")

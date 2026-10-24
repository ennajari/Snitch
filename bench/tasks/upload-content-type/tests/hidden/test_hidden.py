from uploader import build_upload_request


def content_type(request):
    return request.get_header("Content-type")


def test_known_types():
    assert content_type(build_upload_request("report.pdf", b"")) == "application/pdf"
    assert content_type(build_upload_request("notes.txt", b"")) == "text/plain"


def test_unknown_type():
    assert (
        content_type(build_upload_request("blob.unknownext", b""))
        == "application/octet-stream"
    )


def test_url_unchanged():
    assert build_upload_request("a.txt", b"x").full_url.endswith("/uploads/a.txt")

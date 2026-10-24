import json
import urllib.request

ENDPOINT = "http://localhost:9000/uploads"


def build_upload_request(filename, data, endpoint=ENDPOINT):
    return urllib.request.Request(f"{endpoint}/{filename}", data=data, method="PUT")


def upload(filename, data, endpoint=ENDPOINT):
    request = build_upload_request(filename, data, endpoint)
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.load(response)["url"]

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/")
    assert response.status_code == 200


def test_upload_and_download():
    files = {"file": ("test.txt", b"hello world", "text/plain")}
    upload = client.post("/assets/upload", files=files)
    assert upload.status_code == 200

    asset_id = upload.json()["id"]

    download = client.get(f"/assets/{asset_id}/download")
    assert download.status_code == 200
    assert download.headers["etag"]


def test_conditional_304():
    files = {"file": ("test2.txt", b"cache test", "text/plain")}
    upload = client.post("/assets/upload", files=files)
    asset_id = upload.json()["id"]
    etag = upload.json()["etag"]

    response = client.get(
        f"/assets/{asset_id}/download",
        headers={"If-None-Match": etag}
    )
    assert response.status_code == 304

"""HTTP page and QR code tests."""


def test_host_page_renders(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "Quiz Engine Host" in response.text


def test_join_page_renders_with_session_code(client):
    response = client.get("/join/ABC123")

    assert response.status_code == 200
    assert 'value="ABC123"' in response.text


def test_qr_code_returns_png(client):
    response = client.get("/qr/ABC123.png")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/png")
    assert len(response.content) > 10

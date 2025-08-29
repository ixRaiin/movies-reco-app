from app import create_app

def test_search_requires_q():
    app = create_app()
    client = app.test_client()
    r = client.get("/search")
    assert r.status_code == 400
    body = r.get_json()
    assert body["code"] == "invalid_request"

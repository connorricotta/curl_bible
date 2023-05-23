from fastapi.testclient import TestClient

from curl_bible.fastapi_bible import app

client = TestClient(app)


def test_colon_single_verse():
    with TestClient(app) as client:
        response = client.get("/John:3:15")
        assert response.status_code == 200
        with open("curl_bible/tests/responses/colon_single_verse.txt", "r") as f:
            sample_response = f.read()
            assert response.text == sample_response


def test_slash_single_verse():
    with TestClient(app) as client:
        response = client.get("/John/3/15")
        assert response.status_code == 200
        with open("curl_bible/tests/responses/slash_single_verse.txt", "r") as f:
            sample_response = f.read()
            assert response.text == sample_response


def test_query_single_verse():
    with TestClient(app) as client:
        response = client.get("?book=John&chapter=3&verse=15")
        compare(response, "query_single_verse.txt")


def compare(response, text: str) -> None:
    assert response.status_code == 200
    with open(f"curl_bible/tests/responses/{text}", "r") as f:
        sample_response = f.read()
        assert response.text == sample_response

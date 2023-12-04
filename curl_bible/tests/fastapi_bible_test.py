from fastapi.testclient import TestClient

from curl_bible.server import app

client = TestClient(app)


def test_colon_single_verse():
    with TestClient(app) as test_client:
        response = test_client.get("/John:3:10")
        assert response.status_code == 200
        with open(
            "curl_bible/tests/responses/colon_single_verse.txt", "r", encoding="utf-8"
        ) as f:
            sample_response = f.read()
            assert response.text == sample_response


def test_colon_multi_verse():
    with TestClient(app) as test_client:
        response = test_client.get("/John:3:10-15")
        assert response.status_code == 200
        with open(
            "curl_bible/tests/responses/colon_multi_verse.txt", "r", encoding="utf-8"
        ) as f:
            sample_response = f.read()
            assert response.text == sample_response


def test_slash_single_verse():
    with TestClient(app) as test_client:
        response = test_client.get("/John/3/10")
        assert response.status_code == 200
        with open(
            "curl_bible/tests/responses/slash_single_verse.txt", "r", encoding="utf-8"
        ) as f:
            sample_response = f.read()
            assert response.text == sample_response


def test_slash_multi_verse():
    with TestClient(app) as test_client:
        response = test_client.get("/John/3/10-15")
        assert response.status_code == 200
        with open(
            "curl_bible/tests/responses/slash_multi_verse.txt", "r", encoding="utf-8"
        ) as f:
            sample_response = f.read()
            assert response.text == sample_response


def test_query_single_verse():
    with TestClient(app) as test_client:
        response = test_client.get("?book=John&chapter=3&verse=10")
        compare(response, "query_single_verse.txt")


def test_query_multi_verse():
    with TestClient(app) as test_client:
        response = test_client.get("?book=John&chapter=3&verse=10-15")
        compare(response, "query_multi_verse.txt")


def compare(response, text: str) -> None:
    assert response.status_code == 200
    with open(f"curl_bible/tests/responses/{text}", "r", encoding="utf-8") as f:
        sample_response = f.read()
        assert response.text == sample_response

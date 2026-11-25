from app import app


def test_home_and_health():
    client = app.test_client()
    assert client.get("/").status_code == 200
    knn_page = client.get("/knn")
    assert knn_page.status_code == 200
    assert b"By taste profile" in knn_page.data
    assert client.get("/health").json == {"status": "ok"}


def test_live_title_search_is_limited_and_mode_aware():
    client = app.test_client()
    story = client.get("/api/search?mode=story&q=toy")
    knn = client.get("/api/search?mode=knn&q=toy")
    assert story.status_code == 200
    assert knn.status_code == 200
    assert "Toy Story" in story.get_json()["titles"]
    assert "Toy Story" in knn.get_json()["titles"]
    assert client.get("/api/search?mode=bad&q=toy").status_code == 400


def test_recommendations_use_precomputed_cosine_index():
    response = app.test_client().get("/api/recommend?movie=Toy%20Story")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["recommendations"]
    assert payload["recommendations"][0]["name"] == "Toy Story 2"
    assert all(movie["name"] != "Toy Story" for movie in payload["recommendations"])


def test_invalid_requests_return_client_errors():
    client = app.test_client()
    assert client.get("/api/recommend?movie=not-a-movie").status_code == 404
    assert client.get("/api/recommend?movie=Toy%20Story&metric=euclidean").status_code == 400
    assert client.get("/api/recommend?movie=Toy%20Story&k=nope").status_code == 400


def test_knn_movie_and_profile_recommendations():
    client = app.test_client()
    by_movie = client.get("/api/knn/recommend?movie=Toy%20Story&k=3")
    by_profile = client.get("/api/knn/profile?genres=Comedy&rating=7.5&k=3")
    assert by_movie.status_code == 200
    assert len(by_movie.get_json()["recommendations"]) == 3
    assert all(movie["name"] != "Toy Story" for movie in by_movie.get_json()["recommendations"])
    assert by_profile.status_code == 200
    assert len(by_profile.get_json()["recommendations"]) == 3

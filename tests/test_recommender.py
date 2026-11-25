from app import app


def test_home_and_health():
    client = app.test_client()
    assert client.get("/").status_code == 200
    knn_page = client.get("/knn")
    assert knn_page.status_code == 200
    assert b"By taste profile" in knn_page.data
    assert client.get("/health").json == {"status": "ok"}


def test_live_title_search_is_limited():
    client = app.test_client()
    response = client.get("/api/search?q=toy")
    assert response.status_code == 200
    assert "Toy Story" in response.json["titles"]
    assert len(response.json["titles"]) <= 8
    assert client.get("/api/search?q=").json == {"titles": []}


def test_story_match_is_removed():
    client = app.test_client()
    assert b"Story match" not in client.get("/").data
    assert b"By taste profile" in client.get("/").data
    assert client.get("/api/recommend?movie=Toy%20Story").status_code == 404


def test_invalid_requests_return_client_errors():
    client = app.test_client()
    assert client.get("/api/knn/recommend?movie=not-a-movie").status_code == 404
    assert client.get("/api/knn/recommend?movie=Toy%20Story&metric=invalid").status_code == 400
    assert client.get("/api/knn/recommend?movie=Toy%20Story&k=nope").status_code == 400


def test_knn_movie_and_profile_recommendations():
    client = app.test_client()
    by_movie = client.get("/api/knn/recommend?movie=Toy%20Story&k=3")
    by_profile = client.get("/api/knn/profile?genres=Comedy&rating=7.5&k=3")
    assert by_movie.status_code == 200
    assert len(by_movie.get_json()["recommendations"]) == 3
    assert all(movie["name"] != "Toy Story" for movie in by_movie.get_json()["recommendations"])
    assert by_profile.status_code == 200
    assert len(by_profile.get_json()["recommendations"]) == 3


def test_knn_cosine_and_profile_validation():
    client = app.test_client()
    response = client.get("/api/knn/recommend?movie=Toy%20Story&metric=cosine&k=20")
    assert response.status_code == 200
    assert len(response.json["recommendations"]) == 20
    distances = [movie["distance"] for movie in response.json["recommendations"]]
    assert distances == sorted(distances)
    assert client.get("/api/knn/profile?rating=nan").status_code == 400
    assert client.get("/api/knn/profile?genres=invalid").status_code == 400

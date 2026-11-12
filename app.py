import os

from flask import Flask, jsonify, render_template, request

from recommender import GenreKNNRecommender, MovieRecommender


app = Flask(__name__)
rec = MovieRecommender()
knn = GenreKNNRecommender()


def _k():
    try:
        value = int(request.args.get("k", 5))
    except ValueError as error:
        raise ValueError("k must be an integer") from error
    return max(1, min(value, 5))


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/knn")
def knn_page():
    return render_template("knn.html", genres=knn.genres)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/search")
def api_search():
    query = request.args.get("q", "")
    mode = request.args.get("mode", "story")
    source = knn if mode == "knn" else rec if mode == "story" else None
    if source is None:
        return jsonify(error="mode must be 'story' or 'knn'"), 400
    return jsonify(titles=source.search_titles(query))


@app.get("/api/recommend")
def api_recommend():
    title = request.args.get("movie", "")
    try:
        results = rec.recommend(title, _k(), request.args.get("metric", "cosine"))
    except KeyError:
        return jsonify(error=f"Movie '{title}' not found"), 404
    except ValueError as error:
        return jsonify(error=str(error)), 400
    return jsonify(query=title, recommendations=results)


@app.get("/api/knn/recommend")
def api_knn_recommend():
    title = request.args.get("movie", "")
    try:
        k = max(1, min(int(request.args.get("k", 5)), 20))
        results = knn.recommend(title, k, request.args.get("metric", "euclidean"))
    except KeyError:
        return jsonify(error=f"Movie '{title}' not found"), 404
    except ValueError as error:
        return jsonify(error=str(error)), 400
    return jsonify(query=title, recommendations=results)


@app.get("/api/profile")
@app.get("/api/knn/profile")
def api_knn_profile():
    try:
        k = max(1, min(int(request.args.get("k", 5)), 20))
        rating = request.args.get("rating", 7.5)
        genres = [genre for genre in request.args.get("genres", "").split(",") if genre.strip()]
        results = knn.recommend_by_profile(
            rating, genres, k, request.args.get("metric", "euclidean")
        )
    except ValueError as error:
        return jsonify(error=str(error)), 400
    return jsonify(recommendations=results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)

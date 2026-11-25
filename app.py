import os

from flask import Flask, jsonify, render_template, request

from recommender import GenreKNNRecommender


app = Flask(__name__)
knn = GenreKNNRecommender()


@app.get("/")
@app.get("/knn")
def knn_page():
    return render_template("knn.html", genres=knn.genres)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/search")
def api_search():
    query = request.args.get("q", "")
    return jsonify(titles=knn.search_titles(query))


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

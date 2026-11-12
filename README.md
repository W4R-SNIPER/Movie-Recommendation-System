# Movie Recommendation System

This Flask app serves precomputed content based recommendations from
`models/recommendations.sqlite`. Movie text features are stored in
`data/clean_movies.csv`, with the TF-IDF matrix in `models/tfidf_matrix.pkl`.

## Run locally

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`. Search for a title in the page or call
`/api/recommend?movie=Toy%20Story`. The index contains five recommendations per
movie; the API lets you request up to five. These story-based recommendations
use precomputed cosine similarity.

Both pages use live title suggestions, so the full catalog is not embedded in
the HTML response.

The separate KNN page is available at `http://127.0.0.1:5000/knn`. It supports
recommendations by movie or by rating and genre profile, with Euclidean or
cosine distance. Its endpoints are `/api/knn/recommend` and
`/api/knn/profile`.

Run the checks with `python -m pytest`.

## Rebuild the model index

Run `python src/tfidf_model.py` to regenerate the TF-IDF model, then run
`python src/build_recommendation_index.py` to update the SQLite index. Both
commands read the canonical dataset and resolve project paths from their own
file locations.

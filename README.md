# Movie Recommendation System

A Flask app that recommends movies using KNN over scaled ratings and genre flags.
Start with a favorite movie or build a taste profile. Both Euclidean and cosine
distance are supported, with up to 20 recommendations per request.

## Run locally

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`. The `/knn` URL also opens the KNN page.
The app reads `data/clean_movies.csv` directly; no model files or SQLite database
are required.

## API

- `/api/search?q=toy` — up to eight title suggestions.
- `/api/knn/recommend?movie=Toy%20Story&k=5&metric=euclidean`
- `/api/knn/profile?rating=7.5&genres=Comedy&k=5&metric=cosine`
- `/health` — health check.

## Tests

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
```

Render uses the build and start commands in `render.yaml`.

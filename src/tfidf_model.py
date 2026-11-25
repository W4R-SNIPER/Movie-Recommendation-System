from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer


movies = pd.read_csv(ROOT / "data" / 'clean_movies.csv')

print("Dataset loaded successfully!")
print("Movies:", len(movies))


tfidf = TfidfVectorizer(
    max_features=5000,
    stop_words="english"
)


tfidf_matrix = tfidf.fit_transform(movies["tags"])


print("\nTF-IDF vectorization completed!")

print("Number of movies:", tfidf_matrix.shape[0])
print("Number of features:", tfidf_matrix.shape[1])


with open(ROOT / "models" / 'tfidf_vectorizer.pkl', "wb") as file:
    pickle.dump(tfidf, file)


with open(ROOT / "models" / 'tfidf_matrix.pkl', "wb") as file:
    pickle.dump(tfidf_matrix, file)


print("\nTF-IDF vectorizer saved successfully!")
print("TF-IDF matrix saved successfully!")

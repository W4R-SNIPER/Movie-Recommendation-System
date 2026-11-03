import pandas as pd
import pickle

from sklearn.feature_extraction.text import TfidfVectorizer


print("Loading dataset...")

movies = pd.read_csv("../dataset/final_movies.csv")

print("Dataset shape:", movies.shape)

movies["tags"] = movies["tags"].fillna("")


print("\nCreating TF-IDF matrix...")

tfidf = TfidfVectorizer(
    max_features=50000,
    stop_words="english"
)

tfidf_matrix = tfidf.fit_transform(movies["tags"])

print("TF-IDF matrix shape:", tfidf_matrix.shape)


print("\nSaving TF-IDF model...")

with open("../models/tfidf_vectorizer.pkl", "wb") as file:
    pickle.dump(tfidf, file)


print("Saving TF-IDF matrix...")

with open("../models/tfidf_matrix.pkl", "wb") as file:
    pickle.dump(tfidf_matrix, file)


print("\nModel files saved successfully!")

print("../models/tfidf_vectorizer.pkl")
print("../models/tfidf_matrix.pkl")

print("\nNo full similarity matrix was created.")
print("Similarity will be calculated only when a movie is searched.")
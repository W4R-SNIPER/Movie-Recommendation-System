import pandas as pd

movies = pd.read_csv("../dataset/movies_metadata.csv", low_memory=False)

print("Dataset loaded successfully!")
print("Rows:", len(movies))
print("Columns:")
print(movies.columns.tolist())

print("\nFirst 5 movies:")
print(movies[["id", "title"]].head())
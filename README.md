# Movie-Recommendation-System

Run the app with `streamlit run app.py`.

The app reads titles and recommendation results from `models/recommendations.sqlite`.
If `dataset/final_movies.csv` or `models/tfidf_matrix.pkl` changes, rebuild that
index from the project root with `python src/build_recommendation_index.py`.

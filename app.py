from pathlib import Path
import pickle
import re

import pandas as pd
import streamlit as st
from sklearn.metrics.pairwise import cosine_similarity


ROOT = Path(__file__).resolve().parent
MOVIES_PATH = ROOT / "dataset" / "final_movies.csv"
MATRIX_PATH = ROOT / "models" / "tfidf_matrix.pkl"

st.set_page_config(
    page_title="ReelGood · Movie Finder",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_resource(show_spinner="Loading the movie library…")
def load_data():
    movies = pd.read_csv(MOVIES_PATH)
    with MATRIX_PATH.open("rb") as file:
        matrix = pickle.load(file)
    movies["title"] = movies["title"].fillna("Untitled")
    return movies, matrix


def display_year(value):
    if pd.isna(value):
        return "Year unavailable"
    match = re.match(r"\s*(\d{4})", str(value))
    return match.group(1) if match else "Year unavailable"


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --bg:#0b0d12; --panel:#12151d; --muted:#969bab; --accent:#c7f36b; }
.stApp { background: radial-gradient(ellipse at 50% -30%, #253023 0%, #11151b 37%, #0b0d12 72%); color:#f4f5f7; font-family:'DM Sans',sans-serif; }
[data-testid="stHeader"] { background:transparent; }
.block-container { max-width:1100px; padding-top:2.2rem; padding-bottom:4rem; }
.brand { font:800 17px Manrope,sans-serif; letter-spacing:-.5px; color:#fff; }
.brand span { color:var(--accent); }
.hero { text-align:center; padding:4.1rem 0 2.1rem; }
.eyebrow { color:var(--accent); text-transform:uppercase; letter-spacing:2.6px; font-size:11px; font-weight:700; }
.hero h1 { font:800 clamp(42px,7vw,72px)/1.05 Manrope,sans-serif; letter-spacing:-4px; margin:17px 0 14px; color:#f7f7f4; }
.hero h1 em { color:var(--accent); font-style:normal; }
.hero p { color:#a9adba; font-size:16px; margin:0 auto; max-width:540px; }
.search-label { color:#e6e8ed; font-size:13px; font-weight:600; margin:0 0 9px; }
[data-testid="stSelectbox"] > div > div { background:#171a22; border:1px solid #30343e; border-radius:12px; min-height:54px; }
[data-testid="stSelectbox"] input { color:#fff; }
.selected { background:linear-gradient(120deg,#1b2119,#151821); border:1px solid #313a2b; border-radius:18px; padding:25px 29px; margin:26px 0 35px; }
.selected-title { font:700 28px Manrope,sans-serif; letter-spacing:-.8px; margin:5px 0 9px; }
.metadata { color:#b4b7c2; font-size:13px; }
.section-title { font:700 22px Manrope,sans-serif; letter-spacing:-.5px; margin:0 0 5px; }
.section-sub { color:#969bab; font-size:13px; margin-bottom:18px; }
.movie-card { min-height:165px; height:100%; box-sizing:border-box; background:linear-gradient(145deg,#171a22,#11141b); border:1px solid #292d37; border-radius:16px; padding:21px; margin-bottom:13px; transition:border-color .2s, transform .2s; }
.movie-card:hover { border-color:#71864e; transform:translateY(-2px); }
.rank { color:var(--accent); font:700 11px Manrope,sans-serif; letter-spacing:1.4px; text-transform:uppercase; }
.movie-title { color:#f5f5f6; font:700 18px Manrope,sans-serif; margin:13px 0 9px; }
.movie-meta { color:#9da1ae; font-size:12px; }
.score { color:var(--accent); font-size:12px; font-weight:600; float:right; }
.footer { text-align:center; color:#707584; font-size:11px; margin-top:35px; }
div.stButton > button { background:var(--accent); color:#10130c; border:0; border-radius:11px; min-height:50px; font-weight:700; width:100%; }
div.stButton > button:hover { background:#d8ff8d; color:#10130c; border:0; }
@media(max-width:700px){ .hero{padding:2.7rem 0 1.5rem}.hero h1{letter-spacing:-2px}.block-container{padding-left:1.2rem;padding-right:1.2rem} }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="brand">reel<span>good</span> <span style="color:#747987;font-weight:500">/ MOVIE FINDER</span></div>', unsafe_allow_html=True)
st.markdown('''<div class="hero">
<div class="eyebrow">Your next favorite is in here</div>
<h1>Find your next<br><em>great watch.</em></h1>
<p>Pick a movie you love. We’ll find the ones with the same kind of magic.</p>
</div>''', unsafe_allow_html=True)

try:
    movies, tfidf_matrix = load_data()
except FileNotFoundError as error:
    st.error(f"Required project file not found: {error.filename}")
    st.stop()
except Exception as error:
    st.error(f"Could not load the movie recommender: {error}")
    st.stop()

st.markdown('<div class="search-label">What have you been watching?</div>', unsafe_allow_html=True)
titles = movies["title"].dropna().drop_duplicates().sort_values(key=lambda values: values.str.casefold()).tolist()
selected_title = st.selectbox("Search movies", titles, index=None, placeholder="Type a movie title…", label_visibility="collapsed")

if selected_title:
    selected_index = int(movies.index[movies["title"] == selected_title][0])
    movie = movies.iloc[selected_index]
    rating = f"★ {movie['vote_average']:.1f}" if pd.notna(movie.get("vote_average")) and float(movie["vote_average"]) > 0 else "Unrated"
    year = display_year(movie.get("release_date"))
    st.markdown(f'''<div class="selected">
      <div class="eyebrow">Your pick</div>
      <div class="selected-title">{selected_title}</div>
      <div class="metadata">{year} &nbsp; · &nbsp; {rating}</div>
    </div>''', unsafe_allow_html=True)

    scores = cosine_similarity(tfidf_matrix[selected_index], tfidf_matrix).ravel()
    scores[selected_index] = -1
    best = scores.argsort()[-5:][::-1]
    st.markdown('<div class="section-title">Made for your watchlist</div><div class="section-sub">Movies with a similar feel, picked from our library.</div>', unsafe_allow_html=True)
    columns = st.columns(2, gap="medium")
    for rank, index in enumerate(best, start=1):
        recommendation = movies.iloc[index]
        value = recommendation.get("vote_average")
        rating_text = f"★ {float(value):.1f}" if pd.notna(value) and float(value) > 0 else "Unrated"
        movie_year = display_year(recommendation.get("release_date"))
        score = max(0, float(scores[index]))
        with columns[(rank - 1) % 2]:
            st.markdown(f'''<div class="movie-card">
              <div class="rank">PICK 0{rank}<span class="score">{score:.0%} match</span></div>
              <div class="movie-title">{recommendation['title']}</div>
              <div class="movie-meta">{movie_year} &nbsp; · &nbsp; {rating_text}</div>
            </div>''', unsafe_allow_html=True)
else:
    st.markdown('<div style="text-align:center;color:#828795;font-size:13px;padding:15px 0 35px">Search or choose a title to get your recommendations.</div>', unsafe_allow_html=True)

st.markdown('<div class="footer">A little help finding what to watch next.</div>', unsafe_allow_html=True)

from pathlib import Path
import json
import re
import sqlite3
from contextlib import closing

import streamlit as st


ROOT = Path(__file__).resolve().parent
RECOMMENDATIONS_PATH = ROOT / "models" / "recommendations.sqlite"
DATABASE_URI = f"{RECOMMENDATIONS_PATH.as_uri()}?mode=ro"
DISPLAY_RECOMMENDATIONS = 3

st.set_page_config(
    page_title="W4R SNIPER · Movie Finder",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def open_database():
    return sqlite3.connect(DATABASE_URI, uri=True)


@st.cache_data(show_spinner="Loading movie titles…")
def load_titles():
    with closing(open_database()) as connection:
        return [row[0] for row in connection.execute(
            "SELECT DISTINCT title FROM movies ORDER BY title COLLATE NOCASE"
        )]


@st.cache_data
def load_movie_and_recommendations(title):
    with closing(open_database()) as connection:
        movie = connection.execute(
            """SELECT movie_index, title, release_date, vote_average, recommendations
               FROM movies WHERE title = ? ORDER BY movie_index LIMIT 1""",
            (title,),
        ).fetchone()
        if movie is None:
            return None, []

        movie_index, movie_title, release_date, vote_average, raw_recommendations = movie
        recommendations = json.loads(raw_recommendations)[:DISPLAY_RECOMMENDATIONS]
        recommendation_indices = [int(item[0]) for item in recommendations]
        placeholders = ",".join("?" for _ in recommendation_indices)
        rows = connection.execute(
            f"""SELECT movie_index, title, release_date, vote_average
                FROM movies WHERE movie_index IN ({placeholders})""",
            recommendation_indices,
        ).fetchall() if recommendation_indices else []

    by_index = {row[0]: row for row in rows}
    picks = [
        (*by_index[index], float(score))
        for index, score in recommendations if index in by_index
    ]
    return (movie_index, movie_title, release_date, vote_average), picks


def display_year(value):
    if value is None or value == "":
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

st.markdown('<div class="brand">W4R <span>SNIPER</span> <span style="color:#747987;font-weight:500">/ MOVIE FINDER</span></div>', unsafe_allow_html=True)
st.markdown('''<div class="hero">
<div class="eyebrow">Your next favorite is in here</div>
<h1>Find your next<br><em>great watch.</em></h1>
<p>Pick a movie you love. We’ll find the ones with the same kind of magic.</p>
</div>''', unsafe_allow_html=True)

try:
    if not RECOMMENDATIONS_PATH.exists():
        raise FileNotFoundError(RECOMMENDATIONS_PATH)
    titles = load_titles()
except FileNotFoundError as error:
    st.error(f"Required project file not found: {error.filename}")
    st.stop()
except Exception as error:
    st.error(f"Could not load the movie recommender: {error}")
    st.stop()

st.markdown('<div class="search-label">What have you been watching?</div>', unsafe_allow_html=True)
selected_title = st.selectbox("Search movies", titles, index=None, placeholder="Type a movie title…", label_visibility="collapsed")
if selected_title:
    movie, recommendations = load_movie_and_recommendations(selected_title)
    _, movie_title, release_date, vote_average = movie
    rating = f"★ {float(vote_average):.1f}" if vote_average is not None and float(vote_average) > 0 else "Unrated"
    year = display_year(release_date)
    st.markdown(f'''<div class="selected">
      <div class="eyebrow">Your pick</div>
      <div class="selected-title">{movie_title}</div>
      <div class="metadata">{year} &nbsp; · &nbsp; {rating}</div>
    </div>''', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Made for your watchlist</div><div class="section-sub">Movies with a similar feel, picked from our library.</div>', unsafe_allow_html=True)
    columns = st.columns(2, gap="medium")
    for rank, recommendation in enumerate(recommendations, start=1):
        index, title, movie_release_date, value, score = recommendation
        rating_text = f"★ {float(value):.1f}" if value is not None and float(value) > 0 else "Unrated"
        movie_year = display_year(movie_release_date)
        with columns[(rank - 1) % 2]:
            st.markdown(f'''<div class="movie-card">
              <div class="rank">PICK 0{rank}<span class="score">{score:.0%} match</span></div>
              <div class="movie-title">{title}</div>
              <div class="movie-meta">{movie_year} &nbsp; · &nbsp; {rating_text}</div>
            </div>''', unsafe_allow_html=True)
else:
    st.markdown('<div style="text-align:center;color:#828795;font-size:13px;padding:15px 0 35px">Search or choose a title to get your recommendations.</div>', unsafe_allow_html=True)

st.markdown('<div class="footer">A little help finding what to watch next.</div>', unsafe_allow_html=True)

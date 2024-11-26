# app.py
import streamlit as st
import requests
import pickle
import os
from pathlib import Path
from dotenv import load_dotenv

# Define URLs for the `.pkl` files
MOVIE_LIST_URL = "https://firebasestorage.googleapis.com/v0/b/sample-firebase-ai-app-3e813.firebasestorage.app/o/articles%2Fmovie_list.pkl?alt=media&token=6542b5f2-f250-47cd-acf0-272da7c568ec"
SIMILARITY_URL = "https://firebasestorage.googleapis.com/v0/b/sample-firebase-ai-app-3e813.firebasestorage.app/o/articles%2Fsimilarity.pkl?alt=media&token=5b832d2d-1f92-4ecf-a9b4-eadec60d94a8"

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / '.env')
IMDB_API_KEY = os.getenv("IMDB_API_KEY", "imdb-api-key")


@st.cache_data
def download_and_load_pickle(url):
    """
    Downloads a `.pkl` file from a URL and loads it into memory.

    :param url: The URL of the `.pkl` file to download.
    :return: The loaded pickle object.
    """
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        # Load the file into memory directly
        return pickle.loads(response.content)
    else:
        st.error(f"Failed to download file from {url}. Status code: {response.status_code}")
        return None

def fetch_poster(movie_id):
    url = "https://api.themoviedb.org/3/movie/{}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US".format(movie_id)
    data = requests.get(url)
    data = data.json()
    poster_path = data['poster_path']
    full_path = "https://image.tmdb.org/t/p/w500/" + poster_path
    return full_path

def fetch_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={IMDB_API_KEY}&language=en-US"
    response = requests.get(url)
    if response.status_code != 200:
        return {"poster_path": None, "title": "Unknown", "rating": "N/A", "release_date": "N/A"}
    data = response.json()
    poster_path = data.get('poster_path')
    title = data.get('title', "Unknown")
    rating = data.get('vote_average', "N/A")
    release_date = data.get('release_date', "N/A")
    return {
        "poster_url": f"https://image.tmdb.org/t/p/w500/{poster_path}" if poster_path else None,
        "title": title,
        "rating": rating,
        "release_date": release_date,
    }


def recommend(movie):
    """
    Recommend movies similar to the selected movie.

    :param movie: The selected movie title.
    :return: A list of dictionaries with movie details.
    """
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    
    recommendations = []
    for i in distances[1:6]:  # Top 5 recommendations
        movie_id = movies.iloc[i[0]].movie_id
        details = fetch_movie_details(movie_id)
        recommendations.append(details)
    
    return recommendations


# Page configuration
st.set_page_config(page_title="Movie Recommender", layout="wide")
st.markdown(
    """
    <style>
    body {
        background-color: #f4f4f4;
        font-family: Arial, sans-serif;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header
st.title("🎥 Movie Recommender System")

# Load data using caching
movies = download_and_load_pickle(MOVIE_LIST_URL)
similarity = download_and_load_pickle(SIMILARITY_URL)

if movies is not None and similarity is not None:
    # Dropdown for movie selection
    movie_list = movies['title'].values
    selected_movie = st.selectbox(
        "Type or select a movie from the dropdown",
        movie_list,
        help="Start typing or choose a movie to see recommendations."
    )

    # Show recommendations button
    if st.button('Show Recommendation'):
        if selected_movie:  # Ensure a movie is selected
            with st.spinner('Fetching recommendations...'):
                recommendations = recommend(selected_movie)
            
            st.subheader("Recommended Movies:")
            movie_cols = st.columns(len(recommendations))
            for idx, col in enumerate(movie_cols):
                with col:
                    movie = recommendations[idx]
                    st.image(movie["poster_url"], width=150, caption=movie["title"])
                    st.write(f"⭐ Rating: {movie['rating']}")
                    st.write(f"📅 Release: {movie['release_date']}")
        else:
            st.error("Please select a movie to get recommendations.")
else:
    st.error("Failed to load movie data. Please try again later.")



# # Show recommendations button
# if st.button('Show Recommendation'):
#     with st.spinner('Fetching recommendations...'):
#         recommendations = recommend(selected_movie)
    
#     st.subheader("Recommended Movies:")
#     movie_cols = st.columns(len(recommendations))
#     for idx, col in enumerate(movie_cols):
#         with col:
#             movie = recommendations[idx]
#             st.image(movie.get("poster_url", "https://via.placeholder.com/500x750"), width=150, caption=movie['title'])
#             st.write(f"⭐ Rating: {movie['rating']}")
#             st.write(f"📅 Release: {movie['release_date']}")
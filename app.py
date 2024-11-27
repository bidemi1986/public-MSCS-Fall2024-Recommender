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
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# Check if API key is available
if not TMDB_API_KEY:
    st.error("TMDB API key not found. Please set up your API key in the .env file.")
    st.stop()

@st.cache_data
def download_and_load_pickle(url):
    """
    Downloads a `.pkl` file from a URL and loads it into memory.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        return pickle.loads(response.content)
    except Exception as e:
        st.error(f"Failed to download or load file from {url}. Error: {str(e)}")
        return None

def fetch_movie_details(movie_id):
    """
    Fetch movie details from TMDB API with better error handling.
    """
    try:
        headers = {
            "Authorization": f"Bearer {TMDB_API_KEY}",
            "accept": "application/json"
        }
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?language=en-US"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Get poster path and construct full URL if available
        poster_path = data.get('poster_path')
        poster_url = None
        if poster_path:
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
        
        return {
            "poster_url": poster_url,
            "title": data.get('title', "Unknown"),
            "rating": data.get('vote_average', "N/A"),
            "release_date": data.get('release_date', "N/A"),
            "overview": data.get('overview', "No overview available")
        }
    except requests.exceptions.RequestException as e:
        st.warning(f"Failed to fetch details for movie ID {movie_id}: {str(e)}")
        return {
            "poster_url": None,
            "title": "Movie information unavailable",
            "rating": "N/A",
            "release_date": "N/A",
            "overview": "No overview available"
        }

def recommend(movie):
    """
    Recommend movies similar to the selected movie.
    """
    try:
        index = movies[movies['title'] == movie].index[0]
        distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
        
        recommendations = []
        for i in distances[1:6]:  # Top 5 recommendations
            movie_id = movies.iloc[i[0]].movie_id
            details = fetch_movie_details(movie_id)
            recommendations.append(details)
        
        return recommendations
    except Exception as e:
        st.error(f"Error generating recommendations: {str(e)}")
        return []

# Page configuration
st.set_page_config(page_title="Movie Recommender", layout="wide")
st.markdown(
    """
    <style>
    .movie-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    </style>
    """,
    unsafe_allow_html=True
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
    if st.button('Show Recommendations'):
        if selected_movie:
            with st.spinner('Fetching recommendations...'):
                recommendations = recommend(selected_movie)
            
            if recommendations:
                st.subheader("Recommended Movies:")
                movie_cols = st.columns(len(recommendations))
                
                for idx, col in enumerate(movie_cols):
                    with col:
                        movie = recommendations[idx]
                        with st.container():
                            # Display poster if available, otherwise show placeholder
                            if movie["poster_url"]:
                                st.image(movie["poster_url"], width=150, caption=movie["title"])
                            else:
                                st.image("https://via.placeholder.com/150x225?text=No+Poster", width=150, caption=movie["title"])
                            
                            st.markdown(f"⭐ Rating: {movie['rating']}")
                            st.markdown(f"📅 Release: {movie['release_date']}")
                            with st.expander("Overview"):
                                st.write(movie["overview"])
        else:
            st.warning("Please select a movie to get recommendations.")
else:
    st.error("Failed to load movie data. Please try again later.")
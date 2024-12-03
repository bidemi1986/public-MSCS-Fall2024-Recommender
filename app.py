import streamlit as st
import requests
import pickle
import os
import boto3
from pathlib import Path
from dotenv import load_dotenv
from botocore.exceptions import ClientError
import logging
import time

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# CloudWatch handler
# cloudwatch_handler = logging.StreamHandler()
# cloudwatch_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
# logger.addHandler(cloudwatch_handler)

# Load environment variables
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")

# # Initialize CloudWatch client
# cloudwatch = boto3.client('cloudwatch')
# def log_metric(metric_name, value, unit='Count'):
#     """Log custom metric to CloudWatch"""
#     try:
#         cloudwatch.put_metric_data(
#             Namespace='MovieRecommender',
#             MetricData=[
#                 {
#                     'MetricName': metric_name,
#                     'Value': value,
#                     'Unit': unit
#                 }
#             ]
#         )
#     except Exception as e:
#         logger.error(f"Error logging metric {metric_name}: {str(e)}")
# if not TMDB_API_KEY:
#     st.error("TMDB API key not found. Please set up your API key in the .env file.")
#     st.stop()

# if not all([AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_BUCKET_NAME]):
#     st.error("AWS credentials not found. Please set up your AWS credentials in the .env file.")
#     st.stop()

# Initialize AWS S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

@st.cache_data
def download_and_load_pickle_from_s3(bucket, key):
    """
    Downloads a `.pkl` file from S3 and loads it into memory.
    
    Args:
        bucket (str): S3 bucket name
        key (str): Path to file in S3 bucket
    Returns:
        object: Loaded pickle object
    """
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        pickle_data = response['Body'].read()
        return pickle.loads(pickle_data)
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        if error_code == 'NoSuchKey':
            st.error(f"File {key} not found in bucket {bucket}")
        elif error_code == 'NoSuchBucket':
            st.error(f"Bucket {bucket} does not exist")
        else:
            st.error(f"Error accessing S3: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Failed to load file from S3: {str(e)}")
        return None

def fetch_movie_details(movie_id):
    """
    Fetch movie details from TMDB API with better error handling.
    """
    try:
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "accept": "application/json"
        }
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?language=en-US"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
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

# Load data from S3 using caching
movies = download_and_load_pickle_from_s3(AWS_BUCKET_NAME, 'models/movie_list.pkl')
similarity = download_and_load_pickle_from_s3(AWS_BUCKET_NAME, 'models/similarity.pkl')

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



# Add performance monitoring
def monitor_performance(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        
        log_metric(f'{func.__name__}_duration', duration, 'Seconds')
        return result
    return wrapper

@monitor_performance
def fetch_movie_details(movie_id):
    # Your existing fetch_movie_details code...
    pass
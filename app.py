import streamlit as st
import pickle
import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_fixed, RetryError

# Retry settings for API calls
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US"
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    data = response.json()
    poster_path = data.get('poster_path')
    if poster_path:
        full_path = "https://image.tmdb.org/t/p/w500/" + poster_path
    else:
        full_path = "https://via.placeholder.com/500?text=No+Image+Available"
    return full_path

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_trailer(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US"
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    data = response.json()
    if data['results']:
        for video in data['results']:
            if video['type'] == 'Trailer' and video['site'] == 'YouTube':
                return f"https://www.youtube.com/watch?v={video['key']}"
    return None

def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_movie_names = []
    recommended_movie_posters = []
    recommended_movie_ids = []

    for i in distances[1:6]:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movie_ids.append(movie_id)
        try:
            poster = fetch_poster(movie_id)
            recommended_movie_posters.append(poster)
        except (requests.exceptions.RequestException, RetryError) as e:
            print(f"Failed to fetch poster for movie ID {movie_id}: {e}")
            recommended_movie_posters.append("https://via.placeholder.com/500?text=No+Image+Available")
        recommended_movie_names.append(movies.iloc[i[0]].title)

    return recommended_movie_names, recommended_movie_posters, recommended_movie_ids

# Load the movie data
movies_dict = pickle.load(open('movies_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)

similarity = pickle.load(open('similarity.pkl', 'rb'))

# Streamlit UI
st.title('Movie Recommender System')

selected_movie_name = st.selectbox(
    'Select a movie to get recommendations',
    movies['title'].values)

if st.button('Recommend'):
    names, posters, movie_ids = recommend(selected_movie_name)
    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            st.text(names[i])
            st.image(posters[i])
            try:
                trailer_url = fetch_trailer(movie_ids[i])
                if trailer_url:
                    st.video(trailer_url)
                else:
                    st.write("Trailer not available")
            except (requests.exceptions.RequestException, RetryError) as e:
                print(f"Failed to fetch trailer for movie ID {movie_ids[i]}: {e}")
                st.write("Trailer not available")

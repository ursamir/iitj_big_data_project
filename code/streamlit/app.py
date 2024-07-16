import streamlit as st
import redis
import json
import pymongo
import time
from imdb import IMDb

# Connect to MongoDB
mongo_client = pymongo.MongoClient('mongodb://192.168.0.112:8081/')
mongo_db = mongo_client["netflix"]
mongo_ratings_collection = mongo_db["ratings"]

# Connect to Redis
redis_url = "192.168.0.112"
redis_port = 8088
redis_client = redis.StrictRedis(host=redis_url, port=redis_port, db=0)

# Load user IDs and item factors data once
g_user_ids = [user_id.decode('utf-8') for user_id in redis_client.smembers('user_ids')]
item_factors_data = redis_client.get('item_factors')
if item_factors_data:
    item_factors = json.loads(item_factors_data)
else:
    item_factors = None

# Initialize IMDb instance
ia = IMDb()

# Function to fetch user IDs from Redis
@st.cache_data()
def fetch_user_ids(offset, limit):
    return g_user_ids[offset:offset+limit]

# Function to fetch user factors from Redis based on user_id
def fetch_user_factors(user_id):
    user_factors_data = redis_client.hgetall(f'user_factors:{user_id}')
    if user_factors_data:
        user_factors = {key.decode('utf-8'): json.loads(value) for key, value in user_factors_data.items()}
        return user_factors
    else:
        return None

# Function to fetch movie details from Redis based on movie_id
@st.cache_data()
def fetch_movie_details(movie_id):
    movie_data = redis_client.hgetall(f'movie:{movie_id}')
    if movie_data:
        # Convert bytes to string
        movie_details = {key.decode('utf-8'): value.decode('utf-8') for key, value in movie_data.items()}
        return movie_details
    else:
        return None

# Function to fetch movie poster from IMDb
def fetch_movie_poster(title):
    search_results = ia.search_movie(title)
    if search_results:
        movie = search_results[0]
        ia.update(movie, info=['main'])
        if 'cover url' in movie:
            return movie['cover url']
    return None

# Function to recommend movies based on user factors and item factors
@st.cache_data()
def recommend_movies(user_id, user_factors, item_factors, top_n=10):
    if not item_factors:
        return []
    
    # Fetch user's already rated movie_ids from MongoDB
    start_time = time.time()
    already_rated_movies = set()
    ratings = mongo_ratings_collection.find({"customer_id": int(user_id)})
    for rating in ratings:
        already_rated_movies.add(rating["movie_id"])
    end_time = time.time()
    print(f"Time taken to fetch already rated movies: {end_time - start_time:.4f} seconds")

    recommendations = []

    # Perform recommendation logic based on user and item factors (example logic)
    for movie_id, item_features in item_factors.items():
        # Skip movie if already rated by the user
        if movie_id in already_rated_movies:
            continue

        # Perform dot product of user factors and item factors
        user_features = user_factors['features']
        dot_product = sum(u * i for u, i in zip(user_features, item_features))

        # Append movie ID and dot product as a tuple
        recommendations.append((movie_id, dot_product))

    # Sort recommendations based on dot product (higher is better)
    recommendations.sort(key=lambda x: x[1], reverse=True)

    # Select top N recommendations
    top_recommendations = recommendations[:top_n]

    # Fetch movie details for the top recommendations
    recommended_movies = []
    for movie_id, score in top_recommendations:
        movie_details = fetch_movie_details(movie_id)
        if movie_details:
            movie_details['movie_id'] = movie_id
            movie_details['score'] = score
            recommended_movies.append(movie_details)

    return recommended_movies

# Function to fetch top rated movies by user ID from MongoDB
def fetch_top_rated_movies(user_id, top_n=10):
    start_time = time.time()
    top_rated_movies = []
    ratings = mongo_ratings_collection.find({"customer_id": int(user_id)}).sort("rating", pymongo.DESCENDING).limit(top_n)
    for rating in ratings:
        movie_details = fetch_movie_details(rating["movie_id"])
        if movie_details:
            movie_details['movie_id'] = rating["movie_id"]
            movie_details['rating'] = rating["rating"]
            top_rated_movies.append(movie_details)
    end_time = time.time()
    print(f"Time taken to fetch top rated movies: {end_time - start_time:.4f} seconds")
    return top_rated_movies

# Streamlit app
def main():
    st.title('Movie Recommendation System')

    # Load user IDs in batches of 50 items
    offset = st.slider('Select offset', 0, len(g_user_ids), 0, 50)
    user_ids = fetch_user_ids(offset, 50)
    
    # Allow manual input of user ID
    user_id_input = st.text_input('Enter User ID manually')

    if user_id_input:
        user_id = user_id_input.strip()
    else:
        user_id = st.selectbox('Select User ID', list(user_ids)) if user_ids else None
    
    if st.button('Get Recommendations'):
        if user_id:
            # Fetch user factors from Redis
            user_factors = fetch_user_factors(user_id)
            if user_factors and item_factors:
                with st.spinner('Fetching recommendations...'):
                    st.subheader(f'Recommendations for User {user_id}')
                    recommendations = recommend_movies(user_id, user_factors, item_factors)
                    if recommendations:
                        # Prepare data for table
                        table_data = []
                        for movie in recommendations:
                            poster_url = fetch_movie_poster(movie["title"])
                            table_data.append({
                                "Title": movie["title"],
                                "Movie ID": movie["movie_id"],
                                "Year": movie["year_of_release"],
                                "Score": f"{movie['score']:.2f}",
                                "Poster": poster_url
                            })
                        # Display table with posters
                        for movie in table_data:
                            cols = st.columns([1, 2])
                            if movie["Poster"]:
                                cols[0].image(movie["Poster"], width=100)
                            cols[1].write(f"**{movie['Title']}** ({movie['Year']})")
                            cols[1].write(f"**Score**: {movie['Score']}")
                            cols[1].write(f"**Movie ID**: {movie['Movie ID']}")
                            st.markdown("---")
                    else:
                        st.write('No recommendations found.')

                # Fetch top rated movies by the user
                with st.spinner('Fetching top rated movies...'):
                    st.subheader(f'Top Rated Movies by User {user_id}')
                    top_rated_movies = fetch_top_rated_movies(user_id)
                    if top_rated_movies:
                        # Prepare data for table
                        top_rated_table_data = []
                        for movie in top_rated_movies:
                            poster_url = fetch_movie_poster(movie["title"])
                            top_rated_table_data.append({
                                "Title": movie["title"],
                                "Movie ID": movie["movie_id"],
                                "Year": movie["year_of_release"],
                                "Rating": movie['rating'],
                                "Poster": poster_url
                            })
                        # Display table with posters
                        for movie in top_rated_table_data:
                            cols = st.columns([1, 2])
                            if movie["Poster"]:
                                cols[0].image(movie["Poster"], width=100)
                            cols[1].write(f"**{movie['Title']}** ({movie['Year']})")
                            cols[1].write(f"**Rating**: {movie['Rating']}")
                            cols[1].write(f"**Movie ID**: {movie['Movie ID']}")
                            st.markdown("---")
                    else:
                        st.write(f'No top rated movies found for User {user_id}.')
            elif not user_factors:
                st.write(f'User {user_id} not found or no factors available.')
            else:
                st.write('Item factors not found.')
        else:
            st.write('Please select or enter a User ID.')

if __name__ == '__main__':
    main()

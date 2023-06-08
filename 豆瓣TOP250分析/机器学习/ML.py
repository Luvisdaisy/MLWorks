from pymongo import MongoClient
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

client = MongoClient('mongodb://localhost:27017/')
db = client['doubantop250_db']
info_collection = db['movie_info_collection']
review_collection = db['movie_review_collection']

info_result = info_collection.find()
review_result = review_collection.find()

info_dataframe = pd.DataFrame(info_result)
review_dataframe = pd.DataFrame(review_result)

review_dataframe['user_rating'] = review_dataframe['user_rating'].astype(int)
review_dataframe['movie_id'] = review_dataframe['movie_id'].astype(int)
review_dataframe['user_id'] = review_dataframe['user_id'].astype(int)

rating_matrix = review_dataframe.pivot_table(
    index='user_id', columns='movie_id', values='user_rating')
rating_matrix.fillna(0, inplace=True)

user_sim = cosine_similarity(rating_matrix)

target_user_id = 63688511
target_user_ratings = rating_matrix.loc[target_user_id].dropna()
similar_movies = pd.Series()

for movie_id, rating in target_user_ratings.items():
    similar_movies = similar_movies.append(
        user_sim[movie_id].map(lambda x: x * rating))
print(similar_movies)

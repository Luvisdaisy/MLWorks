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
# 数据清洗和转换
review_dataframe = review_dataframe.dropna(
    subset=['movie_id', 'user_id', 'user_rating', 'comment'])
review_dataframe['movie_id'] = review_dataframe['movie_id'].astype(int)
review_dataframe['user_id'] = review_dataframe['user_id'].astype(int)
review_dataframe['user_rating'] = review_dataframe['user_rating'].astype(float)
# 构建用户-物品评分矩阵
rating_matrix = review_dataframe.pivot_table(
    index='user_id', columns='movie_id', values='user_rating')
item_similarity = cosine_similarity(rating_matrix.fillna(0).T)
print(rating_matrix.shape, item_similarity.shape)
# 定义函数生成推荐列表


def generate_recommendations(user_id, top_n=5):
    user_ratings = rating_matrix.loc[user_id].dropna()
    similarities = item_similarity[user_ratings.index]
    weighted_similarities = np.dot(similarities, user_ratings)
    non_rated_movies = rating_matrix.columns[~rating_matrix.loc[user_id].notna(
    )]
    recommendations = pd.DataFrame({
        'movie_id': non_rated_movies,
        'weighted_similarity': weighted_similarities[~user_ratings.index]
    })
    recommendations = recommendations.sort_values(
        by='weighted_similarity', ascending=False).head(top_n)
    return recommendations


# 示例：为用户1生成推荐列表
user_id = 63688511
recommendations = generate_recommendations(user_id)
print(recommendations)

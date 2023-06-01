import csv
from pymongo import MongoClient


def information_storage(file):
    with open(file, 'r', encoding='utf-8') as info_file:
        reader = csv.reader(info_file)
        movie_list = list(reader)
    # 遍历电影列表并存储到MongoDB
    for movie in movie_list:
        movie_data = {
            'num': movie[0],
            'id': movie[1],
            'year': movie[2],
            'title': movie[3],
            'director': movie[4],
            'actors': movie[5],
            'type': movie[6],
            'country': movie[7],
            'duration': movie[8],
            'score': movie[9],
            'rater_num': movie[10]
        }
        # 检查电影是否已存在于数据库
        existing_movie = info_collection.find_one({'id': movie_data['id']})
        if existing_movie:
            print(f"电影已存在，执行更新操作：{existing_movie['title']}")
            info_collection.update_one(
                {'id': movie_data['id']}, {'$set': movie_data})
        else:
            info_collection.insert_one(movie_data)


def review_storage(file):
    with open(file, 'r', encoding='utf-8') as info_file:
        reader = csv.reader(info_file)
        review_list = list(reader)
    # 遍历评论列表并存储到MongoDB
    for review in review_list:
        review_data = {
            'movie_id': review[0],
            'user_id': review[1],
            'user_rating': review[2],
            'comment': review[3],
        }
        # 检查评论是否已存在于数据库
        existing_review = review_collection.find_one(
            {'movie_id': review_data['movie_id'], 'user_id': review_data['user_id']})
        if existing_review:
            print(f"评论已存在，执行更新操作：{existing_review['_id']}")
            review_collection.update_one(
                {'_id': existing_review['_id']}, {'$set': review_data})
        else:
            review_collection.insert_one(review_data)


if __name__ == '__main__':
    client = MongoClient('mongodb://localhost:27017/')
    db = client['doubantop250_db']
    info_collection = db['movie_info_collection']
    review_collection = db['movie_review_collection']
    review_file = 'E:\ProSpace\VSCodePros\Python\MLFinalWork\爬虫\movie_reviews.csv'
    info_file = 'E:\ProSpace\VSCodePros\Python\MLFinalWork\爬虫\movie_data.csv'
    information_storage(info_file)
    review_storage(review_file)

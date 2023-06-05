import csv

from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['doubantop250_db']
info_collection = db['movie_info_collection']
review_collection = db['movie_review_collection']


def information_storage(file):
    try:
        with open(file, 'r', encoding='utf-8') as info_file:
            reader = csv.reader(info_file)
            movie_list = list(reader)

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

            existing_movie = info_collection.find_one({'id': movie_data['id']})
            if existing_movie:
                info_collection.update_one(
                    {'id': movie_data['id']}, {'$set': movie_data})
            else:
                info_collection.insert_one(movie_data)

    except FileNotFoundError:
        print(f"文件未找到：{file}")

    except Exception as e:
        print(f"数据存储发生错误：{e}")


def review_storage(file):
    try:
        with open(file, 'r', encoding='utf-8') as info_file:
            reader = csv.reader(info_file)
            review_list = list(reader)

        for review in review_list:
            review_data = {
                'movie_id': review[0],
                'user_id': review[1],
                'user_rating': review[2],
                'comment': review[3],
            }

            existing_review = review_collection.find_one(
                {'movie_id': review_data['movie_id'], 'user_id': review_data['user_id']})
            if existing_review:
                review_collection.update_one(
                    {'_id': existing_review['_id']}, {'$set': review_data})
            else:
                review_collection.insert_one(review_data)

    except FileNotFoundError:
        print(f"文件未找到：{file}")

    except Exception as e:
        print(f"数据存储发生错误：{e}")


def runMongo():
    review_file = '../数据分析/movie_reviews.csv'
    info_file = '../数据分析/movie_data.csv'

    try:
        print('MongoDB处理中...')
        information_storage(info_file)
        review_storage(review_file)
        print('数据已全部存入MongoDB')

    except Exception as e:
        print(f"运行过程中发生错误：{e}")

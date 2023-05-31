import csv
from pymongo import MongoClient

movie_list = []

# 读取CSV文件数据
with open('E:\ProSpace\VSCodePros\Python\MLFinalWork\movie_data.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    movie_list = list(reader)

# 连接到MongoDB服务器
client = MongoClient('mongodb://localhost:27017/')

# 选择或创建数据库
db = client['doubantop205_db']

# 选择或创建集合
collection = db['movie_info_list']

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
        'duration': movie[8]
    }
    collection.insert_one(movie_data)

# 遍历集合中的数据
for movie_data in collection.find():
    # 处理每个电影数据
    print(movie_data)

# 断开与MongoDB服务器的连接
client.close()

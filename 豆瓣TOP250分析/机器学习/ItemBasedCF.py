# coding = utf-8

# 基于项目的协同过滤推荐算法实现
import math
import random
from operator import itemgetter


class ItemBasedCF():
    # 初始化参数
    def __init__(self):
        # 找到相似的20部电影，为目标用户推荐10部电影
        self.n_sim_movie = 20
        self.n_rec_movie = 10

        # 将数据集划分为训练集和测试集
        self.trainSet = {}
        self.testSet = {}

        # 用户相似度矩阵
        self.movie_sim_matrix = {}
        self.movie_popular = {}
        self.movie_count = 0

        print('计划查找相似电影数 = %d' % self.n_sim_movie)
        print('计划推荐电影数 = %d' % self.n_rec_movie)

    # 读文件得到“用户-电影”数据

    def get_dataset(self, filename, pivot=0.875):
        trainSet_len = 0
        testSet_len = 0
        for line in self.load_file(filename):
            user, movie, rating, timestamp = line.split(',')
            if(random.random() < pivot):
                # 相当于trainSet.get(user)，若该键不存在，则设trainSet[user] = {}，典中典
                self.trainSet.setdefault(user, {})

                # 键中键：形如{'1': {'1287': '2.0', '1953': '4.0', '2105': '4.0'}, '2': {'10': '4.0', '62': '3.0'}}
                # 用户1看了id为1287的电影，打分2.0
                self.trainSet[user][movie] = rating
                trainSet_len += 1
            else:
                self.testSet.setdefault(user, {})
                self.testSet[user][movie] = rating
                testSet_len += 1
        print('训练集测试集划分完成!')
        print('训练集 = %s' % trainSet_len)
        print('测试集 = %s' % testSet_len)

    # 读文件，返回文件的每一行

    def load_file(self, filename):
        with open(filename, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i == 0:  # 去掉文件第一行的title
                    continue
                yield line.strip('\r\n')
        print('加载 %s 成功!' % filename)

    # 计算电影之间的相似度

    def calc_movie_sim(self):
        for user, movies in self.trainSet.items():  # 循环取出一个用户和他看过的电影
            for movie in movies:
                if movie not in self.movie_popular:
                    self.movie_popular[movie] = 0
                self.movie_popular[movie] += 1  # 统计每部电影共被看过的次数

        self.movie_count = len(self.movie_popular)  # 得到电影总数
        print("电影总数 = %d" % self.movie_count)

        # 得到矩阵C，C[i][j]表示同时喜欢电影i和j的用户数
        for user, movies in self.trainSet.items():
            for m1 in movies:
                for m2 in movies:
                    if m1 == m2:
                        continue
                    self.movie_sim_matrix.setdefault(m1, {})
                    self.movie_sim_matrix[m1].setdefault(m2, 0)
                    # ItemCF-IUF改进，惩罚了活跃用户 22.00 10.65 14.98
                    self.movie_sim_matrix[m1][m2] += 1 / \
                        math.log(1 + len(movies))
        print("建立用户相似度矩阵成功!")

        # 计算电影之间的相似性
        print("计算电影相似度矩阵 ...")
        for m1, related_movies in self.movie_sim_matrix.items():  # 电影m1，及m1这行对应的电影们
            for m2, count in related_movies.items():  # 电影m2 及 同时看了m1和m2的用户数
                # 注意0向量的处理，即某电影的用户数为0
                if self.movie_popular[m1] == 0 or self.movie_popular[m2] == 0:
                    self.movie_sim_matrix[m1][m2] = 0
                else:
                    # 计算出电影m1和m2的相似度
                    self.movie_sim_matrix[m1][m2] = count / math.sqrt(
                        self.movie_popular[m1] * self.movie_popular[m2])
        print('计算电影相似度矩阵成功!')

        # 添加归一化    precisioin=0.2177	recall=0.1055	coverage=0.1497
        maxDict = {}
        max = 0
        for m1, related_movies in self.movie_sim_matrix.items():
            for m2, _ in related_movies.items():
                if self.movie_sim_matrix[m1][m2] > max:
                    max = self.movie_sim_matrix[m1][m2]

        for m1, related_movies in self.movie_sim_matrix.items():  # 归一化
            for m2, _ in related_movies.items():
                # self.movie_sim_matrix[m1][m2] = self.movie_sim_matrix[m1][m2] / maxDict[m2]
                self.movie_sim_matrix[m1][m2] = self.movie_sim_matrix[m1][m2] / max

    # 针对目标用户U，找到K部相似的电影，并推荐其N部电影

    def recommend(self, user):
        K = self.n_sim_movie  # 找到相似的20部电影
        N = self.n_rec_movie  # 为用户推荐10部
        rank = {}
        watched_movies = self.trainSet[user]  # 该用户看过的电影

        for movie, rating in watched_movies.items():  # 遍历用户看过的电影及对其评价
            # 找到与movie最相似的K部电影,遍历电影及与movie相似度
            for related_movie, w in sorted(self.movie_sim_matrix[movie].items(), key=itemgetter(1), reverse=True)[:K]:
                if related_movie in watched_movies:  # 如果用户已经看过了，不推荐了
                    continue
                rank.setdefault(related_movie, 0)
                rank[related_movie] += w * float(rating)  # 计算用户对该电影的兴趣
        # 返回用户最感兴趣的N部电影
        return sorted(rank.items(), key=itemgetter(1), reverse=True)[:N]

    # 产生推荐并通过准确率、召回率和覆盖率进行评估

    def evaluate(self):
        print('开始评估 ...')
        N = self.n_rec_movie  # 要推荐的电影数
        # 准确率和召回率
        hit = 0
        rec_count = 0
        test_count = 0
        # 覆盖率
        all_rec_movies = set()

        for i, user in enumerate(self.trainSet):
            test_moives = self.testSet.get(user, {})  # 测试集中用户喜欢的电影
            rec_movies = self.recommend(user)  # 得到推荐的电影及计算出的用户对它们的兴趣

            for movie, w in rec_movies:  # 遍历给user推荐的电影
                if movie in test_moives:  # 测试集中有该电影
                    hit += 1  # 推荐命中+1
                all_rec_movies.add(movie)
            rec_count += N
            test_count += len(test_moives)

        precision = hit / (1.0 * rec_count)
        recall = hit / (1.0 * test_count)
        coverage = len(all_rec_movies) / (1.0 * self.movie_count)
        print('准确率=%.4f\t召回率=%.4f\t覆盖率=%.4f' %
              (precision, recall, coverage))


if __name__ == '__main__':
    rating_file = '../movie_dataset/ratings.csv'
    itemCF = ItemBasedCF()
    itemCF.get_dataset(rating_file)
    itemCF.calc_movie_sim()
    itemCF.evaluate()  # coding = utf-8
    # 对id为 1 的用户推荐结果
    user_id = '1'
    recommended_movies = itemCF.recommend(user_id)

    print(f"对用户 {user_id} 的推荐电影：")
    for movie, _ in recommended_movies:
        print(movie)

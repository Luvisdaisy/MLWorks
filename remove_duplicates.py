import pandas as pd


def remove_duplicates(csv_file):
    # 读取CSV文件并创建DataFrame
    df = pd.read_csv(csv_file, header=None)

    # 去除重复的行，只保留第一个出现的行
    df.drop_duplicates(inplace=True)

    # 将处理后的DataFrame写回CSV文件
    df.to_csv(csv_file, index=False, header=False)


# 使用示例
remove_duplicates(
    'E:\\ProSpace\\VSCodePros\\Python\\MLFinalWork\\爬虫\\movie_reviews.csv')

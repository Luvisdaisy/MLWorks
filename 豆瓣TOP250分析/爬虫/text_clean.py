import csv
import re


def clean_text(text):
    # 去除表情符号
    text = re.sub(r'\[.*?\]', '', text)
    # 去除英文字符和特殊符号
    text = re.sub(r'[a-zA-Z]', '', text)
    text = re.sub(r'[^a-zA-Z\u4e00-\u9fff\s]', '', text)
    # 去除换行符
    text = text.replace('\n', ' ')
    # 去除多余空格
    text = re.sub(r'\s+', ' ', text)
    return text


def process_csv(file):
    print('开始对评论进行清洗...')
    cleaned_data = []
    with open(file, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in enumerate(reader):
            if len(row) > 3:
                review_data = {
                    'movie_id': row[0],
                    'user_id': row[1],
                    'user_rating': row[2],
                    'comment': clean_text(row[3])
                }
                cleaned_data.append(review_data)

    # 将清洗后的数据写入原始文件
    with open(file, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for data in cleaned_data:
            writer.writerow([data['movie_id'], data['user_id'],
                             data['user_rating'], data['comment']])

    print('清洗完成')

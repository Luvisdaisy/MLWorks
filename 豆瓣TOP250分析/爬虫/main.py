import csv
import os
import re
import time

import mongo
import pandas as pd
import requests
import text_clean
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


# 基于proxy_pool项目的代理池
def get_proxy():
    return requests.get("http://127.0.0.1:5010/get?type=https").json()


def delete_proxy(proxy):
    requests.get("http://127.0.0.1:5010/delete/?proxy={}".format(proxy))


# 爬取豆瓣电影TOP250的电影序号、ID、名称、上映时间、导演、主演（前四名）、类型、国家/地区、时长、评分、评价人数
# 爬取每个电影的信息页面
def scrape_movie_list(ua, cookies):
    url = 'https://movie.douban.com/top250?start=125&filter='
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'User-Agent': ua.random,
        'Connection': 'keep-alive',
        'Cookie': cookies,
        'Host': 'movie.douban.com',
        'Referer': 'https://www.bing.com/'
    }

    movie_list = []

    while url:
        count = 0
        if count < 25:
            retry_flag = True
        while retry_flag:
            proxy = get_proxy().get('proxy')
            print(proxy)
            try:
                time.sleep(20)
                response = requests.get(url, headers=headers, proxies={
                                        "http": "http://{}".format(proxy), "https": "https://{}".format(proxy)}, timeout=20)
                # response = requests.get(url, headers=headers, timeout=20)
                print(response)
                soup = BeautifulSoup(response.text, 'html.parser')
                items = soup.find_all('div', class_='item')
                movie_list = scrape_movie_info(movie_list, items, ua, cookies)
                count += 1
                retry_flag = False
            except Exception as e:
                print('Exception:', e)
                print('获取新代理...')
                delete_proxy(proxy)
        next_page = soup.find('span', class_='next').find('a')
        if next_page:
            url = 'https://movie.douban.com/top250'+next_page['href']
            # 爬取完一页后输入新的Cookies
            cookies = input('请更新Cookies:')
        else:
            url = None

    return movie_list


# 爬取电影基本信息
def scrape_movie_info(movie_list, items, ua, cookies):

    for item in items:
        retry_flag = True
        movie_url = item.find('a')
        movie_num = item.find('em').text
        movie_id = movie_url['href'].split('/')[-2]
        detail_headers = {
            'User-Agent': ua.random,
            'Host': 'movie.douban.com',
            'Connection': 'keep-alive',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Referer': 'https://movie.douban.com/top250',
            'Cookies': cookies
        }

        # 测试接口获取的代理
        while retry_flag:
            proxy = get_proxy().get('proxy')
            print(proxy)
            try:
                # 5秒延迟
                time.sleep(5)
                movie_detail = requests.get(
                    url=movie_url['href'], headers=detail_headers, proxies={"http": "http://{}".format(proxy), "https": "https://{}".format(proxy)}, timeout=20)
                movie_detail = requests.get(
                    url=movie_url['href'], headers=detail_headers, timeout=20)
                print(movie_detail)
                # 调用 process_info_html()
                movie_list = process_info_html(
                    movie_num, movie_id, movie_detail, movie_list)
                retry_flag = False
            except Exception as e:
                print(e)
                print('获取新代理...')
                delete_proxy(proxy)

    return movie_list


# 对电影信息页面进行处理
def process_info_html(movie_num, movie_id, movie_detail, movie_list):
    soup_detail = BeautifulSoup(movie_detail.text, 'html.parser')
    # 提取上映年份
    year = soup_detail.find(
        'span', class_='year').text.replace('(', '').replace(')', '')
    # 提取名称
    title = soup_detail.find(
        'span', attrs={'property': 'v:itemreviewed'}).text.split(' ')[0]
    # 提取导演信息
    director = soup_detail.find(
        'a', attrs={'rel': 'v:directedBy'}).text
    # 提取演员信息（前四名）若无演员表则设置为空
    try:
        actors = []
        actors_box = soup_detail.find('span', class_='actor').find(
            'span', class_='attrs').find_all('a')
        for a in actors_box[:4]:
            actors.append(a.text)
    except AttributeError:
        actors = []
    # 提取类型信息
    genre_spans = soup_detail.find_all(
        'span', attrs={'property': 'v:genre'})
    genres = [span.get_text() for span in genre_spans]
    # 提取制片国家信息
    country_span = soup_detail.find('span', string='制片国家/地区:')
    country = country_span.next_sibling.strip()
    # 提取时长信息
    duration = soup_detail.find(
        'span', attrs={'property': 'v:runtime'}).text.replace('分钟', '')
    # 提取评分
    score = soup_detail.find(
        'strong', attrs={'property': 'v:average'}).text
    # 提取评价人数
    rater_num = soup_detail.find(
        'span', attrs={'property': 'v:votes'}).text
    movie_list.append(
        [movie_num, movie_id, year, title, director, actors, genres, country, duration, score, rater_num])
    print(f'获取到第{movie_num}部电影：{title}')


# 爬取电影评论的用户ID和评分值
def scrape_movie_reviews(movie_id, ua, cookies):
    url = f'https://movie.douban.com/subject/{movie_id}/comments?start=0&limit=20&status=P&sort=new_score'
    print(url)
    time.sleep(5)
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'User-Agent': ua.random,
        'Connection': 'keep-alive',
        'Cookie': cookies,
        'Host': 'movie.douban.com',
        'Referer': f'https://www.douban.com/misc/sorry?original-url=https://movie.douban.com/subject/{movie_id}/comments?status=P',
    }
    review_list = []
    wrong_time = 0
    while url and len(review_list) < 100:
        retry_flag = True
        while retry_flag:
            proxy = get_proxy().get('proxy')
            time.sleep(20)
            try:
                # 代理
                response = requests.get(url, headers=headers, proxies={
                                        "http": "http://{}".format(proxy), "https": "https://{}".format(proxy)}, timeout=20)
                # response = requests.get(url, headers=headers, timeout=20)
                print(response)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                comments = soup.find_all('div', class_='comment-item')
                review_list = scrape_comment_info(
                    movie_id, comments, review_list)
                retry_flag = False
            except (requests.exceptions.RequestException, Exception) as e:
                print('Exception:', e)
                wrong_time += 1
                if wrong_time == 5:
                    if(len(review_list) > 70):
                        return review_list
                    return -1
                print('获取新代理...')
                delete_proxy(proxy)
        next_page = soup.find('a', class_='next')
        if next_page:
            url = f'https://movie.douban.com/subject/{movie_id}/comments' + \
                next_page['href']
        else:
            url = None
    return review_list


# 爬取每条评价
def scrape_comment_info(movie_id, comments, review_list):
    for comment in comments:
            # 获取用户id
        user_id = re.search(
            r'u(\d+)-', comment.find('div', class_='avatar').find('img')['src']).group(1)
        # 获取评分，若无评分就设置为0分
        try:
            rating = comment.find('span', class_='rating')['class'][0][-2]
        except:
            rating = '0'
        # 获取短评内容
        short = comment.find('span', class_='short').text
        review_list.append([movie_id, user_id, rating, short])
    return review_list


# 保存数据到CSV文件
def save_to_csv(data, filename):
    with open(filename, 'a', encoding='utf-8-sig', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)


# 对CSV文件去重
def remove_duplicates(csv_file):
    print('开始去重...')

    df = pd.read_csv(csv_file, header=None)
    df.drop_duplicates(inplace=True)
    df.to_csv(csv_file, index=False, header=False)

    print('去重完成')


if __name__ == '__main__':

    ua = UserAgent()
    # 开始运行前打开对应的网页设置好cookies
    # 根据经验这几个网页的cookies都一样，设置为变量直接传参
    # ps：这个cookies好像是不会很快改变但是我仍然设置了阶段性更新cookie
    cookies = input('请查看页面是否正常并更新cookie:')

    movie_data_file = '../数据分析/movie_data.csv'
    review_data_file = '../数据分析/movie_reviews.csv'

    # 爬取电影列表
    movie_list = scrape_movie_list(ua, cookies)
    # 保存电影列表数据到CSV文件
    save_to_csv(movie_list, movie_data_file)
    # 对电影列表去重
    remove_duplicates(movie_data_file)

    # 爬取电影评论数据并保存到CSV文件
    # 爬取评论列表，直接读文件里爬取好的id去爬评论
    with open(movie_data_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        movie_list = list(reader)

    # 存储检查点的文件名
    checkpoint_file = './checkpoint.txt'

    # 断点初始化为1
    last_save_index = 1

    for movie in movie_list:
        if os.path.exists(checkpoint_file):
            with open(checkpoint_file, 'r') as checkpoint:
                duandian = checkpoint.read().strip()
                last_save_index = int(duandian)
        else:
            duandian = '1'
        reviews = []
        movie_num = movie[0]
        try:
            if duandian == movie_num:
                time.sleep(5)
                movie_id = movie[1]
                print(f'开始抓取第{movie_num}部电影的评论')
                movie_reviews = scrape_movie_reviews(movie_id, ua, cookies)
                print(f"获取到第{movie_num}部电影的{len(movie_reviews)}条评论")
                if(len(movie_reviews) < 50):
                    break
                reviews.extend(movie_reviews)
                # 断点更新
                last_save_index += 1
                # 更新检查点为last_save_index,即当前电影的movie_num
                with open(checkpoint_file, 'w') as checkpoint:
                    checkpoint.write(str(last_save_index))
                # 补充评论列表数据到CSV文件
                save_to_csv(reviews, review_data_file)
                print('抓取完成，数据已保存')
        except Exception as e:
            print(e)
            break
    # 对内容进行去重
    remove_duplicates(review_data_file)
    # 对评论进行清理
    text_clean.process_csv(review_data_file)
    mongo.runMongo()

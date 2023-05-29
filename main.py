import csv
import os
import time
import re

import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

# 爬取豆瓣电影TOP250的电影ID、名称、时长、导演、国家/地区


def scrape_movie_list():
    ua = UserAgent()
    url = 'https://movie.douban.com/top250'
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.57',
        'Connection': 'keep-alive',
        'Cookie': 'll="118238"; bid=z8JTeV5on_8; dbcl2="244448908:WwAau8zKCt4"; push_noty_num=0; push_doumail_num=0; __utmv=30149280.24444; _pk_id.100001.4cf6=a9cd60a7576f5267.1685025570.; _vwo_uuid_v2=D1711C5E4BA5B06F9CC17BF1AE5F03A7A|103a245fab24370190d517c188a327ee; __yadk_uid=lplGjeOQBGThY6ihSj4d10TWY3rNkZKZ; ck=PeMP; _pk_ref.100001.4cf6=["","",1685369783,"https://www.bing.com/"]; _pk_ses.100001.4cf6=1; ap_v=0,6.0; __utma=30149280.220114507.1685025469.1685345603.1685369784.7; __utmb=30149280.0.10.1685369784; __utmc=30149280; __utmz=30149280.1685369784.7.3.utmcsr=bing|utmccn=(organic)|utmcmd=organic|utmctr=(not provided); __utma=223695111.1661283949.1685025570.1685345603.1685369784.7; __utmb=223695111.0.10.1685369784; __utmc=223695111; __utmz=223695111.1685369784.7.3.utmcsr=bing|utmccn=(organic)|utmcmd=organic|utmctr=(not provided); frodotk_db="f5d186392fb9c9b9e17492ab8f2d5d2b"',
        'Host': 'movie.douban.com',
        'Referer': 'https://www.bing.com/'
    }
    movie_list = []

    while url:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all('div', class_='item')

        for item in items:
            movie_url = item.find('a')
            movie_num = item.find('em').text
            movie_id = movie_url['href'].split('/')[-2]
            detail_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.57',
                'Host': 'movie.douban.com',
                'Connection': 'keep-alive',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
            }
            movie_detail = requests.get(
                url=movie_url['href'], headers=detail_headers)
            soup_detail = BeautifulSoup(movie_detail.text, 'html.parser')
            # 提取上映年份
            year = soup_detail.find(
                'span', class_='year').text.replace('(', '').replace(')', '')
            # 提取名称
            title = soup_detail.find(
                'span', attrs={'property': 'v:itemreviewed'}).text
            # 提取导演信息
            director = soup_detail.find(
                'a', attrs={'rel': 'v:directedBy'}).text
            # 提取演员信息（前四名）
            actors_box = soup_detail.find('span', class_='actor').find(
                'span', class_='attrs').find_all('a')
            actors = []
            for a in actors_box[:4]:
                actors.append(a.text)
            # 提取类型信息
            genre_spans = soup_detail.find_all(
                'span', attrs={'property': 'v:genre'})
            genres = [span.get_text() for span in genre_spans]

            # 提取制片国家信息
            country_span = soup_detail.find('span', string='制片国家/地区:')
            country = country_span.next_sibling.strip()
            # 提取时长信息
            time = soup_detail.find(
                'span', attrs={'property': 'v:runtime'}).text.replace('分钟', '')
            movie_list.append(
                [movie_num, movie_id, year, title, director, actors, genres, country, time])

        next_page = soup.find('span', class_='next').find('a')
        if next_page:
            url = url + next_page['href']
        else:
            url = None

    return movie_list

# 爬取电影评论的用户ID和评分值


def scrape_movie_reviews(movie_id):
    url = f'https://movie.douban.com/subject/{movie_id}/comments?start=0&limit=20&status=P&sort=new_score'
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.57',
        'Connection': 'keep-alive',
        'Cookie': 'll="118238"; bid=z8JTeV5on_8; dbcl2="244448908:WwAau8zKCt4"; push_noty_num=0; push_doumail_num=0; __utmv=30149280.24444; _vwo_uuid_v2=D1711C5E4BA5B06F9CC17BF1AE5F03A7A|103a245fab24370190d517c188a327ee; __yadk_uid=lplGjeOQBGThY6ihSj4d10TWY3rNkZKZ; ck=PeMP; __utmc=30149280; __utmz=30149280.1685369784.7.3.utmcsr=bing|utmccn=(organic)|utmcmd=organic|utmctr=(not provided); __utmc=223695111; __utmz=223695111.1685369784.7.3.utmcsr=bing|utmccn=(organic)|utmcmd=organic|utmctr=(not provided); frodotk_db="f5d186392fb9c9b9e17492ab8f2d5d2b"; _pk_id.100001.4cf6=a9cd60a7576f5267.1685025570.; _pk_ref.100001.4cf6=["","",1685376863,"https://www.bing.com/"]; _pk_ses.100001.4cf6=1; __utma=30149280.220114507.1685025469.1685373678.1685376864.9; __utmt=1; __utma=223695111.1661283949.1685025570.1685373678.1685376872.9; __utmb=223695111.0.10.1685376872; __utmb=30149280.6.9.1685376917562',
        'Host': 'movie.douban.com',
        'Referer': f'https://movie.douban.com/subject/{movie_id}/'
    }
    review_list = []

    while url and len(review_list) < 600:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        comments = soup.find_all('div', class_='comment-item')

        for comment in comments:
            user_id = re.search(
                r'u(\d+)-', comment.find('div', class_='avatar').find('img')['src']).group(1)
            rating = comment.find('span', class_='rating')['class'][0][-2]
            review_list.append([movie_id, user_id, rating])

        next_page = soup.find('a', class_='next')
        if next_page:
            url = next_page['href']
        else:
            url = None

        time.sleep(2)  # 添加2秒的延迟，避免过于频繁的请求

    return review_list

# 保存数据到CSV文件


def save_to_csv(data, filename):
    with open(filename, 'w', encoding='utf-8-sig', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)


# 获取脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))

# 爬取电影列表
movie_list = scrape_movie_list()

# 保存电影列表数据到CSV文件
save_to_csv(movie_list, os.path.join(script_dir, 'movie_data.csv'))

# 爬取电影评论数据并保存到CSV文件
reviews = []
for movie in movie_list:
    movie_id = movie[1]
    movie_reviews = scrape_movie_reviews(movie_id)
    reviews.extend(movie_reviews)

save_to_csv(reviews, os.path.join(script_dir, 'movie_reviews.csv'))

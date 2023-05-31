import csv
import os
import time
import re

import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup


# 基于proxy_pool项目的代理池
def get_proxy():
    return requests.get("http://127.0.0.1:5010/get?type=https").json()


def delete_proxy(proxy):
    requests.get("http://127.0.0.1:5010/delete/?proxy={}".format(proxy))
# 爬取豆瓣电影TOP250的电影序号、ID、名称、上映时间、导演、主演（前四名）、类型、国家/地区、时长


def scrape_movie_list(ua, cookies):
    url = 'https://movie.douban.com/top250'
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
        # 测试接口获取的代理
        while retry_flag:
            proxy = get_proxy().get('proxy')
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
            except Exception:
                print('该代理出错，获取新代理...')
                delete_proxy(proxy)
        next_page = soup.find('span', class_='next').find('a')
        # 添加2秒的延迟，避免过于频繁的请求
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
            try:
                time.sleep(5)
                movie_detail = requests.get(
                    url=movie_url['href'], headers=detail_headers, proxies={"http": "http://{}".format(proxy), "https": "https://{}".format(proxy)}, timeout=20)
                # movie_detail = requests.get(
                #     url=movie_url['href'], headers=detail_headers, timeout=20)
                print(movie_detail)
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
                duration = soup_detail.find(
                    'span', attrs={'property': 'v:runtime'}).text.replace('分钟', '')
                movie_list.append(
                    [movie_num, movie_id, year, title, director, actors, genres, country, duration])
                time.sleep(5)  # 添加2秒的延迟，避免过于频繁的请求
                print(f'获取到第{movie_num}部电影：{title}')
                retry_flag = False
            except Exception:
                print('该代理出错，获取新代理...')
                delete_proxy(proxy)

    return movie_list

# 爬取电影评论的用户ID和评分值


def scrape_movie_reviews(movie_id, ua, cookies):
    url = f'https://movie.douban.com/subject/{movie_id}/comments?start=0&limit=20&status=P&sort=new_score'
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'User-Agent': ua.random,
        'Connection': 'keep-alive',
        'Cookie': cookies,
        'Host': 'movie.douban.com',
        'Referer': f'https://movie.douban.com/subject/{movie_id}/'
    }
    review_list = []

    while url and len(review_list) < 600:
        if len(review_list) % 50 == 0:
            # 爬取50条评分后输入新的Cookies
            cookies = input('请更新Cookies:')
        retry_flag = True
        while retry_flag:
            proxy = get_proxy().get('proxy')
            try:
                time.sleep(5)
                response = requests.get(url, headers=headers, proxies={
                                        "http": "http://{}".format(proxy), "https": "https://{}".format(proxy)}, timeout=20)
                # response = requests.get(url, headers=headers, timeout=20)
                print(response)
                retry_flag = False
            except Exception:
                print('该代理出错，获取新代理...')
                delete_proxy(proxy)
        soup = BeautifulSoup(response.text, 'html.parser')
        comments = soup.find_all('div', class_='comment-item')
        review_list = scrape_comment_info(comments, review_list)
        next_page = soup.find('a', class_='next')
        if next_page:
            url = next_page['href']
        else:
            url = None
          # 添加20秒的延迟，避免过于频繁的请求
    print(f'获取到{movie_id}的评论信息')
    return review_list

# 爬取每条评价


def scrape_comment_info(comments, review_list):
    for comment in comments:
        user_id = re.search(
            r'u(\d+)-', comment.find('div', class_='avatar').find('img')['src']).group(1)
        rating = comment.find('span', class_='rating')['class'][0][-2]
        review_list.append([movie_id, user_id, rating])
    return review_list


# 保存数据到CSV文件
def save_to_csv(data, filename):
    with open(filename, 'w', encoding='utf-8-sig', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)


if __name__ == '__main__':

    ua = UserAgent()
    cookies = 'll="118238"; bid=z8JTeV5on_8; dbcl2="244448908:WwAau8zKCt4"; push_noty_num=0; push_doumail_num=0; __utmv=30149280.24444; _vwo_uuid_v2=D1711C5E4BA5B06F9CC17BF1AE5F03A7A|103a245fab24370190d517c188a327ee; __yadk_uid=lplGjeOQBGThY6ihSj4d10TWY3rNkZKZ; __utmz=30149280.1685369784.7.3.utmcsr=bing|utmccn=(organic)|utmcmd=organic|utmctr=(not provided); _pk_id.100001.4cf6=a9cd60a7576f5267.1685025570.; ck=PeMP; __utmc=30149280; __utmc=223695111; __utmz=223695111.1685423422.11.5.utmcsr=bing|utmccn=(organic)|utmcmd=organic|utmctr=(not provided); frodotk_db="a801fe883fb3bae4f805fb98bf1b30ac"; ct=y; _pk_ref.100001.4cf6=["","",1685457945,"https://www.douban.com/misc/sorry?original-url=https://movie.douban.com/top250?start=0&filter="]; _pk_ses.100001.4cf6=1; ap_v=0,6.0; __utma=30149280.220114507.1685025469.1685455446.1685457945.15; __utmb=30149280.0.10.1685457945; __utma=223695111.1661283949.1685025570.1685455446.1685457945.16; __utmb=223695111.0.10.1685457945'
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 爬取电影列表
    movie_list = scrape_movie_list(ua, cookies)
    # 保存电影列表数据到CSV文件
    save_to_csv(movie_list, os.path.join(script_dir, 'movie_data.csv'))

    # 爬取电影评论数据并保存到CSV文件
    # 爬取评论列表
    reviews = []
    cookies = input('准备爬取评分信息,请更新Cookie:')
    for movie in movie_list:
        movie_id = movie[1]
        movie_reviews = scrape_movie_reviews(movie_id, ua, cookies)
        reviews.extend(movie_reviews)
    # 保存评论列表数据到CSV文件
    save_to_csv(reviews, os.path.join(script_dir, 'movie_reviews.csv'))

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
        # 测试接口获取的代理
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
                save_to_csv_rewrite(movie_list, os.path.join(
                    script_dir, 'movie_data_test.csv'))
                print(url)
                print(e)
                print('获取新代理...')
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
            print(proxy)
            try:
                time.sleep(20)
                movie_detail = requests.get(
                    url=movie_url['href'], headers=detail_headers, proxies={"http": "http://{}".format(proxy), "https": "https://{}".format(proxy)}, timeout=20)
                movie_detail = requests.get(
                    url=movie_url['href'], headers=detail_headers, timeout=20)
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
                time.sleep(5)  # 添加2秒的延迟，避免过于频繁的请求
                print(f'获取到第{movie_num}部电影：{title}')
                retry_flag = False
            except Exception as e:
                print(e)
                print('获取新代理...')
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

    while url and len(review_list) < 200:
        # 可以尝试定期更新cookies，但200条应该用不上吧，看具体情况
        # if len(review_list) % 40 == 0:
        #     # 爬取200条评分后输入新的Cookies
        #     cookies = input('请更新Cookies:')
        retry_flag = True
        while retry_flag:
            proxy = get_proxy().get('proxy')
            try:
                time.sleep(5)
                # 代理
                response = requests.get(url, headers=headers, proxies={
                                        "http": "http://{}".format(proxy), "https": "https://{}".format(proxy)}, timeout=60)
                # 无代理
                # response = requests.get(url, headers=headers, timeout=20)
                print(response)
                retry_flag = False
            except Exception as e:
                print('Exception:', e)
                print('获取新代理...')
                delete_proxy(proxy)
        soup = BeautifulSoup(response.text, 'html.parser')
        comments = soup.find_all('div', class_='comment-item')
        review_list = scrape_comment_info(movie_id, comments, review_list)
        next_page = soup.find('a', class_='next')
        if next_page:
            url = f'https://movie.douban.com/subject/{movie_id}/comments' + \
                next_page['href']
            # time.sleep(20)  # 添加20秒的延迟，避免过于频繁的请求，建议这里在用自己ip爬的时候使用
        else:
            url = None

    print(f'获取到{movie_id}的评论信息')
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
        short = comment.find('span', class_='short').replace(' ', '')

        review_list.append([movie_id, user_id, rating, short])
    return review_list


# 保存数据到CSV文件
def save_to_csv(data, filename):
    with open(filename, 'a', encoding='utf-8-sig', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)


def save_to_csv_rewrite(data, filename):
    with open(filename, 'w', encoding='utf-8-sig', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)


if __name__ == '__main__':

    ua = UserAgent()
    # 开始运行前打开对应的网页设置好cookies
    # 根据经验这几个网页的cookies都一样，设置为变量直接传参
    # ps：这个cookies好像是不会很快改变但是我仍然设置了阶段性更新cookie
    cookies = 'll="118238"; bid=z8JTeV5on_8; push_noty_num=0; push_doumail_num=0; __utmv=30149280.24444; _vwo_uuid_v2=D1711C5E4BA5B06F9CC17BF1AE5F03A7A|103a245fab24370190d517c188a327ee; __yadk_uid=lplGjeOQBGThY6ihSj4d10TWY3rNkZKZ; _pk_id.100001.4cf6=a9cd60a7576f5267.1685025570.; ct=y; dbcl2="244448908:mBh74PWFgvo"; __utmz=30149280.1685523340.17.5.utmcsr=bing|utmccn=(organic)|utmcmd=organic|utmctr=(not provided); __utmz=223695111.1685523340.18.7.utmcsr=bing|utmccn=(organic)|utmcmd=organic|utmctr=(not provided); ck=SW0a; __utmc=30149280; __utmc=223695111; frodotk_db="7f9fd0e0d5b95a577edf72a2812c0f05"; _pk_ref.100001.4cf6=["","",1685538397,"https://www.bing.com/"]; ap_v=0,6.0; __utma=30149280.220114507.1685025469.1685523340.1685538398.18; __utma=223695111.1661283949.1685025570.1685523340.1685538398.19'
    # 获取脚本所在目录, 用于将输出的文件存放于脚本同目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 电影信息已经不需要再爬取了
    # 爬取电影列表
    movie_list = scrape_movie_list(ua, cookies)
    # 保存电影列表数据到CSV文件
    save_to_csv(movie_list, os.path.join(script_dir, 'movie_data.csv'))

    # 爬取电影评论数据并保存到CSV文件
    # 爬取评论列表，直接读文件里爬取好的id去爬评论
    # with open('E:\ProSpace\VSCodePros\Python\MLFinalWork\movie_data.csv', 'r', encoding='utf-8') as file:
    #     reader = csv.reader(file)
    #     movie_list = list(reader)
    reviews = []
    # 只爬评论就不用了
    # cookies = input('准备爬取评分信息,请更新Cookie:')
    for movie in movie_list:  # for movie in movie_list[:50]:在这里设置爬取的范围
        movie_id = movie[1]
        movie_reviews = scrape_movie_reviews(movie_id, ua, cookies)
        reviews.extend(movie_reviews)
    movie_reviews = scrape_movie_reviews(movie_id, ua, cookies)

    # 保存评论列表数据到CSV文件
    save_to_csv(reviews, os.path.join(script_dir, 'movie_reviews.csv'))

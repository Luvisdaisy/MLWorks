from bs4 import BeautifulSoup
import requests
import re


review_list = []


with open('comments.txt', 'r', encoding='utf-8') as file:
    html = file.read()
soup = BeautifulSoup(html, 'html.parser')
comments = soup.find_all('div', class_='comment-item')
for comment in comments:
    user_id = re.search(
        r'u(\d+)-', comment.find('div', class_='avatar').find('img')['src']).group(1)
    rating = comment.find('span', class_='rating')['class'][0][-2]

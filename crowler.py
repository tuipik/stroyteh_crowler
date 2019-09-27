from random import choice
import requests
from bs4 import BeautifulSoup
from multiprocessing import Pool


def get_html_info(url, useragent=None, proxy=None):
    '''Повертає html текст'''
    r = requests.get(url, headers=useragent, proxies=proxy)
    return r.text


def get_my_ip():
    ip_html = get_html_info('http://sitespy.ru/my-ip')
    soup = BeautifulSoup(ip_html, 'lxml')
    my_ip = soup.find('span', class_='ip').text.strip()
    my_useragent = soup.find('span', class_='ip').find_next_sibling('span').text.strip()

    print(my_ip)
    print(my_useragent)


def get_categories_pages(html):
    '''Повертає список посилань на товари'''
    soup = BeautifulSoup(html, 'lxml')
    soup_urls = soup.find('div', class_="itemsContent").find_all('div', class_='container-item')
    new_soup_urls = []

    for i in soup_urls:
        if i.find('span', class_='cena'):
            pass
        else:
            new_soup_urls += i.find_all('a', class_="productLink product-name")

    items_urls = [f"https://stroyteh.ua{i.get('href')}" for i in new_soup_urls]

    return items_urls


def get_all_active_items_urls(base_urls):
    '''Записує в файл посилання на всі активні товари'''
    user_agents = open('useragents.txt').read().split('\n')
    proxies = open('proxies.txt').read().split('\n')

    try:
        item_url_list = get_categories_pages(get_html_info(base_urls,
                                                           (lambda x: {'User-Agent': choice(x)})(user_agents),
                                                           (lambda y: {'http': 'http://' + choice(y)})(proxies)
                                                           )
                                             )
        with open('item_url_list.txt', 'a') as f:
            for url in item_url_list:
                f.write(f'{url}\n')
        f.close()

    except AttributeError as e:
        print(e)


def main():

    base_urls = open('urls.txt').read().split('\n')  # перелік посилань з sitemap.txt

    with Pool(2) as p:
        p.map(get_all_active_items_urls, base_urls)


if __name__ == "__main__":
    main()

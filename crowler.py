from random import choice
import requests
from bs4 import BeautifulSoup
from multiprocessing import Pool
import time
import threading
import concurrent.futures



def get_html_info(url, useragent=None, proxy=None):
    '''Повертає html текст'''
    print(f"Current thread is {threading.current_thread().name}")
    time.sleep(2)
    r = requests.get(url, headers=useragent, proxies=proxy)
    return r.text


# def get_my_ip():
#     user_agents = open('useragents.txt').read().split('\n')
#     proxies = open('proxies.txt').read().split('\n')
#     ip_html = get_html_info('http://sitespy.ru/my-ip', {"User-Agent": choice(user_agents)},
#                             # {"http": "http://92.50.155.218:8080"})
#                             {"http": "http://" + choice(proxies)})
#     soup = BeautifulSoup(ip_html, 'lxml')
#     my_ip = soup.find('span', class_='ip').text.strip()
#     my_useragent = soup.find('span', class_='ip').find_next_sibling('span').text.strip()
#
#     print(my_ip)
#     print(my_useragent)


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
    print(f"Кількість посилань на товари: {items_urls}")
    return items_urls

def get_proxy():
    proxies = open('proxies.txt').read().split('\n')
    response = False
    while response == False:
        pr = {"http": "http://" + choice(proxies)}
        try:
            ip_html = requests.get('http://sitespy.ru/my-ip', proxies=pr, timeout=5)
            if ip_html.status_code == requests.codes['ok']:
                response = True
                # soup = BeautifulSoup(ip_html.text, 'lxml')
                # my_ip = soup.find('span', class_='ip').text.strip()
                # my_useragent = soup.find('span', class_='ip').find_next_sibling('span').text.strip()
                # print(my_ip)
                # print(pr)
                return pr
        except Exception:
            pass


def get_all_active_items_urls(base_urls):
    '''Записує в файл посилання на всі активні товари'''
    user_agents = open('useragents.txt').read().split('\n')


    try:
        u_a = {"User-Agent": choice(user_agents)}
        pr = get_proxy()
        print('----', pr)
        item_url_list = get_categories_pages(get_html_info(base_urls, useragent=u_a, proxy=pr))

        with open('item_url_list.txt', 'a') as f:
            for url in item_url_list:
                f.write(f'{url}\n')
        f.close()

    except AttributeError as e:
        print(e)


def main():

    base_urls = open('urls.txt').read().split('\n')  # перелік посилань з sitemap.txt

    # with Pool(5) as p:
    #     p.map(get_all_active_items_urls, base_urls)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(get_all_active_items_urls, base_urls)


if __name__ == "__main__":
    main()

from random import choice,randint
import requests
from bs4 import BeautifulSoup
from multiprocessing import Pool
import time
import threading
import concurrent.futures


class ItemCrowler:
    def __init__(self, url):
        self.url = url
        self.user_agents = open('useragents.txt').read().split('\n')
        self.proxies = self.get_proxy()

    def get_proxy(self):
        proxies = open('proxies.txt').read().split('\n')
        response = False
        while response == False:
            pr_choice = choice(proxies)
            pr = {"http": "http://" + pr_choice,
                  "https": "https://" + pr_choice}
            try:
                ip_html = requests.get('http://sitespy.ru/my-ip',
                                       proxies=pr, timeout=2)
                if ip_html.status_code == requests.codes['ok']:
                    response = True
                    soup = BeautifulSoup(ip_html.text, 'lxml')
                    my_ip = soup.find('span', class_='ip').text.strip()
                    print(my_ip)
                    return pr
            except Exception:
                pass

    def get_html_info(self, url, useragent=None, proxy=None):
        '''Повертає html текст'''
        # time.sleep(randint(0, 4))
        r = requests.get(url, headers=useragent, proxies=proxy)
        return r.text

    def get_item_info(self, html):
        attempt = True
        counter = 0
        while attempt:
            try:
                soup = BeautifulSoup(html, 'lxml')

                # Конвектор универсальный Grunhelm GS-2000
                name = soup.find('h1', class_='titleopus').text.strip()
                soup_cat = soup.find_all('span', id='bc-home')[:4]

                # dict=> {'main': 'Главная', 'category': 'Бытовая техника',
                #         'subcategory_1': 'Обогреватели',
                #         'subcategory_2': 'Конвекторы'}
                categories = dict(zip(['main', 'category',
                                       'subcategory_1', 'subcategory_2'],
                                      [category.text.strip()
                                       for category in soup_cat]
                                      ))

                # int=> 598
                old_price = int(soup.find('div', class_='old-price').
                                text.split(' ')[0].strip())

                # int=> 588
                price = int(soup.find('span', itemprop='price').text.strip())

                soup_characteristics = soup.find('div', class_='row tab-pane').\
                    find('table', class_='reviewtab table table-striped').\
                    find_all('tr')

                # dict=> {'Производитель': 'Grunhelm',
                #         'Страна происхождения': 'Китай',
                #         'Гарантия': '1 год', 'Монтаж': 'Напольный/Настенный',}
                characteristics = {i.find('td').text.strip():
                                       i.find('td', class_='odd').text.strip()
                                   for i in soup_characteristics}

                soup_description = soup.find('div', class_='row tab-pane').\
                    find('div', style="").find_all('p')

                # text=> Электроконвектор универсальный «GRUNHELM»
                #        со ступенчатым регулятором мощности и пассивными
                #        опорами. Конвектор работает по принципу
                description = ' '.join([i.text.strip() for i in soup_description])



                print(description)
                attempt = False
            except AttributeError as e:
                print(e)
                counter += 1
                if counter > 5:
                    attempt = False



    def run(self):
        agent = {"User-Agent": choice(self.user_agents)}
        self.get_item_info(self.get_html_info(self.url,
                                              useragent=agent,
                                              proxy=self.proxies))




if __name__ == '__main__':
    urls = [
        'https://stroyteh.ua/product/werk-bm-2t50n-kompressor/',
        'https://stroyteh.ua/product/svitjazj-sd-610-rr-elektrodrelj/',
        'https://stroyteh.ua/product/konvektor-universaljnyj-grunhelm-gs-2000/'
    ]

    for url in urls:
        attempt = True
        while attempt:
            try:
                ItemCrowler(url).run()
                attempt = False
            except (requests.exceptions.ProxyError,
                    requests.exceptions.ConnectionError) as e:
                print(e)

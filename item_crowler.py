from random import choice,randint
import requests
from bs4 import BeautifulSoup
import psycopg2
import json
import db_connection
from multiprocessing import Pool
import time
import threading
import concurrent.futures
from pprint import pprint


class ItemCrowler:
    def __init__(self, url):
        self.url = url
        self.user_agents = open('useragents.txt').read().split('\n')
        self.time_begin = time.time()
        self.run()

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

    def write_log(self, file, url):
        with open(file, 'a') as f:
            f.write(f'{url}\n')
        f.close()


    def get_html_info(self, url, useragent=None, proxy=None):
        '''Повертає html текст'''
        time.sleep(randint(0, 4))
        r = requests.get(url, headers=useragent, proxies=proxy)
        return r.text

    def get_item_info(self, html):

        soup = BeautifulSoup(html, 'lxml')

        try:
            # Конвектор универсальный Grunhelm GS-2000
            name = soup.find('h1', class_='titleopus').text.strip()
        except Exception:
            name = 'Undefined'
            self.write_log('log_urls_with_exceptions.txt', self.url)

        try:
            soup_cat = soup.find_all('span', id='bc-home')[1:4]
            # dict=> {'category': 'Бытовая техника',
            #         'subcategory_1': 'Обогреватели',
            #         'subcategory_2': 'Конвекторы'}
            categories = dict(zip(['category',
                                   'subcategory_1', 'subcategory_2'],
                                  [category.text.strip()
                                   for category in soup_cat]
                                  ))
        except Exception:
            categories = {'category': 'Undefined','subcategory_1': 'Undefined',
                          'subcategory_2': 'Undefined'}
            self.write_log('log_urls_with_exceptions.txt', self.url)

        try:
            # int=> 598
            old_price = int(soup.find('div', class_='old-price').
                            text.split(' ')[0].strip())
        except Exception:
            old_price = 0
            self.write_log('log_urls_with_exceptions.txt', self.url)

        try:
            # int=> 588
            price = int(soup.find('span', itemprop='price').text.strip())
        except Exception:
            price = 0
            self.write_log('log_urls_with_exceptions.txt', self.url)

        try:
            soup_characteristics = soup.find('div', class_='row tab-pane').\
                find('table', class_='reviewtab table table-striped').\
                find_all('tr')
            # dict=> {'Производитель': 'Grunhelm',
            #         'Страна происхождения': 'Китай',
            #         'Гарантия': '1 год', 'Монтаж': 'Напольный/Настенный',}
            characteristics = {i.find('td').text.strip():
                                   i.find('td', class_='odd').text.strip()
                               for i in soup_characteristics}
        except Exception:
            characteristics = {}
            self.write_log('log_urls_with_exceptions.txt', self.url)

        try:
            soup_description = soup.find('div', class_='row tab-pane').\
                find('div', style="").find_all('p')

            # text=> Электроконвектор универсальный «GRUNHELM»
            #        со ступенчатым регулятором мощности и пассивными
            #        опорами. Конвектор работает по принципу
            description = ' '.join([i.text.strip() for i in soup_description])
        except Exception:
            description = ''
            self.write_log('log_urls_with_exceptions.txt', self.url)

        return name, categories, old_price, price, \
               characteristics, description


    def save_to_db(self, connection, data):

        cur = connection.cursor()
        cur.execute(
            "INSERT INTO ITEMS (NAME, CATEGORY, SUBCATEGORY_1, SUBCATEGORY_2, OLD_PRICE, "
            "NEW_PRICE, CHARACTERISTICS, DESCRIPTION) "
            "VALUES ('{name}', '{category}', '{subcategory_1}', '{subcategory_2}', "
            "'{old_price}', '{new_price}', '{characteristics}', '{description}')".
                format(name=data[0], category=data[1]['category'],
                       subcategory_1=data[1]['subcategory_1'],
                       subcategory_2=data[1]['subcategory_2'],
                       old_price=data[2], new_price=data[3],
                       characteristics=json.dumps(data[4], ensure_ascii=False),
                       description=data[5]
                       )
        )

        connection.commit()

    def run(self):
        con = psycopg2.connect(db_connection.connection)

        agent = {"User-Agent": choice(self.user_agents)}

        attempt = True
        while attempt:
            try:
                print(f"Current thread {threading.current_thread().name} "
                      f"begins {self.url}")
                self.save_to_db(con, self.get_item_info(self.get_html_info(
                                                      self.url,
                                                      useragent=agent,
                                                      proxy=self.get_proxy())))
                attempt = False
                self.write_log('log_urls_done.txt', self.url)
                print(f"Current thread {threading.current_thread().name} done "
                      f"{self.url}\nDone in {time.time() - self.time_begin} sec")
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.ProxyError) as e:
                print(e)
        con.close()





if __name__ == '__main__':

    # base_urls = open('item_url_list.txt').read().split('\n')  # перелік посилань на товари
    base_urls = open('log_urls_with_exceptions.txt').read().split('\n')  # перелік посилань на товари в яких були помилки
    urls = set(base_urls)


    t = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(ItemCrowler, urls)
    print(f'All items grabbed in {(time.time() - t)/60} minutes')

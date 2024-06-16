import random
import requests
import multiprocessing as mp
from io import BytesIO
import os


def wrap_proxy(proxy):
    if 'http' in proxy and '://' in proxy:
        proxy = proxy.replace('http://', '').replace('https://', '')
        proxy = 'http://' + proxy

    return {
        'http': proxy,
        'https': proxy
    }


def random_proxy(proxy_list: list):
    if proxy_list is None:
        return None
    
    return wrap_proxy(random.choice(proxy_list))


def test_proxy(proxy):
    proxy_wrapped = wrap_proxy(proxy)
    try:
        response = requests.get('http://httpbin.org/ip', proxies=proxy_wrapped, timeout=6)
        response_ip = response.json()['origin']
        
        if response_ip in proxy:
            print(response.status_code, proxy, response_ip)
            return proxy
    except Exception as e:
        return False


def read_proxy_file(path='proxies_example.txt'):
    with open(path, 'r', encoding='utf-8') as f:
        proxies = f.read().split('\n')
    return proxies


class Cache:
    directory = '.cache'
    path = os.path.join(directory, 'proxies.txt')
    proxies = None

    def __init__(self):
        if not os.path.exists(self.directory):
            os.mkdir(self.directory)

    def read(self):
        if self.proxies is None:
            self.proxies = read_proxy_file(self.path)
        return self.proxies
    
    def get_proxy(self):
        return random_proxy(self.read())


def read_cache_proxies():
    return read_proxy_file(Cache.path)

def write_proxies_file(proxies, path='proxies_example.txt'):
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(proxies))

def save_cache_proxies(proxies):
    write_proxies_file(proxies, Cache.path)


def proxies_test(proxies, n_jobs=mp.cpu_count() - 1):  
    with mp.Pool(n_jobs) as p:
        results = p.map(test_proxy, proxies)
    
    working_proxies = [proxy for proxy in results if isinstance(proxy, str)]
    print(len(working_proxies), 'proxies are working of', len(proxies), 'proxies.')
    return working_proxies


def test_and_rewrite_proxies(path='proxies_example.txt', n_jobs=mp.cpu_count() - 1):
    working_proxies = proxies_test(read_proxy_file(path), n_jobs=n_jobs)
    working_proxies = [proxy for proxy in working_proxies if isinstance(proxy, str)]
    print(working_proxies)
    unique_working_proxies = list(set(working_proxies))
    print(unique_working_proxies)
    write_proxies_file(unique_working_proxies, path)


def proxies_list_to_bytes_file(proxies):
    proxies_text = '\n'.join(proxies)
    return BytesIO(proxies_text.encode('utf-8'))


cache = Cache()


if __name__ == '__main__':
    test_and_rewrite_proxies()
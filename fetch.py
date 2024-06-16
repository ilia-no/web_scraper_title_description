import cloudscraper
from bs4 import BeautifulSoup
import requests
import json
from requests.exceptions import ReadTimeout, ConnectionError, TooManyRedirects, ProxyError
import multiprocessing as mp
import os
import proxy



class Exceptions:
    timeout = 'Server Timeout (Redirect or Server Error)'
    client_timeout = 'Client Timeout'
    dns = "DNS_ERROR (domain doesn't exist)"
    proxy = "Proxy Error (Exceeded retries)"


def get_url(url, secure=True):
    if '://' not in url:
        protocol = 'https' if secure else "http"
        url = protocol + '://' + url
    
    if url.endswith('/*'):
        url = url[:-1]

    print(f'{url=}')
    return url


def get_captcha_provider(
    provider_name="2captcha",
    api_key=None,
):
    return dict(
        provider=provider_name,
        api_key=api_key,
    )
    

def fetch_site(url, load_delay=None, wrapped_proxy=None) -> str:
    if all([
        int(os.environ.get('USE_CAPTCHA_SOLVER', '0')),
        os.getenv('CAPTCHA_API_KEY'),
        os.getenv('CAPTCHA_PROVIDER_NAME')]):
            captcha_provider = get_captcha_provider(os.getenv('CAPTCHA_PROVIDER_NAME'), os.getenv('CAPTCHA_API_KEY'))
    else:
        captcha_provider = None

    if load_delay is None:
        load_delay = int(os.environ.get('LOAD_DELAY', 5))


    url = get_url(url)
    scraper = cloudscraper.create_scraper(
        interpreter="nodejs",
        delay=load_delay,
        browser={
            "browser": "chrome",
            "platform": "windows",
            "desktop": True,
        },
        captcha=captcha_provider,
    )

    try:
        response = scraper.get(url, timeout=int(os.environ.get('TIMEOUT', 10)), proxies=wrapped_proxy)
    except requests.exceptions.SSLError:
        url = url.replace('https://', 'http://')
        response = scraper.get(url, timeout=int(os.environ.get('TIMEOUT', 10)), proxies=wrapped_proxy)
    except ReadTimeout:
        return dict(error=Exceptions.client_timeout, url=url)

    print(f'{response.status_code=}')

    if response.status_code == 200:
        # Return the HTML content of the webpage
        return response.content
    else:
        # Print an error message if the request fails
        print(f"Failed to fetch URL: {url}. Status code: {response.status_code}")
        return dict(error=f"Status code: {response.status_code}", url=url)


def get_title(soup):
    title = soup.find('meta', {'property': 'og:title'})
    if title:
        title = title['content']
    else:
        title = soup.find('title').string if soup.title else None
    return title    


def get_description(soup):
    description = soup.find('meta', {'property': 'og:description'})
    if description:
        description = description['content']
    else:
        description = soup.find('meta', {'name': 'description'})['content'] if soup.find('meta', {'name': 'description'}) else None
    return description


def fetch_meta_from_page_content(content):
    if content is None:
        return None
    
    soup = BeautifulSoup(content, 'html.parser')
    head = soup.head

    title = get_title(head)
    description = get_description(head)

    print(f'{title=} {description=}')
    return dict(title=title, description=description)


def fetch_meta(url, do_json=True, use_proxy=None, proxy_retries=None):
    if proxy_retries is None:
        proxy_retries = int(os.environ.get('PROXY_RETRIES', 8))

    if ';' in url:
        url = url.split(';')[0]
    if '.' not in url:
        return None

    if bool(int(os.getenv('USE_PROXIES', '0'))):
        use_proxy = True
    
    for retry_index in range(proxy_retries + 1):
        if use_proxy:
            wrapped_proxy = proxy.cache.get_proxy()
        else:
            wrapped_proxy = None

        try:
            if retry_index > 0:
                print(f'\nRetry {retry_index} for {url}')

            print(f'\nFetching meta for {url} {wrapped_proxy=}')
            content = fetch_site(url, wrapped_proxy=wrapped_proxy)
            if isinstance(content, dict):
                meta = content
            else:
                meta = fetch_meta_from_page_content(content)
            break

        except ProxyError:
            meta = {'error': Exceptions.proxy}
            if retry_index == proxy_retries:
                break

        except (ConnectionError, TooManyRedirects):
            meta = {'error': Exceptions.timeout}
            break
        except Exception as e:
            meta = dict(error=f'{type(e).__name__} {e}')
            if '[Errno 8] nodename nor servname provided, or not known)' in str(e):
                meta['error'] = Exceptions.dns
            break

    meta['url'] = url
    print(f'{meta=}\n')

    if do_json:
        meta = json.dumps(meta)
    return meta


def fetch_meta_and_save(url, path='results.txt'):
    meta = fetch_meta(url)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(meta) + '\n')
    return True


def fetch_meta_mp(urls, n_jobs=2):
    with mp.Pool(n_jobs) as p:
        results = p.map(fetch_meta, urls)
        
    print(f'{results=}')
    return results

    
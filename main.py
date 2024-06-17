import proxy
from urls import get_urls
from fetch import fetch_meta_mp
from export import json_list_to_bytes_file

import streamlit as st
from io import BytesIO
import os
import pandas as pd
import multiprocessing as mp
import dotenv


APP_TITLE = "Title & Description Scraper"
st.set_page_config(
    page_title=APP_TITLE,
)


dotenv_file = dotenv.find_dotenv()
if dotenv_file:
    dotenv.load_dotenv(dotenv_file)


def set_env_var(key, value, dotenv_file=dotenv_file):
    if isinstance(value, bool):
        value = int(value)
    
    if not isinstance(value, str):
        value = str(value)

    os.environ[key] = value
    dotenv.set_key(dotenv_file, key, value)
    dotenv.load_dotenv(dotenv_file)


def set_default_settings():
    dotenv_path = '.env'
    set_env_var('TIMEOUT', 10, dotenv_path)
    set_env_var('LOAD_DELAY', 5, dotenv_path)
    set_env_var('PROXY_RETRIES', 8, dotenv_path)
    

def load_file(file):
    new_file = BytesIO()
    new_file.write(file.getvalue())
    new_file.seek(0)
    return new_file


def load_urls(file, start=1, end=None, column_name='Location on Site', sep=','):
    st.session_state['urls'] = get_urls(load_file(file), start=start - 1, end=end - 1, column_name=column_name, sep=sep)
    

if not dotenv_file:
    set_default_settings()
    dotenv_file = dotenv.find_dotenv()
    dotenv.load_dotenv(dotenv_file)
    st.rerun()

st.title(APP_TITLE)

st.subheader('Load website urls')
urls_file = st.file_uploader("Upload .csv file with urls", type=['csv'])
if urls_file or st.session_state.get('urls_file'):
    st.session_state['urls_file'] = urls_file
    if not st.session_state.get('all_urls'):
        st.session_state['all_urls'] = get_urls(load_file(urls_file))
        
    col1, col2 = st.columns(2)

    with col1:
        urls_start_index = st.number_input('Start row index (URLs)', min_value=1, max_value=len(st.session_state['all_urls']) + 1, value=1, key='start')
    
    with col2:
        urls_end_index = st.number_input('End row index (URLs)', min_value=1, max_value=len(st.session_state['all_urls']) + 1, value=len(st.session_state['all_urls']) + 1, key='end')
    
    col3, col4 = st.columns(2)
    with col3:
        urls_sep = st.text_input('CSV Separator', value=',', key='sep')
    
    with col4:
        urls_column_name = st.text_input('Column name', value='Location on Site', key='column_name')

    if st.button('Load urls', key='slice_urls'):
        load_urls(urls_file, start=urls_start_index, end=urls_end_index, column_name=urls_column_name, sep=urls_sep)
        st.text(f"{len(st.session_state['urls'])} urls successfully loaded")

    if st.session_state.get('urls'):
        st.dataframe(
            pd.DataFrame(st.session_state['urls'], columns=['urls'], index=range(urls_start_index, urls_end_index)),
            column_config={
                "widgets": st.column_config.TextColumn(
                    "Widgets",
                    help="Urls list",
                    default="st.",
                    validate="^st\.[a-z_]+$",
                )
            },
            hide_index=False,
            use_container_width=True,
        )
    

st.subheader('Scraping settings')
threads_amount = st.slider('Number of threads (more - faster)', min_value=1, max_value=mp.cpu_count() - 1,
                               value=int(os.environ.get('THREADS_AMOUNT', mp.cpu_count() - 1)), key='threads_amount')


col1, col2, col3 = st.columns(3)
with col1:
    timeout = st.number_input('Timeout (seconds)', min_value=1, max_value=300, value=int(os.environ['TIMEOUT']), key='timeout')
    

with col2:
    load_delay = st.number_input('Load delay', min_value=1, max_value=300, value=int(os.environ['LOAD_DELAY']), key='load_delay')

with col3:
    proxy_retries = st.number_input('Proxy retries', min_value=1, max_value=20, value=int(os.environ['PROXY_RETRIES']), key='proxy_retries')

if st.button('Save', key='save_threads'):
    set_env_var('TIMEOUT', timeout)
    set_env_var('LOAD_DELAY', load_delay)
    set_env_var('THREADS_AMOUNT', threads_amount)
    set_env_var('PROXY_RETRIES', proxy_retries)


st.subheader('Captcha solver')
use_captcha_solver = st.toggle('Use captcha solver', key='use_captcha_solver', value=bool(int(os.environ.get('USE_CAPTCHA_SOLVER', '0'))))
if use_captcha_solver:
    set_env_var('USE_CAPTCHA_SOLVER', use_captcha_solver)
    col1, col2 = st.columns(2)

    with col1:
        captcha_providers_options = ['2captcha', 'anticaptcha', 'CapSolver', 'CapMonster Cloud', 'deathbycaptcha', '9kw']
        captcha_provider = st.selectbox('Captcha provider',
                                        captcha_providers_options,
                                        index=captcha_providers_options.index(os.getenv('CAPTCHA_PROVIDER_NAME')),
                                        help="https://pypi.org/project/cloudscraper/")

    with col2:
        captcha_api_key = st.text_input('API key', type='password', value=os.getenv('CAPTCHA_API_KEY'))

    if st.button('Save', key='save_captcha'):
        set_env_var('CAPTCHA_PROVIDER_NAME', captcha_provider)
        set_env_var('CAPTCHA_API_KEY', captcha_api_key)
else:
    set_env_var('USE_CAPTCHA_SOLVER', use_captcha_solver)


st.subheader('Proxies')
use_proxies = st.toggle('Use proxies', key='use_proxies', value=bool(int(os.environ.get('USE_PROXIES', '0'))))
if use_proxies:
    set_env_var('USE_PROXIES', use_proxies)
    proxies_file = st.file_uploader("Upload proxies", type=['txt'])

    if proxies_file:
        lines = load_file(proxies_file).readlines()
        proxies = [line.decode('utf-8').strip() for line in lines]
        st.session_state['all_proxies'] = proxies
        st.session_state['proxies'] = proxies

        col1, col2 = st.columns(2)
        with col1:
            proxies_start_index = st.number_input("Proxies start index", min_value=1, max_value=len(proxies) + 1, value=1, key='proxies_start_index')

        with col2:
            proxies_end_index = st.number_input("Proxies end index", min_value=1, max_value=len(proxies) + 1, value=len(proxies) + 1, key='proxies_end_index')
        
        st.session_state['proxies'] = st.session_state['all_proxies'][proxies_start_index - 1 : proxies_end_index - 1]

        test_proxies_button = st.button('Test proxies', key='test_proxies', use_container_width=True)
        

        col1, col2 = st.columns(2)
        with col1:
            st.text(f'All proxies ({len(st.session_state["proxies"])})')
            st.dataframe(pd.DataFrame(st.session_state['proxies'], columns=['proxies'], index=range(proxies_start_index, proxies_end_index)))

        with col2:
            tested_proxies_title = st.empty()
            tested_proxies = st.empty()
            download_tested_proxies = st.empty()

        if any([test_proxies_button, st.session_state.get('test_proxies_button', False)]):

            if not st.session_state.get('test_proxies_button', False):
                working_proxies = proxy.proxies_test(st.session_state['proxies'], n_jobs=threads_amount)
                st.session_state['working_proxies'] = working_proxies
                st.session_state['test_proxies_button'] = True

            if st.session_state['test_proxies_button']:
                tested_proxies_title.text(f"Working proxies ({len(st.session_state['working_proxies'])})")
                tested_proxies.dataframe(pd.DataFrame(st.session_state['working_proxies'], columns=['working_proxies'], index=range(1, len(st.session_state['working_proxies']) + 1)))
            
            download_tested_proxies.download_button(
                'Download tested proxies',
                proxy.proxies_list_to_bytes_file(st.session_state['working_proxies']),
                'Tested Proxies.txt',
                key='download_tested_proxies',
                use_container_width=True
                )
else:
    set_env_var('USE_PROXIES', use_proxies)


st.header('Start scraping')
if st.button('Run', key="start_scraping", use_container_width=True):
    if int(os.getenv('USE_PROXIES')):
        if st.session_state.get('working_proxies'):
            proxies = st.session_state.get('working_proxies')
        else:
            proxies = st.session_state.get('proxies')
        
        proxy.save_cache_proxies(proxies)


    st.text(f'Scraping started. {len(st.session_state["urls"])} urls' + f', {len(proxies)} proxies' if int(os.getenv('USE_PROXIES')) else '')
    results = fetch_meta_mp(st.session_state['urls'], n_jobs=threads_amount)
    output_file = json_list_to_bytes_file(results)

    st.download_button('Download scraped data', output_file, 'Scraped Data.csv', key='download_output')
    st.text("Scraping finished")


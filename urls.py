import pandas as pd


def get_urls(path, start=0, end=None, column_name='Location on Site', sep=','):
    urls = pd.read_csv(path, sep=sep)[column_name].tolist()
    if end is None:
        end = len(urls)
    
    return urls[start:end]


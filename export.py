import json
import pandas as pd
from io import BytesIO


def json_list_to_df(data: list, index_col='url') -> pd.DataFrame:
    data = [json.loads(item) for item in data]
    df = pd.DataFrame(data)
    if 'error' not in df.columns:
        df['error'] = pd.NA

    df = df[['url', 'title', 'description', 'error']]
    return df

def json_list_to_csv(data: list, path: str='results.csv'):
    df = json_list_to_df(data)
    df.to_csv(path, index=False)
    print(f'Saved to {path}')


def json_list_to_bytes_file(data: list):
    file = BytesIO()
    file.write(file.getvalue())
    file.seek(0)
    json_list_to_csv(data, file)
    return file
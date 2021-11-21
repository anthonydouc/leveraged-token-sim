# -*- coding: utf-8 -*-
import datetime
import os
import pathlib
import pandas as pd

import ssl

dir_path = os.path.dirname(os.path.realpath(__file__))

data_dir = os.path.join(dir_path, 'data')

def read_data_from_api(api_url, data_file='data'):

    today = datetime.datetime.utcnow().strftime('%m-%d')

    data_dir = os.path.join(dir_path, 'data')

    pathlib.Path(data_dir).mkdir(parents=True, exist_ok=True)

    files = os.listdir(data_dir)

    exisiting_files = [file for file in files if data_file in file]

    if len(exisiting_files) > 0:
        data_existing = exisiting_files[0]
    else:
        data_existing = None

    try:
        if f'{data_file}_{today}.csv' in files:
            data = pd.read_csv(os.path.join(data_dir, f'{data_file}_{today}.csv'))
        else:
            data = pd.read_json(api_url)
            data.to_csv(os.path.join(data_dir, f'{data_file}_{today}.csv'))
            # delete existing data
            if data_existing is not None:
                if os.path.exists(os.path.join(data_dir, data_existing)):
                    os.remove(os.path.join(data_dir, data_existing))
            # TODO: add in another case to just read in a non dated file?
           
    except:
        # could not access API - revert to last save.
        data = pd.read_csv(os.path.join(data_dir, data_existing))

    return data


def read_prices_from_api():
    """
    Reads daily token price data from a Flipside Crypto API endpoint.
    """
    
    ssl._create_default_https_context = ssl._create_unverified_context
    
    url = ('https://api.flipsidecrypto.com/api/v2/queries/'
           '2aca3d2a-fe73-4726-90f1-26e89076617e/data/latest')
    
    price_data = read_data_from_api(url, 'token_prices')

    price_data['DAY_DATE'] = pd.to_datetime(price_data['DAY_DATE'])
    
    return price_data


def get_token_prices(price_data, token, min_date=None, max_date=None):
    """
    Gets hourly price data for the specified token. Optionally filters
    between min_date and max_date.
    """    
    
    price_data = price_data[price_data['SYMBOL'] == token]
    
    if min_date is not None:
        price_data = price_data[price_data['DAY_DATE'] >= min_date]
    
    if max_date is not None:
        price_data = price_data[price_data['DAY_DATE'] <= max_date]
    
    return price_data


def read_liquidity_from_api():
    """
    Reads in daily token balances from a Flipside endpoint and converts
    to hourly data (assuming constant balance within each day).
    """
    ssl._create_default_https_context = ssl._create_unverified_context
    
    url = ('https://api.flipsidecrypto.com/api/v2/queries/'
           'd4dcdfbe-f25c-4617-a572-e914f1aa21e5/data/latest')
    
    pool_data = read_data_from_api(url, 'pool_balances')

    pool_data['DATE'] = pd.to_datetime(pool_data['DATE'])
        
    pools = list(pool_data['POOL_NAME'].unique())
    
    data_list = []
    
    for pool in pools:
        data = pool_data[pool_data['POOL_NAME'] == pool]
        
        currencies = list(data['CURRENCY'].unique())
        
        pools = [pool]
        
        min_date, max_date = data['DATE'].min(), data['DATE'].max()
    
        dates = pd.date_range(min_date, max_date, freq='h')

        idx = (pd.MultiIndex.
               from_product((dates, currencies, pools),
                            names=['DATE','CURRENCY','POOL_NAME']))

        data = (data.set_index(['DATE', 'CURRENCY', 'POOL_NAME'])
                .reindex(idx).reset_index())
        
        data_list.append(data)
        
    pool_data = pd.concat(data_list)
           
    pool_data['CURRENCY'] = pool_data['CURRENCY'].map({'LUNA':'pool_y_i',
                                                       'MIR':'pool_y_i',
                                                       'ANC':'pool_y_i',
                                                       'UST':'pool_x_i'})
    
    pool_data = (pool_data.set_index(['DATE', 'CURRENCY','POOL_NAME'])
                 .unstack(1)['BALANCE'].reset_index())
    
    pool_data['pool_x_i'] = (pool_data.groupby('POOL_NAME')['pool_x_i']
                             .fillna(method='ffill'))
    
    pool_data['pool_y_i'] = (pool_data.groupby('POOL_NAME')['pool_y_i']
                             .fillna(method='ffill'))

    return pool_data


def get_pool_liquidity(pool_data, pool, min_date=None, max_date=None):
    """
    Returns hourly pool balance data for each token.
    """
    pool_data = pool_data[pool_data['POOL_NAME'] == pool]
    
    if min_date is not None:
        pool_data = pool_data[pool_data['DATE'] >= min_date]
    
    if max_date is not None:
        pool_data = pool_data[pool_data['DATE'] <= max_date]

    return pool_data[['DATE', 'pool_x_i','pool_y_i']]


def get_model_data(token, min_date=None, max_date=None):
    
    token_pools = {'LUNA': 'LUNA-UST',
                   'MIR': 'MIR-UST',
                   'ANC': 'ANC-UST'}
    
    pool = token_pools[token]
    
    all_token_prices = read_prices_from_api()
    
    token_prices = get_token_prices(all_token_prices, token, min_date, max_date)
    
    min_date, max_date = all_token_prices['DAY_DATE'].min(), all_token_prices['DAY_DATE'].max()
    
    all_pool_liquidity = read_liquidity_from_api()
    
    pool_liquidity = get_pool_liquidity(all_pool_liquidity, pool, min_date, max_date)
    
    return token_prices, all_token_prices, pool_liquidity, all_pool_liquidity

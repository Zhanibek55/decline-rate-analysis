# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import os
import sys
import io

# Настройка кодировки вывода
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='backslashreplace')

def safe_print(text):
    """Безопасный вывод текста с обработкой ошибок кодировки"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', errors='backslashreplace').decode('ascii'))

# Получаем текущий каталог
current_dir = os.path.dirname(os.path.abspath(__file__))
test_data_dir = os.path.join(current_dir, "test_data")

# Пути к файлам данных
prod_file = os.path.join(test_data_dir, "prod_data.csv")
events_file = os.path.join(test_data_dir, "events_data.csv")

try:
    # Загрузка данных с помощью pandas вместо polars
    safe_print("Loading production data from: " + prod_file)
    prod_df = pd.read_csv(prod_file)
    safe_print(f"Number of rows in production data: {len(prod_df)}")
    safe_print(f"Columns in production data: {list(prod_df.columns)}")
    safe_print("Sample production data:")
    safe_print(prod_df.head(5))
    
    safe_print("\nLoading events data from: " + events_file)
    events_df = pd.read_csv(events_file)
    safe_print(f"Number of rows in events data: {len(events_df)}")
    safe_print(f"Columns in events data: {list(events_df.columns)}")
    safe_print("Sample events data:")
    safe_print(events_df.head(5))
    
    # Анализ данных добычи
    safe_print("\nProduction data analysis:")
    safe_print(f"Unique wells: {prod_df['uwi'].unique().tolist()}")
    safe_print(f"Number of wells: {len(prod_df['uwi'].unique())}")
    safe_print(f"Unique horizons: {prod_df['horizon'].unique().tolist()}")
    unique_dates = sorted(prod_df['date'].unique())
    safe_print(f"Number of unique dates: {len(unique_dates)}")
    safe_print(f"Minimum date: {min(unique_dates)}")
    safe_print(f"Maximum date: {max(unique_dates)}")
    
    # Проверка данных для расчета темпа падения
    start_date = "2023/01/01"
    end_date = "2024/01/01"
    safe_print(f"\nCalculating decline rate for period: {start_date} - {end_date}")
    
    # Фильтрация по датам
    filtered_df = prod_df[(prod_df['date'] >= start_date) & (prod_df['date'] <= end_date)]
    safe_print(f"Number of rows after date filtering: {len(filtered_df)}")
    
    # Проверка наличия данных в отфильтрованном диапазоне
    if len(filtered_df) == 0:
        safe_print("No data in the specified date range!")
        sys.exit(0)
    
    # Группировка по горизонту
    group_by_cols = ["horizon"]
    agg = filtered_df.groupby(['date'] + group_by_cols).agg(
        sum_oil_rate=('oil_rate', 'sum'),
        well_count=('uwi', 'count')
    ).reset_index()
    
    safe_print("\nGrouping result by horizon:")
    safe_print(agg.head(5))
    
    # Проверка наличия данных для двух дат (t0 и t1)
    unique_dates = sorted(agg['date'].unique())
    safe_print(f"\nUnique dates after grouping: {unique_dates}")
    
    if len(unique_dates) >= 2:
        t0 = min(unique_dates)
        t1 = max(unique_dates)
        safe_print(f"Start date (t0): {t0}")
        safe_print(f"End date (t1): {t1}")
        
        # Создание сводной таблицы для анализа
        pivoted = pd.pivot_table(
            agg, 
            values=['sum_oil_rate', 'well_count'],
            index=group_by_cols,
            columns=['date']
        )
        
        safe_print("\nPivot result:")
        safe_print(pivoted)
        
        # Проверка наличия колонок для расчета
        rate_t0_col = ('sum_oil_rate', t0)
        rate_t1_col = ('sum_oil_rate', t1)
        
        safe_print(f"\nChecking if columns for t0 and t1 exist:")
        if rate_t0_col in pivoted.columns and rate_t1_col in pivoted.columns:
            safe_print("Both columns are present")
            
            # Расчет темпа падения
            result = pd.DataFrame(index=pivoted.index)
            result['sum_rate_t0'] = pivoted[rate_t0_col]
            result['sum_rate_t1'] = pivoted[rate_t1_col]
            result['well_count_t0'] = pivoted[('well_count', t0)]
            result['well_count_t1'] = pivoted[('well_count', t1)]
            
            # Проверка на ненулевые значения
            valid_rows = (result['sum_rate_t0'] > 0) & (result['sum_rate_t1'] > 0)
            if valid_rows.any():
                result = result[valid_rows].copy()
                result['decline_rate'] = 1 - (result['sum_rate_t1'] / result['sum_rate_t0'])
                result['decline_percent'] = result['decline_rate'] * 100
                
                safe_print("\nDecline rate calculation result:")
                safe_print(result)
                
                # Анализ причин отсутствия результатов в приложении
                safe_print("\nPossible reasons for no results in the app:")
                safe_print("1. Check if the date range in the app matches the data")
                safe_print(f"2. Check if wells have production data at both t0 ({t0}) and t1 ({t1})")
                safe_print("3. Check if the grouping in the app matches the data structure")
                safe_print("4. Check if there are any filters applied in the app that remove all data")
            else:
                safe_print("\nNo wells with non-zero production at both dates")
                safe_print("This is likely why no results are shown in the app")
        else:
            safe_print("Required columns are missing:")
            safe_print(f"Columns in pivot: {pivoted.columns}")
    else:
        safe_print("Not enough unique dates for decline rate calculation (minimum 2 required)")
        safe_print("This is likely why no results are shown in the app")
    
except Exception as e:
    safe_print(f"Error analyzing data: {str(e)}")

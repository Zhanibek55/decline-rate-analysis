import polars as pl
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import os
import pandas as pd
from logger import logger, safe_log

def load_data(uploaded_prod_file=None, uploaded_events_file=None):
    """
    Загружает данные из файлов или генерирует тестовые данные
    
    Args:
        uploaded_prod_file: Загруженный файл с данными добычи
        uploaded_events_file: Загруженный файл с данными событий
        
    Returns:
        tuple: (prod_df, events_df) - DataFrame с данными добычи и событиями
    """
    logger.info("Начало загрузки данных")
    
    if uploaded_prod_file is not None and uploaded_events_file is not None:
        logger.info(f"Загрузка пользовательских файлов: {uploaded_prod_file.name}, {uploaded_events_file.name}")
        # Загрузка данных из пользовательских файлов
        try:
            if uploaded_prod_file.name.endswith('.parquet'):
                logger.info("Загрузка parquet файла с данными добычи")
                prod_df = pl.read_parquet(uploaded_prod_file)
            elif uploaded_prod_file.name.endswith('.csv'):
                logger.info("Загрузка CSV файла с данными добычи")
                # Сохраняем временный файл для чтения
                with open("temp_prod.csv", "wb") as f:
                    f.write(uploaded_prod_file.getvalue())
                logger.debug("Временный файл temp_prod.csv создан")
                
                # Пробуем различные кодировки
                encodings = ["utf-8", "cp1251", "latin1", "windows-1251", "ascii", "iso-8859-1"]
                prod_df = None
                
                for encoding in encodings:
                    try:
                        logger.debug(f"Пробуем кодировку {encoding} для файла добычи")
                        prod_df = pl.read_csv("temp_prod.csv", encoding=encoding)
                        logger.info(f"Успешно загружен файл добычи с кодировкой {encoding}")
                        break
                    except Exception as e:
                        logger.warning(f"Ошибка при чтении с кодировкой {encoding}: {str(e)}")
                
                if prod_df is None:
                    logger.error("Не удалось прочитать файл добычи ни с одной кодировкой")
                    # Пробуем прочитать файл построчно
                    logger.info("Пробуем прочитать файл построчно")
                    try:
                        import csv
                        rows = []
                        with open("temp_prod.csv", "r", encoding="latin1", errors="replace") as f:
                            reader = csv.reader(f)
                            header = next(reader)
                            for row in reader:
                                rows.append(row)
                        
                        # Создаем DataFrame из строк
                        pd_df = pd.DataFrame(rows, columns=header)
                        prod_df = pl.from_pandas(pd_df)
                        logger.info("Успешно прочитан файл добычи построчно")
                    except Exception as e:
                        logger.error(f"Ошибка при построчном чтении: {str(e)}")
                        raise ValueError(f"Не удалось прочитать файл добычи: {str(e)}")
                
            elif uploaded_prod_file.name.endswith(('.xls', '.xlsx')):
                logger.info("Загрузка Excel файла с данными добычи")
                # Сохраняем временный файл для чтения
                with open("temp_prod.xlsx", "wb") as f:
                    f.write(uploaded_prod_file.getvalue())
                prod_df = pl.read_excel("temp_prod.xlsx")
            
            if uploaded_events_file.name.endswith('.parquet'):
                logger.info("Загрузка parquet файла с данными событий")
                events_df = pl.read_parquet(uploaded_events_file)
            elif uploaded_events_file.name.endswith('.csv'):
                logger.info("Загрузка CSV файла с данными событий")
                # Сохраняем временный файл для чтения
                with open("temp_events.csv", "wb") as f:
                    f.write(uploaded_events_file.getvalue())
                logger.debug("Временный файл temp_events.csv создан")
                
                # Пробуем различные кодировки
                encodings = ["utf-8", "cp1251", "latin1", "windows-1251", "ascii", "iso-8859-1"]
                events_df = None
                
                for encoding in encodings:
                    try:
                        logger.debug(f"Пробуем кодировку {encoding} для файла событий")
                        events_df = pl.read_csv("temp_events.csv", encoding=encoding)
                        logger.info(f"Успешно загружен файл событий с кодировкой {encoding}")
                        break
                    except Exception as e:
                        logger.warning(f"Ошибка при чтении с кодировкой {encoding}: {str(e)}")
                
                if events_df is None:
                    logger.error("Не удалось прочитать файл событий ни с одной кодировкой")
                    # Пробуем прочитать файл построчно
                    logger.info("Пробуем прочитать файл событий построчно")
                    try:
                        import csv
                        rows = []
                        with open("temp_events.csv", "r", encoding="latin1", errors="replace") as f:
                            reader = csv.reader(f)
                            header = next(reader)
                            for row in reader:
                                rows.append(row)
                        
                        # Создаем DataFrame из строк
                        pd_df = pd.DataFrame(rows, columns=header)
                        events_df = pl.from_pandas(pd_df)
                        logger.info("Успешно прочитан файл событий построчно")
                    except Exception as e:
                        logger.error(f"Ошибка при построчном чтении: {str(e)}")
                        raise ValueError(f"Не удалось прочитать файл событий: {str(e)}")
                
            elif uploaded_events_file.name.endswith(('.xls', '.xlsx')):
                logger.info("Загрузка Excel файла с данными событий")
                # Сохраняем временный файл для чтения
                with open("temp_events.xlsx", "wb") as f:
                    f.write(uploaded_events_file.getvalue())
                events_df = pl.read_excel("temp_events.xlsx")
            
            # Преобразуем даты в формат datetime
            logger.info("Преобразование дат в формат datetime")
            if "date" in prod_df.columns:
                try:
                    prod_df = prod_df.with_columns(pl.col("date").str.to_date("%Y-%m-%d"))
                    logger.debug("Даты в данных добычи преобразованы успешно")
                except Exception as e:
                    logger.error(f"Ошибка при преобразовании дат в данных добычи: {str(e)}")
                    # Пробуем другой формат
                    try:
                        prod_df = prod_df.with_columns(pl.col("date").str.to_date("%d.%m.%Y"))
                        logger.debug("Даты в данных добычи преобразованы успешно с форматом %d.%m.%Y")
                    except Exception as e2:
                        logger.error(f"Ошибка при преобразовании дат в данных добычи (второй формат): {str(e2)}")
            
            if "event_date" in events_df.columns:
                try:
                    events_df = events_df.with_columns(pl.col("event_date").str.to_date("%Y-%m-%d"))
                    logger.debug("Даты в данных событий преобразованы успешно")
                except Exception as e:
                    logger.error(f"Ошибка при преобразовании дат в данных событий: {str(e)}")
                    # Пробуем другой формат
                    try:
                        events_df = events_df.with_columns(pl.col("event_date").str.to_date("%d.%m.%Y"))
                        logger.debug("Даты в данных событий преобразованы успешно с форматом %d.%m.%Y")
                    except Exception as e2:
                        logger.error(f"Ошибка при преобразовании дат в данных событий (второй формат): {str(e2)}")
            
            logger.info(f"Успешно загружены пользовательские данные")
            logger.info(f"- Данные добычи: {len(prod_df)} записей")
            logger.info(f"- Данные событий: {len(events_df)} записей")
            logger.debug(f"Колонки в данных добычи: {prod_df.columns}")
            logger.debug(f"Колонки в данных событий: {events_df.columns}")
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке данных: {str(e)}")
            # В случае ошибки загружаем тестовые данные
            logger.info("Загрузка тестовых данных из-за ошибки")
            if os.path.exists("test_data/prod_data.csv") and os.path.exists("test_data/events_data.csv"):
                logger.info("Найдены тестовые данные в директории test_data")
                
                # Загрузка тестовых данных добычи
                logger.info("Загрузка тестовых данных добычи")
                encodings = ["utf-8", "cp1251", "latin1", "windows-1251", "ascii", "iso-8859-1"]
                prod_df = None
                
                for encoding in encodings:
                    try:
                        logger.debug(f"Пробуем кодировку {encoding} для тестовых данных добычи")
                        prod_df = pl.read_csv("test_data/prod_data.csv", encoding=encoding)
                        logger.info(f"Успешно загружены тестовые данные добычи с кодировкой {encoding}")
                        break
                    except Exception as e:
                        logger.warning(f"Ошибка при чтении тестовых данных добычи с кодировкой {encoding}: {str(e)}")
                
                if prod_df is None:
                    logger.error("Не удалось прочитать тестовые данные добычи")
                    raise ValueError("Не удалось прочитать тестовые данные добычи")
                
                # Загрузка тестовых данных событий
                logger.info("Загрузка тестовых данных событий")
                encodings = ["utf-8", "cp1251", "latin1", "windows-1251", "ascii", "iso-8859-1"]
                events_df = None
                
                for encoding in encodings:
                    try:
                        logger.debug(f"Пробуем кодировку {encoding} для тестовых данных событий")
                        events_df = pl.read_csv("test_data/events_data.csv", encoding=encoding)
                        logger.info(f"Успешно загружены тестовые данные событий с кодировкой {encoding}")
                        break
                    except Exception as e:
                        logger.warning(f"Ошибка при чтении тестовых данных событий с кодировкой {encoding}: {str(e)}")
                
                if events_df is None:
                    logger.error("Не удалось прочитать тестовые данные событий")
                    raise ValueError("Не удалось прочитать тестовые данные событий")
                
                # Преобразуем даты в формат datetime
                logger.info("Преобразование дат в тестовых данных")
                try:
                    prod_df = prod_df.with_columns(pl.col("date").str.to_date("%Y-%m-%d"))
                    events_df = events_df.with_columns(pl.col("event_date").str.to_date("%Y-%m-%d"))
                    logger.debug("Даты в тестовых данных преобразованы успешно")
                except Exception as e:
                    logger.error(f"Ошибка при преобразовании дат в тестовых данных: {str(e)}")
                
                logger.info(f"Загружены тестовые данные из директории test_data")
                logger.info(f"- Данные добычи: {len(prod_df)} записей")
                logger.info(f"- Данные событий: {len(events_df)} записей")
            else:
                # Импортируем функцию генерации данных и создаем тестовые данные
                logger.info("Генерация новых тестовых данных")
                from sample_data import save_sample_data
                prod_df, events_df = save_sample_data(num_wells=50, format="csv")
                logger.info(f"Сгенерированы новые тестовые данные")
                logger.info(f"- Данные добычи: {len(prod_df)} записей")
                logger.info(f"- Данные событий: {len(events_df)} записей")
    else:
        logger.info("Файлы не предоставлены, проверка наличия тестовых данных")
        # Проверяем, есть ли уже сгенерированные файлы
        if os.path.exists("test_data/prod_data.csv") and os.path.exists("test_data/events_data.csv"):
            logger.info("Найдены тестовые данные в директории test_data")
            
            # Загрузка тестовых данных добычи
            logger.info("Загрузка тестовых данных добычи")
            encodings = ["utf-8", "cp1251", "latin1", "windows-1251", "ascii", "iso-8859-1"]
            prod_df = None
            
            for encoding in encodings:
                try:
                    logger.debug(f"Пробуем кодировку {encoding} для тестовых данных добычи")
                    prod_df = pl.read_csv("test_data/prod_data.csv", encoding=encoding)
                    logger.info(f"Успешно загружены тестовые данные добычи с кодировкой {encoding}")
                    break
                except Exception as e:
                    logger.warning(f"Ошибка при чтении тестовых данных добычи с кодировкой {encoding}: {str(e)}")
            
            if prod_df is None:
                logger.error("Не удалось прочитать тестовые данные добычи")
                raise ValueError("Не удалось прочитать тестовые данные добычи")
            
            # Загрузка тестовых данных событий
            logger.info("Загрузка тестовых данных событий")
            encodings = ["utf-8", "cp1251", "latin1", "windows-1251", "ascii", "iso-8859-1"]
            events_df = None
            
            for encoding in encodings:
                try:
                    logger.debug(f"Пробуем кодировку {encoding} для тестовых данных событий")
                    events_df = pl.read_csv("test_data/events_data.csv", encoding=encoding)
                    logger.info(f"Успешно загружены тестовые данные событий с кодировкой {encoding}")
                    break
                except Exception as e:
                    logger.warning(f"Ошибка при чтении тестовых данных событий с кодировкой {encoding}: {str(e)}")
            
            if events_df is None:
                logger.error("Не удалось прочитать тестовые данные событий")
                raise ValueError("Не удалось прочитать тестовые данные событий")
            
            # Преобразуем даты в формат datetime
            logger.info("Преобразование дат в тестовых данных")
            try:
                prod_df = prod_df.with_columns(pl.col("date").str.to_date("%Y-%m-%d"))
                events_df = events_df.with_columns(pl.col("event_date").str.to_date("%Y-%m-%d"))
                logger.debug("Даты в тестовых данных преобразованы успешно")
            except Exception as e:
                logger.error(f"Ошибка при преобразовании дат в тестовых данных: {str(e)}")
            
            logger.info(f"Загружены тестовые данные из директории test_data")
            logger.info(f"- Данные добычи: {len(prod_df)} записей")
            logger.info(f"- Данные событий: {len(events_df)} записей")
        else:
            # Импортируем функцию генерации данных и создаем тестовые данные
            logger.info("Генерация новых тестовых данных")
            from sample_data import save_sample_data
            prod_df, events_df = save_sample_data(num_wells=50, format="csv")
            logger.info(f"Сгенерированы новые тестовые данные")
            logger.info(f"- Данные добычи: {len(prod_df)} записей")
            logger.info(f"- Данные событий: {len(events_df)} записей")
    
    # Проверяем наличие обязательных колонок
    logger.info("Проверка наличия обязательных колонок")
    required_prod_columns = ["date", "uwi", "horizon", "oil_rate"]
    required_events_columns = ["uwi", "event_date", "event_type"]
    
    missing_prod_columns = [col for col in required_prod_columns if col not in prod_df.columns]
    missing_events_columns = [col for col in required_events_columns if col not in events_df.columns]
    
    if missing_prod_columns:
        logger.error(f"Отсутствуют обязательные колонки в данных добычи: {missing_prod_columns}")
        raise ValueError(f"Отсутствуют обязательные колонки в данных добычи: {missing_prod_columns}")
    
    if missing_events_columns:
        logger.error(f"Отсутствуют обязательные колонки в данных событий: {missing_events_columns}")
        raise ValueError(f"Отсутствуют обязательные колонки в данных событий: {missing_events_columns}")
    
    logger.info("Данные успешно загружены и проверены")
    return prod_df, events_df

def calculate_decline_rate(
    prod_df: pl.DataFrame,
    events_df: pl.DataFrame,
    start_date: datetime.date, 
    end_date: datetime.date, 
    group_by_cols: list[str] | str = "horizon", 
    rate_col: str = "oil_rate", 
    exclude_wells_with_events: bool = False, 
    min_rate: float = 0.0, 
    include_inactive: bool = False
):
    """
    Рассчитывает темп падения переходящего фонда скважин
    
    Args:
        prod_df: DataFrame с данными добычи
        events_df: DataFrame с данными событий
        start_date: Начальная дата периода (базовый период)
        end_date: Конечная дата периода
        group_by_cols: Колонки для группировки (разрезы анализа), может быть строкой или списком
        rate_col: Колонка с дебитом для расчета
        exclude_wells_with_events: Исключать ли скважины с событиями
        min_rate: Минимальный дебит для учета скважины
        include_inactive: Включать ли неактивные скважины в расчет
        
    Returns:
        DataFrame: Результаты расчета темпа падения
    """
    logger.info(f"Расчет темпа падения для периода {start_date} - {end_date}")
    logger.debug(f"Параметры: group_by_cols={group_by_cols}, rate_col={rate_col}, exclude_wells_with_events={exclude_wells_with_events}")
    
    # Исправление: если group_by_cols список из одного списка, взять внутренний
    if isinstance(group_by_cols, list) and len(group_by_cols) == 1 and isinstance(group_by_cols[0], list):
        group_by_cols = group_by_cols[0]
    # Преобразуем group_by_cols в список, если передана строка
    if isinstance(group_by_cols, str):
        group_by_cols = [group_by_cols]
    logger.debug(f"Используемые group_by_cols: {group_by_cols} (type: {type(group_by_cols)})")
    logger.debug(f"rate_col: {rate_col} (type: {type(rate_col)})")
    
    # Проверяем, что DataFrame не пустые
    if prod_df is None or len(prod_df) == 0:
        logger.error("Ошибка: пустой DataFrame с данными добычи")
        return pl.DataFrame()
    
    if events_df is None:
        logger.warning("Предупреждение: пустой DataFrame с данными событий")
        events_df = pl.DataFrame()
    
    # Проверяем наличие необходимых колонок
    required_cols = ["date"] + group_by_cols + [rate_col]
    if "uwi" in prod_df.columns:
        well_id_col = "uwi"
    elif "well_id" in prod_df.columns:
        well_id_col = "well_id"
    else:
        logger.error("Ошибка: не найдена колонка с идентификатором скважины (uwi или well_id)")
        return pl.DataFrame()
    
    required_cols.append(well_id_col)
    
    missing_cols = [col for col in required_cols if col not in prod_df.columns]
    if missing_cols:
        logger.error(f"Ошибка: отсутствуют необходимые колонки: {missing_cols}")
        return pl.DataFrame()
    
    # Конвертируем даты в строковый формат, если они переданы как datetime
    if isinstance(start_date, datetime):
        start_date = start_date.strftime("%Y-%m-%d")
    if isinstance(end_date, datetime):
        end_date = end_date.strftime("%Y-%m-%d")
    
    # Фильтрация по датам
    logger.debug(f"Фильтрация данных по датам: {start_date} - {end_date}")
    try:
        # Преобразуем даты в строки для фильтрации
        if isinstance(start_date, (datetime, date)):
            start_date_str = start_date.strftime("%Y-%m-%d")
        else:
            start_date_str = str(start_date)
        
        if isinstance(end_date, (datetime, date)):
            end_date_str = end_date.strftime("%Y-%m-%d")
        else:
            end_date_str = str(end_date)
            
        # Преобразуем колонку date в строку для сравнения
        filtered_df = prod_df.with_columns(
            pl.col("date").cast(pl.Utf8).alias("date_str")
        ).filter(
            (pl.col("date_str") >= start_date_str) & 
            (pl.col("date_str") <= end_date_str)
        ).drop("date_str")
        
        logger.debug(f"После фильтрации по датам: {len(filtered_df)} записей")
    except Exception as e:
        logger.error(f"Ошибка при фильтрации по датам: {str(e)}")
        return pl.DataFrame()
    
    # Проверяем, что после фильтрации остались данные
    if len(filtered_df) == 0:
        logger.warning(f"Предупреждение: нет данных в указанном диапазоне дат {start_date} - {end_date}")
        return pl.DataFrame()
    
    # Фильтрация по минимальному дебиту
    if min_rate > 0:
        logger.debug(f"Фильтрация по минимальному дебиту: {min_rate}")
        logger.debug(f"  rate_col name: '{rate_col}', type in df: {filtered_df[rate_col].dtype}")
        logger.debug(f"  min_rate value: {min_rate}, type: {type(min_rate)}")
        try:
            # Явно преобразуем min_rate в float и используем pl.lit() для создания литерала
            min_rate_float = float(min_rate)
            filtered_df = filtered_df.filter(pl.col(rate_col) >= pl.lit(min_rate_float))
            logger.debug(f"После фильтрации по минимальному дебиту: {len(filtered_df)} записей")
            logger.debug(f"Filtering wells active in the first month with rate >= {min_rate}...")
        except Exception as e:
            logger.error(f"Ошибка при фильтрации по минимальному дебиту: {str(e)}")
            return pl.DataFrame()
    
    # Фильтрация по событиям
    if exclude_wells_with_events and len(events_df) > 0:
        logger.debug("Фильтрация скважин с событиями")
        try:
            # Получаем список скважин с событиями в указанном периоде
            events_in_period = events_df.filter(
                (pl.col("event_date") >= start_date) & 
                (pl.col("event_date") <= end_date)
            )
            
            if len(events_in_period) > 0:
                event_wells = set(events_in_period[well_id_col].unique().to_list())
                logger.debug(f"Скважины с событиями в периоде: {len(event_wells)}")
                
                # Фильтруем скважины без событий
                filtered_df = filtered_df.filter(~pl.col(well_id_col).is_in(event_wells))
                logger.debug(f"После фильтрации скважин с событиями: {len(filtered_df)} записей")
        except Exception as e:
            logger.error(f"Ошибка при фильтрации скважин с событиями: {str(e)}")
            # Продолжаем без фильтрации по событиям
    
    # Проверяем, что после фильтрации остались данные
    if len(filtered_df) == 0:
        logger.warning("Предупреждение: после фильтрации не осталось данных")
        return pl.DataFrame()
    
    # Проверка наличия нужных колонок перед агрегацией
    logger.debug(f"Колонки в filtered_df перед агрегацией: {filtered_df.columns}")
    logger.debug(f"Типы колонок: {[ (col, filtered_df[col].dtype) for col in filtered_df.columns ]}")
    if rate_col not in filtered_df.columns:
        logger.error(f"Ошибка: колонка rate_col '{rate_col}' отсутствует в filtered_df")
        return pl.DataFrame()
    if well_id_col not in filtered_df.columns:
        logger.error(f"Ошибка: колонка well_id_col '{well_id_col}' отсутствует в filtered_df")
        return pl.DataFrame()
    
    # Диагностика: пробуем каждую агрегацию отдельно
    try:
        sum_rate = filtered_df.group_by(["date"] + group_by_cols).agg([
            pl.sum(rate_col).alias(f"sum_{rate_col}")
        ])
        logger.debug(f"Агрегация sum_{rate_col} успешна, shape: {sum_rate.shape}")
    except Exception as e:
        logger.error(f"Ошибка при агрегации sum_{rate_col}: {str(e)}")
    try:
        count_well = filtered_df.group_by(["date"] + group_by_cols).agg([
            pl.count(well_id_col).alias("well_count")
        ])
        logger.debug(f"Агрегация well_count успешна, shape: {count_well.shape}")
    except Exception as e:
        logger.error(f"Ошибка при агрегации well_count: {str(e)}")
    
    # Группировка данных
    logger.debug(f"Группировка данных по: date, {group_by_cols}")
    try:
        grouped = filtered_df.group_by(["date"] + group_by_cols)
        agg = grouped.agg([
            pl.sum(rate_col).alias(f"sum_{rate_col}"),
            pl.count(well_id_col).alias("well_count")
        ])
        logger.debug(f"После группировки: {len(agg)} записей")
    except Exception as e:
        logger.error(f"Ошибка при группировке данных: {str(e)}")
        return pl.DataFrame()
    
    # Проверяем типы данных в agg
    logger.debug("Проверка типов данных в agg")
    for col in agg.columns:
        logger.debug(f"Колонка {col}: {type(agg[col])}")
    
    # Получаем уникальные даты и проверяем, что их как минимум две
    unique_dates = agg["date"].unique().sort()
    logger.debug(f"Уникальные даты: {unique_dates}")
    
    if len(unique_dates) < 2:
        logger.warning("Предупреждение: недостаточно дат для расчета темпа падения (нужно минимум 2)")
        return pl.DataFrame()
    
    # Определяем даты для расчета темпа падения (первая и последняя)
    t0 = unique_dates[0]
    t1 = unique_dates[-1]
    logger.debug(f"Даты для расчета: t0={t0}, t1={t1}")
    
    # Создаем сводную таблицу
    logger.debug("Создание сводной таблицы")
    try:
        pivoted = (agg
                  .pivot(values=[f"sum_{rate_col}", "well_count"], 
                         index=group_by_cols,
                         columns="date"))
        logger.debug(f"Колонки после pivot: {pivoted.columns}")
        # Переименуем колонки для совместимости с расчетом
        new_columns = []
        for col in pivoted.columns:
            if col.startswith(f"sum_{rate_col}_date_"):
                new_columns.append(col.replace(f"sum_{rate_col}_date_", f"{rate_col}_"))
            elif col.startswith("well_count_date_"):
                new_columns.append(col.replace("well_count_date_", "well_count_"))
            else:
                new_columns.append(col)
        pivoted.columns = new_columns
        logger.debug(f"Колонки после переименования: {pivoted.columns}")
    except Exception as e:
        logger.error(f"Ошибка при pivot: {str(e)}")
        return pl.DataFrame()
    
    # Переименовываем колонки для удобства
    logger.debug("Переименование колонок")
    try:
        new_cols = {}
        for col in pivoted.columns:
            if isinstance(col, tuple) and len(col) == 2:
                metric, date_val = col
                if metric == f"sum_{rate_col}":
                    new_cols[col] = f"{rate_col}_{date_val}"
                elif metric == "well_count":
                    new_cols[col] = f"wells_{date_val}"
        
        logger.debug(f"Переименование колонок: {new_cols}")
        pivoted = pivoted.rename(new_cols)
        logger.debug(f"Колонки после переименования: {pivoted.columns}")
    except Exception as e:
        logger.error(f"Ошибка при переименовании колонок: {str(e)}")
        return pl.DataFrame()
    
    # Получаем имена колонок для расчета
    rate_t0_col = f"{rate_col}_{t0}"
    rate_t1_col = f"{rate_col}_{t1}"
    wells_t0_col = f"wells_{t0}"
    wells_t1_col = f"wells_{t1}"
    
    logger.debug(f"Колонки для расчета: {rate_t0_col}, {rate_t1_col}")
    
    # Проверяем, что все необходимые колонки существуют
    if rate_t0_col not in pivoted.columns or rate_t1_col not in pivoted.columns:
        # Если колонок нет, возвращаем пустой DataFrame
        logger.error(f"Ошибка: не найдены колонки {rate_t0_col} или {rate_t1_col} в результатах pivot")
        logger.error(f"Доступные колонки: {pivoted.columns}")
        # Создаем пустой DataFrame с нужными колонками для совместимости
        empty_df = pl.DataFrame(schema={
            "horizon": pl.Utf8,
            "decline_rate": pl.Float64,
            "decline_percent": pl.Float64,
            "absolute_decline": pl.Float64,
            rate_t0_col: pl.Float64,
            rate_t1_col: pl.Float64
        })
        return empty_df
    
    # Рассчитываем темп падения
    logger.debug("Расчет темпа падения")
    try:
        # Проверяем наличие нулевых значений
        zero_values = pivoted.filter(pl.col(rate_t0_col) == 0).height
        if zero_values > 0:
            logger.warning(f"Обнаружено {zero_values} строк с нулевыми значениями в колонке {rate_t0_col}")
            # Заменяем нули на очень малое значение
            pivoted = pivoted.with_columns(
                pl.when(pl.col(rate_t0_col) == 0).then(0.0001).otherwise(pl.col(rate_t0_col)).alias(rate_t0_col)
            )
        
        result = (pivoted
                 .with_columns([
                     (1 - pl.col(rate_t1_col) / pl.col(rate_t0_col)).alias("decline_rate"),
                     ((1 - pl.col(rate_t1_col) / pl.col(rate_t0_col)) * pl.lit(100.0)).alias("decline_percent"),
                     (pl.col(rate_t0_col) - pl.col(rate_t1_col)).alias("absolute_decline")
                 ]))
        
        logger.debug(f"Рассчитан темп падения для {len(result)} групп")
    except Exception as e:
        logger.error(f"Ошибка при расчете темпа падения: {str(e)}")
        return pl.DataFrame()
    
    # Добавляем расчет изменения количества скважин, если колонки существуют
    if wells_t0_col in pivoted.columns and wells_t1_col in pivoted.columns:
        try:
            result = result.with_columns(
                ((pl.col(wells_t0_col) - pl.col(wells_t1_col)) / pl.col(wells_t0_col) * 100.0).alias("well_count_decline_percent")
            )
            logger.debug("Добавлен расчет изменения количества скважин")
        except Exception as e:
            logger.warning(f"Ошибка при расчете изменения количества скважин: {str(e)}")
    
    logger.info(f"Расчет темпа падения завершен успешно. Получено {len(result)} записей.")
    
    # Проверяем, что результат не пустой
    if len(result) == 0:
        logger.warning("Результат расчета темпа падения - пустой DataFrame")
        # Создаем пустой DataFrame с нужными колонками для совместимости
        empty_df = pl.DataFrame(schema={
            "horizon": pl.Utf8,
            "decline_rate": pl.Float64,
            "decline_percent": pl.Float64,
            "absolute_decline": pl.Float64,
            rate_t0_col: pl.Float64,
            rate_t1_col: pl.Float64
        })
        return empty_df
    
    # Убеждаемся, что результат - это Polars DataFrame
    if not isinstance(result, pl.DataFrame):
        logger.warning(f"Результат расчета не является Polars DataFrame: {type(result)}")
        try:
            result = pl.DataFrame(result)
            logger.info("Результат успешно преобразован в Polars DataFrame")
        except Exception as e:
            logger.error(f"Ошибка при преобразовании результата в Polars DataFrame: {str(e)}")
            # Создаем пустой DataFrame с нужными колонками для совместимости
            empty_df = pl.DataFrame(schema={
                "horizon": pl.Utf8,
                "decline_rate": pl.Float64,
                "decline_percent": pl.Float64,
                "absolute_decline": pl.Float64,
                rate_t0_col: pl.Float64,
                rate_t1_col: pl.Float64
            })
            return empty_df
    
    return result

def calculate_monthly_decline(prod_df, events_df, start_date, end_date, window_size, group_by_cols, rate_col, include_events=False):
    """
    Рассчитывает ежемесячный темп падения для скользящего окна
    
    Args:
        prod_df: DataFrame с данными добычи
        events_df: DataFrame с данными событий
        start_date: Начальная дата анализа
        end_date: Конечная дата анализа
        window_size: Размер окна в месяцах
        group_by_cols: Колонки для группировки
        rate_col: Колонка с дебитом для расчета
        include_events: Включать ли скважины с событиями
        
    Returns:
        DataFrame с динамикой темпа падения
    """
    logger.info(f"Расчет ежемесячного темпа падения для периода {start_date} - {end_date}")
    
    # Проверяем, что даты в формате datetime.date
    if not isinstance(start_date, date):
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        except:
            logger.error(f"Неверный формат начальной даты: {start_date}")
            return pl.DataFrame()
    
    if not isinstance(end_date, date):
        try:
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except:
            logger.error(f"Неверный формат конечной даты: {end_date}")
            return pl.DataFrame()
    
    # Генерируем список дат для скользящего окна
    date_pairs = []
    current_date = start_date
    
    while current_date <= end_date:
        # Вычисляем конец периода (текущая дата + window_size месяцев)
        end_period = date(current_date.year, current_date.month, 1)
        for _ in range(window_size):
            month = end_period.month + 1
            year = end_period.year
            if month > 12:
                month = 1
                year += 1
            end_period = date(year, month, 1)
        
        # Если конец периода не превышает конечную дату анализа, добавляем пару дат
        if end_period <= end_date:
            date_pairs.append((current_date, end_period))
        
        # Переходим к следующему месяцу
        month = current_date.month + 1
        year = current_date.year
        if month > 12:
            month = 1
            year += 1
        current_date = date(year, month, 1)
    
    # Если нет пар дат для анализа, возвращаем пустой DataFrame
    if not date_pairs:
        logger.warning(f"Нет пар дат для анализа в периоде {start_date} - {end_date}")
        return pl.DataFrame()
    
    # Рассчитываем темп падения для каждой пары дат
    results = []
    
    for t0, t1 in date_pairs:
        logger.info(f"Расчет темпа падения для периода {t0} - {t1}")
        
        # Рассчитываем темп падения для текущей пары дат
        decline_df = calculate_decline_rate(
            prod_df=prod_df,
            events_df=events_df,
            start_date=t0,
            end_date=t1,
            group_by_cols=group_by_cols,
            rate_col=rate_col,
            exclude_wells_with_events=not include_events,
            include_inactive=False
        )
        
        # Если получили результат, добавляем его в список
        if len(decline_df) > 0:
            # Оставляем только необходимые колонки для объединения
            # Сохраняем только колонки группировки, темп падения и процент падения
            keep_cols = group_by_cols + ["decline_rate", "decline_percent", "wells_count"]
            
            # Фильтруем колонки, оставляя только те, которые есть в DataFrame
            keep_cols = [col for col in keep_cols if col in decline_df.columns]
            
            # Добавляем колонки с датами периода
            t0_str = t0.strftime("%Y-%m-%d")
            t1_str = t1.strftime("%Y-%m-%d")
            
            decline_df = decline_df.select(keep_cols).with_columns([
                pl.lit(t0).alias("start_date"),
                pl.lit(t1).alias("end_date"),
                pl.lit(t1).alias("calculation_date")
            ])
            
            results.append(decline_df)
    
    # Объединяем результаты
    try:
        if results:
            final_df = pl.concat(results)
            logger.info(f"Расчет ежемесячного темпа падения завершен успешно. Получено {len(final_df)} записей.")
            return final_df
        else:
            logger.warning("Нет результатов для объединения")
            return pl.DataFrame()
    except Exception as e:
        logger.error(f"Ошибка при объединении результатов: {e}")
        return pl.DataFrame()

def plot_decline_rate(decline_df, group_col="horizon", rate_col="decline_percent", 
                     title="Темп падения по горизонтам"):
    """
    Создает график темпа падения
    
    Args:
        decline_df: DataFrame с расчетами темпа падения
        group_col: Колонка для группировки (ось X)
        rate_col: Колонка с темпом падения (ось Y)
        title: Заголовок графика
        
    Returns:
        plotly.graph_objects.Figure: Объект графика
    """
    # Преобразуем в pandas для удобства работы с plotly
    df = safe_to_pandas(decline_df)
    
    # Создаем график
    fig = px.bar(
        df, 
        x=group_col, 
        y=rate_col,
        title=title,
        labels={
            group_col: group_col.capitalize(),
            rate_col: "Темп падения, %"
        },
        text=df[rate_col].round(2)
    )
    
    # Настраиваем внешний вид
    fig.update_layout(
        xaxis_title=group_col.capitalize(),
        yaxis_title="Темп падения, %",
        yaxis=dict(ticksuffix="%"),
        showlegend=False
    )
    
    # Добавляем текстовые метки
    fig.update_traces(
        textposition='outside',
        texttemplate='%{y:.2f}%'
    )
    
    return fig

def plot_decline_trend(monthly_decline, group_col="horizon", rate_col="decline_percent", 
                      title="Динамика темпа падения"):
    """
    Создает график динамики темпа падения
    
    Args:
        monthly_decline: DataFrame с расчетами ежемесячного темпа падения
        group_col: Колонка для группировки (разные линии)
        rate_col: Колонка с темпом падения (ось Y)
        title: Заголовок графика
        
    Returns:
        plotly.graph_objects.Figure: Объект графика
    """
    # Преобразуем в pandas для удобства работы с plotly
    df = safe_to_pandas(monthly_decline)
    
    # Создаем график
    fig = go.Figure()
    
    # Добавляем линии для каждой группы
    for group in df[group_col].unique():
        group_df = df[df[group_col] == group]
        fig.add_trace(go.Scatter(
            x=group_df['calculation_date'],
            y=group_df[rate_col],
            mode='lines+markers',
            name=str(group),
            line=dict(width=2)
        ))
    
    # Настраиваем график
    fig.update_layout(
        title=title,
        xaxis_title="Дата",
        yaxis_title="Темп падения, %",
        yaxis=dict(ticksuffix="%"),
        legend_title=group_col.capitalize(),
        hovermode="closest"
    )
    
    return fig

def fit_decline_curve(prod_df, uwi, rate_col="oil_rate", date_col="date", min_rate=0.1, 
                     model_type="exponential", forecast_months=12):
    """
    Аппроксимирует кривую падения добычи по моделям Арпса
    
    Args:
        prod_df: DataFrame с данными добычи
        uwi: Идентификатор скважины
        rate_col: Колонка с дебитом
        date_col: Колонка с датой
        min_rate: Минимальный дебит для фильтрации
        model_type: Тип модели ('exponential', 'harmonic', 'hyperbolic')
        forecast_months: Количество месяцев для прогноза
        
    Returns:
        tuple: (fig, params, metrics) - график, параметры модели, метрики качества
    """
    logger.info(f"Аппроксимация кривой падения для скважины {uwi}")
    
    try:
        # Фильтруем данные по скважине
        well_data = prod_df.filter(pl.col("uwi") == uwi)
        
        if len(well_data) == 0:
            logger.warning(f"Нет данных для скважины {uwi}")
            return None, None, None
        
        # Фильтруем по минимальному дебиту
        well_data = well_data.filter(pl.col(rate_col) >= pl.lit(float(min_rate)))
        
        if len(well_data) < 3:
            logger.warning(f"Недостаточно точек для аппроксимации (минимум 3): {len(well_data)}")
            return None, None, None
        
        # Сортируем по дате
        well_data = well_data.sort(date_col)
        
        # Преобразуем в pandas для удобства работы с scipy
        df = safe_to_pandas(well_data)
        
        # Преобразуем даты в числовой формат (дни от начала)
        df['days'] = (pd.to_datetime(df[date_col]) - pd.to_datetime(df[date_col].min())).dt.days
        
        # Получаем данные для аппроксимации
        x_data = df['days'].values
        y_data = df[rate_col].values
        
        # Функции для моделей Арпса
        def exponential_decline(t, qi, di):
            """Экспоненциальная модель: q(t) = qi * exp(-di * t)"""
            return qi * np.exp(-di * t)
        
        def harmonic_decline(t, qi, di):
            """Гармоническая модель: q(t) = qi / (1 + di * t)"""
            return qi / (1 + di * t)
        
        def hyperbolic_decline(t, qi, di, b):
            """Гиперболическая модель: q(t) = qi / (1 + b * di * t)^(1/b)"""
            return qi / np.power(1 + b * di * t, 1/b)
        
        # Выбираем модель и начальные параметры
        if model_type == "exponential":
            model_func = exponential_decline
            p0 = [y_data[0], 0.1]  # Начальные значения параметров
            bounds = ([0, 0], [np.inf, 1])
        elif model_type == "harmonic":
            model_func = harmonic_decline
            p0 = [y_data[0], 0.1]
            bounds = ([0, 0], [np.inf, 1])
        elif model_type == "hyperbolic":
            model_func = hyperbolic_decline
            p0 = [y_data[0], 0.1, 0.5]
            bounds = ([0, 0, 0], [np.inf, 1, 2])
        else:
            logger.error(f"Неизвестный тип модели: {model_type}")
            return None, None, None
        
        # Аппроксимация кривой
        try:
            from scipy.optimize import curve_fit
            
            # Выполняем аппроксимацию
            params, covariance = curve_fit(model_func, x_data, y_data, p0=p0, bounds=bounds, maxfev=10000)
            
            # Рассчитываем предсказанные значения
            y_pred = model_func(x_data, *params)
            
            # Рассчитываем метрики качества без использования sklearn
            mse = np.mean((y_data - y_pred) ** 2)
            rmse = np.sqrt(mse)
            mae = np.mean(np.abs(y_data - y_pred))
            ss_total = np.sum((y_data - np.mean(y_data)) ** 2)
            ss_residual = np.sum((y_data - y_pred) ** 2)
            r2 = 1 - (ss_residual / ss_total)
            
            metrics = {
                "mse": mse,
                "rmse": rmse,
                "mae": mae,
                "r2": r2
            }
            
            # Создаем прогноз
            last_date = pd.to_datetime(df[date_col].max())
            forecast_days = np.arange(0, forecast_months * 30)
            forecast_dates = [last_date + pd.Timedelta(days=int(d)) for d in forecast_days]
            forecast_rates = model_func(x_data[-1] + forecast_days, *params)
            
            # Создаем график
            fig = go.Figure()
            
            # Добавляем фактические данные
            fig.add_trace(go.Scatter(
                x=pd.to_datetime(df[date_col]),
                y=df[rate_col],
                mode='markers',
                name='Фактические данные',
                marker=dict(size=8)
            ))
            
            # Добавляем аппроксимацию
            fig.add_trace(go.Scatter(
                x=pd.to_datetime(df[date_col]),
                y=y_pred,
                mode='lines',
                name='Аппроксимация',
                line=dict(width=2)
            ))
            
            # Добавляем прогноз
            fig.add_trace(go.Scatter(
                x=forecast_dates,
                y=forecast_rates,
                mode='lines',
                name='Прогноз',
                line=dict(dash='dash', width=2)
            ))
            
            # Настраиваем график
            model_names = {
                "exponential": "Экспоненциальная",
                "harmonic": "Гармоническая",
                "hyperbolic": "Гиперболическая"
            }
            
            # Форматируем параметры модели в зависимости от типа модели
            if model_type == "hyperbolic" and len(params) >= 3:
                model_params = f"qi = {params[0]:.2f}, di = {params[1]:.4f}, b = {params[2]:.4f}"
            else:
                model_params = f"qi = {params[0]:.2f}, di = {params[1]:.4f}"
            
            fig.update_layout(
                title=f"Аппроксимация добычи скважины {uwi}<br><sub>Модель: {model_names.get(model_type, model_type)}, {model_params}</sub>",
                xaxis_title="Дата",
                yaxis_title=f"Дебит ({rate_col})",
                legend_title="Данные",
                hovermode="closest"
            )
            
            # Добавляем аннотацию с метриками
            fig.add_annotation(
                xref="paper", yref="paper",
                x=0.02, y=0.98,
                text=f"R² = {r2:.4f}<br>RMSE = {rmse:.4f}",
                showarrow=False,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="black",
                borderwidth=1
            )
            
            # Возвращаем результаты
            return fig, params, metrics
            
        except Exception as e:
            logger.error(f"Ошибка при аппроксимации: {str(e)}")
            return None, None, None
            
    except Exception as e:
        logger.error(f"Ошибка при подготовке данных для аппроксимации: {str(e)}")
        return None, None, None

# Вспомогательная функция для безопасного преобразования Polars DataFrame в Pandas DataFrame
def safe_to_pandas(df):
    """
    Безопасно преобразует Polars DataFrame в Pandas DataFrame,
    обрабатывая случаи с пустыми DataFrame
    
    Args:
        df: Polars DataFrame для преобразования
        
    Returns:
        pandas.DataFrame: Преобразованный DataFrame или пустой DataFrame
    """
    try:
        if df is None or len(df) == 0:
            safe_log("warning", "Попытка преобразовать пустой DataFrame в pandas")
            # Создаем пустой pandas DataFrame с базовыми колонками
            return pd.DataFrame(columns=["horizon", "decline_rate", "decline_percent"])
        
        # Проверяем, что это действительно Polars DataFrame
        if not isinstance(df, pl.DataFrame):
            safe_log("warning", f"Объект не является Polars DataFrame: {type(df)}")
            if isinstance(df, pd.DataFrame):
                return df
            return pd.DataFrame(columns=["horizon", "decline_rate", "decline_percent"])
        
        # Преобразуем в pandas DataFrame
        return df.to_pandas()
    except Exception as e:
        safe_log("error", f"Ошибка при преобразовании DataFrame: {str(e)}")
        # Пытаемся создать pandas DataFrame из данных напрямую
        try:
            data = {col: df[col].to_list() for col in df.columns}
            return pd.DataFrame(data)
        except:
            # В случае ошибки возвращаем пустой DataFrame
            return pd.DataFrame(columns=["horizon", "decline_rate", "decline_percent"])

import streamlit as st

# Настройка страницы - должна быть первой командой Streamlit
st.set_page_config(
    page_title="Анализ темпа падения",
    page_icon="📉",
    layout="wide",
    initial_sidebar_state="expanded"
)

import polars as pl
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import numpy as np
from utils import (load_data, calculate_decline_rate, plot_decline_rate,
                  calculate_monthly_decline, plot_decline_trend, fit_decline_curve,
                  safe_to_pandas)
from logger import logger, safe_log
from st_aggrid import AgGrid, GridOptionsBuilder

# Добавляем стилизацию для улучшения интерфейса
st.markdown("""
<style>
    :root {
        --primary-color: #0D47A1;  /* Темно-синий */
        --secondary-color: #2E7D32;  /* Зеленый */
        --background-color: #F5F7FA;
        --text-color: #263238;
    }
    
    .main {
        background-color: var(--background-color);
    }
    
    h1, h2, h3 {
        color: var(--primary-color);
    }
    
    .stButton button {
        background-color: var(--primary-color);
        color: white;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        transition: all 0.3s;
    }
    
    .stButton button:hover {
        background-color: #1565C0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    
    /* Стиль для карточек с метриками */
    div[data-testid="metric-container"] {
        background-color: white;
        border-radius: 5px;
        padding: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Улучшение стиля селекторов */
    div[data-baseweb="select"] {
        border-radius: 4px;
    }
    
    /* Улучшение контрастности для дат */
    input[type="date"] {
        color: var(--text-color);
        background-color: white;
    }
    
    /* Стиль для вкладок */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 4px 4px 0 0;
        padding: 8px 16px;
        border: none;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: white;
        border-bottom: 2px solid var(--primary-color);
    }
</style>
""", unsafe_allow_html=True)

# Функция для безопасного преобразования Polars DataFrame в Pandas DataFrame
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

# Функция для отображения результатов в виде таблицы
def display_results_table(df, key=None):
    # Преобразуем в pandas DataFrame
    pandas_df = safe_to_pandas(df)
    
    # Форматируем числовые колонки
    for col in pandas_df.columns:
        if "decline_rate" in col and pandas_df[col].dtype in ['float64', 'float32']:
            pandas_df[col] = pandas_df[col].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "")
        elif "decline_percent" in col and pandas_df[col].dtype in ['float64', 'float32']:
            pandas_df[col] = pandas_df[col].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "")
    
    # Отображаем таблицу с улучшенным форматированием
    return st.dataframe(
        pandas_df,
        use_container_width=True,
        height=400,
        hide_index=True
    )

# Заголовок приложения
st.title("Анализ темпа падения переходящего фонда скважин")

# Создаем вкладки с иконками
tab1, tab2, tab3, tab4 = st.tabs([
    "⚙️ Настройки", 
    "📊 Расчет темпа падения", 
    "📈 Динамика темпа падения", 
    "🔍 Анализ по скважинам"
])

# Вкладка настроек
with tab1:
    st.header("Настройки")
    
    # Загрузка данных
    st.subheader("Загрузка данных")
    
    # Опция использования тестовых данных
    use_test_data = st.checkbox("Использовать тестовые данные", value=True)
    
    if use_test_data:
        # Загрузка тестовых данных
        if "prod_df" not in st.session_state or "events_df" not in st.session_state:
            with st.spinner("Загрузка тестовых данных..."):
                st.session_state.prod_df, st.session_state.events_df = load_data()
                
                # Отображаем информацию о данных
                st.success(f"Загружены тестовые данные: {len(st.session_state.prod_df)} записей добычи, {len(st.session_state.events_df)} записей событий")
                
                # Метрики данных
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Количество скважин", len(st.session_state.prod_df["uwi"].unique()))
                with col2:
                    st.metric("Период данных", f"{st.session_state.prod_df['date'].min()} - {st.session_state.prod_df['date'].max()}")
                with col3:
                    st.metric("Количество месторождений", len(st.session_state.prod_df["field"].unique()))
        else:
            # Отображаем информацию о данных
            st.success(f"Загружены тестовые данные: {len(st.session_state.prod_df)} записей добычи, {len(st.session_state.events_df)} записей событий")
            
            # Метрики данных
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Количество скважин", len(st.session_state.prod_df["uwi"].unique()))
            with col2:
                st.metric("Период данных", f"{st.session_state.prod_df['date'].min()} - {st.session_state.prod_df['date'].max()}")
            with col3:
                st.metric("Количество месторождений", len(st.session_state.prod_df["field"].unique()))
    else:
        # Загрузка пользовательских данных
        st.write("Загрузите файлы с данными добычи и событий:")
        
        uploaded_prod_file = st.file_uploader("Файл с данными добычи (CSV или Parquet)", type=["csv", "parquet"])
        uploaded_events_file = st.file_uploader("Файл с данными событий (CSV или Parquet)", type=["csv", "parquet"])
        
        if uploaded_prod_file is not None and uploaded_events_file is not None:
            # Загрузка пользовательских данных
            with st.spinner("Загрузка данных..."):
                st.session_state.prod_df, st.session_state.events_df = load_data(uploaded_prod_file, uploaded_events_file)
                
                # Отображаем информацию о данных
                st.success(f"Загружены пользовательские данные: {len(st.session_state.prod_df)} записей добычи, {len(st.session_state.events_df)} записей событий")
                
                # Метрики данных
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Количество скважин", len(st.session_state.prod_df["uwi"].unique()))
                with col2:
                    st.metric("Период данных", f"{st.session_state.prod_df['date'].min()} - {st.session_state.prod_df['date'].max()}")
                with col3:
                    st.metric("Количество месторождений", len(st.session_state.prod_df["field"].unique()))

# Вкладка 2: Расчет темпа падения
with tab2:
    st.header("Расчет темпа падения")
    
    # Настройки расчета
    col1, col2, col3 = st.columns(3)
    
    with col1:
        t0 = st.date_input(
            "Начальная дата (t₀)",
            value=datetime(2024, 1, 1),
            min_value=datetime(2024, 1, 1),
            max_value=datetime(2024, 12, 31)
        )
    
    with col2:
        t1 = st.date_input(
            "Конечная дата (t₁)",
            value=datetime(2024, 12, 1),
            min_value=datetime(2024, 1, 1),
            max_value=datetime(2024, 12, 31)
        )
    
    with col3:
        rate_col = st.selectbox(
            "Параметр для расчета",
            options=["oil_rate", "liquid_rate", "gas_rate"],
            format_func=lambda x: {
                "oil_rate": "Дебит нефти",
                "liquid_rate": "Дебит жидкости",
                "gas_rate": "Дебит газа"
            }.get(x, x)
        )
    
    # Дополнительные настройки
    col1, col2 = st.columns(2)
    
    with col1:
        group_by_cols = st.selectbox(
            "Группировать по",
            options=["horizon", "field"],
            index=0
        )
        
        exclude_events = st.checkbox("Исключать скважины с событиями", value=False)
    
    with col2:
        min_production = st.number_input(
            f"Минимальный дебит для учета скважины ({rate_col})",
            value=0.1,
            min_value=0.0,
            step=0.1
        )
        
        include_inactive = st.checkbox("Включать неактивные скважины", value=False)
    
    # Кнопка для расчета
    if st.button("Рассчитать темп падения"):
        with st.spinner("Выполняется расчет..."):
            safe_log("info", "Начат расчет темпа падения")
            
            # --- НАЧАЛО ДИАГНОСТИКИ ПЕРЕД ВЫЗОВОМ ---
            try:
                actual_rate_col = rate_col # Получаем реальное имя колонки
                safe_log("debug", f"Arguments before calling calculate_decline_rate:")
                safe_log("debug", f"  prod_df type: {type(st.session_state.prod_df)}, shape: {st.session_state.prod_df.shape if st.session_state.prod_df is not None else 'None'}")
                safe_log("debug", f"  events_df type: {type(st.session_state.events_df)}, shape: {st.session_state.events_df.shape if st.session_state.events_df is not None else 'None'}")
                safe_log("debug", f"  start_date: {t0} ({type(t0)})") # Правильное имя переменной
                safe_log("debug", f"  end_date: {t1} ({type(t1)})") # Правильное имя переменной
                safe_log("debug", f"  group_by: {group_by_cols} ({type(group_by_cols)})") # Правильное имя переменной
                safe_log("debug", f"  rate_col: {actual_rate_col} ({type(actual_rate_col)})") # Правильное имя переменной
                safe_log("debug", f"  min_rate: {min_production} ({type(min_production)})") # Правильное имя переменной
                safe_log("debug", f"  exclude_events: {exclude_events} ({type(exclude_events)})")
                safe_log("debug", f"  include_inactive: {include_inactive} ({type(include_inactive)})")
            except Exception as log_e:
                 safe_log("error", f"Error logging arguments before call: {log_e}")
            # --- КОНЕЦ ДИАГНОСТИКИ ПЕРЕД ВЫЗОВОМ ---
            
            # Рассчитываем темп падения
            try:
                decline_df = calculate_decline_rate(
                    st.session_state.prod_df,
                    st.session_state.events_df,
                    start_date=t0,
                    end_date=t1,
                    group_by_cols=group_by_cols,
                    rate_col=rate_col,
                    min_rate=min_production,
                    exclude_wells_with_events=exclude_events,
                    include_inactive=include_inactive
                )
            except Exception as e:
                safe_log("error", f"Ошибка при расчете темпа падения: {e}")
                import traceback
                print("--- TRACEBACK START ---") 
                print(traceback.format_exc())
                print("--- TRACEBACK END ---")
                st.error(f"Произошла ошибка при расчете: {e}")
                st.session_state.decline_df = None
            else:
                # Сохраняем результаты в session_state
                st.session_state.decline_df = decline_df
                
                # Отображаем результаты
                st.subheader("Результаты расчета")
                
                # Проверяем, что DataFrame не пустой
                if decline_df is not None and len(decline_df) > 0:
                    try:
                        # Отображаем таблицу с результатами
                        display_results_table(decline_df, key="decline_df")
                        
                        # Создаем график
                        fig = plot_decline_rate(
                            decline_df,
                            group_col=group_by_cols,
                            rate_col="decline_percent",
                            title=f"Темп падения {rate_col} по {group_by_cols}"
                        )
                        
                        # Улучшаем график
                        fig.update_layout(
                            height=500,
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(family="Arial", size=14),
                            margin=dict(l=20, r=20, t=60, b=20),
                            hovermode="x unified"
                        )
                        
                        # Добавляем подписи значений
                        for i, bar in enumerate(fig.data):
                            y_values = bar.y
                            x_values = bar.x
                            for j, (x, y) in enumerate(zip(x_values, y_values)):
                                fig.add_annotation(
                                    x=x,
                                    y=y,
                                    text=f"{y:.2f}%",
                                    showarrow=False,
                                    yshift=10,
                                    font=dict(color="black", size=12)
                                )
                        
                        # Отображаем график
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Добавляем описание результатов
                        avg_decline = decline_df["decline_percent"].mean()
                        max_decline = decline_df["decline_percent"].max()
                        min_decline = decline_df["decline_percent"].min()
                        
                        st.markdown(f"""
                        ### Анализ результатов:
                        
                        - **Средний темп падения:** {avg_decline:.2f}%
                        - **Максимальный темп падения:** {max_decline:.2f}%
                        - **Минимальный темп падения:** {min_decline:.2f}%
                        
                        Период анализа: с {t0.strftime('%d.%m.%Y')} по {t1.strftime('%d.%m.%Y')}
                        """)
                        safe_log("info", "Расчет темпа падения завершен")
                    except Exception as e:
                        safe_log("error", f"Ошибка при отображении результатов: {str(e)}")
                        st.error(f"Ошибка при отображении результатов: {str(e)}")
                        st.code(str(decline_df), language="python")
                else:
                    safe_log("warning", "Расчет темпа падения вернул пустой результат")
                    st.warning("Расчет темпа падения не дал результатов. Возможные причины:\n"
                              "- Недостаточно данных для указанного периода\n"
                              "- Нет скважин, удовлетворяющих условиям фильтрации\n"
                              "- Все скважины имеют события в указанный период (если включена опция исключения скважин с событиями)")

# Вкладка 3: Динамика темпа падения
with tab3:
    st.header("Динамика темпа падения")
    
    # Настройки расчета
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start_date = st.date_input(
            "Начальная дата анализа",
            value=datetime(2024, 1, 1),
            min_value=datetime(2024, 1, 1),
            max_value=datetime(2024, 12, 31)
        )
    
    with col2:
        end_date = st.date_input(
            "Конечная дата анализа",
            value=datetime(2024, 12, 31),
            min_value=datetime(2024, 1, 1),
            max_value=datetime(2024, 12, 31)
        )
    
    with col3:
        window_size = st.slider(
            "Размер окна (месяцев)",
            min_value=1,
            max_value=12,
            value=3
        )
    
    # Дополнительные настройки
    col1, col2 = st.columns(2)
    
    with col1:
        trend_group_by_cols = st.selectbox(
            "Группировать по",
            options=["horizon", "field"],
            index=0,
            key="trend_group_by" # Добавлен уникальный ключ
        )
        
        trend_rate_col = st.selectbox(
            "Параметр для расчета",
            options=["oil_rate", "liquid_rate", "gas_rate"],
            format_func=lambda x: {
                "oil_rate": "Дебит нефти",
                "liquid_rate": "Дебит жидкости",
                "gas_rate": "Дебит газа"
            }.get(x, x),
            key="trend_rate_col" # Добавлен уникальный ключ
        )
    
    with col2:
        trend_exclude_events = st.checkbox(
            "Исключать скважины с событиями", 
            value=False,
            key="trend_exclude_events" # Добавлен уникальный ключ
        )
    
    # Кнопка для расчета
    if st.button("Рассчитать динамику темпа падения"):
        with st.spinner("Выполняется расчет..."):
            safe_log("info", "Начат расчет динамики темпа падения")
            # Рассчитываем ежемесячный темп падения
            monthly_decline = calculate_monthly_decline(
                st.session_state.prod_df,
                st.session_state.events_df,
                start_date,
                end_date,
                window_size=window_size,
                group_by_cols=[trend_group_by_cols],
                rate_col=trend_rate_col,
                include_events=not trend_exclude_events
            )
            
            # Сохраняем результаты в session_state
            st.session_state.monthly_decline = monthly_decline
            
            # Отображаем результаты
            st.subheader("Результаты расчета")
            
            # Проверяем, что есть данные для отображения
            if monthly_decline is not None and len(monthly_decline) > 0:
                try:
                    # Отображаем таблицу с результатами
                    display_results_table(monthly_decline, key="monthly_decline")
                    
                    # Создаем график
                    fig = plot_decline_trend(
                        monthly_decline,
                        group_col=trend_group_by_cols,
                        rate_col="decline_percent",
                        title=f"Динамика темпа падения {trend_rate_col} по {trend_group_by_cols}"
                    )
                    
                    # Улучшаем график
                    fig.update_layout(
                        height=500,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(family="Arial", size=14),
                        margin=dict(l=20, r=20, t=60, b=20),
                        hovermode="x unified"
                    )
                    
                    # Добавляем подписи значений
                    for i, bar in enumerate(fig.data):
                        y_values = bar.y
                        x_values = bar.x
                        for j, (x, y) in enumerate(zip(x_values, y_values)):
                            fig.add_annotation(
                                x=x,
                                y=y,
                                text=f"{y:.2f}%",
                                showarrow=False,
                                yshift=10,
                                font=dict(color="black", size=12)
                            )
                    
                    # Отображаем график
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Добавляем описание результатов
                    st.markdown(f"""
                    ### Информация о расчете
                    
                    - **Метод расчета:** {{"oil_rate": "Дебит нефти", "liquid_rate": "Дебит жидкости", "gas_rate": "Дебит газа"}}[trend_rate_col]
                    - **Группировка по:** {trend_group_by_cols}
                    - **Исключение скважин с событиями:** {"Да" if trend_exclude_events else "Нет"}
                    - **Размер окна:** {window_size} месяцев
                    - **Период анализа:** с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}
                    """)
                    safe_log("info", "Расчет динамики темпа падения завершен успешно")
                except Exception as e:
                    safe_log("error", f"Ошибка при отображении результатов динамики: {str(e)}")
                    st.error(f"Ошибка при отображении результатов: {str(e)}")
                    st.code(str(monthly_decline), language="python")
            else:
                safe_log("warning", "Расчет динамики темпа падения вернул пустой результат")
                st.warning("Недостаточно данных для расчета динамики темпа падения с указанными параметрами. Возможные причины:\n"
                          "- Недостаточно данных для указанного периода\n"
                          "- Нет скважин, удовлетворяющих условиям фильтрации\n"
                          "- Все скважины имеют события в указанный период (если включена опция исключения скважин с событиями)")

# Вкладка 4: Анализ по скважинам
with tab4:
    st.header("Анализ кривых падения добычи по скважинам")
    
    # Получаем список скважин
    wells = st.session_state.prod_df["uwi"].unique().sort()
    
    # Настройки анализа
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_well = st.selectbox(
            "Выберите скважину",
            options=wells
        )
    
    with col2:
        well_start_date = st.date_input(
            "Начальная дата анализа",
            value=datetime(2024, 1, 1),
            min_value=datetime(2024, 1, 1),
            max_value=datetime(2024, 12, 31),
            key="well_start_date"
        )
    
    with col3:
        well_end_date = st.date_input(
            "Конечная дата анализа",
            value=datetime(2024, 12, 31),
            min_value=datetime(2024, 1, 1),
            max_value=datetime(2024, 12, 31),
            key="well_end_date"
        )
    
    # Дополнительные настройки
    col1, col2 = st.columns(2)
    
    with col1:
        well_rate_col = st.selectbox(
            "Параметр для анализа",
            options=["oil_rate", "liquid_rate", "gas_rate"],
            format_func=lambda x: {
                "oil_rate": "Дебит нефти",
                "liquid_rate": "Дебит жидкости",
                "gas_rate": "Дебит газа"
            }.get(x, x),
            key="well_rate_col" # Добавлен уникальный ключ
        )
    
    with col2:
        model_type = st.selectbox(
            "Тип модели кривой падения",
            options=["exponential", "harmonic", "hyperbolic"],
            format_func=lambda x: {
                "exponential": "Экспоненциальная (Arps, b=0)",
                "harmonic": "Гармоническая (Arps, b=1)",
                "hyperbolic": "Гиперболическая (Arps, 0<b<1)"
            }.get(x, x)
        )
    
    # Кнопка для анализа
    if st.button("Анализировать скважину"):
        with st.spinner("Выполняется анализ..."):
            safe_log("info", "Начат анализ скважины")
            # Аппроксимируем кривую падения
            fig, params, metrics = fit_decline_curve(
                prod_df=st.session_state.prod_df,
                uwi=selected_well,
                rate_col=well_rate_col,
                model_type=model_type
            )
            
            if params is not None:
                # Отображаем результаты
                st.subheader(f"Анализ скважины {selected_well}")
                
                # Отображаем график
                st.plotly_chart(fig, use_container_width=True)
                
                # Отображаем параметры модели
                st.subheader("Параметры модели")
                
                if model_type == "exponential":
                    q0, d = params
                    st.markdown(f"""
                    - **Начальный дебит (q₀):** {q0:.2f}
                    - **Коэффициент падения (D):** {d:.6f} (1/день) = {d*365:.4f} (1/год) = {d*100*365:.2f} %/год
                    - **Формула:** q(t) = q₀ × e^(-D×t)
                    """)
                elif model_type == "harmonic":
                    q0, d = params
                    st.markdown(f"""
                    - **Начальный дебит (q₀):** {q0:.2f}
                    - **Коэффициент падения (D):** {d:.6f} (1/день) = {d*365:.4f} (1/год)
                    - **Формула:** q(t) = q₀ / (1 + D×t)
                    """)
                elif model_type == "hyperbolic":
                    q0, d, b = params
                    st.markdown(f"""
                    - **Начальный дебит (q₀):** {q0:.2f}
                    - **Коэффициент падения (D):** {d:.6f} (1/день) = {d*365:.4f} (1/год)
                    - **Показатель кривизны (b):** {b:.4f}
                    - **Формула:** q(t) = q₀ / (1 + b×D×t)^(1/b)
                    """)
                
                # Отображаем метрики
                st.subheader("Метрики")
                st.markdown(f"""
                - **RMSE:** {metrics['rmse']:.4f}
                - **MAE:** {metrics['mae']:.4f}
                - **R²:** {metrics['r2']:.4f}
                """)
                
                # Получаем события для скважины
                events = (st.session_state.events_df
                        .filter((pl.col("uwi") == selected_well) & 
                                (pl.col("event_date").is_between(well_start_date, well_end_date)))
                        .sort("event_date"))
                
                if len(events) > 0:
                    st.subheader("События на скважине")
                    display_results_table(events, key="events")
                safe_log("info", "Анализ скважины завершен")
            else:
                st.warning("Не удалось аппроксимировать кривую падения для данной скважины. Попробуйте изменить параметры или выбрать другую скважину.")

# Вкладка 5: Информация о данных
with st.expander("Информация о данных"):
    st.header("Информация о данных")
    
    # Отображаем общую информацию о данных
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Данные добычи")
        
        # Общая информация
        num_wells = st.session_state.prod_df["uwi"].unique().shape[0]
        num_horizons = st.session_state.prod_df["horizon"].unique().shape[0]
        date_range = f"{st.session_state.prod_df['date'].min()} - {st.session_state.prod_df['date'].max()}"
        
        st.markdown(f"""
        - **Количество скважин:** {num_wells}
        - **Количество горизонтов:** {num_horizons}
        - **Период данных:** {date_range}
        """)
        
        # Отображаем первые строки данных
        st.subheader("Пример данных добычи")
        display_results_table(st.session_state.prod_df.head(10), key="prod_df_head")
    
    with col2:
        st.subheader("Данные событий")
        
        # Общая информация
        num_events = len(st.session_state.events_df)
        num_wells_with_events = st.session_state.events_df["uwi"].unique().shape[0]
        event_types = st.session_state.events_df["event_type"].unique().to_list()
        
        st.markdown(f"""
        - **Количество событий:** {num_events}
        - **Количество скважин с событиями:** {num_wells_with_events}
        - **Типы событий:** {", ".join(event_types)}
        """)
        
        # Отображаем первые строки данных
        st.subheader("Пример данных событий")
        display_results_table(st.session_state.events_df.head(10), key="events_df_head")
    
    # Отображаем распределение скважин по горизонтам
    st.subheader("Распределение скважин по горизонтам")
    
    horizon_counts = (st.session_state.prod_df
                     .filter(pl.col("date") == st.session_state.prod_df['date'].max())
                     .group_by("horizon")
                     .agg(pl.col("uwi").n_unique().alias("well_count")))
    
    fig = px.pie(
        safe_to_pandas(horizon_counts),
        names="horizon",
        values="well_count",
        title="Распределение скважин по горизонтам"
    )
    
    st.plotly_chart(fig)
    
    # Отображаем распределение событий по типам
    st.subheader("Распределение событий по типам")
    
    event_counts = (st.session_state.events_df
                   .group_by("event_type")
                   .agg(pl.col("uwi").count().alias("event_count")))
    
    fig = px.bar(
        safe_to_pandas(event_counts),
        x="event_type",
        y="event_count",
        title="Распределение событий по типам"
    )
    
    st.plotly_chart(fig)

# Добавляем информацию в нижнем колонтитуле
st.markdown("""
---
### Справочная информация

**Темп падения переходящего фонда скважин** - это показатель, характеризующий естественное снижение добычи у группы скважин, которые добывали как в базовом периоде t₀, так и в текущем периоде t₁, без капитальных вмешательств.

**Формула расчета:**
- D = 1 - (Σ Q₁ / Σ Q₀)
- D% = D × 100%

где:
- D - темп падения (доли единицы)
- D% - темп падения (проценты)
- Σ Q₀ - суммарная добыча переходящего фонда в базовом периоде
- Σ Q₁ - суммарная добыча переходящего фонда в текущем периоде

**Модели кривых падения (Arps):**
- **Экспоненциальная:** q(t) = q₀ × e^(-D×t)
- **Гармоническая:** q(t) = q₀ / (1 + D×t)
- **Гиперболическая:** q(t) = q₀ / (1 + b×D×t)^(1/b)

где:
- q₀ - начальный дебит
- D - коэффициент падения
- b - показатель кривизны (0 ≤ b ≤ 1)
- t - время
""")

# Запуск приложения
if __name__ == "__main__":
    pass

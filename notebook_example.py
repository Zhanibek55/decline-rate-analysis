import sys
import os
sys.path.append('.')  # Добавляем текущую директорию в путь

# Импортируем функции из вашего проекта
from utils import load_data, calculate_decline_rate, plot_decline_rate, safe_to_pandas
from datetime import datetime

# Загружаем тестовые данные
print("Загрузка данных...")
prod_df, events_df = load_data()

# Выводим информацию о загруженных данных
print(f"Данные добычи: {prod_df.shape[0]} записей")
print(f"Данные событий: {events_df.shape[0]} записей")

# Рассчитываем темп падения
print("Расчет темпа падения...")
start_date = datetime.strptime("2024-01-01", "%Y-%m-%d").date()
end_date = datetime.strptime("2024-12-01", "%Y-%m-%d").date()

decline_df = calculate_decline_rate(
    prod_df=prod_df,
    events_df=events_df,
    start_date=start_date,
    end_date=end_date,
    group_by_cols=["horizon"],
    rate_col="oil_rate",
    min_rate=0.1,
    exclude_wells_with_events=False,
    include_inactive=False
)

# Преобразуем в pandas DataFrame для отображения
pandas_df = safe_to_pandas(decline_df)

# Отображаем результаты
print("\nРезультаты расчета темпа падения:")
print(pandas_df)

# Создаем график
print("\nПостроение графика...")
fig = plot_decline_rate(decline_df, group_col="horizon", title="Темп падения по горизонтам")
fig.show()

print("\nАнализ завершен!")

import sys
import io
import os
import locale

def setup_console_encoding():
    """
    Настраивает кодировку консоли для корректного отображения Unicode символов.
    Возвращает исходную кодировку консоли.
    """
    # Сохраняем исходную кодировку
    original_encoding = sys.stdout.encoding
    print(f"Original console encoding: {original_encoding}")
    
    # Метод 1: Установка переменной окружения PYTHONIOENCODING
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # Метод 2: Переопределение stdout с UTF-8 кодировкой
    if sys.version_info >= (3, 6):
        # В Python 3.6+ на Windows консоль по умолчанию использует UTF-8
        print("Using Python 3.6+ with native UTF-8 console support")
    else:
        # Для более старых версий Python
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        print(f"Reconfigured console encoding to: {sys.stdout.encoding}")
    
    return original_encoding

def safe_print(text):
    """
    Безопасный вывод текста в консоль с обработкой ошибок кодировки.
    """
    try:
        print(text)
    except UnicodeEncodeError:
        # Если не удалось вывести в UTF-8, пробуем с заменой символов
        try:
            print(text.encode('utf-8', errors='replace').decode('utf-8'))
        except:
            # Крайний случай - ASCII с заменой всех не-ASCII символов
            print(text.encode('ascii', errors='replace').decode('ascii'))

def safe_open(file_path, mode='r', encoding='utf-8'):
    """
    Безопасное открытие файла с обработкой различных кодировок.
    """
    encodings = ['utf-8', 'cp1251', 'windows-1251', 'latin1', 'ascii']
    
    # Если режим чтения
    if 'r' in mode:
        for enc in encodings:
            try:
                return open(file_path, mode=mode, encoding=enc)
            except UnicodeDecodeError:
                continue
        # Если все кодировки не подошли, используем замену символов
        return open(file_path, mode=mode, encoding='utf-8', errors='replace')
    else:
        # Для записи всегда используем UTF-8
        return open(file_path, mode=mode, encoding='utf-8')

if __name__ == "__main__":
    # Тестирование функций
    original_encoding = setup_console_encoding()
    
    print("\nTesting safe_print function:")
    safe_print("Тестовая строка с кириллицей")
    safe_print("Test string with special characters: ñáéíóú €£¥")
    
    print("\nCurrent working directory:", os.getcwd())
    
    # Пример использования safe_open
    print("\nTesting safe_open function:")
    try:
        with safe_open("test_encoding.txt", "w") as f:
            f.write("Тестовая запись в файл с кириллицей\n")
            f.write("Test writing to file with special characters: ñáéíóú €£¥\n")
        
        print("Successfully wrote to test_encoding.txt")
        
        with safe_open("test_encoding.txt", "r") as f:
            content = f.read()
            print("Read from file:")
            safe_print(content)
    except Exception as e:
        print(f"Error testing file operations: {e}")

import logging
import os
import sys
import io
from datetime import datetime

# Настройка логирования без использования файла
def setup_logger():
    """
    Настраивает логгер только с выводом в консоль, 
    чтобы избежать проблем с кодировкой при записи в файл
    """
    try:
        # Настраиваем логгер
        logger = logging.getLogger("decline_rate_app")
        logger.setLevel(logging.DEBUG)
        
        # Сбрасываем существующие обработчики, если они есть
        if logger.handlers:
            for handler in logger.handlers:
                logger.removeHandler(handler)
        
        # Обработчик для вывода в консоль
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Формат сообщений
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        
        # Добавляем обработчик к логгеру
        logger.addHandler(console_handler)
        
        # Проверяем, что логгер работает
        try:
            logger.info("Logger initialized successfully")
            print("Logger configured and ready")
        except Exception as e:
            print(f"Error during first log write: {str(e)}")
        
        return logger
    except Exception as e:
        print(f"ERROR during logger setup: {str(e)}")
        # Создаем базовый логгер, который выводит только в консоль
        basic_logger = logging.getLogger("basic_logger")
        basic_logger.setLevel(logging.DEBUG)
        
        # Сбрасываем существующие обработчики
        if basic_logger.handlers:
            for handler in basic_logger.handlers:
                basic_logger.removeHandler(handler)
                
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - BASIC - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        basic_logger.addHandler(console_handler)
        
        basic_logger.error(f"Failed to setup main logger: {str(e)}")
        return basic_logger

# Создаем глобальный логгер
logger = setup_logger()

# Добавляем тестовое сообщение при импорте модуля
print("Logger module loaded, logger initialized")

# Функция для безопасного логирования (с обработкой ошибок кодировки)
def safe_log(level, message):
    """
    Безопасно логирует сообщение, обрабатывая возможные ошибки кодировки
    
    Args:
        level: Уровень логирования (info, debug, warning, error, critical)
        message: Сообщение для логирования
    """
    try:
        # Преобразуем сообщение в ASCII для безопасности
        ascii_message = str(message).encode('ascii', 'replace').decode('ascii')
        
        if level == "info":
            logger.info(ascii_message)
        elif level == "debug":
            logger.debug(ascii_message)
        elif level == "warning":
            logger.warning(ascii_message)
        elif level == "error":
            logger.error(ascii_message)
        elif level == "critical":
            logger.critical(ascii_message)
    except Exception as e:
        print(f"General error during logging: {str(e)}")
        print(f"Attempted to log: {level} - {message}")

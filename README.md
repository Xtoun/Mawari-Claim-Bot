# Mawari Claim Bot

Автоматический бот для запроса средств из крана Mawari и отправки MAWARI токенов.

## Интерфейс

При запуске бота отображается интерактивное меню:

```
==================================================
🤖 MAWARI CLAIM BOT
==================================================
1) 🚀 Запустить бота
2) 💰 Проверить балансы Burner кошельков
3) ❌ Выход
==================================================

Выберите опцию (1-3): 
```

## Возможности

- 🔄 Автоматический запрос средств из крана каждые 24 часа
- 🌐 Поддержка HTTP прокси с автоматической ротацией
- 🔑 Генерация адресов кошельков из приватных ключей
- 🔄 Повторные попытки при ошибках (до 3 попыток)
- 💰 Автоматическая отправка 1 MAWARI токена на burner адрес
- 📊 Прогресс бар и детальная таблица результатов
- ⚙️ Гибкая конфигурация через файлы

## Установка

### Windows

1. **Установите Python 3.8 или выше** с [python.org](https://www.python.org/downloads/)

2. **Создайте виртуальное окружение:**
```cmd
# Создание виртуального окружения
python -m venv mawari_bot_env

# Активация виртуального окружения
mawari_bot_env\Scripts\activate

# Обновление pip
python -m pip install --upgrade pip
```

3. **Установите зависимости:**
```cmd
pip install -r requirements.txt
```

4. **Запуск бота:**
```cmd
python mawari_claim_bot.py
```

5. **Деактивация виртуального окружения (когда закончите):**
```cmd
deactivate
```

### Ubuntu/Linux

1. **Установите Python 3.8 или выше:**
```bash
# Обновление пакетов
sudo apt update

# Установка Python и pip
sudo apt install python3 python3-pip python3-venv
```

2. **Создайте виртуальное окружение:**
```bash
# Создание виртуального окружения
python3 -m venv mawari_bot_env

# Активация виртуального окружения
source mawari_bot_env/bin/activate

# Обновление pip
python -m pip install --upgrade pip
```

3. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

4. **Запуск бота:**
```bash
python mawari_claim_bot.py
```

5. **Деактивация виртуального окружения (когда закончите):**
```bash
deactivate
```

### Работа в фоновом режиме с screen (Ubuntu/Linux)

Для работы бота в фоновом режиме с возможностью отключения от терминала:

1. **Установите screen:**
```bash
sudo apt install screen
```

2. **Создайте новый screen сеанс:**
```bash
screen -S mawari_bot
```

3. **В screen сеансе активируйте venv и запустите бота:**
```bash
# Активация виртуального окружения
source mawari_bot_env/bin/activate

# Запуск бота
python mawari_claim_bot.py
```

4. **Отключитесь от screen (бот продолжит работу):**
   - Нажмите `Ctrl + A`, затем `D`

5. **Проверка активных screen сеансов:**
```bash
screen -ls
```

6. **Подключение к screen сеансу:**
```bash
screen -r mawari_bot
```

7. **Завершение screen сеанса:**
```bash
# Внутри screen сеанса нажмите Ctrl + C для остановки бота
# Затем введите:
exit
```

8. **Принудительное завершение screen сеанса:**
```bash
screen -S mawari_bot -X quit
```

## Настройка

### 1. Настройка кошельков (creds.txt)

Отредактируйте файл `creds.txt` в формате:
```
evm_private_key:burner_wallet_address
```

Пример:
```
0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef:0x16A4f86020F583Fb92383712f883aB9Ec82da538
0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890:0x742d35Cc6634C0532925a3b8D4B9db96C4b4d1b6
```

### 2. Настройка прокси (proxies.txt)

Отредактируйте файл `proxies.txt` (опционально):
```
http://127.0.0.1:8080
192.168.1.100:3128
http://user:pass@proxy.example.com:8080
```

## Использование

Запустите бота:
```bash
python mawari_claim_bot.py
```

#!/usr/bin/env python3
"""
Mawari Claim Bot
Автоматический бот для запроса средств из крана Mawari и отправки MAWARI токенов
"""

import json
import time
import random
import requests
from web3 import Web3
from eth_account import Account
from tqdm import tqdm
from tabulate import tabulate
import sys
import os
from datetime import datetime, timedelta
import threading

class MawariClaimBot:
    def __init__(self):
        self.faucet_url = "https://hub.testnet.mawari.net/api/trpc/faucet.requestFaucetFunds?batch=1"
        self.rpc_url = "http://rpc.testnet.mawari.net/http"
        self.chain_id = 576
        self.symbol = "MAWARI"
        self.explorer = "explorer.testnet.mawari.net"
        
        self.wallets = []
        self.proxies = []
        self.web3 = None
        self.results = {
            'successful': [],
            'failed': []
        }
        
    def load_credentials(self):
        """Загружает приватные ключи из creds.txt"""
        try:
            with open('creds.txt', 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        private_key = parts[0].strip()
                        burner_address = parts[1].strip()
                        
                        # Генерируем адрес кошелька из приватного ключа
                        account = Account.from_key(private_key)
                        wallet_address = account.address
                        
                        self.wallets.append({
                            'private_key': private_key,
                            'wallet_address': wallet_address,
                            'burner_address': burner_address,
                            'account': account
                        })
            
            if not self.wallets:
                print("❌ Не найдено валидных кошельков в creds.txt")
                return False
                
            print(f"✅ Загружено {len(self.wallets)} кошельков")
            return True
            
        except FileNotFoundError:
            print("❌ Файл creds.txt не найден")
            return False
        except Exception as e:
            print(f"❌ Ошибка при загрузке creds.txt: {e}")
            return False
    
    def load_proxies(self):
        """Загружает прокси из proxies.txt"""
        try:
            with open('proxies.txt', 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Обрабатываем разные форматы прокси
                    if '://' in line:
                        # Уже полный URL
                        self.proxies.append(line)
                    elif ':' in line:
                        # Формат ip:port:username:password
                        parts = line.split(':')
                        if len(parts) >= 2:
                            if len(parts) == 2:
                                # ip:port
                                self.proxies.append(f"http://{parts[0]}:{parts[1]}")
                            elif len(parts) == 4:
                                # ip:port:username:password
                                self.proxies.append(f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}")
                            else:
                                # Пропускаем неправильный формат
                                print(f"⚠️ Пропущен неправильный формат прокси: {line}")
                    else:
                        # Просто IP или домен
                        self.proxies.append(f"http://{line}")
            
            if self.proxies:
                print(f"✅ Загружено {len(self.proxies)} прокси")
            else:
                print("⚠️ Прокси не найдены")
            
            return True
            
        except FileNotFoundError:
            print("⚠️ Файл proxies.txt не найден")
            return True  # Прокси не обязательны
    
    def init_web3(self):
        """Инициализирует Web3 соединение"""
        try:
            self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
            if self.web3.is_connected():
                print(f"✅ Подключение к RPC установлено: {self.rpc_url}")
                return True
            else:
                print("❌ Не удалось подключиться к RPC")
                return False
        except Exception as e:
            print(f"❌ Ошибка подключения к RPC: {e}")
            return False
    
    def get_random_proxy(self):
        """Возвращает случайный прокси"""
        if not self.proxies:
            return None
        return random.choice(self.proxies)
    
    def make_faucet_request(self, wallet_address, proxy=None):
        """Отправляет запрос к крану"""
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "0": {
                "json": {
                    "rollupSubdomain": "mawari-testnet",
                    "recipientAddress": wallet_address,
                    "turnstileToken": ""
                }
            }
        }
        
        proxies_dict = None
        if proxy:
            proxies_dict = {
                'http': proxy,
                'https': proxy
            }
        
        try:
            response = requests.post(
                self.faucet_url,
                headers=headers,
                json=data,
                proxies=proxies_dict,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    if 'result' in result[0]:
                        # Успешный запрос
                        tx_hash = result[0]['result']['data']['json']['transactionHash']
                        return {'success': True, 'tx_hash': tx_hash}
                    elif 'error' in result[0]:
                        # Ошибка в ответе
                        error_msg = result[0]['error']['json']['message']
                        return {'success': False, 'error': error_msg}
            
            return {'success': False, 'error': f'HTTP {response.status_code}'}
            
        except requests.exceptions.ProxyError:
            return {'success': False, 'error': 'Proxy error'}
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Timeout'}
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': 'Connection error'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_mawari_token(self, wallet, burner_address):
        """Отправляет 1 MAWARI токен на burner адрес"""
        try:
            # Получаем nonce
            nonce = self.web3.eth.get_transaction_count(wallet['wallet_address'])
            
            # Получаем текущий gas price
            gas_price = self.web3.eth.gas_price
            
            # Создаем транзакцию для отправки 1 MAWARI (1 * 10^18 wei)
            amount = self.web3.to_wei(1, 'ether')
            
            transaction = {
                'to': burner_address,
                'value': amount,
                'gas': 21000,
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': self.chain_id
            }
            
            # Подписываем транзакцию
            signed_txn = self.web3.eth.account.sign_transaction(transaction, wallet['private_key'])
            
            # Отправляем транзакцию
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            return {'success': True, 'tx_hash': tx_hash.hex()}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def process_wallet(self, wallet, progress_bar):
        """Обрабатывает один кошелек"""
        wallet_address = wallet['wallet_address']
        burner_address = wallet['burner_address']
        
        # Пробуем запросить средства из крана
        max_attempts = 3
        faucet_success = False
        faucet_tx = None
        
        for attempt in range(max_attempts):
            proxy = self.get_random_proxy() if self.proxies else None
            faucet_result = self.make_faucet_request(wallet_address, proxy)
            
            if faucet_result['success']:
                faucet_success = True
                faucet_tx = faucet_result['tx_hash']
                print(f"✅ {wallet_address[:10]}... - Faucet: {faucet_tx}")
                break
            else:
                error_msg = faucet_result['error']
                print(f"❌ {wallet_address[:10]}... - Faucet attempt {attempt + 1}: {error_msg}")
                if attempt < max_attempts - 1:
                    time.sleep(2)  # Пауза перед следующей попыткой
        
        if not faucet_success:
            self.results['failed'].append({
                'wallet': wallet_address,
                'burner': burner_address,
                'error': 'Faucet failed after 3 attempts'
            })
            progress_bar.update(1)
            return
        
        # Если запрос к крану успешен, отправляем MAWARI токен
        send_result = self.send_mawari_token(wallet, burner_address)
        
        if send_result['success']:
            send_tx = send_result['tx_hash']
            print(f"✅ {wallet_address[:10]}... - Send: {send_tx}")
            self.results['successful'].append({
                'wallet': wallet_address,
                'burner': burner_address,
                'faucet_tx': faucet_tx,
                'send_tx': send_tx
            })
        else:
            error_msg = send_result['error']
            print(f"❌ {wallet_address[:10]}... - Send failed: {error_msg}")
            self.results['failed'].append({
                'wallet': wallet_address,
                'burner': burner_address,
                'faucet_tx': faucet_tx,
                'error': f'Send failed: {error_msg}'
            })
        
        progress_bar.update(1)
    
    def run(self):
        """Основной метод запуска бота"""
        print("🚀 Запуск Mawari Claim Bot")
        print("=" * 50)
        
        # Загружаем данные
        if not self.load_credentials():
            return
        
        self.load_proxies()
        
        # Если только один кошелек и есть прокси, спрашиваем
        if len(self.wallets) == 1 and self.proxies:
            use_proxy = input("Использовать прокси? (y/n): ").lower().strip()
            if use_proxy != 'y':
                self.proxies = []
        
        # Инициализируем Web3
        if not self.init_web3():
            return
        
        print(f"\n📊 Обработка {len(self.wallets)} кошельков...")
        print("=" * 50)
        
        # Создаем прогресс бар
        with tqdm(total=len(self.wallets), desc="Processing wallets", unit="wallet") as pbar:
            for wallet in self.wallets:
                self.process_wallet(wallet, pbar)
                time.sleep(1)  # Пауза между кошельками
        
        # Показываем результаты
        self.show_results()
    
    def check_burner_balances(self):
        """Проверяет балансы MAWARI токенов на Burner кошельках"""
        print("🔍 Проверка балансов Burner кошельков...")
        print("=" * 60)
        
        if not self.web3:
            if not self.init_web3():
                return
        
        balance_data = []
        total_balance = 0
        
        for wallet in self.wallets:
            burner_address = wallet['burner_address']
            try:
                # Получаем баланс в wei
                balance_wei = self.web3.eth.get_balance(burner_address)
                # Конвертируем в MAWARI (1 MAWARI = 10^18 wei)
                balance_mawari = self.web3.from_wei(balance_wei, 'ether')
                total_balance += float(balance_mawari)
                
                balance_data.append([
                    burner_address[:20] + "...",
                    f"{balance_mawari:.6f}",
                    f"{balance_mawari:.2f}"
                ])
                
                print(f"💰 {burner_address[:20]}... - {balance_mawari:.6f} MAWARI")
                
            except Exception as e:
                balance_data.append([
                    burner_address[:20] + "...",
                    "ERROR",
                    "ERROR"
                ])
                print(f"❌ {burner_address[:20]}... - Ошибка: {e}")
        
        # Показываем таблицу
        print("\n" + "=" * 80)
        print("📊 БАЛАНСЫ BURNER КОШЕЛЬКОВ")
        print("=" * 80)
        
        print(tabulate(balance_data, 
                      headers=["Burner Address", "Balance (MAWARI)", "Balance (rounded)"],
                      tablefmt="grid"))
        
        print(f"\n💎 Общий баланс: {total_balance:.6f} MAWARI")
        print(f"🔗 Explorer: https://{self.explorer}")
        print("=" * 80)
    
    def show_results(self):
        """Показывает таблицу результатов"""
        print("\n" + "=" * 80)
        print("📋 РЕЗУЛЬТАТЫ ВЫПОЛНЕНИЯ")
        print("=" * 80)
        
        # Успешные кошельки
        if self.results['successful']:
            print(f"\n✅ УСПЕШНО ОБРАБОТАНО ({len(self.results['successful'])}):")
            successful_data = []
            for result in self.results['successful']:
                successful_data.append([
                    result['wallet'][:20] + "...",
                    result['burner'][:20] + "...",
                    result['faucet_tx'][:20] + "...",
                    result['send_tx'][:20] + "..."
                ])
            
            print(tabulate(successful_data, 
                          headers=["Wallet", "Burner", "Faucet TX", "Send TX"],
                          tablefmt="grid"))
        
        # Неудачные кошельки
        if self.results['failed']:
            print(f"\n❌ НЕ ОБРАБОТАНО ({len(self.results['failed'])}):")
            failed_data = []
            for result in self.results['failed']:
                failed_data.append([
                    result['wallet'][:20] + "...",
                    result['burner'][:20] + "...",
                    result.get('faucet_tx', 'N/A')[:20] + "..." if result.get('faucet_tx') else 'N/A',
                    result['error'][:30] + "..." if len(result['error']) > 30 else result['error']
                ])
            
            print(tabulate(failed_data, 
                          headers=["Wallet", "Burner", "Faucet TX", "Error"],
                          tablefmt="grid"))
        
        print(f"\n📊 Итого: {len(self.results['successful'])} успешно, {len(self.results['failed'])} неудачно")
        print("=" * 80)

def show_menu():
    """Показывает главное меню"""
    print("\n" + "=" * 50)
    print("🤖 MAWARI CLAIM BOT")
    print("=" * 50)
    print("1) 🚀 Запустить бота")
    print("2) 💰 Проверить балансы Burner кошельков")
    print("3) ❌ Выход")
    print("=" * 50)

def main():
    """Главная функция"""
    bot = MawariClaimBot()
    
    while True:
        try:
            show_menu()
            choice = input("\nВыберите опцию (1-3): ").strip()
            
            if choice == "1":
                print("\n🚀 Запуск бота...")
                bot.run()
                input("\nНажмите Enter для возврата в меню...")
                
            elif choice == "2":
                print("\n💰 Проверка балансов...")
                # Загружаем данные для проверки балансов
                if not bot.load_credentials():
                    input("\nНажмите Enter для возврата в меню...")
                    continue
                
                bot.check_burner_balances()
                input("\nНажмите Enter для возврата в меню...")
                
            elif choice == "3":
                print("\n👋 До свидания!")
                break
                
            else:
                print("\n❌ Неверный выбор. Попробуйте снова.")
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n⏹️ Программа остановлена пользователем")
            break
        except Exception as e:
            print(f"\n❌ Критическая ошибка: {e}")
            input("\nНажмите Enter для продолжения...")

if __name__ == "__main__":
    main()

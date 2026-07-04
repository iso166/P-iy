from fastapi import FastAPI, Form, Cookie, Header, Response, HTTPException
from pydantic import BaseModel, EmailStr, Field
import mysql.connector
import bcrypt
import json
from datetime import datetime, timedelta
import os
import random
import threading
import time
from dotenv import load_dotenv
import jwt
from pathlib import Path

load_dotenv()  

db_user = os.getenv("DB_USER")      
db_password = os.getenv("DB_PASSWORD")
SECRET_KEY = os.getenv("KEY")
db_config ={
'host': 'localhost',
'user': db_user,
'password': db_password,
'database': 'testdb'
}

app = FastAPI()
DEVICE_KEY = os.getenv("ESP_DEVICE_KEY")
SENSOR_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS SensorOlcumleri (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(64) NOT NULL,
    temperature DECIMAL(5,2) NOT NULL,
    humidity DECIMAL(5,2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

SENSOR_INSERT_SQL = """
INSERT INTO SensorOlcumleri (device_id, temperature, humidity)
VALUES (%s, %s, %s)
"""

SENSOR_LATEST_SQL = """
SELECT device_id, temperature, humidity, created_at
FROM SensorOlcumleri
ORDER BY created_at DESC, id DESC
LIMIT 1
"""

BANK_ACCOUNTS_SQL = """
CREATE TABLE IF NOT EXISTS BankHesaplar (
    Nickname VARCHAR(30) PRIMARY KEY,
    Balance DECIMAL(14,2) NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)
"""

BANK_TRANSACTIONS_SQL = """
CREATE TABLE IF NOT EXISTS BankIslemleri (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Nickname VARCHAR(30) NOT NULL,
    action_type VARCHAR(32) NOT NULL,
    amount DECIMAL(14,2) NOT NULL,
    asset_name VARCHAR(64) DEFAULT NULL,
    note VARCHAR(255) DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

BANK_LOANS_SQL = """
CREATE TABLE IF NOT EXISTS Krediler (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Nickname VARCHAR(30) NOT NULL,
    amount DECIMAL(14,2) NOT NULL,
    term_months INT NOT NULL,
    monthly_payment DECIMAL(14,2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

BANK_TRANSFERS_SQL = """
CREATE TABLE IF NOT EXISTS BankTransfers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_nickname VARCHAR(30) NOT NULL,
    sender_number CHAR(8) NOT NULL,
    receiver_nickname VARCHAR(30) NOT NULL,
    receiver_number CHAR(8) NOT NULL,
    amount DECIMAL(14,2) NOT NULL,
    note VARCHAR(255) DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

SUPPORT_TICKETS_SQL = """
CREATE TABLE IF NOT EXISTS DestekTalepleri (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Nickname VARCHAR(30) NOT NULL,
    subject VARCHAR(120) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    admin_reply TEXT DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)
"""

MARKET_ASSETS_SQL = """
CREATE TABLE IF NOT EXISTS MarketVarliklari (
    id INT AUTO_INCREMENT PRIMARY KEY,
    asset_class VARCHAR(20) NOT NULL,
    name VARCHAR(80) NOT NULL,
    symbol VARCHAR(40) DEFAULT NULL,
    current_price DECIMAL(14,2) NOT NULL,
    base_price DECIMAL(14,2) NOT NULL,
    active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)
"""

MARKET_HISTORY_SQL = """
CREATE TABLE IF NOT EXISTS MarketFiyatDegisimleri (
    id INT AUTO_INCREMENT PRIMARY KEY,
    asset_id INT NOT NULL,
    old_price DECIMAL(14,2) NOT NULL,
    new_price DECIMAL(14,2) NOT NULL,
    change_amount DECIMAL(14,2) NOT NULL,
    change_percent DECIMAL(8,2) NOT NULL,
    direction VARCHAR(10) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

NOTICE_SQL = """
CREATE TABLE IF NOT EXISTS BankBildirimleri (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Nickname VARCHAR(30) NOT NULL,
    notice_type VARCHAR(20) NOT NULL,
    amount DECIMAL(14,2) NOT NULL,
    description TEXT DEFAULT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'unpaid',
    due_at TIMESTAMP NULL DEFAULT NULL,
    paid_at TIMESTAMP NULL DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

ASSETS_SQL = """
CREATE TABLE IF NOT EXISTS KullaniciVarliklari (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Nickname VARCHAR(30) NOT NULL,
    asset_class VARCHAR(20) NOT NULL,
    asset_name VARCHAR(80) NOT NULL,
    symbol VARCHAR(40) DEFAULT NULL,
    quantity DECIMAL(14,4) NOT NULL DEFAULT 0,
    average_price DECIMAL(14,2) NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

LOGS_SQL = """
CREATE TABLE IF NOT EXISTS UygulamaLoglari (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source VARCHAR(20) NOT NULL,
    level_name VARCHAR(20) NOT NULL,
    event_name VARCHAR(80) NOT NULL,
    detail TEXT DEFAULT NULL,
    nickname VARCHAR(30) DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

MARKET_DEFAULT_TYPES = [
    {"asset_class": "stock", "name": "TEKNO A.Ş.", "symbol": "TEKNO", "current_price": 120.0, "base_price": 120.0},
    {"asset_class": "stock", "name": "YAZILIM BİLİŞİM", "symbol": "YZLM", "current_price": 85.0, "base_price": 85.0},
    {"asset_class": "gold", "name": "Gram Altın", "symbol": "XAU-TRY", "current_price": 2500.0, "base_price": 2500.0},
    {"asset_class": "gold", "name": "Çeyrek Altın", "symbol": "Ceyrek", "current_price": 4200.0, "base_price": 4200.0},
]
ROOT_ACCOUNT = "root"
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
SERVER_LOG_FILE = LOG_DIR / "server.log"


def get_db_connection():
    return mysql.connector.connect(**db_config)


def ensure_sensor_table():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(SENSOR_TABLE_SQL)
        conn.commit()
        print("Sensor tablosu hazir")
    except mysql.connector.Error as err:
        print(f"[HATA] Sensor tablosu hazirlanamadi: {err}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def ensure_bank_tables():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        for statement in (
            BANK_ACCOUNTS_SQL,
            BANK_TRANSACTIONS_SQL,
            BANK_LOANS_SQL,
            SUPPORT_TICKETS_SQL,
            NOTICE_SQL,
            ASSETS_SQL,
            LOGS_SQL,
        ):
            cursor.execute(statement)
        conn.commit()
        print("Banka tabloları hazir")
    except mysql.connector.Error as err:
        print(f"[HATA] Banka tabloları hazirlanamadi: {err}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def ensure_column_exists(table_name, column_name, column_definition):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"SHOW COLUMNS FROM `{table_name}` LIKE %s", (column_name,))
        if cursor.fetchone() is None:
            cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN {column_definition}")
            conn.commit()
    except mysql.connector.Error as err:
        print(f"[HATA] `{table_name}` tablosuna `{column_name}` eklenemedi: {err}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def ensure_bank_loan_columns():
    ensure_column_exists("Krediler", "remaining_principal", "remaining_principal DECIMAL(14,2) NOT NULL DEFAULT 0")
    ensure_column_exists("Krediler", "interest_rate", "interest_rate DECIMAL(6,2) NOT NULL DEFAULT 5.00")
    ensure_column_exists("Krediler", "months_paid", "months_paid INT NOT NULL DEFAULT 0")
    ensure_column_exists("Krediler", "months_remaining", "months_remaining INT NOT NULL DEFAULT 0")
    ensure_column_exists("Krediler", "last_payment_at", "last_payment_at TIMESTAMP NULL DEFAULT NULL")
    ensure_column_exists("Krediler", "next_due_at", "next_due_at TIMESTAMP NULL DEFAULT NULL")


def log_event(source, level_name, event_name, detail=None, nickname=None):
    message = {
        "source": source,
        "level": level_name,
        "event": event_name,
        "detail": detail,
        "nickname": nickname,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    try:
        with SERVER_LOG_FILE.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(message, ensure_ascii=False) + "\n")
    except OSError as err:
        print(f"[HATA] Sunucu günlüğü yazılamadı: {err}")

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO UygulamaLoglari (source, level_name, event_name, detail, nickname)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (source, level_name, event_name, detail, nickname),
        )
        conn.commit()
    except mysql.connector.Error as err:
        print(f"[HATA] Log veritabanına yazılamadı: {err}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def ensure_user_number_column():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SHOW COLUMNS FROM Kullanıcılar LIKE 'UserNumber'")
        if cursor.fetchone() is None:
            cursor.execute("ALTER TABLE Kullanıcılar ADD COLUMN UserNumber CHAR(8) DEFAULT NULL UNIQUE")
            conn.commit()
            print("UserNumber kolonu eklendi")
    except mysql.connector.Error as err:
        print(f"[HATA] UserNumber kolonu hazirlanamadi: {err}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def generate_unique_user_number():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        for _ in range(50):
            number = f"{random.randint(10_000_000, 99_999_999)}"
            cursor.execute("SELECT 1 FROM Kullanıcılar WHERE UserNumber = %s", (number,))
            if cursor.fetchone() is None:
                return number
        raise RuntimeError("Unique user number could not be generated")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def ensure_existing_user_numbers():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT Nickname FROM Kullanıcılar WHERE UserNumber IS NULL OR UserNumber = ''")
        rows = cursor.fetchall()
        if not rows:
            return
        update_cursor = conn.cursor()
        for row in rows:
            user_number = generate_unique_user_number()
            update_cursor.execute(
                "UPDATE Kullanıcılar SET UserNumber = %s WHERE Nickname = %s",
                (user_number, row["Nickname"]),
            )
        conn.commit()
        update_cursor.close()
    except mysql.connector.Error as err:
        print(f"[HATA] Kullanıcı numaraları güncellenemedi: {err}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def ensure_market_tables():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        for statement in (MARKET_ASSETS_SQL, MARKET_HISTORY_SQL):
            cursor.execute(statement)
        conn.commit()
        print("Piyasa tabloları hazir")
    except mysql.connector.Error as err:
        print(f"[HATA] Piyasa tabloları hazirlanamadi: {err}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def seed_default_market_assets():
    if MARKET_DEFAULT_TYPES:
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM MarketVarliklari")
            count = cursor.fetchone()[0]
            if count == 0:
                for asset in MARKET_DEFAULT_TYPES:
                    cursor.execute(
                        """
                        INSERT INTO MarketVarliklari (asset_class, name, symbol, current_price, base_price, active)
                        VALUES (%s, %s, %s, %s, %s, 1)
                        """,
                        (
                            asset["asset_class"],
                            asset["name"],
                            asset.get("symbol"),
                            asset["current_price"],
                            asset["base_price"],
                        ),
                    )
                conn.commit()
        except mysql.connector.Error as err:
            print(f"[HATA] Varsayılan piyasa verisi eklenemedi: {err}")
        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()


def fetch_market_assets(asset_class=None, active_only=True):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT id, asset_class, name, symbol, current_price, base_price, active, updated_at FROM MarketVarliklari"
        params = []
        filters = []
        if active_only:
            filters.append("active = 1")
        if asset_class:
            filters.append("asset_class = %s")
            params.append(asset_class)
        if filters:
            query += " WHERE " + " AND ".join(filters)
        query += " ORDER BY asset_class ASC, name ASC"
        cursor.execute(query, params)
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"[HATA] Piyasa varlıkları okunamadı: {err}")
        return []
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def serialize_market_row(row):
    return {
        "id": row["id"],
        "asset_class": row["asset_class"],
        "name": row["name"],
        "symbol": row["symbol"],
        "current_price": float(row["current_price"]),
        "base_price": float(row["base_price"]),
        "active": bool(row["active"]),
        "updated_at": row["updated_at"].isoformat(timespec="seconds") if row["updated_at"] else None,
    }


def serialize_market_history_row(row):
    return {
        "id": row["id"],
        "asset_id": row["asset_id"],
        "asset_name": row.get("name"),
        "asset_class": row.get("asset_class"),
        "old_price": float(row["old_price"]),
        "new_price": float(row["new_price"]),
        "change_amount": float(row["change_amount"]),
        "change_percent": float(row["change_percent"]),
        "direction": row["direction"],
        "created_at": row["created_at"].isoformat(timespec="seconds") if row["created_at"] else None,
    }


def add_market_asset(asset_class, name, symbol, base_price):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO MarketVarliklari (asset_class, name, symbol, current_price, base_price, active)
            VALUES (%s, %s, %s, %s, %s, 1)
            """,
            (asset_class, name, symbol, base_price, base_price),
        )
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"[HATA] Piyasa varlığı eklenemedi: {err}")
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def add_market_history(asset_id, old_price, new_price):
    change_amount = round(float(new_price) - float(old_price), 2)
    if old_price == 0:
        change_percent = 0.0
    else:
        change_percent = round((change_amount / float(old_price)) * 100, 2)
    direction = "up" if change_amount > 0 else "down" if change_amount < 0 else "flat"
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO MarketFiyatDegisimleri (asset_id, old_price, new_price, change_amount, change_percent, direction)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (asset_id, old_price, new_price, change_amount, change_percent, direction),
        )
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"[HATA] Piyasa hareketi yazılamadı: {err}")
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def fetch_market_history(limit=50):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT h.id, h.asset_id, a.name, a.asset_class, h.old_price, h.new_price,
                   h.change_amount, h.change_percent, h.direction, h.created_at
            FROM MarketFiyatDegisimleri h
            JOIN MarketVarliklari a ON a.id = h.asset_id
            ORDER BY h.created_at DESC, h.id DESC
            LIMIT %s
            """,
            (limit,),
        )
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"[HATA] Piyasa geçmişi okunamadı: {err}")
        return []
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def update_market_prices_once():
    assets = fetch_market_assets(active_only=True)
    if not assets:
        return

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        for asset in assets:
            old_price = float(asset["current_price"])
            volatility = 0.015 if asset["asset_class"] == "gold" else 0.03
            change_rate = random.uniform(-volatility, volatility)
            new_price = max(0.01, round(old_price * (1 + change_rate), 2))
            cursor.execute(
                "UPDATE MarketVarliklari SET current_price = %s WHERE id = %s",
                (new_price, asset["id"]),
            )
            add_market_history(asset["id"], old_price, new_price)
        conn.commit()
        print("Piyasa fiyatları güncellendi")
    except mysql.connector.Error as err:
        print(f"[HATA] Piyasa fiyatları güncellenemedi: {err}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


MARKET_UPDATER_STARTED = False


def market_update_loop():
    while True:
        time.sleep(300)
        update_market_prices_once()


def start_market_updater():
    global MARKET_UPDATER_STARTED
    if MARKET_UPDATER_STARTED:
        return
    MARKET_UPDATER_STARTED = True
    worker = threading.Thread(target=market_update_loop, daemon=True)
    worker.start()


def format_sensor_row(row):
    if row is None:
        return None

    created_at = row["created_at"]
    if hasattr(created_at, "isoformat"):
        created_at = created_at.isoformat(timespec="seconds")

    return {
        "device_id": row["device_id"],
        "temperature": float(row["temperature"]),
        "humidity": float(row["humidity"]),
        "updated_at": created_at,
    }


def format_amount(value):
    return round(float(value), 2)


def ensure_bank_account(nickname):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Nickname FROM BankHesaplar WHERE Nickname = %s", (nickname,))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO BankHesaplar (Nickname, Balance) VALUES (%s, 0)", (nickname,))
            conn.commit()
    except mysql.connector.Error as err:
        print(f"[HATA] Banka hesabı olusturulamadi: {err}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def get_bank_balance(nickname):
    ensure_bank_account(nickname)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT Balance FROM BankHesaplar WHERE Nickname = %s", (nickname,))
        row = cursor.fetchone()
        if row is None:
            return 0.0
        return format_amount(row["Balance"])
    except mysql.connector.Error as err:
        print(f"[HATA] Bakiye okunamadi: {err}")
        return 0.0
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def change_bank_balance(nickname, delta):
    ensure_bank_account(nickname)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE BankHesaplar SET Balance = Balance + %s WHERE Nickname = %s",
            (delta, nickname),
        )
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"[HATA] Bakiye guncellenemedi: {err}")
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def ensure_sufficient_balance(nickname, amount):
    return get_bank_balance(nickname) >= amount


def add_bank_transaction(nickname, action_type, amount, asset_name=None, note=None):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO BankIslemleri (Nickname, action_type, amount, asset_name, note)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (nickname, action_type, amount, asset_name, note),
        )
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"[HATA] Banka işlemi kaydedilemedi: {err}")
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def create_support_ticket(nickname, subject, message):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO DestekTalepleri (Nickname, subject, message)
            VALUES (%s, %s, %s)
            """,
            (nickname, subject, message),
        )
        conn.commit()
        log_event("server", "info", "support_ticket", subject, nickname)
        return True
    except mysql.connector.Error as err:
        print(f"[HATA] Destek talebi kaydedilemedi: {err}")
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def fetch_user_support_tickets(nickname):
    return fetch_rows(
        """
        SELECT id, Nickname, subject, message, status, admin_reply, created_at, updated_at
        FROM DestekTalepleri
        WHERE Nickname = %s
        ORDER BY created_at DESC, id DESC
        """,
        (nickname,),
    )


def get_user_by_number(user_number):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT Nickname, UserNumber FROM Kullanıcılar WHERE UserNumber = %s",
            (user_number,),
        )
        return cursor.fetchone()
    except mysql.connector.Error as err:
        print(f"[HATA] Kullanıcı numarası bulunamadı: {err}")
        return None
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def get_user_number(nickname):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT UserNumber FROM Kullanıcılar WHERE Nickname = %s",
            (nickname,),
        )
        row = cursor.fetchone()
        if row:
            return row["UserNumber"]
        return None
    except mysql.connector.Error as err:
        print(f"[HATA] Kullanıcı numarası okunamadı: {err}")
        return None
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def create_transfer(sender_nickname, sender_number, receiver_nickname, receiver_number, amount, note=None):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO BankTransfers (sender_nickname, sender_number, receiver_nickname, receiver_number, amount, note)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (sender_nickname, sender_number, receiver_nickname, receiver_number, amount, note),
        )
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"[HATA] Transfer kaydedilemedi: {err}")
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def serialize_asset_row(row):
    return {
        "id": row["id"],
        "Nickname": row["Nickname"],
        "asset_class": row["asset_class"],
        "asset_name": row["asset_name"],
        "symbol": row["symbol"],
        "quantity": float(row["quantity"]),
        "average_price": float(row["average_price"]),
        "updated_at": row["updated_at"].isoformat(timespec="seconds") if row["updated_at"] else None,
        "created_at": row["created_at"].isoformat(timespec="seconds") if row["created_at"] else None,
    }


def fetch_user_assets(nickname):
    return fetch_rows(
        """
        SELECT id, Nickname, asset_class, asset_name, symbol, quantity, average_price, updated_at, created_at
        FROM KullaniciVarliklari
        WHERE Nickname = %s
        ORDER BY updated_at DESC, id DESC
        """,
        (nickname,),
    )


def upsert_user_asset(nickname, asset_class, asset_name, symbol, quantity, unit_price):
    conn = None
    cursor = None
    try:
        existing = fetch_rows(
            """
            SELECT id, quantity, average_price
            FROM KullaniciVarliklari
            WHERE Nickname = %s AND asset_class = %s AND asset_name = %s
            LIMIT 1
            """,
            (nickname, asset_class, asset_name),
        )
        conn = get_db_connection()
        cursor = conn.cursor()
        if existing:
            row = existing[0]
            current_quantity = float(row["quantity"])
            current_average = float(row["average_price"])
            new_quantity = current_quantity + float(quantity)
            if new_quantity <= 0:
                cursor.execute(
                    "DELETE FROM KullaniciVarliklari WHERE id = %s",
                    (row["id"],)
                )
            else:
                new_average = ((current_quantity * current_average) + (float(quantity) * float(unit_price))) / new_quantity
                cursor.execute(
                    """
                    UPDATE KullaniciVarliklari
                    SET quantity = %s, average_price = %s, symbol = %s
                    WHERE id = %s
                    """,
                    (new_quantity, format_amount(new_average), symbol, row["id"]),
                )
        else:
            if float(quantity) > 0:
                cursor.execute(
                    """
                    INSERT INTO KullaniciVarliklari (Nickname, asset_class, asset_name, symbol, quantity, average_price)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (nickname, asset_class, asset_name, symbol, quantity, unit_price),
                )
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"[HATA] Kullanıcı varlığı yazılamadı: {err}")
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def clear_user_assets(nickname):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM KullaniciVarliklari WHERE Nickname = %s", (nickname,))
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"[HATA] Kullanıcı varlıkları silinemedi: {err}")
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def serialize_notice_row(row):
    return {
        "id": row["id"],
        "Nickname": row["Nickname"],
        "notice_type": row["notice_type"],
        "amount": float(row["amount"]),
        "description": row["description"],
        "status": row["status"],
        "due_at": row["due_at"].isoformat(timespec="seconds") if row["due_at"] else None,
        "paid_at": row["paid_at"].isoformat(timespec="seconds") if row["paid_at"] else None,
        "created_at": row["created_at"].isoformat(timespec="seconds") if row["created_at"] else None,
    }


def create_bank_notice(nickname, notice_type, amount, description=None, due_at=None):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO BankBildirimleri (Nickname, notice_type, amount, description, status, due_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (nickname, notice_type, amount, description, "unpaid", due_at),
        )
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"[HATA] Bildirim oluşturulamadı: {err}")
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def fetch_user_notices(nickname):
    return fetch_rows(
        """
        SELECT id, Nickname, notice_type, amount, description, status, due_at, paid_at, created_at
        FROM BankBildirimleri
        WHERE Nickname = %s
        ORDER BY created_at DESC, id DESC
        """,
        (nickname,),
    )


def pay_bank_notice(nickname, notice_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, amount, status
            FROM BankBildirimleri
            WHERE id = %s AND Nickname = %s
            LIMIT 1
            """,
            (notice_id, nickname),
        )
        notice = cursor.fetchone()
        if notice is None or notice["status"] == "paid":
            return False, "notice not found"
        amount = format_amount(notice["amount"])
        if not ensure_sufficient_balance(nickname, amount):
            return False, "insufficient funds"
        if not change_bank_balance(nickname, -amount):
            return False, "balance update failed"
        cursor.close()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE BankBildirimleri
            SET status = 'paid', paid_at = NOW()
            WHERE id = %s
            """,
            (notice_id,),
        )
        conn.commit()
        add_bank_transaction(nickname, f"notice_{notice_id}", amount, note="Vergi/Fatura ödemesi")
        return True, None
    except mysql.connector.Error as err:
        print(f"[HATA] Bildirim ödenemedi: {err}")
        return False, "database error"
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def serialize_loan_row(row):
    return {
        "id": row["id"],
        "Nickname": row["Nickname"],
        "amount": float(row["amount"]),
        "term_months": row["term_months"],
        "monthly_payment": float(row["monthly_payment"]),
        "remaining_principal": float(row["remaining_principal"]) if row.get("remaining_principal") is not None else float(row["amount"]),
        "interest_rate": float(row["interest_rate"]) if row.get("interest_rate") is not None else 5.0,
        "months_paid": int(row["months_paid"]) if row.get("months_paid") is not None else 0,
        "months_remaining": int(row["months_remaining"]) if row.get("months_remaining") is not None else int(row["term_months"]),
        "status": row["status"],
        "last_payment_at": row["last_payment_at"].isoformat(timespec="seconds") if row.get("last_payment_at") else None,
        "next_due_at": row["next_due_at"].isoformat(timespec="seconds") if row.get("next_due_at") else None,
        "created_at": row["created_at"].isoformat(timespec="seconds") if row["created_at"] else None,
    }


def calculate_monthly_due(loan_row):
    remaining = float(loan_row.get("remaining_principal") or loan_row["amount"])
    months_remaining = int(loan_row.get("months_remaining") or loan_row["term_months"])
    months_remaining = max(1, months_remaining)
    principal_part = remaining / months_remaining
    interest_part = remaining * 0.05
    return format_amount(principal_part + interest_part)


def update_loan_progress(loan_id, status, remaining_principal, months_paid, months_remaining, last_payment_at=None, next_due_at=None):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE Krediler
            SET status = %s,
                remaining_principal = %s,
                months_paid = %s,
                months_remaining = %s,
                last_payment_at = %s,
                next_due_at = %s
            WHERE id = %s
            """,
            (status, remaining_principal, months_paid, months_remaining, last_payment_at, next_due_at, loan_id),
        )
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"[HATA] Kredi güncellenemedi: {err}")
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def seize_user_account(nickname, reason):
    ensure_bank_account(ROOT_ACCOUNT)
    seized_balance = get_bank_balance(nickname)
    if seized_balance > 0:
        change_bank_balance(nickname, -seized_balance)
        change_bank_balance(ROOT_ACCOUNT, seized_balance)
        add_bank_transaction(nickname, "seizure_balance", seized_balance, note=reason)
        add_bank_transaction(ROOT_ACCOUNT, "seizure_income", seized_balance, note=f"{nickname} | {reason}")

    seized_value = 0.0
    assets = fetch_user_assets(nickname)
    for asset in assets:
        current_asset = find_market_asset(asset["asset_class"], asset["asset_name"])
        unit_price = float(current_asset["current_price"]) if current_asset else float(asset["average_price"])
        total_value = format_amount(unit_price * float(asset["quantity"]))
        seized_value += total_value
        add_bank_transaction(
            nickname,
            "seizure_asset",
            total_value,
            asset_name=asset["asset_name"],
            note=reason,
        )
        add_bank_transaction(
            ROOT_ACCOUNT,
            "seizure_asset_income",
            total_value,
            asset_name=asset["asset_name"],
            note=f"{nickname} | {reason}",
        )

    if seized_value > 0:
        change_bank_balance(ROOT_ACCOUNT, seized_value)
    clear_user_assets(nickname)
    return format_amount(seized_balance + seized_value)


def create_loan_record(nickname, amount, term_months):
    monthly_payment = format_amount((float(amount) * 1.05) / term_months)
    next_due_at = datetime.now() + timedelta(days=30)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Krediler (
                Nickname, amount, term_months, monthly_payment, status,
                remaining_principal, interest_rate, months_paid, months_remaining,
                last_payment_at, next_due_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                nickname,
                amount,
                term_months,
                monthly_payment,
                "active",
                amount,
                5.00,
                0,
                term_months,
                None,
                next_due_at,
            ),
        )
        conn.commit()
        return monthly_payment
    except mysql.connector.Error as err:
        print(f"[HATA] Kredi kaydı oluşturulamadı: {err}")
        return None
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def pay_loan_installment(nickname, loan_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, Nickname, amount, term_months, monthly_payment, status,
                   remaining_principal, interest_rate, months_paid, months_remaining,
                   last_payment_at, next_due_at, created_at
            FROM Krediler
            WHERE id = %s AND Nickname = %s
            LIMIT 1
            """,
            (loan_id, nickname),
        )
        loan = cursor.fetchone()
        if loan is None or loan["status"] != "active":
            return False, "loan not found"
        due_amount = calculate_monthly_due(loan)
        if not ensure_sufficient_balance(nickname, due_amount):
            return False, "insufficient funds"
        if not change_bank_balance(nickname, -due_amount):
            return False, "balance update failed"
        remaining_principal = max(0.0, float(loan["remaining_principal"]) - (float(loan["remaining_principal"]) / max(1, int(loan["months_remaining"]))))
        months_paid = int(loan["months_paid"]) + 1
        months_remaining = max(0, int(loan["months_remaining"]) - 1)
        next_due_at = datetime.now() + timedelta(days=30) if months_remaining > 0 else None
        new_status = "closed" if months_remaining == 0 or remaining_principal <= 0.01 else "active"
        update_loan_progress(
            loan_id,
            new_status,
            round(remaining_principal, 2),
            months_paid,
            months_remaining,
            datetime.now(),
            next_due_at,
        )
        add_bank_transaction(nickname, "loan_payment", due_amount, note=f"Kredi taksiti #{loan_id}")
        return True, None
    except mysql.connector.Error as err:
        print(f"[HATA] Kredi taksidi ödenemedi: {err}")
        return False, "database error"
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def pay_loan_early(nickname, loan_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, Nickname, remaining_principal, status, months_paid
            FROM Krediler
            WHERE id = %s AND Nickname = %s
            LIMIT 1
            """,
            (loan_id, nickname),
        )
        loan = cursor.fetchone()
        if loan is None or loan["status"] != "active":
            return False, "loan not found"
        settlement = format_amount(float(loan["remaining_principal"]) * 1.05)
        if not ensure_sufficient_balance(nickname, settlement):
            return False, "insufficient funds"
        if not change_bank_balance(nickname, -settlement):
            return False, "balance update failed"
        update_loan_progress(loan_id, "closed", 0, int(loan.get("months_paid") or 0), 0, datetime.now(), None)
        add_bank_transaction(nickname, "loan_early_payoff", settlement, note=f"Erken kredi kapatma #{loan_id}")
        return True, None
    except mysql.connector.Error as err:
        print(f"[HATA] Kredi erken kapatılamadı: {err}")
        return False, "database error"
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def process_due_loans_once():
    loans = fetch_rows(
        """
        SELECT id, Nickname, amount, term_months, monthly_payment, status,
               remaining_principal, interest_rate, months_paid, months_remaining,
               last_payment_at, next_due_at, created_at
        FROM Krediler
        WHERE status = 'active' AND next_due_at IS NOT NULL AND next_due_at <= NOW()
        ORDER BY next_due_at ASC, id ASC
        """,
    )
    for loan in loans:
        due_amount = calculate_monthly_due(loan)
        nickname = loan["Nickname"]
        if ensure_sufficient_balance(nickname, due_amount):
            pay_loan_installment(nickname, loan["id"])
            log_event("server", "info", "loan_payment", f"{nickname} loan #{loan['id']} installment collected", nickname)
        else:
            seized = seize_user_account(nickname, f"Kredi tahsil edilemedi #{loan['id']}")
            update_loan_progress(loan["id"], "defaulted", 0, int(loan["months_paid"]), int(loan["months_remaining"]), datetime.now(), None)
            add_bank_transaction(nickname, "loan_default", seized, note=f"Kredi tahsil edilemedi #{loan['id']}")
            log_event("server", "warning", "loan_default", f"{nickname} loan #{loan['id']} defaulted", nickname)


LOAN_WORKER_STARTED = False


def loan_worker_loop():
    while True:
        time.sleep(60)
        process_due_loans_once()


def start_loan_worker():
    global LOAN_WORKER_STARTED
    if LOAN_WORKER_STARTED:
        return
    LOAN_WORKER_STARTED = True
    worker = threading.Thread(target=loan_worker_loop, daemon=True)
    worker.start()


def fetch_rows(query, params=(), dictionary=True):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=dictionary)
        cursor.execute(query, params)
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"[HATA] Sorgu calistirilamadi: {err}")
        return []
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def fetch_latest_sensor_reading():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(SENSOR_LATEST_SQL)
        return format_sensor_row(cursor.fetchone())
    except mysql.connector.Error as err:
        print(f"[HATA] Sensor verisi okunamadi: {err}")
        return None
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def insert_sensor_reading(device_id, temperature, humidity):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(SENSOR_INSERT_SQL, (device_id, temperature, humidity))
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"[HATA] Sensor verisi yazilamadi: {err}")
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def verify_device_key(device_key):
    if not DEVICE_KEY:
        return True
    return device_key == DEVICE_KEY


@app.on_event("startup")
def startup_event():
    ensure_sensor_table()
    ensure_bank_tables()
    ensure_bank_loan_columns()
    ensure_user_number_column()
    ensure_existing_user_numbers()
    ensure_market_tables()
    seed_default_market_assets()
    start_market_updater()
    start_loan_worker()
    process_due_loans_once()
    log_event("server", "info", "startup", "Sunucu başlatıldı")


@app.middleware("http")
async def request_logger(request, call_next):
    started_at = time.time()
    try:
        response = await call_next(request)
        elapsed_ms = round((time.time() - started_at) * 1000, 2)
        log_event(
            "server",
            "info",
            "http_request",
            f"{request.method} {request.url.path} -> {response.status_code} ({elapsed_ms} ms)",
        )
        return response
    except Exception as exc:
        elapsed_ms = round((time.time() - started_at) * 1000, 2)
        log_event(
            "server",
            "error",
            "http_error",
            f"{request.method} {request.url.path} failed after {elapsed_ms} ms: {exc}",
        )
        raise

sorgu_SQL = "SELECT Password, ROL, UserNumber FROM Kullanıcılar WHERE Nickname = %s"

def sorgu(girilen_kullanici, girilen_sifre):
        print("sorgu başladı")
        if not girilen_kullanici or not girilen_sifre:
            print("boş")
            return False

        conn = None
        cursor = None
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            print("Başarılı bağlantı")

            print("Sorgu başladı")
            cursor.execute(sorgu_SQL, (girilen_kullanici,))
            print("Sorgu bitii")

            sonuc = cursor.fetchone()

            if sonuc:

                db_sifre_hash = sonuc[0]
                db_rol = sonuc[1]
                db_numara = sonuc[2]
                if isinstance(db_sifre_hash, str):
                    db_sifre_hash = db_sifre_hash.encode('utf-8')
                    print("hash lendi")     
                girilen_sifre_bytes = girilen_sifre.encode('utf-8')
                   
                if bcrypt.checkpw(girilen_sifre_bytes, db_sifre_hash):

                    print(f"[BAŞARILI] Giriş yapıldı! Hoş geldiniz: {girilen_kullanici}")
                    payload = {
                        "sub": girilen_kullanici,
                        "Rol": db_rol,
                        "Numara": db_numara,
                        "exp": datetime.utcnow() + timedelta(minutes=120)
                    }
                    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
                    return token, db_rol, girilen_kullanici, db_numara
                    
                else:

                    print("[HATA] Hatalı şifre yada kullanıcı adı!")
                    return False
                    
            else:       

                print("[HATA] Hatalı şifre yada kullanıcı adı!")
                return False
        except mysql.connector.Error as err:
            print(f"[HATA] Veritabanı hatası: {err}")
            return False
        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()
        
def kaydet_veritabani(yeni_kullanici, yeni_sifre, yeni_sifre2, email):

    print("Kayıt işlemi başladı...")
    conn = None
    cursor = None
    KAYIT_SQL = """
INSERT INTO Kullanıcılar (Nickname, Password, EMail, Rol, UserNumber)
VALUES (%s, %s, %s, %s, %s)
"""

    if not yeni_kullanici or not yeni_sifre:

        print("[HATA] Kayıt için kullanıcı adı veya şifre boş bırakılamaz!")
        return False

    if yeni_sifre != yeni_sifre2:
        print("şifreyi düzgün tekrarla")
        return False

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        print("Bağlantı kuruldu")

        user_number = generate_unique_user_number()

        sifre_bytes = yeni_sifre.encode('utf-8')

        tuz = bcrypt.gensalt()

        hashlenmis_sifre = bcrypt.hashpw(sifre_bytes, tuz)
        print("Hashlendi")
        cursor.execute(
            KAYIT_SQL,
            (yeni_kullanici, hashlenmis_sifre.decode('utf-8'), email, "normal", user_number)
        )
        print("Kayıt işemi yapılıyor")
        conn.commit()

        print(f"[BAŞARILI] {yeni_kullanici} başarıyla kayıt edildi! Numara: {user_number}")
        
        return user_number

    except mysql.connector.Error as err:
        if err.errno == 1062:
                      
            print("[HATA] Bu kullanıcı adı zaten kullanılıyor!")
            return False
        else:
            
            print(f"[HATA] Veritabanı hatası: {err}")
            return False            
    finally:
        print("Bağlantıdan çıkıldı")
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

def token_decode(token_str):
    try:
        print("token kontrol")
        cıktı = jwt.decode(token_str, SECRET_KEY, algorithms=["HS256"])
        print(cıktı)
        return cıktı
    except jwt.ExpiredSignatureError:
        print("Token süresi dolmuş.")
        return None
    except jwt.InvalidTokenError:
        print("Geçersiz token.")
        return None


def get_token_context(token_str):
    payload = token_decode(token_str)
    if payload is None:
        return None, None
    return payload, payload.get("sub")


def is_admin_payload(payload):
    return payload is not None and payload.get("Rol") == "admin"
class LoginData(BaseModel):
    username: str
    password: str
class SingupData(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=8)
    password2: str
    mail: EmailStr    

class tokenData(BaseModel):
    token: str


class SensorUpdateData(BaseModel):
    device_id: str = "esp8266-dht11"
    temperature: float = Field(ge=-50, le=150)
    humidity: float = Field(ge=0, le=100)
    device_key: str | None = None


class BankActionData(BaseModel):
    token: str
    action: str = Field(min_length=2, max_length=30)
    amount: float | None = Field(default=None, ge=0)
    quantity: float | None = Field(default=None, ge=0)
    asset_name: str | None = Field(default=None, max_length=64)
    asset_class: str | None = Field(default=None, max_length=20)
    subject: str | None = Field(default=None, max_length=120)
    message: str | None = Field(default=None, max_length=1000)
    term_months: int | None = Field(default=None, ge=1, le=120)
    target_user: str | None = Field(default=None, max_length=30)


class BankAdminActionData(BaseModel):
    token: str
    target_user: str = Field(min_length=3, max_length=30)
    amount: float = Field(gt=0)
    action: str = Field(min_length=3, max_length=20)
    note: str | None = Field(default=None, max_length=255)


class AdminSupportReplyData(BaseModel):
    token: str
    ticket_id: int = Field(gt=0)
    reply: str = Field(min_length=1, max_length=1000)
    status: str = Field(default="closed", max_length=20)


class SupportTicketData(BaseModel):
    token: str
    subject: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1, max_length=1000)


class TransferData(BaseModel):
    token: str
    recipient_number: str = Field(min_length=8, max_length=8)
    amount: float = Field(gt=0)
    note: str | None = Field(default=None, max_length=255)


class MarketAdminAddData(BaseModel):
    token: str
    asset_class: str = Field(min_length=3, max_length=20)
    name: str = Field(min_length=1, max_length=80)
    symbol: str | None = Field(default=None, max_length=40)
    base_price: float = Field(gt=0)


class BankNoticeCreateData(BaseModel):
    token: str
    target_user: str = Field(min_length=3, max_length=30)
    notice_type: str = Field(min_length=3, max_length=20)
    amount: float = Field(gt=0)
    description: str | None = Field(default=None, max_length=1000)
    due_days: int | None = Field(default=30, ge=1, le=365)


class LoanPaymentData(BaseModel):
    token: str
    loan_id: int = Field(gt=0)
    mode: str = Field(default="monthly", max_length=20)


class BankNoticePayData(BaseModel):
    token: str
    notice_id: int = Field(gt=0)

@app.post("/login")
def login(data: LoginData):
    sonuc = sorgu(data.username, data.password)
    if not sonuc:
        log_event("server", "warning", "login_fail", data.username)
        return {"status": "fail"}

    token, db_rol, girilenkullancı, db_numara = sonuc
    print("Başarılı")
    log_event("server", "info", "login_success", girilenkullancı, girilenkullancı)
    return {"status": "success", "Token": token, "Rol": db_rol, "Kim": girilenkullancı, "Numara": db_numara}

@app.post("/singup")
def singup(data: SingupData):
    user_number = kaydet_veritabani(data.username, data.password, data.password2, data.mail)
    if user_number:
        print("Kayıt yapıldı")
        log_event("server", "info", "signup_success", data.username, data.username)
        return {"status": "success", "Numara": user_number}
    print("Kayıt yapılamadı")
    log_event("server", "warning", "signup_fail", data.username, data.username)
    return {"status": "fail"}

@app.post("/veri")
def veri_lot(data: tokenData):
    print("lot sorgu")
    sonuc = token_decode(data.token)

    if sonuc is None:
        return {"status": "fail"}

    if sonuc.get("Rol") == "admin":
        print("token sorgu doğru")
        latest_sensor = fetch_latest_sensor_reading()
        return {
            "status": "success",
            "device_id": latest_sensor.get("device_id") if latest_sensor else None,
            "temperature": latest_sensor.get("temperature") if latest_sensor else None,
            "humidity": latest_sensor.get("humidity") if latest_sensor else None,
            "updated_at": latest_sensor.get("updated_at") if latest_sensor else None,
        }

    else:
        print("hatalı token veya yetki yok")  
        return {"status": "fail"}  


@app.post("/sensor/update")
def sensor_update(data: SensorUpdateData):
    if not verify_device_key(data.device_key):
        print("sensör anahtarı hatalı")
        log_event("server", "warning", "sensor_auth_fail", data.device_id, data.device_id)
        raise HTTPException(status_code=401, detail="Invalid device key")

    if not insert_sensor_reading(data.device_id, round(data.temperature, 2), round(data.humidity, 2)):
        return {"status": "fail"}

    print("sensör verisi güncellendi")
    log_event("server", "info", "sensor_update", f"{data.device_id} {data.temperature}/{data.humidity}", data.device_id)
    return {"status": "success"}


def serialize_transaction_row(row):
    return {
        "id": row["id"],
        "Nickname": row["Nickname"],
        "action_type": row["action_type"],
        "amount": float(row["amount"]),
        "asset_name": row["asset_name"],
        "note": row["note"],
        "created_at": row["created_at"].isoformat(timespec="seconds") if row["created_at"] else None,
    }


def serialize_account_row(row):
    return {
        "Nickname": row["Nickname"],
        "Balance": float(row["Balance"]),
        "updated_at": row["updated_at"].isoformat(timespec="seconds") if row["updated_at"] else None,
    }

def serialize_support_row(row):
    return {
        "id": row["id"],
        "Nickname": row["Nickname"],
        "subject": row["subject"],
        "message": row["message"],
        "status": row["status"],
        "admin_reply": row["admin_reply"],
        "created_at": row["created_at"].isoformat(timespec="seconds") if row["created_at"] else None,
        "updated_at": row["updated_at"].isoformat(timespec="seconds") if row["updated_at"] else None,
    }


def serialize_transfer_row(row):
    return {
        "id": row["id"],
        "sender_nickname": row["sender_nickname"],
        "sender_number": row["sender_number"],
        "receiver_nickname": row["receiver_nickname"],
        "receiver_number": row["receiver_number"],
        "amount": float(row["amount"]),
        "note": row["note"],
        "created_at": row["created_at"].isoformat(timespec="seconds") if row["created_at"] else None,
    }


def find_market_asset(asset_class, name_or_symbol):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, asset_class, name, symbol, current_price, base_price, active, updated_at
            FROM MarketVarliklari
            WHERE active = 1 AND asset_class = %s AND (name = %s OR symbol = %s)
            LIMIT 1
            """,
            (asset_class, name_or_symbol, name_or_symbol),
        )
        return cursor.fetchone()
    except mysql.connector.Error as err:
        print(f"[HATA] Piyasa varlığı bulunamadı: {err}")
        return None
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


@app.post("/bank/action")
def bank_action(data: BankActionData):
    payload, nickname = get_token_context(data.token)
    if payload is None:
        return {"status": "fail"}

    ensure_bank_account(nickname)
    action = data.action.strip().lower()
    amount = format_amount(data.amount or 0)
    quantity = format_amount(data.quantity or 0)
    asset_name = data.asset_name.strip() if data.asset_name else None
    asset_class = data.asset_class.strip().lower() if data.asset_class else None

    if action in {"tax", "vergi"}:
        if amount <= 0:
            return {"status": "fail", "message": "invalid amount"}
        if not ensure_sufficient_balance(nickname, amount):
            return {"status": "fail", "message": "insufficient funds"}
        if not change_bank_balance(nickname, -amount):
            return {"status": "fail"}
        add_bank_transaction(nickname, "tax", amount, note="Vergi ödemesi")
        log_event("server", "info", "tax_paid", f"{nickname} {amount}", nickname)
        return {"status": "success", "balance": get_bank_balance(nickname)}

    if action in {"bill", "fatura"}:
        if amount <= 0:
            return {"status": "fail", "message": "invalid amount"}
        if not ensure_sufficient_balance(nickname, amount):
            return {"status": "fail", "message": "insufficient funds"}
        if not change_bank_balance(nickname, -amount):
            return {"status": "fail"}
        add_bank_transaction(nickname, "bill", amount, note="Fatura ödemesi")
        log_event("server", "info", "bill_paid", f"{nickname} {amount}", nickname)
        return {"status": "success", "balance": get_bank_balance(nickname)}

    if action in {"stock_buy", "hisse_al", "gold_buy", "altin_al"}:
        if quantity <= 0:
            return {"status": "fail", "message": "invalid quantity"}
        if asset_class not in {"stock", "gold"}:
            asset_class = "stock" if action in {"stock_buy", "hisse_al"} else "gold"
        if not asset_name:
            return {"status": "fail", "message": "missing asset name"}
        asset = find_market_asset(asset_class, asset_name)
        if asset is None:
            return {"status": "fail", "message": "asset not found"}
        unit_price = format_amount(asset["current_price"])
        total_cost = format_amount(unit_price * quantity)
        if not ensure_sufficient_balance(nickname, total_cost):
            return {"status": "fail", "message": "insufficient funds"}
        if not change_bank_balance(nickname, -total_cost):
            return {"status": "fail"}
        add_bank_transaction(
            nickname,
            f"{asset_class}_buy",
            total_cost,
            asset_name=asset["name"],
            note=f"{quantity} adet x {unit_price} TL",
        )
        upsert_user_asset(
            nickname,
            asset_class,
            asset["name"],
            asset.get("symbol"),
            quantity,
            unit_price,
        )
        log_event("server", "info", "asset_buy", f"{nickname} {asset_class} {asset['name']} x{quantity}", nickname)
        return {
            "status": "success",
            "balance": get_bank_balance(nickname),
            "unit_price": unit_price,
            "total_cost": total_cost,
        }

    if action in {"stock_sell", "hisse_sat", "gold_sell", "altin_sat"}:
        if quantity <= 0:
            return {"status": "fail", "message": "invalid quantity"}
        if asset_class not in {"stock", "gold"}:
            asset_class = "stock" if action in {"stock_sell", "hisse_sat"} else "gold"
        if not asset_name:
            return {"status": "fail", "message": "missing asset name"}
        
        # Kullanıcının varlıklarını kontrol et
        conn = get_db_connection()
        if conn is None:
            return {"status": "fail", "message": "database error"}
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM KullaniciVarliklari WHERE Nickname = %s AND asset_class = %s AND asset_name = %s"
        cursor.execute(query, (nickname, asset_class, asset_name))
        user_asset = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user_asset is None:
            return {"status": "fail", "message": "asset not found"}
        
        current_quantity = format_amount(user_asset["quantity"])
        if current_quantity < quantity:
            return {"status": "fail", "message": f"insufficient quantity. Have: {current_quantity}"}
        
        asset = find_market_asset(asset_class, asset_name)
        if asset is None:
            return {"status": "fail", "message": "asset not found in market"}
        
        unit_price = format_amount(asset["current_price"])
        total_revenue = format_amount(unit_price * quantity)
        
        # Bakiyeyi artır
        if not change_bank_balance(nickname, total_revenue):
            return {"status": "fail"}
        
        # İşlemi kaydet
        add_bank_transaction(
            nickname,
            f"{asset_class}_sell",
            total_revenue,
            asset_name=asset["name"],
            note=f"{quantity} adet x {unit_price} TL",
        )
        
        # Varlığı güncelle (satılan miktarı çıkar)
        upsert_user_asset(
            nickname,
            asset_class,
            asset["name"],
            asset.get("symbol"),
            -quantity,
            unit_price,
        )
        
        log_event("server", "info", "asset_sell", f"{nickname} {asset_class} {asset['name']} x{quantity}", nickname)
        return {
            "status": "success",
            "balance": get_bank_balance(nickname),
            "unit_price": unit_price,
            "total_revenue": total_revenue,
        }

    if action in {"loan", "kredi"}:
        if amount <= 0:
            return {"status": "fail", "message": "invalid amount"}
        term_months = data.term_months or 6
        monthly_payment = create_loan_record(nickname, amount, term_months)
        if monthly_payment is None:
            return {"status": "fail"}
        if not change_bank_balance(nickname, amount):
            return {"status": "fail"}
        add_bank_transaction(nickname, "loan", amount, note=f"Kredi çekildi: {term_months} ay")
        log_event("server", "info", "loan_created", f"{nickname} {amount} {term_months} ay", nickname)
        return {
            "status": "success",
            "balance": get_bank_balance(nickname),
            "monthly_payment": monthly_payment,
            "term_months": term_months,
        }

    return {"status": "fail", "message": "unknown action"}


@app.post("/bank/transfer")
def bank_transfer(data: TransferData):
    payload, sender_nickname = get_token_context(data.token)
    if payload is None:
        return {"status": "fail"}

    sender_number = payload.get("Numara") or get_user_number(sender_nickname)
    receiver = get_user_by_number(data.recipient_number)
    amount = format_amount(data.amount)

    if not receiver:
        return {"status": "fail", "message": "recipient not found"}
    if receiver["Nickname"] == sender_nickname:
        return {"status": "fail", "message": "same user"}
    if amount <= 0:
        return {"status": "fail", "message": "invalid amount"}
    if not ensure_sufficient_balance(sender_nickname, amount):
        return {"status": "fail", "message": "insufficient funds"}

    if not change_bank_balance(sender_nickname, -amount):
        return {"status": "fail"}
    if not change_bank_balance(receiver["Nickname"], amount):
        change_bank_balance(sender_nickname, amount)
        return {"status": "fail"}

    note = data.note.strip() if data.note else None
    if not create_transfer(
        sender_nickname,
        sender_number,
        receiver["Nickname"],
        receiver["UserNumber"],
        amount,
        note,
    ):
        change_bank_balance(sender_nickname, amount)
        change_bank_balance(receiver["Nickname"], -amount)
        return {"status": "fail"}

    add_bank_transaction(sender_nickname, "transfer_out", amount, note=f"Gönderilen: {receiver['UserNumber']}")
    add_bank_transaction(receiver["Nickname"], "transfer_in", amount, note=f"Gelen: {sender_number}")
    log_event("server", "info", "transfer", f"{sender_nickname}->{receiver['Nickname']} {amount}", sender_nickname)
    return {
        "status": "success",
        "balance": get_bank_balance(sender_nickname),
        "recipient": receiver["Nickname"],
    }


@app.post("/bank/summary")
def bank_summary(data: tokenData):
    payload, nickname = get_token_context(data.token)
    if payload is None:
        return {"status": "fail"}

    ensure_bank_account(nickname)
    transactions = fetch_rows(
        """
        SELECT id, Nickname, action_type, amount, asset_name, note, created_at
        FROM BankIslemleri
        WHERE Nickname = %s
        ORDER BY created_at DESC, id DESC
        LIMIT 10
        """,
        (nickname,),
    )
    loans = fetch_rows(
        """
        SELECT id, Nickname, amount, term_months, monthly_payment, status, created_at
        FROM Krediler
        WHERE Nickname = %s
        ORDER BY created_at DESC, id DESC
        LIMIT 10
        """,
        (nickname,),
    )
    transfers = fetch_rows(
        """
        SELECT id, sender_nickname, sender_number, receiver_nickname, receiver_number, amount, note, created_at
        FROM BankTransfers
        WHERE sender_nickname = %s OR receiver_nickname = %s
        ORDER BY created_at DESC, id DESC
        LIMIT 10
        """,
        (nickname, nickname),
    )
    return {
        "status": "success",
        "balance": get_bank_balance(nickname),
        "user_number": payload.get("Numara") or get_user_number(nickname),
        "transactions": [serialize_transaction_row(row) for row in transactions],
        "loans": [serialize_loan_row(row) for row in loans],
        "transfers": [serialize_transfer_row(row) for row in transfers],
        "notices": [serialize_notice_row(row) for row in fetch_user_notices(nickname)],
        "assets": [serialize_asset_row(row) for row in fetch_user_assets(nickname)],
    }


@app.post("/bank/support")
def bank_support(data: SupportTicketData):
    payload, nickname = get_token_context(data.token)
    if payload is None:
        return {"status": "fail"}
    if create_support_ticket(nickname, data.subject, data.message):
        return {"status": "success"}
    return {"status": "fail"}


@app.post("/bank/support/my")
def bank_support_my(data: tokenData):
    payload, nickname = get_token_context(data.token)
    if payload is None:
        return {"status": "fail"}
    tickets = fetch_user_support_tickets(nickname)
    return {
        "status": "success",
        "tickets": [serialize_support_row(row) for row in tickets],
    }


@app.post("/bank/notices")
def bank_notices(data: tokenData):
    payload, nickname = get_token_context(data.token)
    if payload is None:
        return {"status": "fail"}
    notices = fetch_user_notices(nickname)
    return {
        "status": "success",
        "notices": [serialize_notice_row(row) for row in notices],
    }


@app.post("/bank/notice/pay")
def bank_notice_pay(data: BankNoticePayData):
    payload, nickname = get_token_context(data.token)
    if payload is None:
        return {"status": "fail"}
    success, reason = pay_bank_notice(nickname, data.notice_id)
    if not success:
        return {"status": "fail", "message": reason or "payment failed"}
    log_event("server", "info", "notice_pay", f"{nickname} notice #{data.notice_id} paid", nickname)
    return {"status": "success", "balance": get_bank_balance(nickname)}


@app.post("/bank/loan/pay")
def bank_loan_pay(data: LoanPaymentData):
    payload, nickname = get_token_context(data.token)
    if payload is None:
        return {"status": "fail"}
    mode = data.mode.strip().lower()
    if mode == "early":
        success, reason = pay_loan_early(nickname, data.loan_id)
    else:
        success, reason = pay_loan_installment(nickname, data.loan_id)
    if not success:
        return {"status": "fail", "message": reason or "payment failed"}
    log_event("server", "info", "loan_pay", f"{nickname} loan #{data.loan_id} {mode}", nickname)
    return {"status": "success", "balance": get_bank_balance(nickname)}


@app.post("/market/list")
def market_list(data: tokenData):
    payload, _ = get_token_context(data.token)
    if payload is None:
        return {"status": "fail"}
    assets = fetch_market_assets(active_only=True)
    return {
        "status": "success",
        "assets": [serialize_market_row(row) for row in assets],
    }


@app.post("/market/history")
def market_history(data: tokenData):
    payload, _ = get_token_context(data.token)
    if payload is None:
        return {"status": "fail"}
    history = fetch_market_history(50)
    return {
        "status": "success",
        "history": [serialize_market_history_row(row) for row in history],
    }


@app.post("/market/admin/add")
def market_admin_add(data: MarketAdminAddData):
    payload, _ = get_token_context(data.token)
    if not is_admin_payload(payload):
        return {"status": "fail"}
    asset_class = data.asset_class.strip().lower()
    if asset_class not in {"stock", "gold"}:
        return {"status": "fail", "message": "invalid asset class"}
    symbol = data.symbol.strip() if data.symbol else None
    if add_market_asset(asset_class, data.name.strip(), symbol, format_amount(data.base_price)):
        log_event("server", "info", "market_add", f"{asset_class}:{data.name.strip()}", payload.get("sub"))
        return {"status": "success"}
    return {"status": "fail"}


@app.post("/bank/admin/notice")
def bank_admin_notice(data: BankNoticeCreateData):
    payload, admin_name = get_token_context(data.token)
    if not is_admin_payload(payload):
        return {"status": "fail"}
    notice_type = data.notice_type.strip().lower()
    if notice_type not in {"tax", "bill"}:
        return {"status": "fail", "message": "invalid notice type"}
    due_at = datetime.now() + timedelta(days=data.due_days or 30)
    if create_bank_notice(
        data.target_user.strip(),
        notice_type,
        format_amount(data.amount),
        data.description.strip() if data.description else None,
        due_at,
    ):
        log_event(
            "server",
            "info",
            "admin_notice",
            f"{admin_name} -> {data.target_user.strip()} {notice_type} {data.amount}",
            admin_name,
        )
        return {"status": "success"}
    return {"status": "fail"}


@app.post("/bank/admin/accounts")
def bank_admin_accounts(data: tokenData):
    payload, _ = get_token_context(data.token)
    if not is_admin_payload(payload):
        return {"status": "fail"}
    accounts = fetch_rows(
        """
        SELECT Nickname, Balance, updated_at
        FROM BankHesaplar
        ORDER BY updated_at DESC, Nickname ASC
        """
    )
    return {
        "status": "success",
        "accounts": [serialize_account_row(row) for row in accounts],
    }


@app.post("/bank/admin/transactions")
def bank_admin_transactions(data: tokenData):
    payload, _ = get_token_context(data.token)
    if not is_admin_payload(payload):
        return {"status": "fail"}
    transactions = fetch_rows(
        """
        SELECT id, Nickname, action_type, amount, asset_name, note, created_at
        FROM BankIslemleri
        ORDER BY created_at DESC, id DESC
        LIMIT 50
        """
    )
    return {
        "status": "success",
        "transactions": [serialize_transaction_row(row) for row in transactions],
    }


@app.post("/bank/admin/loans")
def bank_admin_loans(data: tokenData):
    payload, _ = get_token_context(data.token)
    if not is_admin_payload(payload):
        return {"status": "fail"}
    loans = fetch_rows(
        """
        SELECT id, Nickname, amount, term_months, monthly_payment, status, created_at
        FROM Krediler
        ORDER BY created_at DESC, id DESC
        LIMIT 50
        """
    )
    return {
        "status": "success",
        "loans": [serialize_loan_row(row) for row in loans],
    }


@app.post("/bank/admin/support")
def bank_admin_support(data: tokenData):
    payload, _ = get_token_context(data.token)
    if not is_admin_payload(payload):
        return {"status": "fail"}
    tickets = fetch_rows(
        """
        SELECT id, Nickname, subject, message, status, admin_reply, created_at, updated_at
        FROM DestekTalepleri
        ORDER BY created_at DESC, id DESC
        LIMIT 50
        """
    )
    return {
        "status": "success",
        "tickets": [serialize_support_row(row) for row in tickets],
    }


@app.post("/bank/admin/adjust")
def bank_admin_adjust(data: BankAdminActionData):
    payload, admin_name = get_token_context(data.token)
    if not is_admin_payload(payload):
        return {"status": "fail"}

    target_user = data.target_user.strip()
    action = data.action.strip().lower()
    amount = format_amount(data.amount)
    ensure_bank_account(target_user)

    if action not in {"credit", "debit"}:
        return {"status": "fail", "message": "invalid action"}

    if action == "debit" and not ensure_sufficient_balance(target_user, amount):
        return {"status": "fail", "message": "insufficient funds"}

    delta = amount if action == "credit" else -amount
    if not change_bank_balance(target_user, delta):
        return {"status": "fail"}

    add_bank_transaction(
        target_user,
        f"admin_{action}",
        amount,
        note=data.note or f"Admin: {admin_name}",
    )
    log_event("server", "info", "admin_adjust", f"{admin_name} {action} {target_user} {amount}", admin_name)
    return {"status": "success", "balance": get_bank_balance(target_user)}


@app.post("/bank/admin/support/reply")
def bank_admin_support_reply(data: AdminSupportReplyData):
    payload, admin_name = get_token_context(data.token)
    if not is_admin_payload(payload):
        return {"status": "fail"}

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE DestekTalepleri
            SET status = %s, admin_reply = %s
            WHERE id = %s
            """,
            (data.status, f"{data.reply} | Admin: {admin_name}", data.ticket_id),
        )
        conn.commit()
        log_event("server", "info", "support_reply", f"ticket {data.ticket_id} by {admin_name}", admin_name)
        return {"status": "success"}
    except mysql.connector.Error as err:
        print(f"[HATA] Destek talebi guncellenemedi: {err}")
        return {"status": "fail"}
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

# main.py — БЛОК 1: Импорты, настройка, инициализация БД
import os
import asyncio
import aiosqlite
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

# 🔒 Токен берётся из переменной окружения (Replit Secrets)
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен! Добавьте его в Secrets на Replit.")

# 🤖 Инициализация
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# 📊 Пути и константы
DB_PATH = "cars_bot.db"

# 💱 Курсы валют (примерные, можно обновлять)
USD_TO_RUB = 80
USD_TO_EUR = 0.93

# 🎨 Доступные цвета для покраски
PAINT_COLORS = [
    "Красный", "Синий", "Чёрный", "Белый", "Жёлтый",
    "Зелёный", "Фиолетовый", "Оранжевый", "Серый", "Бронзовый"
]

# 📦 Глобальный список всех машин (будет заполнен в БЛОКЕ 2)
ALL_CARS: List[Dict] = []

# 🏠 Список недвижимости (будет заполнен позже)
REAL_ESTATE = {}

# 🔐 Админ (только @sky_for_pagani2)
CREATOR_USERNAME = "sky_for_pagani2"

# 🔄 Утилита: форматирование больших чисел
def format_number(n: int) -> str:
    if n >= 1_000_000_000:
        return f"{n // 1_000_000_000} млрд"
    if n >= 1_000_000:
        return f"{n // 1_000_000} млн"
    if n >= 1_000:
        return f"{n // 1_000} тыс"
    return str(n)

# 🕒 Утилита: ISO-время
def now_iso() -> str:
    return datetime.utcnow().isoformat()

# 🛠️ Инициализация базы данных
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Таблица пользователей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                display_name TEXT,
                balance INTEGER DEFAULT 0,
                last_drop TEXT,
                last_luck_case TEXT,
                last_tuning_case TEXT,
                used_new_client_case BOOLEAN DEFAULT 0,
                currency TEXT DEFAULT 'USD',
                real_estate_income INTEGER DEFAULT 0,
                promo_test_used BOOLEAN DEFAULT 0,
                promo_test2_used BOOLEAN DEFAULT 0,
                promo_bt_used BOOLEAN DEFAULT 0,
                promo_betatest_used BOOLEAN DEFAULT 0
            )
        """)

        # Таблица машин игроков
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                car_id INTEGER,
                is_duplicate BOOLEAN DEFAULT 0,
                source TEXT,
                acquired_at TEXT,
                color TEXT DEFAULT 'Стандартный'
            )
        """)

        # Глобальные лимиты на машины
        await db.execute("""
            CREATE TABLE IF NOT EXISTS global_car_counts (
                car_id INTEGER PRIMARY KEY,
                issued_count INTEGER DEFAULT 0
            )
        """)

        # Таблица владения недвижимостью
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_real_estate (
                user_id INTEGER,
                estate_id TEXT,
                purchased_at TEXT,
                PRIMARY KEY (user_id, estate_id)
            )
        """)

        await db.commit()

# 🚀 Запуск инициализации при старте
@dp.startup()
async def on_startup():
    await init_db()
    print("✅ База данных инициализирована. Бот запущен.")

# 🧪 Тестовая команда (для отладки)
@dp.message(Command("ping"))
async def ping(message: Message):
    await message.answer("pong! Бот жив и сохраняет данные в cars_bot.db")
  # main.py — БЛОК 2: Все машины

# 🎁 ВСЕ ВЫПАДАЮЩИЕ МАШИНЫ (DROP) — 110 штук (сокращённый пул)
DROP_CARS = [
    # Mercedes (15)
    {"id": 1, "name": "Mercedes-Benz 190E 2.5-16 Evolution II", "price_usd": 150_000, "year": 1991, "type": "drop", "max_global": 502, "image": "190e_evo2.png"},
    {"id": 2, "name": "Mercedes-Benz CLK GTR", "price_usd": 4_500_000, "year": 1998, "type": "drop", "max_global": 35, "image": "clk_gtr.png"},
    {"id": 3, "name": "Mercedes-Benz SLR McLaren 722", "price_usd": 1_200_000, "year": 2006, "type": "drop", "max_global": 150, "image": "slr_722.png"},
    {"id": 4, "name": "Mercedes-Benz SLS AMG Black Series", "price_usd": 300_000, "year": 2013, "type": "drop", "max_global": 350, "image": "sls_black.png"},
    {"id": 5, "name": "Mercedes-Benz G 63 AMG 6x6", "price_usd": 500_000, "year": 2013, "type": "drop", "max_global": 100, "image": "g63_6x6.png"},
    {"id": 6, "name": "Mercedes-Benz AMG GT Black Series", "price_usd": 350_000, "year": 2021, "type": "drop", "max_global": 730, "image": "gt_black.png"},
    {"id": 7, "name": "Mercedes-Benz 300 SL Gullwing", "price_usd": 1_800_000, "year": 1954, "type": "drop", "max_global": 1400, "image": "300sl_gullwing.png"},
    {"id": 8, "name": "Mercedes-Benz 500 E", "price_usd": 80_000, "year": 1991, "type": "drop", "max_global": 10_000, "image": "500e.png"},
    {"id": 9, "name": "Mercedes-Benz C 63 AMG Black Series", "price_usd": 120_000, "year": 2011, "type": "drop", "max_global": 250, "image": "c63_black.png"},
    {"id": 10, "name": "Mercedes-Benz E 63 AMG W212", "price_usd": 90_000, "year": 2013, "type": "drop", "max_global": 800, "image": "e63_w212.png"},
    {"id": 11, "name": "Mercedes-Benz R129 SL 600", "price_usd": 70_000, "year": 1995, "type": "drop", "max_global": 2000, "image": "sl600.png"},
    {"id": 12, "name": "Mercedes-Benz 190E Cosworth", "price_usd": 200_000, "year": 1988, "type": "drop", "max_global": 502, "image": "190e_cosworth.png"},
    {"id": 13, "name": "Mercedes-Benz CLK DTM AMG", "price_usd": 600_000, "year": 2004, "type": "drop", "max_global": 100, "image": "clk_dtm.png"},
    {"id": 14, "name": "Mercedes-Benz A 45 AMG", "price_usd": 55_000, "year": 2013, "type": "drop", "max_global": 5000, "image": "a45_amg.png"},
    {"id": 15, "name": "Mercedes-Benz Unimog U5000", "price_usd": 200_000, "year": 2010, "type": "drop", "max_global": 1000, "image": "unimog.png"},

    # BMW (15)
    {"id": 16, "name": "BMW M1", "price_usd": 550_000, "year": 1978, "type": "drop", "max_global": 453, "image": "bmw_m1.png"},
    {"id": 17, "name": "BMW E30 M3 Sport Evolution", "price_usd": 200_000, "year": 1990, "type": "drop", "max_global": 600, "image": "e30_m3.png"},
    {"id": 18, "name": "BMW E46 M3 CSL", "price_usd": 180_000, "year": 2003, "type": "drop", "max_global": 1383, "image": "e46_m3_csl.png"},
    {"id": 19, "name": "BMW 850 CSi", "price_usd": 120_000, "year": 1992, "type": "drop", "max_global": 1510, "image": "850csi.png"},
    {"id": 20, "name": "BMW Z8", "price_usd": 350_000, "year": 2000, "type": "drop", "max_global": 5703, "image": "bmw_z8.png"},
    {"id": 21, "name": "BMW M3 GTR (E46)", "price_usd": 1_500_000, "year": 2001, "type": "drop", "max_global": 10, "image": "m3_gtr.png"},
    {"id": 22, "name": "BMW 1 Series M Coupe", "price_usd": 70_000, "year": 2011, "type": "drop", "max_global": 7400, "image": "1m_coupe.png"},
    {"id": 23, "name": "BMW M4 CSL", "price_usd": 150_000, "year": 2022, "type": "drop", "max_global": 1000, "image": "m4_csl.png"},
    {"id": 24, "name": "BMW Z3 M Coupe", "price_usd": 60_000, "year": 1998, "type": "drop", "max_global": 5000, "image": "z3_mcoup.png"},
    {"id": 25, "name": "BMW i8", "price_usd": 100_000, "year": 2014, "type": "drop", "max_global": 20_000, "image": "bmw_i8.png"},
    {"id": 26, "name": "BMW M5 CS", "price_usd": 140_000, "year": 2021, "type": "drop", "max_global": 1000, "image": "m5_cs.png"},
    {"id": 27, "name": "BMW Alpina B7", "price_usd": 130_000, "year": 2020, "type": "drop", "max_global": 2000, "image": "alpina_b7.png"},
    {"id": 28, "name": "BMW 3.0 CSL '70s", "price_usd": 600_000, "year": 1973, "type": "drop", "max_global": 1265, "image": "30csl_70s.png"},
    {"id": 29, "name": "BMW M2 Competition", "price_usd": 60_000, "year": 2018, "type": "drop", "max_global": 5000, "image": "m2_comp.png"},
    {"id": 30, "name": "BMW X5 M", "price_usd": 90_000, "year": 2020, "type": "drop", "max_global": 10_000, "image": "x5m.png"},

    # Nissan (8)
    {"id": 31, "name": "Nissan Skyline GT-R R34", "price_usd": 200_000, "year": 1999, "type": "drop", "max_global": 11_548, "image": "r34.png"},
    {"id": 32, "name": "Nissan GT-R Nismo", "price_usd": 220_000, "year": 2015, "type": "drop", "max_global": 15_000, "image": "gtr_nismo.png"},
    {"id": 33, "name": "Nissan 300ZX Twin Turbo", "price_usd": 50_000, "year": 1990, "type": "drop", "max_global": 15_000, "image": "300zx.png"},
    {"id": 34, "name": "Nissan Silvia S15", "price_usd": 40_000, "year": 1999, "type": "drop", "max_global": 6000, "image": "s15.png"},
    {"id": 35, "name": "Nissan Fairlady Z (Z33)", "price_usd": 35_000, "year": 2003, "type": "drop", "max_global": 20_000, "image": "z33.png"},
    {"id": 36, "name": "Nissan Laurel C33", "price_usd": 20_000, "year": 1990, "type": "drop", "max_global": 10_000, "image": "laurel.png"},
    {"id": 37, "name": "Nissan Stagea", "price_usd": 25_000, "year": 1996, "type": "drop", "max_global": 8000, "image": "stagea.png"},
    {"id": 38, "name": "Nissan Cima Y34", "price_usd": 30_000, "year": 1996, "type": "drop", "max_global": 5000, "image": "cima.png"},

    # Toyota (12)
    {"id": 39, "name": "Toyota Supra MK4", "price_usd": 80_000, "year": 1993, "type": "drop", "max_global": 50_000, "image": "supra_mk4.png"},
    {"id": 40, "name": "Toyota GR Supra", "price_usd": 60_000, "year": 2019, "type": "drop", "max_global": 100_000, "image": "gr_supra.png"},
    {"id": 41, "name": "Toyota Celica GT-Four (ST205)", "price_usd": 40_000, "year": 1994, "type": "drop", "max_global": 15_000, "image": "celica.png"},
    {"id": 42, "name": "Toyota Land Cruiser FJ40", "price_usd": 90_000, "year": 1975, "type": "drop", "max_global": 20_000, "image": "fj40.png"},
    {"id": 43, "name": "Toyota 2000GT", "price_usd": 1_200_000, "year": 1967, "type": "drop", "max_global": 351, "image": "2000gt.png"},
    {"id": 44, "name": "Toyota MR2 SW20", "price_usd": 25_000, "year": 1993, "type": "drop", "max_global": 20_000, "image": "mr2.png"},
    {"id": 45, "name": "Toyota Celsior UCF10", "price_usd": 30_000, "year": 1990, "type": "drop", "max_global": 10_000, "image": "celsior.png"},
    {"id": 46, "name": "Toyota Altezza RS200", "price_usd": 20_000, "year": 1998, "type": "drop", "max_global": 8000, "image": "altezza.png"},
    {"id": 47, "name": "Toyota Chaser JZX100", "price_usd": 25_000, "year": 1996, "type": "drop", "max_global": 12_000, "image": "chaser.png"},
    {"id": 48, "name": "Toyota Aristo V300", "price_usd": 30_000, "year": 1997, "type": "drop", "max_global": 8000, "image": "aristo.png"},
    {"id": 49, "name": "Toyota Soarer JZZ30", "price_usd": 35_000, "year": 1991, "type": "drop", "max_global": 10_000, "image": "soarer.png"},
    {"id": 50, "name": "Toyota Century G50", "price_usd": 200_000, "year": 2018, "type": "drop", "max_global": 5000, "image": "century.png"},

    # Lexus (5)
    {"id": 51, "name": "Lexus LFA", "price_usd": 400_000, "year": 2010, "type": "drop", "max_global": 500, "image": "lexus_lfa.png"},
    {"id": 52, "name": "Lexus IS F", "price_usd": 45_000, "year": 2007, "type": "drop", "max_global": 10_000, "image": "isf.png"},
    {"id": 53, "name": "Lexus RC F", "price_usd": 75_000, "year": 2014, "type": "drop", "max_global": 15_000, "image": "rcf.png"},
    {"id": 54, "name": "Lexus SC 430", "price_usd": 25_000, "year": 2001, "type": "drop", "max_global": 20_000, "image": "sc430.png"},
    {"id": 55, "name": "Lexus GX 470", "price_usd": 40_000, "year": 2002, "type": "drop", "max_global": 100_000, "image": "gx470.png"},

    # Cadillac (4)
    {"id": 56, "name": "Cadillac CTS-V", "price_usd": 80_000, "year": 2009, "type": "drop", "max_global": 10_000, "image": "ctsv.png"},
    {"id": 57, "name": "Cadillac Escalade ESV", "price_usd": 100_000, "year": 2021, "type": "drop", "max_global": 50_000, "image": "escalade.png"},
    {"id": 58, "name": "Cadillac Eldorado", "price_usd": 30_000, "year": 1959, "type": "drop", "max_global": 20_000, "image": "eldorado.png"},
    {"id": 59, "name": "Cadillac ATS-V", "price_usd": 60_000, "year": 2016, "type": "drop", "max_global": 5000, "image": "atsv.png"},

    # Русские авто (6)
    {"id": 60, "name": "Lada Niva Legend", "price_usd": 15_000, "year": 2021, "type": "drop", "max_global": 1_000_000, "image": "niva.png"},
    {"id": 61, "name": "UAZ 469", "price_usd": 20_000, "year": 1970, "type": "drop", "max_global": 500_000, "image": "uaz469.png"},
    {"id": 62, "name": "Moskvich 412", "price_usd": 10_000, "year": 1970, "type": "drop", "max_global": 200_000, "image": "moskvich.png"},
    {"id": 63, "name": "GAZ Chaika", "price_usd": 50_000, "year": 1960, "type": "drop", "max_global": 3000, "image": "chaika.png"},
    {"id": 64, "name": "ZIL-114", "price_usd": 100_000, "year": 1970, "type": "drop", "max_global": 150, "image": "zil114.png"},
    {"id": 65, "name": "Marussia B2", "price_usd": 200_000, "year": 2012, "type": "drop", "max_global": 30, "image": "marussia.png"},

    # Китайские (5)
    {"id": 66, "name": "Hongqi L5", "price_usd": 800_000, "year": 2014, "type": "drop", "max_global": 500, "image": "hongqi_l5.png"},
    {"id": 67, "name": "NIO EP9", "price_usd": 1_500_000, "year": 2016, "type": "drop", "max_global": 10, "image": "nio_ep9.png"},
    {"id": 68, "name": "BYD Han", "price_usd": 60_000, "year": 2020, "type": "drop", "max_global": 100_000, "image": "byd_han.png"},
    {"id": 69, "name": "Geely Coolray", "price_usd": 25_000, "year": 2019, "type": "drop", "max_global": 500_000, "image": "coolray.png"},
    {"id": 70, "name": "Chery Tiggo 8", "price_usd": 20_000, "year": 2018, "type": "drop", "max_global": 300_000, "image": "tiggo8.png"},

    # Прочие бренды (40)
    {"id": 71, "name": "Fiat 500 Abarth", "price_usd": 25_000, "year": 2008, "type": "drop", "max_global": 100_000, "image": "fiat_500.png"},
    {"id": 72, "name": "Renault Alpine A110", "price_usd": 70_000, "year": 2017, "type": "drop", "max_global": 5000, "image": "alpine_a110.png"},
    {"id": 73, "name": "Jaguar XJR-15", "price_usd": 1_000_000, "year": 1991, "type": "drop", "max_global": 53, "image": "xjr15.png"},
    {"id": 74, "name": "Mazda RX-7 FD", "price_usd": 40_000, "year": 1992, "type": "drop", "max_global": 68_000, "image": "rx7.png"},
    {"id": 75, "name": "Subaru Impreza WRX STI", "price_usd": 45_000, "year": 2004, "type": "drop", "max_global": 100_000, "image": "sti.png"},
    {"id": 76, "name": "Mitsubishi Lancer Evolution IX", "price_usd": 40_000, "year": 2005, "type": "drop", "max_global": 25_000, "image": "evo9.png"},
    {"id": 77, "name": "Dodge Viper ACR", "price_usd": 150_000, "year": 2016, "type": "drop", "max_global": 1000, "image": "viper_acr.png"},
    {"id": 78, "name": "Chevrolet Corvette C7 Z06", "price_usd": 200_000, "year": 2013, "type": "drop", "max_global": 20_000, "image": "corvette.png"},
    {"id": 79, "name": "Ford Mustang GT", "price_usd": 50_000, "year": 2015, "type": "drop", "max_global": 200_000, "image": "mustang_gt.png"},
    {"id": 80, "name": "Aston Martin V8 Vantage", "price_usd": 120_000, "year": 2005, "type": "drop", "max_global": 22_000, "image": "vantage.png"},
    {"id": 81, "name": "Lotus Elise", "price_usd": 60_000, "year": 2000, "type": "drop", "max_global": 20_000, "image": "elise.png"},
    {"id": 82, "name": "Maserati MC12", "price_usd": 900_000, "year": 2004, "type": "drop", "max_global": 50, "image": "mc12.png"},
    {"id": 83, "name": "Alfa Romeo 8C Competizione", "price_usd": 200_000, "year": 2007, "type": "drop", "max_global": 500, "image": "8c.png"},
    {"id": 84, "name": "Ferrari 308 GTB", "price_usd": 100_000, "year": 1975, "type": "drop", "max_global": 5000, "image": "308.png"},
    {"id": 85, "name": "Porsche 911 Carrera RS", "price_usd": 500_000, "year": 1973, "type": "drop", "max_global": 1580, "image": "911_rs.png"},
    {"id": 86, "name": "Volvo 240 Turbo", "price_usd": 30_000, "year": 1983, "type": "drop", "max_global": 50_000, "image": "volvo240.png"},
    {"id": 87, "name": "Saab 9-3 Viggen", "price_usd": 25_000, "year": 1999, "type": "drop", "max_global": 10_000, "image": "saab_viggen.png"},
    {"id": 88, "name": "Opel Calibra", "price_usd": 20_000, "year": 1990, "type": "drop", "max_global": 100_000, "image": "calibra.png"},
    {"id": 89, "name": "Peugeot 205 GTI", "price_usd": 35_000, "year": 1984, "type": "drop", "max_global": 50_000, "image": "205gti.png"},
    {"id": 90, "name": "Mini Cooper S R53", "price_usd": 25_000, "year": 2002, "type": "drop", "max_global": 100_000, "image": "mini_r53.png"},
    {"id": 91, "name": "Kia Stinger GT", "price_usd": 50_000, "year": 2017, "type": "drop", "max_global": 50_000, "image": "stinger.png"},
    {"id": 92, "name": "Hyundai Genesis Coupe", "price_usd": 30_000, "year": 2010, "type": "drop", "max_global": 100_000, "image": "genesis_coupe.png"},
    {"id": 93, "name": "Suzuki Swift Sport", "price_usd": 20_000, "year": 2017, "type": "drop", "max_global": 200_000, "image": "swift_sport.png"},
    {"id": 94, "name": "Dacia Duster", "price_usd": 15_000, "year": 2010, "type": "drop", "max_global": 1_000_000, "image": "duster.png"},
    {"id": 95, "name": "Tata Nano", "price_usd": 2_500, "year": 2008, "type": "drop", "max_global": 1_000_000, "image": "nano.png"},
    {"id": 96, "name": "Holden Commodore HSV", "price_usd": 80_000, "year": 2015, "type": "drop", "max_global": 10_000, "image": "commodore.png"},
    {"id": 97, "name": "TVR Griffith", "price_usd": 150_000, "year": 1996, "type": "drop", "max_global": 2000, "image": "tvr_griffith.png"},
    {"id": 98, "name": "Morgan Plus Six", "price_usd": 100_000, "year": 2019, "type": "drop", "max_global": 500, "image": "morgan.png"},
    {"id": 99, "name": "Caterham Seven", "price_usd": 60_000, "year": 2020, "type": "drop", "max_global": 1000, "image": "caterham.png"},
    {"id": 100, "name": "Noble M600", "price_usd": 350_000, "year": 2010, "type": "drop", "max_global": 300, "image": "noble_m600.png"},
    {"id": 101, "name": "Ruf CTR Yellowbird", "price_usd": 1_000_000, "year": 1987, "type": "drop", "max_global": 25, "image": "ruf_yellowbird.png"},
    {"id": 102, "name": "Ginetta G55", "price_usd": 80_000, "year": 2011, "type": "drop", "max_global": 500, "image": "ginetta.png"},
    {"id": 103, "name": "BAC Mono", "price_usd": 180_000, "year": 2011, "type": "drop", "max_global": 300, "image": "bac_mono.png"},
    {"id": 104, "name": "Ariel Atom", "price_usd": 80_000, "year": 2015, "type": "drop", "max_global": 1000, "image": "ariel_atom.png"},
    {"id": 105, "name": "Radical SR3", "price_usd": 150_000, "year": 2003, "type": "drop", "max_global": 500, "image": "radical_sr3.png"},
    {"id": 106, "name": "Donkervoort D8 GTO", "price_usd": 100_000, "year": 2013, "type": "drop", "max_global": 500, "image": "donkervoort.png"},
    {"id": 107, "name": "Lancia Delta Integrale", "price_usd": 100_000, "year": 1987, "type": "drop", "max_global": 5000, "image": "delta_integrale.png"},
    {"id": 108, "name": "Fiat X1/9", "price_usd": 15_000, "year": 1972, "type": "drop", "max_global": 100_000, "image": "x19.png"},
    {"id": 109, "name": "Triumph TR6", "price_usd": 50_000, "year": 1969, "type": "drop", "max_global": 10_000, "image": "tr6.png"},
    {"id": 110, "name": "MG B GT", "price_usd": 30_000, "year": 1965, "type": "drop", "max_global": 20_000, "image": "mgb_gt.png"},
]

# 🛍️ АВТОСАЛОН — 30+ машин
SALON_CARS = [
    {"id": 111, "name": "Pagani Huayra", "price_usd": 2_400_000, "year": 2011, "type": "salon", "max_global": 100, "image": "huayra.png"},
    {"id": 112, "name": "Pagani Utopia", "price_usd": 2_600_000, "year": 2022, "type": "salon", "max_global": 99, "image": "utopia.png"},
    {"id": 113, "name": "Mercedes-AMG Project ONE", "price_usd": 2_700_000, "year": 2022, "type": "salon", "max_global": 275, "image": "project_one.png"},
    {"id": 114, "name": "Mercedes-Benz SLR McLaren Stirling Moss", "price_usd": 1_300_000, "year": 2009, "type": "salon", "max_global": 6, "image": "stirling_moss.png"},
    {"id": 115, "name": "Mercedes-Benz SLR McLaren 722", "price_usd": 1_200_000, "year": 2006, "type": "salon", "max_global": 150, "image": "slr_722_salon.png"},
    {"id": 116, "name": "Rolls-Royce Boat Tail", "price_usd": 28_000_000, "year": 2021, "type": "salon", "max_global": 5, "image": "boat_tail.png"},
    {"id": 117, "name": "Brabham BT62", "price_usd": 1_200_000, "year": 2018, "type": "salon", "max_global": 70, "image": "bt62.png"},
    {"id": 118, "name": "Bugatti Chiron", "price_usd": 3_000_000, "year": 2016, "type": "salon", "max_global": 500, "image": "chiron.png"},
    {"id": 119, "name": "Bugatti Tourbillon", "price_usd": 4_000_000, "year": 2024, "type": "salon", "max_global": 250, "image": "tourbillon.png"},
    {"id": 120, "name": "Bugatti Chiron Super Sport", "price_usd": 3_800_000, "year": 2021, "type": "salon", "max_global": 30, "image": "chiron_ss.png"},
    {"id": 121, "name": "Bugatti Veyron", "price_usd": 1_700_000, "year": 2005, "type": "salon", "max_global": 450, "image": "veyron.png"},
    {"id": 122, "name": "Hispano-Suiza Carmen", "price_usd": 1_700_000, "year": 2019, "type": "salon", "max_global": 19, "image": "carmen.png"},
    {"id": 123, "name": "Spania GTA Spano", "price_usd": 1_200_000, "year": 2013, "type": "salon", "max_global": 99, "image": "spano.png"},
    {"id": 124, "name": "Koenigsegg Regera", "price_usd": 2_000_000, "year": 2015, "type": "salon", "max_global": 85, "image": "regera.png"},
    {"id": 125, "name": "Rolls-Royce Droptail", "price_usd": 30_000_000, "year": 2023, "type": "salon", "max_global": 3, "image": "droptail.png"},
    # Вторая подгруппа — "обычные" редкие
    {"id": 126, "name": "Spyker C8 Preliator", "price_usd": 1_500_000, "year": 2016, "type": "salon", "max_global": 50, "image": "spyker.png"},
    {"id": 127, "name": "Gumpert Apollo IE", "price_usd": 3_000_000, "year": 2019, "type": "salon", "max_global": 10, "image": "apollo_ie.png"},
    {"id": 128, "name": "Zenvo TSR-S", "price_usd": 2_000_000, "year": 2019, "type": "salon", "max_global": 5, "image": "zenvo.png"},
    {"id": 129, "name": "Ares Design Project1", "price_usd": 1_700_000, "year": 2020, "type": "salon", "max_global": 99, "image": "ares_p1.png"},
    {"id": 130, "name": "Vanda Electrics Dendrobium", "price_usd": 3_000_000, "year": 2023, "type": "salon", "max_global": 10, "image": "dendrobium.png"},
    {"id": 131, "name": "De Tomaso P900", "price_usd": 2_000_000, "year": 2023, "type": "salon", "max_global": 18, "image": "p900.png"},
    {"id": 132, "name": "Czinger 21C", "price_usd": 1_700_000, "year": 2022, "type": "salon", "max_global": 80, "image": "czinger_21c.png"},
    {"id": 133, "name": "SSC Tuatara", "price_usd": 1_900_000, "year": 2020, "type": "salon", "max_global": 100, "image": "tuatara.png"},
    {"id": 134, "name": "Hennessey Venom F5", "price_usd": 2_100_000, "year": 2021, "type": "salon", "max_global": 24, "image": "venom_f5.png"},
    {"id": 135, "name": "Rimac Nevera", "price_usd": 2_400_000, "year": 2021, "type": "salon", "max_global": 150, "image": "nevera.png"},
    {"id": 136, "name": "Pininfarina Battista", "price_usd": 2_200_000, "year": 2019, "type": "salon", "max_global": 150, "image": "battista.png"},
    {"id": 137, "name": "Lotus Evija", "price_usd": 2_300_000, "year": 2020, "type": "salon", "max_global": 130, "image": "evija.png"},
    {"id": 138, "name": "Ferrari Daytona SP3", "price_usd": 2_200_000, "year": 2021, "type": "salon", "max_global": 599, "image": "daytona_sp3.png"},
    {"id": 139, "name": "Lamborghini Sián FKP 37",
    {"id": 140, "name": "McLaren Speedtail", "price_usd": 2_250_000, "year": 2019, "type": "salon", "max_global": 106, "image": "speedtail.png"},
]

# ✨ АКЦИЯ УДАЧИ — 70+ машин (разделены по категориям ниже)
LUCK_CASE_CARS = [
    {"id": 201, "name": "Rolls Royce Phantom II Jonckheere Aerodynamic Coupe", "price_usd": 8_000_000, "year": 1934, "type": "luck_case", "max_global": 1, "image": "phantom_jonckheere.png", "category": "Ретро Иконы"},
    {"id": 202, "name": "Nissan Z Nismo GT4", "price_usd": 250_000, "year": 2023, "type": "luck_case", "max_global": 100, "image": "z_nismo.png", "category": "Гоночные машины"},
    {"id": 203, "name": "W Motors Lykan Hypersport", "price_usd": 3_400_000, "year": 2013, "type": "luck_case", "max_global": 7, "image": "lykan.png", "category": "Гиперкары"},
    {"id": 204, "name": "W Motors Fenyr Supersport", "price_usd": 2_000_000, "year": 2016, "type": "luck_case", "max_global": 25, "image": "fenyr.png", "category": "Гиперкары"},
    {"id": 205, "name": "Ford Mustang GTD", "price_usd": 300_000, "year": 2023, "type": "luck_case", "max_global": 1000, "image": "mustang_gtd.png", "category": "Гоночные машины"},
    {"id": 206, "name": "Ford Mustang RTR Spec5", "price_usd": 150_000, "year": 2020, "type": "luck_case", "max_global": 500, "image": "rtr_spec5.png", "category": "Трековые авто"},
    {"id": 207, "name": "Ford Mustang Mach-E 1400", "price_usd": 1_000_000, "year": 2020, "type": "luck_case", "max_global": 1, "image": "mach_e_1400.png", "category": "Концепты"},
    {"id": 208, "name": "Ford GT40 MkI", "price_usd": 10_000_000, "year": 1966, "type": "luck_case", "max_global": 12, "image": "gt40.png", "category": "Гоночные машины"},
    {"id": 209, "name": "Bugatti Type 57SC Atlantic", "price_usd": 40_000_000, "year": 1936, "type": "luck_case", "max_global": 3, "image": "type57sc.png", "category": "Ретро Иконы"},
    {"id": 210, "name": "Lexus LFA", "price_usd": 400_000, "year": 2010, "type": "luck_case", "max_global": 500, "image": "lfa_luck.png", "category": "Гиперкары"},
    {"id": 211, "name": "Bugatti Mistral", "price_usd": 5_000_000, "year": 2022, "type": "luck_case", "max_global": 99, "image": "mistral.png", "category": "Гиперкары"},
    {"id": 212, "name": "Bugatti EB110 Super Sport", "price_usd": 3_000_000, "year": 1992, "type": "luck_case", "max_global": 30, "image": "eb110.png", "category": "Гиперкары"},
    {"id": 213, "name": "Bugatti Chiron Super Sport 300+", "price_usd": 3_900_000, "year": 2019, "type": "luck_case", "max_global": 30, "image": "ss300.png", "category": "Гиперкары"},
    {"id": 214, "name": "Koenigsegg CC850", "price_usd": 3_200_000, "year": 2022, "type": "luck_case", "max_global": 175, "image": "cc850.png", "category": "Гиперкары"},
    {"id": 215, "name": "Koenigsegg CCX", "price_usd": 900_000, "year": 2006, "type": "luck_case", "max_global": 50, "image": "ccx.png", "category": "Гиперкары"},
    {"id": 216, "name": "Koenigsegg Regera Ghost Package", "price_usd": 2_500_000, "year": 2021, "type": "luck_case", "max_global": 10, "image": "regera_ghost.png", "category": "Гиперкары"},
    {"id": 217, "name": "Koenigsegg Agera RS", "price_usd": 2_500_000, "year": 2015, "type": "luck_case", "max_global": 25, "image": "agera_rs.png", "category": "Гиперкары"},
    {"id": 218, "name": "Koenigsegg One:1", "price_usd": 2_700_000, "year": 2014, "type": "luck_case", "max_global": 2, "image": "one1.png", "category": "Гиперкары"},
    {"id": 219, "name": "Koenigsegg Jesko Attack", "price_usd": 3_000_000, "year": 2022, "type": "luck_case", "max_global": 125, "image": "jesko_attack.png", "category": "Гиперкары"},
    {"id": 220, "name": "Koenigsegg Jesko Absolute", "price_usd": 2_800_000, "year": 2022, "type": "luck_case", "max_global": 125, "image": "jesko_absolute.png", "category": "Гиперкары"},
    {"id": 221, "name": "Koenigsegg CCXR Trevita", "price_usd": 4_800_000, "year": 2009, "type": "luck_case", "max_global": 3, "image": "trevita.png", "category": "Гиперкары"},
    {"id": 222, "name": "Pagani Zonda F", "price_usd": 1_500_000, "year": 2005, "type": "luck_case", "max_global": 20, "image": "zonda_f.png", "category": "Гиперкары"},
    {"id": 223, "name": "Pagani Zonda R", "price_usd": 2_000_000, "year": 2009, "type": "luck_case", "max_global": 15, "image": "zonda_r.png", "category": "Трековые авто"},
    {"id": 224, "name": "Pagani Zonda Cinque", "price_usd": 1_800_000, "year": 2009, "type": "luck_case", "max_global": 5, "image": "zonda_cinque.png", "category": "Гиперкары"},
    {"id": 225, "name": "Pagani Zonda C12", "price_usd": 1_200_000, "year": 1999, "type": "luck_case", "max_global": 30, "image": "zonda_c12.png", "category": "Гиперкары"},
    {"id": 226, "name": "Pagani Huayra R", "price_usd": 3_500_000, "year": 2020, "type": "luck_case", "max_global": 30, "image": "huayra_r.png", "category": "Трековые авто"},
    {"id": 227, "name": "Pagani Huayra BC", "price_usd": 2_800_000, "year": 2016, "type": "luck_case", "max_global": 20, "image": "huayra_bc.png", "category": "Гиперкары"},
    {"id": 228, "name": "Bentley Continental GT3", "price_usd": 500_000, "year": 2013, "type": "luck_case", "max_global": 100, "image": "gt3.png", "category": "Гоночные машины"},
    {"id": 229, "name": "Hennessey Venom F5 Roadster", "price_usd": 3_000_000, "year": 2022, "type": "luck_case", "max_global": 12, "image": "venom_f5_roadster.png", "category": "Гиперкары"},
    {"id": 230, "name": "Jaguar E-Type Series 3 V12 Roadster", "price_usd": 300_000, "year": 1971, "type": "luck_case", "max_global": 1000, "image": "etype.png", "category": "Ретро Иконы"},
    {"id": 231, "name": "Porsche 911 GT1", "price_usd": 15_000_000, "year": 1996, "type": "luck_case", "max_global": 20, "image": "911_gt1.png", "category": "Гоночные машины"},
    {"id": 232, "name": "Porsche 963 LMDh #5", "price_usd": 2_000_000, "year": 2023, "type": "luck_case", "max_global": 1, "image": "963_5.png", "category": "Гоночные машины"},
    {"id": 233, "name": "Porsche Mission R", "price_usd": 1_000_000, "year": 2021, "type": "luck_case", "max_global": 10, "image": "mission_r.png", "category": "Концепты"},
    {"id": 234, "name": "Porsche 917K #23", "price_usd": 20_000_000, "year": 1970, "type": "luck_case", "max_global": 1, "image": "917k_23.png", "category": "Гоночные машины"},
    {"id": 235, "name": "Porsche 917K", "price_usd": 18_000_000, "year": 1970, "type": "luck_case", "max_global": 10, "image": "917k.png", "category": "Гоночные машины"},
    {"id": 236, "name": "Porsche 917/20 Pink Pig", "price_usd": 18_500_000, "year": 1971, "type": "luck_case", "max_global": 1, "image": "pink_pig.png", "category": "Гоночные машины"},
    {"id": 237, "name": "Porsche 911 Turbo S (991.2)", "price_usd": 180_000, "year": 2017, "type": "luck_case", "max_global": 10_000, "image": "911_turbo_s.png", "category": "Гиперкары"},
    {"id": 238, "name": "Porsche 959 Bruce Canepa", "price_usd": 1_200_000, "year": 1986, "type": "luck_case", "max_global": 50, "image": "959_canepa.png", "category": "Ретро Иконы"},
    {"id": 239, "name": "Porsche 911 GT3 RS", "price_usd": 220_000, "year": 2022, "type": "luck_case", "max_global": 2000, "image": "gt3_rs.png", "category": "Трековые авто"},
    {"id": 240, "name": "Porsche 935 Martini Racing", "price_usd": 800_000, "year": 2019, "type": "luck_case", "max_global": 77, "image": "935_martini.png", "category": "Гоночные машины"},
    {"id": 241, "name": "Porsche 956B", "price_usd": 12_000_000, "year": 1983, "type": "luck_case", "max_global": 20, "image": "956b.png", "category": "Гоночные машины"},
    {"id": 242, "name": "Ram 1500 TRX", "price_usd": 80_000, "year": 2021, "type": "luck_case", "max_global": 5000, "image": "ram_trx.png", "category": "Необычные"},
    {"id": 243, "name": "Mercedes-Benz E320 W210 4Matic", "price_usd": 10_000, "year": 1997, "type": "luck_case", "max_global": 10_000, "image": "e320_w210.png", "category": "Обычные машины"},
    {"id": 244, "name": "Mercedes-Benz O303", "price_usd": 200_000, "year": 1980, "type": "luck_case", "max_global": 1000, "image": "o303.png", "category": "Необычные"},
    {"id": 245, "name": "Mercedes CLK LM", "price_usd": 3_000_000, "year": 1998, "type": "luck_case", "max_global": 25, "image": "clk_lm.png", "category": "Гоночные машины"},
    {"id": 246, "name": "McLaren 650S", "price_usd": 300_000, "year": 2013, "type": "luck_case", "max_global": 5000, "image": "650s.png", "category": "Гиперкары"},
    {"id": 247, "name": "McLaren 650S GT3", "price_usd": 600_000, "year": 2015, "type": "luck_case", "max_global": 50, "image": "650s_gt3.png", "category": "Гоночные машины"},
    {"id": 248, "name": "McLaren MP4/4", "price_usd": 8_000_000, "year": 1988, "type": "luck_case", "max_global": 1, "image": "mp44.png", "category": "Гоночные машины"},
    {"id": 249, "name": "McLaren P1 MADMAC", "price_usd": 5_000_000, "year": 2020, "type": "luck_case", "max_global": 1, "image": "p1_madmac.png", "category": "Гиперкары"},
    {"id": 250, "name": "McLaren P1", "price_usd": 1_500_000, "year": 2013, "type": "luck_case", "max_global": 375, "image": "p1.png", "category": "Гиперкары"},
    {"id": 251, "name": "McLaren Senna", "price_usd": 1_000_000, "year": 2018, "type": "luck_case", "max_global": 500, "image": "senna.png", "category": "Трековые авто"},
    {"id": 252, "name": "McLaren Senna GTR", "price_usd": 1_500_000, "year": 2019, "type": "luck_case", "max_global": 75, "image": "senna_gtr.png", "category": "Трековые авто"},
    {"id": 253, "name": "McLaren 600LT", "price_usd": 250_000, "year": 2018, "type": "luck_case", "max_global": 1000, "image": "600lt.png", "category": "Гиперкары"},
    {"id": 254, "name": "McLaren Speedtail", "price_usd": 2_250_000, "year": 2019, "type": "luck_case", "max_global": 106, "image": "speedtail_luck.png", "category": "Гиперкары"},
    {"id": 255, "name": "McLaren MCL38", "price_usd": 1_000_000, "year": 2024, "type": "luck_case", "max_global": 1, "image": "mcl38.png", "category": "Гоночные машины"},
    {"id": 256, "name": "Ferrari Daytona SP3", "price_usd": 2_200_000, "year": 2021, "type": "luck_case", "max_global": 499, "image": "daytona_sp3_luck.png", "category": "Гиперкары"},
    {"id": 257, "name": "Ferrari F40 LM", "price_usd": 4_000_000, "year": 1988, "type": "luck_case", "max_global": 10, "image": "f40_lm.png", "category": "Гоночные машины"},
    {"id": 258, "name": "Ferrari F8 Tributo", "price_usd": 280_000, "year": 2019, "type": "luck_case", "max_global": 4000, "image": "f8.png", "category": "Гиперкары"},
    {"id": 259, "name": "Ferrari 12Cilindri Spider", "price_usd": 400_000, "year": 2024, "type": "luck_case", "max_global": 500, "image": "12cilindri.png", "category": "Гиперкары"},
    {"id": 260, "name": "Ferrari F50", "price_usd": 2_200_000, "year": 1995, "type": "luck_case", "max_global": 349, "image": "f50.png", "category": "Гиперкары"},
    {"id": 261, "name": "Ferrari FXX Evolution", "price_usd": 2_500_000, "year": 2009, "type": "luck_case", "max_global": 30, "image": "fxx_evo.png", "category": "Трековые авто"},
    {"id": 262, "name": "Ferrari KC23", "price_usd": 3_000_000, "year": 2023, "type": "luck_case", "max_global": 1, "image": "kc23.png", "category": "Концепты"},
    {"id": 263, "name": "Lamborghini Countach LPI 800-4", "price_usd": 2_600_000, "year": 2021, "type": "luck_case", "max_global": 112, "image": "countach_lpi.png", "category": "Гиперкары"},
    {"id": 264, "name": "Lamborghini Murciélago LP 670-4 SuperVeloce", "price_usd": 500_000, "year": 2009, "type": "luck_case", "max_global": 350, "image": "murcielago_sv.png", "category": "Гиперкары"},
    {"id": 265, "name": "Lamborghini Countach 1989", "price_usd": 800_000, "year": 1989, "type": "luck_case", "max_global": 10, "image": "countach_89.png", "category": "Ретро Иконы"},
    {"id": 266, "name": "Lamborghini Aventador S LP 740-4", "price_usd": 500_000, "year": 2016, "type": "luck_case", "max_global": 1000, "image": "aventador_s.png", "category": "Гиперкары"},
    {"id": 267, "name": "Lamborghini Veneno Roadster", "price_usd": 8_000_000, "year": 2014, "type": "luck_case", "max_global": 9, "image": "veneno_roadster.png", "category": "Гиперкары"},
    {"id": 268, "name": "Lamborghini Sián FKP 37 Ad Personam", "price_usd": 4_000_000, "year": 2019, "type": "luck_case", "max_global": 1, "image": "sian_adp.png", "category": "Гиперкары"},
    {"id": 269, "name": "Lamborghini Huracán STO", "price_usd": 350_000, "year": 2021, "type": "luck_case", "max_global": 1000, "image": "huracan_sto.png", "category": "Трековые авто"},
    {"id": 270, "name": "Lamborghini SC63 LMDh", "price_usd": 1_500_000, "year": 2023, "type": "luck_case", "max_global": 1, "image": "sc63.png", "category": "Гоночные машины"},
    {"id": 271, "name": "Apollo Intensa Emozione Orange Dragon", "price_usd": 7_000_000, "year": 2018, "type": "luck_case", "max_global": 2, "image": "apollo_orange.png", "category": "Гиперкары"},
    {"id": 272, "name": "Apollo Intensa Emozione", "price_usd": 3_000_000, "year": 2018, "type": "luck_case", "max_global": 10, "image": "apollo_ie_luck.png", "category": "Гиперкары"},
    {"id": 273, "name": "Apollo Project Evo", "price_usd": 3_500_000, "year": 2022, "type": "luck_case", "max_global": 30, "image": "apollo_evo.png", "category": "Трековые авто"},
    {"id": 274, "name": "Pininfarina Battista Nino Farina", "price_usd": 2_500_000, "year": 2023, "type": "luck_case", "max_global": 4, "image": "battista_nino.png", "category": "Гиперкары"},
]
# main.py — БЛОК 2 (обновлённый фрагмент)

TUNING_BRANDS = {
    "RuDesign": [
        {"id": 301, "name": "Bugatti Chiron Super Sport 110 ANS Ettore Bugatti", "price_usd": 10_000_000, "year": 2021, "type": "tuning", "max_global": 110, "image": "chiron_110_ans.png"},
        {"id": 302, "name": "Bugatti Tourbillon Equipe Porcelainé", "price_usd": 6_700_000, "year": 2024, "type": "tuning", "max_global": 250, "image": "tourbillon_porcelain.png"},
        {"id": 303, "name": "Pagani Huayra RPL", "price_usd": 4_000_000, "year": 2023, "type": "tuning", "max_global": 15, "image": "huayra_rpl.png"},
        {"id": 304, "name": "Pagani Huayra Barchetta Codalunga", "price_usd": 12_000_000, "year": 2021, "type": "tuning", "max_global": 5, "image": "barchetta_codalunga.png"},
        {"id": 305, "name": "Pagani Utopia Authentić", "price_usd": 4_000_000, "year": 2022, "type": "tuning", "max_global": 99, "image": "utopia_authentic.png"},
        {"id": 306, "name": "Pagani Huayra Epitome Cabriolét", "price_usd": 12_000_000, "year": 2023, "type": "tuning", "max_global": 8, "image": "epitome_cabriolet.png"},
        {"id": 307, "name": "Pagani Huayra BC: Imola Cabriolét", "price_usd": 8_200_000, "year": 2022, "type": "tuning", "max_global": 8, "image": "imola_cabriolet.png"},
        {"id": 308, "name": "Mercedes-Hispano G-Klasse Sagrera", "price_usd": 970_000, "year": 2023, "type": "tuning", "max_global": 50, "image": "g_klasse_sagrera.png"},
        {"id": 309, "name": "Mercedes-Benz Hispano-Suiza", "price_usd": 1_000_000, "year": 2022, "type": "tuning", "max_global": 20, "image": "mercedes_hispano.png"},
        {"id": 310, "name": "Mercedes-Hispano G-Carmen Two-door", "price_usd": 1_100_000, "year": 2023, "type": "tuning", "max_global": 30, "image": "g_carmen.png"},
        {"id": 311, "name": "Aspark Owl LongTail", "price_usd": 3_700_000, "year": 2023, "type": "tuning", "max_global": 7, "image": "owl_longtail.png"},
        {"id": 312, "name": "Saleen S7 BetMobili *2025 Enjoy Halloween Two", "price_usd": 9_000_000, "year": 2025, "type": "tuning", "max_global": 1, "image": "saleen_halloween.png"},
        {"id": 313, "name": "Brabham BT62 Xtreme Modema", "price_usd": 2_000_000, "year": 2023, "type": "tuning", "max_global": 20, "image": "bt62_xtreme.png"},
    ],
    
    "Mansory": [
        {"id": 314, "name": "Mansory Ford GT Le Mansory", "price_usd": 800_000, "year": 2018, "type": "tuning", "max_global": 10, "image": "ford_gt_mansory.png"},
        {"id": 315, "name": "Mansory Torofeo", "price_usd": 450_000, "year": 2020, "type": "tuning", "max_global": 100, "image": "torofeo.png"},
        {"id": 316, "name": "Mansory Carbonado EVO Roadster", "price_usd": 500_000, "year": 2021, "type": "tuning", "max_global": 150, "image": "carbonado_evo.png"},
        {"id": 317, "name": "Mansory Venatus", "price_usd": 400_000, "year": 2019, "type": "tuning", "max_global": 200, "image": "venatus.png"},
        {"id": 318, "name": "Mansory Cabrera", "price_usd": 350_000, "year": 2018, "type": "tuning", "max_global": 250, "image": "cabrera.png"},
        {"id": 319, "name": "Mansory Cyrus", "price_usd": 380_000, "year": 2020, "type": "tuning", "max_global": 180, "image": "cyrus.png"},
        {"id": 320, "name": "Mansory Centuria", "price_usd": 420_000, "year": 2021, "type": "tuning", "max_global": 120, "image": "centuria.png"},
        {"id": 321, "name": "Mansory Vivre", "price_usd": 300_000, "year": 2019, "type": "tuning", "max_global": 300, "image": "vivre.png"},
    ],
    
    "PAGANsky DesignACHE": [
        {"id": 322, "name": "Ford GT 'LeMen'", "price_usd": 2_000_000, "year": 2022, "type": "tuning", "max_global": 25, "image": "ford_gt_lemen.png"},
        {"id": 323, "name": "Pagani Huayra Codalunga Speedster PAGANskeì Preparation", "price_usd": 9_600_000, "year": 2022, "type": "tuning", "max_global": 5, "image": "codalunga_speedster.png"},
        {"id": 324, "name": "Porsche 918 Co'up (Coupe) SFP", "price_usd": 3_100_000, "year": 2021, "type": "tuning", "max_global": 10, "image": "porsche_918_sfp.png"},
        {"id": 325, "name": "Rolls Royce Boattail Jonckheere Aerodynamic Coupe 'Moderna'", "price_usd": 52_920_000, "year": 2023, "type": "tuning", "max_global": 1, "image": "boattail_moderna.png"},
        {"id": 326, "name": "Mercedes-AMG Project: One/two Landalet", "price_usd": 4_300_000, "year": 2023, "type": "tuning", "max_global": 50, "image": "project_one_landalet.png"},
        {"id": 327, "name": "Ferrari F80 GEMBALLA MIG U-3", "price_usd": 8_000_000, "year": 2024, "type": "tuning", "max_global": 3, "image": "f80_gemballa.png"},
        {"id": 328, "name": "Ferrari F80 APERTA LA SWEDEN", "price_usd": 5_000_000, "year": 2024, "type": "tuning", "max_global": 5, "image": "f80_aperta.png"},
        {"id": 329, "name": "McLaren Senna F1 'Champion Ayrton Senna'", "price_usd": 3_000_000, "year": 2021, "type": "tuning", "max_global": 10, "image": "senna_f1_champion.png"},
    ],
    
    "Zagato": [
        {"id": 330, "name": "Aston Martin DB4 GT Zagato", "price_usd": 7_000_000, "year": 1961, "type": "tuning", "max_global": 19, "image": "db4_zagato.png"},
        {"id": 331, "name": "Aston Martin DB7 Zagato", "price_usd": 600_000, "year": 2002, "type": "tuning", "max_global": 99, "image": "db7_zagato.png"},
        {"id": 332, "name": "Aston Martin V12 Zagato", "price_usd": 500_000, "year": 2011, "type": "tuning", "max_global": 150, "image": "v12_zagato.png"},
        {"id": 333, "name": "Aston Martin Vanquish Zagato", "price_usd": 1_200_000, "year": 2016, "type": "tuning", "max_global": 325, "image": "vanquish_zagato.png"},
        {"id": 334, "name": "Alfa Romeo Giulietta SZ Zagato", "price_usd": 1_000_000, "year": 1960, "type": "tuning", "max_global": 250, "image": "giulietta_sz.png"},
        {"id": 335, "name": "Alfa Romeo SZ Zagato", "price_usd": 350_000, "year": 1989, "type": "tuning", "max_global": 1000, "image": "alfa_sz.png"},
        {"id": 336, "name": "Lancia Hyena Zagato", "price_usd": 400_000, "year": 1992, "type": "tuning", "max_global": 25, "image": "lancia_hyena.png"},
        {"id": 337, "name": "Lancia Fulvia Coupe Zagato", "price_usd": 300_000, "year": 1968, "type": "tuning", "max_global": 100, "image": "fulvia_zagato.png"},
        {"id": 338, "name": "Fiat 8V Zagato", "price_usd": 2_000_000, "year": 1954, "type": "tuning", "max_global": 30, "image": "fiat_8v_zagato.png"},
        {"id": 339, "name": "Maserati A6G 2000 Coupe Zagato", "price_usd": 1_500_000, "year": 1956, "type": "tuning", "max_global": 20, "image": "a6g_zagato.png"},
        {"id": 340, "name": "Maserati Biturbo Spyder Zagato", "price_usd": 200_000, "year": 1986, "type": "tuning", "max_global": 100, "image": "biturbo_zagato.png"},
        {"id": 341, "name": "Spyker C12 Zagato", "price_usd": 1_200_000, "year": 2008, "type": "tuning", "max_global": 30, "image": "spyker_c12_zagato.png"},
        {"id": 342, "name": "Lamborghini P147 Zagato", "price_usd": 1_800_000, "year": 2020, "type": "tuning", "max_global": 10, "image": "p147_zagato.png"},
    ],
    
    "ItalDesign": [
        {"id": 343, "name": "Italdesign Parcour", "price_usd": 1_300_000, "year": 2013, "type": "tuning", "max_global": 1, "image": "parcour.png"},
        {"id": 344, "name": "Italdesign Zerouno", "price_usd": 1_600_000, "year": 2017, "type": "tuning", "max_global": 5, "image": "zerouno.png"},
    ],
    
    "Gemballa": [
        {"id": 345, "name": "Ferrari Enzo Gemballa MIG U-1", "price_usd": 4_000_000, "year": 2003, "type": "tuning", "max_global": 1, "image": "enzo_gemballa_mig.png"},
        {"id": 346, "name": "Porsche Carrera GT Mirage", "price_usd": 1_200_000, "year": 2005, "type": "tuning", "max_global": 25, "image": "carrera_gt_mirage.png"},
        {"id": 347, "name": "Ferrari Testarossa Gemballa", "price_usd": 800_000, "year": 1985, "type": "tuning", "max_global": 10, "image": "testarossa_gemballa.png"},
    ],
    
    "RUF": [
        {"id": 348, "name": "RUF CTR Yellowbird", "price_usd": 1_000_000, "year": 1987, "type": "tuning", "max_global": 25, "image": "ctr_yellowbird.png"},
        {"id": 349, "name": "RUF CTR3", "price_usd": 900_000, "year": 2007, "type": "tuning", "max_global": 50, "image": "ctr3.png"},
        {"id": 350, "name": "RUF RT 12", "price_usd": 700_000, "year": 2010, "type": "tuning", "max_global": 100, "image": "rt12.png"},
        {"id": 351, "name": "RUF SCR 4.2", "price_usd": 650_000, "year": 2018, "type": "tuning", "max_global": 150, "image": "scr_42.png"},
    ],
    
    "Hennessey": [
        {"id": 352, "name": "Hennessey Venom F5", "price_usd": 2_100_000, "year": 2021, "type": "tuning", "max_global": 24, "image": "venom_f5.png"},
        {"id": 353, "name": "Hennessey Venom F5 Roadster", "price_usd": 3_000_000, "year": 2022, "type": "tuning", "max_global": 12, "image": "venom_f5_roadster.png"},
        {"id": 354, "name": "Hennessey Exorcist ZR1", "price_usd": 300_000, "year": 2018, "type": "tuning", "max_global": 100, "image": "exorcist.png"},
        {"id": 355, "name": "Hennessey Mammoth 1000 TRX", "price_usd": 250_000, "year": 2021, "type": "tuning", "max_global": 200, "image": "mammoth_trx.png"},
    ],
    
    "9FF": [
        {"id": 356, "name": "9FF GT9-R", "price_usd": 1_000_000, "year": 2008, "type": "tuning", "max_global": 20, "image": "gt9r.png"},
        {"id": 357, "name": "9FF GT9 CS", "price_usd": 900_000, "year": 2010, "type": "tuning", "max_global": 30, "image": "gt9_cs.png"},
        {"id": 358, "name": "9FF T9", "price_usd": 500_000, "year": 2006, "type": "tuning", "max_global": 50, "image": "t9.png"},
        {"id": 359, "name": "9FF Carrera GTR", "price_usd": 600_000, "year": 2012, "type": "tuning", "max_global": 40, "image": "carrera_gtr.png"},
    ],
    
    "Brabus": [
        {"id": 360, "name": "Brabus Rocket 900", "price_usd": 500_000, "year": 2020, "type": "tuning", "max_global": 25, "image": "rocket_900.png"},
        {"id": 361, "name": "Brabus G900", "price_usd": 600_000, "year": 2021, "type": "tuning", "max_global": 30, "image": "g900.png"},
        {"id": 362, "name": "Brabus 850 6.0 Biturbo", "price_usd": 450_000, "year": 2019, "type": "tuning", "max_global": 100, "image": "850_biturbo.png"},
        {"id": 363, "name": "Brabus S700", "price_usd": 400_000, "year": 2022, "type": "tuning", "max_global": 120, "image": "s700.png"},
    ],
    
    "Carlex": [
        {"id": 364, "name": "Carlex DeTomaso P72", "price_usd": 1_200_000, "year": 2020, "type": "tuning", "max_global": 1, "image": "p72_carlex.png"},
        {"id": 365, "name": "Carlex DeTomaso P900", "price_usd": 2_000_000, "year": 2023, "type": "tuning", "max_global": 18, "image": "p900_carlex.png"},
        {"id": 366, "name": "Carlex SCG 003S", "price_usd": 600_000, "year": 2015, "type": "tuning", "max_global": 3, "image": "scg_003s_carlex.png"},
        {"id": 367, "name": "Carlex SCG 003 Race Car", "price_usd": 5_000_000, "year": 2016, "type": "tuning", "max_global": 2, "image": "scg_003_race_carlex.png"},
    ],
    
    "Saleen": [
        {"id": 368, "name": "Saleen S7 Twin Turbo", "price_usd": 800_000, "year": 2005, "type": "tuning", "max_global": 300, "image": "s7_twin_turbo.png"},
        {"id": 369, "name": "Saleen S1", "price_usd": 100_000, "year": 2018, "type": "tuning", "max_global": 500, "image": "s1.png"},
        {"id": 370, "name": "Saleen S5S Raptor", "price_usd": 250_000, "year": 2007, "type": "tuning", "max_global": 50, "image": "s5s_raptor.png"},
        {"id": 371, "name": "Saleen F150", "price_usd": 80_000, "year": 2020, "type": "tuning", "max_global": 1000, "image": "f150_saleen.png"},
    ],
}
# main.py — БЛОК 3: Недвижимость

REAL_ESTATE = {
    "houses": [
        {
            "id": "house_1",
            "name": "Дом The Vineyards Resort",
            "location": "Bulgaria, Aheloi",
            "price_usd": 210_000,
            "image": "vineyards_resort.jpg"
        },
        {
            "id": "house_2",
            "name": "Дом Updown Court",
            "location": "England, Windlesham",
            "price_usd": 140_000_000,
            "image": "updown_court.jpg"
        },
        {
            "id": "house_3",
            "name": "Особняк Daniel’s Lane",
            "location": "USA, NY",
            "price_usd": 100_000_000,
            "image": "daniels_lane.jpg"
        }
    ],
    "villas": [
        {
            "id": "villa_1",
            "name": "Вилла Coastlands House",
            "location": "USA, California",
            "price_usd": 2_000_000,
            "image": "coastlands_house.jpg"
        },
        {
            "id": "villa_2",
            "name": "Вилла Swiss Gold House",
            "location": "Швейцария",
            "price_usd": 12_000_000,
            "image": "swiss_gold_house.jpg"
        },
        {
            "id": "villa_3",
            "name": "Вилла Villa Leopolda",
            "location": "Франция",
            "price_usd": 506_000_000,
            "image": "villa_leopolda.jpg"
        }
    ],
    "apartments": [
        {
            "id": "apt_1",
            "name": "Квартира Yaroslavl City",
            "location": "РФ, Ярославль",
            "price_usd": 1_050_000,
            "image": "yaroslavl_city.jpg"
        },
        {
            "id": "apt_2",
            "name": "Таун-хаус Boka Place Porto Montenegro",
            "location": "Chernogoria, Tivan",
            "price_usd": 910_000,
            "image": "boka_place.jpg"
        }
    ],
    "income_property": [
        {
            "id": "income_1",
            "name": "Небоскреб Commerzbank Tower",
            "location": "Франкфурт-на-Майне, Германия",
            "price_usd": 1_200_000_000,
            "income_per_10_sec": 120_000,
            "image": "commerzbank_tower.jpg"
        },
        {
            "id": "income_2",
            "name": "Небоскреб-апартаменты Messeturm",
            "location": "Франкфурт-на-Майне, Германия",
            "price_usd": 3_700_000_000,
            "income_per_10_sec": 200_000,
            "image": "messeturm.jpg"
        },
        {
            "id": "income_3",
            "name": "Небоскреб-штабквартира Post Tower",
            "location": "Бонн, Германия",
            "price_usd": 1_800_000_000,
            "income_per_10_sec": 100_000,
            "image": "post_tower.jpg"
        },
        {
            "id": "income_4",
            "name": "Отель-небоскреб Park Inn by Radisson Berlin Alexanderplatz",
            "location": "Берлин, Германия",
            "price_usd": 3_200_000_000,
            "income_per_10_sec": 500_000,
            "image": "park_inn_berlin.jpg"
        },
        {
            "id": "income_5",
            "name": "Небоскреб Лахта-Центр",
            "location": "РФ, С.-Петербург",
            "price_usd": 2_400_000_000,
            "income_per_10_sec": 80_000,
            "image": "lahhta_center.jpg"
        },
        {
            "id": "income_6",
            "name": "ТЦ Wenge",
            "location": "РФ, Ярославль",
            "price_usd": 6_000_000,
            "income_per_10_sec": 6_000,
            "image": "wenge_mall.jpg"
        },
        {
            "id": "income_7",
            "name": "Пентхаус Antalia",
            "location": "Мумбаи",
            "price_usd": 1_000_000_000,
            "income_per_10_sec": 30_000,
            "image": "antalia_penthouse.jpg"
        }
    ]
}
# main.py — БЛОК 4: Главное меню и команды

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

async def ensure_user(user: types.User):
    """Гарантирует, что пользователь есть в БД"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO users 
            (user_id, username, display_name, currency) 
            VALUES (?, ?, ?, ?)
        """, (user.id, user.username, user.full_name, "USD"))
        await db.commit()

async def get_balance_with_income(user_id: int) -> int:
    """Возвращает баланс + доход от недвижимости (и сразу зачисляет его)"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Сначала получим текущий баланс
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return 0
            balance = row[0]

        # Рассчитаем и начислим доход от недвижимости
        total_income = 0
        now = datetime.utcnow()
        async with db.execute("""
            SELECT estate_id, last_collected FROM user_real_estate WHERE user_id = ?
        """, (user_id,)) as cursor:
            rows = await cursor.fetchall()

        for estate_id, last_collected_str in rows:
            estate = None
            for category in REAL_ESTATE.values():
                for item in category:
                    if item["id"] == estate_id:
                        estate = item
                        break
                if estate: break
            if not estate or "income_per_10_sec" not in estate:
                continue

            last_collected = datetime.fromisoformat(last_collected_str)
            seconds_passed = (now - last_collected).total_seconds()
            intervals = int(seconds_passed // 10)
            income = intervals * estate["income_per_10_sec"]
            
            if income > 0:
                total_income += income
                new_collected = last_collected + timedelta(seconds=intervals * 10)
                await db.execute("""
                    UPDATE user_real_estate SET last_collected = ? WHERE user_id = ? AND estate_id = ?
                """, (new_collected.isoformat(), user_id, estate_id))

        # Обновим баланс и real_estate_income
        new_balance = balance + total_income
        await db.execute("""
            UPDATE users SET balance = ?, real_estate_income = ? WHERE user_id = ?
        """, (new_balance, total_income, user_id))
        await db.commit()
        return new_balance

def format_price(price: int, currency: str) -> str:
    """Форматирует цену в выбранной валюте"""
    if currency == "RUB":
        return f"{format_number(int(price * USD_TO_RUB))} ₽"
    elif currency == "EUR":
        return f"{format_number(int(price * USD_TO_EUR))} €"
    else:
        return f"${format_number(price)}"

# ========== ГЛАВНОЕ МЕНЮ ==========

async def main_menu(message: Message):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🚗 Автосалон", callback_data="menu_salon")
    keyboard.button(text="💰 Мои средства", callback_data="menu_balance")
    keyboard.button(text="🚘 Мои машины", callback_data="menu_my_cars_0")
    keyboard.button(text="🎁 Выбить машину", callback_data="drop_car")
    keyboard.button(text="✨ Акция удачи", callback_data="menu_luck_case")
    keyboard.button(text="🔧 Тюнинг ателье", callback_data="menu_tuning")
    keyboard.button(text="🏠 Недвижимость", callback_data="menu_realestate")
    keyboard.button(text="🏆 Лидеры", callback_data="menu_leaders")
    keyboard.button(text="🌍 Все машины", callback_data="menu_all_cars_0")
    keyboard.button(text="⚙️ Ещё авто", callback_data="menu_extra")
    keyboard.button(text="🧰 Консоль", callback_data="menu_console")
    keyboard.adjust(2)
    await message.answer("🚘 Добро пожаловать в Car's by RuDesign!", reply_markup=keyboard.as_markup())

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await ensure_user(message.from_user)
    await main_menu(message)

# ========== МОИ СРЕДСТВА ==========

@dp.callback_query(F.data == "menu_balance")
async def menu_balance(callback: CallbackQuery):
    user_id = callback.from_user.id
    await ensure_user(callback.from_user)
    balance = await get_balance_with_income(user_id)
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT currency, real_estate_income FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            currency = row[0]
            real_estate_income = row[1] or 0

    text = f"💰 Ваш баланс: {format_price(balance, currency)}\n"
    if real_estate_income > 0:
        text += f"📈 Заработано на недвижимости: {format_price(real_estate_income, currency)}\n"
    text += "\nВыберите действие:"

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="💱 Отображение валюты", callback_data="menu_currency")
    keyboard.button(text="⬅️ Назад", callback_data="back_to_main")
    await callback.message.edit_text(text, reply_markup=keyboard.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "menu_currency")
async def menu_currency(callback: CallbackQuery):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="$ USD", callback_data="set_currency_USD")
    keyboard.button(text="₽ RUB", callback_data="set_currency_RUB")
    keyboard.button(text="€ EUR", callback_data="set_currency_EUR")
    keyboard.button(text="⬅️ Назад", callback_data="menu_balance")
    keyboard.adjust(3)
    await callback.message.edit_text("Выберите валюту для отображения:", reply_markup=keyboard.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("set_currency_"))
async def set_currency(callback: CallbackQuery):
    currency = callback.data.split("_")[2]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET currency = ? WHERE user_id = ?", (currency, callback.from_user.id))
        await db.commit()
    await callback.answer(f"Валюта установлена: {currency}")
    await menu_balance(callback)

# ========== АВТОСАЛОН (ПАГИНАЦИЯ) ==========

SALON_SUBGROUPS = ["Гиперкары и роскошь", "Обычное"]

@dp.callback_query(F.data == "menu_salon")
async def menu_salon(callback: CallbackQuery):
    keyboard = InlineKeyboardBuilder()
    for i, group in enumerate(SALON_SUBGROUPS):
        keyboard.button(text=group, callback_data=f"salon_group_{i}")
    keyboard.button(text="⬅️ Назад", callback_data="back_to_main")
    keyboard.adjust(1)
    await callback.message.edit_text("Выберите категорию:", reply_markup=keyboard.as_markup())
    await callback.answer()

def get_salon_cars(group_index: int) -> list:
    if group_index == 0:  # Гиперкары
        return SALON_CARS[:15]
    else:  # Обычное
        return SALON_CARS[15:30]

@dp.callback_query(F.data.startswith("salon_group_"))
async def salon_group(callback: CallbackQuery):
    group_index = int(callback.data.split("_")[2])
    cars = get_salon_cars(group_index)
    if not cars:
        await callback.answer("Категория пуста", show_alert=True)
        return
    await show_car_page(callback, cars, 0, f"salon_{group_index}", "салон")

async def show_car_page(callback: CallbackQuery, cars: list, page: int, prefix: str, source_type: str):
    car = cars[page]
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT currency FROM users WHERE user_id = ?", (callback.from_user.id,)) as cursor:
            row = await cursor.fetchone()
            currency = row[0] if row else "USD"

    text = (
        f"🚘 {car['name']}\n"
        f"📅 Год: {car['year']}\n"
        f"💰 Цена: {format_price(car['price_usd'], currency)}\n"
        f"🔢 Лимит: {car['max_global']} шт. в мире"
    )

    keyboard = InlineKeyboardBuilder()
    if page > 0:
        keyboard.button(text="⬅️ Назад", callback_data=f"{prefix}_{page-1}")
    keyboard.button(text="🛒 Купить", callback_data=f"buy_{source_type}_{car['id']}")
    if page < len(cars) - 1:
        keyboard.button(text="Дальше ➡️", callback_data=f"{prefix}_{page+1}")
    keyboard.button(text="↩️ Меню", callback_data="menu_salon")
    keyboard.adjust(2 if (page > 0 and page < len(cars)-1) else 1, 1, 1)

    await callback.message.edit_text(text, reply_markup=keyboard.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("salon_0_") | F.data.startswith("salon_1_"))
async def salon_page(callback: CallbackQuery):
    prefix = "_".join(callback.data.split("_")[:2])  # "salon_0" или "salon_1"
    page = int(callback.data.split("_")[2])
    group_index = int(prefix.split("_")[1])
    cars = get_salon_cars(group_index)
    await show_car_page(callback, cars, page, prefix, "salon")

# ========== ПОКУПКА МАШИНЫ ==========

@dp.callback_query(F.data.startswith("buy_salon_"))
async def buy_salon_car(callback: CallbackQuery):
    car_id = int(callback.data.split("_")[2])
    car = next((c for c in SALON_CARS if c["id"] == car_id), None)
    if not car:
        await callback.answer("Машина не найдена", show_alert=True)
        return

    user_id = callback.from_user.id
    balance = await get_balance_with_income(user_id)
    
    if balance < car["price_usd"]:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return

    # Проверим глобальный лимит
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT issued_count FROM global_car_counts WHERE car_id = ?", (car_id,)) as cursor:
            row = await cursor.fetchone()
            issued = row[0] if row else 0

        if issued >= car["max_global"]:
            await callback.answer("❌ Машина больше не доступна — лимит исчерпан!", show_alert=True)
            return

        # Списываем деньги
        new_balance = balance - car["price_usd"]
        await db.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))

        # Проверим, есть ли уже у игрока эта машина
        async with db.execute("SELECT 1 FROM user_cars WHERE user_id = ? AND car_id = ?", (user_id, car_id)) as cursor:
            is_duplicate = await cursor.fetchone() is not None

        # Добавим в коллекцию
        await db.execute("""
            INSERT INTO user_cars (user_id, car_id, is_duplicate, source, acquired_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, car_id, is_duplicate, "Куплена", now_iso()))

        # Обновим глобальный счётчик
        await db.execute("""
            INSERT INTO global_car_counts (car_id, issued_count)
            VALUES (?, 1)
            ON CONFLICT(car_id) DO UPDATE SET issued_count = issued_count + 1
        """)

        await db.commit()

    await callback.answer("✅ Покупка совершена! Машина добавлена в коллекцию.", show_alert=True)
    await main_menu(callback.message)

# ========== КНОПКА НАЗАД В ГЛАВНОЕ МЕНЮ ==========

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    await main_menu(callback.message)
    await callback.answer()

# Продолжение в следующем сообщении из-за длины...
# main.py — БЛОК 4 (продолжение)

# ========== МОИ МАШИНЫ (ПАГИНАЦИЯ + ПОКРАСКА) ==========

@dp.callback_query(F.data.startswith("menu_my_cars_"))
async def menu_my_cars(callback: CallbackQuery):
    page = int(callback.data.split("_")[3])
    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT car_id, is_duplicate, source, color FROM user_cars WHERE user_id = ?
        """, (user_id,)) as cursor:
            cars = await cursor.fetchall()

    if not cars:
        await callback.answer("У вас пока нет машин!", show_alert=True)
        await main_menu(callback.message)
        return

    cars_per_page = 1
    total_pages = len(cars)
    if page >= total_pages:
        page = 0

    car_id, is_duplicate, source, color = cars[page]

    # Найдём данные машины
    car = next((c for c in ALL_CARS if c["id"] == car_id), None)
    if not car:
        car = {"name": "Неизвестная машина", "year": "???", "price_usd": 0}

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT currency FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            currency = row[0] if row else "USD"

    duplicate_text = " (Дубликат)" if is_duplicate else ""
    source_text = source or "Неизвестно"
    color_text = f"\n🎨 Цвет: {color}" if color and color != "Стандартный" else ""

    text = (
        f"🚘 {car['name']}{duplicate_text}\n"
        f"📅 Год: {car['year']}\n"
        f"💰 Цена: {format_price(car['price_usd'], currency)}\n"
        f"📌 Источник: {source_text}"
        f"{color_text}"
    )

    keyboard = InlineKeyboardBuilder()
    if page > 0:
        keyboard.button(text="⬅️ Назад", callback_data=f"menu_my_cars_{page-1}")
    
    # Кнопка "Обменять" всегда доступна
    keyboard.button(text="🔄 Обменять", callback_data=f"exchange_start_{car_id}")
    
    # Кнопка "Выбрать цвет" — только для салона и тюнинга
    if source in ("Куплена", "Тюнинг"):
        keyboard.button(text="🎨 Выбрать цвет", callback_data=f"paint_{car_id}")

    if page < total_pages - 1:
        keyboard.button(text="Дальше ➡️", callback_data=f"menu_my_cars_{page+1}")
    
    keyboard.button(text="↩️ Меню", callback_data="back_to_main")
    keyboard.adjust(2 if (page > 0 and page < total_pages - 1) else 1, 1, 1)

    await callback.message.edit_text(text, reply_markup=keyboard.as_markup())
    await callback.answer()

# ========== ПОКРАСКА ==========

@dp.callback_query(F.data.startswith("paint_"))
async def paint_menu(callback: CallbackQuery):
    car_id = int(callback.data.split("_")[1])
    keyboard = InlineKeyboardBuilder()
    for color in PAINT_COLORS:
        keyboard.button(text=color, callback_data=f"set_color_{car_id}_{color}")
    keyboard.button(text="↩️ Назад", callback_data=f"menu_my_cars_0")
    keyboard.adjust(2)
    await callback.message.edit_text("Выберите цвет:", reply_markup=keyboard.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("set_color_"))
async def set_color(callback: CallbackQuery):
    parts = callback.data.split("_")
    car_id = int(parts[2])
    color = "_".join(parts[3:])  # на случай цветов с пробелами

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE user_cars SET color = ? WHERE user_id = ? AND car_id = ?
        """, (color, callback.from_user.id, car_id))
        await db.commit()

    await callback.answer(f"✅ Цвет изменён на: {color}")
    await menu_my_cars(callback)

# ========== АКЦИЯ УДАЧИ (С ПОДКАТЕГОРИЯМИ) ==========

LUCK_CATEGORIES = ["Гиперкары", "Трековые авто", "Концепты", "Обычные машины", "Гоночные машины", "Необычные", "Ретро Иконы"]

def get_luck_cars_by_category(category: str) -> list:
    return [car for car in LUCK_CASE_CARS if car.get("category") == category]

@dp.callback_query(F.data == "menu_luck_case")
async def menu_luck_case(callback: CallbackQuery):
    # Проверим таймер (1 раз в 24 часа)
    user_id = callback.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT last_luck_case FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            last_used = row[0] if row and row[0] else None

    if last_used:
        last_used_dt = datetime.fromisoformat(last_used)
        if datetime.utcnow() - last_used_dt < timedelta(hours=24):
            await callback.answer("⏳ Акция удачи доступна раз в 24 часа!", show_alert=True)
            return

    keyboard = InlineKeyboardBuilder()
    for cat in LUCK_CATEGORIES:
        keyboard.button(text=cat, callback_data=f"luck_cat_{cat}")
    keyboard.button(text="↩️ Меню", callback_data="back_to_main")
    keyboard.adjust(2)
    await callback.message.edit_text("Выберите категорию для Акции удачи:", reply_markup=keyboard.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("luck_cat_"))
async def luck_category_select(callback: CallbackQuery):
    category = callback.data.replace("luck_cat_", "")
    cars = get_luck_cars_by_category(category)
    if not cars:
        await callback.answer("В этой категории нет машин!", show_alert=True)
        return

    # Выберем случайную машину
    import random
    car = random.choice(cars)

    # Проверим глобальный лимит
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT issued_count FROM global_car_counts WHERE car_id = ?", (car["id"],)) as cursor:
            row = await cursor.fetchone()
            issued = row[0] if row else 0

        if issued >= car["max_global"]:
            await callback.answer("❌ Эта машина больше не доступна — лимит исчерпан!", show_alert=True)
            return

        # Проверим, есть ли уже у игрока
        user_id = callback.from_user.id
        async with db.execute("SELECT 1 FROM user_cars WHERE user_id = ? AND car_id = ?", (user_id, car["id"])) as cursor:
            is_duplicate = await cursor.fetchone() is not None

        if is_duplicate:
            await callback.answer("❌ У вас уже есть эта машина! В Акции удачи дубликаты запрещены.", show_alert=True)
            return

        # Добавим машину и доход
        balance = await get_balance_with_income(user_id)
        new_balance = balance + car["price_usd"]
        await db.execute("UPDATE users SET balance = ?, last_luck_case = ? WHERE user_id = ?", (new_balance, now_iso(), user_id))
        await db.execute("""
            INSERT INTO user_cars (user_id, car_id, is_duplicate, source, acquired_at)
            VALUES (?, ?, 0, ?, ?)
        """, (user_id, car["id"], "Акция удачи", now_iso()))
        await db.execute("""
            INSERT INTO global_car_counts (car_id, issued_count)
            VALUES (?, 1)
            ON CONFLICT(car_id) DO UPDATE SET issued_count = issued_count + 1
        """)
        await db.commit()

    await callback.answer(f"🎉 Поздравляем! Вы получили: {car['name']} за ${format_number(car['price_usd'])}!", show_alert=True)
    await main_menu(callback.message)

# ========== ТЮНИНГ АТЕЛЬЕ ==========

TUNING_ATELIERS = list(TUNING_BRANDS.keys())

@dp.callback_query(F.data == "menu_tuning")
async def menu_tuning(callback: CallbackQuery):
    keyboard = InlineKeyboardBuilder()
    for atelier in TUNING_ATELIERS:
        keyboard.button(text=atelier, callback_data=f"tuning_atelier_{atelier}")
    keyboard.button(text="🎁 Новый клиент", callback_data="new_client_case")
    keyboard.button(text="↩️ Меню", callback_data="back_to_main")
    keyboard.adjust(2)
    await callback.message.edit_text("Выберите ателье:", reply_markup=keyboard.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("tuning_atelier_"))
async def tuning_atelier(callback: CallbackQuery):
    atelier = callback.data.replace("tuning_atelier_", "")
    cars = TUNING_BRANDS.get(atelier, [])
    if not cars:
        await callback.answer("Ателье временно пусто", show_alert=True)
        return

    # Покажем первую машину (можно добавить пагинацию, но для краткости — сразу выбор)
    car = cars[0]
    await show_tuning_car(callback, atelier, 0)

async def show_tuning_car(callback: CallbackQuery, atelier: str, page: int):
    cars = TUNING_BRANDS[atelier]
    car = cars[page]
    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT currency FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            currency = row[0] if row else "USD"

    text = (
        f"🔧 {car['name']} от {atelier}\n"
        f"📅 Год: {car['year']}\n"
        f"💰 Цена: {format_price(car['price_usd'], currency)}\n"
        f"🔢 Лимит: {car['max_global']} шт."
    )

    keyboard = InlineKeyboardBuilder()
    if page > 0:
        keyboard.button(text="⬅️ Назад", callback_data=f"tuning_page_{atelier}_{page-1}")
    keyboard.button(text="🛒 Купить", callback_data=f"buy_tuning_{car['id']}")
    if page < len(cars) - 1:
        keyboard.button(text="Дальше ➡️", callback_data=f"tuning_page_{atelier}_{page+1}")
    keyboard.button(text="↩️ Назад", callback_data="menu_tuning")
    keyboard.adjust(2 if (page > 0 and page < len(cars)-1) else 1, 1, 1)

    await callback.message.edit_text(text, reply_markup=keyboard.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("tuning_page_"))
async def tuning_page(callback: CallbackQuery):
    parts = callback.data.split("_")
    atelier = parts[2]
    page = int(parts[3])
    await show_tuning_car(callback, atelier, page)

@dp.callback_query(F.data.startswith("buy_tuning_"))
async def buy_tuning_car(callback: CallbackQuery):
    car_id = int(callback.data.split("_")[2])
    # Найдём машину в любом ателье
    car = None
    for brand_cars in TUNING_BRANDS.values():
        for c in brand_cars:
            if c["id"] == car_id:
                car = c
                break
        if car: break

    if not car:
        await callback.answer("Машина не найдена", show_alert=True)
        return

    user_id = callback.from_user.id
    balance = await get_balance_with_income(user_id)
    
    if balance < car["price_usd"]:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT issued_count FROM global_car_counts WHERE car_id = ?", (car_id,)) as cursor:
            row = await cursor.fetchone()
            issued = row[0] if row else 0

        if issued >= car["max_global"]:
            await callback.answer("❌ Лимит исчерпан!", show_alert=True)
            return

        new_balance = balance - car["price_usd"]
        await db.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))

        async with db.execute("SELECT 1 FROM user_cars WHERE user_id = ? AND car_id = ?", (user_id, car_id)) as cursor:
            is_duplicate = await cursor.fetchone() is not None

        await db.execute("""
            INSERT INTO user_cars (user_id, car_id, is_duplicate, source, acquired_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, car_id, is_duplicate, "Тюнинг", now_iso()))

        await db.execute("""
            INSERT INTO global_car_counts (car_id, issued_count)
            VALUES (?, 1)
            ON CONFLICT(car_id) DO UPDATE SET issued_count = issued_count + 1
        """)
        await db.commit()

    await callback.answer("✅ Машина куплена!", show_alert=True)
    await main_menu(callback.message)

# ========== КЕЙС "НОВЫЙ КЛИЕНТ" (1 РАЗ ЗА ИГРУ) ==========

@dp.callback_query(F.data == "new_client_case")
async def new_client_case(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT used_new_client_case FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            used = row[0] if row else 0

    if used:
        await callback.answer("Вы уже использовали кейс «Новый клиент»! Он доступен только один раз.", show_alert=True)
        return

    # Выберем случайную машину из NEW_CLIENT_CASE
    import random
    car = random.choice(NEW_CLIENT_CASE)

    async with aiosqlite.connect(DB_PATH) as db:
        # Проверим лимит
        async with db.execute("SELECT issued_count FROM global_car_counts WHERE car_id = ?", (car["id"],)) as cursor:
            row = await cursor.fetchone()
            issued = row[0] if row else 0

        if issued >= car["max_global"]:
            await callback.answer("❌ Эта машина недоступна!", show_alert=True)
            return

        # Добавим
        balance = await get_balance_with_income(user_id)
        new_balance = balance + car["price_usd"]
        await db.execute("""
            UPDATE users SET balance = ?, used_new_client_case = 1 WHERE user_id = ?
        """, (new_balance, user_id))
        await db.execute("""
            INSERT INTO user_cars (user_id, car_id, is_duplicate, source, acquired_at)
            VALUES (?, ?, 0, ?, ?)
        """, (user_id, car["id"], "Новый клиент", now_iso()))
        await db.execute("""
            INSERT INTO global_car_counts (car_id, issued_count)
            VALUES (?, 1)
            ON CONFLICT(car_id) DO UPDATE SET issued_count = issued_count + 1
        """)
        await db.commit()

    await callback.answer(f"🎁 Добро пожаловать! Вы получили: {car['name']}!", show_alert=True)
    await main_menu(callback.message)

# ========== ЛИДЕРБОРД ==========

@dp.callback_query(F.data == "menu_leaders")
async def menu_leaders(callback: CallbackQuery):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT user_id, username, display_name, balance 
            FROM users 
            ORDER BY balance DESC 
            LIMIT 10
        """) as cursor:
            leaders = await cursor.fetchall()

    text = "🏆 Топ-10 самых богатых игроков:\n\n"
    for i, (user_id, username, name, balance) in enumerate(leaders, 1):
        display = f"@{username}" if username else name
        text += f"{i}. {display} — ${format_number(balance)}\n"

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="👥 Все игроки", callback_data="all_players")
    keyboard.button(text="↩️ Меню", callback_data="back_to_main")
    await callback.message.edit_text(text, reply_markup=keyboard.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "all_players")
async def all_players(callback: CallbackQuery):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT user_id, username, display_name, balance 
            FROM users 
            ORDER BY balance DESC
        """) as cursor:
            players = await cursor.fetchall()

    text = f"👥 Всего игроков: {len(players)}\n\n"
    for user_id, username, name, balance in players[:50]:  # Ограничим для читаемости
        display = f"@{username}" if username else name
        text += f"{display} — ${format_number(balance)}\n"

    if len(players) > 50:
        text += f"\n... и ещё {len(players) - 50} игроков"

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="↩️ Назад", callback_data="menu_leaders")
    await callback.message.edit_text(text, reply_markup=keyboard.as_markup())
    await callback.answer()

# ========== КОНСОЛЬ (ТОЛЬКО ДЛЯ @sky_for_pagani2) ==========

@dp.callback_query(F.data == "menu_console")
async def menu_console(callback: CallbackQuery):
    if callback.from_user.username != CREATOR_USERNAME:
        await callback.answer("🚫 Вы не создатель!", show_alert=True)
        return

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="💰 Выдать деньги", callback_data="admin_give_money")
    keyboard.button(text="🚘 Выдать машину", callback_data="admin_give_car")
    keyboard.button(text="⛔ Заблокировать", callback_data="admin_ban")
    keyboard.button(text="🗑 Аннулировать", callback_data="admin_wipe")
    keyboard.button(text="↩️ Меню", callback_data="back_to_main")
    keyboard.adjust(2)
    await callback.message.edit_text("🛠 Консоль администратора:", reply_markup=keyboard.as_markup())
    await callback.answer()

# Остальные админ-функции будут в БЛОКЕ 7

# ========== ВСЕ МАШИНЫ ==========

@dp.callback_query(F.data.startswith("menu_all_cars_"))
async def menu_all_cars(callback: CallbackQuery):
    page = int(callback.data.split("_")[3])
    total = len(ALL_CARS)
    if page >= total:
        page = 0

    car = ALL_CARS[page]
    user_id = callback.from_user.id

    # Проверим, есть ли у игрока
    has_car = False
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT 1 FROM user_cars WHERE user_id = ? AND car_id = ?", (user_id, car["id"])) as cursor:
            has_car = await cursor.fetchone() is not None

    status = "есть в твоей коллекции" if has_car else "отсутствует в коллекции"

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT currency FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            currency = row[0] if row else "USD"

    text = (
        f"🚘 {car['name']}\n"
        f"📅 Год: {car['year']}\n"
        f"💰 Цена: {format_price(car['price_usd'], currency)}\n"
        f"📦 Статус: {status}"
    )

    keyboard = InlineKeyboardBuilder()
    if page > 0:
        keyboard.button(text="⬅️ Назад", callback_data=f"menu_all_cars_{page-1}")
    if has_car:
        keyboard.button(text="💰 Продать", callback_data=f"sell_car_{car['id']}")
    if page < total - 1:
        keyboard.button(text="Дальше ➡️", callback_data=f"menu_all_cars_{page+1}")
    keyboard.button(text="↩️ Меню", callback_data="back_to_main")
    keyboard.adjust(2 if (page > 0 and page < total - 1) else 1, 1, 1)

    await callback.message.edit_text(text, reply_markup=keyboard.as_markup())
    await callback.answer()

# Продажа машин будет реализована позже (если нужно)

# Конец БЛОКА 4
# main.py — БЛОК 5: Выбить машину и промокоды

# ========== ВЫБИТЬ МАШИНУ (DROP) ==========

@dp.callback_query(F.data == "drop_car")
async def drop_car(callback: CallbackQuery):
    user_id = callback.from_user.id
    await ensure_user(callback.from_user)

    # Проверим таймер: 30 минут
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT last_drop FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            last_drop = row[0] if row and row[0] else None

    if last_drop:
        last_drop_dt = datetime.fromisoformat(last_drop)
        if datetime.utcnow() - last_drop_dt < timedelta(minutes=30):
            await callback.answer("⏳ Вы можете выбить машину раз в 30 минут!", show_alert=True)
            return

    # Выберем случайную машину из DROP_CARS
    import random
    car = random.choice(DROP_CARS)

    # Добавим машину (дубликаты РАЗРЕШЕНЫ в drop)
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверим глобальный лимит
        async with db.execute("SELECT issued_count FROM global_car_counts WHERE car_id = ?", (car["id"],)) as cursor:
            row = await cursor.fetchone()
            issued = row[0] if row else 0

        if issued >= car["max_global"]:
            # Если лимит исчерпан — попробуем другую (до 10 попыток)
            for _ in range(10):
                new_car = random.choice(DROP_CARS)
                async with db.execute("SELECT issued_count FROM global_car_counts WHERE car_id = ?", (new_car["id"],)) as cursor:
                    row2 = await cursor.fetchone()
                    issued2 = row2[0] if row2 else 0
                if issued2 < new_car["max_global"]:
                    car = new_car
                    break
            else:
                await callback.answer("❌ Сейчас нет доступных машин для выпадения!", show_alert=True)
                return

        # Проверим, есть ли уже у игрока (для отметки дубликата)
        async with db.execute("SELECT 1 FROM user_cars WHERE user_id = ? AND car_id = ?", (user_id, car["id"])) as cursor:
            is_duplicate = await cursor.fetchone() is not None

        # Начислим цену к балансу
        balance = await get_balance_with_income(user_id)
        new_balance = balance + car["price_usd"]
        await db.execute("UPDATE users SET balance = ?, last_drop = ? WHERE user_id = ?", (new_balance, now_iso(), user_id))
        await db.execute("""
            INSERT INTO user_cars (user_id, car_id, is_duplicate, source, acquired_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, car["id"], is_duplicate, "Выпала", now_iso()))
        await db.execute("""
            INSERT INTO global_car_counts (car_id, issued_count)
            VALUES (?, 1)
            ON CONFLICT(car_id) DO UPDATE SET issued_count = issued_count + 1
        """)
        await db.commit()

    status = " (дубликат)" if is_duplicate else ""
    await callback.answer(f"🎁 Вы выбили: {car['name']}{status} (+${format_number(car['price_usd'])})!", show_alert=True)
    await main_menu(callback.message)

# ========== ПРОМОКОДЫ ==========

@dp.message(Command("promo"))
async def cmd_promo(message: Message):
    user_id = message.from_user.id
    await ensure_user(message.from_user)
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Используйте: /promo <код>")
        return

    promo_code = args[1]
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return

        # Проверим, использован ли уже
        promo_flag = None
        reward = 0
        extra_drops = 0

        if promo_code == "test":
            if row[11]:  # promo_test_used
                await message.answer("❌ Промокод уже активирован!")
                return
            promo_flag = "promo_test_used"
            reward = 1_200_000_000
        elif promo_code == "test2":
            if row[12]:  # promo_test2_used
                await message.answer("❌ Промокод уже активирован!")
                return
            promo_flag = "promo_test2_used"
            reward = 150_000_000
        elif promo_code == "BT":
            if row[13]:  # promo_bt_used
                await message.answer("❌ Промокод уже активирован!")
                return
            promo_flag = "promo_bt_used"
            reward = 20_000_000
        elif promo_code == "BetaTest":
            if row[14]:  # promo_betatest_used
                await message.answer("❌ Промокод уже активирован!")
                return
            promo_flag = "promo_betatest_used"
            extra_drops = 5  # даёт 5 бесплатных кейсов "Выбить машину"
        else:
            await message.answer("❌ Неизвестный промокод!")
            return

        # Начислим награду
        if reward > 0:
            balance = await get_balance_with_income(user_id)
            new_balance = balance + reward
            await db.execute(f"UPDATE users SET balance = ?, {promo_flag} = 1 WHERE user_id = ?", (new_balance, user_id))
            await db.commit()
            await message.answer(f"✅ Промокод активирован! Получено ${format_number(reward)}")
        elif extra_drops > 0:
            # Для BetaTest — просто даём флаг, а обработку сделаем при нажатии "Выбить машину"
            await db.execute(f"UPDATE users SET {promo_flag} = 1 WHERE user_id = ?", (user_id,))
            await db.commit()
            await message.answer("✅ Промокод BetaTest активирован! Теперь у вас 5 бесплатных попыток 'Выбить машину'.")

# ========== МОДИФИКАЦИЯ DROP ДЛЯ BETA TEST ==========

# Обновим функцию drop_car, чтобы учитывать BetaTest
# (замените старую функцию drop_car на эту)

@dp.callback_query(F.data == "drop_car")
async def drop_car(callback: CallbackQuery):
    user_id = callback.from_user.id
    await ensure_user(callback.from_user)

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT last_drop, promo_betatest_used, balance 
            FROM users WHERE user_id = ?
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return
            last_drop, has_beta, balance = row

    # Проверим: если есть BetaTest — пропускаем таймер
    if not has_beta:
        if last_drop:
            last_drop_dt = datetime.fromisoformat(last_drop)
            if datetime.utcnow() - last_drop_dt < timedelta(minutes=30):
                await callback.answer("⏳ Вы можете выбить машину раз в 30 минут!", show_alert=True)
                return

    import random
    car = random.choice(DROP_CARS)

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT issued_count FROM global_car_counts WHERE car_id = ?", (car["id"],)) as cursor:
            row = await cursor.fetchone()
            issued = row[0] if row else 0

        if issued >= car["max_global"]:
            for _ in range(10):
                new_car = random.choice(DROP_CARS)
                async with db.execute("SELECT issued_count FROM global_car_counts WHERE car_id = ?", (new_car["id"],)) as cursor:
                    row2 = await cursor.fetchone()
                    issued2 = row2[0] if row2 else 0
                if issued2 < new_car["max_global"]:
                    car = new_car
                    break
            else:
                await callback.answer("❌ Сейчас нет доступных машин!", show_alert=True)
                return

        async with db.execute("SELECT 1 FROM user_cars WHERE user_id = ? AND car_id = ?", (user_id, car["id"])) as cursor:
            is_duplicate = await cursor.fetchone() is not None

        # Начислим
        new_balance = balance + car["price_usd"]
        await db.execute("UPDATE users SET balance = ?, last_drop = ? WHERE user_id = ?", (new_balance, now_iso(), user_id))
        await db.execute("""
            INSERT INTO user_cars (user_id, car_id, is_duplicate, source, acquired_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, car["id"], is_duplicate, "Выпала", now_iso()))
        await db.execute("""
            INSERT INTO global_car_counts (car_id, issued_count)
            VALUES (?, 1)
            ON CONFLICT(car_id) DO UPDATE SET issued_count = issued_count + 1
        """)
        await db.commit()

    status = " (дубликат)" if is_duplicate else ""
    await callback.answer(f"🎁 Вы выбили: {car['name']}{status} (+${format_number(car['price_usd'])})!", show_alert=True)
    await main_menu(callback.message)
  # main.py — БЛОК 6: Обмен машинами

# ========== FSM STATES ==========

class ExchangeStates(StatesGroup):
    waiting_for_partner = State()
    waiting_for_car_selection = State()
    waiting_for_confirmation = State()

# ========== КНОПКА "ОБМЕНЯТЬ" ИЗ МОИХ МАШИН ==========

@dp.callback_query(F.data.startswith("exchange_start_"))
async def exchange_start(callback: CallbackQuery, state: FSMContext):
    car_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id

    # Проверим, есть ли у игрока эта машина
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT 1 FROM user_cars WHERE user_id = ? AND car_id = ?", (user_id, car_id)) as cursor:
            if not await cursor.fetchone():
                await callback.answer("❌ У вас нет этой машины!", show_alert=True)
                return

    await state.update_data(car_id=car_id, initiator_id=user_id)
    await state.set_state(ExchangeStates.waiting_for_partner)
    
    await callback.message.edit_text(
        "🔄 Введите @username или имя игрока, с которым хотите обменяться:"
    )
    await callback.answer()

# ========== ВВОД ИМЕНИ ПАРТНЁРА ==========

@dp.message(ExchangeStates.waiting_for_partner)
async def process_partner(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пожалуйста, введите имя или @username.")
        return

    partner_identifier = message.text.strip()
    if partner_identifier.startswith("@"):
        partner_identifier = partner_identifier[1:]

    # Найдём партнёра в БД
    partner_id = None
    partner_name = None
    async with aiosqlite.connect(DB_PATH) as db:
        # Сначала по username
        async with db.execute("SELECT user_id, display_name FROM users WHERE username = ?", (partner_identifier,)) as cursor:
            row = await cursor.fetchone()
            if row:
                partner_id, partner_name = row
            else:
                # Потом по display_name
                async with db.execute("SELECT user_id, display_name FROM users WHERE display_name = ?", (partner_identifier,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        partner_id, partner_name = row

    if not partner_id:
        await message.answer("❌ Игрок не найден. Убедитесь, что он заходил в бота.")
        return

    if partner_id == message.from_user.id:
        await message.answer("❌ Нельзя обмениваться с самим собой!")
        return

    data = await state.get_data()
    car_id = data["car_id"]
    car = next((c for c in ALL_CARS if c["id"] == car_id), None)
    if not car:
        await message.answer("❌ Ошибка: машина не найдена.")
        await state.clear()
        return

    await state.update_data(partner_id=partner_id, partner_name=partner_name)
    await state.set_state(ExchangeStates.waiting_for_car_selection)

    # Получим список машин партнёра
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT car_id FROM user_cars WHERE user_id = ?
        """, (partner_id,)) as cursor:
            partner_cars = await cursor.fetchall()

    if not partner_cars:
        await message.answer(f"❌ У игрока {partner_name} нет машин для обмена.")
        await state.clear()
        return

    # Построим клавиатуру с машинами партнёра
    keyboard = InlineKeyboardBuilder()
    for (pid,) in partner_cars[:20]:  # Ограничим для читаемости
        pcar = next((c for c in ALL_CARS if c["id"] == pid), None)
        if pcar:
            keyboard.button(text=pcar["name"][:30], callback_data=f"exchange_select_{pid}")
    keyboard.button(text="❌ Отмена", callback_data="exchange_cancel")
    keyboard.adjust(1)

    await message.answer(
        f"Выберите машину игрока {partner_name} для обмена:",
        reply_markup=keyboard.as_markup()
    )

@dp.callback_query(F.data == "exchange_cancel")
async def exchange_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Обмен отменён.")
    await callback.answer()

# ========== ВЫБОР МАШИНЫ ПАРТНЁРА ==========

@dp.callback_query(F.data.startswith("exchange_select_"))
async def exchange_select_car(callback: CallbackQuery, state: FSMContext):
    partner_car_id = int(callback.data.split("_")[2])
    data = await state.get_data()
    initiator_id = data["initiator_id"]
    partner_id = data["partner_id"]
    car_id = data["car_id"]

    # Сохраним выбор
    await state.update_data(partner_car_id=partner_car_id)
    await state.set_state(ExchangeStates.waiting_for_confirmation)

    # Получим данные машин
    initiator_car = next((c for c in ALL_CARS if c["id"] == car_id), None)
    partner_car = next((c for c in ALL_CARS if c["id"] == partner_car_id), None)

    if not initiator_car or not partner_car:
        await callback.message.edit_text("❌ Ошибка: машины не найдены.")
        await state.clear()
        return

    # Отправим запрос партнёру
    try:
        confirm_keyboard = InlineKeyboardBuilder()
        confirm_keyboard.button(text="✅ Принять", callback_data=f"exchange_confirm_{initiator_id}_{car_id}_{partner_car_id}")
        confirm_keyboard.button(text="❌ Отклонить", callback_data="exchange_reject")
        confirm_keyboard.adjust(2)

        await bot.send_message(
            partner_id,
            f"🔄 Игрок {callback.from_user.full_name} предлагает обмен:\n"
            f"Ваша машина: {partner_car['name']}\n"
            f"Его машина: {initiator_car['name']}\n\n"
            "У вас есть 5 минут на ответ!",
            reply_markup=confirm_keyboard.as_markup()
        )

        # Запустим таймер
        asyncio.create_task(exchange_timeout(partner_id, 300))  # 300 сек = 5 мин

        await callback.message.edit_text("✅ Запрос на обмен отправлен!")
        await callback.answer()
        await state.clear()

    except Exception as e:
        await callback.message.edit_text("❌ Не удалось отправить запрос. Возможно, игрок заблокировал бота.")
        await state.clear()
        await callback.answer()

# ========== ТАЙМЕР ДЛЯ ОБМЕНА ==========

async def exchange_timeout(user_id: int, seconds: int):
    await asyncio.sleep(seconds)
    try:
        await bot.send_message(user_id, "⏰ Время на обмен истекло. Запрос отменён.")
    except:
        pass  # Игнорируем, если не удалось отправить

# ========== ПОДТВЕРЖДЕНИЕ ОБМЕНА ==========

@dp.callback_query(F.data.startswith("exchange_confirm_"))
async def exchange_confirm(callback: CallbackQuery):
    parts = callback.data.split("_")
    initiator_id = int(parts[2])
    car_id = int(parts[3])
    partner_car_id = int(parts[4])
    partner_id = callback.from_user.id

    # Проверим, есть ли машины у игроков
    async with aiosqlite.connect(DB_PATH) as db:
        # У инициатора должна быть car_id
        async with db.execute("SELECT 1 FROM user_cars WHERE user_id = ? AND car_id = ?", (initiator_id, car_id)) as cursor:
            if not await cursor.fetchone():
                await callback.answer("❌ Обмен невозможен: машина уже продана или удалена.", show_alert=True)
                return

        # У партнёра должна быть partner_car_id
        async with db.execute("SELECT 1 FROM user_cars WHERE user_id = ? AND car_id = ?", (partner_id, partner_car_id)) as cursor:
            if not await cursor.fetchone():
                await callback.answer("❌ Обмен невозможен: машина уже продана или удалена.", show_alert=True)
                return

        # Удалим старые записи
        await db.execute("DELETE FROM user_cars WHERE user_id = ? AND car_id = ?", (initiator_id, car_id))
        await db.execute("DELETE FROM user_cars WHERE user_id = ? AND car_id = ?", (partner_id, partner_car_id))

        # Добавим новые
        await db.execute("""
            INSERT INTO user_cars (user_id, car_id, is_duplicate, source, acquired_at)
            VALUES (?, ?, 0, 'Обмен', ?)
        """, (partner_id, car_id, now_iso()))
        await db.execute("""
            INSERT INTO user_cars (user_id, car_id, is_duplicate, source, acquired_at)
            VALUES (?, ?, 0, 'Обмен', ?)
        """, (initiator_id, partner_car_id, now_iso()))

        await db.commit()

    await callback.message.edit_text("✅ Обмен успешно завершён!")
    try:
        await bot.send_message(initiator_id, "✅ Обмен успешно завершён!")
    except:
        pass

@dp.callback_query(F.data == "exchange_reject")
async def exchange_reject(callback: CallbackQuery):
    await callback.message.edit_text("❌ Обмен отклонён.")
    await callback.answer()
  # main.py — БЛОК 7: Админка (Консоль)

# ========== ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ: СПИСОК ИГРОКОВ ==========

async def get_all_players_kb(action: str) -> InlineKeyboardMarkup:
    """Возвращает клавиатуру со всеми игроками для админки"""
    keyboard = InlineKeyboardBuilder()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id, username, display_name FROM users") as cursor:
            players = await cursor.fetchall()
    
    for user_id, username, name in players:
        if user_id == 777000:  # Telegram Service
            continue
        display = f"@{username}" if username else name[:20]
        keyboard.button(text=display, callback_data=f"admin_{action}_{user_id}")
    keyboard.button(text="❌ Отмена", callback_data="back_to_main")
    keyboard.adjust(2)
    return keyboard.as_markup()

# ========== ВЫДАТЬ ДЕНЬГИ ==========

@dp.callback_query(F.data == "admin_give_money")
async def admin_give_money_menu(callback: CallbackQuery):
    if callback.from_user.username != CREATOR_USERNAME:
        await callback.answer("🚫 Доступ запрещён!", show_alert=True)
        return

    kb = await get_all_players_kb("give_money")
    await callback.message.edit_text("Выберите игрока для выдачи денег:", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_give_money_"))
async def admin_select_money_amount(callback: CallbackQuery):
    if callback.from_user.username != CREATOR_USERNAME:
        return

    target_id = int(callback.data.split("_")[3])
    keyboard = InlineKeyboardBuilder()
    amounts = [
        ("100 000", 100_000),
        ("10 000 000", 10_000_000),
        ("100 000 000", 100_000_000),
        ("1 000 000 000", 1_000_000_000),
    ]
    for label, amount in amounts:
        keyboard.button(text=label, callback_data=f"admin_add_balance_{target_id}_{amount}")
    keyboard.button(text="❌ Отмена", callback_data="admin_give_money")
    keyboard.adjust(2)
    
    await callback.message.edit_text("Выберите сумму для выдачи:", reply_markup=keyboard.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_add_balance_"))
async def admin_add_balance(callback: CallbackQuery):
    if callback.from_user.username != CREATOR_USERNAME:
        return

    parts = callback.data.split("_")
    target_id = int(parts[3])
    amount = int(parts[4])

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, target_id))
        await db.commit()

    await callback.message.edit_text(f"✅ Игроку выдано ${format_number(amount)}")
    await callback.answer()

# ========== ВЫДАТЬ МАШИНУ ==========

@dp.callback_query(F.data == "admin_give_car")
async def admin_give_car_menu(callback: CallbackQuery):
    if callback.from_user.username != CREATOR_USERNAME:
        return

    kb = await get_all_players_kb("give_car")
    await callback.message.edit_text("Выберите игрока:", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_give_car_"))
async def admin_select_car_for_player(callback: CallbackQuery):
    if callback.from_user.username != CREATOR_USERNAME:
        return

    target_id = int(callback.data.split("_")[3])
    # Покажем первую машину из общего списка
    await show_admin_car_page(callback, target_id, 0)

async def show_admin_car_page(callback: CallbackQuery, target_id: int, page: int):
    total = len(ALL_CARS)
    if page >= total:
        page = 0
    car = ALL_CARS[page]

    text = f"Выберите машину для выдачи:\n\n{car['name']} ({car['year']})\nЦена: ${format_number(car['price_usd'])}"

    keyboard = InlineKeyboardBuilder()
    if page > 0:
        keyboard.button(text="⬅️", callback_data=f"admin_car_page_{target_id}_{page-1}")
    keyboard.button(text="✅ Выдать", callback_data=f"admin_grant_car_{target_id}_{car['id']}")
    if page < total - 1:
        keyboard.button(text="➡️", callback_data=f"admin_car_page_{target_id}_{page+1}")
    keyboard.button(text="❌ Отмена", callback_data="admin_give_car")
    keyboard.adjust(3)

    await callback.message.edit_text(text, reply_markup=keyboard.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_car_page_"))
async def admin_car_page(callback: CallbackQuery):
    if callback.from_user.username != CREATOR_USERNAME:
        return

    parts = callback.data.split("_")
    target_id = int(parts[3])
    page = int(parts[4])
    await show_admin_car_page(callback, target_id, page)

@dp.callback_query(F.data.startswith("admin_grant_car_"))
async def admin_grant_car(callback: CallbackQuery):
    if callback.from_user.username != CREATOR_USERNAME:
        return

    parts = callback.data.split("_")
    target_id = int(parts[3])
    car_id = int(parts[4])

    car = next((c for c in ALL_CARS if c["id"] == car_id), None)
    if not car:
        await callback.answer("❌ Машина не найдена", show_alert=True)
        return

    async with aiosqlite.connect(DB_PATH) as db:
        # Проверим, есть ли уже у игрока (для дубликата)
        async with db.execute("SELECT 1 FROM user_cars WHERE user_id = ? AND car_id = ?", (target_id, car_id)) as cursor:
            is_duplicate = await cursor.fetchone() is not None

        await db.execute("""
            INSERT INTO user_cars (user_id, car_id, is_duplicate, source, acquired_at)
            VALUES (?, ?, ?, 'Админка', ?)
        """, (target_id, car_id, is_duplicate, now_iso()))

        # Обновим глобальный счётчик
        await db.execute("""
            INSERT INTO global_car_counts (car_id, issued_count)
            VALUES (?, 1)
            ON CONFLICT(car_id) DO UPDATE SET issued_count = issued_count + 1
        """)
        await db.commit()

    await callback.message.edit_text(f"✅ Машина «{car['name']}» выдана игроку!")
    await callback.answer()

# ========== ЗАБЛОКИРОВАТЬ ИГРОКА ==========

@dp.callback_query(F.data == "admin_ban")
async def admin_ban_menu(callback: CallbackQuery):
    if callback.from_user.username != CREATOR_USERNAME:
        return

    kb = await get_all_players_kb("ban")
    await callback.message.edit_text("Выберите игрока для блокировки:", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_ban_"))
async def admin_confirm_ban(callback: CallbackQuery):
    if callback.from_user.username != CREATOR_USERNAME:
        return

    target_id = int(callback.data.split("_")[2])
    if target_id == callback.from_user.id:
        await callback.answer("❌ Нельзя заблокировать себя!", show_alert=True)
        return

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="✅ Заблокировать", callback_data=f"admin_do_ban_{target_id}")
    keyboard.button(text="❌ Отмена", callback_data="admin_ban")
    keyboard.adjust(2)

    await callback.message.edit_text("⚠️ Вы уверены? Игрок больше не сможет играть!", reply_markup=keyboard.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_do_ban_"))
async def admin_do_ban(callback: CallbackQuery):
    if callback.from_user.username != CREATOR_USERNAME:
        return

    target_id = int(callback.data.split("_")[3])
    # Простая реализация: удалим из users и user_cars
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM users WHERE user_id = ?", (target_id,))
        await db.execute("DELETE FROM user_cars WHERE user_id = ?", (target_id,))
        await db.execute("DELETE FROM user_real_estate WHERE user_id = ?", (target_id,))
        await db.commit()

    await callback.message.edit_text("⛔ Игрок заблокирован (данные удалены).")
    await callback.answer()

# ========== АННУЛИРОВАТЬ ИГРОКА ==========

@dp.callback_query(F.data == "admin_wipe")
async def admin_wipe_menu(callback: CallbackQuery):
    if callback.from_user.username != CREATOR_USERNAME:
        return

    kb = await get_all_players_kb("wipe")
    await callback.message.edit_text("Выберите игрока для полной аннуляции:", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_wipe_"))
async def admin_confirm_wipe(callback: CallbackQuery):
    if callback.from_user.username != CREATOR_USERNAME:
        return

    target_id = int(callback.data.split("_")[2])
    if target_id == callback.from_user.id:
        await callback.answer("❌ Нельзя аннулировать себя!", show_alert=True)
        return

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🗑 Аннулировать", callback_data=f"admin_do_wipe_{target_id}")
    keyboard.button(text="❌ Отмена", callback_data="admin_wipe")
    keyboard.adjust(2)

    await callback.message.edit_text(
        "⚠️ ВНИМАНИЕ! Это удалит ВЕСЬ прогресс игрока: деньги, машины, таймеры, промокоды. Продолжить?",
        reply_markup=keyboard.as_markup()
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_do_wipe_"))
async def admin_do_wipe(callback: CallbackQuery):
    if callback.from_user.username != CREATOR_USERNAME:
        return

    target_id = int(callback.data.split("_")[3])
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM users WHERE user_id = ?", (target_id,))
        await db.execute("DELETE FROM user_cars WHERE user_id = ?", (target_id,))
        await db.execute("DELETE FROM user_real_estate WHERE user_id = ?", (target_id,))
        await db.commit()

    await callback.message.edit_text("🗑 Прогресс игрока полностью аннулирован.")
    await callback.answer()
  # main.py — БЛОК 8: Недвижимость и финальная логика

# ========== МЕНЮ НЕДВИЖИМОСТИ ==========

@dp.callback_query(F.data == "menu_realestate")
async def menu_realestate(callback: CallbackQuery):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🏠 Дома", callback_data="realestate_houses")
    keyboard.button(text="🏡 Виллы", callback_data="realestate_villas")
    keyboard.button(text="🏢 Квартиры", callback_data="realestate_apartments")
    keyboard.button(text="📈 Другая недвижимость", callback_data="realestate_income")
    keyboard.button(text="↩️ Меню", callback_data="back_to_main")
    keyboard.adjust(2)
    await callback.message.edit_text("Выберите тип недвижимости:", reply_markup=keyboard.as_markup())
    await callback.answer()

# ========== ОБЩАЯ ФУНКЦИЯ ПОКУПКИ НЕДВИЖИМОСТИ ==========

async def show_estate_page(callback: CallbackQuery, category: str, page: int):
    estates = REAL_ESTATE.get(category, [])
    if not estates:
        await callback.answer("Категория пуста", show_alert=True)
        return

    if page >= len(estates):
        page = 0
    estate = estates[page]

    # Проверим, куплен ли уже
    user_id = callback.from_user.id
    is_purchased = False
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT 1 FROM user_real_estate WHERE user_id = ? AND estate_id = ?
        """, (user_id, estate["id"])) as cursor:
            is_purchased = await cursor.fetchone() is not None

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT currency FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            currency = row[0] if row else "USD"

    price_text = "✅ Уже куплено" if is_purchased else format_price(estate["price_usd"], currency)
    income_text = f"\n📈 Доход: {format_price(estate.get('income_per_10_sec', 0), currency)} / 10 сек" if estate.get("income_per_10_sec") else ""

    text = (
        f"🏘 {estate['name']}\n"
        f"📍 {estate['location']}\n"
        f"💰 Цена: {price_text}"
        f"{income_text}"
    )

    keyboard = InlineKeyboardBuilder()
    if page > 0:
        keyboard.button(text="⬅️ Назад", callback_data=f"estate_{category}_{page-1}")
    if not is_purchased:
        # Для доходной недвижимости — проверим баланс
        if category == "income_property":
            balance = await get_balance_with_income(user_id)
            if balance < 500_000_000:
                keyboard.button(text="🔒 Только при ≥500 млн $", callback_data="locked_income")
            else:
                keyboard.button(text="🛒 Купить", callback_data=f"buy_estate_{estate['id']}")
        else:
            keyboard.button(text="🛒 Купить", callback_data=f"buy_estate_{estate['id']}")
    if page < len(estates) - 1:
        keyboard.button(text="Дальше ➡️", callback_data=f"estate_{category}_{page+1}")
    keyboard.button(text="↩️ Назад", callback_data="menu_realestate")
    keyboard.adjust(2 if (page > 0 and page < len(estates)-1) else 1, 1, 1)

    await callback.message.edit_text(text, reply_markup=keyboard.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "locked_income")
async def locked_income(callback: CallbackQuery):
    await callback.answer("🔒 Эта недвижимость доступна только при балансе от 500 млн USD!", show_alert=True)

# ========== ОБРАБОТЧИКИ КАТЕГОРИЙ ==========

@dp.callback_query(F.data == "realestate_houses")
async def realestate_houses(callback: CallbackQuery):
    await show_estate_page(callback, "houses", 0)

@dp.callback_query(F.data == "realestate_villas")
async def realestate_villas(callback: CallbackQuery):
    await show_estate_page(callback, "villas", 0)

@dp.callback_query(F.data == "realestate_apartments")
async def realestate_apartments(callback: CallbackQuery):
    await show_estate_page(callback, "apartments", 0)

@dp.callback_query(F.data == "realestate_income")
async def realestate_income(callback: CallbackQuery):
    await show_estate_page(callback, "income_property", 0)

@dp.callback_query(F.data.startswith("estate_"))
async def estate_page(callback: CallbackQuery):
    parts = callback.data.split("_")
    category = parts[1]
    page = int(parts[2])
    await show_estate_page(callback, category, page)

# ========== ПОКУПКА НЕДВИЖИМОСТИ ==========

@dp.callback_query(F.data.startswith("buy_estate_"))
async def buy_estate(callback: CallbackQuery):
    estate_id = callback.data.split("_")[2]
    estate = None
    category = None
    for cat, items in REAL_ESTATE.items():
        for item in items:
            if item["id"] == estate_id:
                estate = item
                category = cat
                break
        if estate: break

    if not estate:
        await callback.answer("❌ Недвижимость не найдена!", show_alert=True)
        return

    user_id = callback.from_user.id
    balance = await get_balance_with_income(user_id)

    if balance < estate["price_usd"]:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return

    # Для доходной недвижимости — двойная проверка
    if category == "income_property" and balance < 500_000_000:
        await callback.answer("❌ Требуется минимум 500 млн USD!", show_alert=True)
        return

    # Проверим, не куплено ли уже
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT 1 FROM user_real_estate WHERE user_id = ? AND estate_id = ?", (user_id, estate_id)) as cursor:
            if await cursor.fetchone():
                await callback.answer("❌ У вас уже есть эта недвижимость!", show_alert=True)
                return

        # Списываем деньги
        new_balance = balance - estate["price_usd"]
        await db.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))

        # Добавим в собственность
        await db.execute("""
            INSERT INTO user_real_estate (user_id, estate_id, purchased_at, last_collected)
            VALUES (?, ?, ?, ?)
        """, (user_id, estate_id, now_iso(), now_iso()))

        await db.commit()

    await callback.answer(f"✅ Недвижимость куплена: {estate['name']}", show_alert=True)
    await menu_realestate(callback)

# ========== ФИНАЛЬНЫЙ ЗАПУСК ==========

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")

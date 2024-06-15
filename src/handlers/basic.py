import asyncio
import sqlite3
from datetime import datetime

from aiogram import F, types, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton, InlineKeyboardMarkup

from src.config.cfg import bot
from src.keyboards.inline import menu_kb, return_to_main_kb, how_many_day_sub_banks, how_many_day_sub_crypt, MyCallBack, \
    type_of_payment
from src.handlers.cryptomus import create_invoice, get_invoice
from src.parser.database import get_all_ads
from src.config.check_dub import add_json, read_json, clear_json

router = Router()

# В глобальной области видимости определите структуру данных для хранения уже отправленных уведомлений
sent_notifications = {}
is_running = {}


def format_message(ad_text):
    # Функция для форматирования текста объявления с использованием HTML-тега <b>
    format_text = ad_text.split('\n')
    return "<b>" + "</b>\n<b>".join(format_text) + "</b>"


async def start_parsing_for_active_users():
    conn_sub = sqlite3.connect('subscriptions.db')
    # conn = psycopg2.connect(
    #    dbname="subscriptions",
    #    user="postgres",
    #    password="root",
    #    host="localhost",
    #    port="5432"
    # )
    cursor = conn_sub.cursor()
    cursor.execute('SELECT user_id FROM subscriptions WHERE parser_active = 1')
    active_users = cursor.fetchall()
    conn_sub.close()

    tasks = []
    for active_user in active_users:
        user_id = active_user[0]
        if user_id not in is_running or not is_running[user_id]:
            tasks.append(parse_and_send_notifications(user_id))

    if tasks:
        await asyncio.gather(*tasks)


async def parse_and_send_notifications(user_id):
    global is_running
    is_running[user_id] = True  # Устанавливаем состояние парсера для данного пользователя
    while is_running.get(user_id, False):  # Проверяем состояние парсера для данного пользователя
        await asyncio.sleep(5)  # 3600 секунд = 1 час
        # Выполняем парсинг
        new_ad_text = get_all_ads()

        # Проверяем, было ли уже отправлено такое уведомление для данного пользователя
        ad_text = new_ad_text[0][1]  # Предполагаем, что текст объявления находится во втором элементе кортежа
        formatted_message = format_message(ad_text)  # Форматируем текст объявления
        if user_id not in sent_notifications:
            sent_notifications[user_id] = set()

        if ((formatted_message not in sent_notifications[user_id])
                and not (any(entry.get('content') == formatted_message for entry in read_json(user_id)))):
            # Отправляем уведомление
            await bot.send_message(user_id, formatted_message, parse_mode="HTML")
            add_json(user_id, formatted_message)
            # Добавляем отправленное уведомление в список уже отправленных для данного пользователя
            sent_notifications[user_id].add(formatted_message)

        # Проверяем подписку пользователя каждые 6 часов
        if datetime.now().hour % 6 == 0:
            conn_sub = sqlite3.connect('subscriptions.db')
            # conn = psycopg2.connect(
            #    dbname="subscriptions",
            #    user="postgres",
            #    password="root",
            #    host="localhost",
            #    port="5432"
            # )
            cursor = conn_sub.cursor()
            cursor.execute('SELECT user_substatus FROM subscriptions WHERE user_id=?', (user_id,))
            result = cursor.fetchone()
            conn_sub.close()
            print('Проверка подписки')

            if result and result[0] != 1:
                # Останавливаем парсинг
                is_running[user_id] = False
                # Устанавливаем значение parser_active в 0
                # conn = psycopg2.connect(
                #    dbname="subscriptions",
                #    user="postgres",
                #    password="root",
                #    host="localhost",
                #    port="5432"
                # )
                conn_sub = sqlite3.connect('subscriptions.db')
                cursor = conn_sub.cursor()
                cursor.execute('UPDATE subscriptions SET parser_active = 0 WHERE user_id = ?', (user_id,))
                conn_sub.commit()
                conn_sub.close()
                # Отправляем сообщение о завершении подписки
                await bot.send_message(user_id,
                                       "Ваша подписка закончилась. Чтобы продолжить использование парсера, подпишитесь заново.")

        # Ждем некоторое время перед следующим парсингом
        await asyncio.sleep(3)


# Роутер основного меню..

@router.message(F.text == '/start')
async def get_talk(message: Message, state: FSMContext):
    await message.reply("Привет, я бот-парсер!", reply_markup=menu_kb)


# Роутер возвращения...

@router.callback_query(MyCallBack.filter(F.foo == 'return_to_main'))
async def get_to_main(query: CallbackQuery, callback_data: MyCallBack):
    await query.answer("Основное меню")
    await query.message.edit_text("Пожалуйста, выбери, что ты хочешь сделать", reply_markup=menu_kb)


@router.callback_query(MyCallBack.filter(F.foo == 'return_typeOfPay'))
async def get_to_main(query: CallbackQuery, callback_data: MyCallBack):
    await query.message.edit_text("Выбери способ оплаты", reply_markup=type_of_payment)


# Роутер информации для пользователя..

@router.callback_query(MyCallBack.filter(F.foo == 'info'))
async def callback_info(query: CallbackQuery, callback_data: MyCallBack):
    await query.answer("Информация о парсинге")
    await query.message.edit_text(
        'Парсинг происходит по самым новым объявлениям по Айфонам в городе Челябинск\n\nЕсли есть вопросы или нужен парсер по другим городам и продуктам пишите'
        ' @Azelisi и @holyd4mn\n\n  При использовании парсера вы соглашаетесь с отказом от ответственности',
        reply_markup=return_to_main_kb)


# Роутер для пополнения счёта пользователя..

@router.callback_query(MyCallBack.filter(F.foo == 'pay'))
async def top_up_user(query: CallbackQuery, callback_data: MyCallBack):
    await query.message.edit_text(
        "Выбери способ оплаты", reply_markup=type_of_payment)


# Для банков

@router.callback_query(MyCallBack.filter(F.foo == 'pay_bank'))
async def top_up_user_bank(query: CallbackQuery, callback_data: MyCallBack):
    await query.message.edit_text(
        "Оформить подписку\n\n7 дней - <b>599 RUB</b>\n14 дней - <b>999 RUB</b>\n30 дней - <b>1799 RUB</b>",
        parse_mode='HTML', reply_markup=how_many_day_sub_banks)


# Для крипты

@router.callback_query(MyCallBack.filter(F.foo == 'pay_crypt'))
async def top_up_user_crypt(query: CallbackQuery, callback_data: MyCallBack):
    await query.message.edit_text(
        "Оформить подписку\n\n7 дней - <b>599 RUB</b>\n14 дней - <b>999 RUB</b>\n30 дней - <b>1799 RUB</b>",
        parse_mode='HTML', reply_markup=how_many_day_sub_crypt)


@router.callback_query(MyCallBack.filter(F.foo == 'pay_trial'))
async def top_up_user_trial(query: CallbackQuery, callback_data: MyCallBack):
    user_id = query.from_user.id
    # conn = psycopg2.connect(
    #    dbname="subscriptions",
    #    user="postgres",
    #    password="root",
    #    host="localhost",
    #    port="5432"
    # )
    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()

    # Проверяем, использовал ли пользователь уже пробную подписку
    cursor.execute('SELECT user_trial_status, user_subtime FROM subscriptions WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()

    if row:
        trial_status, expiration_time = row
        if trial_status:
            # Если пользователь уже использовал пробную подписку, отправляем сообщение об этом
            await query.message.answer("Вы уже использовали пробную подписку.", reply_markup=menu_kb)
        else:
            # Если пользователь еще не использовал пробную подписку, добавляем или обновляем запись в базе данных
            trial_duration = 168  # Продолжительность пробной подписки на 1 день
            if expiration_time is not None:
                # Если у пользователя уже есть срок истечения подписки, добавляем к нему продолжительность пробной подписки
                expiration_time += trial_duration
            else:
                # Если у пользователя нет срока истечения подписки, устанавливаем продолжительность пробной подписки
                expiration_time = trial_duration

            cursor.execute('''
                INSERT INTO subscriptions (user_id, user_subtime, user_substatus, user_trial_status)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET user_subtime = ?, user_substatus = ?, user_trial_status = ?
            ''', (user_id, expiration_time, True, True, expiration_time, True, True))

            conn.commit()
            conn.close()

            await query.message.answer(
                "Пробная подписка оформлена на неделю",
                parse_mode='HTML', reply_markup=menu_kb)
    else:
        # Если запись о пользователе отсутствует, создаем новую запись с пробной подпиской
        expiration_time = 168  # Продолжительность пробной подписки на неделю
        cursor.execute('''
            INSERT INTO subscriptions (user_id, user_subtime, user_substatus, user_trial_status)
            VALUES (?, ?, ?, ?)
        ''', (user_id, expiration_time, True, True))
        conn.commit()
        conn.close()

        await query.message.answer(
            "Пробная подписка оформлена на неделю",
            parse_mode='HTML', reply_markup=menu_kb)


@router.callback_query(MyCallBack.filter(F.foo == 'sub_crypt_7'))
async def top_up_user_crypt_7(query: CallbackQuery):
    invoice = await create_invoice(query.message.from_user.id, 599)
    markup_crypt = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f'o_{invoice["result"]["uuid"]}')]
    ])
    await query.message.reply(f"Ваш чек:\n<b>{invoice['result']['url']}</b>", reply_markup=markup_crypt, parse_mode="HTML")


@router.callback_query(MyCallBack.filter(F.foo == 'sub_crypt_14'))
async def top_up_user_crypt_14(query: CallbackQuery):
    invoice = await create_invoice(query.message.from_user.id, 999)
    markup_crypt = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f'o_{invoice["result"]["uuid"]}')]
    ])
    await query.message.reply(f"Ваш чек:\n<b>{invoice['result']['url']}</b>", reply_markup=markup_crypt, parse_mode="HTML")


@router.callback_query(MyCallBack.filter(F.foo == 'sub_crypt_30'))
async def top_up_user_crypt_30(query: CallbackQuery):
    invoice = await create_invoice(query.message.from_user.id, 1799)
    markup_crypt = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f'o_{invoice["result"]["uuid"]}')]
    ])
    await query.message.reply(f"Ваш чек:\n<b>{invoice['result']['url']}</b>", reply_markup=markup_crypt, parse_mode="HTML")

@router.callback_query(F.data.startswith("o_"))
async def check_crypto_order(query: CallbackQuery): 
    invoice = await get_invoice(query.data.split("_")[1])
    if invoice["result"]["status"] == "paid": 
        await query.answer()
        await query.message.answer("Счёт оплачен 😉")
    else:
        await query.answer()
        await query.message.answer("Похоже Вы не оплатили счёт ☹️")

# Роутер парсинга..
# Проверка в базе на то что пользователь подписан (то есть, смотрим в базу данных user_id и sub_status и если sub_status равен 1 то всё заебисб)
@router.callback_query(MyCallBack.filter(F.foo == 'parsing'))
async def start_process_of_pars(query: types.CallbackQuery, callback_data: MyCallBack):
    await query.answer("")
    global parser_states
    user_id = query.from_user.id

    print(f"Start parsing cycle for user {user_id}, {query.data}")

    # Проверяем подписку пользователя
    # conn = psycopg2.connect(
    #    dbname="subscriptions",
    #    user="postgres",
    #    password="root",
    #    host="localhost",
    #    port="5432"
    # )
    conn_sub = sqlite3.connect('subscriptions.db')
    cursor = conn_sub.cursor()

    cursor.execute('SELECT user_substatus FROM subscriptions WHERE user_id=?', (user_id,))
    result = cursor.fetchone()
    cursor.execute('SELECT parser_active FROM subscriptions WHERE user_id=?', (user_id,))
    parser_active = cursor.fetchone()
    conn_sub.close()

    if result and result[0] == 1 and parser_active and parser_active[0] == 0:
        # conn = psycopg2.connect(
        #    dbname="subscriptions",
        #    user="postgres",
        #    password="root",
        #    host="localhost",
        #    port="5432"
        # )
        conn_sub = sqlite3.connect('subscriptions.db')
        cursor = conn_sub.cursor()
        cursor.execute('UPDATE subscriptions SET parser_active = 1 WHERE user_id = ?', (user_id,))
        conn_sub.commit()
        conn_sub.close()

        # Отправляем уведомление о начале парсинга
        await query.message.answer(
            "Парсинг запущен 🚀\nТы будешь получать уведомления о новых объявлениях\n\nДля остановки напиши - <b>Стоп</b>",
            parse_mode="HTML")
        # Запускаем асинхронную функцию, которая будет выполнять парсинг и отправлять уведомления
        await asyncio.create_task(parse_and_send_notifications(user_id))
    elif parser_active and parser_active[0] == 1:
        await query.message.answer("Парсинг уже запущен для вашего пользователя!")
    else:
        # Если пользователь не подписан, отправляем ему сообщение о необходимости подписки
        await query.message.answer("Для использования парсера необходимо подписаться!", reply_markup=menu_kb)


# Роутер остановки парсера
## Да, по-другому не смог, потому в рот ебал это while TRUE

@router.message(F.text.lower().in_(['/stop', 'стоп', 'stop', 'cnjg']))
async def stop_pars(message: Message):
    user_id = message.from_user.id
    if user_id in is_running:
        del is_running[user_id]  # Удаляем состояние парсера для данного пользователя
        del sent_notifications[user_id]
        clear_json(user_id)
        await bot.send_message(user_id, "Парсер остановлен 😴",
                               reply_markup=menu_kb)  # Отправляем уведомление о том, что парсер остановлен

        # Устанавливаем значение parser_active в 0
        conn_sub = sqlite3.connect('subscriptions.db')
        cursor = conn_sub.cursor()
        cursor.execute('UPDATE subscriptions SET parser_active = 0 WHERE user_id = ?', (user_id,))
        conn_sub.commit()
        conn_sub.close()

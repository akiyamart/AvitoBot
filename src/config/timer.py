import asyncio
import sqlite3



async def timer_db():
    while True:
        # Подключение к базе данных
        conn_sub = sqlite3.connect('subscriptions.db')
        # conn = psycopg2.connect(
        #    dbname="subscriptions",
        #    user="postgres",
        #    password="root",
        #    host="localhost",
        #    port="5432"
        # )
        cursor = conn_sub.cursor()
        # Получаем все записи из таблицы subscriptions
        cursor.execute('SELECT user_id, user_subtime, user_substatus FROM subscriptions')
        subscriptions = cursor.fetchall()

        for subscription in subscriptions:
            user_id, expiration_time, is_subscribed = subscription
            # Уменьшаем время подписки на 12 часов
            expiration_time -= 12
            # Если время подписки меньше или равно 0, устанавливаем статус подписки в False
            if expiration_time <= 0:
                expiration_time = 0
                is_subscribed = False

            # Обновляем запись в базе данных
            cursor.execute('''
                UPDATE subscriptions
                SET user_subtime=?, user_substatus=?
                WHERE user_id=?
            ''', (expiration_time, is_subscribed, user_id))

            # Проверяем подписку пользователя каждые 12 часов
          #  cursor.execute('SELECT user_id FROM subscriptions WHERE user_substatus = 1 AND user_subtime <= 0')
          #  active_users = cursor.fetchall()
           # for user_id in active_users:
            #    # Запускаем процесс парсинга для подписанных пользователей
           #     await parse_and_send_notifications(user_id)

        # Сохраняем изменения и закрываем подключение к базе данных
        conn_sub.commit()
        conn_sub.close()

        # await asyncio.sleep(60 * 60 * 12)  # Обновление каждые 12 часов
        await asyncio.sleep(60 * 60 * 12)

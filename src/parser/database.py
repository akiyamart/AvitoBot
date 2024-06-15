import psycopg2
from psycopg2 import sql

# Подключение к базе данных PostgreSQL
conn = psycopg2.connect(
    user='postgres',
    password='epfEABm98nUzUZ',  # добавьте этот параметр, если у вас есть пароль
    dbname='AvitoBase',
    host='localhost',
    port='5432'
)

# Пульт управления для базы данных
cursor = conn.cursor()

# Создание таблиц, если они не существуют  
def create_table_ads():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ads (
            id SERIAL PRIMARY KEY,
            text TEXT          
        )
    ''')
    conn.commit()

def create_table_subscriptions(): 
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions( 
            user_id INTEGER PRIMARY KEY, 
            user_subtime INTEGER, 
            user_substatus BOOLEAN, 
            user_trial_status BOOLEAN       
        )
    ''')
    conn.commit()

# is_ad_in_database: Проверяет, существует ли объявление (ad_text) в таблице ads.
def is_ad_in_database(ad_text):
    cursor.execute('SELECT * FROM ads WHERE text=%s', (ad_text,))
    result = cursor.fetchone()
    return result is not None

# save_ad_to_database: Сохраняет объявление (ad_text) в таблицу ads.
def save_ad_to_database(ad_text):
    cursor.execute('SELECT id FROM ads ORDER BY id DESC LIMIT 1')
    last_id = cursor.fetchone()
    if last_id:
        cursor.execute('DELETE FROM ads WHERE id=%s', (last_id[0],))
        conn.commit()
        print("Последняя запись удалена")

    cursor.execute('INSERT INTO ads (text) VALUES (%s)', (ad_text,))
    conn.commit()

# get_all_ads: Получает все записи из таблицы ads.
def get_all_ads(): 
    cursor.execute('SELECT * FROM ads')
    return cursor.fetchall()

# Закрытие соединения с базой данных
def close_connection():
    cursor.close()
    conn.close()

# Проерка работы всех функциий 
if __name__ == '__main__':
    create_table_ads()
    create_table_subscriptions()

    if not is_ad_in_database("Какой-то текст"):
        save_ad_to_database("Какой-то текст")
    
    ads = get_all_ads()
    for ad in ads:
        print(ad)

    close_connection()

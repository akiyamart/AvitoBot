from src.config.cfg import bot, dp
from src.handlers import basic
from src.config.timer import timer_db
from src.handlers.basic import start_parsing_for_active_users

import logging
import asyncio


async def on_startup():
    print("Бот запущен")
    # Запуск асинхронной функции timer, start_parsing, запуск парсера
    asyncio.create_task(timer_db())
    asyncio.create_task(start_parsing_for_active_users())


async def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - [%(levelname)s] - %(name)s"
                               "(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
                        )
    await bot.delete_webhook(drop_pending_updates=True)
    dp.startup.register(on_startup)
    dp.include_routers(basic.router)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())

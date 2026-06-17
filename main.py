#!/usr/bin/env python3
"""
Telegram Members Parser Bot
Парсит участников групп/каналов и сохраняет их в JSON файл
"""

import asyncio
import logging
import json
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from config import API_ID, API_HASH, PHONE, SESSION_NAME
from parser import MembersParser

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize client and parser
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
parser = MembersParser()


async def start_bot():
    """Запустить бота"""
    await client.start(phone=PHONE)
    logger.info("✅ Бот успешно подключен к Telegram")
    
    me = await client.get_me()
    logger.info(f"📱 Аккаунт: {me.first_name} {me.last_name or ''} (@{me.username})")


@client.on(events.NewMessage(pattern='/start'))
async def handle_start(event):
    """Обработчик команды /start"""
    await event.reply(
        "👋 Добро пожаловать в Telegram Members Parser!\n\n"
        "Доступные команды:\n"
        "/parse <group_id> - Парсить участников группы\n"
        "/list - Показать список групп\n"
        "/stats <group_name> - Статистика по группе\n"
        "/export <group_name> - Экспортировать в CSV\n"
        "/clear <group_name> - Очистить группу\n"
        "/help - Справка"
    )


@client.on(events.NewMessage(pattern=r'/parse\s+(.+)'))
async def handle_parse(event):
    """Обработчик команды /parse"""
    try:
        args = event.pattern_match.group(1).strip()
        
        # Попытаться преобразовать в число (группа по ID)
        try:
            group_id = int(args)
        except ValueError:
            # Иначе использовать как username
            group_id = args
        
        await event.reply(f"🔄 Начинаю парсинг... Это может занять время.")
        
        # Парсить группу
        added = await parser.parse_group(client, group_id)
        
        await event.reply(
            f"✅ Парсинг завершен!\n"
            f"Добавлено участников: {added}\n"
            f"Данные сохранены в members.json"
        )
    
    except Exception as e:
        logger.error(f"Ошибка при парсинге: {e}")
        await event.reply(f"❌ Ошибка: {str(e)}")


@client.on(events.NewMessage(pattern='/list'))
async def handle_list(event):
    """Обработчик команды /list"""
    groups = parser.get_all_groups()
    
    if not groups:
        await event.reply("📭 Нет загруженных групп")
        return
    
    response = "📋 Загруженные группы:\n\n"
    for group in groups:
        count = len(parser.get_members(group))
        response += f"• {group} ({count} участников)\n"
    
    await event.reply(response)


@client.on(events.NewMessage(pattern=r'/stats\s+(.+)'))
async def handle_stats(event):
    """Обработчик команды /stats"""
    try:
        group_name = event.pattern_match.group(1).strip()
        stats = parser.get_group_stats(group_name)
        
        if 'error' in stats:
            await event.reply(f"❌ {stats['error']}")
            return
        
        response = (
            f"📊 Статистика: {stats['group_name']}\n\n"
            f"Всего участников: {stats['total_members']}\n"
            f"Реальные пользователи: {stats['real_users']}\n"
            f"Боты: {stats['bots']}\n"
            f"С username: {stats['with_username']}\n"
            f"С номером телефона: {stats['with_phone']}\n"
            f"Последнее обновление: {stats['last_updated']}"
        )
        
        await event.reply(response)
    
    except Exception as e:
        await event.reply(f"❌ Ошибка: {str(e)}")


@client.on(events.NewMessage(pattern=r'/export\s+(.+)'))
async def handle_export(event):
    """Обработчик команды /export"""
    try:
        group_name = event.pattern_match.group(1).strip()
        
        await event.reply(f"⏳ Экспортирую {group_name}...")
        
        output_file = parser.export_csv(group_name)
        
        # Отправить файл
        await client.send_file(
            event.chat_id,
            output_file,
            caption=f"✅ Экспортированы участники из '{group_name}'"
        )
    
    except Exception as e:
        logger.error(f"Ошибка при экспорте: {e}")
        await event.reply(f"❌ Ошибка: {str(e)}")


@client.on(events.NewMessage(pattern=r'/clear\s+(.+)'))
async def handle_clear(event):
    """Обработчик команды /clear"""
    try:
        group_name = event.pattern_match.group(1).strip()
        
        if parser.clear_group(group_name):
            await event.reply(f"✅ Группа '{group_name}' очищена")
        else:
            await event.reply(f"❌ Группа '{group_name}' не найдена")
    
    except Exception as e:
        await event.reply(f"❌ Ошибка: {str(e)}")


@client.on(events.NewMessage(pattern='/help'))
async def handle_help(event):
    """Обработчик команды /help"""
    help_text = (
        "📚 Справка по командам:\n\n"
        "/start - Начальное приветствие\n\n"
        "/parse <group_id> - Парсить участников\n"
        "  Примеры:\n"
        "    /parse -1001234567890 (по ID группы)\n"
        "    /parse @groupname (по username)\n\n"
        "/list - Показать все загруженные группы\n\n"
        "/stats <group_name> - Статистика по группе\n"
        "  Пример: /stats \"My Group\"\n\n"
        "/export <group_name> - Экспортировать в CSV файл\n"
        "  Пример: /export \"My Group\"\n\n"
        "/clear <group_name> - Очистить данные группы\n"
        "  Пример: /clear \"My Group\"\n\n"
        "/help - Эта справка"
    )
    
    await event.reply(help_text)


async def main():
    """Главная функция"""
    logger.info("🚀 Запускаю Telegram Members Parser...")
    
    try:
        # Подключить бота
        await start_bot()
        
        logger.info("👂 Слушаю входящие сообщения...")
        await client.run_until_disconnected()
    
    except SessionPasswordNeededError:
        logger.error("❌ Требуется двухфакторная аутентификация")
        logger.error("Пожалуйста, установите пароль в Telegram Settings")
    
    except KeyboardInterrupt:
        logger.info("⏹️ Бот остановлен")
    
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    
    finally:
        await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())

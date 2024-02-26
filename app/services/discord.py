import random
import httpx
from loguru import logger
import asyncio
from app.db.db import get_slot, ParsedMessageSchema, DBMessages, Slot


class DiscordCLI():
    def __init__(self, token, proxy=None):
        self.token = token
        if proxy:
            self.proxies = {
                "http://": f"http://{proxy}",
                "https://": f"https://{proxy}"
            }
        else:
            self.proxies = None
        self.headers = {"Authorization": self.token}

    async def send_message(self, channel_id: str, text):
        logger.info(f"Sending message: {text}")
        url = f'https://discord.com/api/v9/channels/{channel_id}/messages'
        payload = {"mobile_network_type": "unknown",
                   "content": f"{text}",
                   "tts": False,
                   "flags": 0}

        async with httpx.AsyncClient(proxies=self.proxies) as client:
            r = await client.post(url, headers=self.headers, data=payload)
            return r.json()

    async def get_messages(self, chatid, limit=5):
        async with httpx.AsyncClient(proxies=self.proxies) as client:
            try:
                url = f'https://discord.com/api/v9/channels/{chatid}/messages?limit={limit}'
                r = await client.get(url, headers=self.headers)
                r.raise_for_status()
                data = r.json()
                if len(data) < 1:
                    logger.debug('No messages found')
                    return None
                return data

            except httpx.HTTPError as http_err:
                if http_err.response.status_code == 400:
                    logger.error(f'Bad request error: {http_err}')
                    raise
                elif len(data) <= 1:
                    logger.success('Successfully parsed all messages')
                    return 'Successfully parsed all messages'
                else:
                    logger.error(f'Error occurred: {http_err}')
                    raise
            except Exception as err:
                logger.error(f'Unexpected error occurred: {err}')
                raise


async def run_slot(slot: Slot):
    logger.success(f'Запущен слот: {slot.id}')
    while True:
        slot = await Slot.get(slot.id)
        for i in range(slot.timeout):
            if not slot.enable:
                logger.success(f'Слот {slot.id} Завершил работу')
                return False
            await asyncio.sleep(1)

        parser_client = DiscordCLI(token=slot.parser_config.token, proxy=slot.parser_config.proxy)
        messages_list = await parser_client.get_messages(chatid=slot.parser_config.chatid, limit=1)
        last_message_id = messages_list[0]['id']
        message_in_db = await DBMessages.find_one(DBMessages.message.id == last_message_id)
        if message_in_db is None:
            parsed_messages = await parser_client.get_messages(chatid=slot.parser_config.chatid, limit=100)
            for message in parsed_messages[::-1]:
                message_model = ParsedMessageSchema(id=message['id'],
                                                    author_id=message['author']['id'],
                                                    content=message['content'])

                message_db = await DBMessages.find_one(DBMessages.message.id == message_model.id)
                if message_db is None:
                    message_db = await DBMessages(slot=slot.id,
                                                  message=message_model,
                                                  isPublish=False,
                                                  resender=None).create()
                    logger.debug(f'Сообщение не найдено в базе, сохраняем: {message_db.model_dump()}')
                else:
                    logger.debug(f'Сообщение уже содержится в базе')
                    continue
                logger.info(message_model.model_dump())
                logger.debug('Выбираем аккаунт для ресендинга')
                accounts = [account for account in slot.poster_config.accounts if account.status == 'active']
                if not accounts:
                    logger.error('Нет активных аккаунтов.')
                    slot.enable = False
                    await slot.save()
                    return

                account = random.choice(accounts)
                logger.debug(f'Выбран аккаунт  {account}')
                poster_client = DiscordCLI(token=account.token, proxy=account.proxy)
                logger.info(f'Отправляю текст: {message_model.content}')
                poster_send = await poster_client.send_message(channel_id=slot.poster_config.chatid,
                                                               text=message_model.content)
                if not poster_send:
                    logger.debug('Аккаунт не смог отправить сообщение')
                    slot.enable = False
                    await slot.save()
                else:
                    logger.debug(f'Аккаунт успешно отправил сообщение: {poster_send}')
                    message_db.resender = account.token
                    message_db.isPublish = True
                    await message_db.save()

                await asyncio.sleep(3)

        else:
            logger.debug('Нет новых сообщений')

        logger.debug(f'Раунд парсинга завершен\n________________________________')

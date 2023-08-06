from pyrogram import Client, filters
from pyrogram.errors import ChatAdminRequired, PeerFlood, BadRequest
from os import environ
from dotenvy import load_env, read_file
import argparse
import asyncio
from time import sleep

# fuck.py -chats=chats.txt -msg=msg.txt -env=./.env
parser = argparse.ArgumentParser(description="Files for spamming")
parser.add_argument('-chats', metavar='your chats', type=str, help='Path to your links of chat')
parser.add_argument('-msg', metavar='message', type=str, help='Path to your message')
parser.add_argument('-env', metavar='your profile', type=str, help='Path to your .env file with api')

args = parser.parse_args()
chats = args.chats
msg_user = open(args.msg, 'r').read()
env = args.env

load_env(read_file(env))

api_id = environ.get("API_ID")
api_hash = environ.get("API_HASH")
app = Client("my_account", api_id, api_hash)


async def is_user_in_chat(chat_id):
    try:
        me = await app.get_me()
        chat_member = await app.get_chat_member(chat_id, me.id)
        return chat_member.status in ["member", "administrator"]
    except Exception:
        return False


@app.on_message(filters.command('start', prefixes='/'))
async def start(client, msg):
    for chat_link in fc:
        try:
            chat_id = await app.get_chat(f'@{chat_link}')
            is_user_present = await is_user_in_chat(chat_id)
            if not is_user_present:
                await app.join_chat(chat_id.id)
                await app.send_message(chat_id=chat_id.id, text=f'{msg_user}')
        except ChatAdminRequired:
            print(f'The group({chat_link}) should be open or you have to be administrator')
        except PeerFlood:
            print('We done! Sending messages is prohibited')
        except BadRequest as e:
            print(f'{e}')
        sleep(5)


if __name__ == '__main__':
    link = open(chats, 'r')
    fc = []
    for i in link:
        if i[-1] == '\n':
            fc.append(i[13:-1])
        else:
            fc.append(i[13:])
    app.run()
    asyncio.run(start())

import html
import asyncio
from pyrogram import Client, filters
from pyrogram.errors.exceptions.flood_420 import FloodWait
from .. import config, slave, log_errors, app_user_ids

logged = set()
lock = asyncio.Lock()

@Client.on_message(~filters.forwarded & ~filters.chat(config['config']['log_chat']) & filters.incoming & filters.forwarded & (filters.group | filters.channel))
@log_errors
async def log_forwards(client, message):
    if not config['config'].get('log_forwards'):
        return
    if getattr(message.from_user, 'id', None) in app_user_ids:
        return
    for i in app_user_ids:
        if message.forward_from:
            if i == message.forward_from.id:
                forwardee = app_user_ids[i]
                break
        j = app_user_ids[i].first_name
        if app_user_ids[i].last_name:
            j += f' {app_user_ids[i].last_name}'
        if j == message.forward_sender_name:
            forwardee = app_user_ids[i]
            break
    else:
        return
    identifier = (message.chat.id, message.message_id)
    async with lock:
        if identifier in logged:
            return
        chat_text = html.escape(message.chat.title)
        if message.chat.username:
            chat_text = f'<a href="https://t.me/{message.chat.username}">{chat_text}</a>'
        text = f'<b>Forwarded Event</b>\n- <b>Chat:</b> {chat_text} '
        if message.chat.is_verified:
            chat_text += '<code>[VERIFIED]</code> '
        if message.chat.is_support:
            chat_text += '<code>[SUPPORT]</code> '
        if message.chat.is_scam:
            chat_text += '<code>[SCAM]</code> '
        text += f'[<code>{message.chat.id}</code>]'
        if message.chat.type != 'channel':
            if message.from_user:
                user_text = message.from_user.first_name
                if message.from_user.last_name:
                    user_text += f' {message.from_user.last_name}'
                user_text = '<code>[DELETED]</code>' if message.from_user.is_deleted else html.escape(user_text or 'Empty???')
                if message.from_user.is_verified:
                    user_text += ' <code>[VERIFIED]</code>'
                if message.from_user.is_support:
                    user_text += ' <code>[SUPPORT]</code>'
                if message.from_user.is_scam:
                    user_text += ' <code>[SCAM]</code>'
                user_text += f' [<code>{message.from_user.id}</code>]'
            elif message.sender_chat and message.sender_chat.id != message.chat.id:
                user_text = html.escape(message.sender_chat.title)
                if message.sender_chat.username:
                    user_text = f'<a href="https://t.me/{message.sender_chat.username}">{user_text}</a>'
                if message.sender_chat.is_verified:
                    user_text += ' <code>[VERIFIED]</code>'
                if message.sender_chat.is_support:
                    user_text += ' <code>[SUPPORT]</code>'
                if message.sender_chat.is_scam:
                    user_text += ' <code>[SCAM]</code>'
            else:
                user_text = 'Anonymous'
            text += f'\n- <b>Forwarder:</b> {user_text}'
        text += f'\n- <b><a href="{message.link}">Message'
        mtext = (message.text or message.caption or '').strip()
        if mtext:
            text += ':'
        text += '</a></b>'
        if mtext:
            text += f' {html.escape(mtext.strip()[:2000])}'
        text += '\n- <b>Forwardee:</b> '
        user_text = forwardee.first_name
        if forwardee.last_name:
            user_text += f' {forwardee.last_name}'
        user_text = '<code>[DELETED]</code>' if forwardee.is_deleted else html.escape(user_text or 'Empty???')
        if forwardee.is_verified:
            user_text += ' <code>[VERIFIED]</code>'
        if forwardee.is_support:
            user_text += ' <code>[SUPPORT]</code>'
        if forwardee.is_scam:
            user_text += ' <code>[SCAM]</code>'
        text += f'{user_text} [<code>{forwardee.id}</code>]'
        while True:
            try:
                await slave.send_message(config['config']['log_chat'], text, disable_web_page_preview=True)
            except FloodWait as ex:
                await asyncio.sleep(ex.x + 1)
            else:
                break
        logged.add(identifier)

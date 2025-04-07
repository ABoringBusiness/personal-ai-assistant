import os
import asyncio
import re
from telegram import Bot, Update
from telegram.constants import ParseMode
from telegram.error import TelegramError, TimedOut, NetworkError


class TelegramChannel:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("CHAT_ID")
        self.bot = Bot(token=self.token)
        self.last_update_id = 0  # Track the last update ID for offset

    def _escape_markdown(self, text):
        """Escape markdown special characters to prevent formatting errors"""
        # Characters that need to be escaped in Markdown v1
        markdown_chars = ['_', '*', '`', '[']
        
        # Escape each character with a backslash
        for char in markdown_chars:
            text = text.replace(char, '\\' + char)
            
        return text

    def send_message(self, text):
        try:
            # Try to send with Markdown formatting first
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Attempt to send with MarkdownV2 (which has stricter escaping requirements)
            try:
                message = loop.run_until_complete(
                    self.bot.send_message(chat_id=self.chat_id, text=text, parse_mode=ParseMode.MARKDOWN)
                )
                print(f"Message sent to Telegram: {text[:50]}...")
                return "Message sent successfully on Telegram"
            except TelegramError as e:
                if "Can't parse entities" in str(e):
                    # Try with escaped markdown
                    escaped_text = self._escape_markdown(text)
                    message = loop.run_until_complete(
                        self.bot.send_message(chat_id=self.chat_id, text=escaped_text, parse_mode=ParseMode.MARKDOWN)
                    )
                    print(f"Message sent with escaped markdown: {escaped_text[:50]}...")
                    return "Message sent successfully with escaped formatting"
                else:
                    raise
        except TelegramError as e:
            # If all attempts with Markdown fail, send without formatting
            print(f"Markdown error, sending without formatting: {e}")
            try:
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                message = loop.run_until_complete(
                    self.bot.send_message(chat_id=self.chat_id, text=text, parse_mode=None)
                )
                print(f"Message sent without formatting: {text[:50]}...")
                return "Message sent successfully on Telegram (without formatting)"
            except TelegramError as e2:
                print(f"Error sending message without formatting: {e2}")
                return f"Failed to send message: {str(e2)}"

    def receive_messages(self, after_timestamp):
        try:
            # Create a new event loop if there isn't one available
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Use offset to get only new updates
            updates = loop.run_until_complete(
                self.bot.get_updates(offset=self.last_update_id + 1, timeout=5)
            )
            
            # Debug log
            if updates:
                print(f"Received {len(updates)} updates from Telegram")
            
            new_messages = []
            for update in updates:
                # Update our last_update_id
                if update.update_id > self.last_update_id:
                    self.last_update_id = update.update_id
                
                if isinstance(update, Update) and update.message and update.message.text:
                    message = update.message
                    
                    # Check if the message is from the configured chat_id
                    if str(message.chat_id) == str(self.chat_id):
                        if message.date.timestamp() > after_timestamp:
                            new_messages.append({
                                "text": message.text,
                                "date": message.date.strftime("%Y-%m-%d %H:%M"),
                            })
                            print(f"Processed message: {message.text}")
            
            return new_messages
        except TimedOut:
            # This is expected with long polling, just return empty list
            return []
        except NetworkError as e:
            print(f"Network error in receive_messages: {e}")
            return []
        except TelegramError as e:
            print(f"Telegram error in receive_messages: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error in receive_messages: {e}")
            return []

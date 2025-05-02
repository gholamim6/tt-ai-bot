# Author: Mohsen Gholami
# https://github.com/gholamim6/
# last update: 2025/04/14


import sys
import json
import time
import teamtalk
from threading import Thread
from pathlib import Path
import textwrap


class Bot(teamtalk.TeamTalkServer):
    def __init__(self):
        super().__init__()
        # Call a function to load settings needed for running the bot like teamtalk account and api keys
        self.load_settings()
        # Comment the next line if you don't want to save the bot info like teamtalk account and api keys on your disk.
        self.save_settings()
        # This function ensures that for each message the assigned function will be called.
        # It's like the events in javascript
        self.subscribe("messagedeliver", self.on_message_deliver)
        # Creat a dictionary to remember which user talks to which AI
        self.chats = {}

    def load_settings(self):
        # Generate a default address for storing bot settings like teamtalk account info and api keys
        self.settings_dir = Path.home() / '.tt-ai-bot.json'
        if self.settings_dir.exists():
            with open(self.settings_dir) as settings_file:
                self.settings = json.load(settings_file)
        else:
            self.settings = dict(
                openai_api_key = "",
                groq_api_key = "",
                host="localhost",
                port=10333,
                username="",
                password="",
                nickname="",
                channel="/",
                channel_password=""
            )
            for setting in self.settings:
                print(f"Enter the {setting}", end="", flush=True)
                if self.settings[setting]:
                    print(f", default ({self.settings[setting]}): ", end="", flush=True)
                else:
                    print(f": ", end="", flush=True)
                setting_value = input()
                if setting_value:
                    self.settings[setting] = setting_value
        if len(sys.argv) < 2 or sys.argv[1].strip().lower() != "run":
            settings_keys = list(self.settings.keys())
            menu_number  = -1
            while menu_number != 0:
                print("Is these settings for your bot correct?")
                print("If yes press 0 to run the bot or press the key number to edit that setting")
                print("or press CTRL+c to exit the app")
                print("You can also send run command when running from commandline to skip this and Start the bot immediately.")
                for setting_number, setting_key in enumerate(self.settings.keys(), start=1):
                    print(f'{setting_number}. {setting_key}: "{self.settings[setting_key]}"')
                try:
                    menu_number = int(input())
                    if menu_number > 0 and not menu_number  > len(settings_keys):
                        key_to_edit = settings_keys[menu_number - 1]
                        self.settings[key_to_edit] = input(f"Enter the {key_to_edit}: ")
                except KeyboardInterrupt:
                    print("goodbye!")
                    exit()
                except:
                    print("Wrong number.")
                    continue
        if type(self.settings["port"]) == str:
            self.settings["port"] = int(self.settings["port"])
    
    def save_settings(self):
        with open(self.settings_dir, "w") as settings_file:
            json.dump(self.settings, settings_file, indent=True)
    
    def start_bot(self):
        # This function start the bot by connecting to the teamtalk server if the account info is correct.
        host, port = self.settings["host"], self.settings["port"]
        self.set_connection_info(host, port)
        self.connect()
        username, password = self.settings["username"], self.settings["password"]
        nickname, app_name = self.settings["nickname"], "tt_bot"
        self.login(nickname, username, password, app_name)
        channel, channel_password = self.settings["channel"], self.settings["channel_password"]
        if channel:
            self.join(channel, channel_password)
        # this last function ensures that bot can read and write to teamtalk server. we put in a thread to avoid blocking main thread.
        Thread(target=self.handle_messages, args=(1,), daemon=True).start()

    def restart_bot(self):
        if not self.disconnecting:
            self.disconnect()
        # sleep for three seconds to bot handles the disconnecting status
        time.sleep(3)
        super().__init__()
        self.subscribe("messagedeliver", self.on_message_deliver)
        self.start_bot()
        
    def split_long_text(self, text):
        # Because of teamtalk limits for message length, We split it to smaller line and send it in several messages if necessary
        short_texts = []
        text_lines = textwrap.wrap(text, width=250)
        text_buffer = ''
        while text_lines:
            if len(text_buffer + text_lines[0]) > 250:
                short_texts.append(text_buffer.strip())
                text_buffer = ''
            else:
                text_buffer += text_lines.pop(0) + '\n'
                if not text_lines:
                    short_texts.append(text_buffer.strip())
        return short_texts

    def send_response(self, message_type, user, message):
        # Send a response message to a user or channel
        if message_type == teamtalk.USER_MSG:
            self.user_message(user, message)
        elif message_type == teamtalk.CHANNEL_MSG:
            self.channel_message(message)

    def send_ai_response(self, chat_id, user, message_type, message):
        # Getting and sending AI responses has put in a separate function which ables us to call it via thread and thus The bot can respond to multiple user at once.
        response = ''
        if self.chats[chat_id] == "chatgpt":
            response = self.ask_chatgpt(chat_id, message, max_tokens=200, model="gpt-4o-mini")
        elif self.chats[chat_id] == "groq":
            response = self.ask_groq(chat_id, message, max_tokens=200)
        print(f'AI Response: "{response}"')
        for text in self.split_long_text(response):
            self.send_response(message_type, user, text)

    def on_message_deliver(self, server, params):
        # This function receives messages and decides what to do based on the content.
        response = ''
        message = params["content"].strip()
        message_type = params["type"]
        user = self.get_user(params["srcuserid"])
        username = user["username"]
        nickname = user["nickname"]
        chat_id = ""
        if message_type == teamtalk.USER_MSG:
            print(f'private message from "{nickname}" with username "{username}":\n"{message}"')
            chat_id = f'user:{username}'
        elif message_type == teamtalk.CHANNEL_MSG:
            if not message.startswith('/'):
                return
            print(f'channel message from "{nickname}" with username "{username}":\n"{message}"')
            chanid = params["chanid"]
            chat_id = f'channel:{chanid}'
        # First checking if the user wants a help for using the bot.
        if not message or message.lower() == "h":
            self.send_response(message_type, user, self.get_help())
            return
        # Adding this condition to avoid answering the bot messages itself.
        elif username == self.me['username']:
            return
        # Add a condition to avoid answering users outside the channel that bot joined
        if (self.me.get("chanid") != user.get("chanid")):
            self.send_response(message_type, user, "افسوس! شما نمیتوانید خارج از کانال به ربات پیام بدهید!")
            return
        # Creat a chat_id to save the users and channels and which AI they choosed to talk in self.chats dictionary
            message = message.lstrip('/')
        # Adding bot options menu to select and remove AI to chat.
        # Add Persian numbers to get numbers in different forms.
        if message in "1۱":
            self.chats[chat_id] = "chatgpt"
            if not chat_id in self.chatgpt_user_messages:
                response = "ساخت گفتگوی تازه با ChatGPT."
            else:
                response = "ادامه گفتگوی پیشین با ChatGPT."
        elif message in "2۲":
            self.chats[chat_id] = "groq"
            if not chat_id in self.groq_user_messages:
                response = "ساخت گفتگوی تازه با Groq."
            else:
                response = "ادامه گفتگوی پیشین با Groq."
        elif message in "3۳":
            if chat_id in self.chats:
                self.chats.pop(chat_id)
            if chat_id in self.chatgpt_user_messages:
                self.chatgpt_user_messages.pop(chat_id)
                response = "گفتگوی پیشین با ChatGPT پاک شد."
            else:
                response = "شما هیچ گفتگویی  با ChatGPT نداشتید."
        elif message in "4۴":
            if chat_id in self.chats:
                self.chats.pop(chat_id)
            if chat_id in self.groq_user_messages:
                self.groq_user_messages.pop(chat_id)
                response = "گفتگوی پیشین با Groq پاک شد."
            else:
                response = "شما هیچ گفتگویی  با Groq نداشتید."
        # If the user does not send the help command or menu number and has started a chat with ai, I send the message to the respected ai.
        elif chat_id in self.chats:
            Thread(target=self.send_ai_response, args=(chat_id, user, message_type, message), daemon=True).start()
        # If user does not send any above command and hasn't started a chat, I will send the help message to introduce him/her to the bot options.
        else:
            response = self.get_help()
        # Finally i send the bot response.
        for text in self.split_long_text(response):
            self.send_response(message_type, user, text)

    def get_help(self):
        # Creating a help string for introducing the bot menu to the user.
        text = "برای در یافت راهنما حرف h و برای هر یک از دستورات زیر یکی از شماره ها را به ربات بفرستید.\n"
        text += 'برای فرستادن این دستورات در کانال یک کاراکتر "/" پیش از تمام این دستور ها بیفزایید.\n'
        text += "1. ساخت یا ادامه گفتگو با ChatGPT.\n"
        text += "2. ساخت یا ادامه گفتگو با Groq.\n"
        text += "3. پاک کردن گفتگوی پیشین با ChatGPT.\n"
        text += "4. پاک کردن گفتگوی پیشین با Groq.\n"
        return text


# creat a bot
bot = Bot()

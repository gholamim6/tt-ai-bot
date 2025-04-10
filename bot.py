import sys
import json
import teamtalk
from threading import Thread
from pathlib import Path


class Bot(teamtalk.TeamTalkServer):
    def __init__(self):
        super().__init__()
        self.load_settings()
        self.subscribe("messagedeliver", self.on_message_deliver)
        self.chats = {}

    def load_settings(self):
        # generate a default address for storing bot settings like teamtalk account info and api keys
        self.settings_dir = Path.home() / '.tt-ai-bot.json'
        if self.settings_dir.exists():
            with open(self.settings_dir) as settings_file:
                self.settings = json.load(settings_file)
        else:
            self.settings = dict(
                openai_api_key = "",
                deepseek_api_key = "",
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
                        self.save_settings()
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
        host, port = self.settings["host"], self.settings["port"]
        self.set_connection_info(host, port)
        self.connect()
        username, password = self.settings["username"], self.settings["password"]
        nickname, app_name = self.settings["nickname"], "tt_bot"
        self.login(nickname, username, password, app_name)
        # self.change_status(0, 'برای دریافت راهنما نویسه "h" را بفرستید.')
        channel, channel_password = self.settings["channel"], self.settings["channel_password"]
        if channel:
            self.join(channel, channel_password)
        Thread(target=self.handle_messages, args=(1,), daemon=True).start()

    def split_long_text(self, text):
        if len(text) < 513:
            return [text]
        short_texts = []
        text_lines = text.splitlines()
        text_buffer = ''
        while text_lines:
            if len(text_buffer + text_lines[0]) > 512:
                short_texts.append(text_buffer)
                text_buffer = ''
            else:
                text_buffer += text_lines.pop(0) + '\n'
                if not text_lines:
                    short_texts.append(text_buffer)
        return short_texts

    def send_response(self, message_type, user, message):
        if message_type == teamtalk.USER_MSG:
            self.user_message(user, message)
        elif message_type == teamtalk.CHANNEL_MSG:
            self.channel_message(message)

    def on_message_deliver(self, server, params):
        message = params["content"].strip()
        message_type = params["type"]
        user = self.get_user(params["srcuserid"])
        username = user["username"]
        nickname = user["nickname"]
        chat_id = ""
        if not message or message.lower() == "h":
            self.send_response(message_type, user, self.get_help())
            return
        elif username == self.me['username']:
            return
        if message_type == teamtalk.USER_MSG:
            print(f'private message from "{nickname}" with username "{username}":\n"{message}"')
            chat_id = f'user:{username}'
        elif message_type == teamtalk.CHANNEL_MSG:
            print(f'channel message from "{nickname}" with username "{username}":\n"{message}"')
            chanid = params["chanid"]
            chat_id = f'channel:{chanid}'
        text = ''
        if message in "1۱":
            self.chats[chat_id] = "chatgpt"
            if not chat_id in self.chatgpt_user_messages:
                text = "ساخت گفتگوی تازه با ChatGPT."
            else:
                text = "ادامه گفتگوی پیشین با ChatGPT."
        elif message in "2۲":
            self.chats[chat_id] = "deepseek"
            if not chat_id in self.deepseek_user_messages:
                text = "ساخت گفتگوی تازه با Deepseek."
            else:
                text = "ادامه گفتگوی پیشین با Deepseek."
        elif message in "3۳":
            self.chats[chat_id] = "groq"
            if not chat_id in self.groq_user_messages:
                text = "ساخت گفتگوی تازه با Groq."
            else:
                text = "ادامه گفتگوی پیشین با Groq."
        elif message in "4۴":
            if chat_id in self.chatgpt_user_messages:
                del self.chatgpt_user_messages[chat_id]
                text = "گفتگوی پیشین با ChatGPT پاک شد."
            else:
                text = "شما هیچ گفتگویی  با ChatGPT نداشتید."
        elif message in "5۵":
            if chat_id in self.deepseek_user_messages:
                del self.deepseek_user_messages[chat_id]
                text = "گفتگوی پیشین با Deepseek پاک شد."
            else:
                text = "شما هیچ گفتگویی  با Deepseek نداشتید."
        elif message in "6۶":
            if chat_id in self.groq_user_messages:
                del self.groq_user_messages[chat_id]
                text = "گفتگوی پیشین با Groq پاک شد."
            else:
                text = "شما هیچ گفتگویی  با Groq نداشتید."
        elif chat_id in self.chats:
            response = ""
            if self.chats[chat_id] == "chatgpt":
                response = self.ask_chatgpt(chat_id, message)
            elif self.chats[chat_id] == "deepseek":
                response = self.ask_deepseek(chat_id, message)
            elif self.chats[chat_id] == "groq":
                response = self.ask_groq(chat_id, message)
            for text in self.split_long_text(response):
                self.send_response(message_type, user, text)
        else:
            text = self.get_help()
        if text:
            self.send_response(message_type, user, text)

    def get_help(self):
        text = "برای در یافت راهنما حرف h و برای هر یک از دستورات زیر یکی از شماره ها را به ربات بفرستید.\n"
        text += "1. ساخت یا ادامه گفتگو با ChatGPT.\n"
        text += "2. ساخت یا ادامه گفتگو با Deepseek.\n"
        text += "3. ساخت یا ادامه گفتگو با Groq.\n"
        text += "4. پاک کردن گفتگوی پیشین با ChatGPT.\n"
        text += "5. پاک کردن گفتگوی پیشین با Deepseek.\n"
        text += "6. پاک کردن گفتگوی پیشین با Groq.\n"
        return text


# creat a bot
bot = Bot()

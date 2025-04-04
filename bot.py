import sys
import json
import teamtalk
from threading import Thread
from pathlib import Path


class Bot(teamtalk.TeamTalkServer):
    def __init__(self):
        super().__init__()
        self.load_settings()
        self.save_settings()
        self.subscribe("messagedeliver", self.on_message_deliver)
    
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
        host, port = self.settings["host"], self.settings["port"]
        self.set_connection_info(host, port)
        self.connect()
        username, password = self.settings["username"], self.settings["password"]
        nickname, app_name = self.settings["nickname"], "tt_bot"
        self.login(nickname, username, password, app_name)
        channel, channel_password = self.settings["channel"], self.settings["channel_password"]
        if channel:
            self.join(channel, channel_password)
        Thread(target=self.handle_messages, args=(1,), daemon=True).start()

    def on_message_deliver(self, server, params):
        content = params["content"]
        user = self.get_user(params["srcuserid"])
        nickname = user["nickname"]
        username = user["username"]
        if params["type"] == teamtalk.USER_MSG:
            print(f'private message from "{nickname}" with username "{username}":\n"{content}"')
        elif params["type"] == teamtalk.CHANNEL_MSG:
            print(f'channel message from "{nickname}" with username "{username}":\n"{content}"')


# creat a bot
bot = Bot()

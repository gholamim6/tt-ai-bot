# Author: Mohsen Gholami
# https://github.com/gholamim6/
# last update: 2025/04/14


import os
import platform
from bot import bot
from ai import chatgpt_user_messages, deepseek_user_messages, groq_user_messages
from ai import ask_chatgpt, ask_deepseek, ask_groq


if __name__ == "__main__":
    # Adding the ai functions and dictionaries to the bot object.
    # Because of circular import error, I can not import the ai functions and objects in bot.py directly.
    bot.chatgpt_user_messages, bot.groq_user_messages = chatgpt_user_messages, groq_user_messages
    bot.ask_chatgpt, bot.ask_groq = ask_chatgpt, ask_groq
    # clear the screen from settings in console for security reasons.
    if platform.platform().startswith('Linux'):
        os.system('clear')
    else:
        os.system('cls')
    # Start the bot.
    bot.start_bot()
    # adding a loop which ables us to restart the bot more easyly.
    while True:
        try:
            # Add a input to stop the loop.
            input("Press CTRL+C to exit.\nPress enter to restart.\n")
            bot.restart_bot()
        except KeyboardInterrupt:
            print('Exiting ...')
            break

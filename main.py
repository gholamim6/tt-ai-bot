from bot import bot
from ai import chatgpt_user_messages, deepseek_user_messages, groq_user_messages
from ai import ask_chatgpt, ask_deepseek, ask_groq


if __name__ == "__main__":
    bot.chatgpt_user_messages, bot.groq_user_messages = chatgpt_user_messages, groq_user_messages
    bot.ask_chatgpt, bot.ask_groq = ask_chatgpt, ask_groq
    bot.start_bot()
    input("Press enter to exit.")

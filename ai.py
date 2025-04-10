import openai
import groq
import requests
from bot import bot

openai_api_key = bot.settings["openai_api_key"]
deepseek_api_key = bot.settings["deepseek_api_key"]
groq_api_key = bot.settings["groq_api_key"]

chatgpt_user_messages = {}

def ask_chatgpt(user_id, question, api_key=openai_api_key, max_tokens=200, model="gpt-4"):
    try:
        if user_id not in chatgpt_user_messages:
            chatgpt_user_messages[user_id] = []

        chatgpt_user_messages[user_id].append({"role": "user", "content": question})

        if len(chatgpt_user_messages[user_id]) > 30:
            chatgpt_user_messages[user_id].pop(0)

        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=chatgpt_user_messages[user_id],
            max_tokens=max_tokens
        )

        if not response.choices:
            return "مشکلی در دریافت پاسخ از ChatGPT به وجود آمد!"

        answer = response.choices[0].message.content
        chatgpt_user_messages[user_id].append({"role": "assistant", "content": answer})

        return answer.strip()

    except openai.OpenAIError as e:
        return f"خطای OpenAI: {str(e)}"
    except ConnectionError:
        return "اینترنت شما قطع است!"
    except Exception as e:
        return f"خطای ناشناخته: {str(e)}"


deepseek_user_messages = {}

def ask_deepseek(user_id, question, api_key=deepseek_api_key, max_tokens=200, model="deepseek-chat"):
    try:
        if user_id not in deepseek_user_messages:
            deepseek_user_messages[user_id] = []

        deepseek_user_messages[user_id].append({"role": "user", "content": question})

        if len(deepseek_user_messages[user_id]) > 30:
            deepseek_user_messages[user_id].pop(0)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": model,
            "messages": deepseek_user_messages[user_id],
            "max_tokens": max_tokens
        }

        response = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()

        answer = response.json()['choices'][0]['message']['content']
        deepseek_user_messages[user_id].append({"role": "assistant", "content": answer})

        return answer.strip()

    except requests.exceptions.RequestException as e:
        return f"خطا در ارتباط با DeepSeek: {e}"
    except Exception as e:
        return f"خطای ناشناخته در DeepSeek: {e}"


groq_user_messages = {}

def ask_groq(user_id, question, api_key=groq_api_key, max_tokens=200, model="llama3-8b-8192"):
    try:
        if user_id not in groq_user_messages:
            groq_user_messages[user_id] = []

        groq_user_messages[user_id].append({"role": "user", "content": question})

        if len(groq_user_messages[user_id]) > 30:
            groq_user_messages[user_id].pop(0)

        client = groq.Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=groq_user_messages[user_id],
            max_tokens=max_tokens
        )

        if not response.choices:
            return "مشکلی در دریافت پاسخ از Groq به وجود آمد!"

        answer = response.choices[0].message.content
        groq_user_messages[user_id].append({"role": "assistant", "content": answer})

        return answer.strip()

    except groq.APIConnectionError as e:
        return f"خطای Groq: به سرور نمیتوان وصل شد.\n{e.__cause__}"
    except groq.APIStatusError as e:
        return f"خطای شماره {e.status_code}: {e.response}"
    except ConnectionError:
        return "اینترنت شما قطع است!"
    except Exception as e:
        return f"خطای ناشناخته: {str(e)}"

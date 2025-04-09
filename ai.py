import openai
import requests
from bot import bot

openai_api_key = bot.setting[openai_api_key]
deepseek_api_key = bot.setting[deepseek_api_key]

chatgpt_user_messages = {}

def ask_chatgpt(user_id, question, api_key, max_tokens=200, model="gpt-4"):
    try:
        if user_id not in chatgpt_user_messages:
            chatgpt_user_messages[user_id] = []

        chatgpt_user_messages[user_id].append({"role": "user", "content": question})

        if len(chatgpt_user_messages[user_id]) > 30:
            chatgpt_user_messages[user_id].pop(0)

        client = openai.OpenAI(api_key=openai_api_key)
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

def ask_deepseek(user_id, question, api_key, max_tokens=200, model="deepseek-chat"):
    try:
        if user_id not in deepseek_user_messages:
            deepseek_user_messages[user_id] = []

        deepseek_user_messages[user_id].append({"role": "user", "content": question})

        if len(deepseek_user_messages[user_id]) > 30:
            deepseek_user_messages[user_id].pop(0)

        headers = {
            "Authorization": f"Bearer {deepseek_api_key}",
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
    
    

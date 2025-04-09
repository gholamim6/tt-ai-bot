import openai
import requests


def ask_chatgpt(question, max_tokens=200):
    try:
        client = openai.OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": question}],
            max_tokens=max_tokens
        )
        if not response.choices:
            return "مشکلی در دریافت پاسخ از ChatGPT به وجود آمد!"
        answer = response.choices[0].message.content
        return answer
    except openai.OpenAIError as e:
        return f" خطای OpenAi: {str(e)}"
    except ConnectionError:
        return " اینترنت شما قطع است! "
    except Exception as e:
        return f"خطای ناشناخته: {str(e)}"



def ask_deepseek(question, api_key):
    url = "https://api.deepseek.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {deepseek_api_key}",
        "Content-Type": "application/json"
    }
          
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": question}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        answer = response.json()['choices'][0]['message']['content']
        return answer.strip()
    except Exception as e:
        return f"خطا در ارتباط با DeepSeek: {e}"


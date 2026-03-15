import os
import requests

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


def expand_session_with_llm(session_struct, user_profile=None):
    """Expand structured session into human-friendly tips using OpenAI if available,
    otherwise fallback to a templated description.
    """
    prompt = f"Generate coaching tips for this session: {session_struct}."

    if OPENAI_API_KEY:
        try:
            url = 'https://api.openai.com/v1/chat/completions'
            headers = {
                'Authorization': f'Bearer {OPENAI_API_KEY}',
                'Content-Type': 'application/json'
            }
            data = {
                'model': 'gpt-4o-mini',
                'messages': [
                    {'role': 'system', 'content': 'You are a helpful fitness coach.'},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 300
            }
            resp = requests.post(url, headers=headers, json=data, timeout=10)
            if resp.status_code == 200:
                j = resp.json()
                return j['choices'][0]['message']['content'].strip()
        except Exception:
            pass

    # fallback templated description
    t = session_struct.get('notes', '')
    dur = session_struct.get('duration_min')
    desc = f"Session: {session_struct.get('type')} — {dur} minutes. {t}"
    return desc

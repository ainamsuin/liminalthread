import os
import requests
import json
import time

# 환경변수 로드
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
HF_KEY = os.getenv("HF_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_liminal_prompts():
    """1. OpenRouter 무료 모델을 통해 프롬프트 5개 생성"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
    
    system_msg = (
        "You are an AI agent generating Liminal Space concepts. "
        "Generate exactly 5 distinct, eerie, nostalgic liminal space scenes. "
        "For each, provide a 'title', a 'description' (in Korean), and a detailed 'image_prompt' (in English, focusing on 90s VHS, flash photography, lo-fi, empty, no humans). "
        "Output strictly in valid JSON format like: {\"scenes\": [{\"title\": \"...\", \"description\": \"...\", \"image_prompt\": \"...\"}]}"
    )
    
    data = {
        "model": "openrouter/free", # 완전 무료 모델 라우터 이용
        "messages": [{"role": "system", "content": system_msg}],
        "response_format": {"type": "json_object"}
    }
    
    res = requests.post(url, headers=headers, json=data).json()
    return json.loads(res['choices'][0]['message']['content'])['scenes']

def generate_image(prompt, index):
    """2. Hugging Face 무료 추론 API를 사용하여 이미지 생성"""
    # 현재 무료로 가장 퀄리티가 좋은 FLUX Schnell 모델 사용
    model_url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    headers = {"Authorization": f"Bearer {HF_KEY}"}
    
    response = requests.post(model_url, headers=headers, json={"inputs": prompt})
    if response.status_code == 200:
        file_path = f"liminal_{index}.png"
        with open(file_path, "wb") as f:
            f.write(response.content)
        return file_path
    return None

def send_to_telegram(title, desc, img_path):
    """3. 텔레그램으로 이미지와 설명 전송"""
    caption = f"🌌 *{title}*\n\n{desc}"
    
    if img_path and os.path.exists(img_path):
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
        with open(img_path, "rb") as photo:
            requests.post(url, data={"chat_id": TG_CHAT_ID, "caption": caption, "parse_mode": "Markdown"}, files={"photo": photo})
    else:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TG_CHAT_ID, "text": f"{caption}\n(이미지 생성 실패)"})

if __name__ == "__main__":
    try:
        scenes = get_liminal_prompts()
        for i, scene in enumerate(scenes):
            img_file = generate_image(scene['image_prompt'], i)
            send_to_telegram(scene['title'], scene['description'], img_file)
            time.sleep(3) # 텔레그램 API 방어용 단기 슬립
    except Exception as e:
        print(f"에러 발생: {e}")

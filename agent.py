import os
import requests
import json
import time

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
HF_KEY = os.getenv("HF_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_liminal_prompts():
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com", # OpenRouter 필수 권장 헤더
        "X-Title": "Liminal Agent"
    }
    
    system_msg = (
        "You are an AI agent generating Liminal Space concepts. "
        "Generate exactly 5 distinct, eerie, nostalgic liminal space scenes. "
        "For each, provide a 'title', a 'description' (in Korean), and a detailed 'image_prompt' (in English). "
        "Output strictly in valid JSON format like: {\"scenes\": [{\"title\": \"...\", \"description\": \"...\", \"image_prompt\": \"...\"}]}"
    )
    
   data = {
        "model": "meta-llama/llama-3-8b-instruct:free",
        "messages": [{"role": "system", "content": system_msg}],
        "response_format": {"type": "json_object"}
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code != 200:
        print(f"❌ OpenRouter API 연결 자체 실패 (코드 {response.status_code}): {response.text}")
        return []
        
    res_json = response.json()
    
    # 💡 'choices' 키가 없는 경우(에러 발생 시) 응답 전문을 출력하도록 안전장치 추가
    if 'choices' not in res_json:
        print(f"❌ OpenRouter가 에러를 반환했습니다. 반환된 데이터:\n{json.dumps(res_json, indent=2)}")
        return []
        
    raw_content = res_json['choices'][0]['message']['content']
    print(f"🤖 AI가 생성한 원본 텍스트:\n{raw_content}")
    
    return json.loads(raw_content)['scenes']

def generate_image(prompt, index):
    model_url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    headers = {"Authorization": f"Bearer {HF_KEY}"}
    
    try:
        response = requests.post(model_url, headers=headers, json={"inputs": prompt}, timeout=30)
        if response.status_code == 200:
            file_path = f"liminal_{index}.png"
            with open(file_path, "wb") as f:
                f.write(response.content)
            return file_path
        else:
            print(f"⚠️ 이미지 생성 실패 (코드 {response.status_code}): {response.text}")
    except Exception as e:
        print(f"⚠️ 이미지 API 호출 중 예외 발생: {e}")
    return None

def send_to_telegram(title, desc, img_path):
    caption = f"🌌 *{title}*\n\n{desc}"
    
    if img_path and os.path.exists(img_path):
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
        with open(img_path, "rb") as photo:
            res = requests.post(url, data={"chat_id": TG_CHAT_ID, "caption": caption, "parse_mode": "Markdown"}, files={"photo": photo})
    else:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        res = requests.post(url, data={"chat_id": TG_CHAT_ID, "text": f"{caption}\n(이미지 생성 실패)", "parse_mode": "Markdown"})
    
    if res.status_code != 200:
        print(f"❌ 텔레그램 전송 실패 (코드 {res.status_code}): {res.text}")

if __name__ == "__main__":
    try:
        scenes = get_liminal_prompts()
        if not scenes:
            print("❌ 생성된 장면이 없어 스크립트를 종료합니다.")
        else:
            for i, scene in enumerate(scenes):
                img_file = generate_image(scene['image_prompt'], i)
                send_to_telegram(scene['title'], scene['description'], img_file)
                time.sleep(3)
            print("🎉 모든 에이전트 임무 완료!")
    except Exception as e:
        print(f"💥 스크립트 실행 중 치명적 에러 발생: {e}")

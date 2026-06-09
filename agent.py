import os
import requests
import json
import time

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
HF_KEY = os.getenv("HF_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_active_free_models():
    """1. OpenRouter에서 무료 모델을 가져와 최신/고성능 순으로 정렬합니다."""
    url = "https://openrouter.ai/api/v1/models"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            all_models = response.json().get('data', [])
            free_models_data = [m for m in all_models if ':free' in m['id']]
            
            def evaluate_model_performance(model):
                model_id = model['id'].lower()
                context_length = model.get('context_length', 0)
                
                priority_score = 0
                if 'qwen-2.5' in model_id or 'qwen-3' in model_id:
                    priority_score = 50
                elif 'llama-3.3' in model_id or 'llama-3.1' in model_id or 'llama-3.2' in model_id:
                    priority_score = 40
                elif 'gemma-2' in model_id:
                    priority_score = 30
                elif 'phi-3' in model_id:
                    priority_score = 20
                
                return (priority_score, context_length)
            
            free_models_data.sort(key=evaluate_model_performance, reverse=True)
            sorted_ids = [m['id'] for m in free_models_data]
            print(f"🎯 [정렬 완료] 최신/고성능 탑재 1순위 모델: {sorted_ids[0] if sorted_ids else '없음'}")
            return sorted_ids
            
    except Exception as e:
        print(f"⚠️ 무료 모델 목록 조회 및 정렬 중 오류 발생: {e}")
    
    return ["openrouter/free"]

def get_liminal_prompts():
    """2. 단일 시각적 앵커와 극도의 몽환적 미학을 결합한 5단 시퀀스를 생성합니다."""
    free_models = get_active_free_models()
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "Dreamcore Agent"
    }
    
    # 💡 몽환적 미학(Ethereal Dreamcore) 및 시각적 앵커(Visual Anchor) 강제 주입
    system_msg = (
        "You are an expert cinematic Dreamcore director specializing in ethereal, nostalgic, and deeply surreal dreamscapes.\n\n"
        "--- 🚨 CRITICAL CONTINUITY MANDATE: THE VISUAL ANCHOR 🚨 ---\n"
        "To ensure an absolute, flawless connection between all 5 cuts, you must establish EXACTLY ONE 'Visual Anchor' that physically exists and is tracked across the entire video. Choose one from the pool below or invent a similar singular element for this generation:\n"
        "- Anchor 1: A single, endless glowing neon pastel pink wire running continuously along the ground.\n"
        "- Anchor 2: A perfect straight line of slowly floating, glowing white ceramic spheres suspended in mid-air.\n"
        "- Anchor 3: A single set of copper railway tracks laid over impossible terrains.\n\n"
        "Every single cut must follow or frame this EXACT same anchor. Cut N must begin exactly where the camera perspective of Cut N-1 left off, tracing the path of the anchor deeper into the dreamscape. This guarantees a seamless macro-narrative.\n\n"
        "--- 🌌 ETHEREAL DREAMCORE AESTHETICS (Extreme Dream-logic) ---\n"
        "Shift completely away from gritty, dark horror. The vibe must be beautiful, nostalgic, airy, and deeply melancholic—like a half-forgotten childhood memory melting away:\n"
        "- Scale & Atmosphere: Vast, grand, infinite spaces flooded with thick, glowing volumetric fog and soft mist. Everything is drenched in a perpetual, surreal pastel twilight or hazy golden hour sky (lavender, soft peach, mint green, faded cream).\n"
        "- Surreal Architecture: Giant marble archways rising out of an endless sea of calm, glass-like water; massive open-air malls with no walls where the floors are covered in soft, perfect green grass; colossal columns supporting clouds instead of a roof.\n"
        "- Framing: The scenes should be profoundly static, calm, and frozen in time. No internal chaos. Let the camera breathe with an organic, nearly unnoticeable soft drift, capturing the absolute stillness of a dream.\n\n"
        "--- ANTI-CGI REALISM RULES ---\n"
        "Avoid terms like 'photorealistic' or '3D render'. Describe vintage analog film aesthetics to grounding the unreality: overexposed lens bloom, hazy soft-focus look, dream-like light leaks, fine 16mm organic film grain, soft halation around glowing edges, and desaturated, nostalgic retro color grading.\n\n"
        "--- OUTPUT FORMAT ---\n"
        "Output must be strictly valid JSON matching this schema (all text fields must be entirely in ENGLISH):\n"
        "{\n"
        "  \"series_title\": \"[A highly intriguing, poetic, viral-ready video title about this specific dream path]\",\n"
        "  \"scenes\": [\n"
        "    {\n"
        "      \"title\": \"Cut [1-5]: [Sequential Stage Name] - Tracking the [Chosen Anchor Name]\",\n"
        "      \"description\": \"[Explain exactly how the camera moves from the previous shot's terminal point along the visual anchor, describing the immense scale and dreamy pastel atmosphere in English]\",\n"
        "      \"video_prompt\": \"[8-second English text-to-video prompt capturing the static/slow drift framing, the continuous visual anchor, soft-focus lens bloom, and 16mm analog dream texture]\"\n"
        "    }\n"
        "  ]\n"
        "}"
    )
    
    for model_id in free_models:
        print(f"🔄 [프롬프트 생성 시도] 사용 모델: {model_id}")
        data = {
            "model": model_id,
            "messages": [{"role": "system", "content": system_msg}],
            "response_format": {"type": "json_object"}
        }
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                res_json = response.json()
                if 'choices' in res_json:
                    raw_content = res_json['choices'][0]['message']['content']
                    print(f"✅ [성공] {model_id} 모델이 시각적 앵커 기반의 몽환적 서사 구성을 마쳤습니다.")
                    return json.loads(raw_content)
            print(f"⚠️ [우회] {model_id} 에러 발생 (코드 {response.status_code}). 차선책으로 이동.")
        except Exception as e:
            print(f"⚠️ {model_id} 예외 발생: {e}. 차선책으로 이동.")
        time.sleep(1)
    return {}

def generate_image(prompt, index):
    """3. 429 우회 재시도 및 백업 모델 아키텍처가 탑재된 이미지 렌더링 함수"""
    target_models = [
        "black-forest-labs/FLUX.1-schnell",
        "stabilityai/stable-diffusion-xl-base-1.0",
        "SG161222/RealVisXL_V4.0"
    ]
    headers = {"Authorization": f"Bearer {HF_KEY}"}
    
    for model_path in target_models:
        model_url = f"https://router.huggingface.co/hf-inference/models/{model_path}"
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                print(f"🎨 [이미지 생성 시도] 모델: {model_path} ({attempt + 1}/{max_retries})")
                response = requests.post(model_url, headers=headers, json={"inputs": prompt}, timeout=60)
                
                if response.status_code == 200:
                    file_path = f"liminal_{index}.png"
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    print(f"✅ [렌더링 성공] {model_path}를 통해 이미지를 확보했습니다.")
                    return file_path
                
                elif response.status_code == 429:
                    wait_time = 7 * (attempt + 1)
                    print(f"⚠️ [Rate Limit 429] 허깅페이스 제한 감지. {wait_time}초 후 재시도합니다...")
                    time.sleep(wait_time)
                else:
                    print(f"⚠️ 이미지 생성 에러 (코드 {response.status_code}). 차선책 처리 진행.")
                    break
                    
            except Exception as e:
                print(f"⚠️ 이미지 API 통신 예외 발생: {e}")
                time.sleep(3)
        
        print(f"🔄 {model_path} 제한 초과로 다음 백업 모델로 전형합니다.")
    
    return None

def send_to_telegram(series_title, title, desc, img_path):
    """4. 텔레그램으로 최종 흥미 유발 타이틀과 컷 가이드 전송"""
    caption = f"✨ *Dreamcore Video:* {series_title}\n\n🎬 *{title}*\n*Description:* {desc}"
    
    if img_path and os.path.exists(img_path):
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
        with open(img_path, "rb") as photo:
            res = requests.post(url, data={"chat_id": TG_CHAT_ID, "caption": caption, "parse_mode": "Markdown"}, files={"photo": photo})
    else:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        res = requests.post(url, data={"chat_id": TG_CHAT_ID, "text": f"{caption}\n⚠️ (Image Generation Timeout/429)", "parse_mode": "Markdown"})
    
    if res.status_code != 200:
        print(f"❌ 텔레그램 전송 실패 (코드 {res.status_code}): {res.text}")

if __name__ == "__main__":
    try:
        res_data = get_liminal_prompts()
        scenes = res_data.get('scenes', [])
        series_title = res_data.get('series_title', 'A Memory That Never Happened')
        
        if not scenes:
            print("❌ 모든 무료 모델 리스트를 순회했으나 프롬프트 데이터 확보에 실패했습니다.")
        else:
            for i, scene in enumerate(scenes):
                img_file = generate_image(scene['video_prompt'], i)
                send_to_telegram(series_title, scene['title'], scene['description'], img_file)
                time.sleep(6)
            print("🎉 모든 에이전트 임무 완료!")
    except Exception as e:
        print(f"💥 스크립트 실행 중 치명적 에러 발생: {e}")

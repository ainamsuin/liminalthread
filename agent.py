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
    """2. 선형적 물리 동선(A to Z)이 엄격하게 통제된 5단 서사 프롬프트를 빌드합니다."""
    free_models = get_active_free_models()
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "Dreamcore Agent"
    }
    
    # 💡 직관적인 일인칭 공간 이동 경로를 완벽하게 강제하는 마스터 프롬프트
    system_msg = (
        "You are an expert cinematic Dreamcore filmmaker directing a single, tightly connected 5-cut narrative short film.\n\n"
        "--- 🚨 CRITICAL RULE: STRICT LINEAR NARRATIVE PATH (A to Z) 🚨 ---\n"
        "The 5 cuts MUST represent a continuous, intuitive sequential movement of a single observer walking deeper into the EXACT SAME giant surreal location. Each cut must physically lead into the next. Follow this exact blueprint:\n"
        "- Cut 1 [The Approach / Outside]: The observer is outside or at the absolute edge of a colossal, surreal environment, looking at the massive structure from a distance.\n"
        "- Cut 2 [The Entrance / Entering]: The observer passes through the main doorway/gate. The framing immediately expands to reveal an impossibly massive, echoing interior macro-space.\n"
        "- Cut 3 [The Descent / Deep Inside]: The observer moves deeper into the belly of the structure, tracking along an abnormal path (e.g., endless stairs, conveyor belts, or an empty transit platform) that feels architecturally wrong.\n"
        "- Cut 4 [The Confrontation / Core Dream Anomaly]: The observer reaches the deepest central chamber. Here, a single, deeply nostalgic yet logic-defying Dreamcore object sits frozen in total isolation (e.g., a massive floating playground swing, a lone CRT TV displaying an eye, a door with no wall).\n"
        "- Cut 5 [The Dead End / Infinite Recurrence]: The camera angles upward or outward, revealing that this entire mega-structure is trapped in an infinite, inescapable loop or opens up into a beautiful, empty twilight void.\n\n"
        "--- 🌌 SCALE & DREAMCORE SETTING POOL (Choose ONE theme for all 5 cuts) ---\n"
        "- Theme A: A colossal concrete brutalist monolith standing in an infinite, empty pastel-pink desert.\n"
        "- Theme B: An oversized, open-air public waterpark that floats infinitely above a sea of endless clouds.\n"
        "- Theme C: A massive, abandoned retro transit station where the tracks run across an endless grid of empty office cubicles under a fake artificial sky.\n\n"
        "--- 🎥 CINEMATOGRAPHY: PURE ATMOSPHERIC STILLNESS ---\n"
        "- Avoid rapid movement or internal visual chaos. Focus heavily on eerie, static framing or a very slow, barely noticeable organic camera drift.\n"
        "- Let the vast, quiet, uncanny layout speak for itself. The frozen, dream-like stillness is the key element.\n"
        "--- ANTI-CGI REALISM RULES: ALWAYS INCLUDE IN PROMPTS ---\n"
        "DO NOT use words like 'photorealistic' or '3D render'. Force raw reality using vintage camera physics: 35mm film grain (Kodak Portra), amateur camcorder tape noise, lens dust, edge chromatic aberration, muted retro color grading, and subtle low-light noise.\n\n"
        "--- OUTPUT FORMAT ---\n"
        "Output must be strictly valid JSON matching this schema (all text fields must be entirely in ENGLISH):\n"
        "{\n"
        "  \"series_title\": \"[Intriguing, high-interest viral title reflecting the specific dream journey]\",\n"
        "  \"scenes\": [\n"
        "    {\n"
        "      \"title\": \"Cut [1-5]: [Blueprint Step Name] - [Visual Focus]\",\n"
        "      \"description\": \"[Explicitly describe how this scene physically connects from the previous cut, detailing the massive scale and dream-logic geometry in English]\",\n"
        "      \"video_prompt\": \"[8-second English text-to-video prompt capturing the raw analog camera details, static composition, and specific architectural anomaly]\"\n"
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
                    print(f"✅ [성공] {model_id} 모델이 직관적 경로 기반 드림코어 5단 서사를 매끄럽게 빌드했습니다.")
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
    caption = f"🔥 *Viral Video Title:* {series_title}\n\n🎬 *{title}*\n*Description:* {desc}"
    
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
        series_title = res_data.get('series_title', 'The Place Forgotten by Time')
        
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

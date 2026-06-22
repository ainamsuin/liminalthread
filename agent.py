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
    """2. 5컷 연동, 포근한 드림코어 공간 및 300자 내외 요약 규칙이 주입된 프롬프트 빌더"""
    free_models = get_active_free_models()
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "Whimsical Dreamcore Director"
    }
    
    # 💡 [핵심 연출 패치] 5컷 제한, 단일 컨셉 공간, 동심/포근한 무드, 컷당 300자 내외 명시
    system_msg = (
        "You are an expert cinematic director specializing in web-authenticated 'Dreamcore' and 'Liminal Space' aesthetics.\n"
        "Your task is to direct a single, visually continuous 5-cut narrative sequence. Each cut is exactly 7 to 8 seconds long.\n\n"
        "--- 📐 UNIFIED FRAMING MANDATE: DISTANT EXTREME WIDE SHOTS ONLY ---\n"
        "- Every single cut (Cuts 1 to 5) must strictly utilize an Extreme Wide Shot (EWS) or a Distant Establishing Shot.\n"
        "- The framing must remain perfectly still, frozen, and locked-off on a static tripod for the entire duration of every shot. No camera movement.\n\n"
        "--- 🚨 SINGLE CONCEPTS & WHIMSICAL DREAMCORE STYLE ---\n"
        "- Unified Location Concept: Select EXACTLY ONE massive child-centric nostalgic location for all 5 cuts (e.g., an endless pastel indoor play center, a colossal whimsical daycare void, or an infinite soft-tiled fantasy pool). Do not change the overall location theme between cuts.\n"
        "- Atmosphere: The space must feel completely vacant and empty, yet intensely nostalgic and whimsical. It should evoke childhood comfort and innocence rather than fear. It must feel strange and dreamlike, but absolutely peaceful, warm, and non-threatening (no creepy or horrific elements).\n"
        "- Visual Specifications: Use vast, sprawling macro layouts, soft pastel tones, warm yellow fluorescent grids, hazy light bloom (halation), and low-fi vintage flash photography artifacts with flat static shadows.\n"
        "- Spatial Permanence: The space itself must remain structurally fixed and solid during the shot.\n\n"
        "--- 📜 CONCISE DESCRIPTION RULE (300 Characters Target) ---\n"
        "- The relationship between cuts must be causally linked, moving deeper into different angles of the same massive nostalgic complex.\n"
        "- The 'description' field for EACH cut MUST be concise, aiming for approximately 300 characters in English. Briefly but vividly outline the vast layout, the dreamlike pastel environment, the soft lighting bloom, and the peaceful, silent room tone.\n\n"
        "--- OUTPUT FORMAT ---\n"
        "Output must be strictly valid JSON matching this schema (all text fields must be entirely in ENGLISH):\n"
        "{\n"
        "  \"series_title\": \"[A poetic, whimsical English video title]\",\n"
        "  \"unified_space_concept\": \"[The single chosen location type, e.g., 'Infinite Pastel Indoor Playground']\",\n"
        "  \"scenes\": [\n"
        "    {\n"
        "      \"title\": \"Cut [1-5]: [Blueprint Stage Name]\",\n"
        "      \"description\": \"[A CONCISE ENGLISH NARRATIVE AIMING FOR ~300 CHARACTERS. Describe the vast vacant child-centric layout, peaceful dreamlike atmosphere, and soft halation.]\",\n"
        "      \"video_prompt\": \"[8-second English text-to-video prompt forcing a distant, PERFECTLY LOCKED-OFF EXTREME WIDE TRIPOD SHOT, massive empty dreamcore child playground architecture, vintage flash artifacts, low-fi grain, pastel tones, warm yellow lighting halation, and peaceful silent room tone.]\"\n"
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
                    print(f"✅ [성공] {model_id} 모델이 포근한 5컷 드림코어 구성을 완료했습니다.")
                    return json.loads(raw_content)
            print(f"⚠️ [우회] {model_id} 에러 발생 (코드 {response.status_code}). 차선책으로 이동.")
        except Exception as e:
            print(f"⚠️ {model_id} 예외 발생: {e}. 차선책으로 이동.")
        time.sleep(1)
    return {}

def generate_image(prompt, index):
    """3. 429 우회 및 Timeout 에러 완화를 위해 재시도 백오프를 강화한 이미지 렌더링 함수"""
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
                response = requests.post(model_url, headers=headers, json={"inputs": prompt}, timeout=90)
                
                if response.status_code == 200:
                    file_path = f"liminal_{index}.png"
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    print(f"✅ [렌더링 성공] {model_path}를 통해 {index+1}번째 초광각 프리뷰를 확보했습니다.")
                    return file_path
                
                elif response.status_code == 429:
                    wait_time = 15 * (attempt + 1)
                    print(f"⚠️ [Rate Limit 429] 허깅페이스 제한 감지. {wait_time}초 후 공격적인 재시도를 진행합니다...")
                    time.sleep(wait_time)
                else:
                    print(f"⚠️ 이미지 생성 에러 (코드 {response.status_code}). 차선책 처리 진행.")
                    break
                    
            except Exception as e:
                print(f"⚠️ 이미지 API 통신 예외 발생: {e}")
                time.sleep(3)
        
        print(f"🔄 {model_path} 제한 초과로 다음 백업 모델로 전형합니다.")
    
    return None

def send_to_telegram(unified_space_concept, series_title, title, desc, img_path):
    """4. 텔레그램으로 정제된 포근한 드림코어 5개 컷 발송"""
    caption = f"🧸 *Unified Dreamcore Void ({unified_space_concept}):* {series_title}\n\n🎬 *{title}*\n\n📜 *Detailed Narrative:* \n{desc}"
    
    if img_path and os.path.exists(img_path):
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
        with open(img_path, "rb") as photo:
            res = requests.post(url, data={"chat_id": TG_CHAT_ID, "caption": caption, "parse_mode": "Markdown"}, files={"photo": photo})
    else:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        res = requests.post(url, data={"chat_id": TG_CHAT_ID, "text": f"{caption}\n\n⚠️ (Image Generation Timeout/429 - Preview FAILED)", "parse_mode": "Markdown"})
    
    if res.status_code != 200:
        print(f"❌ 텔레그램 전송 실패 (코드 {res.status_code}): {res.text}")

if __name__ == "__main__":
    try:
        res_data = get_liminal_prompts()
        scenes = res_data.get('scenes', [])
        series_title = res_data.get('series_title', 'A Peaceful Echo')
        unified_space_concept = res_data.get('unified_space_concept', 'Whimsical Void')
        
        if not scenes:
            print("❌ 모든 무료 모델 리스트를 순회했으나 데이터 확보에 실패했습니다.")
        else:
            print(f"🚀 총 {len(scenes)}개의 '단일 컨셉 초광각 고정형 드림코어' 시퀀스 생성을 시작합니다.")
            for i, scene in enumerate(scenes):
                img_file = generate_image(scene['video_prompt'], i)
                send_to_telegram(unified_space_concept, series_title, scene['title'], scene['description'], img_file)
                time.sleep(12) # 429 API 보호 쿨다운
            print("🎉 5컷 마스터 디렉터 에이전트 미션 완수!")
    except Exception as e:
        print(f"💥 스크립트 실행 중 치명적 에러 발생: {e}")

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
    """2. 오직 필요한 사양만 긍정문으로 주입한 리셋된 프롬프트 엔진"""
    free_models = get_active_free_models()
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "Pure Reset Dreamcore Director"
    }
    
    # 💡 [프롬프트 원점 리셋] 금지어 삭제, 오직 해야 할 'EWS 고정형 드림코어 사양'만 확실히 명시
    system_msg = (
        "You are an expert cinematic director specializing in web-authenticated 'Liminal Space', 'The Backrooms', and 'Dreamcore' aesthetics.\n"
        "Your task is to direct a single, visually continuous 4-cut narrative sequence. Each cut is exactly 7 to 8 seconds long.\n\n"
        "--- 📐 UNIFIED FRAMING MANDATE: DISTANT EXTREME WIDE SHOTS ONLY ---\n"
        "- Every single cut (Cuts 1 to 4) must strictly utilize an Extreme Wide Shot (EWS) or a Distant Establishing Shot.\n"
        "- Position the camera at a far-off, fixed vantage point to capture the grand, macro-scale layout of the entire building or the massive interior space from afar.\n"
        "- The framing must remain perfectly still, frozen, and locked-off on a static tripod for the entire duration of the shot.\n\n"
        "--- 🚨 DREAMCORE & LIMINAL VISUAL ARCHETYPES ---\n"
        "- Environment: Ground the scenes in vacant 1990s to 2000s nostalgic spaces. Focus exclusively on locations such as empty indoor playgrounds, dead shopping malls, vacant school corridors, sterile tiled indoor swimming pools, or fast-food kids zones.\n"
        "- Lighting & Color: Apply a distinct aesthetic palette consisting of soft pastel tones, yellow fluorescent lighting grid illumination, and heavy hazy light bloom (halation).\n"
        "- Camera Quality: Replicate vintage old film textures, low-fi noise, and the flat lighting artifacts of retro consumer flash photography.\n"
        "- Spatial Rule: The architectural layout must remain entirely fixed, solid, and structurally permanent during the shot. The space must look realistic, yet feature an uncanny, strange architectural boundary or subtle spatial error in its construction.\n\n"
        "--- ⛓️ VISUAL CONTINUITY & HYPER-DETAILED NARRATIVE (1000 Characters Target) ---\n"
        "- Enforce strict visual continuity across the 4 cuts. Each scene must logically inherit the layout of the previous space, moving deeper into the single massive nostalgic complex.\n"
        "- The 'description' field for EACH cut MUST be an extremely dense, long-form narrative exposition in English, aiming for approximately 1000 characters. You must meticulously detail: the macro architectural geometry, the precise positioning of the distant camera standpoint, the behavior of the fluorescent light sources, the exact nostalgic textures (e.g., specific scuffs on pastel playground plastic, faded carpet patterns), and the deep echoing room tone.\n\n"
        "--- OUTPUT FORMAT ---\n"
        "Output must be strictly valid JSON matching this schema (all text fields must be entirely in ENGLISH):\n"
        "{\n"
        "  \"series_title\": \"[A poetic, nostalgia-driven English video title]\",\n"
        "  \"chosen_location_type\": \"[e.g., '90s vacant indoor playground', 'abandoned pastel mall void']\",\n"
        "  \"scenes\": [\n"
        "    {\n"
        "      \"title\": \"Cut [1-4]: [Blueprint Stage Name]\",\n"
        "      \"description\": \"[AN EXTREMELY DENSE, LONG-FORM ENGLISH NARRATIVE AIMING FOR ~1000 CHARACTERS. Detail the macro layout, the structural connection to the previous space, the distant static perspective, lighting bloom, and deep room tone.]\",\n"
        "      \"video_prompt\": \"[8-second English text-to-video prompt forcing a distant, PERFECTLY LOCKED-OFF EXTREME WIDE TRIPOD SHOT, macro dreamcore architecture, vintage flash photography artifacts, low-fi film grain, pastel tones, yellow fluorescent light halation, and quiet ambient room tone.]\"\n"
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
                    print(f"✅ [성공] {model_id} 모델이 리셋된 드림코어 4컷 구성을 완료했습니다.")
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

def send_to_telegram(chosen_location_type, series_title, title, desc, img_path):
    """4. 텔레그램으로 정제된 드림코어 4개 컷 발송"""
    caption = f"🏢 *Extreme Wide Static Dreamcore ({chosen_location_type}):* {series_title}\n\n🎬 *{title}*\n\n📜 *Detailed Narrative:* \n{desc}"
    
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
        series_title = res_data.get('series_title', 'A Static Void')
        chosen_location_type = res_data.get('chosen_location_type', 'Nostalgic Void')
        
        if not scenes:
            print("❌ 모든 무료 모델 리스트를 순회했으나 데이터 확보에 실패했습니다.")
        else:
            print(f"🚀 총 {len(scenes)}개의 '초광각 고정형 드림코어' 시퀀스 생성을 시작합니다.")
            for i, scene in enumerate(scenes):
                img_file = generate_image(scene['video_prompt'], i)
                send_to_telegram(chosen_location_type, series_title, scene['title'], scene['description'], img_file)
                time.sleep(12) # 429 API 보호 쿨다운
            print("🎉 4컷 리셋 마스터 디렉터 에이전트 미션 완수!")
    except Exception as e:
        print(f"💥 스크립트 실행 중 치명적 에러 발생: {e}")

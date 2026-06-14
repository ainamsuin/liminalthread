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
    """2. 웹 실기반의 드림코어/백룸 개념과 완벽히 고정된 카메라 샷을 생성하는 프롬프트를 빌드합니다."""
    free_models = get_active_free_models()
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "Static Dreamcore Director"
    }
    
    # 💡 [핵심 연출 패치] PERFECTLY STATIC CAMERA 및 DREAMCORE 비주얼 정의 주입
    system_msg = (
        "You are an expert cinematic director specializing in web-authenticated 'Liminal Space', 'The Backrooms', and especially 'Dreamcore' aesthetics.\n"
        "Your task is to direct a single, visually continuous 10-cut narrative sequence. Each cut is exactly 7 to 8 seconds long.\n\n"
        "--- 🚨 CRITICAL BAN: ABSOLUTE PROHIBITIONS (STRICTLY FORBIDDEN) 🚨 ---\n"
        "1. NO CAMERA MOVEMENT: ABSOLUTELY ZERO Dolly, Zero Walking, Zero Pan, Zero Tilt, Zero Roll, Zero Zoom. The camera must be PERFECTLY LOCKED-OFF AND STATIC on a tripod for the entire 8 seconds. The strangeness comes from the environment's internal, frozen stillness.\n"
        "2. NO TEXT: No text, letters, signs, numbers, captions, watermarks, or overlays anywhere in the frame.\n"
        "3. NO PEOPLE: Completely vacant spaces. Absolutely no human figures, shadows, silhouettes, or body parts.\n\n"
        "--- 🚨 DREAMCORE & LIMINAL VISUAL ARCHETYPES (AUTHENTIC WEB DEFINITION) 🚨 ---\n"
        "- Establish a Single Master Aesthetic Tone from real web 'Dreamcore' imagery: unsettling nostalgia, childhood memory places (90s/00s playgrounds, daycares, malls), soft pastel textures, extreme hazy light blooms (halation), overexposed light, and early vintage low-fi flash photography artifacts (harsh shadows, red-eye grain).\n"
        "- Ground scenes in real web concepts: infinite yellow-wallpapered corporate grids (Backrooms Level 0), sterile tiled indoor poolrooms (Poolrooms), 90s dead suburban malls, and hazy, sun-drenched suburban domestic voids.\n"
        "- Spatial Permanence: The space itself must NEVER morph, warp, or dissolve during the shot. The environment is fixed and solid. The eerie wrongness comes from its original, frozen architectural anomaly.\n\n"
        "--- 🚨 CONTINUITY & HYPER-DETAILED NARRATIVE (1000 Characters Target) 🚨 ---\n"
        "- Cut N must physically begin exactly where Cut N-1 left off. Maintain absolute visual continuity.\n"
        "- The 'description' field for EACH cut MUST be an extremely dense, long-form narrative exposition (~1000 characters in English). Meticulously inventory micro-textures (e.g., specific scuffs on linoleum, water stains on acoustic ceiling tiles, the specific texture of aged carpet fibers), lighting analysis (e.g., precise color temp, source like 'dim sun spill through dirty skylight'), Object inventory, air quality, sensory isolation, and breaking down the specific non-threatening focusing sound (e.g., soft ventilation whir, distant gentle echo of stillness) drawing the viewer in.\n\n"
        "--- OUTPUT FORMAT ---\n"
        "Output must be strictly valid JSON matching this schema (all text fields must be entirely in ENGLISH):\n"
        "{\n"
        "  \"series_title\": \"[A poetic, nostalgia-driven English video title]\",\n"
        "  \"chosen_culture\": \"[e.g., 'USA', 'SOUTH KOREA']\",\n"
        "  \"chosen_location\": \"[e.g., '90s daycare', 'infinite tiled poolroom']\",\n"
        "  \"scenes\": [\n"
        "    {\n"
        "      \"title\": \"Cut [1-10]: [Blueprint Stage Name] - [Unified Dreamcore Detail]\",\n"
        "      \"description\": \"[AN EXTREMELY DENSE, LONG-FORM ENGLISH NARRATIVE AIMING FOR ~1000 CHARACTERS. Meticulously inventory textures, static lights, sound design, air quality, and spatial position inheritance from the previous shot.]\",\n"
        "      \"video_prompt\": \"[8-second English text-to-video prompt forcing a PERFECTLY LOCKED-OFF STATIC TRIPOD frame, unmoving dreamcore architecture, vintage low-fi flash grain, nostalgic lighting bloom, and focusing sound. Specify the chosen sound, material textures, and non-threatening comfort.]\"\n"
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
                    print(f"✅ [성공] {model_id} 모델이 고정형 드림코어 10컷 구성을 완료했습니다.")
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
                response = requests.post(model_url, headers=headers, json={"inputs": prompt}, timeout=90) # Timeout 증가 (90s)
                
                if response.status_code == 200:
                    file_path = f"liminal_{index}.png"
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    print(f"✅ [렌더링 성공] {model_path}를 통해 {index+1}번째 고정 컷 프리뷰를 확보했습니다.")
                    return file_path
                
                elif response.status_code == 429:
                    # 💡 [기술적 완화 패치] 429 발생 시 더 길고 공격적인 백오프 대기 적용 (15s, 30s, 45s)
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

def send_to_telegram(chosen_culture, chosen_location, series_title, title, desc, img_path):
    """4. 텔레그램으로 완벽하게 제어된 정적 10개 컷과 가이드 발송"""
    caption = f"🏢 *Static Dreamcore Masterpiece ({chosen_culture} - {chosen_location}):* {series_title}\n\n🎬 *{title}*\n\n📜 *Detailed Narrative:* \n{desc}"
    
    if img_path and os.path.exists(img_path):
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
        with open(img_path, "rb") as photo:
            res = requests.post(url, data={"chat_id": TG_CHAT_ID, "caption": caption, "parse_mode": "Markdown"}, files={"photo": photo})
    else:
        # 이미지가 실패하더라도 기획서는 전송
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        res = requests.post(url, data={"chat_id": TG_CHAT_ID, "text": f"{caption}\n\n⚠️ (Image Generation Timeout/429 - Preview FAILED, but Prompts are Valid)", "parse_mode": "Markdown"})
    
    if res.status_code != 200:
        print(f"❌ 텔레그램 전송 실패 (코드 {res.status_code}): {res.text}")

if __name__ == "__main__":
    try:
        res_data = get_liminal_prompts()
        scenes = res_data.get('scenes', [])
        series_title = res_data.get('series_title', 'A Static Void')
        chosen_culture = res_data.get('chosen_culture', 'Unknown')
        chosen_location = res_data.get('chosen_location', 'Unknown')
        
        if not scenes:
            print("❌ 모든 무료 모델 리스트를 순회했으나 데이터 확보에 실패했습니다.")
        else:
            print(f"🚀 총 {len(scenes)}개의 고정형 '{chosen_culture} - {chosen_location}' 시퀀스 생성을 시작합니다.")
            for i, scene in enumerate(scenes):
                img_file = generate_image(scene['video_prompt'], i)
                send_to_telegram(chosen_culture, chosen_location, series_title, scene['title'], scene['description'], img_file)
                # 💡 [기술적 완화 패치] 이미지 생성 간 대기 시간을 기존 6초에서 12초로 증가 (API 쿼터 보호)
                time.sleep(12)
            print("🎉 10컷 마스터 디렉터 에이전트 미션 완수!")
    except Exception as e:
        print(f"💥 스크립트 실행 중 치명적 에러 발생: {e}")

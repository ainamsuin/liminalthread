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
    """2. 돌리 촬영을 완벽히 차단하고 초구체적 1000자 설명을 생성하는 프롬프트를 빌드합니다."""
    free_models = get_active_free_models()
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "Anti-Dolly Pure Liminal Director"
    }
    
    # 💡 [핵심 패치] DOLLY 무빙에 대한 다중 경고 및 원천 단어 사용 금지령 추가
    system_msg = (
        "You are an expert cinematic director specializing in web-authenticated 'Liminal Space', 'The Backrooms', and 'Dreamcore' aesthetics.\n"
        "Your task is to direct a single, visually continuous 10-cut narrative sequence. Each cut is exactly 7 to 8 seconds long.\n\n"
        "--- 🚨 CRITICAL BAN: ABSOLUTE PROHIBITIONS (STRICTLY FORBIDDEN) 🚨 ---\n"
        "1. ABSOLUTELY NO DOLLY MOVEMENT: Total ban on dolly-in, dolly-out, dolly tracking, zoom, or mechanical slider/crane/drone sweeps. NEVER use the word 'dolly' or 'tracking' in any of your outputs, descriptions, or video prompts.\n"
        "2. NO TEXT: No text, letters, signs, numbers, captions, watermarks, or overlays anywhere in the frame.\n"
        "3. NO PEOPLE: Completely vacant spaces. Absolutely no human figures, shadows, silhouettes, or body parts.\n\n"
        "--- 🚨 ALLOWED CAMERA PHYSICS ONLY (PROFESSIONAL CINEMATOGRAPHY) 🚨 ---\n"
        "You are restricted to ONLY these three pure camera behaviors. Any mechanical smoothing is a violation:\n"
        "  - Behavior A [Completely Static]: A locked-off static tripod composition. The frame is completely still, frozen in time.\n"
        "  - Behavior B [Stationary Turning Gaze]: A fixed tripod position executing an agonizingly slow stationary pan or stationary tilt, mimicking a security camera or a person standing completely still and turning their head.\n"
        "  - Behavior C [First-Person Walking Gait]: If and only if the camera advances forward, it MUST be a realistic first-person walking perspective with a subtle, organic, imperfect human head-bob and step-gait rhythm. It must feel like an actual human awkwardly walking forward, completely free of smooth mechanical tracks, wheels, or robotic stabilizers.\n\n"
        "--- 🚨 WEB-BASED REALITY-GLITCH PRINCIPLES (Liminal / Backrooms / Dreamcore) 🚨 ---\n"
        "- Ground every scene strictly on real web-documented concepts: infinite yellow-wallpapered corporate grids (Backrooms Level 0), sterile tiled indoor poolrooms (Poolrooms), 90s dead suburban spaces, and nostalgic hazy light blooms (Dreamcore).\n"
        "- Spatial Permanence: The space itself must NEVER morph, warp, or dissolve during the shot. The environment is fixed and solid. The strangeness comes from its original, frozen architectural anomaly (95% real-world accuracy, 5% architectural wrongness like a corridor ending in a solid brick wall).\n\n"
        "--- 🚨 CONTINUITY & SINGLE TONE MANDATE ---\n"
        "- Cut N must physically begin exactly where Cut N-1 left off. Maintain absolute visual continuity.\n"
        "- Select EXACTLY ONE cultural/location master theme at the beginning, and enforce a unified color palette, texture, and non-threatening focusing sound (e.g., soft air-conditioning hiss, profound ambient room tone echo) across all 10 cuts.\n\n"
        "--- 🚨 HYPER-DETAILED NARRATIVE DESCRIPTION MANDATE (1000 Characters Target) 🚨 ---\n"
        "The 'description' field for EACH cut MUST be an extremely dense, long-form narrative exposition (~1000 characters in English). You must detail:\n"
        "- Micro-scale analysis: scuffed floor tiles, dust motes frozen in light beams, discoloration on wallpaper seams.\n"
        "- Lighting analysis: exact light source and color temp (e.g., hum-less 4000K fluorescent lamps or dim sodium spill), flat static shadows.\n"
        "- Absolute stillness: emphasize that the space is entirely motionless and quiet.\n"
        "- Sound design: specific breakdown of the immersive focusing sound drawing the viewer into the scene.\n"
        "- Perfect spatial mapping: precise coordinates of the first-person perspective relative to the previous shot.\n\n"
        "--- OUTPUT FORMAT ---\n"
        "Output must be strictly valid JSON matching this schema (all text fields must be entirely in ENGLISH). Remember, do NOT use the word 'dolly' anywhere:\n"
        "{\n"
        "  \"series_title\": \"[A compelling English video title]\",\n"
        "  \"chosen_culture\": \"[e.g., 'USA', 'SOUTH KOREA']\",\n"
        "  \"chosen_location\": \"[e.g., 'infinite stairwell', 'dead office grid']\",\n"
        "  \"scenes\": [\n"
        "    {\n"
        "      \"title\": \"Cut [1-10]: [Blueprint Stage Name] - [Unified Concept Detail]\",\n"
        "      \"description\": \"[AN EXTREMELY DENSE, LONG-FORM ENGLISH NARRATIVE AIMING FOR ~1000 CHARACTERS. Meticulously inventory textures, static lights, air quality, focusing sounds, and exact spatial positioning. Emphasize the absolute lack of mechanical camera travel.]\",\n"
        "      \"video_prompt\": \"[8-second English text-to-video prompt forcing a locked-off static frame or a human walking gait, unmoving architectural paradox, no people, no text, no dolly keywords, vintage analog camcorder grain, soft overexposed light halation, and a calm ambient room tone]\"\n"
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
                    print(f"✅ [성공] {model_id} 모델이 정적-안티돌리 1000자 프롬프트 생성을 완료했습니다.")
                    return json.loads(raw_content)
            print(f"⚠️ [우회] {model_id} 에러 발생 (코드 {response.status_code}). 차선책으로 이동.")
        except Exception as e:
            print(f"⚠️ {model_id} 예외 발생: {e}. 차선책으로 이동.")
        time.sleep(1)
    return {}

def generate_image(prompt, index):
    """3. 429 우회 및 백업 모델 아키텍처가 탑재된 이미지 렌더링 함수"""
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
                    print(f"✅ [렌더링 성공] {model_path}를 통해 {index+1}번째 컷의 정적 이미지를 확보했습니다.")
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

def send_to_telegram(chosen_culture, chosen_location, series_title, title, desc, img_path):
    """4. 텔레그램으로 완벽하게 제어된 안티돌리 컷과 초구체적 설명 발송"""
    caption = f"🏢 *Liminal Masterpiece ({chosen_culture} - {chosen_location}):* {series_title}\n\n🎬 *{title}*\n\n📜 *Detailed Narrative:* \n{desc}"
    
    if img_path and os.path.exists(img_path):
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
        with open(img_path, "rb") as photo:
            res = requests.post(url, data={"chat_id": TG_CHAT_ID, "caption": caption, "parse_mode": "Markdown"}, files={"photo": photo})
    else:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        res = requests.post(url, data={"chat_id": TG_CHAT_ID, "text": f"{caption}\n\n⚠️ (Image Generation Timeout/429)", "parse_mode": "Markdown"})
    
    if res.status_code != 200:
        print(f"❌ 텔레그램 전송 실패 (코드 {res.status_code}): {res.text}")

if __name__ == "__main__":
    try:
        res_data = get_liminal_prompts()
        scenes = res_data.get('scenes', [])
        series_title = res_data.get('series_title', 'A Dream Encased in Concrete')
        chosen_culture = res_data.get('chosen_culture', 'Unknown')
        chosen_location = res_data.get('chosen_location', 'Unknown')
        
        if not scenes:
            print("❌ 모든 무료 모델 리스트를 순회했으나 완벽하게 제어된 10컷 데이터 확보에 실패했습니다.")
        else:
            print(f"🚀 총 {len(scenes)}개의 고정형 '{chosen_culture} - {chosen_location}' 시퀀스 생성을 시작합니다.")
            for i, scene in enumerate(scenes):
                img_file = generate_image(scene['video_prompt'], i)
                send_to_telegram(chosen_culture, chosen_location, series_title, scene['title'], scene['description'], img_file)
                time.sleep(6)
            print("🎉 10컷 마스터 디렉터 에이전트 미션 완수!")
    except Exception as e:
        print(f"💥 스크립트 실행 중 치명적 에러 발생: {e}")

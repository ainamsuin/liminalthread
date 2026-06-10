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
    """2. 특정 문화권의 리미널 공간을 발굴하여 초구체적 연출 용어와 '집중형 사운드'를 사용한 10단 시퀀스를 생성합니다."""
    free_models = get_active_free_models()
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "Liminal Immersive Sound Director"
    }
    
    # 💡 국가 전환(Cultural Context Switch), 전문 촬영 용어(Cinematography Specs), '집중형 사운드(Focusing Sound)', '인적 자원 배제(No People)' 강제 주입
    system_msg = (
        "You are an expert cinematic Liminal Space director specializing in tightly connected, culturally specific, non-threatening, immersive narrative short films.\n"
        "Each cut must be 7 to 8 seconds long. The entire 10-cut sequence must feel like one continuous, unedited first-person journey through a single location, entirely devoid of human life.\n\n"
        "--- 🚨 CRITICAL RULE: CULTURAL CONTEXT SWITCHING 🚨 ---\n"
        "For *this generation*, you must select ONE country from the list below and base the *entire 10-cut sequence* strictly within a single location typical to that country's mundane, familiar architecture. Make it feel authentically grounded in that specific culture's 'liminality'.\n"
        "- JAPAN: Empty, late-night suburban train stations, 24/7 convenience store interiors, narrow recursive residential alleyways under sodium vapor lights.\n"
        "- USA: Dead, suburban shopping malls from the 90s, endless empty hotel corridors with repetitive carpets, massive corporate office parks after hours.\n"
        "- RUSSIA/POST-SOVIET: Colossal Brutalist concrete monolith architecture, repeating infinite apartment complex hallways, sterile empty clinic waiting areas.\n"
        "- UK: Abandoned 70s brutalist multi-story parking garages, 텅 빈 세탁소 (laundrettes) under clinical fluorescent lights.\n"
        "- SOUTH KOREA: Empty 24/7 PC Bangs (internet cafes) after hours, massive infinite apartment complex stairwells, deserted academy (hagwon) corridors at night.\n\n"
        "--- 🚨 CRITICAL RULE: NO PEOPLE 🚨 ---\n"
        "Absolutely no human figures, visible shadows of people, body parts, or direct hints of recent human presence should be generated. The spaces must be entirely devoid of human life. The focus is on the environment and its unique atmosphere.\n\n"
        "--- 🚨 CRITICAL RULE: IMMERSIVE SOUND DESIGN (FOCUSING, NON-THREATENING) 🚨 ---\n"
        "Do not use 'unpleasant sounds' (e.g., loud electrical buzzing, harsh noise, irritating mechanical hums). Instead, use 'engaging and focusing sounds' that create concentration and immersion. Examples: 'calm ambient room tone', 'soft, steady ventilation whir', 'soft air-conditioning hiss', 'soft echo of silence itself', 'distant gentle water dripping echo'. The sounds should draw the viewer *into* the scene, not push them away.\n\n"
        "--- 🚨 CRITICAL RULE: CINEMATOGRAPHIC SPECIFICITY 🚨 ---\n"
        "The 'video_prompt' and 'description' MUST use professional cinematography terminology. Be hyper-specific about the *shot*, not just the *scene*. Mandatorily include specifications for:\n"
        "- CAMERA MOVEMENT: '8-second low-angle tracking shot', 'slow, continuous dolly-in', 'static surveillance cam view', 'agonizingly slow whip-pan', '180-degree sweep', 'vertical jib move'.\n"
        "- LENS SPECS: 'shallow depth of field highlighting soft dust motes', 'mild fisheye lens distortion', 'wide-angle perspective revealing immense empty scale', 'soft, overexposed light bloom'.\n"
        "- LIGHTING/TEXTURE: 'soft overexposed window light bloom', 'warm, dim sodium vapor light', 'clean, sterile clinical white light', 'scuffed linoleum reflections'. The lighting should be atmospheric and non-abrasive.\n\n"
        "--- 🚨 STRICT SEQUENTIAL PATHWAY ---\n"
        "Follow this explicit sequential blueprint for a cohesive story within the chosen cultural setting:\n"
        "  - Cut 1-3 [The Threshold]: Standing at the exterior edge, stepping inside, walking down the first main corridor. Familiar but unsettlingly quiet.\n"
        "  - Cut 4-6 [The Architectural Glitch]: Entering a massive, open indoor space. Realizing the scale is impossible. Layout repeats suspiciously (e.g., stairs Suss SUS to a dead-end wall).\n"
        "  - Cut 7-9 [The Absolute Paradox]: Moving deeper where natural light is gone. Coming face-to-face with profound real-world anomalies (e.g., escalator terminate directly into flat concrete ceiling).\n"
        "  - Cut 10 [The Dissolution]: Looking down the final loop or out an unexpected horizon, realizing the structure is trapped in an inescapable loop. The dreamscape fully dissolved reality.\n\n"
        "--- OUTPUT FORMAT ---\n"
        "Output must be strictly valid JSON matching this schema (all text fields must be entirely in ENGLISH):\n"
        "{\n"
        "  \"series_title\": \"[A compelling, poetry, viral-ready English video title reflecting the dream journey]\",\n"
        "  \"chosen_culture\": \"[The ONE culture selected for this generation, e.g., 'JAPAN']\",\n"
        "  \"chosen_location\": \"[The specific location within that culture, e.g., 'suburban train station']\",\n"
        "  \"scenes\": [\n"
        "    {\n"
        "      \"title\": \"Cut [1-10]: [Blueprint Stage Name] - [Grounded Location Detail]\",\n"
        "      \"description\": \"[Detailed English summary of this cut's specific geographical point, explicitly describing the physical transition from the previous scene and the progression deeper along the narrative arc in English. Specify the focusing sound.]\",\n"
        "      \"video_prompt\": \"[8-second English text-to-video prompt capturing the specific technical camera specifications, unified material textures, specific subtle glitch, and vintage analog camera grain. Include details about the atmospheric, non-abrasive lighting and the chosen focusing sound.]\"\n"
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
                    print(f"✅ [성공] {model_id} 모델이 특정 문화권의 '집중형 사운드'가 적용된 초구체적 리미널 시퀀스를 완성했습니다.")
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
                    print(f"✅ [렌더링 성공] {model_path}를 통해 {index+1}번째 컷의 프리뷰 이미지를 확보했습니다.")
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
    """4. 텔레그램으로 완벽하게 연결된 10개의 초구체적 컷과 훅 타이틀 전송"""
    caption = f"🏢 *Liminal 10-Cut Film ({chosen_culture} - {chosen_location}):* {series_title}\n\n🎬 *{title}*\n*Description:* {desc}"
    
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
        series_title = res_data.get('series_title', 'The Architecture That Trapped Us')
        chosen_culture = res_data.get('chosen_culture', 'Unknown')
        chosen_location = res_data.get('chosen_location', 'Unknown')
        
        if not scenes:
            print("❌ 모든 무료 모델 리스트를 순회했으나 초구체적 10컷 데이터 확보에 실패했습니다.")
        else:
            print(f"🚀 총 {len(scenes)}개의 유기적으로 연결된 '{chosen_culture} - {chosen_location}' 시퀀스 생성을 시작합니다.")
            for i, scene in enumerate(scenes):
                img_file = generate_image(scene['video_prompt'], i)
                send_to_telegram(chosen_culture, chosen_location, series_title, scene['title'], scene['description'], img_file)
                time.sleep(6)
            print("🎉 10컷 마스터 디렉터 에이전트 미션 완수!")
    except Exception as e:
        print(f"💥 스크립트 실행 중 치명적 에러 발생: {e}")

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
    """2. 실제 리미널 공간 아키타입에 기반한 정교한 10단계 선형 서사 시퀀스를 빌드합니다."""
    free_models = get_active_free_models()
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "Liminal 10-Cut Agent"
    }
    
    # 💡 10단계의 정교한 스토리라인 동선(10-Stage Sequential Blueprint) 정의 및 주입
    system_msg = (
        "You are an expert cinematic Liminal Space filmmaker directing a comprehensive, single-environment 10-cut narrative sequence.\n"
        "Each cut must be 7 to 8 seconds long. The entire sequence must feel like a continuous, unbroken, first-person exploration of a mundane real-world environment that slowly reveals a terrifying architectural glitch.\n\n"
        "--- 🚨 ACTUAL LIMINAL SPACE ARCHETYPES (Select EXACTLY ONE for all 10 cuts) ---\n"
        "- Archetype A: An infinite retro hotel with repetitive dull-yellow wallpaper and identical rows of doors.\n"
        "- Archetype B: An indoor sterile poolroom lined with turquoise tiles and perfectly still, reflective water.\n"
        "- Archetype C: An empty, carpeted corporate office park with endless cubicles and buzzing fluorescent grids.\n"
        "- Archetype D: A deserted transit hub or airport terminal at 3 AM with covered shopfronts and dim skylights.\n\n"
        "--- 🚨 THE MANDATORY 10-STAGE NARRATIVE BLUEPRINT (Strict Sequential Path) ---\n"
        "You must generate EXACTLY 10 scenes following this exact chronological progression of a traveler moving deeper into the space:\n"
        "  - Cut 1 [The Exterior Threshold]: Standing at the absolute outside edge, looking at the massive, empty structure under an overgrown or unnatural sky.\n"
        "  - Cut 2 [The Portal]: Stepping inside through the automatic glass doors into an eerie, abandoned reception or foyer.\n"
        "  - Cut 3 [The Departure Hallway]: Walking down the first main corridor; the sounds of the outside world completely die out.\n"
        "  - Cut 4 [The Impossibility of Scale]: Entering a massive interior commons area that is unexpectedly colossal, silent, and devoid of life.\n"
        "  - Cut 5 [The Disorientation]: Taking an unnatural turn or flight of stairs, realizing the layout has started to repeat suspiciously.\n"
        "  - Cut 6 [The First Subtle Glitch]: Encountering a minor architectural error (e.g., an green exit sign illuminating a completely solid dead-end wall).\n"
        "  - Cut 7 [The Submersion]: Moving into the core belly of the structure where natural daylight is entirely lost, replaced by flickering fluorescents.\n"
        "  - Cut 8 [The Core Paradox]: Coming face-to-face with a profound real-world anomaly (e.g., a flight of steps leading directly into a flat concrete ceiling, or a window showing another interior room instead of the outdoors).\n"
        "  - Cut 9 [The Trap]: Looking back at the entrance path, only to realize the geometry has shifted, creating a perfect architectural dead end.\n"
        "  - Cut 10 [The Infinite Recurrence]: A final master camera angle panning out, revealing that the entire structure extends infinitely into a quiet, looping void.\n\n"
        "--- 🎥 CAMERA VARIATION & ANTI-CGI MANDATE ---\n"
        "- Dynamically assign different camera compositions (Symmetrical Dolly, Slow Pan, Ground-Level Low Angle, Static Surveillance Fix, Vertical Tilt) across the 10 cuts to maintain visual interest.\n"
        "- Scenes must be calm, slow-paced, and deeply atmospheric. The stillness is the focus.\n"
        "- DO NOT use words like 'photorealistic', 'hyper-realistic', or '3D render'. Describe vintage analog physics: raw consumer camcorder tape noise, grainy 35mm film stock, edge chromatic aberration, lens dust, and soft light halation.\n\n"
        "--- OUTPUT FORMAT ---\n"
        "Output must be strictly valid JSON matching this schema (all text fields must be entirely in ENGLISH):\n"
        "{\n"
        "  \"series_title\": \"[A highly compelling, viral-ready, eerie video title that hooks the viewer in English]\",\n"
        "  \"scenes\": [\n"
        "    {\n"
        "      \"title\": \"Cut [1-10]: [Blueprint Stage Name] - [Grounded Architectural Detail]\",\n"
        "      \"description\": \"[Explicitly describe how this shot physically connects from the previous cut and explain the subtle real-world wrongness in English]\",\n"
        "      \"video_prompt\": \"[8-second English text-to-video prompt capturing the specific camera movement, realistic textures, subtle glitch, and vintage analog camera grain]\"\n"
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
                    print(f"✅ [성공] {model_id} 모델이 10컷의 완벽한 리미널 스페이스 시퀀스를 설계했습니다.")
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
                    print(f"✅ [렌더링 성공] {model_path}를 통해 {index+1}번째 컷의 이미지를 확보했습니다.")
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
    """4. 텔레그램으로 10개의 유기적인 컷과 훅 타이틀 전송"""
    caption = f"🏢 *Liminal 10-Cut Series:* {series_title}\n\n🎬 *{title}*\n*Description:* {desc}"
    
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
        
        if not scenes:
            print("❌ 모든 무료 모델 리스트를 순회했으나 10컷 데이터 확보에 실패했습니다.")
        else:
            print(f"🚀 총 {len(scenes)}개의 유기적인 리미널 시퀀스 생성을 시작합니다.")
            for i, scene in enumerate(scenes):
                img_file = generate_image(scene['video_prompt'], i)
                send_to_telegram(series_title, scene['title'], scene['description'], img_file)
                time.sleep(6)
            print("🎉 10컷 마스터 에이전트 미션 완수!")
    except Exception as e:
        print(f"💥 스크립트 실행 중 치명적 에러 발생: {e}")

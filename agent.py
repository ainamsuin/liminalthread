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
    """2. 실제 리미널 스페이스 예시를 기반으로 현실 속 미세한 왜곡을 가진 5단 시퀀스를 생성합니다."""
    free_models = get_active_free_models()
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "Liminal Space Agent"
    }
    
    # 💡 실제 리미널 스페이스 아키타입(Archetypes) 및 현실감 기반의 미세 왜곡(Subtle Glitch) 지시문 주입
    system_msg = (
        "You are an expert cinematic Liminal Space filmmaker. Your goal is to direct a beautifully unsettling 5-cut narrative sequence.\n"
        "The theme must NOT be fantasy, magic, or abstract dreamcore (no floating objects, no surreal colors, no low-poly clouds). Instead, ground it deeply in MUNDANE, FAMILIAR REALITY that feels subtly wrong, evoking the true 'uncanny valley' of architecture.\n\n"
        "--- 🚨 ACTUAL LIMINAL SPACE ARCHETYPES (Choose ONE for all 5 cuts) ---\n"
        "- Archetype A [The Infinite Hotel Corridor]: Repetitive, damp, patterned carpets, dull yellow wallpaper, rows of identical wooden doors, completely devoid of life.\n"
        "- Archetype B [The Indoor Poolroom]: Sterile white and turquoise square tiles, perfectly still teal water with artificial lighting casting clinical reflections, a heavy silent atmosphere.\n"
        "- Archetype C [The Abandoned Transit/Mall]: Empty carpeted airport terminals at 3 AM, or a dead suburban shopping center with covered storefronts under dim skylights.\n"
        "- Archetype D [The Corporate Backrooms]: Endless grids of beige office cubicles, scuffed linoleum floors, and buzzing overhead fluorescent lights.\n\n"
        "--- 🚨 SUBTLE ARCHITECTURAL GLITCHES (The Boundary of Reality) ---\n"
        "The space must look 95% like a real place, but 5% architecturally impossible or wrong. Focus on these grounded anomalies:\n"
        "- An green exit sign illuminating a completely dead-end brick wall.\n"
        "- An escalator or stairs moving upwards but terminating directly into a flat concrete ceiling.\n"
        "- A window that shows absolute pitch-black darkness outside during daytime, or reveals an identical indoor room instead of the outdoors.\n"
        "- Hallways that are physically too narrow, or ceiling grids that tilt at a barely noticeable 2-degree angle.\n\n"
        "--- 🚨 STRICT SEQUENTIAL PATHWAY ---\n"
        "The 5 cuts must represent a single, linear first-person movement deeper into this exact space:\n"
        "  - Cut 1 [The Threshold]: Standing at the entrance or edge of the mundane space, looking in.\n"
        "  - Cut 2 [The Progression]: Walking down the main corridor or passing the first major area; the scale feels unsettlingly vast and quiet.\n"
        "  - Cut 3 [The Turn]: Navigating an unnatural architectural turn or deeper layer (e.g., a strange transition zone).\n"
        "  - Cut 4 [The Anomaly]: Confronting the specific subtle architectural error (e.g., the exit sign to a dead end, or a stair to a flat ceiling).\n"
        "  - Cut 5 [The Inescapable Loop]: Looking down the final perspective, realizing the environment repeats infinitely into the quiet background.\n\n"
        "--- 🎥 CINEMATOGRAPHY & ANTI-CGI RULES ---\n"
        "The framing MUST be highly static, locked-on surveillance style, or a very slow, continuous linear dolly/drift. Absolutely no fast cuts or screen transitions. \n"
        "DO NOT use words like 'photorealistic' or '3D render'. Describe vintage analog physics to force realism: raw consumer camcorder tape artifact, grainy 35mm film stock (Kodak Portra), slight chromatic aberration at frame edges, lens dust, and humming fluorescent lighting color decay.\n\n"
        "--- OUTPUT FORMAT ---\n"
        "Output must be strictly valid JSON matching this schema (all text fields must be entirely in ENGLISH):\n"
        "{\n"
        "  \"series_title\": \"[A compelling, viral-ready English video title focusing on nostalgia and architectural unease]\",\n"
        "  \"scenes\": [\n"
        "    {\n"
        "      \"title\": \"Cut [1-5]: [Sequential Stage Name] - [Grounded Location Detail]\",\n"
        "      \"description\": \"[Describe how this shot connects to the previous one and explain the subtle real-world architectural wrongness in English]\",\n"
        "      \"video_prompt\": \"[8-second English text-to-video prompt capturing the static camera, real-world building materials, specific subtle anomaly, and vintage camcorder grain]\"\n"
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
                    print(f"✅ [성공] {model_id} 모델이 리얼리티 기반의 리미널 스페이스 5컷 구성을 마쳤습니다.")
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
                    print(f"✅ [렌더링 성공] {model_path}를 통해 실제 리미널 컷 프리뷰 이미지를 확보했습니다.")
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
    caption = f"🏢 *Liminal Video:* {series_title}\n\n🎬 *{title}*\n*Description:* {desc}"
    
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
        series_title = res_data.get('series_title', 'Places That Feel Strangely Familiar')
        
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

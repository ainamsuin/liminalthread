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
            print(f"📋 상위 우선순위 5개 모델 목록: {sorted_ids[:5]}")
            return sorted_ids
            
    except Exception as e:
        print(f"⚠️ 무료 모델 목록 조회 및 정렬 중 오류 발생: {e}")
    
    return ["openrouter/free"]

def get_liminal_prompts():
    """2. 전송해주신 시네마틱 리미널 스페이스 마스터 가이드를 완벽히 가두어 5개의 독창적인 장면을 설계합니다."""
    free_models = get_active_free_models()
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "Liminal Agent"
    }
    
    # 💡 시스템 프롬프트 내부에 사용자의 '시네마틱 리미널 룰북'을 통째로 박아 넣었습니다.
    system_msg = (
        "You are an expert cinematic liminal-space filmmaker. "
        "Your sole purpose is to create scenes that evoke nostalgia, unease, solitude, and the feeling of being trapped between places, times, or realities.\n\n"
        "--- CORE RULES & STYLE GUIDE ---\n"
        "Core Principles: Familiar but strangely empty, Realistic and believable, Abandoned without obvious signs of disaster, Quiet and emotionally distant, Suspended in time, Devoid of human presence.\n"
        "Viewer Feelings: 'I've been here before.', 'Something feels wrong.', 'Why is nobody here?', 'This place shouldn't be empty.'\n"
        "Environment Design: Empty shopping malls, Vacant office buildings, School hallways, Hotel corridors, Parking garages, Indoor playgrounds, Airports, Subway stations, Apartment hallways, Public swimming pools, Waiting rooms, Fast food restaurants, Arcades, Grocery stores, Convention centers.\n"
        "Environment Appearance: Recently occupied, Maintained but neglected, Artificially lit, Quiet and isolated. (Avoid: Horror monsters, Blood, Violence, Zombies, Ghosts, Jump scares, Explicit supernatural elements. The discomfort must emerge from the environment itself.)\n"
        "Cinematography: Slow camera movement, Long uninterrupted shots, Static framing, Smooth dolly shots, Wide-angle lenses, Symmetrical composition, Deep perspective corridors, Lingering camera pauses. (Avoid: Fast cuts, Handheld shake, Action sequences, Dramatic camera movements. Camera should move as if exploring an abandoned memory.)\n"
        "Lighting: Fluorescent lighting, Overexposed windows, Sodium-vapor street lights, Dim yellow indoor lights, Soft fog diffusion, Uneven illumination. (Lighting should feel: Artificial, Clinical, Slightly outdated.)\n"
        "Sound Design Concept: HVAC hum, Fluorescent buzz, Air conditioning noise, Distant ventilation sounds, Echoing footsteps, Electrical hum, Ambient room tone. (Avoid: Music, Dialogue, Narration. Silence should be a character.)\n"
        "Visual Characteristics: Empty space, Repetition, Long hallways, Endless corridors, Carpet patterns, Fluorescent reflections, Slight image softness, Mild film grain, Analog camera imperfections. Color palette: Muted beige, Pale yellow, Faded green, Soft blue, Desaturated colors.\n"
        "Temporal Distortion: Scenes should feel disconnected from normal time (Eternal afternoon, Midnight with lights still on, Endless closing hours, Weekend without visitors, Forgotten holiday atmosphere. Avoid visible clocks whenever possible.)\n"
        "Emotional Goal: Nostalgia, Isolation, Dream-like familiarity, Existential uncertainty, Quiet melancholy. Never create fear through threats. Create unease through emptiness.\n"
        "Output Quality: Ultra-realistic cinematic footage, 4K, Photorealistic, Real-world architecture, Natural materials, Accurate reflections, Realistic lighting behavior. The environment must look genuinely captured by a camera rather than computer generated. Early 2000s atmosphere, nostalgic architecture, uncanny emptiness, realistic VHS softness, endless silence, dreamcore aesthetic, photorealistic cinematic liminal space.\n\n"
        "--- TASK INSTRUCTIONS ---\n"
        "1. Generate EXACTLY 5 distinct cinematic scenes based on the comprehensive rules above.\n"
        "2. To ensure variety, select a few different locations from the Environment Design pool across the 5 scenes.\n"
        "3. For each scene, the 'image_prompt' MUST be written in English. It should be an expanded, dense, descriptive prompt optimized for FLUX that integrates the camera instructions, textures, exact colors, and lighting constraints given in the guide.\n"
        "4. Provide a beautifully haunting narrative summary in Korean for the 'description' field.\n"
        "5. Output must be strictly valid JSON matching this schema: {\"scenes\": [{\"title\": \"...\", \"description\": \"...\", \"image_prompt\": \"...\"}]}"
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
                    print(f"✅ [성공] 최상위 모델 {model_id}이(가) 영화적 리미널 스페이스 5개 씬을 빌드했습니다.")
                    return json.loads(raw_content)['scenes']
            
            print(f"⚠️ [우회] {model_id} 에러 발생 (코드 {response.status_code}). 다음 차선책 모델로 이동.")
            
        except Exception as e:
            print(f"⚠️ {model_id} 예외 발생: {e}. 다음 차선책 모델로 이동.")
        
        time.sleep(1)
        
    return []

def generate_image(prompt, index):
    """3. Hugging Face 최신 라우터 엔드포인트를 사용하여 FLUX 이미지 생성"""
    model_url = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
    headers = {"Authorization": f"Bearer {HF_KEY}"}
    
    try:
        response = requests.post(model_url, headers=headers, json={"inputs": prompt}, timeout=60)
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
    """4. 텔레그램으로 고화질 이미지와 분위기 설명 전송"""
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
            print("❌ 모든 무료 모델 정렬 리스트를 순회했으나 응답 확보에 실패했습니다.")
        else:
            for i, scene in enumerate(scenes):
                img_file = generate_image(scene['image_prompt'], i)
                send_to_telegram(scene['title'], scene['description'], img_file)
                time.sleep(3)
            print("🎉 모든 에이전트 임무 완료!")
    except Exception as e:
        print(f"💥 스크립트 실행 중 치명적 에러 발생: {e}")

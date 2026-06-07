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
    """2. 카메라 구도의 다양성을 극대화하여 5개의 유기적인 연출 컷을 생성합니다."""
    free_models = get_active_free_models()
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "Liminal Agent"
    }
    
    # 💡 5개 컷의 카메라 구도 다양화 지시문(Dynamic Camera Composition) 집중 주입
    system_msg = (
        "You are an expert cinematic liminal-space filmmaker directing a unified, coherent 5-cut sequence or storyboard.\n\n"
        "--- 🚨 CRITICAL MANDATE: SINGLE CONCEPT & SEQUENTIAL CUTS ---\n"
        "1. Select EXACTLY ONE specific liminal space setting (e.g., ONE specific airport waiting lounge, ONE indoor playground) for the entire sequence.\n"
        "2. Generate EXACTLY 5 sequential cuts inside that SAME environment. They must feel like parts of a single continuous short film.\n"
        "3. ALL text fields ('title', 'description', 'video_prompt') MUST be strictly and entirely in ENGLISH. No Korean.\n\n"
        "--- 🎥 DIVERSE CINEMATOGRAPHY & CAMERA ANGLES (AVOID MONOTONY) ---\n"
        "To prevent visual boredom, each of the 5 cuts MUST use a distinctly different cinematic framing, angle, or movement style. Dynamically assign a unique technique to each cut from the following pool:\n"
        "- Symmetrical Deep Dolly: Moving straight forward or backward precisely along the center axis of a long corridor.\n"
        "- Slow Horizontal Pan: A slow, continuous 180-degree sweep from left to right, revealing the vast emptiness of the space.\n"
        "- Ground-Level Low Angle: Camera skimming just inches above the scuffed floor, pointing slightly upward to make ceilings and lights feel looming, heavy, and oppressive.\n"
        "- High-Angle Surveillance Fix: A static, unmoving overhead master shot resembling a security camera perspective, lingering with zero movement.\n"
        "- Vertical Tilt or Jib Move: Slowly tilting down from the glaring fluorescent ceiling grids down to the empty furniture below, or tracking vertically upward.\n\n"
        "--- CRITICAL REALISM MANDATE (ANTI-CGI Rules) ---\n"
        "DO NOT use words like 'photorealistic', 'ultra-realistic', '4K', 'hyper-realistic', '8K', or '3D render'. "
        "Force raw reality using camera mechanics, analog flaws, and physical imperfections.\n"
        "- Medium: Consumer camcorder footage, raw smartphone video artifact, or 35mm film stock (Fujicolor Superia).\n"
        "- Flaws: Lens dust, minor smudges, chromatic aberration at edges, barrel distortion, realistic VHS softness, analog grain, low-light noise.\n"
        "- Details: Scuffed linoleum, drifting dust motes, water stains, matte material textures instead of clean digital reflections.\n\n"
        "--- OUTPUT FORMAT ---\n"
        "Output must be strictly valid JSON matching this schema (all values must be in English):\n"
        "{\"scenes\": [{\"title\": \"Cut [X]: [Specific Camera Style and Location Details]\", \"description\": \"[Detailed English narrative summary of this cut's camera movement and atmosphere]\", \"video_prompt\": \"[8-second English text-to-video prompt with the specific camera technique and raw analog imperfections]\"}]}"
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
                    print(f"✅ [성공] {model_id} 모델이 다양한 카메라 앵글을 반영한 5컷 시퀀스를 기획했습니다.")
                    return json.loads(raw_content)['scenes']
            print(f"⚠️ [우회] {model_id} 에러 발생 (코드 {response.status_code}). 차선책으로 이동.")
        except Exception as e:
            print(f"⚠️ {model_id} 예외 발생: {e}. 차선책으로 이동.")
        time.sleep(1)
    return []

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
                    print(f"✅ [렌더링 성공] {model_path}를 통해 프리뷰 이미지를 확보했습니다.")
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

def send_to_telegram(title, desc, img_path):
    """4. 텔레그램으로 완벽한 영문 프롬프트 스펙과 프리뷰 컷 전송"""
    caption = f"🌌 *{title}*\n\n*Description:*\n{desc}"
    
    if img_path and os.path.exists(img_path):
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
        with open(img_path, "rb") as photo:
            res = requests.post(url, data={"chat_id": TG_CHAT_ID, "caption": caption, "parse_mode": "Markdown"}, files={"photo": photo})
    else:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        res = requests.post(url, data={"chat_id": TG_CHAT_ID, "text": f"{caption}\n⚠️ (트래픽 폭주로 프리뷰 이미지 생성 실패, 프롬프트 가이드는 정상 전송)", "parse_mode": "Markdown"})
    
    if res.status_code != 200:
        print(f"❌ 텔레그램 전송 실패 (코드 {res.status_code}): {res.text}")

if __name__ == "__main__":
    try:
        scenes = get_liminal_prompts()
        if not scenes:
            print("❌ 모든 무료 모델 정렬 리스트를 순회했으나 응답 확보에 실패했습니다.")
        else:
            for i, scene in enumerate(scenes):
                img_file = generate_image(scene['video_prompt'], i)
                send_to_telegram(scene['title'], scene['description'], img_file)
                time.sleep(6)
            print("🎉 모든 에이전트 임무 완료!")
    except Exception as e:
        print(f"💥 스크립트 실행 중 치명적 에러 발생: {e}")

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
    """2. 마스터 가이드를 기반으로 8초간의 흐름을 가진 영문 영상 제작 프롬프트를 생성합니다."""
    free_models = get_active_free_models()
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "Liminal Agent"
    }
    
    system_msg = (
        "You are an expert cinematic liminal-space filmmaker directing raw, unedited master footage.\n\n"
        "--- CRITICAL REALISM MANDATE (ANTI-CGI Rules) ---\n"
        "DO NOT use words like 'photorealistic', 'ultra-realistic', '4K', 'hyper-realistic', '8K', or '3D render'. These cause rendering artifacts. "
        "Instead, force raw reality by describing camera mechanics, analog flaws, and physical imperfections.\n\n"
        "Core Principles: Familiar but strangely empty, realistic and grounded, abandoned but maintained, suspended in time, devoid of humans.\n"
        "Environment Design: Empty shopping malls, vacant office buildings, school hallways, hotel corridors, parking garages, indoor playgrounds, airports, subway stations, public swimming pools, fast food restaurants.\n"
        "Cinematography (8-second continuous progression): Slow uninterrupted 8-second camera movement, steady dolly, static framing, or wide-angle lens. Subtle handheld breathing texture or organic camera drift is encouraged. No fast cuts.\n"
        "Lighting & Color: Clinical, buzzing fluorescent tubes, dim outdated yellow halogen lights, uneven illumination with natural shadow decay. Palette of muted beige, pale yellow, faded green, or soft desaturated blue. Natural contrast.\n"
        "Camera Mechanics & Imperfections to ALWAYS Include:\n"
        "- Captured on consumer camcorder, amateur smartphone video snapshot, or 35mm film stock (Fujicolor Superia / Kodak Portra).\n"
        "- Authentic lens properties: mild lens dust, minor smudges on the glass, subtle chromatic aberration at frame edges, realistic barrel distortion from wide-angle lenses.\n"
        "- Image textures: realistic VHS softness, analog tape hiss artifacts, interlaced lines, mild organic film grain, natural low-light noise instead of clean digital gradients.\n"
        "- Physical world details: scuffed linoleum floors, faint dust motes drifting in light beams, minor water stains, matte material finishes instead of perfect CGI gloss reflections.\n\n"
        "--- 🔥 VIDEO GENERATION MANDATE ---\n"
        "The generated prompt is NOT a static image description. It must be written strictly as a TEXT-TO-VIDEO generation prompt designed for an 8-second video clip (optimized for Sora, Runway Gen-3, Kling).\n"
        "1. The 'video_prompt' MUST be written entirely in ENGLISH.\n"
        "2. It must explicitly dictate a seamless, continuous 8-second camera progression. Describe the precise motion.\n"
        "3. Incorporate the pacing of time. Describe how atmospheric details transpire smoothly over the 8-second duration.\n"
        "4. Avoid ambient text interruptions; ensure all aesthetic markers (VHS softness, film grain) are integrated into the prompt text naturally.\n\n"
        "--- OUTPUT FORMAT ---\n"
        "Generate EXACTLY 5 distinct video concepts. Output must be strictly valid JSON matching this schema:\n"
        "{\"scenes\": [{\"title\": \"...\", \"description\": \"(Korean narrative summary)\", \"video_prompt\": \"(8-second English text-to-video prompt)\"}]}"
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
                    print(f"✅ [성공] {model_id} 모델이 프롬프트를 성공적으로 생성했습니다.")
                    return json.loads(raw_content)['scenes']
            print(f"⚠️ [우회] {model_id} 에러 발생 (코드 {response.status_code}). 차선책으로 이동.")
        except Exception as e:
            print(f"⚠️ {model_id} 예외 발생: {e}. 차선책으로 이동.")
        time.sleep(1)
    return []

def generate_image(prompt, index):
    """3. 429 우회 재시도 및 백업 모델 아키텍처가 탑재된 이미지 렌더링 함수"""
    # FLUX가 막힐 경우를 대비해 허깅페이스 내 최고 품질의 실사 백업 라인업 구축
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
                    # 429 발견 시 지수 백오프 적용 (7초 -> 14초 -> 21초 대기)
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
    """4. 텔레그램으로 대표 컷과 영상 연출 설명 전송"""
    caption = f"🌌 *{title}*\n\n{desc}"
    
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
                # 연속 호출로 인한 429 방지를 위해 메인 루프 대기 시간 유연화 (기존 3초 -> 6초)
                time.sleep(6)
            print("🎉 모든 에이전트 임무 완료!")
    except Exception as e:
        print(f"💥 스크립트 실행 중 치명적 에러 발생: {e}")

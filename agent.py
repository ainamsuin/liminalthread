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
    """2. 그래픽 티를 빼고 철저한 실사 카메라 스펙으로 무장한 8초 비디오 프롬프트를 생성합니다."""
    free_models = get_active_free_models()
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "Liminal Agent"
    }
    
    # 💡 극대화된 실사 표현을 위한 안티 CGI 프롬프트 엔지니어링 지시문 설계
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
        "--- TASK INSTRUCTIONS ---\n"
        "1. Generate EXACTLY 5 distinct video concepts. Ensure location variety across scenes.\n"
        "2. The 'video_prompt' MUST be written entirely in ENGLISH as an 8-second text-to-video prompt. Explicitly map out the 8-second continuous timeline and include the raw analog camera specs mentioned above.\n"
        "3. Provide a beautifully haunting narrative summary in Korean for the 'description' field.\n"
        "4. Output must be strictly valid JSON matching this schema:\n"
        "{\"scenes\": [{\"title\": \"...\", \"description\": \"(Korean)\", \"video_prompt\": \"(8-second English raw camera prompt)\"}]}"
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
                    print(f"✅ [성공] 최상위 모델 {model_id}이(가) 실사화 필터링이 완료된 프롬프트를 빌드했습니다.")
                    return json.loads(raw_content)['scenes']
            
            print(f"⚠️ [우회] {model_id} 에러 발생 (코드 {response.status_code}). 다음 차선책 모델로 이동.")
            
        except Exception as e:
            print(f"⚠️ {model_id} 예외 발생: {e}. 다음 차선책 모델로 이동.")
        
        time.sleep(1)
        
    return []

def generate_image(prompt, index):
    """3. 비디오 프롬프트를 기반으로 대표 스틸 이미지 렌더링"""
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
            print(f"⚠️ 프리뷰 이미지 생성 실패 (코드 {response.status_code}): {response.text}")
    except Exception as e:
        print(f"⚠️ 이미지 API 호출 중 예외 발생: {e}")
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
        res = requests.post(url, data={"chat_id": TG_CHAT_ID, "text": f"{caption}\n(프리뷰 생성 실패)", "parse_mode": "Markdown"})
    
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
                time.sleep(3)
            print("🎉 모든 에이전트 임무 완료!")
    except Exception as e:
        print(f"💥 스크립트 실행 중 치명적 에러 발생: {e}")

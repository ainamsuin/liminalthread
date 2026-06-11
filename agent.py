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
    """2. 공간의 절대적 정적 유지와 카메라 움직임을 극도로 제한한 10단 리미널 시퀀스를 생성합니다."""
    free_models = get_active_free_models()
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "Pure Static Liminal Director"
    }
    
    # 💡 공간 불변 규칙(Static Space Rule) 및 카메라 움직임 극제한(Restrained Camera) 지시문 주입
    system_msg = (
        "You are an expert cinematic Liminal Space director specializing in purely static, frozen, and architecturally eerie environmental short films.\n"
        "Each cut must be 7 to 8 seconds long. The entire 10-cut sequence must feel like a quiet, slow first-person observation of a single location, completely devoid of human life.\n\n"
        "--- 🚨 THE GOLDEN LAW: THE STRANGENESS IS THE SPACE ITSELF 🚨 ---\n"
        "1. NO SPATIAL MORPHING OR SHIFTING: The space, walls, objects, and geometry must NEVER change, morph, dissolve, or distort during the shot. The environment is entirely permanent and fixed. The eerie wrongness comes solely from its original, permanent, frozen architectural state (e.g., a real staircase that simply terminates at a solid ceiling).\n"
        "2. EXTREMELY RESTRAINED CAMERA: Absolutely NO active tracking shots, NO dynamic dolly shots, and NO dramatic camera travel. The camera must capture the absolute stillness of the space. Only three framing methods are allowed:\n"
        "   - Method A [Completely Static]: A locked-off, entirely unmoving tripod or surveillance camera view where nothing moves except perhaps a soft light reflection.\n"
        "   - Method B [Slow Stationary Looking Around]: A stationary camera performing an agonizingly slow, subtle pan or tilt from a single fixed point, simply observing the architecture.\n"
        "   - Method C [Barely Noticeable Creep]: An incredibly slow, minute forward drift that is almost imperceptible, emphasizing the frozen weight of the corridor.\n\n"
        "--- 🌏 CULTURAL CONTEXT SWITCHING (Select EXACTLY ONE per generation) ---\n"
        "- JAPAN: Empty, late-night suburban train stations, 24/7 convenience store interiors, narrow residential alleyways under sodium vapor lights.\n"
        "- USA: Dead suburban shopping malls from the 90s, endless empty hotel corridors with repetitive carpets, massive corporate office parks after hours.\n"
        "- RUSSIA/POST-SOVIET: Colossal Brutalist concrete monolith architecture, repeating infinite apartment complex hallways, sterile empty clinic waiting areas.\n"
        "- UK: Abandoned 70s brutalist multi-story parking garages, empty laundrettes under clinical fluorescent lights.\n"
        "- SOUTH KOREA: Empty 24/7 PC Bangs (internet cafes) after hours, massive infinite apartment complex stairwells, deserted academy (hagwon) corridors at night.\n\n"
        "--- 🚨 NO PEOPLE & IMMERSIVE FOCUSING SOUND 🚨 ---\n"
        "- Absolutely no human figures, silhouettes, or shadows. Completely vacant spaces.\n"
        "- Focus on immersive, non-threatening background sounds that enhance concentration: 'soft air-conditioning hiss', 'calm ambient room tone', 'the profound echo of quietness', 'a gentle, steady ventilation whir'. No harsh or startling noises.\n\n"
        "--- 🎥 CINEMATOGRAPHIC TERMINOLOGY MANDATE ---\n"
        "The 'video_prompt' and 'description' must explicitly define the static physics. Use terms like: 'locked-off static tripod framing', 'agonizingly slow 8-second stationary pan', 'imperceptible micro-creep forward', 'wide-angle flat perspective emphasizing the unmoving, frozen geometry', 'raw consumer camcorder tape texture (VHS softness)'.\n\n"
        "--- OUTPUT FORMAT ---\n"
        "Output must be strictly valid JSON matching this schema (all text fields must be entirely in ENGLISH):\n"
        "{\n"
        "  \"series_title\": \"[A compelling, viral-ready English video title reflecting the frozen environment]\",\n"
        "  \"chosen_culture\": \"[The ONE culture selected for this generation, e.g., 'SOUTH KOREA']\",\n"
        "  \"chosen_location\": \"[The specific location within that culture, e.g., 'hagwon corridor']\",\n"
        "  \"scenes\": [\n"
        "    {\n"
        "      \"title\": \"Cut [1-10]: [Blueprint Stage Name] - [Grounded Location Detail]\",\n"
        "      \"description\": \"[Detailed English summary of this cut's geography, explaining how the stationary camera or micro-creep framing connects logically to the previous point in space]\",\n"
        "      \"video_prompt\": \"[8-second English text-to-video prompt forcing a completely static or slow-pan frame, unmoving/non-morphing architectural anomalies, realistic material textures, focusing sound, and vintage analog camera grain]\"\n"
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
                    print(f"✅ [성공] {model_id} 모델이 정적 보존 법칙이 적용된 리미널 시퀀스를 완성했습니다.")
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
    """4. 텔레그램으로 완벽하게 고정된 정적 10개 컷과 훅 타이틀 전송"""
    caption = f"🏢 *Static Liminal 10-Cut ({chosen_culture} - {chosen_location}):* {series_title}\n\n🎬 *{title}*\n*Description:* {desc}"
    
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
        series_title = res_data.get('series_title', 'The Static Reality')
        chosen_culture = res_data.get('chosen_culture', 'Unknown')
        chosen_location = res_data.get('chosen_location', 'Unknown')
        
        if not scenes:
            print("❌ 모든 무료 모델 리스트를 순회했으나 데이터 확보에 실패했습니다.")
        else:
            print(f"🚀 총 {len(scenes)}개의 정적 리미널 시퀀스 생성을 시작합니다.")
            for i, scene in enumerate(scenes):
                img_file = generate_image(scene['video_prompt'], i)
                send_to_telegram(chosen_culture, chosen_location, series_title, scene['title'], scene['description'], img_file)
                time.sleep(6)
            print("🎉 10컷 마스터 디렉터 에이전트 미션 완수!")
    except Exception as e:
        print(f"💥 스크립트 실행 중 치명적 에러 발생: {e}")

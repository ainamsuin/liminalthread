import os
import requests
import json
import time

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
HF_KEY = os.getenv("HF_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def clean_url(url_str):
    """혹시 모를 마크다운 기호나 대괄호 잔재를 강제로 제거하는 유틸리티"""
    return url_str.strip().lstrip('[').split(']')[0].strip()

def get_active_free_models():
    """1. OpenRouter에서 무료 모델을 가져와 최신/고성능 순으로 정렬합니다."""
    raw_url = "https://openrouter.ai/api/v1/models"
    url = clean_url(raw_url)
    
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
    """2. 드림코어 프롬프트를 생성하고, 반환된 텍스트를 안전하게 디코딩합니다."""
    free_models = get_active_free_models()
    
    raw_url = "https://openrouter.ai/api/v1/chat/completions"
    url = clean_url(raw_url)
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "Robust Dreamcore Director"
    }
    
    system_msg = (
        "You are an expert cinematic director specializing in web-authenticated 'Dreamcore' and 'Liminal Space' aesthetics.\n"
        "Your task is to direct a single, visually continuous 5-cut narrative sequence. Each cut is exactly 7 to 8 seconds long.\n\n"
        "--- 📐 UNIFIED FRAMING MANDATE: DISTANT EXTREME WIDE SHOTS ONLY ---\n"
        "- Every single cut (Cuts 1 to 5) must strictly utilize an Extreme Wide Shot (EWS) or a Distant Establishing Shot.\n"
        "- The framing must remain perfectly still, frozen, and locked-off on a static tripod for the entire duration of every shot. No camera movement.\n\n"
        "--- 🚨 SINGLE CONCEPTS & WHIMSICAL DREAMCORE STYLE ---\n"
        "- Unified Location Concept: Select EXACTLY ONE massive child-centric nostalgic location for all 5 cuts (e.g., an endless pastel indoor play center, a colossal whimsical daycare void, or an infinite soft-tiled fantasy pool). Do not change the overall location theme between cuts.\n"
        "- Atmosphere: The space must feel completely vacant and empty, yet intensely nostalgic and whimsical. It should evoke childhood comfort and innocence rather than fear. It must feel strange and dreamlike, but absolutely peaceful, warm, and non-threatening (no creepy or horrific elements).\n"
        "- Visual Specifications: Use vast, sprawling macro layouts, soft pastel tones, warm yellow fluorescent grids, hazy light bloom (halation), and low-fi vintage flash photography artifacts with flat static shadows.\n"
        "- Spatial Permanence: The space itself must remain structurally fixed and solid during the shot.\n\n"
        "--- 📜 CONCISE DESCRIPTION RULE (300 Characters Target) ---\n"
        "- The relationship between cuts must be causally linked, moving deeper into different angles of the same massive nostalgic complex.\n"
        "- The 'description' field for EACH cut MUST be concise, aiming for approximately 300 characters in English. Briefly but vividly outline the vast layout, the dreamlike pastel environment, the soft lighting bloom, and the peaceful, silent room tone.\n\n"
        "--- OUTPUT FORMAT ---\n"
        "Output must be strictly valid JSON matching this schema (all text fields must be entirely in ENGLISH):\n"
        "{\n"
        "  \"series_title\": \"[A poetic, whimsical English video title]\",\n"
        "  \"unified_space_concept\": \"[The single chosen location type, e.g., 'Infinite Pastel Indoor Playground']\",\n"
        "  \"scenes\": [\n"
        "    {\n"
        "      \"title\": \"Cut [1-5]: [Blueprint Stage Name]\",\n"
        "      \"description\": \"[A CONCISE ENGLISH NARRATIVE AIMING FOR ~300 CHARACTERS. Describe the vast vacant child-centric layout, peaceful dreamlike atmosphere, and soft halation.]\",\n"
        "      \"video_prompt\": \"[8-second English text-to-video prompt forcing a distant, PERFECTLY LOCKED-OFF EXTREME WIDE TRIPOD SHOT, massive empty dreamcore child playground architecture, vintage flash artifacts, low-fi grain, pastel tones, warm yellow lighting halation, and peaceful silent room tone.]\"\n"
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
                    raw_content = res_json['choices'][0]['message']['content'].strip()
                    
                    if raw_content.startswith("```"):
                        raw_content = raw_content.replace("```json", "").replace("```", "").strip()
                    
                    parsed_dict = json.loads(raw_content)
                    if isinstance(parsed_dict, str):
                        parsed_dict = json.loads(parsed_dict)
                        
                    if isinstance(parsed_dict, dict) and 'scenes' in parsed_dict:
                        print(f"✅ [성공] {model_id} 모델 데이터를 안정적으로 로드했습니다.")
                        return parsed_dict
            print(f"⚠️ [우회] {model_id} 에러 발생 (코드 {response.status_code}). 차선책으로 이동.")
        except Exception as e:
            print(f"⚠️ {model_id} 예외 파싱 오류 발생: {e}. 차선책으로 이동.")
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
        raw_model_url = f"[https://router.huggingface.co/hf-inference/models/](https://router.huggingface.co/hf-inference/models/){model_path}"
        model_url = clean_url(raw_model_url)
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                print(f"🎨 [이미지 생성 시도] 모델: {model_path} ({attempt + 1}/{max_retries})")
                response = requests.post(model_url, headers=headers, json={"inputs": prompt}, timeout=90)
                
                if response.status_code == 200:
                    file_path = f"liminal_{index}.png"
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    print(f"✅ [렌더링 성공] {model_path}를 통해 {index+1}번째 초광각 프리뷰를 확보했습니다.")
                    return file_path
                
                elif response.status_code == 429:
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

def send_to_telegram(unified_space_concept, series_title, title, desc, img_path):
    """4. 텔레그램으로 정제된 포근한 드림코어 5개 컷 발송"""
    caption = f"🧸 *Unified Dreamcore Void ({unified_space_concept}):* {series_title}\n\n🎬 *{title}*\n\n📜 *Detailed Narrative:* \n{desc}"
    
    if img_path and os.path.exists(img_path):
        url = clean_url(f"[https://api.telegram.org/bot](https://api.telegram.org/bot){TG_TOKEN}/sendPhoto")
        with open(img_path, "rb") as photo:
            res = requests.post(url, data={"chat_id": TG_CHAT_ID, "caption": caption, "parse_mode": "Markdown"}, files={"photo": photo})
    else:
        url = clean_url(f"[https://api.telegram.org/bot](https://api.telegram.org/bot){TG_TOKEN}/sendMessage")
        res = requests.post(url, data={"chat_id": TG_CHAT_ID, "text": f"{caption}\n\n⚠️ (Image Generation Timeout/429 - Preview FAILED)", "parse_mode": "Markdown"})
    
    if res.status_code != 200:
        print(f"❌ 텔레그램 전송 실패 (코드 {res.status_code}): {res.text}")

if __name__ == "__main__":
    try:
        res_data = get_liminal_prompts()
        
        if not isinstance(res_data, dict):
            print("⚠️ 최상위 데이터가 딕셔너리 구조가 아닙니다. 기본값으로 강제 리셋합니다.")
            res_data = {}
            
        series_title = res_data.get('series_title', 'A Peaceful Echo')
        unified_space_concept = res_data.get('unified_space_concept', 'Whimsical Void')
        scenes = res_data.get('scenes', [])
        
        if isinstance(scenes, str):
            try:
                scenes = json.loads(scenes)
            except:
                scenes = []
                
        if not isinstance(scenes, list) or not scenes:
            print("❌ 예외 처리 필터링 결과, 유효한 5컷의 리스트 시퀀스를 파싱해내지 못했습니다. 스크립트를 재실행해 주세요.")
        else:
            print(f"🚀 총 {len(scenes)}개의 '단일 컨셉 초광각 고정형 드림코어' 시퀀스 루프를 안전하게 개시합니다.")
            for i, scene in enumerate(scenes):
                if not isinstance(scene, dict):
                    print(f"⚠️ {i+1}번째 컷 데이터가 문자열 등 부적절한 타입으로 파싱되어 스킵합니다.")
                    continue
                
                title = scene.get('title', f"Cut {i+1}: Whimsical Zone")
                description = scene.get('description', "No descriptions generated.")
                video_prompt = scene.get('video_prompt', "A static empty pastel playground, dreamcore.")
                
                img_file = generate_image(video_prompt, i)
                send_to_telegram(unified_space_concept, series_title, title, description, img_file)
                time.sleep(12)
            print("🎉 5컷 마스터 디렉터 에이전트 미션 완수!")
    except Exception as e:
        print(f"💥 구조적 우회 처리 도중 예기치 못한 에러 발생: {e}")

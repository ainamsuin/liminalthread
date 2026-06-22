import os
import requests
import json
import time

# [보안 필터] 환경 변수 양끝의 공백 및 불필요한 따옴표 완벽 세정
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "").strip("'\" ")
HF_KEY = os.getenv("HF_API_KEY", "").strip("'\" ")
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip("'\" ")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip("'\" ")

# 사용자가 실수로 'bot12345...' 형태로 'bot' 접두사를 중복 입력했을 때만 작동하는 안전 장치
if TG_TOKEN.lower().startswith("bot") and any(c.isdigit() for c in TG_TOKEN[3:8]):
    TG_TOKEN = TG_TOKEN[3:]

def clean_url(url_str):
    """마크다운 링크 오염이나 대괄호 잔재 방어 유틸리티"""
    return url_str.strip().lstrip('[').split(']')[0].strip()

def get_active_free_models():
    """1. OpenRouter에서 무료 모델을 가져와 최신/고성능 순으로 정렬합니다."""
    url = clean_url("https://openrouter.ai/api/v1/models")
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
    url = clean_url("https://openrouter.ai/api/v1/chat/completions")
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "Robust Dreamcore Director"
    }
    
    system_msg = (
        "You are an expert cinematic director specializing in 'Dreamcore' and 'Liminal Space' aesthetics.\n"
        "Your task is to direct a single, visually continuous 5-cut narrative sequence. Each cut is exactly 7 to 8 seconds long.\n\n"
        "--- OUTPUT FORMAT ---\n"
        "Output must be strictly valid JSON matching this schema:\n"
        "{\n"
        "  \"series_title\": \"[A poetic, whimsical English video title]\",\n"
        "  \"unified_space_concept\": \"[The single chosen location type, e.g., 'Infinite Pastel Indoor Playground']\",\n"
        "  \"scenes\": [\n"
        "    {\n"
        "      \"title\": \"Cut [1-5]: [Blueprint Stage Name]\",\n"
        "      \"description\": \"[CONCISE ENGLISH NARRATIVE AIMING FOR ~300 CHARACTERS]\",\n"
        "      \"video_prompt\": \"[8-second English text-to-video prompt forcing a distant, PERFECTLY LOCKED-OFF EXTREME WIDE TRIPOD SHOT, massive empty dreamcore architecture, vintage flash artifacts, low-fi grain, pastel tones, warm yellow lighting, and peaceful silent room tone.]\"\n"
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
    """3. 표준 공용 서버리스 인프라 주소로 복구된 이미지 렌더링 함수"""
    if not prompt or not isinstance(prompt, str):
        prompt = "A distant perfectly locked-off extreme wide tripod shot of a massive empty dreamcore child playground, pastel tones, vintage photography grain, peaceful silent room tone."
        
    target_models = [
        "black-forest-labs/FLUX.1-schnell",
        "stabilityai/stable-diffusion-xl-base-1.0",
        "SG161222/RealVisXL_V4.0"
    ]
    headers = {
        "Authorization": f"Bearer {HF_KEY}",
        "Content-Type": "application/json"
    }
    
    for model_path in target_models:
        # 💡 [해결 1] 허깅페이스 공용 무료 서버리스 인프라 표준 주소(api-inference)로 전면 복구
        raw_model_url = f"[https://api-inference.huggingface.co/models/](https://api-inference.huggingface.co/models/){model_path}"
        model_url = clean_url(raw_model_url)
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                print(f"🎨 [이미지 생성 시도] 모델: {model_path} ({attempt + 1}/{max_retries})")
                response = requests.post(model_url, headers=headers, json={"inputs": prompt.strip()}, timeout=90)
                
                if response.status_code == 200:
                    file_path = f"liminal_{index}.png"
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    print(f"✅ [렌더링 성공] {model_path}를 통해 {index+1}번째 초광각 프리뷰를 확보했습니다.")
                    return file_path
                
                elif response.status_code == 429:
                    wait_time = 15 * (attempt + 1)
                    print(f"⚠️ [Rate Limit 429] 허깅페이스 제한 감지. {wait_time}초 후 재시도...")
                    time.sleep(wait_time)
                else:
                    print(f"⚠️ 이미지 생성 에러 (코드 {response.status_code}): {response.text[:150]}")
                    break
                    
            except Exception as e:
                print(f"⚠️ 이미지 API 통신 예외 발생: {e}")
                time.sleep(3)
        
        print(f"🔄 {model_path} 제한 초과로 다음 백업 모델로 전형합니다.")
    
    return None

def send_to_telegram(unified_space_concept, series_title, title, desc, img_path):
    """4. 텔레그램 전송 레이어"""
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
    # 💡 [해결 2] 환경 변수 주입 유효성 진단 디버그 로그 확보 (404 원인 추적용)
    print("⚙️ [CI/CD 환경 변수 주입 성상 체크]")
    print(f"  - OpenRouter Key: {'정상 로드' if OPENROUTER_KEY else '❌ 누락'} (총 {len(OPENROUTER_KEY)}자)")
    print(f"  - HuggingFace Key: {'정상 로드' if HF_KEY else '❌ 누락'} (총 {len(HF_KEY)}자)")
    
    # 텔레그램 토큰 마스킹 시각화
    tg_visible = f"{TG_TOKEN[:4]}***{TG_TOKEN[-4:]}" if len(TG_TOKEN) > 8 else "유효하지 않음"
    print(f"  - Telegram Bot Token: {tg_visible} (총 {len(TG_TOKEN)}자)")
    print(f"  - Telegram Chat ID: {TG_CHAT_ID}")
    print("-" * 50)

    try:
        res_data = get_liminal_prompts()
        
        if not isinstance(res_data, dict):
            res_data = {}
            
        series_title = res_data.get('series_title', 'A Peaceful Echo')
        unified_space_concept = res_data.get('unified_space_concept', 'Whimsical Void')
        scenes = res_data.get('scenes', [])
        
        if isinstance(scenes, str):
            try: scenes = json.loads(scenes)
            except: scenes = []
                
        if not isinstance(scenes, list) or not scenes:
            print("❌ 예외 처리 필터링 결과, 유효한 5컷의 리스트 시퀀스를 파싱해내지 못했습니다. 스크립트를 재실행해 주세요.")
        else:
            print(f"🚀 총 {len(scenes)}개의 '단일 컨셉 초광각 고정형 드림코어' 시퀀스 루프를 안전하게 개시합니다.")
            for i, scene in enumerate(scenes):
                if not isinstance(scene, dict):
                    continue
                
                title = scene.get('title', f"Cut {i+1}: Whimsical Zone")
                description = scene.get('description', "No descriptions generated.")
                video_prompt = scene.get('video_prompt') or scene.get('prompt') or scene.get('image_prompt') or "A static empty pastel playground, dreamcore."
                
                img_file = generate_image(video_prompt, i)
                send_to_telegram(unified_space_concept, series_title, title, description, img_file)
                time.sleep(12)
            print("🎉 5컷 마스터 디렉터 에이전트 미션 완수!")
    except Exception as e:
        print(f"💥 구조적 우회 처리 도중 예기치 못한 에러 발생: {e}")

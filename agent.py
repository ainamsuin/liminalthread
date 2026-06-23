import os
import requests
import json
import time

def sanitize_env(val):
    """
    [Core Sanitizer] 
    단순 공백 제거를 넘어 눈에 보이지 않는 \r, \n, \t 등 모든 제어 문자와 
    감싸진 따옴표를 완전히 박멸하여 URL 파괴 현상을 원천 차단합니다.
    """
    if not val:
        return ""
    # 1단계: 앞뒤 모든 종류의 화이트스페이스(\r, \n 포함) 제거
    val = val.strip()
    # 2단계: 양끝의 불필요한 단일/쌍따옴표 제거
    val = val.strip("'\"")
    # 3단계: 잔여 공백 최종 청소
    return val.strip()

# 환경 변수 초정밀 정제 주입
OPENROUTER_KEY = sanitize_env(os.getenv("OPENROUTER_API_KEY", ""))
HF_KEY = sanitize_env(os.getenv("HF_API_KEY", ""))
TG_TOKEN = sanitize_env(os.getenv("TELEGRAM_BOT_TOKEN", ""))
TG_CHAT_ID = sanitize_env(os.getenv("TELEGRAM_CHAT_ID", ""))

if TG_TOKEN.lower().startswith("bot") and any(c.isdigit() for c in TG_TOKEN[3:8]):
    TG_TOKEN = TG_TOKEN[3:]

def clean_url(url_str):
    return url_str.strip().lstrip('[').split(']')[0].strip()

def get_active_free_models():
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
                if 'qwen-2.5' in model_id or 'qwen-3' in model_id: priority_score = 50
                elif 'llama-3.3' in model_id or 'llama-3.1' in model_id: priority_score = 40
                elif 'gemma-2' in model_id: priority_score = 30
                return (priority_score, context_length)
            
            free_models_data.sort(key=evaluate_model_performance, reverse=True)
            sorted_ids = [m['id'] for m in free_models_data]
            print(f"🎯 [정렬 완료] 최신/고성능 탑재 1순위 모델: {sorted_ids[0] if sorted_ids else '없음'}")
            return sorted_ids
    except Exception as e:
        print(f"⚠️ 무료 모델 목록 조회 중 오류 발생: {e}")
    return ["openrouter/free"]

def get_liminal_prompts():
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

        "--- MOOD & TONE ---\n"
        "The overall mood MUST be WARM, PEACEFUL, and NON-THREATENING.\n"
        "Evoke childhood comfort and innocence — like a quiet, sunlit space that feels safe and gently nostalgic.\n"
        "DO NOT use horror, dread, unsettling shadows, or any uncanny valley elements. "
        "The space is simply empty and still, not scary.\n\n"

        "--- SPATIAL UNITY RULE ---\n"
        "CRITICAL: First, decide on ONE single physical location for 'unified_space_concept' (e.g. 'Infinite Pastel Indoor Playground').\n"
        "ALL 5 cuts MUST remain inside that exact same location. "
        "Each cut shows a DIFFERENT ZONE or ANGLE within that one space — do NOT change to a new location between cuts.\n\n"

        "--- OUTPUT FORMAT ---\n"
        "Output must be strictly valid JSON matching this schema:\n"
        "{\n"
        "  \"series_title\": \"[Poetic Video Title]\",\n"
        "  \"unified_space_concept\": \"[Single Location Type, e.g. Infinite Pastel Indoor Playground]\",\n"
        "  \"scenes\": [\n"
        "    {\n"
        "      \"title\": \"Cut [1-5]: [Zone Name]\",\n"
        "      \"description\": \"[Max 300 characters. Concise scene narrative only. Warm and peaceful tone.]\",\n"
        "      \"video_prompt\": \"[8-second English tripod shot prompt, pastel tones, low-fi grain, warm soft light]\"\n"
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
    """5. DNS 장애 극복형 이중화 호스트 라우팅 메커니즘을 반영한 이미지 생성 레이어"""
    if not prompt or not isinstance(prompt, str):
        prompt = "A distant perfectly locked-off extreme wide tripod shot of a massive empty dreamcore child playground."
        
    target_models = [
        "black-forest-labs/FLUX.1-schnell",
        "stabilityai/stable-diffusion-xl-base-1.0",
        "SG161222/RealVisXL_V4.0"
    ]
    
    # 💡 [해결 1] 러너 환경별 DNS NameResolutionError 원천 차단을 위한 대체 도메인 풀 구성
    hf_dns_hosts = [
        "https://api-inference.huggingface.co",
        "https://api.huggingface.co"
    ]
    
    headers = {
        "Authorization": f"Bearer {HF_KEY}",
        "Content-Type": "application/json"
    }
    
    for model_path in target_models:
        for host_base in hf_dns_hosts:
            raw_model_url = f"{host_base}/models/{model_path}"
            model_url = clean_url(raw_model_url)
            
            try:
                print(f"🎨 [이미지 생성 시도] 엔드포인트: {host_base} | 모델: {model_path}")
                response = requests.post(model_url, headers=headers, json={"inputs": prompt.strip()}, timeout=60)
                
                if response.status_code == 200:
                    file_path = f"liminal_{index}.png"
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    print(f"✅ [렌더링 성공] {model_path} 프리뷰 확보 완료.")
                    return file_path
                elif response.status_code == 429:
                    print("⚠️ [Rate Limit 429] 허깅페이스 제한 감지. 백업 엔드포인트/모델로 전환합니다.")
                    continue
                else:
                    print(f"⚠️ 이미지 생성 응답 거절 (코드 {response.status_code})")
                    
            except requests.exceptions.ConnectionError as ce:
                # DNS 에러가 발생하면 무너지지 않고 다음 주소(api.huggingface.co)로 패스
                print(f"⚠️ [{host_base}] DNS 혹은 네트워크 해석 실패. 즉시 백업 도메인으로 셰이핑합니다.")
                continue
            except Exception as e:
                print(f"⚠️ 이미지 API 통신 예외 발생: {e}")
                continue
        
        print(f"🔄 {model_path} 제한 또는 DNS 이슈로 다음 백업 모델로 전형합니다.")
    return None

def send_to_telegram(unified_space_concept, series_title, title, desc, img_path):
    caption = f"🧸 *Unified Dreamcore Void ({unified_space_concept}):* {series_title}\n\n🎬 *{title}*\n\n📜 *Detailed Narrative:* \n{desc}"
    
    # 💡 [해결 2] 완전 정제된 토큰을 사용하여 결함 없는 깔끔한 URL 라우팅 패스 확보
    if img_path and os.path.exists(img_path):
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
        with open(img_path, "rb") as photo:
            res = requests.post(url, data={"chat_id": TG_CHAT_ID, "caption": caption, "parse_mode": "Markdown"}, files={"photo": photo})
    else:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        res = requests.post(url, data={"chat_id": TG_CHAT_ID, "text": f"{caption}\n\n⚠️ (Image Preview FAILED)", "parse_mode": "Markdown"})
    
    if res.status_code != 200:
        print(f"❌ 텔레그램 전송 실패 (코드 {res.status_code}): {res.text}")

if __name__ == "__main__":
    print("⚙️ [CI/CD 환경 변수 주입 성상 체크]")
    print(f"  - OpenRouter Key: {'정상 로드' if OPENROUTER_KEY else '❌ 누락'} (총 {len(OPENROUTER_KEY)}자)")
    print(f"  - HuggingFace Key: {'정상 로드' if HF_KEY else '❌ 누락'} (총 {len(HF_KEY)}자)")
    tg_visible = f"{TG_TOKEN[:4]}***{TG_TOKEN[-4:]}" if len(TG_TOKEN) > 8 else "유효하지 않음"
    print(f"  - Telegram Bot Token: {tg_visible} (총 {len(TG_TOKEN)}자)")
    print(f"  - Telegram Chat ID: {TG_CHAT_ID}")
    print("-" * 50)

    try:
        res_data = get_liminal_prompts()
        series_title = res_data.get('series_title', 'A Peaceful Echo')
        unified_space_concept = res_data.get('unified_space_concept', 'Whimsical Void')
        scenes = res_data.get('scenes', [])
        
        if isinstance(scenes, str):
            try: scenes = json.loads(scenes)
            except: scenes = []
                
        if not isinstance(scenes, list) or not scenes:
            print("❌ 유효한 5컷의 리스트 시퀀스를 파싱해내지 못했습니다.")
        else:
            print(f"🚀 총 {len(scenes)}개의 '단일 컨셉 초광각 고정형 드림코어' 시퀀스 루프를 안전하게 개시합니다.")
            for i, scene in enumerate(scenes):
                if not isinstance(scene, dict): continue
                title = scene.get('title', f"Cut {i+1}: Whimsical Zone")
                description = scene.get('description', "No descriptions.")
                video_prompt = scene.get('video_prompt') or scene.get('prompt') or "A static empty pastel playground, dreamcore."
                
                img_file = generate_image(video_prompt, i)
                send_to_telegram(unified_space_concept, series_title, title, description, img_file)
                time.sleep(10)
            print("🎉 5컷 마스터 디렉터 에이전트 미션 완수!")
    except Exception as e:
        print(f"💥 구조적 우회 처리 도중 예기치 못한 에러 발생: {e}")

import os
import requests
import json
import time

# ─── 환경 변수 정제 ──────────────────────────────────────────────────

def sanitize_env(val):
    """\r, \n, \t 등 제어 문자와 감싸진 따옴표 완전 제거."""
    if not val:
        return ""
    return val.strip().strip("'\"").strip()

OPENROUTER_KEY = sanitize_env(os.getenv("OPENROUTER_API_KEY", ""))
HF_KEY         = sanitize_env(os.getenv("HF_API_KEY", ""))
TG_TOKEN       = sanitize_env(os.getenv("TELEGRAM_BOT_TOKEN", ""))
TG_CHAT_ID     = sanitize_env(os.getenv("TELEGRAM_CHAT_ID", ""))

# "bot" 프리픽스 자동 제거 (일부 환경에서 토큰 앞에 붙어 오는 경우 대비)
if TG_TOKEN.lower().startswith("bot") and len(TG_TOKEN) > 3 and TG_TOKEN[3].isdigit():
    TG_TOKEN = TG_TOKEN[3:]


# ═══════════════════════════════════════════════════════════════════
# 🎨 미학 코덱스 — 장르별 정확한 정의
# ═══════════════════════════════════════════════════════════════════
AESTHETIC_CODEX = {
    "liminal_space": (
        "Liminal spaces are TRANSITIONAL, IN-BETWEEN environments caught between uses: "
        "empty school hallways after hours, hotel corridors at 3am, "
        "mall food courts before opening, parking garages at dawn. "
        "VISUAL TRAITS: PRISTINE and INTACT (NO decay, NO ruin, NO damage), "
        "fluorescent or incandescent lighting, clean surfaces with minor normal wear. "
        "Eeriness from ABSENCE OF PEOPLE, not deterioration. "
        "Color temp: cool 4500-6500K fluorescent whites or warm 2700K incandescent yellows."
    ),
    "dreamcore": (
        "Dreamcore: intact nostalgic spaces from 1990s-2000s childhood, subtly 'off'. "
        "Locations: Discovery Zone/Chuck E. Cheese indoor play areas, "
        "suburban mall arcades, hotel indoor pools, elementary school gymnasiums. "
        "VISUAL TRAITS: soft pastels (dusty pink #D4A5A5, mint #98D8C8, pale yellow #F5E6A3, baby blue), "
        "warm diffused non-directional light, NO harsh shadows, "
        "low-fi VHS grain. Everything CLEAN and INTACT — familiar yet subtly wrong."
    ),
    "backrooms": (
        "Backrooms canonical levels: "
        "Level 0: infinite yellow wallpaper (#D4C17A), fluorescent tubes, moist carpet. "
        "Level 5: infinite hotel lobby, maroon-gold carpet, yellow chandeliers. "
        "Level 37 (Poolrooms): infinite indoor pools, cyan/mint tiles, still water, "
        "diffused light of unknown origin. "
        "VISUAL TRAITS: INTACT spaces (not ruined), infinite repetition, "
        "found-footage lo-fi grain, ambient fluorescent hum or water echo."
    )
}

IMAGE_STYLE_SUFFIX = {
    "liminal_space": (
        "liminal space photography, photorealistic, 35mm film grain, "
        "intact clean empty transitional architecture, fluorescent lighting, hyperrealistic"
    ),
    "dreamcore": (
        "dreamcore aesthetic, soft desaturated pastel palette, 1990s 2000s nostalgia, "
        "warm diffused glow, VHS film grain, faded photograph, empty intact clean"
    ),
    "backrooms": (
        "backrooms found footage photography, hyperrealistic, lo-fi grain, "
        "intact infinite corridor, fluorescent sodium yellow lights, slightly overexposed"
    )
}

NEGATIVE_PROMPT = (
    "ruins, ruin, decay, rot, graffiti, crumbling walls, structural damage, derelict, "
    "rubble, broken windows, peeling paint, mold, rust, post-apocalyptic, horror, "
    "people, human figure, silhouette, shadow of person, "
    "text, signs, watermark, logo, motion blur, camera shake, "
    "illustration, painting, cartoon, anime, CGI render, harsh shadows"
)

# 현실→비현실 5단계 아크 정의 (FIX #NEW — 스토리 컨셉 핵심)
UNREALITY_STAGES = {
    1: {
        "name": "GROUNDED",
        "guide": "Completely real and intact. Just empty. Normal lighting, no anomalies whatsoever. "
                 "Eeriness comes purely from scale and absence of people."
    },
    2: {
        "name": "SUBTLE",
        "guide": "One small impossibility that could almost be explained away: "
                 "a corridor slightly too long to fit the building, "
                 "an escalator running upward with no floor above, "
                 "a reflection that is slightly out of sync."
    },
    3: {
        "name": "UNCANNY",
        "guide": "Clearly geometrically impossible but calm and beautiful: "
                 "a room visible through a window on an interior wall, "
                 "two identical corridors side by side that should not both exist, "
                 "a skylight showing another ceiling rather than the sky."
    },
    4: {
        "name": "SURREAL",
        "guide": "Multiple spatial impossibilities simultaneously visible: "
                 "the corridor curves gently upward and continues infinitely, "
                 "two doors on opposite walls open into the same room, "
                 "the floor tiles form a pattern impossible to install in physical reality."
    },
    5: {
        "name": "VOID",
        "guide": "Complete spatial dissolution — the space has become its own logic: "
                 "the room extends beyond any visible boundary, "
                 "light illuminates perfectly with no identifiable source, "
                 "the architecture implies a scale no building could physically contain."
    }
}


# ═══════════════════════════════════════════════════════════════════
# 유틸리티
# ═══════════════════════════════════════════════════════════════════

def get_active_free_models():
    """OpenRouter 무료 모델 목록 조회 및 성능순 정렬."""
    url = "https://openrouter.ai/api/v1/models"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            free = [m for m in r.json().get('data', []) if ':free' in m['id']]

            def score(m):
                mid, ctx = m['id'].lower(), m.get('context_length', 0)
                s = 0
                if 'qwen3' in mid or 'qwen-3' in mid:           s = 60
                elif 'qwen-2.5' in mid:                          s = 55
                elif 'deepseek' in mid:                          s = 50
                elif 'llama-3.3' in mid:                         s = 45
                elif 'llama-3.1' in mid or 'llama-3.2' in mid:  s = 40
                elif 'gemma-3' in mid:                           s = 35
                elif 'gemma-2' in mid:                           s = 30
                elif 'phi-4' in mid:                             s = 25
                return (s, ctx)

            free.sort(key=score, reverse=True)
            ids = [m['id'] for m in free]
            print(f"🎯 1순위 모델: {ids[0] if ids else 'None'} | 총 {len(ids)}개")
            return ids
    except Exception as e:
        print(f"⚠️ 모델 목록 오류: {e}")
    return ["meta-llama/llama-3.3-70b-instruct:free"]


def call_openrouter(messages, free_models, require_json=True, max_tokens=2500, max_models=5):
    """공통 OpenRouter 호출. 실패 시 상위 max_models 내 자동 폴백."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "Liminal Reality-Break Director"
    }
    for mid in free_models[:max_models]:
        body = {"model": mid, "messages": messages, "max_tokens": max_tokens}
        if require_json:
            body["response_format"] = {"type": "json_object"}
        try:
            print(f"  🔄 [{mid}]")
            r = requests.post(url, headers=headers, json=body, timeout=60)
            if r.status_code == 200 and 'choices' in r.json():
                content = r.json()['choices'][0]['message']['content'].strip()
                # markdown 코드블록 방어
                if content.startswith("```"):
                    content = content.replace("```json", "").replace("```", "").strip()
                print(f"  ✅ 응답 ({len(content)}자)")
                return content
            print(f"  ⚠️ {r.status_code} → 다음 모델")
        except Exception as e:
            print(f"  ⚠️ 예외: {e}")
        time.sleep(1)
    return None


# ═══════════════════════════════════════════════════════════════════
# Phase 1 — 스토리 컨셉 + 5단계 현실/비현실 아크 생성
# ═══════════════════════════════════════════════════════════════════

def generate_story_concept(free_models):
    """
    단일 내러티브 컨셉과 5단계 현실→비현실 공간 아크를 생성.
    각 단계는 공간 연결(visible_next_zone) + 비현실 요소(unreality_element)를 가짐.
    """
    stage_guide = "\n".join(
        f"  Stage {k} ({v['name']}): {v['guide']}"
        for k, v in UNREALITY_STAGES.items()
    )
    aesthetic_summary = "\n".join(
        f"  [{k}]: {v[:200]}..." for k, v in AESTHETIC_CODEX.items()
    )

    prompt = f"""You are a narrative director specializing in liminal space, dreamcore, and backrooms.

Design a single coherent story for a 5-shot static wide-shot video sequence.
The sequence follows ONE CONTINUOUS JOURNEY through a single vast location,
gradually drifting from ordinary reality into serene spatial impossibility.

REALITY-TO-UNREALITY ARC (assign one stage per cut, in order):
{stage_guide}

AESTHETIC OPTIONS (choose ONE):
{aesthetic_summary}

SPATIAL RULES:
- Each zone is physically adjacent to the next, with a clear sight line between them
- All spaces are INTACT and CLEAN — eeriness from emptiness and geometry, NOT from decay or ruin
- Camera: always extreme wide shot, perfectly static tripod, no movement

Create a 5-stage spatial journey. The unreality_element MUST be:
- A specific, concrete, architectural visual anomaly
- Calmly visible in the far background of a static wide shot
- Beautiful and eerie, not frightening

Output ONLY valid JSON:
{{
  "series_title": "[poetic English title suggesting a gradual drift into unreality]",
  "narrative_premise": "[2 sentences: who was here, what is this place, what is being slowly revealed as the viewer drifts deeper]",
  "chosen_culture": "[e.g., USA, SOUTH KOREA, JAPAN]",
  "chosen_location": "[e.g., infinite suburban dead mall, subterranean poolroom complex]",
  "aesthetic_type": "[liminal_space | dreamcore | backrooms]",
  "primary_color_palette": "[3-5 dominant colors with mood description]",
  "reality_arc": [
    {{
      "stage": 1,
      "stage_name": "GROUNDED",
      "zone_name": "[architectural zone name]",
      "zone_description": "[50-word: intact empty architecture, materials, specific lighting]",
      "unreality_element": "none",
      "visible_next_zone": "[which specific feature of stage 2 zone is visible from here — exact doorway, corridor end, or architectural detail]"
    }},
    {{
      "stage": 2,
      "stage_name": "SUBTLE",
      "zone_name": "[zone name]",
      "zone_description": "[50-word zone description]",
      "unreality_element": "[one specific small impossibility — concrete and architectural]",
      "visible_next_zone": "[which feature of stage 3 is visible from here]"
    }},
    {{
      "stage": 3,
      "stage_name": "UNCANNY",
      "zone_name": "[zone name]",
      "zone_description": "[50-word zone description]",
      "unreality_element": "[clearly impossible geometry, calm and beautiful]",
      "visible_next_zone": "[which feature of stage 4 is visible from here]"
    }},
    {{
      "stage": 4,
      "stage_name": "SURREAL",
      "zone_name": "[zone name]",
      "zone_description": "[50-word zone description]",
      "unreality_element": "[multiple spatial impossibilities visible simultaneously]",
      "visible_next_zone": "[which feature of stage 5 is visible from here]"
    }},
    {{
      "stage": 5,
      "stage_name": "VOID",
      "zone_name": "[zone name]",
      "zone_description": "[50-word zone description]",
      "unreality_element": "[total spatial dissolution — space extends beyond all possible physical boundaries]",
      "visible_next_zone": ""
    }}
  ]
}}"""

    print("\n📖 [Phase 1] 스토리 컨셉 + 현실/비현실 아크 생성 중...")
    content = call_openrouter(
        [{"role": "user", "content": prompt}],
        free_models, require_json=True, max_tokens=3000
    )
    if not content:
        print("❌ 스토리 컨셉 생성 실패")
        return None
    try:
        sc = json.loads(content)
        # aesthetic_type 정규화 (대소문자/오타 방어)
        raw = sc.get('aesthetic_type', '').lower()
        if 'dreamcore' in raw:   sc['aesthetic_type'] = 'dreamcore'
        elif 'backroom' in raw:  sc['aesthetic_type'] = 'backrooms'
        else:                    sc['aesthetic_type'] = 'liminal_space'

        arc_len = len(sc.get('reality_arc', []))
        print(f"✅ 컨셉: '{sc.get('series_title')}' | {sc['aesthetic_type']} | {arc_len}단계")
        print(f"   내러티브: {sc.get('narrative_premise', '')[:120]}")
        return sc
    except json.JSONDecodeError as e:
        print(f"❌ 스토리 컨셉 JSON 파싱 오류: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════
# Phase 2 — 순차 컷 생성 (이전 컷 description 체인 + 비현실 요소 강제)
# ═══════════════════════════════════════════════════════════════════

def generate_cut(stage_data, prev_description, story_concept, free_models):
    """
    스토리 컨셉 + 이전 컷 description을 참조하여 단일 컷 생성.
    unreality_element는 프레임 내 REQUIRED 시각 요소로 강제.
    """
    stage_num   = stage_data.get('stage', 1)
    stage_name  = stage_data.get('stage_name', 'GROUNDED')
    zone_name   = stage_data.get('zone_name', '')
    zone_desc   = stage_data.get('zone_description', '')
    unreality   = stage_data.get('unreality_element', 'none')
    visible_next = stage_data.get('visible_next_zone', '')

    aesthetic_type  = story_concept.get('aesthetic_type', 'liminal_space')
    aesthetic_guide = AESTHETIC_CODEX.get(aesthetic_type, '')
    color_palette   = story_concept.get('primary_color_palette', '')
    premise         = story_concept.get('narrative_premise', '')

    # 이전 컷 → 현재 컷 공간 앵커 주입 (연결성 핵심)
    if prev_description:
        link_text = (
            f"frame the exact space visible from Cut {stage_num - 1}: '{visible_next}'"
            if visible_next
            else f"conclude the drift, referencing the spatial scale of Cut {stage_num - 1}"
        )
        continuity_block = (
            f"SPATIAL CONTINUITY MANDATE:\n"
            f"Cut {stage_num - 1} showed: {prev_description[:360]}...\n\n"
            f"THIS cut MUST {link_text}.\n"
            f"The description MUST open by naming which specific element from "
            f"Cut {stage_num - 1} is now the primary foreground of this wide shot."
        )
        desc_opening = (
            f"MUST begin by explicitly stating which architectural element from "
            f"Cut {stage_num - 1} is now foregrounded in this static extreme wide shot."
        )
    else:
        continuity_block = "This is the OPENING SHOT. Establish the grand scale, color palette, and atmosphere."
        desc_opening = "Establish the architectural scale, dominant colors, and the mood of this vast empty space."

    # 비현실 요소 지시
    if unreality and unreality.lower() != 'none':
        unreality_block = (
            f"UNREALITY ELEMENT — REQUIRED VISUAL (Stage {stage_num}: {stage_name}):\n"
            f"{unreality}\n\n"
            f"This anomaly MUST be calmly and clearly visible somewhere in the extreme wide shot. "
            f"It should feel inevitable and serene — the space ACCEPTS this impossibility. "
            f"It is not frightening. It is simply how this place has always been."
        )
    else:
        unreality_block = (
            f"REALITY BASELINE (Stage 1 — GROUNDED):\n"
            f"This frame contains NO impossible elements. "
            f"It is completely real: intact, clean, functioning, just empty. "
            f"The unsettling quality comes entirely from scale and the absence of people."
        )

    prompt = f"""Generate Cut {stage_num} of 5 for a liminal space narrative video series.

NARRATIVE PREMISE: {premise}
AESTHETIC: {aesthetic_type.upper()} — {aesthetic_guide}
COLOR PALETTE: {color_palette}
ZONE: {zone_name} — {zone_desc}

{continuity_block}

{unreality_block}

ABSOLUTE RULES:
1. Camera: 100% STATIC TRIPOD. EXTREME WIDE SHOT. Zero movement — no dolly, pan, zoom, or tilt.
2. Space: INTACT, CLEAN, FUNCTIONING. Zero decay / ruin / damage / graffiti / broken fixtures.
   Empty because people have left or never arrived, not because it has deteriorated.
3. No people, silhouettes, or shadows of people anywhere.
4. No visible text, signs, or numbers.
5. Tone: eerie and beautiful, dreamlike, NOT horrifying or violent.

Output ONLY valid JSON:
{{
  "title": "Cut {stage_num} [{stage_name}]: {zone_name} — [Specific Visual Anchor]",
  "description": "[~900 character English narrative. {desc_opening} Then: exact intact materials visible from extreme distance, specific lighting (color temp + source positions), how the unreality element reads from the far static vantage, ambient sound that draws attention inward. Tone: calm, beautiful, quietly wrong.]",
  "video_prompt": "[Detailed text-to-image prompt: static extreme wide shot, {aesthetic_type} aesthetic, {color_palette}, intact clean empty architecture, {unreality if unreality.lower() != 'none' else 'purely realistic empty space'}, film grain, no people, no text, NOT ruined, NOT decayed, serene and eerie]"
}}"""

    content = call_openrouter(
        [{"role": "user", "content": prompt}],
        free_models, require_json=True, max_tokens=2000
    )
    if not content:
        return None
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"  ❌ Cut {stage_num} JSON 파싱 오류: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════
# 이미지 생성 — 강화 프롬프트 + negative prompt + 모델별 최적 파라미터
# ═══════════════════════════════════════════════════════════════════

def build_image_prompt(raw_prompt, aesthetic_type, color_palette):
    style = IMAGE_STYLE_SUFFIX.get(aesthetic_type, IMAGE_STYLE_SUFFIX['liminal_space'])
    return f"{raw_prompt}, {style}, dominant colors: {color_palette}"


def generate_image(prompt, index, aesthetic_type='liminal_space', color_palette=''):
    if not prompt or not isinstance(prompt, str):
        prompt = "A distant perfectly static extreme wide tripod shot of a massive empty liminal space interior."

    enhanced = build_image_prompt(prompt, aesthetic_type, color_palette)
    headers = {"Authorization": f"Bearer {HF_KEY}"}

    # NOTE: router.huggingface.co 사용 (api-inference.huggingface.co는 구형 엔드포인트)
    models_cfg = [
        {
            "path": "black-forest-labs/FLUX.1-schnell",
            # FLUX.1-schnell: CFG-free distilled model → guidance_scale=0.0 필수
            "payload": {
                "inputs": enhanced,
                "parameters": {"num_inference_steps": 4, "guidance_scale": 0.0}
            }
        },
        {
            "path": "stabilityai/stable-diffusion-xl-base-1.0",
            "payload": {
                "inputs": enhanced,
                "parameters": {
                    "negative_prompt": NEGATIVE_PROMPT,
                    "num_inference_steps": 40,
                    "guidance_scale": 7.5
                }
            }
        },
        {
            "path": "SG161222/RealVisXL_V4.0",
            "payload": {
                "inputs": enhanced,
                "parameters": {
                    "negative_prompt": NEGATIVE_PROMPT,
                    "num_inference_steps": 35,
                    "guidance_scale": 7.0
                }
            }
        }
    ]

    for cfg in models_cfg:
        # FIX: 깨끗한 URL 직접 조합 (markdown 포맷 문자열 금지)
        url = f"https://router.huggingface.co/hf-inference/models/{cfg['path']}"
        for attempt in range(3):
            try:
                print(f"  🎨 [{cfg['path']}] 시도 {attempt + 1}/3")
                r = requests.post(url, headers=headers, json=cfg['payload'], timeout=90)
                if r.status_code == 200:
                    path = f"liminal_{index:02d}.png"
                    with open(path, "wb") as f:
                        f.write(r.content)
                    print(f"  ✅ 저장: {path}")
                    return path
                elif r.status_code == 429:
                    wait = 15 * (attempt + 1)
                    print(f"  ⚠️ 429 Rate Limit. {wait}초 대기...")
                    time.sleep(wait)
                else:
                    print(f"  ⚠️ {r.status_code}. 다음 모델로.")
                    break
            except requests.exceptions.ConnectionError:
                print(f"  ⚠️ ConnectionError. 다음 모델로.")
                break
            except Exception as e:
                print(f"  ⚠️ 예외: {e}")
                time.sleep(3)
        print(f"  🔄 {cfg['path']} 포기. 백업 모델 시도.")
    return None


# ═══════════════════════════════════════════════════════════════════
# 텔레그램 — FIX: URL을 f-string으로 직접 조합 (markdown 포맷 제거)
# ═══════════════════════════════════════════════════════════════════

def send_to_telegram(story_meta, title, desc, img_path):
    caption = (
        f"🌀 *{story_meta['series_title']}*\n"
        f"📍 {story_meta['culture']} — {story_meta['location']}\n"
        f"💭 {story_meta['premise']}\n\n"
        f"🎬 *{title}*\n\n"
        f"{desc}"
    )[:1024]

    if img_path and os.path.exists(img_path):
        # FIX: 깨끗한 URL 직접 조합
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
        with open(img_path, "rb") as photo:
            r = requests.post(
                url,
                data={"chat_id": TG_CHAT_ID, "caption": caption, "parse_mode": "Markdown"},
                files={"photo": photo}
            )
    else:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        r = requests.post(
            url,
            data={"chat_id": TG_CHAT_ID, "text": caption + "\n\n⚠️ 이미지 생성 실패", "parse_mode": "Markdown"}
        )

    if r.status_code != 200:
        print(f"  ❌ 전송 실패 ({r.status_code}): {r.text}")
    else:
        print(f"  ✅ 텔레그램 전송 완료")


# ═══════════════════════════════════════════════════════════════════
# 메인
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("⚙️ 환경 변수 체크")
    print(f"  OpenRouter  : {'✅' if OPENROUTER_KEY else '❌ 누락'} ({len(OPENROUTER_KEY)}자)")
    print(f"  HuggingFace : {'✅' if HF_KEY else '❌ 누락'} ({len(HF_KEY)}자)")
    tg_preview = f"{TG_TOKEN[:4]}***{TG_TOKEN[-4:]}" if len(TG_TOKEN) > 8 else "유효하지 않음"
    print(f"  TG Token    : {tg_preview} ({len(TG_TOKEN)}자)")
    print(f"  TG Chat ID  : {TG_CHAT_ID}")
    print("-" * 50)

    try:
        free_models = get_active_free_models()

        # ── Phase 1: 스토리 컨셉 + 5단계 현실/비현실 아크 ────────────
        story = generate_story_concept(free_models)
        if not story or not story.get('reality_arc'):
            print("❌ 스토리 컨셉 생성 실패. 종료.")
            exit(1)

        story_meta = {
            "series_title":   story.get('series_title', 'The Drift'),
            "culture":        story.get('chosen_culture', 'Unknown'),
            "location":       story.get('chosen_location', 'Unknown'),
            "premise":        story.get('narrative_premise', ''),
            "aesthetic_type": story.get('aesthetic_type', 'liminal_space'),
            "color_palette":  story.get('primary_color_palette', '')
        }
        reality_arc = story.get('reality_arc', [])

        print(f"\n📋 '{story_meta['series_title']}'")
        print(f"📍 {story_meta['culture']} / {story_meta['location']}")
        print(f"🎨 {story_meta['aesthetic_type']} | {len(reality_arc)}단계 아크\n")

        # ── Phase 2: 순차 컷 생성 ─────────────────────────────────────
        scenes = []
        prev_description = None  # 직전 컷 description → 다음 컷 공간 앵커로 주입

        print("🎬 컷 순차 생성 시작\n")
        for stage_data in reality_arc:
            stage_num  = stage_data.get('stage', '?')
            stage_name = stage_data.get('stage_name', '')
            zone_name  = stage_data.get('zone_name', '')
            unreality  = stage_data.get('unreality_element', 'none')

            print(f"── Cut {stage_num} [{stage_name}]: {zone_name} ──")
            if unreality and unreality.lower() != 'none':
                print(f"   비현실 요소: {unreality[:90]}...")

            cut = generate_cut(stage_data, prev_description, story, free_models)
            if cut:
                scenes.append(cut)
                prev_description = cut.get('description', '')
                print(f"  📝 완료 ({len(prev_description)}자) | 다음 컷 앵커 준비됨")
            else:
                # 실패해도 prev_description 유지 → 체인 단절 방지
                print(f"  ⚠️ 실패. prev_description 유지하여 연속성 보존.")
            time.sleep(2)

        # ── Phase 3: 이미지 생성 + 텔레그램 전송 ─────────────────────
        print(f"\n🖼️ 이미지 생성 + 전송 ({len(scenes)}컷)\n")
        for i, scene in enumerate(scenes):
            print(f"── 이미지 {i + 1}/{len(scenes)} ──")
            img = generate_image(
                scene['video_prompt'], i,
                aesthetic_type=story_meta['aesthetic_type'],
                color_palette=story_meta['color_palette']
            )
            send_to_telegram(story_meta, scene['title'], scene['description'], img)
            time.sleep(10)

        print(f"\n🎉 완료! {len(scenes)}/5컷 처리됨.")

    except Exception as e:
        print(f"💥 에러: {e}")
        raise

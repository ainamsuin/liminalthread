import os
import re
import requests
import json
import time

# ─── 환경 변수 정제 ──────────────────────────────────────────────────

def sanitize_env(val):
    if not val:
        return ""
    return val.strip().strip("'\"").strip()

OPENROUTER_KEY = sanitize_env(os.getenv("OPENROUTER_API_KEY", ""))
HF_KEY         = sanitize_env(os.getenv("HF_API_KEY", ""))
TG_TOKEN       = sanitize_env(os.getenv("TELEGRAM_BOT_TOKEN", ""))
TG_CHAT_ID     = sanitize_env(os.getenv("TELEGRAM_CHAT_ID", ""))

if TG_TOKEN.lower().startswith("bot") and len(TG_TOKEN) > 3 and TG_TOKEN[3].isdigit():
    TG_TOKEN = TG_TOKEN[3:]


# ═══════════════════════════════════════════════════════════════════
# 🎨 미학 코덱스
# ═══════════════════════════════════════════════════════════════════
AESTHETIC_CODEX = {
    "liminal_space": (
        "Liminal spaces are TRANSITIONAL, IN-BETWEEN environments caught between uses: "
        "empty school gymnasiums after hours, hotel lobbies at 3am, "
        "mall food courts before opening, parking structures at dawn, "
        "empty swimming pools, airport gates between flights. "
        "VISUAL TRAITS: PRISTINE and INTACT (NO decay, NO ruin, NO damage), "
        "fluorescent or incandescent lighting, clean surfaces with minor normal wear. "
        "Eeriness from ABSENCE OF PEOPLE, not deterioration. "
        "Color temp: cool 4500-6500K fluorescent whites or warm 2700K incandescent yellows."
    ),
    "dreamcore": (
        "Dreamcore: intact nostalgic spaces from 1990s-2000s childhood, subtly 'off'. "
        "Locations: Discovery Zone or Chuck E. Cheese indoor play areas, "
        "suburban mall arcades, hotel indoor pools, elementary school cafeterias, "
        "roller skating rinks, daycare interiors, community center game rooms, "
        "bowling alleys, laundromats, VHS rental stores. "
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
        "Level 94: infinite supermarket aisles, flickering overhead lights. "
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
        "intact infinite space, fluorescent sodium yellow lights, slightly overexposed"
    )
}

NEGATIVE_PROMPT = (
    "ruins, ruin, decay, rot, graffiti, crumbling walls, structural damage, derelict, "
    "rubble, broken windows, peeling paint, mold, rust, post-apocalyptic, horror, "
    "people, human figure, silhouette, shadow of person, "
    "text, signs, watermark, logo, motion blur, camera shake, "
    "illustration, painting, cartoon, anime, CGI render, harsh shadows, "
    "hallway, corridor, morphing, transforming, changing, melting, shifting, "
    "motion, movement, dynamic, animated"
)

# ═══════════════════════════════════════════════════════════════════
# 현실→비현실 10단계 아크
#
# 핵심 원칙: 각 공간은 이미 그 상태로 존재한다.
# 영상 내에서 공간의 변형은 발생하지 않는다.
# 카메라와 공간 모두 완전히 정적이다.
# 각 단계는 "이 공간이 원래부터 이렇게 지어진/존재한 것"을 보여준다.
# ═══════════════════════════════════════════════════════════════════
UNREALITY_STAGES = {
    1: {
        "name": "GROUNDED_OPEN",
        "guide": (
            "A completely real, mundane space — just vast and empty. "
            "Proportions are normal. Lighting is normal. Nothing is wrong. "
            "The eeriness comes only from scale and the total absence of people. "
            "This space has always been exactly like this. "
            "No impossible features of any kind. No transformation, no movement."
        )
    },
    2: {
        "name": "GROUNDED_VAST",
        "guide": (
            "A real space whose proportions are slightly but undeniably off — "
            "the ceiling is one floor too high, or the room is 20% wider than a room this shape should be. "
            "This is how it was built. It has always been this size. "
            "Nothing moves or changes. The wrongness is architectural and permanent."
        )
    },
    3: {
        "name": "SUBTLE_HINT",
        "guide": (
            "A space where one small architectural detail was built impossibly — "
            "a window that faces an interior wall, a staircase with an extra landing that has no floor above, "
            "a door at the end of a room that opens onto a solid wall. "
            "This detail has always been here. The space does not react to it. "
            "Everything else is normal. Nothing moves."
        )
    },
    4: {
        "name": "SUBTLE_CONFIRM",
        "guide": (
            "The camera is now positioned inside or adjacent to the impossible detail from stage 3. "
            "The detail is clearly real and structural — it was built this way. "
            "A second, smaller impossible architectural feature is visible in the far distance: "
            "a room that appears to exist where the exterior wall should be, "
            "or a ceiling fixture that casts no shadow despite bright light. "
            "Both features are permanent. Neither moves."
        )
    },
    5: {
        "name": "UNCANNY_SINGLE",
        "guide": (
            "One clear, calm geometric impossibility dominates the frame — "
            "a room whose floor is also its ceiling with furniture on both surfaces, "
            "two identical rooms that exist side by side where only one should fit, "
            "a staircase that ascends in a closed loop. "
            "This is how the space was built. It has always looked this way. "
            "It is beautiful and eerie, not threatening. Nothing moves."
        )
    },
    6: {
        "name": "UNCANNY_SPREAD",
        "guide": (
            "Two separate geometric impossibilities are visible simultaneously in the same frame. "
            "They coexist calmly. Light sources in different parts of the frame "
            "cast shadows in conflicting directions — both shadow patterns are permanent, "
            "not changing. The space was constructed with these contradictions built in. "
            "Nothing moves or transforms."
        )
    },
    7: {
        "name": "SURREAL_FOLD",
        "guide": (
            "A topologically impossible space — like an Escher building made real. "
            "The far end of the space connects back to its own entrance, visible from the wide shot. "
            "Two surfaces that should be floor and ceiling are instead both floors. "
            "This geometry has always existed in this space. "
            "The space is calm and completely static. No movement, no transformation."
        )
    },
    8: {
        "name": "SURREAL_DEEP",
        "guide": (
            "Multiple physical laws are violated simultaneously in different zones of the frame, "
            "but all violations are permanent and stable — "
            "one zone has no visible light source yet is perfectly lit, "
            "another zone shows furniture adhering to a surface at 90 degrees to gravity, "
            "a third zone has a perfectly still reflection that shows a different room. "
            "All of these have always been this way. Nothing moves."
        )
    },
    9: {
        "name": "VOID_APPROACH",
        "guide": (
            "The space extends visibly and permanently beyond any boundary "
            "a physical building could contain — "
            "floor and ceiling surfaces continue past the point where perspective should cause them to vanish, "
            "implying infinite extension. "
            "This is not a transformation — the space has always been this large. "
            "Camera and space are both completely still."
        )
    },
    10: {
        "name": "VOID_COMPLETE",
        "guide": (
            "Total spatial dissolution — the space exists outside normal physics entirely. "
            "There are no walls, only the permanent suggestion of walls extending in all directions forever. "
            "Light exists with no source and has always done so. "
            "The narrative anchor is the only recognizable, scale-giving object — "
            "unchanged from Cut 1, perfectly ordinary, floating in the permanent infinite. "
            "Nothing moves. This has always been the final state of this space."
        )
    }
}

# 웹서치 쿼리 — 다양한 dreamcore 공간 발굴용
DREAMCORE_SEARCH_QUERIES = [
    "dreamcore aesthetic spaces 2024 types",
    "liminal space types rooms photography",
    "backrooms levels aesthetic spaces",
    "dreamcore nostalgia interior spaces 90s 2000s",
    "eerie empty indoor spaces photography aesthetic"
]


# ═══════════════════════════════════════════════════════════════════
# 유틸리티
# ═══════════════════════════════════════════════════════════════════

def get_active_free_models():
    url = "https://openrouter.ai/api/v1/models"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            free = [m for m in r.json().get('data', []) if ':free' in m['id']]

            def score(m):
                mid, ctx = m['id'].lower(), m.get('context_length', 0)
                if any(x in mid for x in ('coder', 'coding', 'code-', 'nemotron')):
                    return (-1, 0)
                s = 0
                if 'llama-3.3' in mid:                          s = 65
                elif 'qwen-2.5-72b' in mid:                     s = 60
                elif ('qwen3' in mid or 'qwen-3' in mid) and '72b' in mid: s = 58
                elif 'qwen-2.5' in mid:                         s = 55
                elif 'deepseek' in mid and 'coder' not in mid:  s = 50
                elif 'llama-3.1' in mid:                        s = 45
                elif 'gemma-3' in mid:                          s = 40
                elif 'gemma-2' in mid:                          s = 35
                elif 'qwen3' in mid or 'qwen-3' in mid:        s = 30
                elif 'phi-4' in mid:                            s = 25
                elif 'llama-3.2' in mid:                        s = 20
                return (s, ctx)

            free.sort(key=score, reverse=True)
            ids = [m['id'] for m in free if score(m)[0] >= 0]
            print(f"🎯 1순위 모델: {ids[0] if ids else 'None'} | 총 {len(ids)}개")
            return ids
    except Exception as e:
        print(f"⚠️ 모델 목록 오류: {e}")
    return ["meta-llama/llama-3.3-70b-instruct:free"]


def call_openrouter(messages, free_models, require_json=True, max_tokens=2500):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "Liminal Reality-Break Director"
    }

    def _try_model(mid):
        body = {"model": mid, "messages": messages, "max_tokens": max_tokens}
        if require_json:
            body["response_format"] = {"type": "json_object"}
        try:
            r = requests.post(url, headers=headers, json=body, timeout=60)
            if r.status_code == 200 and 'choices' in r.json():
                content = r.json()['choices'][0]['message']['content'].strip()
                if content.startswith("```"):
                    content = content.replace("```json", "").replace("```", "").strip()
                if len(content) < 80:
                    print(f"  ⚠️ 응답 너무 짧음 ({len(content)}자) [{mid}]")
                    return None
                return content
            if r.status_code == 429:
                return ('RATE_LIMIT', r.headers.get('Retry-After'))
            print(f"  ⚠️ {r.status_code} [{mid}]")
            return None
        except Exception as e:
            print(f"  ⚠️ 예외 [{mid}]: {e}")
            return None

    for mid in free_models:
        print(f"  🔄 [{mid}]")
        result = _try_model(mid)

        if isinstance(result, tuple) and result[0] == 'RATE_LIMIT':
            try:
                wait = min(int(result[1]), 90) if result[1] else 60
            except (ValueError, TypeError):
                wait = 60
            print(f"  ⚠️ 429 [{mid}] → {wait}초 대기 후 재시도...")
            time.sleep(wait)
            result = _try_model(mid)
            if isinstance(result, tuple):
                print(f"  ⚠️ 재시도도 429 [{mid}] → 다음 모델")
                time.sleep(5)
                continue
            if isinstance(result, str):
                print(f"  ✅ 재시도 성공 ({len(result)}자)")
                return result
            continue

        if isinstance(result, str):
            print(f"  ✅ 응답 ({len(result)}자)")
            return result

        time.sleep(3)

    print("  ⏳ 전체 모델 소진. 90초 대기 후 최종 재시도...")
    time.sleep(90)
    for mid in free_models[:3]:
        print(f"  🔄 [최종 재시도] [{mid}]")
        result = _try_model(mid)
        if isinstance(result, str):
            print(f"  ✅ 최종 재시도 성공 ({len(result)}자)")
            return result
        time.sleep(10)

    print("  ❌ 모든 재시도 소진")
    return None


# ═══════════════════════════════════════════════════════════════════
# Phase 0 — 웹서치: 다양한 dreamcore 공간 레퍼런스 수집
# DuckDuckGo Instant Answer API (무료, API키 불필요)
# ═══════════════════════════════════════════════════════════════════

def search_dreamcore_web(free_models):
    """
    DuckDuckGo로 dreamcore/liminal 공간 타입 검색 후
    LLM으로 다양한 공간 목록 추출.
    실패 시 빈 리스트 반환 (이후 LLM 내부 지식으로 대체).
    """
    print("\n🔍 [Phase 0] 웹서치: dreamcore 공간 레퍼런스 수집 중...")
    raw_snippets = []

    for q in DREAMCORE_SEARCH_QUERIES:
        try:
            enc_q = requests.utils.quote(q)
            url = f"https://api.duckduckgo.com/?q={enc_q}&format=json&no_html=1&skip_disambig=1"
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
            if r.status_code == 200:
                data = r.json()
                abstract = data.get('AbstractText', '')
                if abstract:
                    raw_snippets.append(abstract[:350])
                for topic in data.get('RelatedTopics', [])[:6]:
                    if isinstance(topic, dict):
                        text = topic.get('Text', '')
                        if text:
                            raw_snippets.append(text[:180])
            time.sleep(1.5)
        except Exception as e:
            print(f"  ⚠️ 검색 오류 ({q[:30]}): {e}")

    if not raw_snippets:
        print("  ⚠️ 웹서치 결과 없음 — LLM 내부 지식으로 진행")
        return []

    print(f"  📄 원시 스니펫 {len(raw_snippets)}개 수집. LLM으로 공간 타입 추출 중...")

    combined = "\n---\n".join(raw_snippets[:25])
    prompt = f"""You are a dreamcore/liminal space expert.
From the following web search snippets about dreamcore and liminal aesthetics,
extract and list 20 SPECIFIC, DIVERSE indoor space types that appear or are referenced.

RULES:
- No hallways, no corridors — these are banned
- Focus on ROOMS, AREAS, ZONES with distinct character
- Include unusual, specific, creative space types
- Mix familiar (90s arcade) with obscure (supermarket back room, hotel ice machine alcove)
- Cover a wide range of scale, from intimate to vast

Web search data:
{combined}

Output ONLY valid JSON:
{{"space_types": ["specific space type 1", "specific space type 2", ...]}}"""

    content = call_openrouter(
        [{"role": "user", "content": prompt}],
        free_models, require_json=True, max_tokens=600
    )
    if content:
        try:
            types = json.loads(content).get('space_types', [])
            # hallway/corridor 방어 필터
            types = [t for t in types if not any(
                w in t.lower() for w in ('hallway', 'corridor', 'hall way')
            )]
            print(f"  ✅ 공간 타입 {len(types)}개 추출: {', '.join(types[:5])}...")
            return types
        except Exception as e:
            print(f"  ⚠️ 추출 파싱 오류: {e}")

    return []


# ═══════════════════════════════════════════════════════════════════
# Phase 1 — 스토리 컨셉 + 10단계 아크
# ═══════════════════════════════════════════════════════════════════

def generate_story_concept(free_models, web_space_refs=None, max_retries=3):
    stage_guide = "\n".join(
        f"  Stage {k} ({v['name']}): {v['guide']}"
        for k, v in UNREALITY_STAGES.items()
    )
    aesthetic_summary = "\n".join(
        f"  [{k}]: {v[:220]}..." for k, v in AESTHETIC_CODEX.items()
    )

    # 웹서치 결과 주입
    if web_space_refs:
        web_ref_block = (
            f"WEB-SOURCED SPACE TYPES (use these as creative inspiration — "
            f"pick from this list or create variations, but never repeat the same type twice):\n"
            + "\n".join(f"  - {t}" for t in web_space_refs[:20])
        )
    else:
        web_ref_block = (
            "SPACE INSPIRATION (use diverse, creative, specific space types — "
            "no hallways, no corridors. "
            "Examples: indoor bowling alley, empty laundromat, roller skating rink, "
            "hotel indoor pool, arcade game room, elementary cafeteria, "
            "community center gymnasium, VHS rental store, indoor mini-golf, "
            "dental waiting room, motel lobby, supermarket produce section, "
            "hotel ice machine alcove, daycare nap room, mall photo booth area)"
        )

    prompt = f"""You are a narrative director specializing in liminal space, dreamcore, and backrooms.

Design a single coherent story for a 10-shot static wide-shot video sequence.
The sequence follows ONE CONTINUOUS JOURNEY through a single vast location,
gradually drifting from ordinary reality into serene spatial impossibility.

ABSOLUTE SPACE RULES:
1. NO hallways. NO corridors. Each zone must be a ROOM or AREA with its own distinct character.
2. Each space EXISTS in its current state permanently. It does not transform on camera.
   The camera is static. The space is static. The wrongness is built into the architecture.
3. Eeriness comes from what the space IS, not from anything happening or changing within it.
4. All spaces are INTACT and CLEAN — not ruined, not decayed.

NARRATIVE ANCHOR RULE:
Choose ONE small, concrete, ordinary object that appears in EVERY cut across all 10 stages.
Its position and state in each cut advances the story without anything physically changing.
Examples: a single shopping cart, a red folding umbrella, an open book, a small potted plant.

REALITY-TO-UNREALITY ARC (10 stages, one per cut):
{stage_guide}

AESTHETIC OPTIONS (choose ONE):
{aesthetic_summary}

{web_ref_block}

Output ONLY valid JSON:
{{
  "series_title": "[poetic English title]",
  "narrative_premise": "[3 sentences: what this place is, what the anchor object means, what the journey reveals]",
  "chosen_culture": "[e.g., USA, SOUTH KOREA, JAPAN]",
  "chosen_location": "[e.g., abandoned indoor water park, infinite underground shopping complex]",
  "aesthetic_type": "[liminal_space | dreamcore | backrooms]",
  "primary_color_palette": "[3-5 dominant hex colors with mood description]",
  "narrative_anchor": {{
    "object": "[exact name of the recurring object]",
    "origin_story": "[one sentence: why this object was left here]",
    "final_state": "[one sentence: what seeing it alone in Cut 10 means]"
  }},
  "reality_arc": [
    {{
      "stage": 1,
      "stage_name": "GROUNDED_OPEN",
      "zone_name": "[specific room/area name — NOT a hallway or corridor]",
      "zone_description": "[60-word: exact space type, intact architecture, materials, specific lighting]",
      "unreality_element": "none",
      "anchor_state": "[exact position and appearance of the anchor in this cut]",
      "story_beat": "[what this cut reveals — 1 sentence]",
      "visible_next_zone": "[which architectural opening or feature connects to stage 2's zone]"
    }},
    {{
      "stage": 2,
      "stage_name": "GROUNDED_VAST",
      "zone_name": "[specific room/area — NOT a hallway or corridor]",
      "zone_description": "[60 words]",
      "unreality_element": "proportions permanently wrong — space is 20% too large in one dimension",
      "anchor_state": "[anchor position — appears slightly farther than expected, space has always been this large]",
      "story_beat": "[1 sentence]",
      "visible_next_zone": "[connection to stage 3]"
    }},
    {{
      "stage": 3,
      "stage_name": "SUBTLE_HINT",
      "zone_name": "[specific room/area — NOT a hallway or corridor]",
      "zone_description": "[60 words]",
      "unreality_element": "[one impossible architectural detail built into the space — permanent, static]",
      "anchor_state": "[anchor position — shadow or reflection subtly wrong but unchanging]",
      "story_beat": "[1 sentence]",
      "visible_next_zone": "[connection to stage 4]"
    }},
    {{
      "stage": 4,
      "stage_name": "SUBTLE_CONFIRM",
      "zone_name": "[specific room/area — NOT a hallway or corridor]",
      "zone_description": "[60 words]",
      "unreality_element": "[stage 3 anomaly now fills the foreground; a second impossible static detail in far distance]",
      "anchor_state": "[anchor is in an impossible position — it was always here, no one moved it]",
      "story_beat": "[1 sentence]",
      "visible_next_zone": "[connection to stage 5]"
    }},
    {{
      "stage": 5,
      "stage_name": "UNCANNY_SINGLE",
      "zone_name": "[specific room/area — NOT a hallway or corridor]",
      "zone_description": "[60 words]",
      "unreality_element": "[one clear impossible architecture that has always existed this way — beautiful and calm]",
      "anchor_state": "[anchor duplicated — two identical copies, both real, equidistant]",
      "story_beat": "[1 sentence]",
      "visible_next_zone": "[connection to stage 6]"
    }},
    {{
      "stage": 6,
      "stage_name": "UNCANNY_SPREAD",
      "zone_name": "[specific room/area — NOT a hallway or corridor]",
      "zone_description": "[60 words]",
      "unreality_element": "[two simultaneous impossible architectural features; light shadows permanently conflicting]",
      "anchor_state": "[anchor multiplied to 3-4 copies, forming a static pattern]",
      "story_beat": "[1 sentence]",
      "visible_next_zone": "[connection to stage 7]"
    }},
    {{
      "stage": 7,
      "stage_name": "SURREAL_FOLD",
      "zone_name": "[specific room/area — NOT a hallway or corridor]",
      "zone_description": "[60 words]",
      "unreality_element": "[Escher-like static topology — far end connects back to entrance, visible in single wide shot]",
      "anchor_state": "[anchor tiled across every surface — floor wall ceiling — always been this way]",
      "story_beat": "[1 sentence]",
      "visible_next_zone": "[connection to stage 8]"
    }},
    {{
      "stage": 8,
      "stage_name": "SURREAL_DEEP",
      "zone_name": "[specific room/area — NOT a hallway or corridor]",
      "zone_description": "[60 words]",
      "unreality_element": "[multiple physical laws permanently violated in separate static zones of the same frame]",
      "anchor_state": "[anchor has become part of the architecture — built into the structure itself]",
      "story_beat": "[1 sentence]",
      "visible_next_zone": "[connection to stage 9]"
    }},
    {{
      "stage": 9,
      "stage_name": "VOID_APPROACH",
      "zone_name": "[specific room/area — NOT a hallway or corridor]",
      "zone_description": "[60 words]",
      "unreality_element": "[space permanently extends beyond visible physical limits — has always been infinite]",
      "anchor_state": "[anchor appears once, tiny, centered in infinite middle distance]",
      "story_beat": "[1 sentence]",
      "visible_next_zone": "[connection to stage 10]"
    }},
    {{
      "stage": 10,
      "stage_name": "VOID_COMPLETE",
      "zone_name": "[specific room/area — NOT a hallway or corridor]",
      "zone_description": "[60 words]",
      "unreality_element": "[total static dissolution — space exists outside physics, has always been this way]",
      "anchor_state": "[anchor alone in infinite space, unchanged from Cut 1 — the only real thing remaining]",
      "story_beat": "[the final revelation — 1 sentence]",
      "visible_next_zone": ""
    }}
  ]
}}"""

    print("\n📖 [Phase 1] 스토리 컨셉 + 10단계 아크 생성 중...")

    for attempt in range(1, max_retries + 1):
        if attempt > 1:
            print(f"  🔄 Phase 1 재시도 {attempt}/{max_retries}...")
            time.sleep(20)

        content = call_openrouter(
            [{"role": "user", "content": prompt}],
            free_models, require_json=True, max_tokens=4500
        )

        if not content:
            print(f"  ⚠️ 응답 없음 (시도 {attempt}/{max_retries})")
            continue

        try:
            sc = json.loads(content)
            arc = sc.get('reality_arc', [])

            if len(arc) < 10:
                print(f"  ⚠️ reality_arc {len(arc)}단계 — 10단계 필요. 재시도.")
                continue

            # hallway/corridor 방어 필터
            blocked = []
            for stage in arc:
                zn = stage.get('zone_name', '').lower()
                zd = stage.get('zone_description', '').lower()
                if any(w in zn or w in zd for w in ('hallway', 'corridor', 'hall way')):
                    blocked.append(stage.get('stage'))
            if blocked:
                print(f"  ⚠️ hallway/corridor 감지 (stage {blocked}). 재시도.")
                continue

            raw = sc.get('aesthetic_type', '').lower()
            if 'dreamcore' in raw:   sc['aesthetic_type'] = 'dreamcore'
            elif 'backroom' in raw:  sc['aesthetic_type'] = 'backrooms'
            else:                    sc['aesthetic_type'] = 'liminal_space'

            anchor = sc.get('narrative_anchor', {})
            print(f"✅ 컨셉: '{sc.get('series_title')}' | {sc['aesthetic_type']} | {len(arc)}단계")
            print(f"   내러티브: {sc.get('narrative_premise', '')[:150]}")
            print(f"   앵커: {anchor.get('object', 'N/A')}")
            return sc

        except json.JSONDecodeError as e:
            print(f"  ❌ JSON 파싱 오류 (시도 {attempt}/{max_retries}): {e}")

    print("❌ 스토리 컨셉 생성 실패")
    return None


# ═══════════════════════════════════════════════════════════════════
# Phase 2 — 순차 컷 생성
# ═══════════════════════════════════════════════════════════════════

def generate_cut(stage_data, prev_cuts_summary, story_concept, free_models):
    stage_num    = stage_data.get('stage', 1)
    stage_name   = stage_data.get('stage_name', 'GROUNDED_OPEN')
    zone_name    = stage_data.get('zone_name', '')
    zone_desc    = stage_data.get('zone_description', '')
    unreality    = stage_data.get('unreality_element', 'none')
    anchor_state = stage_data.get('anchor_state', '')
    story_beat   = stage_data.get('story_beat', '')
    visible_next = stage_data.get('visible_next_zone', '')

    aesthetic_type  = story_concept.get('aesthetic_type', 'liminal_space')
    aesthetic_guide = AESTHETIC_CODEX.get(aesthetic_type, '')
    color_palette   = story_concept.get('primary_color_palette', '')
    premise         = story_concept.get('narrative_premise', '')
    anchor_obj      = story_concept.get('narrative_anchor', {}).get('object', '')
    anchor_origin   = story_concept.get('narrative_anchor', {}).get('origin_story', '')
    anchor_final    = story_concept.get('narrative_anchor', {}).get('final_state', '')

    if prev_cuts_summary:
        prev_last = prev_cuts_summary[-1]
        older_cuts = prev_cuts_summary[:-1]

        older_block = ""
        if older_cuts:
            older_lines = "\n".join(
                f"  Cut {c['stage']} [{c['stage_name']}] — {c['zone_name']}: "
                f"anchor={c['anchor_state']} | beat={c['story_beat']}"
                for c in older_cuts
            )
            older_block = f"EARLIER CUTS (anchor trajectory):\n{older_lines}\n\n"

        continuity_block = (
            f"{older_block}"
            f"PREVIOUS CUT — Cut {prev_last['stage']} [{prev_last['stage_name']}] "
            f"in zone '{prev_last['zone_name']}' — FULL DESCRIPTION:\n"
            f"{prev_last['description']}\n\n"
            f"ANCHOR IN PREVIOUS CUT: {prev_last['anchor_state']}\n\n"
            f"THIS CUT MUST:\n"
            f"1. Open with the camera already positioned in the space that was visible "
            f"at the end of Cut {prev_last['stage']} — specifically: '{visible_next}'\n"
            f"2. The first architectural element described must be that connecting feature.\n"
            f"3. The spatial journey feels like a single continuous walk — "
            f"the viewer moved from the previous zone into this one.\n"
            f"4. The anchor must be in the exact state: {anchor_state}"
        )
        desc_opening_rule = (
            f"Open with the connecting feature from Cut {prev_last['stage']} "
            f"now in the foreground. Then describe '{zone_name}'."
        )
    else:
        continuity_block = (
            "This is the OPENING SHOT (Cut 1). "
            "Establish the exact space, its full scale, color palette, "
            "and the narrative anchor's precise mundane position. "
            "This should feel like the most ordinary, real version of this space possible."
        )
        desc_opening_rule = (
            "Establish: exact space type and architecture, dominant colors and materials, "
            "specific lighting (color temp + fixture type + positions), "
            "and the narrative anchor's precise position. Tone: completely real and mundane, but vast and empty."
        )

    if unreality and unreality.lower() != 'none':
        unreality_block = (
            f"EXISTING SPATIAL ANOMALY (Stage {stage_num}: {stage_name}):\n"
            f"{unreality}\n\n"
            f"CRITICAL: This anomaly is PERMANENT and STATIC — the space was built or exists this way. "
            f"Nothing transforms, morphs, or changes within the frame. "
            f"The camera is fixed. The space is fixed. The wrongness is architectural fact."
        )
    else:
        unreality_block = (
            f"NO ANOMALY (Stage 1 — fully real):\n"
            f"Zero impossible features. Everything is normal architecture. "
            f"Camera and space are both completely static."
        )

    video_unreality = unreality if unreality.lower() != 'none' else 'purely realistic static empty space'

    prompt = f"""You are generating Cut {stage_num} of 10 for a liminal space narrative series.

═══ SERIES CONTEXT ═══
NARRATIVE PREMISE: {premise}
AESTHETIC: {aesthetic_type.upper()} — {aesthetic_guide}
COLOR PALETTE: {color_palette}

NARRATIVE ANCHOR (present in every cut):
  Object: {anchor_obj}
  Why it's here: {anchor_origin}
  What it means in Cut 10: {anchor_final}

═══ THIS CUT ═══
ZONE: {zone_name}
ZONE DETAILS: {zone_desc}
ANCHOR THIS CUT: {anchor_state}
STORY BEAT: {story_beat}
NEXT ZONE (visible from this cut): {visible_next}

═══ CONTINUITY ═══
{continuity_block}

═══ SPATIAL ANOMALY ═══
{unreality_block}

═══ ABSOLUTE RULES ═══
1. Camera: 100% STATIC TRIPOD. EXTREME WIDE SHOT. Zero movement of any kind.
2. Space: STATIC. Nothing transforms, morphs, or changes within the frame.
   The space exists in its current state permanently. It was always this way.
3. Space: INTACT, CLEAN, FUNCTIONING. Zero decay, ruin, or damage.
4. No people, silhouettes, or shadows of people.
5. No visible text, signs, or numbers.
6. No hallways. No corridors. The zone must be a distinct room or area.
7. Tone: eerie and beautiful, dreamlike, calm — NOT horrifying or violent.
8. Anchor must be explicitly placed: {anchor_state}

Output ONLY valid JSON:
{{
  "title": "Cut {stage_num}/10 [{stage_name}]: {zone_name}",
  "description": "[1000-1200 character English narrative. {desc_opening_rule} Then: exact architecture seen from static extreme wide distance, specific lighting details, the narrative anchor's current position and state, the spatial anomaly as a calm permanent fact (if any), one detail that threads back to the previous cut. Tone: calm, vast, beautiful, quietly wrong.]",
  "video_prompt": "[Detailed text-to-image prompt: static extreme wide shot, {aesthetic_type} aesthetic, {color_palette}, intact clean empty architecture in {zone_name}, {video_unreality}, {anchor_obj} visible, film grain, no people, no text, NOT ruined, no hallway, no corridor, serene and eerie, perfectly still]"
}}"""

    content = call_openrouter(
        [{"role": "user", "content": prompt}],
        free_models, require_json=True, max_tokens=2500
    )
    if not content:
        return None
    try:
        result = json.loads(content)
        # 체인 전달용 메타데이터 주입
        result['stage']       = stage_num
        result['stage_name']  = stage_name
        result['zone_name']   = zone_name
        result['anchor_state'] = anchor_state
        result['story_beat']  = story_beat
        return result
    except json.JSONDecodeError as e:
        print(f"  ❌ Cut {stage_num} JSON 파싱 오류: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════
# 이미지 생성
# ═══════════════════════════════════════════════════════════════════

def build_image_prompt(raw_prompt, aesthetic_type, color_palette):
    style = IMAGE_STYLE_SUFFIX.get(aesthetic_type, IMAGE_STYLE_SUFFIX['liminal_space'])
    # hallway/corridor 방어 필터
    clean = re.sub(r'\b(hallway|corridor|hall way)\b', '', raw_prompt, flags=re.IGNORECASE)
    return f"{clean.strip()}, {style}, dominant colors: {color_palette}"


def generate_image(prompt, index, aesthetic_type='liminal_space', color_palette=''):
    if not prompt or not isinstance(prompt, str):
        prompt = "A perfectly static extreme wide tripod shot of a massive empty dreamcore interior space."

    enhanced = build_image_prompt(prompt, aesthetic_type, color_palette)
    headers = {"Authorization": f"Bearer {HF_KEY}"}

    models_cfg = [
        {
            "path": "black-forest-labs/FLUX.1-schnell",
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
# 텔레그램 전송
# ═══════════════════════════════════════════════════════════════════

def send_to_telegram(story_meta, title, desc, img_path, cut_num=None, total=10):
    short_caption = (
        f"🌀 *{story_meta['series_title']}*\n"
        f"📍 {story_meta['culture']} — {story_meta['location']}\n"
        f"🎬 *{title}*"
    )
    if cut_num:
        short_caption += f"\n[{cut_num}/{total}]"

    full_text = (
        f"💭 {story_meta['premise']}\n\n"
        f"{desc}"
    )

    def _send(url, **kwargs):
        r = requests.post(url, **kwargs)
        if r.status_code != 200:
            print(f"  ❌ 전송 실패 ({r.status_code}): {r.text}")
            return False
        return True

    if img_path and os.path.exists(img_path):
        with open(img_path, "rb") as photo:
            ok = _send(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto",
                data={"chat_id": TG_CHAT_ID, "caption": short_caption, "parse_mode": "Markdown"},
                files={"photo": photo}
            )
        if ok:
            _send(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                data={"chat_id": TG_CHAT_ID, "text": full_text, "parse_mode": "Markdown"}
            )
    else:
        full_fallback = f"{short_caption}\n\n{full_text}\n\n⚠️ 이미지 생성 실패"
        _send(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data={"chat_id": TG_CHAT_ID, "text": full_fallback, "parse_mode": "Markdown"}
        )

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

        # ── Phase 0: 웹서치 — dreamcore 공간 레퍼런스 수집 ───────────
        web_space_refs = search_dreamcore_web(free_models)

        # ── Phase 1: 스토리 컨셉 + 10단계 아크 ───────────────────────
        story = generate_story_concept(free_models, web_space_refs=web_space_refs, max_retries=3)
        if not story or not story.get('reality_arc'):
            print("❌ 스토리 컨셉 생성 실패. 종료.")
            exit(1)

        anchor = story.get('narrative_anchor', {})
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
        print(f"🎨 {story_meta['aesthetic_type']} | {len(reality_arc)}단계")
        print(f"🔑 앵커: {anchor.get('object', 'N/A')}\n")

        # ── Phase 2: 순차 컷 생성 ─────────────────────────────────────
        scenes = []
        prev_cuts_summary = []

        print("🎬 컷 순차 생성 시작 (10컷)\n")
        for stage_data in reality_arc:
            stage_num  = stage_data.get('stage', '?')
            stage_name = stage_data.get('stage_name', '')
            zone_name  = stage_data.get('zone_name', '')
            anchor_st  = stage_data.get('anchor_state', '')

            print(f"── Cut {stage_num}/10 [{stage_name}]: {zone_name} ──")
            print(f"   앵커: {anchor_st[:80]}...")

            cut = generate_cut(stage_data, prev_cuts_summary, story, free_models)

            if cut:
                scenes.append(cut)
                prev_cuts_summary.append({
                    "stage":        stage_num,
                    "stage_name":   stage_name,
                    "zone_name":    zone_name,
                    "description":  cut.get('description', ''),
                    "anchor_state": anchor_st,
                    "story_beat":   stage_data.get('story_beat', '')
                })
                print(f"  📝 완료 ({len(cut.get('description',''))}자)")
            else:
                print(f"  ⚠️ 실패. 이전 체인 유지.")
            time.sleep(2)

        # ── Phase 3: 이미지 생성 + 텔레그램 전송 ─────────────────────
        total_scenes = len(scenes)
        print(f"\n🖼️ 이미지 생성 + 전송 ({total_scenes}컷)\n")
        for i, scene in enumerate(scenes):
            cut_num = scene.get('stage', i + 1)
            print(f"── 이미지 {i + 1}/{total_scenes} (Cut {cut_num}) ──")
            img = generate_image(
                scene['video_prompt'], i,
                aesthetic_type=story_meta['aesthetic_type'],
                color_palette=story_meta['color_palette']
            )
            send_to_telegram(
                story_meta, scene['title'], scene['description'],
                img, cut_num=cut_num, total=total_scenes
            )
            time.sleep(10)

        print(f"\n🎉 완료! {total_scenes}/10컷 처리됨.")

    except Exception as e:
        print(f"💥 에러: {e}")
        raise

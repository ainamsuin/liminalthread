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
# 4가지 미학 타입: liminal_space / dreamcore / weirdcore / backrooms
# 핵심 감정: anemoia(가본 적 없는 과거에 대한 향수) + derealization(비현실감)
# ═══════════════════════════════════════════════════════════════════
AESTHETIC_CODEX = {
    "liminal_space": (
        "Liminal spaces are transitional environments caught between uses — "
        "gas stations at dusk with no customers, empty residential cul-de-sacs at twilight, "
        "hotel lobbies at 3am, mall escalator atria before opening, parking structures at dawn, "
        "empty swimming pools, airport gates between flights, "
        "small churches lit warmly from inside at night against a dark street. "
        "VISUAL TRAITS: PRISTINE and INTACT, sodium vapor or fluorescent lighting against darkening exteriors, "
        "warm 2700K incandescent or cool 5000K fluorescent. "
        "VHS grain and mildly faded color palette. "
        "Eeriness from ABSENCE OF PEOPLE in spaces that should be full of life. "
        "Core emotion: ANEMOIA — nostalgia for a time and place you have never actually visited."
    ),
    "dreamcore": (
        "Dreamcore: intact nostalgic spaces from 1990s-2000s childhood that feel subtly wrong. "
        "Locations: empty indoor playgrounds (ball pit rooms, foam cube pits, tube mazes), "
        "Discovery Zone or Chuck E. Cheese game areas, suburban mall arcades, "
        "hotel indoor pools with no swimmers, elementary school cafeterias at night, "
        "roller skating rinks with empty skate floor, daycare interiors, "
        "community center gymnasiums, bowling alleys with every lane empty, "
        "laundromats at 2am, VHS rental stores with full shelves and no customers. "
        "VISUAL TRAITS: soft pastels (dusty pink #D4A5A5, mint #98D8C8, pale yellow #F5E6A3, baby blue #A8C8E8), "
        "warm diffused non-directional glow, VHS film grain, analog video noise. "
        "Everything CLEAN and INTACT — achingly familiar yet quietly wrong. "
        "Core emotion: COMFORT and EERIE simultaneously — the warm unsettling feeling."
    ),
    "weirdcore": (
        "Weirdcore: spaces that feel like scenes from a half-remembered dream or a nightmare set. "
        "Locations: bathrooms tiled entirely in oversaturated orange or deep red, "
        "rooms lit only by a single colored window (crimson, sickly green, sodium orange), "
        "empty diners with wrong-colored vinyl booths, motel rooms with inexplicable wall decor, "
        "office break rooms with garish patterned carpet, gas stations at 3am under flat white light, "
        "empty residential streets under yellow sodium lamps in heavy fog. "
        "VISUAL TRAITS: wrong color temperature (too warm, too pink, too green), "
        "extreme single-source lighting creating deep shadows, "
        "distorted or slightly wrong proportions, heavy VHS scan lines and grain. "
        "Core emotion: DEREALIZATION — the world looks real but feels like a stage set or a dream."
    ),
    "backrooms": (
        "Backrooms canonical levels: "
        "Level 0: infinite yellow wallpaper (#D4C17A), fluorescent tubes, damp carpet. "
        "Level 5: infinite hotel lobby, maroon-gold carpet, yellow chandeliers. "
        "Level 37 (Poolrooms): infinite indoor pools, cyan-mint tiles, still reflective water, "
        "sourceless diffused light. "
        "Level 94: infinite supermarket aisles under flickering overhead fluorescents. "
        "VISUAL TRAITS: INTACT spaces with infinite repetition, "
        "found-footage lo-fi grain, ambient fluorescent hum. "
        "Core emotion: WRONGNESS — the architecture implies spaces that should not exist."
    )
}

IMAGE_STYLE_SUFFIX = {
    "liminal_space": (
        "liminal space analog photography, VHS film grain, faded desaturated colors, "
        "intact clean empty space, sodium vapor or fluorescent lighting, "
        "anemoia nostalgia, photorealistic, hyperrealistic, lo-fi analog texture"
    ),
    "dreamcore": (
        "dreamcore aesthetic, soft desaturated pastel palette, 1990s 2000s nostalgia, "
        "warm diffused analog glow, VHS film grain, analog video noise, faded photograph, "
        "empty intact clean, comfort and eerie simultaneously, lo-fi childhood memory"
    ),
    "weirdcore": (
        "weirdcore aesthetic, VHS scan lines, analog video degradation, "
        "wrong oversaturated color temperature, single harsh light source, deep shadows, "
        "derealization uncanny surreal, dreamlike, distorted proportions, "
        "empty space, no people, eerie"
    ),
    "backrooms": (
        "backrooms found footage photography, hyperrealistic, lo-fi VHS grain, "
        "intact infinite space, fluorescent sodium yellow lights, slightly overexposed, "
        "analog video noise, found footage aesthetic"
    )
}

# weirdcore는 harsh shadows가 의도적이므로 해당 타입에서는 제외 처리
NEGATIVE_PROMPT_BASE = (
    "ruins, ruin, decay, rot, graffiti, crumbling walls, structural damage, derelict, "
    "rubble, broken windows, peeling paint, mold, rust, post-apocalyptic, "
    "people, human figure, silhouette, shadow of person, "
    "text, signs, watermark, logo, motion blur, camera shake, "
    "illustration, painting, cartoon, anime, CGI render, "
    "hallway, corridor, morphing, transforming, changing, melting, shifting, "
    "motion, movement, dynamic, animated"
)
NEGATIVE_PROMPT_NON_WEIRD = NEGATIVE_PROMPT_BASE + ", harsh shadows, horror"
NEGATIVE_PROMPT_WEIRDCORE = NEGATIVE_PROMPT_BASE + ", horror, gore"


# ═══════════════════════════════════════════════════════════════════
# 현실→비현실 10단계 아크
# 각 공간은 그 상태로 이미 존재한다. 카메라와 공간 모두 완전히 정적.
# ═══════════════════════════════════════════════════════════════════
UNREALITY_STAGES = {
    1: {
        "name": "GROUNDED_OPEN",
        "guide": (
            "Completely real. A vast, empty space that should be full of people but isn't. "
            "Normal architecture, normal lighting, zero anomalies. "
            "The narrative anchor appears in its expected, mundane position. "
            "Emotional quality: anemoia — the place feels like a memory you don't have."
        )
    },
    2: {
        "name": "GROUNDED_VAST",
        "guide": (
            "Still fully real, but one dimension is permanently wrong — "
            "the ceiling is one floor too high, or the room is 20% too wide for its shape. "
            "This is how it was built. The anchor is in a plausible position but seems farther away "
            "than the architecture should allow."
        )
    },
    3: {
        "name": "SUBTLE_HINT",
        "guide": (
            "One small architectural detail was built impossibly — "
            "a window facing an interior wall, a door that opens onto solid floor, "
            "a staircase with a landing that has no floor above. "
            "This has always been here. The anchor's shadow or reflection is subtly wrong. "
            "Everything else is normal."
        )
    },
    4: {
        "name": "SUBTLE_CONFIRM",
        "guide": (
            "The camera is now inside or adjacent to the impossible detail from stage 3. "
            "It is clearly real and structural. A second small impossibility is faintly visible "
            "in the far distance — a room where the exterior wall should be. "
            "The anchor has moved to a position no one could have placed it. "
            "Both features are permanent and static."
        )
    },
    5: {
        "name": "UNCANNY_SINGLE",
        "guide": (
            "One clear, calm geometric impossibility dominates the frame — "
            "a room whose floor is also its ceiling with furniture on both surfaces, "
            "two identical rooms existing side by side where only one could fit, "
            "a staircase ascending in a closed loop with no exit. "
            "Built this way. Has always looked like this. The anchor is now duplicated — "
            "two identical copies, equidistant, both equally real."
        )
    },
    6: {
        "name": "UNCANNY_SPREAD",
        "guide": (
            "Two geometric impossibilities coexist calmly in the same frame. "
            "Light sources cast shadows in permanently conflicting directions. "
            "The space was constructed with these contradictions built in. "
            "The anchor has multiplied to 3-4 copies forming a quiet pattern. Nothing moves."
        )
    },
    7: {
        "name": "SURREAL_FOLD",
        "guide": (
            "A topologically impossible space, like an Escher building made real — "
            "the far end of the space connects back to its own entrance, visible from the wide shot. "
            "Two surfaces that should be floor and ceiling are both floors. "
            "The anchor tiles across every surface — floor, wall, ceiling — always been this way. "
            "Calm and static."
        )
    },
    8: {
        "name": "SURREAL_DEEP",
        "guide": (
            "Multiple physical laws are permanently violated in different zones of the same frame — "
            "one zone has no visible light source yet is perfectly lit, "
            "another has furniture adhering to a 90-degree surface, "
            "a third shows a reflection of a completely different room. "
            "All permanent. The anchor has become part of the architecture itself. Nothing moves."
        )
    },
    9: {
        "name": "VOID_APPROACH",
        "guide": (
            "The space extends permanently beyond any physical limit — "
            "floors and ceilings continue past the point perspective should erase them, "
            "implying infinite extension. This is how the space has always been. "
            "The anchor appears once, tiny, perfectly centered in the infinite middle distance — "
            "the last recognizable scale reference."
        )
    },
    10: {
        "name": "VOID_COMPLETE",
        "guide": (
            "Total permanent spatial dissolution — the space exists outside physics entirely. "
            "No walls, only the permanent suggestion of walls extending forever in all directions. "
            "Light exists with no source and has always done so. "
            "The anchor is unchanged from Cut 1: perfectly ordinary, perfectly alone, "
            "the only proof this place was ever real. Nothing moves. This has always been the end."
        )
    }
}

DREAMCORE_SEARCH_QUERIES = [
    "dreamcore aesthetic spaces 2024 types rooms",
    "liminal space photography locations types outdoor indoor",
    "weirdcore aesthetic spaces surreal rooms",
    "backrooms levels aesthetic spaces rooms",
    "vaporwave liminal space nostalgia anemoia photography"
]

# 자동 교체용 대안 공간 목록 (hallway/corridor 감지 시 사용)
# 실내+실외 혼합, 분석에서 언급된 공간 포함
ZONE_ALTS = [
    "Gas Station Canopy at Dusk",
    "Empty Indoor Playground Ball Pit Room",
    "Roller Skating Rink Floor",
    "Hotel Indoor Pool Deck",
    "Arcade Game Room",
    "Elementary School Cafeteria",
    "Bowling Alley Lane Area",
    "Laundromat Interior at 2am",
    "Community Center Gymnasium",
    "Supermarket Produce Section",
    "Indoor Mini-Golf Course",
    "Airport Gate Lounge",
    "Underground Food Court Atrium",
    "Small Church Interior at Night",
    "Suburban Backyard at Twilight",
    "Empty Residential Cul-de-sac",
    "Motel Exterior Courtyard at Night",
    "Indoor Water Park Basin",
    "VHS Rental Store",
    "Mall Escalator Atrium"
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
        "X-Title": "derealisat"
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
# Phase 0 — 웹서치: dreamcore/weirdcore 공간 레퍼런스 수집
# ═══════════════════════════════════════════════════════════════════

def search_dreamcore_web(free_models):
    print("\n🔍 [Phase 0] 웹서치: 공간 레퍼런스 수집 중...")
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
            print(f"  ⚠️ 검색 오류: {e}")

    if not raw_snippets:
        print("  ⚠️ 웹서치 결과 없음 — 내장 레퍼런스로 진행")
        return []

    print(f"  📄 스니펫 {len(raw_snippets)}개 수집. 공간 타입 추출 중...")
    combined = "\n---\n".join(raw_snippets[:25])
    prompt = f"""From these web search results about dreamcore, weirdcore, liminal space, and vaporwave aesthetics,
extract 20 SPECIFIC, DIVERSE space types — both indoor and outdoor — that embody these aesthetics.

RULES:
- No hallways, no corridors
- Include outdoor transitional spaces (gas stations, streets, churches, parking lots)
- Include unusual indoor spaces (ball pit rooms, roller rinks, VHS stores)
- Include weirdcore-specific spaces (wrong-colored bathrooms, motel rooms, empty diners)
- Mix familiar with obscure

Web data:
{combined}

Output ONLY valid JSON:
{{"space_types": ["type 1", "type 2", ...]}}"""

    content = call_openrouter(
        [{"role": "user", "content": prompt}],
        free_models, require_json=True, max_tokens=600
    )
    if content:
        try:
            types = json.loads(content).get('space_types', [])
            types = [t for t in types if not any(
                w in t.lower() for w in ('hallway', 'corridor', 'hall way')
            )]
            print(f"  ✅ {len(types)}개 추출: {', '.join(types[:4])}...")
            return types
        except Exception as e:
            print(f"  ⚠️ 추출 오류: {e}")
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
        f"  [{k}]: {v[:250]}..." for k, v in AESTHETIC_CODEX.items()
    )

    if web_space_refs:
        web_ref_block = (
            "WEB-SOURCED SPACE TYPES (use as creative inspiration — never repeat the same type twice, "
            "include both indoor and outdoor spaces):\n"
            + "\n".join(f"  - {t}" for t in web_space_refs[:20])
        )
    else:
        web_ref_block = (
            "SPACE INSPIRATION — include BOTH indoor and outdoor transitional spaces:\n"
            "  Indoor: empty indoor playground, roller skating rink, hotel indoor pool, arcade room,\n"
            "    elementary school cafeteria, bowling alley, laundromat, VHS rental store,\n"
            "    indoor mini-golf, mall escalator atrium, community center gym\n"
            "  Outdoor/Transitional: gas station canopy at dusk, empty residential street at night,\n"
            "    small church exterior lit from inside, motel exterior courtyard, suburban backyard,\n"
            "    empty parking lot under sodium lamps, outdoor mall walkway at dawn\n"
            "  Weirdcore-specific: orange-tiled bathroom, room lit by single red window,\n"
            "    empty diner with wrong-colored booths, office break room with garish carpet"
        )

    prompt = f"""You are a visual artist creating content for the @derealisat aesthetic channel.
Your work embodies derealization — spaces that feel like memories you never had.

Design a 10-shot static image slideshow series. Each image is a perfectly still wide shot
of a single empty space, lit atmospherically, with VHS analog grain texture.
The 10 images form a continuous journey that drifts from mundane reality into serene impossibility.

EMOTIONAL CORE:
- ANEMOIA: nostalgia for times and places you have never actually experienced
- DEREALIZATION: familiar spaces that feel like dream sets or stage props
- COMFORT + EERIE simultaneously: the warm unsettling feeling of an empty space that should be occupied
- VHS ANALOG TEXTURE throughout: every image feels like a found tape from the 1990s

ABSOLUTE RULES:
1. NO hallways. NO corridors. Every zone is a ROOM, AREA, or OUTDOOR SPACE with distinct character.
2. Each space EXISTS in its current state permanently — nothing transforms on camera.
3. Include BOTH indoor and outdoor/transitional spaces across the 10 cuts.
4. All spaces are INTACT and CLEAN — no decay, no ruin.
5. Camera and space: completely static in every cut.

TITLE FORMAT:
The series title must be CRYPTIC and MINIMAL — either:
  - 1 to 3 enigmatic lowercase English words (e.g., "last summer", "someone's house", "not yet")
  - OR a single phrase with unicode block characters (e.g., "░░░░░", "the ▓▓▓▓ place")
  - NEVER a full descriptive sentence. NEVER more than 5 words.

NARRATIVE ANCHOR:
One small ordinary object appears in every cut. Its changing position IS the story.

REALITY-TO-UNREALITY ARC:
{stage_guide}

AESTHETIC OPTIONS (choose ONE):
{aesthetic_summary}

{web_ref_block}

Output ONLY valid JSON:
{{
  "series_title": "[cryptic minimal title — 1-5 words, can include unicode block chars like ░ ▒ ▓]",
  "narrative_premise": "[3 sentences: what this place is, why the anchor was left here, what drifting deeper reveals]",
  "chosen_culture": "[e.g., USA, SOUTH KOREA, JAPAN]",
  "chosen_location": "[poetic location name — avoid plain descriptions]",
  "aesthetic_type": "[liminal_space | dreamcore | weirdcore | backrooms]",
  "primary_color_palette": "[3-5 dominant hex colors with mood: e.g. #D4C17A warm sodium yellow, #98D8C8 mint pool teal]",
  "narrative_anchor": {{
    "object": "[small ordinary object, e.g. 'a red folding umbrella leaning against a pillar']",
    "origin_story": "[one sentence: why it was left here]",
    "final_state": "[one sentence: what it means to see it alone in Cut 10]"
  }},
  "reality_arc": [
    {{
      "stage": 1,
      "stage_name": "GROUNDED_OPEN",
      "zone_name": "[specific room or outdoor space — NOT a hallway or corridor]",
      "zone_description": "[60-word: exact space, architecture, materials, lighting color temp and fixture type]",
      "unreality_element": "none",
      "anchor_state": "[exact position and appearance of anchor in this cut]",
      "story_beat": "[what this cut evokes — 1 sentence, emotional not plot]",
      "visible_next_zone": "[architectural or spatial feature that connects to stage 2]"
    }},
    {{
      "stage": 2, "stage_name": "GROUNDED_VAST",
      "zone_name": "[NOT hallway/corridor]", "zone_description": "[60 words]",
      "unreality_element": "one dimension permanently too large — built this way",
      "anchor_state": "[anchor farther than expected — space always was this large]",
      "story_beat": "[1 sentence, emotional]", "visible_next_zone": "[connection to stage 3]"
    }},
    {{
      "stage": 3, "stage_name": "SUBTLE_HINT",
      "zone_name": "[NOT hallway/corridor]", "zone_description": "[60 words]",
      "unreality_element": "[one impossible architectural detail — permanent, static, built in]",
      "anchor_state": "[shadow or reflection subtly wrong — always been this way]",
      "story_beat": "[1 sentence, emotional]", "visible_next_zone": "[connection to stage 4]"
    }},
    {{
      "stage": 4, "stage_name": "SUBTLE_CONFIRM",
      "zone_name": "[NOT hallway/corridor]", "zone_description": "[60 words]",
      "unreality_element": "[stage 3 anomaly now foreground; second impossible detail in far distance]",
      "anchor_state": "[anchor in impossible position — was always here]",
      "story_beat": "[1 sentence, emotional]", "visible_next_zone": "[connection to stage 5]"
    }},
    {{
      "stage": 5, "stage_name": "UNCANNY_SINGLE",
      "zone_name": "[NOT hallway/corridor]", "zone_description": "[60 words]",
      "unreality_element": "[one clear impossible architecture — beautiful, calm, always existed]",
      "anchor_state": "[anchor duplicated — two identical copies, equidistant, both real]",
      "story_beat": "[1 sentence, emotional]", "visible_next_zone": "[connection to stage 6]"
    }},
    {{
      "stage": 6, "stage_name": "UNCANNY_SPREAD",
      "zone_name": "[NOT hallway/corridor]", "zone_description": "[60 words]",
      "unreality_element": "[two simultaneous impossible features; shadows permanently conflicting]",
      "anchor_state": "[anchor multiplied to 3-4 copies, static pattern]",
      "story_beat": "[1 sentence, emotional]", "visible_next_zone": "[connection to stage 7]"
    }},
    {{
      "stage": 7, "stage_name": "SURREAL_FOLD",
      "zone_name": "[NOT hallway/corridor]", "zone_description": "[60 words]",
      "unreality_element": "[Escher-like topology — far end connects to entrance, visible in single wide shot]",
      "anchor_state": "[anchor tiled across all surfaces — floor wall ceiling — always been this way]",
      "story_beat": "[1 sentence, emotional]", "visible_next_zone": "[connection to stage 8]"
    }},
    {{
      "stage": 8, "stage_name": "SURREAL_DEEP",
      "zone_name": "[NOT hallway/corridor]", "zone_description": "[60 words]",
      "unreality_element": "[multiple physical laws permanently violated in separate static zones of same frame]",
      "anchor_state": "[anchor has become part of the architecture itself]",
      "story_beat": "[1 sentence, emotional]", "visible_next_zone": "[connection to stage 9]"
    }},
    {{
      "stage": 9, "stage_name": "VOID_APPROACH",
      "zone_name": "[NOT hallway/corridor]", "zone_description": "[60 words]",
      "unreality_element": "[space permanently extends beyond any physical boundary — always been infinite]",
      "anchor_state": "[anchor alone, tiny, centered in infinite middle distance]",
      "story_beat": "[1 sentence, emotional]", "visible_next_zone": "[connection to stage 10]"
    }},
    {{
      "stage": 10, "stage_name": "VOID_COMPLETE",
      "zone_name": "[NOT hallway/corridor]", "zone_description": "[60 words]",
      "unreality_element": "[total static dissolution — space exists outside physics, always was this way]",
      "anchor_state": "[anchor alone in infinite space, unchanged from Cut 1]",
      "story_beat": "[the final emotional revelation — 1 sentence]",
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

            # hallway/corridor 자동 교체 (재시도 대신 즉시 수정)
            BANNED = ('hallway', 'corridor', 'hall way', 'passageway')
            alt_idx = 0
            for stage in arc:
                zn = stage.get('zone_name', '')
                zd = stage.get('zone_description', '')
                if any(w in zn.lower() or w in zd.lower() for w in BANNED):
                    new_name = ZONE_ALTS[alt_idx % len(ZONE_ALTS)]
                    alt_idx += 1
                    stage['zone_name'] = new_name
                    stage['zone_description'] = re.sub(
                        r'\b(hallway|corridor|hall way|passageway)s?\b',
                        new_name, zd, flags=re.IGNORECASE
                    )
                    print(f"  🔧 Stage {stage.get('stage')} 자동 교체 → {new_name}")

            # aesthetic_type 정규화 + weirdcore 추가
            raw = sc.get('aesthetic_type', '').lower()
            if 'dreamcore' in raw:       sc['aesthetic_type'] = 'dreamcore'
            elif 'weirdcore' in raw:     sc['aesthetic_type'] = 'weirdcore'
            elif 'backroom' in raw:      sc['aesthetic_type'] = 'backrooms'
            else:                        sc['aesthetic_type'] = 'liminal_space'

            anchor = sc.get('narrative_anchor', {})
            print(f"✅ '{sc.get('series_title')}' | {sc['aesthetic_type']} | {len(arc)}단계")
            print(f"   {sc.get('narrative_premise', '')[:150]}")
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

    neg_prompt = (NEGATIVE_PROMPT_WEIRDCORE
                  if aesthetic_type == 'weirdcore'
                  else NEGATIVE_PROMPT_NON_WEIRD)

    if prev_cuts_summary:
        prev_last = prev_cuts_summary[-1]
        older_cuts = prev_cuts_summary[:-1]

        older_block = ""
        if older_cuts:
            older_lines = "\n".join(
                f"  Cut {c['stage']} [{c['stage_name']}] {c['zone_name']}: "
                f"{c['anchor_state']} | {c['story_beat']}"
                for c in older_cuts
            )
            older_block = f"EARLIER CUTS:\n{older_lines}\n\n"

        continuity_block = (
            f"{older_block}"
            f"PREVIOUS CUT — Cut {prev_last['stage']} [{prev_last['stage_name']}] "
            f"in '{prev_last['zone_name']}' FULL DESCRIPTION:\n"
            f"{prev_last['description']}\n\n"
            f"ANCHOR PREVIOUS CUT: {prev_last['anchor_state']}\n\n"
            f"THIS CUT MUST:\n"
            f"1. Open already positioned in the space visible at the end of Cut {prev_last['stage']}: "
            f"'{visible_next}'\n"
            f"2. First architectural element named = that connecting feature.\n"
            f"3. Feels like one continuous walk deeper into the same location.\n"
            f"4. Anchor in exact state: {anchor_state}"
        )
        desc_rule = (
            f"Open with the connecting feature from Cut {prev_last['stage']} "
            f"now in the foreground. Then: describe '{zone_name}'."
        )
    else:
        continuity_block = (
            "OPENING SHOT (Cut 1). "
            "Establish: exact space, full scale, color palette, VHS texture quality, "
            "and the anchor's precise mundane position. "
            "This is the most ordinary this place will ever look. "
            "It should feel like a found VHS tape of somewhere you have never been "
            "but somehow remember."
        )
        desc_rule = (
            "Establish: exact space type, dominant colors and materials, "
            "specific lighting (color temp + fixture type), VHS texture quality, "
            "and the anchor's precise mundane position."
        )

    if unreality and unreality.lower() != 'none':
        unreality_block = (
            f"PERMANENT SPATIAL ANOMALY (Stage {stage_num}: {stage_name}):\n"
            f"{unreality}\n\n"
            f"This was BUILT this way or has ALWAYS existed in this state. "
            f"Nothing transforms. Nothing moves. The camera is fixed. The space is fixed. "
            f"The anomaly is an architectural fact."
        )
    else:
        unreality_block = (
            "NO ANOMALY — Stage 1: completely real.\n"
            "Zero impossible features. Normal architecture. "
            "Eeriness from scale, emptiness, and VHS analog texture only."
        )

    video_unreality = unreality if unreality.lower() != 'none' else 'completely real static empty space'

    prompt = f"""You are creating Cut {stage_num}/10 for the @derealisat aesthetic series.

The series embodies DEREALIZATION — familiar spaces that feel like dreams or memories you never had.
Every image is a perfectly still, extreme wide shot with VHS analog texture.
The emotional target: ANEMOIA + the warm unsettling feeling of an empty space that should be full.

═══ SERIES ═══
PREMISE: {premise}
AESTHETIC: {aesthetic_type.upper()} — {aesthetic_guide}
PALETTE: {color_palette}
ANCHOR: {anchor_obj} (left here because: {anchor_origin} | in Cut 10: {anchor_final})

═══ THIS CUT ═══
ZONE: {zone_name}
ZONE DETAILS: {zone_desc}
ANCHOR THIS CUT: {anchor_state}
EMOTIONAL BEAT: {story_beat}
NEXT ZONE VISIBLE: {visible_next}

═══ CONTINUITY ═══
{continuity_block}

═══ ANOMALY ═══
{unreality_block}

═══ RULES ═══
1. STATIC TRIPOD. EXTREME WIDE SHOT. Zero movement.
2. Space is STATIC — nothing transforms or changes. Anomalies are permanent architectural facts.
3. INTACT, CLEAN, FUNCTIONING. Zero decay or ruin.
4. No people. No text. No hallways. No corridors.
5. VHS analog texture must be felt in the description — grain, faded colors, analog warmth.
6. Tone: COMFORT + EERIE simultaneously. Dreamlike calm. Anemoia.
7. Anchor: {anchor_state}

Output ONLY valid JSON:
{{
  "title": "[cryptic minimal title for this cut — 1-5 words maximum, enigmatic, lowercase preferred]",
  "description": "[1000-1200 character English narrative. {desc_rule} Include: exact architecture from static extreme distance, specific lighting color temp and quality, VHS grain and analog texture quality, the anchor's current position and state, the permanent anomaly as calm architectural fact (if any), one sensory detail threading back to the previous cut. Tone: anemoia, derealization, comfort-eerie, dreamlike calm.]",
  "video_prompt": "[Detailed text-to-image prompt: static extreme wide shot, {aesthetic_type} aesthetic VHS analog, {color_palette}, intact clean empty {zone_name}, {video_unreality}, {anchor_obj} visible, VHS grain scan lines faded colors analog noise, no people no text NOT ruined no hallway no corridor, perfectly still, {aesthetic_type} nostalgia eerie comfort]"
}}"""

    content = call_openrouter(
        [{"role": "user", "content": prompt}],
        free_models, require_json=True, max_tokens=2500
    )
    if not content:
        return None
    try:
        result = json.loads(content)
        result['stage']        = stage_num
        result['stage_name']   = stage_name
        result['zone_name']    = zone_name
        result['anchor_state'] = anchor_state
        result['story_beat']   = story_beat
        return result
    except json.JSONDecodeError as e:
        print(f"  ❌ Cut {stage_num} JSON 파싱 오류: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════
# 이미지 생성
# ═══════════════════════════════════════════════════════════════════

def build_image_prompt(raw_prompt, aesthetic_type, color_palette):
    style = IMAGE_STYLE_SUFFIX.get(aesthetic_type, IMAGE_STYLE_SUFFIX['liminal_space'])
    clean = re.sub(r'\b(hallway|corridor|hall way)\b', '', raw_prompt, flags=re.IGNORECASE)
    return f"{clean.strip()}, {style}, dominant colors: {color_palette}"


def generate_image(prompt, index, aesthetic_type='liminal_space', color_palette=''):
    if not prompt or not isinstance(prompt, str):
        prompt = "A perfectly static extreme wide VHS analog shot of a vast empty space, anemoia dreamcore."

    neg = (NEGATIVE_PROMPT_WEIRDCORE if aesthetic_type == 'weirdcore'
           else NEGATIVE_PROMPT_NON_WEIRD)
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
                    "negative_prompt": neg,
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
                    "negative_prompt": neg,
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
                    print(f"  ⚠️ 429. {wait}초 대기...")
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
        print(f"  🔄 {cfg['path']} 포기.")
    return None


# ═══════════════════════════════════════════════════════════════════
# 텔레그램 전송 — @derealisat 미학 반영: 최소화, 신비주의
# ═══════════════════════════════════════════════════════════════════

def send_to_telegram(story_meta, title, desc, img_path, cut_num=None, total=10):
    # 최소화된 캡션: 채널 컨셉에 맞게 정보 노출 최소화
    caption_lines = [f"{story_meta['series_title']}"]
    if cut_num:
        caption_lines.append(f"░{'█' * cut_num}{'░' * (total - cut_num)}░  {cut_num}/{total}")
    caption_lines.append(f"\n{title}")
    short_caption = "\n".join(caption_lines)

    # 설명 텍스트: 분위기 중심, 메타정보 최소화
    full_text = desc

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
                data={"chat_id": TG_CHAT_ID, "caption": short_caption},
                files={"photo": photo}
            )
        if ok:
            _send(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                data={"chat_id": TG_CHAT_ID, "text": full_text}
            )
    else:
        _send(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data={"chat_id": TG_CHAT_ID, "text": f"{short_caption}\n\n{full_text}"}
        )

    print(f"  ✅ 전송 완료")


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

        # ── Phase 0: 웹서치 ───────────────────────────────────────────
        web_space_refs = search_dreamcore_web(free_models)

        # ── Phase 1: 스토리 컨셉 + 10단계 아크 ───────────────────────
        story = generate_story_concept(free_models, web_space_refs=web_space_refs, max_retries=3)
        if not story or not story.get('reality_arc'):
            print("❌ 스토리 컨셉 생성 실패. 종료.")
            exit(1)

        anchor = story.get('narrative_anchor', {})
        story_meta = {
            "series_title":   story.get('series_title', '░░░'),
            "culture":        story.get('chosen_culture', ''),
            "location":       story.get('chosen_location', ''),
            "premise":        story.get('narrative_premise', ''),
            "aesthetic_type": story.get('aesthetic_type', 'liminal_space'),
            "color_palette":  story.get('primary_color_palette', '')
        }
        reality_arc = story.get('reality_arc', [])

        print(f"\n░ '{story_meta['series_title']}'")
        print(f"  {story_meta['aesthetic_type']} | {len(reality_arc)}컷")
        print(f"  앵커: {anchor.get('object', 'N/A')}\n")

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
            print(f"   {anchor_st[:80]}...")

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
                print(f"  ⚠️ 실패. 체인 유지.")
            time.sleep(2)

        # ── Phase 3: 이미지 생성 + 전송 ──────────────────────────────
        total_scenes = len(scenes)
        print(f"\n🖼️ 이미지 생성 + 전송 ({total_scenes}컷)\n")
        for i, scene in enumerate(scenes):
            cut_num = scene.get('stage', i + 1)
            print(f"── {i + 1}/{total_scenes} (Cut {cut_num}) ──")
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

        print(f"\n🎉 완료. {total_scenes}/10컷.")

    except Exception as e:
        print(f"💥 에러: {e}")
        raise

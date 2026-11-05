"""
Copywriter Agent (AI 마케팅 & 바이럴 카피라이팅 모듈 - Justice Buys 벤치마킹 에디션)
- Google Antigravity SDK (gemini-3.5-flash-lite) 기반 자율 카피라이터
- 글로벌 1위 제휴 크리에이터(Justice Buys / Mavigadget) 흥행 공식 탑재:
  1. 0.5초 시선 강탈 훅 (인사말 완전 삭제, 즉각적 문제 제기/호기심 유발)
  2. #상품번호(예: "Link #2001 is in my bio!") 나레이션 및 캡션 CTA 자동 결합
  3. 1상품 3훅(Multi-Hook) A/B 테스트 변형 대본 자동 생성 모드 지원:
     - Angle A (problem_solver): 일상적 짜증/문제 해결 앵글
     - Angle B (curiosity_shock): 시각적 충격/호기심 갭 앵글
     - Angle C (value_flex): 가성비/비교 우위 강조 앵글
  4. FTC 법적 고지(#ad, #commissionsearned) 강제 삽입 및 무중단 Graceful Fallback
"""

import asyncio
import json
import os
import random
import re
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Windows 콘솔 인코딩 방어
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# .env 파일 명시적 탐색 로드
for env_path in [Path(".env"), Path("C:/project/AgentCorp/.env")]:
    if env_path.exists():
        load_dotenv(env_path)
        break


def extract_item_code(product_id: str) -> str:
    """product_id(예: 'ali_2001')에서 '#2001' 형태의 고유 번호를 추출합니다."""
    digits = "".join(ch for ch in str(product_id) if ch.isdigit())
    return f"#{digits}" if digits else "#001"


class ScriptOutput(BaseModel):
    product_id: str
    item_code: str = "#001"
    hook_angle: str = "problem_solver"
    variant_id: str = "A"
    product_title: str
    hook: str
    body: str
    cta: str
    full_narration: str
    caption: str
    hashtags: List[str]
    generation_mode: str = "ai_agent"  # "ai_agent" or "template_fallback"


class CopywriterAgent:
    # 1상품 3훅(Multi-Hook) A/B 테스트 앵글 정의
    MULTI_HOOK_ANGLES = [
        {
            "variant_id": "A",
            "angle_key": "problem_solver",
            "angle_name": "Problem-Solver Hook (일상 불편함 저격)",
            "instruction": "Start by calling out an annoying everyday problem that this gadget solves in 2 seconds.",
            "fallback_hooks": [
                "If you hate wasting time on everyday messes, this genius gadget is a total game changer.",
                "Stop doing this the hard way when this tiny gadget fixes it in two seconds!",
                "I was today years old when I found out this annoying problem has a ten-dollar fix."
            ]
        },
        {
            "variant_id": "B",
            "angle_key": "curiosity_shock",
            "angle_name": "Curiosity-Shock Hook (시각적 쾌감·호기심 자극)",
            "instruction": "Start with a bizarre, shocking, or deeply satisfying visual statement that forces viewers to keep watching.",
            "fallback_hooks": [
                "This is the weirdest viral gadget I've ever tested, and it actually works!",
                "Wait until you see what happens when I turn this viral gadget on...",
                "Three million people watched this gadget in action for one insanely satisfying reason."
            ]
        },
        {
            "variant_id": "C",
            "angle_key": "value_flex",
            "angle_name": "Value-Flex Hook (극강의 가성비·비교 우위)",
            "instruction": "Highlight the insane price-to-performance ratio—how a cheap gadget outperforms expensive alternatives.",
            "fallback_hooks": [
                "Why pay a hundred bucks when this ${price} gadget does the exact same job better?",
                "This ${price} viral find just replaced three expensive tools in my house!",
                "Best under-${price_ceil} gadget find of the year, hands down."
            ]
        }
    ]

    def __init__(self, model_name: str = "gemini-3.5-flash-lite"):
        self.model_name = model_name
        self.api_key = os.environ.get("GEMINI_API_KEY")

        # #상품번호 결합형 바이오 링크 유도 CTA 풀 (Justice Buys 스타일)
        self.cta_pool = [
            "Link {item_code} is in my bio! Search {item_code} to grab yours before it sells out!",
            "Link {item_code} is waiting in my bio—just type {item_code} in the search bar!",
            "I dropped Link {item_code} right in my bio for you guys!",
            "Tap my bio link and search {item_code} to check today's discount!"
        ]

        # 해시태그 풀
        self.hashtag_master_pool = [
            "#aliexpressfinds", "#coolgadgets", "#amazonfinds", "#lifehacks",
            "#smartgadgets", "#techfinds", "#viralproducts", "#gadgetlover",
            "#uniquegadgets", "#musthaves", "#tiktokmademebuyit"
        ]

        # FTC 필수 법적 고지 태그
        self.mandatory_compliance_tags = ["#ad", "#commissionsearned"]

    def _fallback_generate(
        self,
        product: Dict[str, Any],
        angle_spec: Optional[Dict[str, Any]] = None
    ) -> ScriptOutput:
        """API 오류나 키 부재 시 안전하게 구동되는 룰 기반 템플릿 폴백 (#상품번호 및 3훅 앵글 지원)"""
        prod_id = product.get("id", "ali_001")
        item_code = extract_item_code(prod_id)
        title = product.get("title", "Viral Gadget")
        price = float(product.get("price_usd", 15.0))

        if angle_spec is None:
            angle_spec = self.MULTI_HOOK_ANGLES[0]

        variant_id = angle_spec["variant_id"]
        angle_key = angle_spec["angle_key"]
        hook_templates = angle_spec["fallback_hooks"]

        selected_hook = random.choice(hook_templates).format(
            price=int(price),
            price_ceil=int(price) + 5,
            rand_num=random.randint(10, 99)
        )

        body = (
            f"This is the {title}. "
            f"It's only {price:.2f} dollars right now, and over {int(product.get('orders_count', 2000)):,} people rated it {product.get('rating', 4.8)} stars. "
            f"Watch how effortlessly it works right out of the box."
        )

        selected_cta = random.choice(self.cta_pool).format(item_code=item_code)
        full_narration = f"{selected_hook} {body} {selected_cta}"
        random_tags = random.sample(self.hashtag_master_pool, k=4)
        final_tags = random_tags + self.mandatory_compliance_tags

        caption = (
            f"{selected_hook}\n\n"
            f"🔎 Search Code: {item_code} in my bio link!\n"
            f"✨ Product: {title}\n"
            f"🔗 Link {item_code} is in my bio to shop!\n\n"
            f"{' '.join(final_tags)}"
        )

        return ScriptOutput(
            product_id=prod_id,
            item_code=item_code,
            hook_angle=angle_key,
            variant_id=variant_id,
            product_title=title,
            hook=selected_hook,
            body=body,
            cta=selected_cta,
            full_narration=full_narration,
            caption=caption,
            hashtags=final_tags,
            generation_mode="template_fallback"
        )

    async def _generate_with_agent_async(
        self,
        product: Dict[str, Any],
        angle_spec: Optional[Dict[str, Any]] = None
    ) -> ScriptOutput:
        """Google Antigravity SDK를 사용하여 #상품번호 CTA 및 앵글별 바이럴 영문 대본 생성"""
        from google.antigravity import Agent, LocalAgentConfig
        from google.antigravity.hooks import policy

        prod_id = product.get("id", "ali_001")
        item_code = extract_item_code(prod_id)
        title = product.get("title", "Viral Gadget")
        price = float(product.get("price_usd", 15.0))
        category = product.get("category", "gadgets")
        reasons = ", ".join(product.get("viral_reasons", []))

        if angle_spec is None:
            angle_spec = self.MULTI_HOOK_ANGLES[0]

        variant_id = angle_spec["variant_id"]
        angle_key = angle_spec["angle_key"]
        angle_instruction = angle_spec["instruction"]

        prompt = f"""
You are the Lead Viral Short-Form Video Copywriter benchmarking Justice Buys (#1 global gadget affiliate creator).
Write a zero-fluff, ultra-fast-paced English spoken script and social caption for the following product:

Product ID Code: {item_code}
Product Name: {title}
Price: ${price:.2f} USD
Category: {category}
Selling Points: {reasons}
Hook Angle Strategy ({angle_key}): {angle_instruction}

Format Requirements:
1. "hook": A punchy first 3-second hook following the Hook Angle Strategy ({angle_key}). Zero greetings, start in media res (1 sentence, 8-14 words).
2. "body": 2 snappy, conversational sentences showing utility and why people love it (no robotic spec listing).
3. "cta": MUST explicitly tell the viewer: "Link {item_code} is in my bio! Search {item_code} to grab yours before it sells out!" (1 sentence).
4. "full_narration": Complete spoken script combining hook, body, and cta (45-60 words total, must include "Link {item_code} is in my bio").
5. "caption": Catchy social caption featuring "🔎 Link {item_code} is in my bio!", product name, and 4-6 viral hashtags plus mandatory #ad #commissionsearned.
6. "hashtags": Array of strings including trending tags and #ad, #commissionsearned.

Respond ONLY with a valid JSON object matching this schema:
{{
  "hook": "string",
  "body": "string",
  "cta": "string",
  "full_narration": "string",
  "caption": "string",
  "hashtags": ["string"]
}}
"""
        config = LocalAgentConfig(
            model=self.model_name,
            policies=[policy.deny_all()]
        )
        async with Agent(config) as agent:
            response = await agent.chat(prompt)
            raw_text = await response.text()

        clean_json = raw_text.strip()
        if clean_json.startswith("```"):
            clean_json = re.sub(r"^```(?:json)?\n?", "", clean_json)
            clean_json = re.sub(r"\n?```$", "", clean_json)

        data = json.loads(clean_json)

        # #상품번호 CTA 강제 보장
        cta_text = data.get("cta", "").strip()
        if item_code not in cta_text:
            cta_text = f"Link {item_code} is in my bio! Search {item_code} to grab yours before it sells out!"

        full_narration = data.get("full_narration", "").strip()
        if item_code not in full_narration:
            full_narration = f"{data.get('hook', '').strip()} {data.get('body', '').strip()} {cta_text}"

        caption_text = data.get("caption", "").strip()
        if item_code not in caption_text:
            caption_text = f"🔎 Link {item_code} is in my bio!\n{caption_text}"

        tags = data.get("hashtags", [])
        for req_tag in self.mandatory_compliance_tags:
            if req_tag not in tags:
                tags.append(req_tag)

        return ScriptOutput(
            product_id=prod_id,
            item_code=item_code,
            hook_angle=angle_key,
            variant_id=variant_id,
            product_title=title,
            hook=data.get("hook", "").strip(),
            body=data.get("body", "").strip(),
            cta=cta_text,
            full_narration=full_narration,
            caption=caption_text,
            hashtags=tags,
            generation_mode="ai_agent"
        )

    def generate_script(
        self,
        product: Dict[str, Any],
        angle_spec: Optional[Dict[str, Any]] = None
    ) -> ScriptOutput:
        """단일 훅 대본 생성 (#상품번호 자동 포함)"""
        if not self.api_key:
            return self._fallback_generate(product, angle_spec=angle_spec)

        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(self._generate_with_agent_async(product, angle_spec=angle_spec))
            else:
                return asyncio.run(self._generate_with_agent_async(product, angle_spec=angle_spec))
        except Exception as e:
            print(f"[CopywriterAgent] Agent SDK 실행 중 예외 발생, 템플릿 폴백으로 전환: {e}")
            return self._fallback_generate(product, angle_spec=angle_spec)

    def generate_multi_hook_scripts(self, product: Dict[str, Any]) -> List[ScriptOutput]:
        """
        [글로벌 1위 벤치마킹: 1상품 3훅 A/B 테스트 생성 모드]
        동일한 1개 상품에 대해 서로 다른 3가지 바이럴 훅 각도(Problem / Curiosity / Value)의
        스크립트 패키지 3종(Variant A, B, C)을 생성하여 반환합니다.
        """
        variants: List[ScriptOutput] = []
        for angle_spec in self.MULTI_HOOK_ANGLES:
            script = self.generate_script(product, angle_spec=angle_spec)
            variants.append(script)
        return variants

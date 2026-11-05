"""
AliExpress Sourcing Agent (상품 소싱 & AI 바이럴/컴플라이언스 분석 모듈)
- Google Antigravity SDK (gemini-3.5-flash-lite) 연동
- 최신 멀티에이전트 이커머스 소싱 파이프라인 레퍼런스 준수:
  1. 1차 정량적 지표 필터링 (가격, 평점, 판매량, 비디오 소스 유무)
  2. 2차 AI 심층 추론 (바이럴 시각 요소 분석, 저작권/상표권/위험물 계정 정지 리스크 사전 검증)
  3. 숏폼 제작팀(Creative Team)을 위한 타겟 오디언스 및 촬영 훅 앵글 자동 제안
  4. 무중단 폴백 아키텍처 (Graceful Fallback)
"""

import asyncio
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
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

import config


class AIAnalysisInsight(BaseModel):
    viral_factor: str = Field(description="숏폼에서 시청자를 사로잡는 핵심 시각/기능적 포인트")
    anti_ban_risk: str = Field(default="LOW", description="계정 정지 및 정책 위반 위험도 (LOW, MEDIUM, HIGH)")
    compliance_notes: str = Field(description="상표권/안전성 관련 주의사항 및 컴플라이언스 메모")
    recommended_hook_angle: str = Field(description="제작팀에게 권장하는 3초 훅 연출 방식")
    target_audience: str = Field(description="타겟 시청자 및 구매자 페르소나")
    analysis_mode: str = "ai_agent"  # "ai_agent" or "rule_fallback"


class ProductItem(BaseModel):
    id: str
    title: str
    original_url: str
    affiliate_url: Optional[str] = None
    price_usd: float
    rating: float = 0.0
    orders_count: int = 0
    images: List[str] = Field(default_factory=list)
    video_url: Optional[str] = None
    category: str = "gadgets"
    viral_score: float = 0.0
    viral_reasons: List[str] = Field(default_factory=list)
    ai_insight: Optional[AIAnalysisInsight] = None


class AliExpressSourcingAgent:
    def __init__(self, tracking_id: str = config.ALIEXPRESS_TRACKING_ID, model_name: str = "gemini-3.5-flash-lite"):
        self.tracking_id = tracking_id
        self.output_file = config.DATA_DIR / "sourced_products.json"
        self.model_name = model_name
        self.api_key = os.environ.get("GEMINI_API_KEY")

    def calculate_viral_score(self, item: ProductItem) -> tuple[float, list[str]]:
        """
        글로벌 숏폼 바이럴 가능성 평가 (100점 만점)
        1. 충동구매 가격대 ($5 ~ $35): 시청자가 링크 클릭 후 바로 결제하기 가장 좋은 가격대
        2. 높은 평점 (4.5 이상): 반품/부정적 댓글 방지
        3. 검증된 판매량 (주문 300건 이상): 시장성 검증 완료
        4. 시연 비디오 보유 여부: 쇼츠/릴스 제작 필수 요소
        """
        score = 0.0
        reasons = []

        # 1. 가격 분석 (최대 30점)
        if config.VIRAL_PRICE_MIN <= item.price_usd <= config.VIRAL_PRICE_MAX:
            score += 30.0
            reasons.append(f"충동구매 최적 가격대 (${item.price_usd:.2f})")
        elif item.price_usd < config.VIRAL_PRICE_MIN:
            score += 15.0
            reasons.append(f"초저가 미끼 상품 (${item.price_usd:.2f})")
        else:
            score += 10.0

        # 2. 평점 분석 (최대 25점)
        if item.rating >= 4.8:
            score += 25.0
            reasons.append(f"최상위 고객 만족도 (★{item.rating:.1f})")
        elif item.rating >= 4.5:
            score += 20.0
            reasons.append(f"안정적인 평점 (★{item.rating:.1f})")
        elif item.rating >= 4.0:
            score += 10.0

        # 3. 판매량/주문수 (최대 25점)
        if item.orders_count >= 1000:
            score += 25.0
            reasons.append(f"검증된 메가 히트 상품 ({item.orders_count:,}건 판매)")
        elif item.orders_count >= config.MIN_ORDERS:
            score += 15.0
            reasons.append(f"우수한 판매량 ({item.orders_count:,}건 판매)")
        else:
            score += 5.0

        # 4. 영상 소스 유무 (최대 20점 - 숏폼 제작에 결정적)
        if item.video_url:
            score += 20.0
            reasons.append("고화질 시연 데모 비디오 확보")
        elif len(item.images) >= 3:
            score += 10.0
            reasons.append("다각도 제품 이미지 3장 이상 확보")

        return round(score, 1), reasons

    def generate_affiliate_link(self, product_url: str) -> str:
        """알리익스프레스 제휴 트래킹 파라미터 결합 (간이 링크)"""
        separator = "&" if "?" in product_url else "?"
        return f"{product_url}{separator}aff_fcid={self.tracking_id}"

    def _fallback_ai_insight(self, item: ProductItem) -> AIAnalysisInsight:
        """API 부재 또는 오류 시 동작하는 룰 기반 분석 폴백"""
        return AIAnalysisInsight(
            viral_factor=f"Strong problem-solving appeal in {item.category} category under ${item.price_usd:.2f}",
            anti_ban_risk="LOW",
            compliance_notes="Standard consumer accessory. Ensure FTC #ad disclosures on video and description.",
            recommended_hook_angle="Immediate demonstration of the primary feature in the first 2 seconds.",
            target_audience="Young adults, gadget enthusiasts, budget shoppers",
            analysis_mode="rule_fallback"
        )

    async def _analyze_with_agent_async(self, item: ProductItem) -> AIAnalysisInsight:
        """Google Antigravity SDK를 활용한 AI 바이럴 & 컴플라이언스 심층 분석"""
        from google.antigravity import Agent, LocalAgentConfig
        from google.antigravity.hooks import policy

        prompt = f"""
You are the Chief Product Sourcing & Risk Analyst for a global social commerce network.
Analyze the following AliExpress product candidate for TikTok/Shorts viral marketing:

Title: {item.title}
Category: {item.category}
Price: ${item.price_usd:.2f} USD
Rating: {item.rating} / 5.0
Orders: {item.orders_count}
Has Demo Video: {bool(item.video_url)}

Evaluate 5 key aspects:
1. "viral_factor": What specific visual or practical gimmick makes this blow up on 숏폼 (1-2 sentences).
2. "anti_ban_risk": "LOW", "MEDIUM", or "HIGH". Check for trademark infringement (e.g. fake Apple/Nike/Lego), medical claims, dangerous batteries, or weapons.
3. "compliance_notes": Safety/legal precautions for advertising this item.
4. "recommended_hook_angle": Direct advice to the video creator on how to shoot the first 3-second hook.
5. "target_audience": Primary demographic and buyer intent.

Respond ONLY with valid JSON:
{{
  "viral_factor": "string",
  "anti_ban_risk": "LOW" | "MEDIUM" | "HIGH",
  "compliance_notes": "string",
  "recommended_hook_angle": "string",
  "target_audience": "string"
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
        return AIAnalysisInsight(
            viral_factor=data.get("viral_factor", "").strip(),
            anti_ban_risk=data.get("anti_ban_risk", "LOW").strip(),
            compliance_notes=data.get("compliance_notes", "").strip(),
            recommended_hook_angle=data.get("recommended_hook_angle", "").strip(),
            target_audience=data.get("target_audience", "").strip(),
            analysis_mode="ai_agent"
        )

    def analyze_item_insight(self, item: ProductItem) -> AIAnalysisInsight:
        """동기 인터페이스로 AI 분석 수행 (Graceful Fallback 지원)"""
        if not self.api_key:
            return self._fallback_ai_insight(item)

        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(self._analyze_with_agent_async(item))
            else:
                return asyncio.run(self._analyze_with_agent_async(item))
        except Exception as e:
            print(f"[AliExpressSourcingAgent] AI 분석 중 예외 발생, 기본 인사이트로 폴백: {e}")
            return self._fallback_ai_insight(item)

    def evaluate_and_save(self, items: List[ProductItem], run_ai_analysis: bool = True) -> List[ProductItem]:
        """점수를 산출하고 고득점 상품(65점 이상)을 선별 및 AI 분석하여 저장"""
        qualified = []
        for item in items:
            score, reasons = self.calculate_viral_score(item)
            item.viral_score = score
            item.viral_reasons = reasons
            item.affiliate_url = self.generate_affiliate_link(item.original_url)

            if score >= 65.0:  # 65점 이상만 합격
                if run_ai_analysis:
                    print(f"🔍 [Sourcing AI Agent] '{item.title[:40]}...' 심층 분석 중...")
                    item.ai_insight = self.analyze_item_insight(item)
                qualified.append(item)

        # 바이럴 점수 높은 순 정렬
        qualified.sort(key=lambda x: x.viral_score, reverse=True)

        # JSON 저장
        existing = []
        if self.output_file.exists():
            try:
                with open(self.output_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = []

        combined = {item.id: item.model_dump() for item in qualified}
        # 이전 데이터 유지 및 병합
        for old in existing:
            if old["id"] not in combined:
                combined[old["id"]] = old

        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(list(combined.values()), f, ensure_ascii=False, indent=2)

        return qualified


if __name__ == "__main__":
    agent = AliExpressSourcingAgent(tracking_id="bio-search")
    sample_products = [
        ProductItem(
            id="ali_1001",
            title="Mini Portable Electric Air Duster & Vacuum 2-in-1 for Keyboard & Car",
            original_url="https://aliexpress.com/item/100500123456.html",
            price_usd=16.80,
            rating=4.8,
            orders_count=3420,
            images=[
                "https://ae-pic-a1.aliexpress-media.com/sample1.jpg",
                "https://ae-pic-a1.aliexpress-media.com/sample2.jpg"
            ],
            video_url="https://ae-video.aliexpress-media.com/demo.mp4",
            category="tech_gadgets"
        ),
        ProductItem(
            id="ali_1002",
            title="Automatic Stirring Magnetic Mug for Coffee & Milk",
            original_url="https://aliexpress.com/item/100500987654.html",
            price_usd=9.99,
            rating=4.6,
            orders_count=1850,
            images=["https://ae-pic-a1.aliexpress-media.com/mug1.jpg"],
            video_url="https://ae-video.aliexpress-media.com/mug_demo.mp4",
            category="kitchen_gadgets"
        )
    ]

    results = agent.evaluate_and_save(sample_products)
    print(f"\n=== [Agent 1] 소싱 및 AI 심층 분석 완료: {len(results)}개 상품 ===")
    for item in results:
        print(f"[{item.viral_score}점] {item.title}")
        print(f"  - AI 분석 모드: {item.ai_insight.analysis_mode if item.ai_insight else 'N/A'}")
        print(f"  - 바이럴 핵심 요인: {item.ai_insight.viral_factor if item.ai_insight else 'N/A'}")
        print(f"  - 계정 정지 위험도: {item.ai_insight.anti_ban_risk if item.ai_insight else 'N/A'}")
        print(f"  - 추천 훅 앵글: {item.ai_insight.recommended_hook_angle if item.ai_insight else 'N/A'}\n")

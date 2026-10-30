"""
AliExpress Sourcing Agent (상품 소싱 & 바이럴 스코어링 모듈)
- 글로벌 숏폼(TikTok/Shorts)에서 터질 가능성이 높은 알리익스프레스 꿀템을 분석하고 선별합니다.
"""

import json
import re
from typing import Optional, List
from pydantic import BaseModel, Field
from pathlib import Path
import config

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

class AliExpressSourcingAgent:
    def __init__(self, tracking_id: str = config.ALIEXPRESS_TRACKING_ID):
        self.tracking_id = tracking_id
        self.output_file = config.DATA_DIR / "sourced_products.json"

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

    def evaluate_and_save(self, items: List[ProductItem]) -> List[ProductItem]:
        """점수를 산출하고 고득점 상품(70점 이상)을 선별하여 저장"""
        qualified = []
        for item in items:
            score, reasons = self.calculate_viral_score(item)
            item.viral_score = score
            item.viral_reasons = reasons
            item.affiliate_url = self.generate_affiliate_link(item.original_url)

            if score >= 65.0:  # 65점 이상만 합격
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
    # 테스트 샘플 실행
    agent = AliExpressSourcingAgent(tracking_id="agentcorp_global_01")
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
        ),
        ProductItem(
            id="ali_1003",
            title="Generic Low Quality Cable",
            original_url="https://aliexpress.com/item/100500111111.html",
            price_usd=1.20,
            rating=3.8,
            orders_count=50,
            images=[],
            video_url=None,
            category="accessories"
        )
    ]

    results = agent.evaluate_and_save(sample_products)
    print(f"=== [Agent 1] 소싱 완료: {len(results)}개 바이럴 상품 선별 ===")
    for item in results:
        print(f"[{item.viral_score}점] {item.title}")
        print(f"  - 가격: ${item.price_usd} | 평점: ★{item.rating} | 판매량: {item.orders_count:,}건")
        print(f"  - 선별 사유: {', '.join(item.viral_reasons)}")
        print(f"  - 제휴 링크: {item.affiliate_url}\n")


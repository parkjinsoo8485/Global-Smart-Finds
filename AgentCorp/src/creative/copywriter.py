"""
Copywriter Agent (마케팅 & 바이럴 카피라이팅 모듈)
- SNS 계정 정지 방지(Anti-Ban) 규칙 준수:
  1. 매번 달라지는 훅(Hook) & 문장 변형 엔진
  2. 랜덤 해시태그 풀(Pool) 조합
  3. FTC 법적 고지(#ad, #commissionsearned) 강제 삽입
  4. Link-in-Bio 유도 CTA 적용
"""

import random
from typing import Dict, Any, List
from pydantic import BaseModel

class ScriptOutput(BaseModel):
    product_id: str
    product_title: str
    hook: str
    body: str
    cta: str
    full_narration: str
    caption: str
    hashtags: List[str]

class CopywriterAgent:
    def __init__(self):
        # 3초 바이럴 훅 (다양한 어조로 준비하여 중복 방지)
        self.hooks_pool = [
            "You won't believe what I just found on AliExpress!",
            "If you hate wasting time, this little gadget is an absolute lifesaver.",
            "Stop scrolling! This might be the most satisfying purchase I've ever made.",
            "AliExpress finds you didn't know you needed, Part {rand_num}!",
            "I honestly didn't expect this cheap gadget to work this well...",
            "Why is nobody talking about this insane viral gadget yet?",
            "This $ {price} gadget replaced three things on my desk!"
        ]

        # 콜 투 액션 (바이오 링크 유도)
        self.cta_pool = [
            "Check the link in my bio to grab yours before it sells out!",
            "Link is waiting in my bio if you want one!",
            "I dropped the direct link in my bio for you guys!",
            "Tap the link in bio to check current discount prices!"
        ]

        # 해시태그 풀 (스팸 탐지 방지를 위해 매번 4~6개 랜덤 추출)
        self.hashtag_master_pool = [
            "#aliexpressfinds", "#coolgadgets", "#amazonfinds", "#lifehacks",
            "#smartgadgets", "#techfinds", "#viralproducts", "#gadgetlover",
            "#uniquegadgets", "#musthaves", "#tiktokmademebuyit"
        ]

        # FTC 필수 법적 고지 태그
        self.mandatory_compliance_tags = ["#ad", "#commissionsearned"]

    def generate_script(self, product: Dict[str, Any]) -> ScriptOutput:
        """소싱된 제품 데이터를 바탕으로 계정 안전 규정을 준수한 영문 대본 및 캡션 생성"""
        title = product.get("title", "Viral Gadget")
        price = product.get("price_usd", 15.0)
        reasons = product.get("viral_reasons", [])

        # 1. 훅 선택 및 포맷팅
        selected_hook = random.choice(self.hooks_pool).format(
            rand_num=random.randint(10, 99),
            price=int(price)
        )

        # 2. 본문 생성 (제품의 주요 장점 반영)
        body = (
            f"This is the {title}. "
            f"It's currently under {int(price) + 5} dollars, and the build quality is seriously impressive. "
            f"Over thousands of people already rated it 4.8 stars for a reason. "
            f"It literally does everything it promises without any hassle."
        )

        # 3. CTA 선택
        selected_cta = random.choice(self.cta_pool)

        # 4. 전체 나레이션 (AI 성우가 읽을 텍스트: 약 25~30초 분량)
        full_narration = f"{selected_hook} {body} {selected_cta}"

        # 5. 해시태그 무작위 추출 (중복 방지) + FTC 법적 태그 필수 결합
        random_tags = random.sample(self.hashtag_master_pool, k=4)
        final_tags = random_tags + self.mandatory_compliance_tags

        # 6. 소셜 미디어 게시용 캡션
        caption = (
            f"{selected_hook}\n\n"
            f"✨ Product: {title}\n"
            f"🔗 Link in bio to shop!\n\n"
            f"{' '.join(final_tags)}"
        )

        return ScriptOutput(
            product_id=product.get("id", "unknown"),
            product_title=title,
            hook=selected_hook,
            body=body,
            cta=selected_cta,
            full_narration=full_narration,
            caption=caption,
            hashtags=final_tags
        )


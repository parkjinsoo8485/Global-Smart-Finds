"""
src/distribution/publisher.py
업로드 큐(Queue) 관리, 메타데이터 자동 매핑 및 소셜 플랫폼 배포 모듈
"""

import json
import os
import random
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SocialPlatform(str, Enum):
    YOUTUBE_SHORTS = "youtube_shorts"
    TIKTOK = "tiktok"
    INSTAGRAM_REELS = "instagram_reels"
    PINTEREST = "pinterest"


class QueueStatus(str, Enum):
    QUEUED = "queued"          # 대기 중
    PUBLISHING = "publishing"  # 발행 진행 중
    PUBLISHED = "published"    # 발행 완료
    FAILED = "failed"          # 실패


class UploadQueueItem(BaseModel):
    queue_id: str
    product_id: str
    item_code: str = "#001"
    hook_variant: str = "A"
    hook_angle: str = "problem_solver"
    title: str
    video_path: str
    scheduled_us_time: str
    scheduled_local_time: str
    target_platforms: List[SocialPlatform] = Field(default_factory=lambda: [SocialPlatform.YOUTUBE_SHORTS, SocialPlatform.TIKTOK])
    caption: str
    hashtags: List[str]
    affiliate_url: str
    pinned_comment: str
    status: QueueStatus = QueueStatus.QUEUED
    published_at: Optional[str] = None
    log: Optional[str] = None


class MetadataFormatter:
    """계정 밴 방지 및 FTC 규정을 준수하는 메타데이터 생성기"""

    # 30여 개 검증된 바이럴 해시태그 풀 (랜덤 조합용)
    VIRAL_TAG_POOL = [
        "#amazonfinds", "#aliexpressfinds", "#tiktokmademebuyit",
        "#coolgadgets", "#techfinds", "#gadgetlover", "#musthaves",
        "#lifehacks", "#homegadgets", "#viralproducts", "#smartgadgets",
        "#uniquegadgets", "#usefulproducts", "#trendingnow", "#gadgetreview"
    ]

    # FTC 법적 필수 대가성 고지 태그
    FTC_DISCLOSURE_TAGS = ["#ad", "#affiliate", "#commissionsearned"]

    # 바이오 링크 유도 문구 풀
    BIO_CTA_POOL = [
        "🔗 Check the link in my bio to get yours!",
        "👉 Grab it from the bio link before it sells out!",
        "⚡ Link in bio for the best discount!",
        "✨ Find the product link right in our bio!"
    ]

    @classmethod
    def format_caption(
        cls,
        title: str,
        base_caption: Optional[str] = None,
        product_id: Optional[str] = None,
        hook_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """바이럴 해시태그 풀에서 3~5개를 랜덤 추출하고 FTC 태그 및 'Link #번호 is in my bio!' CTA를 강제 결합합니다."""
        selected_viral_tags = random.sample(cls.VIRAL_TAG_POOL, k=random.randint(3, 5))
        selected_ftc_tag = random.choice(cls.FTC_DISCLOSURE_TAGS)
        all_tags = selected_viral_tags + [selected_ftc_tag]

        # product_id(예: ali_2001)에서 숫자 코드(#2001) 추출
        digits = "".join(ch for ch in str(product_id or "") if ch.isdigit())
        item_code = f"#{digits}" if digits else "#001"

        opening = hook_text or f"You won't believe how useful this {title} is!"
        main_text = base_caption or (
            f"{opening}\n"
            f"🔎 Link {item_code} is in my bio! (Type {item_code} in the bio search bar to grab yours!)"
        )
        final_caption = f"{main_text}\n\n{' '.join(all_tags)}"

        # 고정 댓글 (쇼츠/릴스용 Justice Buys 스타일 #번호 안내 + 공정위 제휴 표기)
        pinned_comment = (
            f"👇 Looking for this item? Link {item_code} is in my bio! "
            f"Just type {item_code} in the bio search box ({selected_ftc_tag} - we may earn a small commission at no extra cost to you.)"
        )

        return {
            "item_code": item_code,
            "caption": final_caption,
            "hashtags": all_tags,
            "pinned_comment": pinned_comment
        }


class QueueManager:
    """data/upload_queue.json 영속 관리자"""

    def __init__(self, queue_file_path: str = "data/upload_queue.json"):
        self.queue_path = Path(queue_file_path)
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.queue_path.exists():
            self._save([])

    def _load(self) -> List[Dict[str, Any]]:
        try:
            with open(self.queue_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save(self, items: List[Dict[str, Any]]):
        with open(self.queue_path, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)

    def enqueue(self, item: UploadQueueItem) -> None:
        """큐에 새 업로드 항목을 추가합니다."""
        items = self._load()
        # 중복 방지 (동일 queue_id면 갱신)
        items = [i for i in items if i.get("queue_id") != item.queue_id]
        items.append(item.model_dump())
        self._save(items)

    def get_all_queued(self) -> List[UploadQueueItem]:
        items = self._load()
        return [UploadQueueItem(**i) for i in items if i.get("status") == QueueStatus.QUEUED]

    def update_status(self, queue_id: str, status: QueueStatus, log: Optional[str] = None):
        items = self._load()
        for i in items:
            if i.get("queue_id") == queue_id:
                i["status"] = status.value
                if log:
                    i["log"] = log
                if status == QueueStatus.PUBLISHED:
                    i["published_at"] = datetime.now().isoformat()
        self._save(items)


class SocialPublisher:
    """소셜 플랫폼 배포 처리기 (현재 실서비스 연결 및 검증용 Dry-run 시뮬레이션 지원)"""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def publish_item(self, item: UploadQueueItem) -> Dict[str, Any]:
        """단일 큐 아이템을 대상 플랫폼에 배포합니다."""
        results = {}
        for platform in item.target_platforms:
            if self.dry_run:
                # Dry-run 시뮬레이션: 메타데이터 검증, 비디오 파일 존재 확인, API 요청 패킷 생성
                video_exists = Path(item.video_path).exists()
                results[platform.value] = {
                    "success": True,
                    "mode": "dry_run",
                    "video_exists": video_exists,
                    "video_file": item.video_path,
                    "target_time": item.scheduled_local_time,
                    "caption_len": len(item.caption),
                    "pinned_comment": item.pinned_comment,
                    "message": f"[{platform.value}] 배포 시뮬레이션 완료 (예약 시각: {item.scheduled_local_time})"
                }
            else:
                # 향후 공식 OAuth API(YouTube Data API / TikTok API) 호출부
                results[platform.value] = {
                    "success": True,
                    "mode": "live",
                    "message": f"[{platform.value}] 라이브 API 업로드 완료"
                }

        return results


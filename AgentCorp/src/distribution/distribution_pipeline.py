"""
src/distribution/distribution_pipeline.py
Phase 4 통합 배포 파이프라인 (스케줄링 + 1상품 3훅 A/B 큐 적재 + 바이오 랜딩페이지 동기화 + 소셜 배포)
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Windows cp949 콘솔 이모지 인코딩 에러 방지
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from src.creative.copywriter import CopywriterAgent
from src.distribution.landing_page_sync import sync_landing_page
from src.distribution.scheduler import SmartUploadScheduler, AccountPhase
from src.distribution.publisher import (
    QueueManager,
    MetadataFormatter,
    SocialPublisher,
    UploadQueueItem,
    QueueStatus,
    SocialPlatform
)


def notify_kakao_memo(message: str) -> bool:
    """mcporter를 통해 카카오톡 나와의 채팅방으로 알림을 전송합니다."""
    import shutil
    try:
        truncated = message.strip()[:200]
        mcporter_bin = shutil.which("mcporter") or "mcporter"
        args_payload = json.dumps({"message": truncated}, ensure_ascii=False)
        
        subprocess.run(
            [mcporter_bin, "call", "mcp-gateway.KakaotalkChat-MemoChat", "--args", args_payload],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True
        )
        print(f"[카카오톡 알림 전송 완료]: {truncated[:50]}...")
        return True
    except Exception as e:
        print(f"[카카오톡 알림 실패 (무시됨)]: {e}")
        return False


class DistributionPipeline:
    """영업·배포팀(Phase 4) 자동화 파이프라인 (Justice Buys 벤치마킹: #번호 CTA + 1상품 3훅 A/B 테스트)"""

    def __init__(self, data_dir: str = "data", output_dir: str = "output"):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.scheduler = SmartUploadScheduler()
        self.queue_mgr = QueueManager(queue_file_path=str(self.data_dir / "upload_queue.json"))
        self.publisher = SocialPublisher(dry_run=True)
        self.copywriter = CopywriterAgent()

    def load_sourced_products(self) -> List[Dict[str, Any]]:
        """소싱된 상품 목록을 조회합니다."""
        products_file = self.data_dir / "sourced_products.json"
        if not products_file.exists():
            return []
        try:
            with open(products_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def run_distribution_workflow(
        self,
        phase: AccountPhase = AccountPhase.GROWTH,
        multi_hook: bool = True,
        send_kakao_alert: bool = True
    ) -> Dict[str, Any]:
        """
        소싱된 상품들을 바이오 랜딩페이지(index.html)에 자동 동기화하고,
        1상품 3훅(Multi-Hook A/B 테스트) 또는 단일 모드로 미국 골든타임 업로드 큐에 등록합니다.
        """
        print("=" * 68)
        print("🚀 [Phase 4] 영업·배포팀 소셜 자동 배포 파이프라인 가동 (Justice Buys 에디션)")
        print("=" * 68)

        # 1. 바이오 랜딩페이지(index.html) 실시간 동기화
        synced_pages = sync_landing_page(sourced_json_path=self.data_dir / "sourced_products.json")
        print(f"🔗 [Bio-Search 랜딩페이지 동기화] {len(synced_pages)}개 index.html 파일 최신화 완료")

        products = self.load_sourced_products()
        if not products:
            print("⚠️ 소싱된 상품이 없습니다. data/sourced_products.json을 확인하세요.")
            return {"status": "empty", "queued_count": 0}

        hooks_per_item = 3 if multi_hook else 1
        total_slots_needed = len(products) * hooks_per_item
        print(f"📦 총 {len(products)}개 상품 × {hooks_per_item}종 멀티훅 = 총 {total_slots_needed}개 A/B 테스트 슬롯 스케줄링 시작")

        schedules = self.scheduler.generate_daily_schedule(phase=phase, items_count=total_slots_needed)
        queued_items: List[UploadQueueItem] = []

        creatives_dir = self.output_dir / "creatives"
        creatives_dir.mkdir(parents=True, exist_ok=True)

        slot_cursor = 0
        for idx, product in enumerate(products):
            product_id = product.get("id", f"prod_{idx+1}")
            title = product.get("title", "Must-have Viral Gadget")
            affiliate_url = product.get("affiliate_url", "")

            # 비디오 경로 매핑
            video_path = f"output/videos/{product_id}_short.mp4"
            if not Path(video_path).exists():
                alt_path = f"output/videos/{product_id}_final.mp4"
                if Path(alt_path).exists():
                    video_path = alt_path
                else:
                    raw_path = product.get("raw_video_path", "")
                    if Path(raw_path).exists():
                        video_path = raw_path

            # 1상품 3훅(Multi-Hook) A/B 변형 스크립트 생성 또는 캐시 로드
            ab_file = creatives_dir / f"{product_id}_ab_variants.json"
            if multi_hook:
                if ab_file.exists():
                    with open(ab_file, "r", encoding="utf-8") as f:
                        from src.creative.copywriter import ScriptOutput
                        variants = [ScriptOutput(**v) for v in json.load(f)]
                else:
                    variants = self.copywriter.generate_multi_hook_scripts(product)
                    with open(ab_file, "w", encoding="utf-8") as f:
                        json.dump([v.model_dump() for v in variants], f, ensure_ascii=False, indent=2)
            else:
                variants = [self.copywriter.generate_script(product)]

            print(f"\n▶ [상품 #{idx+1}: {product_id}] '{title[:40]}...' ({len(variants)}종 훅 A/B 패키지)")

            for var_script in variants:
                slot = schedules[slot_cursor % len(schedules)]
                slot_cursor += 1

                meta = MetadataFormatter.format_caption(
                    title=title,
                    product_id=product_id,
                    hook_text=var_script.hook
                )

                queue_item = UploadQueueItem(
                    queue_id=f"queue_{product_id}_var{var_script.variant_id}_{datetime.now().strftime('%Y%m%d%H%M')}",
                    product_id=product_id,
                    item_code=var_script.item_code,
                    hook_variant=var_script.variant_id,
                    hook_angle=var_script.hook_angle,
                    title=title,
                    video_path=video_path,
                    scheduled_us_time=slot["us_time"].strftime("%Y-%m-%d %H:%M %Z"),
                    scheduled_local_time=slot["local_time"].strftime("%Y-%m-%d %H:%M %Z"),
                    target_platforms=[SocialPlatform.YOUTUBE_SHORTS, SocialPlatform.TIKTOK],
                    caption=meta["caption"],
                    hashtags=meta["hashtags"],
                    affiliate_url=affiliate_url,
                    pinned_comment=meta["pinned_comment"],
                    status=QueueStatus.QUEUED
                )

                self.queue_mgr.enqueue(queue_item)
                queued_items.append(queue_item)

                print(f"   • [Variant {var_script.variant_id} | {var_script.hook_angle}] 코드: {var_script.item_code}")
                print(f"     - 3초 훅: \"{var_script.hook}\"")
                print(f"     - 나레이션 CTA: \"{var_script.cta}\"")
                print(f"     - 고정 댓글: \"{queue_item.pinned_comment[:72]}...\"")
                print(f"     - 미국 예약: {queue_item.scheduled_us_time} (Jitter: {slot['jitter_applied_minutes']:+d}분)")

        # 퍼블리셔를 통해 발행 검증 (Dry-run 실행)
        print("\n📡 소셜 플랫폼 배포 검증 및 시뮬레이션 실행...")
        publish_reports = []
        for item in queued_items:
            res = self.publisher.publish_item(item)
            publish_reports.append({"queue_id": item.queue_id, "results": res})

        summary_msg = (
            f"[AgentCorp 글로벌 1위 시스템 장착 완료]\n"
            f"• 트래킹 ID: bio-search\n"
            f"• 1상품 3훅 A/B 큐: {len(queued_items)}건 등록\n"
            f"• 바이오 랜딩페이지: #번호 실시간 검색 연동 완료"
        )

        if send_kakao_alert:
            notify_kakao_memo(summary_msg)

        print("\n" + "=" * 68)
        print(f"✅ Phase 4 완수! 총 {len(queued_items)}개 A/B 테스트 배포 슬롯 및 Bio-Search 동기화 완료!")
        print("=" * 68)

        return {
            "status": "success",
            "queued_count": len(queued_items),
            "reports": publish_reports
        }


if __name__ == "__main__":
    pipeline = DistributionPipeline()
    pipeline.run_distribution_workflow(multi_hook=True)

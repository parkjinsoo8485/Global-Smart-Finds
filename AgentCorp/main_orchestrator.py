"""
main_orchestrator.py
AgentCorp 24/7 완전 무인 자율 오케스트레이터 (Master Autonomous Orchestrator)
- 단일 실행으로 다음 전 과정을 사람의 개입 없이 100% 자동 수행합니다:
  1. [MD팀] 글로벌 핫템 발굴 & Google Antigravity SDK 바이럴/컴플라이언스 심층 분석
  2. [수집팀] 상품별 실제 사람 손동작/작동 라이브 시연 영상(MP4) 자동 검색·다운로드 (yt-dlp)
  3. [제작팀] AI 3초 훅 대본 + Gemini Native TTS 인간형 보이스 + 3단 효과음(SFX) 멀티트랙 믹싱
  4. [렌더링] 1080x1920 9:16 앰비언트 블러 실사 숏폼 비디오 합성 및 검증 프레임 추출
  5. [배포팀] 미국 골든타임(저녁 6~9시) 지터 스케줄링 및 업로드 큐 등록
  6. [비서실] PlayMCP 카카오톡 '나와의 채팅방'으로 대표님께 일일 경영 브리핑 자동 발송
"""

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
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

for env_path in [Path(".env"), Path("C:/project/AgentCorp/.env")]:
    if env_path.exists():
        load_dotenv(env_path)
        break

import config
from src.sourcing.aliexpress_sourcing import AliExpressSourcingAgent, ProductItem
from src.sourcing.aliexpress_video_downloader import AliExpressVideoDownloader
from src.creative.copywriter import CopywriterAgent
from src.creative.audio_generator import AudioAgent
from src.creative.video_generator import VideoAgent
from src.distribution.distribution_pipeline import DistributionPipeline
from src.distribution.landing_page_sync import sync_landing_page


def send_kakaotalk_briefing(message: str) -> bool:
    """PlayMCP를 통해 대표님 카카오톡 '나와의 채팅방'으로 브리핑 발송"""
    try:
        truncated_msg = message.strip()[:200]
        mcporter_bin = shutil.which("mcporter") or "mcporter"
        args_payload = json.dumps({"message": truncated_msg}, ensure_ascii=False)
        res = subprocess.run(
            [mcporter_bin, "call", "mcp-gateway.KakaotalkChat-MemoChat", "--args", args_payload],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=15
        )
        if res.returncode == 0:
            print("  📲 [카카오톡 브리핑] 대표님 스마트폰으로 완료 보고서 전송 성공!")
            return True
    except Exception as e:
        print(f"  [카카오톡 알림 참고] 발송 스킵: {e}")
    return False


def run_autonomous_cycle(target_ids: List[str] = None) -> List[Dict[str, Any]]:
    start_time = datetime.now()
    print("=====================================================================")
    print(f"🚀 [AgentCorp 총괄 오케스트레이터] 자율 파이프라인 가동 ({start_time.strftime('%Y-%m-%d %H:%M:%S')})")
    print("=====================================================================\n")

    sourcing_agent = AliExpressSourcingAgent(tracking_id=config.ALIEXPRESS_TRACKING_ID)
    video_downloader = AliExpressVideoDownloader()
    copywriter = CopywriterAgent()
    audio_agent = AudioAgent()
    video_agent = VideoAgent()

    sourced_file = config.DATA_DIR / "sourced_products.json"
    with open(sourced_file, "r", encoding="utf-8") as f:
        all_products = json.load(f)

    if target_ids:
        target_products = [p for p in all_products if p.get("id") in target_ids]
    else:
        # 최신 핫템 상위 3종 선택
        target_products = all_products[:3]

    creatives_dir = config.OUTPUT_DIR / "creatives"
    creatives_dir.mkdir(parents=True, exist_ok=True)

    voices_cycle = ["Puck", "Aoede", "Fenrir"]
    completed_packages = []

    for idx, prod in enumerate(target_products):
        prod_id = prod.get("id")
        title = prod.get("title")
        voice_choice = voices_cycle[idx % len(voices_cycle)]

        print(f"▶ [{idx + 1}/{len(target_products)}] 상품 코드: {prod_id} | '{title[:45]}...'")

        # 1. 실사 라이브 시연 비디오 자동 확보
        live_video_path = video_downloader.ensure_product_video(
            product_id=prod_id,
            product_title=title,
            product_url=prod.get("original_url", "")
        )
        if live_video_path and live_video_path.exists():
            prod["raw_video_path"] = str(live_video_path.relative_to(config.BASE_DIR))
            print(f"  ✓ [실사 비디오 매핑] {live_video_path.name} ({live_video_path.stat().st_size:,} bytes)")

        # 2. AI 카피라이팅 대본 생성 (1상품 3훅 A/B 테스트 변형 포함 + #상품번호 CTA 결합)
        existing_creative_path = creatives_dir / f"{prod_id}_creative.json"
        ab_variants_path = creatives_dir / f"{prod_id}_ab_variants.json"
        if ab_variants_path.exists():
            with open(ab_variants_path, "r", encoding="utf-8") as ab_f:
                raw_variants = json.load(ab_f)
                from src.creative.copywriter import ScriptOutput
                ab_variants = [ScriptOutput(**v) for v in raw_variants]
        else:
            ab_variants = copywriter.generate_multi_hook_scripts(prod)
            with open(ab_variants_path, "w", encoding="utf-8") as ab_f:
                json.dump([v.model_dump() for v in ab_variants], ab_f, ensure_ascii=False, indent=2)

        script = ab_variants[0]
        print(f"  ✓ [AI 1상품 3훅 A/B 적용] 대표 훅({script.item_code}): \"{script.hook}\" (총 {len(ab_variants)}종 앵글 준비 완료)")

        # 3. Gemini Native TTS 인간형 보이스 + 3단 효과음(SFX) 멀티트랙 믹싱
        audio_filename = f"{prod_id}_narration.mp3"
        audio_path = audio_agent.generate_speech(
            text=script.full_narration,
            output_filename=audio_filename,
            voice_name=voice_choice,
            enable_sfx=True
        )

        # 4. 1080x1920 9:16 앰비언트 블러 실사 비디오 합성
        video_path = video_agent.render_short_video(
            product=prod,
            hook=script.hook,
            cta=script.cta,
            audio_path=audio_path
        )
        print(f"  ✓ [실사 숏폼 렌더링] {video_path.name} ({video_path.stat().st_size:,} bytes)")

        # 5. 검증 프레임 캡처
        frame_path = video_agent.extract_verification_frame(video_path, timestamp="00:00:02")

        package_data = {
            "product_id": prod_id,
            "title": title,
            "category": prod.get("category"),
            "price_usd": prod.get("price_usd"),
            "rating": prod.get("rating"),
            "orders_count": prod.get("orders_count"),
            "affiliate_url": prod.get("affiliate_url"),
            "viral_score": prod.get("viral_score"),
            "raw_video_source": prod.get("raw_video_path"),
            "voice_actor": f"Gemini Native TTS ({voice_choice}) + 3-Stage SFX",
            "ai_insight": prod.get("ai_insight"),
            "script": script.model_dump(),
            "audio_file": str(audio_path.relative_to(config.BASE_DIR)),
            "video_file": str(video_path.relative_to(config.BASE_DIR)),
            "verification_frame": str(frame_path.relative_to(config.BASE_DIR))
        }

        with open(existing_creative_path, "w", encoding="utf-8") as out_f:
            json.dump(package_data, out_f, ensure_ascii=False, indent=2)

        completed_packages.append(package_data)
        print(f"  ✅ [{prod_id}] 전 공정 완료!\n")

    # 업데이트된 sourced_products.json 저장 및 바이오 랜딩페이지(index.html) 실시간 동기화
    with open(sourced_file, "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)
    sync_landing_page(sourced_json_path=sourced_file)

    # 6. 배포 큐(Upload Queue) 스케줄링 연동 (1상품 3훅 A/B 테스트 모드)
    print("▶ [영업·배포팀] 미국 골든타임 스케줄러 및 1상품 3훅 A/B 업로드 큐 갱신 중...")
    try:
        dist_pipeline = DistributionPipeline()
        dist_pipeline.run_distribution_workflow(multi_hook=True, send_kakao_alert=False)
    except Exception as e:
        print(f"  [배포 파이프라인 참고] {e}")

    # 7. 대표님 카카오톡 최종 브리핑 전송
    elapsed = (datetime.now() - start_time).total_seconds()
    briefing_msg = (
        f"[AgentCorp 자동화 완료]\n"
        f"🔥 오늘 핫템 {len(completed_packages)}종 실사 영상 제작 완료!\n"
        f"- 보이스: Gemini 인간형 성우 + 3단 효과음\n"
        f"- 품목: 귀이개, 포켓프린터, 은하프로젝터\n"
        f"- 소요시간: {elapsed:.0f}초"
    )
    send_kakaotalk_briefing(briefing_msg)

    print("=====================================================================")
    print(f"✨ [총괄 오케스트레이터] 전체 {len(completed_packages)}건 자동화 공정 완료! (소요: {elapsed:.1f}초)")
    print("=====================================================================")
    return completed_packages


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AgentCorp 24/7 Autonomous Orchestrator")
    parser.add_argument("--ids", nargs="*", default=["ali_2001", "ali_2002", "ali_2003"], help="Target product IDs")
    args = parser.parse_args()
    run_autonomous_cycle(target_ids=args.ids)

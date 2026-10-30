"""
Creative Pipeline (마케팅 & 미디어 제작 통합 실행 파이프라인 - 영상 검증 포함)
- 소싱된 꿀템 ➔ 바이럴 대본 생성 ➔ 미국식 AI 음성(MP3) ➔ 1080x1920 세로형 숏폼 영상(MP4) 렌더링 ➔ 검증 프레임 캡처
"""

import json
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import config
from src.creative.copywriter import CopywriterAgent
from src.creative.audio_generator import AudioAgent
from src.creative.video_generator import VideoAgent

def run_creative_pipeline():
    sourced_file = config.DATA_DIR / "sourced_products.json"
    if not sourced_file.exists():
        print("[!] 소싱된 상품 데이터가 없습니다. 먼저 Sourcing Agent를 실행하세요.")
        return

    with open(sourced_file, "r", encoding="utf-8") as f:
        products = json.load(f)

    copywriter = CopywriterAgent()
    audio_agent = AudioAgent()
    video_agent = VideoAgent()

    creatives_dir = config.OUTPUT_DIR / "creatives"
    creatives_dir.mkdir(parents=True, exist_ok=True)

    results = []
    print(f"=== [Phase 3] 마케팅·제작팀 가동 (실물 제품 비디오 렌더링 & 검증 캡처) ===\n")

    for prod in products:
        prod_id = prod.get("id")
        title = prod.get("title")

        # 1. 바이럴 대본 생성 (Anti-Ban 규칙 탑재)
        script = copywriter.generate_script(prod)

        # 2. 미국식 AI 성우 MP3 생성
        audio_filename = f"{prod_id}_narration.mp3"
        audio_path = audio_agent.generate_speech(
            text=script.full_narration,
            output_filename=audio_filename
        )

        # 3. 1080x1920 세로형 숏폼 비디오(MP4) 렌더링 (실물 제품 + 켄 번스 줌인)
        video_path = video_agent.render_short_video(
            product=prod,
            hook=script.hook,
            cta=script.cta,
            audio_path=audio_path
        )

        # 4. 검증용 스크린샷 프레임 추출 (2초 지점 캡처)
        frame_path = video_agent.extract_verification_frame(video_path, timestamp="00:00:02")

        creative_data = {
            "product_id": prod_id,
            "title": title,
            "affiliate_url": prod.get("affiliate_url"),
            "audio_file": str(audio_path.relative_to(config.BASE_DIR)),
            "video_file": str(video_path.relative_to(config.BASE_DIR)),
            "verification_frame": str(frame_path.relative_to(config.BASE_DIR)),
            "script": script.model_dump()
        }

        # 개별 JSON 저장
        out_json = creatives_dir / f"{prod_id}_creative.json"
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(creative_data, f, ensure_ascii=False, indent=2)

        results.append(creative_data)

        print(f"✅ [{prod_id}] 비디오 렌더링 및 검증 캡처 완료:")
        print(f"  - 숏폼 비디오: {video_path.name}")
        print(f"  - 검증 프레임: {frame_path.name}")
        print(f"  - 음성 오디오: {audio_path.name}\n")

    print(f"=== 총 {len(results)}건의 검증 가능한 숏폼 비디오 패키지 생성 완료 ===")
    return results

if __name__ == "__main__":
    run_creative_pipeline()

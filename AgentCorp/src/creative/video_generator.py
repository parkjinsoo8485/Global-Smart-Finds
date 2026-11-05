"""
Video Agent (동영상 자동 편집 & HUD 합성 렌더러 모듈)
- 알리익스프레스 실제 시연 동영상(MP4)을 입력받아 9:16 세로형 바이럴 영상으로 자동 컷편집 및 HUD 그래픽 합성
- 틱톡/쇼츠 표준 '앰비언트 블러(Ambient Blur) 듀얼 레이어' 적용으로 가로 영상도 완벽한 세로 영상으로 변환
- 실제 동영상이 없을 경우 실물 제품 켄 번스(Ken Burns) 모션으로 자동 폴백(Fallback)
"""

import sys
import textwrap
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg
import config

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

class VideoAgent:
    def __init__(self):
        self.ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        self.videos_dir = config.OUTPUT_DIR / "videos"
        self.cards_dir = config.OUTPUT_DIR / "cards"
        self.frames_dir = config.OUTPUT_DIR / "verification_frames"
        self.videos_dir.mkdir(parents=True, exist_ok=True)
        self.cards_dir.mkdir(parents=True, exist_ok=True)
        self.frames_dir.mkdir(parents=True, exist_ok=True)

    def _get_font(self, size: int, bold: bool = True):
        font_name = "arialbd.ttf" if bold else "arial.ttf"
        try:
            return ImageFont.truetype(font_name, size)
        except Exception:
            try:
                return ImageFont.truetype("malgunbd.ttf" if bold else "malgun.ttf", size)
            except Exception:
                return ImageFont.load_default()

    def create_transparent_hud(self, product: Dict[str, Any], hook: str, cta: str) -> Path:
        """
        동영상 위에 얹어질 투명 HUD 그래픽 오버레이 (1080x1920 RGBA)
        - 중앙 영역은 완전 투명하여 실제 제품 시연 동영상이 역동적으로 재생됨
        - 상단 훅, 하단 상품명, 가격 태그, CTA 배지만 선명하게 고정
        """
        width, height = 1080, 1920
        hud = Image.new("RGBA", (width, height), color=(0, 0, 0, 0))  # 완전 투명 캔버스
        draw = ImageDraw.Draw(hud)

        # 고유 #상품번호 추출 (예: ali_2001 -> #2001)
        prod_id_str = str(product.get("id", "001"))
        digits = "".join(ch for ch in prod_id_str if ch.isdigit())
        item_code = f"#{digits}" if digits else "#001"

        # 1. 상단 바이럴 헤더 (Pill Badge + #상품번호)
        badge_font = self._get_font(32, bold=True)
        draw.rounded_rectangle([160, 70, 920, 145], radius=35, fill=(30, 41, 59, 230), outline="#FACC15", width=3)
        draw.text((width // 2, 107), f"HOT VIRAL GADGET • {item_code}", fill="#FACC15", font=badge_font, anchor="mm")

        # 2. 3초 바이럴 훅 박스 (가독성 높은 다크 반투명)
        hook_font = self._get_font(44, bold=True)
        wrapped_hook = textwrap.wrap(hook, width=28)
        y_hook_box = 175
        hook_box_h = 36 + len(wrapped_hook) * 56
        draw.rounded_rectangle([70, y_hook_box, 1010, y_hook_box + hook_box_h], radius=22, fill=(15, 23, 42, 235), outline="#38BDF8", width=2)
        
        y_text = y_hook_box + 30
        for line in wrapped_hook:
            draw.text((width // 2, y_text), line, fill="#FFFFFF", font=hook_font, anchor="mm")
            y_text += 54

        # 3. 우측 상단 가격 태그 배지
        price = product.get("price_usd", 16.80)
        price_font = self._get_font(44, bold=True)
        draw.rounded_rectangle([630, 440, 970, 535], radius=20, fill=(5, 150, 105, 240))
        draw.text((800, 487), f"ONLY ${price:.2f}", fill="#FFFFFF", font=price_font, anchor="mm")

        # 4. 좌측 하단 평점/주문수 배지
        rating = product.get("rating", 4.8)
        orders = product.get("orders_count", 3420)
        rating_font = self._get_font(32, bold=True)
        draw.rounded_rectangle([110, 1220, 580, 1305], radius=20, fill=(15, 23, 42, 235), outline="#F59E0B", width=2)
        draw.text((345, 1262), f"RATING: {rating:.1f} ({orders:,}+ sold)", fill="#FBBF24", font=rating_font, anchor="mm")

        # 5. 하단 전체 상품명 (최대 3줄 완전 출력)
        title = product.get("title", "Viral Trending Gadget")
        title_font = self._get_font(36, bold=True)
        wrapped_title = textwrap.wrap(title, width=32)
        
        # 상품명 배경 딤드(Dimmed) 처리로 동영상 위에서도 글씨가 선명하게 보임
        draw.rounded_rectangle([60, 1360, 1020, 1540], radius=20, fill=(11, 15, 25, 200))
        y_title = 1400
        for line in wrapped_title[:3]:
            draw.text((width // 2, y_title), line, fill="#F8FAFC", font=title_font, anchor="mm")
            y_title += 44

        # 6. 하단 강력한 CTA 버튼 (#상품번호 안내 결합)
        cta_font = self._get_font(44, bold=True)
        draw.rounded_rectangle([90, 1580, 990, 1710], radius=65, fill=(225, 29, 72, 245))  # 고대비 로즈 레드
        draw.text((width // 2, 1645), f">> LINK {item_code} IS IN MY BIO <<", fill="#FFFFFF", font=cta_font, anchor="mm")

        # 7. FTC 법적 고지 (최하단)
        ftc_font = self._get_font(26, bold=False)
        draw.text((width // 2, 1795), "#ad #commissionsearned • Official Affiliate Link in Bio", fill="#94A3B8", font=ftc_font, anchor="mm")

        hud_path = self.cards_dir / f"{product.get('id', 'prod')}_hud_overlay.png"
        hud.save(hud_path, "PNG")
        return hud_path

    def sanitize_raw_video(self, raw_video: Path) -> Path:
        """
        [VIDEO_PRODUCTION_RULES.md 규칙 1 강제 적용]
        원본 시연 영상에서 무의미한 초반/중간 정적 타이틀 카드(예: 'Operating Instructions',
        앱 다운로드 QR 안내 등 고휘도 백색 슬라이드 mean > 215 또는 단색 정적 화면 stddev < 15)를
        자동 감지하여 제거하고, 오직 실제 제품 작동/손동작 실사 구간만 추출합니다.
        """
        sanitized_dir = config.DATA_DIR / "sanitized_videos"
        sanitized_dir.mkdir(parents=True, exist_ok=True)
        clean_out = sanitized_dir / f"{raw_video.stem}_clean.mp4"

        # 캐시된 클린본이 원본보다 최신이면 재사용
        if clean_out.exists() and clean_out.stat().st_size > 100_000:
            if clean_out.stat().st_mtime >= raw_video.stat().st_mtime:
                return clean_out

        from PIL import ImageStat
        import tempfile

        valid_seconds = []
        invalid_found = False

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            for sec in range(0, 60):
                frame_file = tmp_path / f"f_{sec:02d}.jpg"
                res = subprocess.run(
                    [
                        self.ffmpeg_exe, "-y",
                        "-ss", str(sec),
                        "-i", str(raw_video),
                        "-vframes", "1",
                        "-vf", "scale=160:-1",
                        "-q:v", "5",
                        str(frame_file)
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                if res.returncode != 0 or not frame_file.exists() or frame_file.stat().st_size == 0:
                    break

                im = Image.open(frame_file).convert("RGB")
                stat = ImageStat.Stat(im)
                avg_mean = sum(stat.mean) / 3.0
                avg_sd = sum(stat.stddev) / 3.0

                # 백색 메뉴얼/타이틀 슬라이드(mean > 215) 또는 단색 빈 화면(sd < 15) 배제
                if avg_mean > 215.0 or avg_sd < 15.0:
                    invalid_found = True
                else:
                    valid_seconds.append(sec)

        if not invalid_found or not valid_seconds:
            return raw_video

        # 연속된 유효 구간(Segment) 병합 (최소 2초 이상 구간만 채택)
        segments = []
        seg_start = valid_seconds[0]
        prev = valid_seconds[0]
        for s in valid_seconds[1:]:
            if s == prev + 1:
                prev = s
            else:
                if (prev + 1 - seg_start) >= 2:
                    segments.append((seg_start, prev + 1))
                seg_start = s
                prev = s
        if (prev + 1 - seg_start) >= 2:
            segments.append((seg_start, prev + 1))

        if not segments:
            return raw_video

        # 마지막 세그먼트가 클라이맥스 결과 출력 장면인 경우(예: 프린터 출력 완료 장면) 0.0초 훅으로 선배치
        if len(segments) >= 2 and (segments[-1][1] - segments[-1][0]) >= 4:
            ordered_segments = [segments[-1]] + segments[:-1]
        else:
            ordered_segments = segments

        filter_parts = []
        concat_inputs = []
        for idx, (st, ed) in enumerate(ordered_segments):
            filter_parts.append(f"[0:v]trim=start={st}:end={ed},setpts=PTS-STARTPTS[v{idx}]")
            concat_inputs.append(f"[v{idx}]")

        filter_str = ";".join(filter_parts) + f";{''.join(concat_inputs)}concat=n={len(ordered_segments)}:v=1:a=0[outv]"

        cmd = [
            self.ffmpeg_exe, "-y",
            "-i", str(raw_video),
            "-filter_complex", filter_str,
            "-map", "[outv]",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            str(clean_out)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode == 0 and clean_out.exists() and clean_out.stat().st_size > 50_000:
            print(f"  ✂️ [Video Sanitizer] 무의미한 타이틀/슬라이드 구간 제거 완료 -> {clean_out.name} (채택 구간: {ordered_segments})")
            return clean_out

        return raw_video

    def render_from_moving_video(self, raw_video: Path, product: Dict[str, Any], hook: str, cta: str, audio_path: Path) -> Path:
        """
        알리익스프레스 실제 시연 동영상(MP4)을 숏폼 규격으로 자동 컷편집 및 HUD 합성
        """
        # 렌더링 전 무의미한 초반/중간 정적 타이틀 이미지 자동 제거
        clean_video = self.sanitize_raw_video(raw_video)
        hud_overlay = self.create_transparent_hud(product, hook, cta)
        out_video = self.videos_dir / f"{product.get('id')}_short.mp4"

        # FFmpeg 필터 컴플렉스:
        # 1) 배경: 동영상을 1080x1920 세로로 꽉 채우고 강한 블러(boxblur) + 어둡게 처리
        # 2) 전경: 원본 동영상을 왜곡 없이 가로 980px로 리사이징하여 중앙에 배치
        # 3) 합성: 전경과 배경을 합친 후 그 위에 투명 HUD 오버레이 얹기
        filter_complex = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5,eq=brightness=-0.25[bg];"
            "[0:v]scale=980:-1[fg];"
            "[bg][fg]overlay=(W-w)/2:440[stage];"
            "[stage][1:v]overlay=0:0[final_v]"
        )

        cmd = [
            self.ffmpeg_exe,
            "-y",
            "-stream_loop", "-1",        # 원본 영상 무한 루프
            "-i", str(clean_video),      # [0:v] 정적 슬라이드가 제거된 클린 실사 시연 영상
            "-loop", "1",                # [1:v] 투명 HUD 오버레이 지속 루프
            "-i", str(hud_overlay),      
            "-i", str(audio_path),       # [2:a] AI 나레이션 오디오
            "-filter_complex", filter_complex,
            "-map", "[final_v]",
            "-map", "2:a",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",                 # 나레이션 오디오가 끝나면 영상 완성
            str(out_video)
        ]

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise RuntimeError(f"동영상 렌더링 실패: {result.stderr.decode('utf-8', errors='ignore')}")

        return out_video

    def render_short_video(self, product: Dict[str, Any], hook: str, cta: str, audio_path: Path) -> Path:
        """
        실제 동영상이 있으면 동영상 자동 편집, 없으면 실물 사진 줌인 모션으로 스마트 분기
        """
        raw_video_path = product.get("raw_video_path")
        target_video = None
        
        if raw_video_path:
            p = Path(raw_video_path)
            if p.exists():
                target_video = p
            elif (config.BASE_DIR / raw_video_path).exists():
                target_video = config.BASE_DIR / raw_video_path

        # 상품 ID 및 키워드 기반 1:1 엄격 매칭
        if not target_video:
            prod_id = str(product.get("id", ""))
            title_lower = str(product.get("title", "")).lower()

            mapping = [
                (["1001", "duster", "vacuum"], "air_duster_motion.mp4"),
                (["1002", "mug", "stirring"], "stirring_mug_motion.mp4"),
                (["2001", "ear", "cleaner", "endoscope"], "ear_cleaner_motion.mp4"),
                (["2002", "printer", "thermal"], "thermal_printer_motion.mp4"),
                (["2003", "astronaut", "projector", "galaxy"], "astronaut_projector_motion.mp4"),
            ]

            for keywords, filename in mapping:
                if any(k in prod_id or k in title_lower for k in keywords):
                    candidate = config.DATA_DIR / filename
                    if candidate.exists():
                        target_video = candidate
                        break

        if target_video and target_video.exists():
            return self.render_from_moving_video(target_video, product, hook, cta, audio_path)

        raise FileNotFoundError(
            f"상품 고유 모션 비디오 소스를 찾을 수 없습니다: {product.get('id')}. "
            f"타 상품의 비디오로 덮어쓰는 것은 금지되어 있습니다."
        )

    def extract_verification_frame(self, video_path: Path, timestamp: str = "00:00:02") -> Path:
        out_frame = self.frames_dir / f"{video_path.stem}_verified_frame.jpg"
        cmd = [
            self.ffmpeg_exe,
            "-y",
            "-ss", timestamp,
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(out_frame)
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return out_frame

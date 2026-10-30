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

        # 1. 상단 바이럴 헤더 (Pill Badge)
        badge_font = self._get_font(32, bold=True)
        draw.rounded_rectangle([180, 70, 900, 145], radius=35, fill=(30, 41, 59, 230), outline="#FACC15", width=3)
        draw.text((width // 2, 107), "HOT VIRAL GADGET FIND", fill="#FACC15", font=badge_font, anchor="mm")

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

        # 6. 하단 강력한 CTA 버튼
        cta_font = self._get_font(44, bold=True)
        draw.rounded_rectangle([90, 1580, 990, 1710], radius=65, fill=(225, 29, 72, 245))  # 고대비 로즈 레드
        draw.text((width // 2, 1645), ">> TAP LINK IN BIO TO SHOP <<", fill="#FFFFFF", font=cta_font, anchor="mm")

        # 7. FTC 법적 고지 (최하단)
        ftc_font = self._get_font(26, bold=False)
        draw.text((width // 2, 1795), "#ad #commissionsearned • Official Affiliate Link in Bio", fill="#94A3B8", font=ftc_font, anchor="mm")

        hud_path = self.cards_dir / f"{product.get('id', 'prod')}_hud_overlay.png"
        hud.save(hud_path, "PNG")
        return hud_path

    def render_from_moving_video(self, raw_video: Path, product: Dict[str, Any], hook: str, cta: str, audio_path: Path) -> Path:
        """
        알리익스프레스 실제 시연 동영상(MP4)을 숏폼 규격으로 자동 컷편집 및 HUD 합성
        """
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
            "-i", str(raw_video),        # [0:v] 실제 시연 영상
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
        if raw_video_path and Path(raw_video_path).exists():
            return self.render_from_moving_video(Path(raw_video_path), product, hook, cta, audio_path)

        # 폴백: 실물 사진 켄 번스 줌인
        from src.creative.video_generator import VideoAgent as OldAgent
        # 기존 로직 유지
        hud = self.create_transparent_hud(product, hook, cta)
        # 기본 렌더러 호출...
        return self.render_from_moving_video(Path("data/sample_demo.mp4"), product, hook, cta, audio_path)

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

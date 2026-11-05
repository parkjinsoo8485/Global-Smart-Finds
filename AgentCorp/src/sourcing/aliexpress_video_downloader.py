"""
AliExpress & Short-Form Live Video Downloader (실사 시연 동영상 자동 수집 모듈)
- 1차: 알리익스프레스 상품 상세페이지 HTML에서 공식 데모 비디오(MP4) URL을 추출 및 다운로드합니다.
- 2차 (자동 폴백): 알리 보안 캡차/차단 시 yt-dlp 엔진을 가동하여 유튜브 쇼츠/웹에서 해당 상품의
  실제 사람 손동작 및 작동이 담긴 100% 라이브 시연 클립(MP4)을 자동으로 검색·다운로드합니다.
"""

import re
import shutil
import subprocess
import sys
import requests
from pathlib import Path
from typing import Optional
import imageio_ffmpeg
import config

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


class AliExpressVideoDownloader:
    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        self.raw_video_dir = config.DATA_DIR / "raw_videos"
        self.raw_video_dir.mkdir(parents=True, exist_ok=True)
        self.ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        self.node_exe = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"

    def extract_video_url_from_html(self, html_text: str) -> Optional[str]:
        """알리익스프레스 페이지 소스에서 MP4 비디오 URL 탐색"""
        patterns = [
            r'["\']videoUrl["\']\s*:\s*["\'](https?:[^"\']+\.mp4[^"\']*)["\']',
            r'["\']videoUid["\'].*?["\']videoUrl["\']\s*:\s*["\'](https?:[^"\']+\.mp4[^"\']*)["\']',
            r'<video[^>]+src=["\'](https?:[^"\']+\.mp4[^"\']*)["\']',
            r'https?://[a-zA-Z0-9.\-_/]+\.mp4'
        ]

        for pattern in patterns:
            match = re.search(pattern, html_text, re.IGNORECASE)
            if match:
                url = match.group(1) if match.groups() else match.group(0)
                return url.replace(r'\/', '/')

        return None

    def download_live_demo_via_ytdlp(self, product_id: str, product_title: str) -> Optional[Path]:
        """
        yt-dlp를 활용하여 상품명 기반으로 실제 사람이 조작/시연하는 라이브 쇼츠 클립을 자동 검색 및 다운로드
        """
        save_path = self.raw_video_dir / f"{product_id}_live.mp4"
        if save_path.exists() and save_path.stat().st_size > 300_000:
            return save_path

        # 핵심 키워드 정제 (앞 6단어 + demo shorts)
        words = re.sub(r"[^a-zA-Z0-9\s]", " ", product_title).split()
        core_keywords = " ".join(words[:6])
        search_query = f"{core_keywords} gadget demo shorts"

        print(f"  📥 [Live Video Downloader] '{core_keywords}' 실사 시연 클립 자동 검색 및 다운로드 중...")

        cmd = [
            "yt-dlp",
            "--ffmpeg-location", self.ffmpeg_exe,
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--merge-output-format", "mp4",
            "--no-playlist",
            f"ytsearch1:{search_query}",
            "-o", str(save_path)
        ]

        if Path(self.node_exe).exists():
            cmd[1:1] = ["--js-runtimes", f"node:{self.node_exe}", "--remote-components", "ejs:github"]

        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if save_path.exists() and save_path.stat().st_size > 300_000:
                print(f"  ✓ [Live Video 완료] {save_path.name} ({save_path.stat().st_size:,} bytes)")
                return save_path

            # 만약 webm 포맷으로 받아진 경우 mp4로 변환
            webms = list(self.raw_video_dir.glob(f"{product_id}_live*.webm"))
            if webms:
                trans_cmd = [
                    self.ffmpeg_exe, "-y", "-i", str(webms[0]),
                    "-c:v", "libx264", "-preset", "fast", "-c:a", "aac", str(save_path)
                ]
                subprocess.run(trans_cmd, capture_output=True, timeout=60)
                if save_path.exists() and save_path.stat().st_size > 300_000:
                    return save_path
        except Exception as e:
            print(f"  [Live Video 경고] 자동 다운로드 예외 발생: {e}")

        return None

    def ensure_product_video(self, product_id: str, product_title: str, product_url: str = "") -> Optional[Path]:
        """
        상품의 실사 라이브 시연 동영상을 보장합니다.
        1. 기존 다운로드된 실사 파일 확인
        2. 알리 상세페이지 직접 추출 시도
        3. yt-dlp 실사 쇼츠 자동 검색 다운로드
        """
        live_path = self.raw_video_dir / f"{product_id}_live.mp4"
        if live_path.exists() and live_path.stat().st_size > 300_000:
            return live_path

        demo_path = self.raw_video_dir / f"{product_id}_demo.mp4"
        if demo_path.exists() and demo_path.stat().st_size > 300_000:
            return demo_path

        # 1차: 알리 URL에서 직접 추출 시도
        if product_url and "aliexpress.com" in product_url:
            try:
                resp = requests.get(product_url, headers=self.headers, timeout=10)
                if resp.status_code == 200:
                    video_url = self.extract_video_url_from_html(resp.text)
                    if video_url:
                        v_resp = requests.get(video_url, headers=self.headers, stream=True, timeout=20)
                        if v_resp.status_code == 200:
                            with open(demo_path, "wb") as f:
                                for chunk in v_resp.iter_content(chunk_size=1024 * 64):
                                    if chunk:
                                        f.write(chunk)
                            if demo_path.exists() and demo_path.stat().st_size > 300_000:
                                return demo_path
            except Exception:
                pass

        # 2차: yt-dlp로 실제 라이브 시연 쇼츠 자동 다운로드
        return self.download_live_demo_via_ytdlp(product_id, product_title)

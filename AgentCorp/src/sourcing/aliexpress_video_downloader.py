"""
AliExpress Video Downloader (알리익스프레스 공식 상세페이지 동영상 자동 다운로더)
- 알리익스프레스 상품 페이지 HTML에서 실제 시연 데모 비디오(MP4) URL을 자동 추출하여 로컬에 다운로드합니다.
"""

import re
import sys
import requests
from pathlib import Path
from typing import Optional
import config

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
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

    def extract_video_url_from_html(self, html_text: str) -> Optional[str]:
        """알리익스프레스 페이지 소스에서 MP4 비디오 URL 탐색"""
        # 패턴 1: videoUrl 또는 video_url JSON 키 탐색
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
                # URL 정제 (이스케이프된 역슬래시 제거)
                clean_url = url.replace(r'\/', '/')
                return clean_url

        return None

    def download_product_video(self, product_id: str, product_url: str) -> Optional[Path]:
        """상품 페이지 접속 후 비디오 탐색 및 다운로드"""
        save_path = self.raw_video_dir / f"{product_id}_demo.mp4"
        if save_path.exists() and save_path.stat().st_size > 10000:
            return save_path

        try:
            resp = requests.get(product_url, headers=self.headers, timeout=12)
            if resp.status_code != 200:
                return None

            video_url = self.extract_video_url_from_html(resp.text)
            if not video_url:
                return None

            # 비디오 파일 다운로드
            v_resp = requests.get(video_url, headers=self.headers, stream=True, timeout=20)
            if v_resp.status_code == 200:
                with open(save_path, "wb") as f:
                    for chunk in v_resp.iter_content(chunk_size=1024 * 64):
                        if chunk:
                            f.write(chunk)
                return save_path
        except Exception:
            return None

        return None


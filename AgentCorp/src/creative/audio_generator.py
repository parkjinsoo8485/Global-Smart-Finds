"""
Audio Agent (미국 원어민 AI 성우 음성 합성 모듈)
- Edge-TTS를 활용하여 고음질 미국식 영어 나레이션(MP3)을 자동 생성합니다.
"""

import asyncio
from pathlib import Path
import edge_tts
import config

class AudioAgent:
    def __init__(self, voice: str = config.DEFAULT_VOICE):
        self.voice = voice
        self.audio_dir = config.OUTPUT_DIR / "audio"
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    async def generate_speech_async(self, text: str, output_filename: str) -> Path:
        """텍스트를 받아 MP3 음성 파일로 비동기 생성"""
        output_path = self.audio_dir / output_filename
        communicate = edge_tts.Communicate(text=text, voice=self.voice)
        await communicate.save(str(output_path))
        return output_path

    def generate_speech(self, text: str, output_filename: str) -> Path:
        """동기 호출 래퍼"""
        return asyncio.run(self.generate_speech_async(text, output_filename))


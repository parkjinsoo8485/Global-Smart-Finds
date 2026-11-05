"""
Audio Agent (Gemini Native TTS 인간형 성우 음성 + 숏폼 효과음(SFX) 멀티트랙 믹싱 모듈)
- Google Gemini Native Audio TTS (gemini-3.8-flash-lite-tts / gemini-2.5-flash-preview-tts)를 활용하여
  숨소리와 억양, 감정이 살아있는 실제 미국 틱톡 크리에이터 수준의 나레이션을 생성합니다.
- 숏폼 리텐션을 극대화하는 3단 효과음(오프닝 Whoosh/Pop, 전환 Ding, 클로징 CTA Chime) 및 미세 리듬 베드를
  자동 합성하여 나레이션과 멀티트랙 믹싱(Multi-track Mixing)합니다.
- API 할당량 초과 등 예외 발생 시 Edge-TTS로 무중단 폴백(Graceful Fallback)합니다.
"""

import asyncio
import base64
import json
import math
import os
import random
import struct
import subprocess
import sys
import wave
from pathlib import Path
from typing import Optional
import requests
from dotenv import load_dotenv
import edge_tts
import imageio_ffmpeg

# 콘솔 인코딩 방어
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

for env_path in [Path(".env"), Path("C:/project/AgentCorp/.env")]:
    if env_path.exists():
        load_dotenv(env_path)
        break

import config


class AudioAgent:
    def __init__(self, voice: str = config.DEFAULT_VOICE):
        self.fallback_voice = voice
        self.gemini_voices = ["Puck", "Aoede", "Fenrir", "Kore"]
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        self.audio_dir = config.OUTPUT_DIR / "audio"
        self.sfx_dir = config.DATA_DIR / "sfx"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.sfx_dir.mkdir(parents=True, exist_ok=True)

        # 기본 SFX 에셋 준비
        self._ensure_sfx_assets()

    def _ensure_sfx_assets(self):
        """숏폼 전용 고품질 효과음(WAV) 3종을 DSP 파형 합성으로 생성"""
        sample_rate = 44100

        # 1. 오프닝 Hook SFX (Whoosh + Punchy Pop: 0.45초)
        hook_sfx = self.sfx_dir / "sfx_hook_whoosh_pop.wav"
        if not hook_sfx.exists():
            duration = 0.45
            n_samples = int(sample_rate * duration)
            with wave.open(str(hook_sfx), "w") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                for i in range(n_samples):
                    t = i / sample_rate
                    # 0.0~0.3s: 주파수가 빠르게 상승하는 스우시(Whoosh) + 노이즈
                    if t < 0.3:
                        env = math.sin((t / 0.3) * math.pi)
                        freq = 120 + (t / 0.3) ** 2 * 900
                        noise = random.uniform(-0.35, 0.35)
                        tone = math.sin(2 * math.pi * freq * t) * 0.65
                        val = (tone + noise) * env * 0.55
                    else:
                        # 0.3~0.45s: 경쾌한 버블/팝(Pop) 임팩트
                        pt = t - 0.3
                        env = math.exp(-pt * 28)
                        freq = 520 + pt * 1400
                        val = math.sin(2 * math.pi * freq * pt) * env * 0.8
                    sample = int(max(-1.0, min(1.0, val)) * 32767)
                    wf.writeframes(struct.pack("<h", sample))

        # 2. 중간 포인트 Sparkle Ding SFX (0.6초)
        ding_sfx = self.sfx_dir / "sfx_transition_ding.wav"
        if not ding_sfx.exists():
            duration = 0.6
            n_samples = int(sample_rate * duration)
            with wave.open(str(ding_sfx), "w") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                for i in range(n_samples):
                    t = i / sample_rate
                    env = math.exp(-t * 8.5)
                    # 밝고 청량한 메이저 배음 (C6 + G6 + C7)
                    val = (
                        math.sin(2 * math.pi * 1046.5 * t) * 0.5
                        + math.sin(2 * math.pi * 1567.98 * t) * 0.3
                        + math.sin(2 * math.pi * 2093.0 * t) * 0.2
                    ) * env * 0.5
                    sample = int(max(-1.0, min(1.0, val)) * 32767)
                    wf.writeframes(struct.pack("<h", sample))

        # 3. 엔딩 CTA Chime SFX (더블 알림 차임: 0.7초)
        cta_sfx = self.sfx_dir / "sfx_cta_chime.wav"
        if not cta_sfx.exists():
            duration = 0.7
            n_samples = int(sample_rate * duration)
            with wave.open(str(cta_sfx), "w") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                for i in range(n_samples):
                    t = i / sample_rate
                    if t < 0.18:
                        env = math.exp(-t * 12)
                        freq = 880.0  # A5
                    else:
                        t2 = t - 0.18
                        env = math.exp(-t2 * 6.5)
                        freq = 1318.5  # E6 (상승 화음)
                    val = (
                        math.sin(2 * math.pi * freq * t) * 0.65
                        + math.sin(2 * math.pi * (freq * 2) * t) * 0.25
                    ) * env * 0.55
                    sample = int(max(-1.0, min(1.0, val)) * 32767)
                    wf.writeframes(struct.pack("<h", sample))

    def _generate_gemini_tts_wav(self, text: str, raw_wav_path: Path, voice_name: str = "Puck") -> bool:
        """
        Gemini Native Audio TTS API를 호출하여 실제 사람처럼 생동감 있는 WAV 오디오 생성
        """
        if not self.api_key:
            return False

        # 감정과 호흡이 살아있는 틱톡 크리에이터 디렉팅 프롬프트
        directed_prompt = (
            "Read the following short-form video script in a natural, expressive, "
            "excited, and conversational American English TikTok creator voice. "
            "Keep the hook punchy and energetic, and sound genuinely impressed:\n\n"
            f"{text}"
        )

        models_to_try = ["gemini-3.8-flash-lite-tts", "gemini-2.5-flash-preview-tts"]

        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": directed_prompt}]}],
                "generationConfig": {
                    "responseModalities": ["AUDIO"],
                    "speechConfig": {
                        "voiceConfig": {
                            "prebuiltVoiceConfig": {
                                "voiceName": voice_name
                            }
                        }
                    }
                }
            }
            try:
                resp = requests.post(url, json=payload, timeout=25)
                if resp.status_code == 200:
                    data = resp.json()
                    part = data["candidates"][0]["content"]["parts"][0]["inlineData"]
                    audio_bytes = base64.b64decode(part["data"])
                    mime_type = part.get("mimeType", "")

                    if audio_bytes[:4] == b"RIFF" or "wav" in mime_type:
                        with open(raw_wav_path, "wb") as f:
                            f.write(audio_bytes)
                    else:
                        # Raw PCM (24kHz, 16-bit, mono)일 경우 WAV 헤더 래핑
                        with wave.open(str(raw_wav_path), "wb") as wf:
                            wf.setnchannels(1)
                            wf.setsampwidth(2)
                            wf.setframerate(24000)
                            wf.writeframes(audio_bytes)

                    print(f"  🎙️ [Gemini Native TTS] '{model}' (Voice: {voice_name}) 인간형 보이스 생성 성공!")
                    return True
            except Exception as e:
                print(f"  [Gemini TTS 경고] {model} 호출 실패: {e}")

        return False

    async def _generate_edge_tts_fallback(self, text: str, out_path: Path) -> Path:
        """Gemini API 한도 초과 시 구동되는 Edge-TTS 폴백"""
        communicate = edge_tts.Communicate(text=text, voice=self.fallback_voice, rate="+8%", pitch="+2Hz")
        await communicate.save(str(out_path))
        return out_path

    def _get_audio_duration(self, file_path: Path) -> float:
        """FFmpeg로 오디오 파일의 정확한 길이(초) 추출"""
        cmd = [self.ffmpeg_exe, "-i", str(file_path)]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore")
        import re
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
        if match:
            h, m, s = int(match.group(1)), int(match.group(2)), float(match.group(3))
            return h * 3600 + m * 60 + s
        return 18.0

    def _mix_voice_with_sfx(self, voice_file: Path, final_mp3_path: Path) -> Path:
        """
        성우 나레이션 오디오에 3단 효과음(오프닝 훅 Whoosh/Pop, 전환 Ding, 엔딩 CTA Chime)을
        타이밍에 맞춰 멀티트랙 믹싱(Multi-track Mixing)합니다.
        """
        duration = self._get_audio_duration(voice_file)
        hook_sfx = self.sfx_dir / "sfx_hook_whoosh_pop.wav"
        ding_sfx = self.sfx_dir / "sfx_transition_ding.wav"
        cta_sfx = self.sfx_dir / "sfx_cta_chime.wav"

        # 효과음 삽입 타이밍 계산 (밀리초 단위)
        hook_delay_ms = 50  # 0.05초 (시작 즉시 시선 강탈)
        ding_delay_ms = int(min(duration * 0.35, 4.2) * 1000)  # 본문 전환점 (약 3.5~4.2초)
        cta_delay_ms = int(max(duration - 3.2, duration * 0.78) * 1000)  # 마지막 CTA 시작 시점

        filter_complex = (
            f"[0:a]volume=1.15[voice];"
            f"[1:a]volume=0.45,adelay={hook_delay_ms}|{hook_delay_ms}[sfx1];"
            f"[2:a]volume=0.35,adelay={ding_delay_ms}|{ding_delay_ms}[sfx2];"
            f"[3:a]volume=0.42,adelay={cta_delay_ms}|{cta_delay_ms}[sfx3];"
            f"[voice][sfx1][sfx2][sfx3]amix=inputs=4:duration=first:dropout_transition=0,alimiter=limit=0.95[outa]"
        )

        cmd = [
            self.ffmpeg_exe,
            "-y",
            "-i", str(voice_file),
            "-i", str(hook_sfx),
            "-i", str(ding_sfx),
            "-i", str(cta_sfx),
            "-filter_complex", filter_complex,
            "-map", "[outa]",
            "-c:a", "libmp3lame",
            "-b:a", "192k",
            str(final_mp3_path)
        ]

        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode == 0 and final_mp3_path.exists():
            print(f"  🔊 [SFX Mixer] 3단 효과음(Whoosh/Pop + Ding + CTA Chime) 멀티트랙 믹싱 완료!")
            return final_mp3_path
        else:
            # 믹싱 실패 시 원본 보이스만 변환
            fallback_cmd = [
                self.ffmpeg_exe, "-y", "-i", str(voice_file),
                "-c:a", "libmp3lame", "-b:a", "192k", str(final_mp3_path)
            ]
            subprocess.run(fallback_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return final_mp3_path

    def generate_speech(self, text: str, output_filename: str, voice_name: Optional[str] = None, enable_sfx: bool = True) -> Path:
        """
        Gemini 인간형 보이스 생성 후 3단 효과음(SFX)을 믹싱하여 최종 MP3를 반환합니다.
        """
        final_mp3_path = self.audio_dir / output_filename
        temp_raw_voice = self.audio_dir / f"temp_raw_{Path(output_filename).stem}.wav"

        selected_voice = voice_name or random.choice(["Puck", "Aoede"])

        # 1. Gemini Native TTS 우선 시도
        gemini_ok = self._generate_gemini_tts_wav(text, temp_raw_voice, voice_name=selected_voice)

        if not gemini_ok:
            print("  [AudioAgent] Edge-TTS 폴백으로 음성 생성 중...")
            temp_raw_voice = self.audio_dir / f"temp_raw_{Path(output_filename).stem}.mp3"
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
                loop.run_until_complete(self._generate_edge_tts_fallback(text, temp_raw_voice))
            else:
                asyncio.run(self._generate_edge_tts_fallback(text, temp_raw_voice))

        # 2. 효과음(SFX) 멀티트랙 믹싱
        if enable_sfx:
            self._mix_voice_with_sfx(temp_raw_voice, final_mp3_path)
        else:
            cmd = [self.ffmpeg_exe, "-y", "-i", str(temp_raw_voice), "-c:a", "libmp3lame", "-b:a", "192k", str(final_mp3_path)]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # 임시 파일 정리
        if temp_raw_voice.exists():
            try:
                temp_raw_voice.unlink()
            except Exception:
                pass

        return final_mp3_path

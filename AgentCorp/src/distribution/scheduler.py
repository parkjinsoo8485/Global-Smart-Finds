"""
src/distribution/scheduler.py
인간적인 불규칙성(Jitter)을 적용한 미국 골든타임 소셜 업로드 스케줄러
"""

import random
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional
import zoneinfo


class AccountPhase(str, Enum):
    WARMUP = "warmup"      # 1주차: 하루 1회 업로드 (봇 의심 차단)
    GROWTH = "growth"      # 2~3주차: 하루 2회 업로드
    MATURE = "mature"      # 4주차 이후: 하루 최대 3회 업로드


class GoldenTimeSlot:
    """미국 시청자 기준 최적의 참여 시간대 (US Eastern Time 기준)"""
    MORNING_COMMUTE = 8    # 출근길 (08:00 EST)
    LUNCH_BREAK = 12       # 점심시간 (12:30 EST)
    EVENING_PRIME = 19     # 저녁 골든타임 (19:00 EST)
    NIGHT_SCROLL = 21      # 취침 전 피드 탐색 (21:30 EST)


class SmartUploadScheduler:
    """SNS_ANTI_BAN_GUIDELINES을 준수하는 지능형 스케줄러"""

    def __init__(self, target_tz: str = "America/New_York", local_tz: str = "Asia/Seoul"):
        try:
            self.us_tz = zoneinfo.ZoneInfo(target_tz)
        except Exception:
            # Fallback for systems without tzdata
            self.us_tz = timezone(timedelta(hours=-5))
            
        try:
            self.local_tz = zoneinfo.ZoneInfo(local_tz)
        except Exception:
            self.local_tz = timezone(timedelta(hours=9))

    def calculate_next_upload_slot(
        self,
        phase: AccountPhase = AccountPhase.GROWTH,
        slot_index: int = 0,
        jitter_minutes: int = 20,
        base_date: Optional[datetime] = None
    ) -> Dict[str, datetime]:
        """미국 골든타임에 ±jitter_minutes 오차를 준 예약 시각을 산출합니다.

        Args:
            phase: 계정 성장 단계
            slot_index: 당일 업로드 순번 (0: 1차, 1: 2차, 2: 3차)
            jitter_minutes: 인간적인 불규칙 오차 범위 (기본 ±20분)
            base_date: 기준 일시 (기본: 현재)

        Returns:
            Dict containing 'us_time' (미국 현지시간) and 'local_time' (한국 시간)
        """
        now_us = datetime.now(self.us_tz) if base_date is None else base_date.astimezone(self.us_tz)
        
        # 단계별 허용 슬롯 시간대 (EST 기준)
        if phase == AccountPhase.WARMUP:
            target_hours = [GoldenTimeSlot.EVENING_PRIME]  # 저녁 7시 1회 집중
        elif phase == AccountPhase.GROWTH:
            target_hours = [GoldenTimeSlot.LUNCH_BREAK, GoldenTimeSlot.EVENING_PRIME]
        else:
            target_hours = [GoldenTimeSlot.LUNCH_BREAK, GoldenTimeSlot.EVENING_PRIME, GoldenTimeSlot.NIGHT_SCROLL]

        target_hour = target_hours[min(slot_index, len(target_hours) - 1)]

        # 오늘 해당 시간
        candidate_time = now_us.replace(hour=target_hour, minute=0, second=0, microsecond=0)

        # 인간적인 랜덤 오차(Jitter) 주입 (-jitter ~ +jitter)
        jitter = random.randint(-jitter_minutes, jitter_minutes)
        scheduled_us = candidate_time + timedelta(minutes=jitter)

        # 이미 지난 시각이라면 다음날로 예약
        if scheduled_us <= now_us:
            scheduled_us += timedelta(days=1)

        scheduled_local = scheduled_us.astimezone(self.local_tz)

        return {
            "us_time": scheduled_us,
            "local_time": scheduled_local,
            "jitter_applied_minutes": jitter,
            "target_hour": target_hour
        }

    def generate_daily_schedule(
        self,
        phase: AccountPhase = AccountPhase.GROWTH,
        items_count: int = 2
    ) -> List[Dict[str, datetime]]:
        """당일 업로드할 항목들에 대한 전체 스케줄 리스트를 생성합니다."""
        schedules = []
        max_allowed = 1 if phase == AccountPhase.WARMUP else (2 if phase == AccountPhase.GROWTH else 3)
        actual_count = min(items_count, max_allowed)

        for i in range(actual_count):
            slot = self.calculate_next_upload_slot(phase=phase, slot_index=i)
            schedules.append(slot)

        # 시간순 정렬
        schedules.sort(key=lambda s: s["us_time"])
        return schedules


# AgentCorp Roadmap & Execution Checklist

- **최종 업데이트**: 2026-11-05
- **현재 진행 단계**: `Phase 2·3·4·6 전 과정 무인 자동화 오케스트레이터 구축 완료 (Gemini Native TTS 성우 + 3단 효과음 SFX 믹싱 + 실사 비디오 합성 + 카카오톡 브리핑)`

---

## 단계별 마일스톤 (Autonomous Roadmap)

### [x] Phase 1: 기반 인프라 & 제휴 파트너 준비
- [x] AliExpress Portals 계정 및 트래킹 ID(`bio-search`) 발급·연동 완료
- [ ] 글로벌 타겟 소셜 채널 개설 (YouTube Shorts, TikTok, Pinterest)
- [x] 프로필용 바이오 링크(`index.html` - `#번호` 실시간 검색 & 카테고리 필터) 구축 완료
- [x] SNS 계정 정지 및 섀도우밴 방지 가이드라인 수립 ([`SNS_ANTI_BAN_GUIDELINES.md`](file:///c:/project/AgentCorp/SNS_ANTI_BAN_GUIDELINES.md))

### [x] Phase 2: [MD팀] 알리익스프레스 상품 소싱 & AI 바이럴/컴플라이언스 분석기
- [x] 알리익스프레스 핫딜/슈퍼딜 메타데이터 파서 및 데이터 모델 설계 (`ProductItem`)
- [x] 1차 정량적 바이럴 필터링 (충동구매 가격대 $5~$35, 평점 4.5+, 주문 300+, 데모 비디오 100점 만점 스코어링)
- [x] **[신규] Google Antigravity SDK (`gemini-3.5-flash-lite`) 연동 AI 심층 분석기 탑재**
  - 숏폼 피드에서 터지는 핵심 시각 요소(`viral_factor`) 자동 추론
  - 상표권 도용 및 정책 위반 위험(`anti_ban_risk`) 사전 점검
  - 제작팀 전용 추천 3초 훅 촬영 앵글(`recommended_hook_angle`) 및 타겟 페르소나 도출
- [x] 소싱 결과 자동 제휴 링크 결합 및 JSON 데이터베이스(`data/sourced_products.json`) 저장 연동
- [x] 무중단 운영을 위한 Graceful Fallback(룰 기반 템플릿) 내장

### [x] Phase 3: [마케팅·제작팀] AI 영문 대본 및 숏폼 영상 완전 자동 생성 엔진
- [x] **[신규] Google Antigravity SDK (`gemini-3.5-flash-lite`) 기반 자율 카피라이터 (`CopywriterAgent`)**
  - 3초 시선 강탈 훅(Pattern Interrupt, Curiosity Gap, Relatable Frustration) 맞춤 생성
  - 마이크로 클리프행어(Micro-cliffhangers) 구조의 원어민 숏폼 구어체 대본 자동 작성
  - FTC 규정 태그(#ad, #commissionsearned) 및 고효율 해시태그 풀 최적화
  - API 할당량 초과 또는 네트워크 오류 시 무중단 룰 기반 엔진으로 자가 복구(Self-Healing)
- [x] **[고도화] Gemini Native Audio TTS (`gemini-3.8-flash-lite-tts` / `Puck`, `Aoede`, `Fenrir`) 인간형 성우 나레이션 엔진 (`AudioAgent`)**
  - 실제 미국 Z세대 틱톡커의 호흡·억양·감정선이 살아있는 하이퍼 리얼리스틱 음성 합성 (Edge-TTS 자동 폴백 지원)
- [x] **[고도화] 3단 입체 효과음(SFX) DSP 파형 합성 및 FFmpeg 멀티트랙 오디오 믹싱**
  - 오프닝 0.0초 `Whoosh + Pop` 훅 효과음 (`data/sfx/sfx_hook_whoosh_pop.wav`)
  - 중반부(45% 지점) `Crystal Ding` 화면 전환 효과음 (`data/sfx/sfx_transition_ding.wav`)
  - 엔딩 CTA(종료 1.8초 전) `Harmonic Chime` 구매 유도 효과음 (`data/sfx/sfx_cta_chime.wav`)
- [x] 알리익스프레스 및 `yt-dlp` 기반 실제 사람 손동작 라이브 시연 동영상(MP4) 자동 검색·다운로더 (`AliExpressVideoDownloader`)
- [x] 실제 움직이는 동영상 기반 9:16 앰비언트 블러(Ambient Blur) 듀얼 레이어 + 투명 HUD 오버레이 합성 렌더러 완성 (`VideoAgent`)
- [x] **[고도화] 초반/중간 무의미한 타이틀 카드·정적 안내 이미지 자동 컷편집(`sanitize_raw_video`) 및 0.0초 하이라이트 선배치 규칙 수립** ([`VIDEO_PRODUCTION_RULES.md`](file:///c:/project/AgentCorp/VIDEO_PRODUCTION_RULES.md))
- [x] 정적인 느낌 완전 탈피: 상품별 1:1 실사 모션 비디오와 Gemini 인간형 음성 + 3단 효과음 동기화 렌더링 완료

### [x] Phase 4: [영업·배포팀] 소셜 자동 배포 및 제휴 링크 매핑
- [x] 미국 시청자 골든타임(저녁 6~9시) 기준 지터(±20분 랜덤 오차) 자동 스케줄러 개발 (`scheduler.py`)
- [x] 업로드 큐(Queue) 관리 및 메타데이터 자동 매핑 (`publisher.py`, `data/upload_queue.json`)
- [x] 영상 고정 댓글 및 프로필 링크에 제휴 링크(#ad, #commissionsearned) 자동 매핑
- [x] 소셜 배포 파이프라인과 PlayMCP 카카오톡 일일/실시간 보고 연동 (`distribution_pipeline.py`)

### [ ] Phase 5: [재무·분석실] 성과 트래킹 & 자율 최적화 (CFO Agent)
- [ ] 채널별 조회수, 링크 클릭률(CTR), 수수료 수익 집계 모듈
- [ ] 저성과 카테고리 자동 도태 및 고수익 상품군 소싱 가중치 자율 반영
- [ ] Antigravity Agent SDK 기반 일일/주간 성과 자동 리포팅 및 전략 피드백 루프

### [x] Phase 6: [총괄 기획실] 24/7 완전 무인 오케스트레이션 & 대표 일일 보고
- [x] 전 부서 에이전트 24/7 자동 순환 실행 마스터 오케스트레이터 ([`main_orchestrator.py`](file:///c:/project/AgentCorp/main_orchestrator.py)) 및 원클릭 실행 배치 파일 ([`run_daily_automation.bat`](file:///c:/project/AgentCorp/run_daily_automation.bat))
- [x] 예외 상황 자율 복구(Self-healing) 및 작업 로그 시스템
- [x] 대표님 스마트폰(카카오톡 나와의 채팅방)으로 일일 완료 브리핑 자율 발송

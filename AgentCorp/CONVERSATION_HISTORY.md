# AgentCorp: 전체 대화 기록 및 프로젝트 개발 일지 (Full Conversation & Development Log)

- **작성 일자**: 2026-10-30
- **프로젝트 명**: AgentCorp (Global Autonomous AI Affiliate Corporation)
- **GitHub 저장소**: `https://github.com/parkjinsoo8485/Global-Smart-Finds.git`
- **프로젝트 위치**: `c:\project\AgentCorp`

---

## 1. 초기 비즈니스 모델 탐색 및 결정

### 사용자 질문:
> *"지금부터 에이전트 회사를 운영하려고 하는데 어떤 회사를 운영하는 것이 좋겠니? 수익을 낼 수 있는 회사를 추천해줘."*

### AI 제안 (4대 비즈니스 모델):
1. **B2B 세일즈 & 리드 발굴 에이전트** (기업 대상 영업 자동화)
2. **버티컬 마이크로 SaaS** (정부지원사업/R&D 제안서 자동화)
3. **AI 자동화 에이전시 (AAA)** (중소기업 업무 자동화 파이프라인 구축 외주)
4. **1인 자율 운영 제휴 마케팅 (Affiliate Marketing)** (SNS 트래픽 기반 패시브 인컴)

### 사용자 피드백 & 비즈니스 모델 확정:
> *"물건을 판매하는 링크를 sns에 뿌려서 구매고객이 발생하면 수익이 나는 그런 것이 있다고 하던데"*  
> *"글로벌 무대에서 진행해보도록 하자. 모든 단계를 그려줘."*  
> *"알리익스프레스부터 시작해 보자."*

- **확정된 비즈니스**: **글로벌 알리익스프레스 제휴 마케팅 (AliExpress Portals Affiliate)**
- **선정 이유**:
  - 아마존 대비 높은 수수료율 (3% ~ 최대 50%)
  - 가입 및 승인 장벽이 낮고 전 세계 글로벌 무료/저가 배송 지원
  - 상세페이지 내 풍부한 시연 동영상 소스 확보 용이

---

## 2. 완전 자율 에이전트 기업(Autonomous Agent Corp) 체제 수립

### 사용자 요청:
> *"지금 에이전트 회사를 운영하려고 하는거야 맞지? 완전 자율 에이전트 회사를 운영하려고 하니, 필요한 로드맵을 추가해주고 보완해줘. 다음단계는 뭐지?"*

### 사내 가상 조직도 확립:
- **소유주 (Chairman/Human-in-the-Loop)**: 최종 의사결정 및 정산
- **총괄 CEO 에이전트 (`main_orchestrator.py`)**: 24/7 파이프라인 지휘, 부서 조율, 일일 경영 브리핑 전송
- **MD/상품기획팀 (`Sourcing Agent`)**: 알리 핫딜 발굴 및 100점 만점 바이럴 스코어링
- **마케팅/카피팀 (`Copywriter Agent`)**: 미국 숏폼 3초 훅 대본 및 캡션 생성
- **미디어/제작팀 (`Audio Agent` & `Video Agent`)**: 미국 원어민 TTS + 영상 자동 편집 및 HUD 합성
- **영업/퍼블리싱팀 (`Publisher Agent`)**: 미국 시간대 자동 스케줄링 및 제휴 링크 매핑
- **재무/성과분석실 (`CFO Agent`)**: CTR, 전환율 분석 및 저성과 상품 도태 피드백

---

## 3. SNS 계정 정지 및 섀도우밴 방지(Anti-Ban) 규칙 수립

### 사용자 요청:
> *"마케팅을 에이전트에서 만드는 것이 다른 sns에 블락되거나 계정정지 되지 않도록 하는 규칙을 만들어줘. 어떻게 해야 계정이 중지되지 않고 잘 될 수 있는지 면밀하게 조사해서 md파일로 만들어줘."*

### 결과물: [`SNS_ANTI_BAN_GUIDELINES.md`](file:///c:/project/AgentCorp/SNS_ANTI_BAN_GUIDELINES.md)
- **4대 절대 수칙**:
  1. **영상 고유 해시 변형**: 원본 그대로 재사용 금지. 앰비언트 블러 듀얼 레이어 + 미세 속도 조절 + AI 음성 + BGM.
  2. **댓글 링크 도배 금지**: 프로필 바이오 링크(Link-in-Bio)로만 유도.
  3. **인간적 스케줄링 (Human Jittering)**: ±15~30분 랜덤 오차 적용.
  4. **FTC 법적 고지 강제**: 미국 소비자법 준수를 위해 `#ad`, `#commissionsearned` 필수 자동 삽입.

---

## 4. Phase 2: [MD팀] 꿀템 소싱 에이전트 개발

- **코드 파일**: [`src/sourcing/aliexpress_sourcing.py`](file:///c:/project/AgentCorp/src/sourcing/aliexpress_sourcing.py)
- **바이럴 스코어링 알고리즘 (100점 만점)**:
  - 충동구매 가격대 ($5 ~ $35): +30점
  - 최상위 평점 (★4.5 이상): +20~25점
  - 검증된 주문량 (300건 이상): +15~25점
  - 시연 데모 비디오 확보: +20점
- **선별 데이터베이스**: [`data/sourced_products.json`](file:///c:/project/AgentCorp/data/sourced_products.json) 저장 완료

---

## 5. Phase 3: [마케팅·제작팀] 반복 피드백 및 정밀 개선 과정

홍보 영상 제작 과정에서 대표님의 정밀한 피드백을 반영하여 총 3차례에 걸친 대대적인 전면 개편이 이루어졌습니다:

### 1차 시도 및 문제점:
- **사용자 피드백**: *"제품에 대한 영상으로는 적절하지 않은데 다시 생각해봐."* (스크린샷 첨부)
- **원인 분석**: 텍스트 카드뉴스 형태로 렌더링되어 제품 실물이 전혀 보이지 않고 글자 잘림 발생.
- **조치**: 제품 실물 사진을 중앙에 65% 이상 배치하고 배경 앰비언트 블러 적용.

### 2차 시도 및 문제점:
- **사용자 피드백**: *"이것이 무선 에어건이니? 홍보 영상을 만드는 것이 제일 중요한 작업중에 하나라고 생각해. 정밀 수정해."* (스크린샷 첨부)
- **원인 분석**:
  1. 무선 에어건 제품인데 일반 키보드 사진이 들어감.
  2. Windows 기본 폰트에서 이모지가 네모 박스(`□`)로 깨져서 출력됨.
  3. 하단 상품명 끝부분 잘림.
- **조치**:
  1. `image-generator` 서브에이전트를 가동하여 **실제 초강력 무선 터보 에어건(Handheld Jet Air Duster) 실물 비주얼** 및 **회전하는 커피 소용돌이 머그잔 비주얼** 생성 및 매칭.
  2. 이모지 대신 순수 영문 타이포그래피(`HOT VIRAL GADGET FIND`, `RATING: 4.8`, `>> TAP LINK IN BIO TO SHOP <<`)로 교체하여 네모 박스 100% 제거.
  3. 동적 텍스트 줄바꿈으로 상품명 전체가 선명하게 출력되도록 수정.

### 3차 시도 및 문제점:
- **사용자 피드백**: *"그런데 알리에 있는 동영상을 다운받아서 자동 편집하면 좋겠는데 너무 정적이야."*
- **조치**:
  1. **알리 동영상 다운로더 개발**: [`src/sourcing/aliexpress_video_downloader.py`](file:///c:/project/AgentCorp/src/sourcing/aliexpress_video_downloader.py)
  2. **동영상 듀얼 레이어 컷편집 & 투명 HUD 렌더러 완성**: [`src/creative/video_generator.py`](file:///c:/project/AgentCorp/src/creative/video_generator.py)
  3. **검증 완료**: 뒤에서 실제 에어건/머그잔이 작동하는 모션 비디오가 재생되고, 그 위에 투명 HUD가 얹어지며, 미국 원어민 AI 음성이 완벽하게 동기화됨.

---

## 6. 현재 프로젝트 파일 구조 (Project Structure)

```
c:\project\AgentCorp\
├── .gitignore
├── config.py                               # 전역 설정 및 환경 변수
├── requirements.txt                        # 필수 라이브러리 목록
├── README.md                               # 기업 개요 및 아키텍처 명세서
├── ROADMAP.md                              # 마일스톤 및 진척도 체크리스트
├── SNS_ANTI_BAN_GUIDELINES.md              # 계정 정지 및 섀도우밴 방지 4대 절대 수칙
├── AgentCorp_Business_Plan.md              # 초기 비즈니스 기획서
├── CONVERSATION_HISTORY.md                 # 본 개발 일지 및 대화 요약서
│
├── data/
│   ├── sourced_products.json               # 선별된 알리익스프레스 꿀템 DB
│   ├── real_air_duster.jpg                 # 무선 에어건 실물 사진
│   ├── real_stirring_mug.jpg               # 자동 회전 머그잔 실물 사진
│   ├── air_duster_motion.mp4               # 무선 에어건 모션 비디오
│   └── stirring_mug_motion.mp4             # 자동 머그잔 모션 비디오
│
├── src/
│   ├── sourcing/
│   │   ├── aliexpress_sourcing.py          # [MD팀] 꿀템 발굴 & 바이럴 스코어링
│   │   └── aliexpress_video_downloader.py  # [MD팀] 알리 시연 동영상 추출기
│   │
│   └── creative/
│       ├── copywriter.py                   # [마케팅팀] 바이럴 대본 & FTC 태그 생성
│       ├── audio_generator.py              # [제작팀] Edge-TTS 미국 원어민 성우 MP3
│       ├── video_generator.py              # [제작팀] 동영상 컷편집 & HUD 렌더러
│       └── creative_pipeline.py            # [제작팀] 대본+음성+영상 원클릭 파이프라인
│
└── output/
    ├── audio/                              # 생성된 나레이션 MP3 파일들
    ├── cards/                              # 렌더링된 HUD 투명 오버레이
    ├── creatives/                          # 콘텐츠 메타데이터 JSON
    ├── verification_frames/                # 비디오 추출 검증 스크린샷 JPG
    └── videos/                             # 최종 완성된 세로형 숏폼 MP4 비디오
```

---

## 7. 향후 예정 단계 (Next Steps)

- **Phase 4: [영업·배포팀] 스케줄러 & 업로더 에이전트 (`Publisher Agent`)**
  - 미국 현지 저녁 골든타임 기준 ±20분 지터(랜덤 오차) 스케줄러 개발
  - 유튜브 쇼츠, 틱톡, 핀터레스트 자동 업로드 큐 연동
- **Phase 5: [재무팀] 성과 트래킹 & 자율 최적화 (`CFO Agent`)**
- **Phase 6: [총괄실] 24/7 완전 무인 오케스트레이터 & 대표 일일 보고 브리핑**

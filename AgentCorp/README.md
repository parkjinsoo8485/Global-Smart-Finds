# AgentCorp: Global AI Affiliate Agent System

> **완전 자율 운영(Fully Autonomous) 글로벌 제휴 마케팅 AI 에이전트 회사**

## 1. 프로젝트 비전 (Vision)
- **타겟 시장**: 글로벌(미국/영미권 및 글로벌 배송 타겟, 결제 통화 USD)
- **비즈니스 모델**: **알리익스프레스 어필리에이트 (AliExpress Portals)** 우선 런칭 ➔ 추후 아마존 확장
- **선정 이유**: 
  - 아마존 대비 높은 수수료율 (3% ~ 최대 50% 핫딜)
  - 상세페이지 내 풍부한 시연 영상/데모 소스 (숏폼 제작에 최적)
  - 가입 승인 장벽이 낮고 전 세계 글로벌 무료/저가 배송 지원
- **운영 형태**: 1인 소유, 5대 전문 가상 에이전트 군단 기반 24/7 무인 자동화

---

## 2. 사내 에이전트 조직도 (Autonomous Corporate Structure)

```
                     [ 대표님 (Owner / Human-in-the-Loop) ]
                                      │ (경영 보고 확인 & 최종 의사결정)
                     [ 총괄 CEO 에이전트 (Orchestrator) ]
                                      │
     ┌──────────────────┬─────────────┴───────┬──────────────────┐
     ▼                  ▼                     ▼                  ▼
[MD/상품기획팀]   [마케팅/카피팀]       [미디어/제작팀]     [영업/배포팀]
Sourcing Agent   Copywriter Agent      Media Render Agent   Publisher Agent
(알리 꿀템 발굴)   (미국 바이럴 대본)    (TTS+영상+자막)     (SNS 자동 발행)
     │                  │                     │                  │
     └──────────────────┴─────────────┬───────┴──────────────────┘
                                      ▼
                         [재무/성과분석실 (CFO)]
                         Analytics & Finance Agent
                         (수익 집계, 텔레그램 일일 보고)
```

### 사내 부서별 핵심 R&R
1. **총괄 기획실 (CEO/Orchestrator)**: 24/7 파이프라인 스케줄링, 부서 간 업무 조율, 일일 경영 브리핑 전송
2. **MD/상품기획팀 (Sourcing Agent)**: 알리익스프레스 실시간 핫딜 크롤링 및 바이럴 점수(Viral Score) 산출
3. **마케팅/카피팀 (Copywriter Agent)**: 영미권 숏폼 후킹 공식(3초 룰) 기반 대본 및 해시태그 생성
4. **미디어/제작팀 (Media Agent)**: 미국 원어민 음성(TTS) 합성, 제품 데모 비디오 컷편집 및 다이내믹 자막 결합
5. **영업/퍼블리싱팀 (Publisher Agent)**: 미국 골든타임 자동 스케줄링 및 제휴 고유 링크/바이오 링크 매핑
6. **재무/성과분석실 (CFO Agent)**: 클릭률(CTR), 구매 전환율, 정산 수수료 트래킹 및 고수익 카테고리 자율 피드백

---

## 3. 기술 스택 및 안전 규정 (Tech Stack & Safety Rules)
- **Language**: Python 3.10+
- **Agent Framework**: LangChain / LangGraph (Orchestration)
- **LLM**: Gemini API
- **Media Engine**: MoviePy / FFmpeg / Edge-TTS
- **Platforms**: AliExpress Portals, YouTube Data API, Pinterest API
- **보안/계정 안전 규정**: [`SNS_ANTI_BAN_GUIDELINES.md`](file:///c:/project/AgentCorp/SNS_ANTI_BAN_GUIDELINES.md) (스팸 차단 및 섀도우밴 방지 4대 절대 수칙)


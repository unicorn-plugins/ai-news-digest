---
name: run-daily-digest
description: AI 뉴스레터 발행 (메인 기능) - RSS 수집부터 이메일 발송까지 전체 워크플로우 실행
type: orchestrator
user-invocable: true
---

# AI 뉴스레터 발행

[AI News Digest 뉴스레터 발행 시작]

## 목표

9개 RSS 피드에서 AI 관련 최신 뉴스를 수집하여 중복 제거, 요약, 번역 후
HTML 뉴스레터를 생성하고 수신자에게 이메일로 발송하는 전체 워크플로우를 실행합니다.

## 활성화 조건

- 사용자가 "뉴스레터 발행", "AI 뉴스 다이제스트 실행", "/ai-news-digest:run-daily-digest" 요청
- cron job에 의한 매일 오전 8시 자동 실행
- 수동으로 뉴스레터 발행이 필요한 경우

## 워크플로우

### Step 1: 전체 워크플로우 조율 → Agent: orchestrator
`/oh-my-claudecode:ralph`을 활용하여 완료 보장:
- **TASK**: 6단계 AI 뉴스레터 발행 워크플로우 전체 조율 및 실행
- **EXPECTED OUTCOME**: 뉴스레터 발행 완료 및 이메일 발송 성공
- **MUST DO**: 각 단계 성공/실패 판단, 에러 시 최대 3회 재시도, 에러 로그 저장 및 알림
- **MUST NOT DO**: 개별 RSS 수집이나 콘텐츠 처리 직접 수행
- **CONTEXT**: orchestrator 에이전트가 다음 하위 에이전트들을 순차 호출

#### Phase 1: 데이터 수집 및 처리
1. collector 에이전트 호출 → RSS 피드에서 24시간 이내 뉴스 수집
2. content-processor 에이전트 호출 → 중복 제거 + Groq API 요약 + 한국어 번역

#### Phase 2: 데이터 저장 및 뉴스레터 생성
3. data-manager 에이전트 호출 → PostgreSQL에 뉴스 항목 저장
4. newsletter-publisher 에이전트 호출 → HTML 뉴스레터 생성
5. newsletter-publisher 에이전트 호출 → Gmail SMTP 이메일 발송

#### Phase 3: 후처리 및 에러 관리
6. data-manager 에이전트 호출 → 뉴스레터 발행 기록 저장
7. 에러 발생 시: data-manager → 에러 로그 저장, newsletter-publisher → 관리자 알림

### 에이전트 호출 규칙

**에이전트 FQN 목록**:
- `ai-news-digest:orchestrator:orchestrator` (HIGH 티어)
- `ai-news-digest:collector:collector` (MEDIUM 티어)
- `ai-news-digest:content-processor:content-processor` (MEDIUM 티어)
- `ai-news-digest:data-manager:data-manager` (LOW 티어)
- `ai-news-digest:newsletter-publisher:newsletter-publisher` (LOW 티어)

**프롬프트 조립 절차**:
1. `agents/{agent-name}/` 에서 3파일 로드: AGENT.md + agentcard.yaml + tools.yaml
2. `runtime-mapping.yaml` 참조하여 구체화:
   - **모델 구체화**: agentcard.yaml의 `tier` → `tiers` 매핑에서 모델 결정
   - **툴 구체화**: tools.yaml의 추상 도구 → `tools` 매핑에서 실제 도구 결정
   - **금지액션 구체화**: agentcard.yaml의 `forbidden_actions` → `forbidden_actions` 매핑에서 제외할 도구 결정
   - **최종 도구** = (구체화된 도구) - (제외 도구)
3. 3파일을 합쳐 하나의 프롬프트로 조립
4. **프롬프트 구성 순서**: 공통 정적(runtime-mapping) → 에이전트별 정적(3파일) → 동적(작업 지시)
5. `Task(subagent_type=FQN, model=구체화된모델, prompt=조립된프롬프트)` 호출

**오케스트레이션 스킬 활용**:
- **전체 워크플로우**: `/oh-my-claudecode:ralph` (완료 보장 실행 워크플로우)
- **에러 처리**: 재시도 로직과 에러 알림 포함
- **성능 모니터링**: 각 단계별 실행 시간 측정 및 통계 수집

## MUST 규칙

| 규칙 | 설명 |
|------|------|
| orchestrator 에이전트 위임 필수 | 모든 실제 작업은 orchestrator 에이전트가 담당 |
| 6단계 워크플로우 순차 실행 | 수집→처리→저장→생성→발송→기록 순서 엄격 준수 |
| 에러 발생 시 재시도 로직 적용 | DB 연결 실패, API 오류 시 최대 3회 재시도 |
| 에러 발생 시 관리자 알림 필수 | 모든 에러는 data-manager를 통해 로그 저장 후 알림 |
| 성공/실패 명확한 결과 보고 | 각 단계별 상태와 최종 결과를 구체적으로 출력 |

## MUST NOT 규칙

| 금지 사항 | 이유 |
|----------|------|
| 스킬이 직접 RSS 수집 금지 | collector 에이전트가 전담, 역할 분리 원칙 |
| 스킬이 직접 DB 조작 금지 | data-manager 에이전트가 전담 |
| 스킬이 직접 API 호출 금지 | content-processor 에이전트가 전담 |
| 에러 발생 시 워크플로우 중단 금지 | 가능한 단계까지 진행 후 결과 보고 |
| 설정 파일 직접 수정 금지 | 읽기 전용으로 설정 확인만 수행 |

## 검증 체크리스트

- [ ] orchestrator 에이전트가 올바른 FQN으로 호출되는지 확인
- [ ] 6단계 워크플로우가 순서대로 실행되는지 확인
- [ ] 각 하위 에이전트의 성공/실패가 정확히 판단되는지 확인
- [ ] 에러 발생 시 재시도 로직이 작동하는지 확인
- [ ] 에러 로그가 PostgreSQL에 저장되는지 확인
- [ ] 관리자에게 에러 알림 이메일이 발송되는지 확인
- [ ] 최종 결과가 명확하고 구체적으로 보고되는지 확인
- [ ] 뉴스레터 발행 기록이 데이터베이스에 저장되는지 확인
- [ ] 모든 에이전트가 runtime-mapping.yaml에 올바르게 매핑되는지 확인
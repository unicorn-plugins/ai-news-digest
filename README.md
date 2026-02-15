# AI News Digest

> AI 관련 최신 뉴스를 자동 수집·요약하여 한국어 뉴스레터로 발행하는 DMAP 플러그인

---

## 개요

AI News Digest는 9개의 주요 RSS 피드에서 AI 관련 최신 뉴스를 24시간마다 자동으로 수집하여 중복을 제거하고, Groq API로 요약한 뒤 한국어로 번역하여 HTML 뉴스레터로 발행하는 완전 자동화된 시스템입니다.

**주요 기능:**
- 9개 RSS 피드에서 24시간 이내 AI 뉴스 자동 수집 (arxiv, Google AI, OpenAI, TechCrunch 등)
- fuzzywuzzy를 활용한 지능형 중복 제거 (85% 유사도 기준)
- Groq API(llama-3.1-8b-instant)를 사용한 영문 뉴스 요약 및 한국어 번역
- 카테고리별 구성 (연구 트렌드, 빅테크 트렌드, 산업 뉴스, 개발 실무)
- PostgreSQL 기반 데이터 관리 및 발행 이력 추적
- Gmail SMTP를 통한 HTML 뉴스레터 자동 발송
- 매일 오전 8시 cron 자동 실행 및 에러 알림 시스템

---

## 설치

### 사전 요구사항

- [Claude Code](https://claude.com/claude-code) CLI 설치
- PostgreSQL 14+ (setup 스킬에서 자동 설치)
- Python 3.9+ (필수 라이브러리: feedparser, groq, psycopg2, fuzzywuzzy, jinja2, pyyaml)
- Groq API 키 (https://console.groq.com/keys)
- Gmail 앱 비밀번호 (2단계 인증 필요)

### 플러그인 설치

**방법 1: 마켓플레이스 — GitHub (권장)**

```bash
# 1. GitHub 저장소를 마켓플레이스로 등록
claude plugin marketplace add unicorn-plugins/ai-news-digest

# 2. 플러그인 설치 (형식: ai-news-digest@ai-news-digest)
claude plugin install ai-news-digest@ai-news-digest

# 3. 설치 확인
claude plugin list
```

**방법 2: 마켓플레이스 — 로컬**

```bash
# 1. 로컬 경로를 마켓플레이스로 등록
claude plugin marketplace add ./ai-news-digest

# 2. 플러그인 설치
claude plugin install ai-news-digest@ai-news-digest

# 3. 설치 확인
claude plugin list
```

> **설치 후 setup 스킬 실행:**
> ```
> /ai-news-digest:setup
> ```
> - PostgreSQL 자동 설치 및 데이터베이스 초기화
> - Groq API 키 및 Gmail SMTP 설정
> - 뉴스레터 수신자 목록 설정
> - 매일 오전 8시 자동 실행을 위한 cron job 등록

### 처음 GitHub을 사용하시나요?

다음 가이드를 참고하세요:

- [GitHub 계정 생성 가이드](https://github.com/unicorn-plugins/gen-ma-plugin/blob/main/resources/guides/github/github-account-setup.md)
- [Personal Access Token 생성 가이드](https://github.com/unicorn-plugins/gen-ma-plugin/blob/main/resources/guides/github/github-token-guide.md)
- [GitHub Organization 생성 가이드](https://github.com/unicorn-plugins/gen-ma-plugin/blob/main/resources/guides/github/github-organization-guide.md)

---

## 업그레이드

### Git Repository 마켓플레이스

저장소의 최신 커밋을 가져와 플러그인을 업데이트함.

```bash
# 마켓플레이스 업데이트 (최신 커밋 반영)
claude plugin marketplace update ai-news-digest

# 플러그인 재설치
claude plugin install ai-news-digest@ai-news-digest

# 설치 확인
claude plugin list
```

> **버전 고정**: `marketplace.json`에 특정 `ref`/`sha`가 지정된 경우,
> 저장소 관리자가 해당 값을 업데이트해야 새 버전이 반영됨.

> **갱신이 반영되지 않는 경우**: 플러그인을 삭제 후 재설치함.
> ```bash
> claude plugin remove ai-news-digest@ai-news-digest
> claude plugin marketplace update ai-news-digest
> claude plugin install ai-news-digest@ai-news-digest
> ```

### 로컬 마켓플레이스

로컬 경로의 파일을 직접 갱신한 뒤 마켓플레이스를 업데이트함.

```bash
# 1. 로컬 플러그인 소스 갱신 (예: git pull 또는 파일 복사)
cd ai-news-digest
git pull origin main

# 2. 마켓플레이스 업데이트
claude plugin marketplace update ai-news-digest

# 3. 플러그인 재설치
claude plugin install ai-news-digest@ai-news-digest
```

> **갱신이 반영되지 않는 경우**: 플러그인을 삭제 후 재설치함.
> ```bash
> claude plugin remove ai-news-digest@ai-news-digest
> claude plugin marketplace update ai-news-digest
> claude plugin install ai-news-digest@ai-news-digest
> ```

> **setup 재실행**: 업그레이드 후 `install.yaml`에 새 도구가 추가된 경우
> `/ai-news-digest:setup`을 재실행하여 누락된 도구를 설치할 것.

---

## 사용법

### 슬래시 명령

| 명령 | 설명 |
|------|------|
| `/ai-news-digest:setup` | 플러그인 초기 설정 (PostgreSQL, API 키, 수신자, cron 등록) |
| `/ai-news-digest:run-daily-digest` | 뉴스레터 발행 실행 (메인 기능) |
| `/ai-news-digest:help` | 사용 안내 및 트러블슈팅 가이드 |
| `/ai-news-digest:add-ext-skill` | 외부 DMAP 플러그인 연동 추가 |
| `/ai-news-digest:remove-ext-skill` | 외부 DMAP 플러그인 연동 제거 |

### 사용 예시

```
사용자: AI 뉴스레터 발행해줘
→ 플러그인이 9개 RSS 피드에서 뉴스 수집 → 중복 제거 → Groq API 요약 → PostgreSQL 저장 → HTML 뉴스레터 생성 → 이메일 발송을 자동으로 처리
```

### 자동 실행 설정

setup 완료 후 매일 오전 8시에 자동으로 뉴스레터가 발행됩니다:

```bash
# cron job 확인
crontab -l

# 수동 실행 (테스트용)
/ai-news-digest:run-daily-digest
```

---

## 에이전트 구성

| 에이전트 | 티어 | 역할 |
|----------|------|------|
| collector | MEDIUM | RSS 피드 수집 및 파싱, 24시간 필터링 |
| content-processor | MEDIUM | 중복 검사, Groq API 요약, 한국어 번역 |
| data-manager | LOW | PostgreSQL CRUD 연산, 데이터 저장 및 조회 |
| newsletter-publisher | LOW | HTML 뉴스레터 생성 및 Gmail SMTP 발송 |

---

## 데이터 소스

### 수집 중인 RSS 피드 (9개)

| 카테고리 | 피드명 | URL |
|---------|--------|-----|
| **연구 트렌드** | arxiv cs.AI | https://arxiv.org/rss/cs.AI |
| | arxiv cs.LG | https://arxiv.org/rss/cs.LG |
| **빅테크 트렌드** | Anthropic Blog | GitHub RSS 피드 |
| | Google AI Blog | https://blog.google/technology/ai/rss/ |
| | OpenAI Blog | https://openai.com/blog/rss.xml |
| **산업 뉴스** | TechCrunch | https://techcrunch.com/feed/ |
| | VentureBeat | https://venturebeat.com/category/ai/feed/ |
| | Hugging Face | https://huggingface.co/blog/feed.xml |
| **개발 실무** | LangChain Blog | https://blog.langchain.dev/rss/ |
| | InfoQ | https://feed.infoq.com/ai-ml-data-eng/ |

---

## 요구사항

### 필수 도구

| 도구 | 유형 | 용도 |
|------|------|------|
| PostgreSQL | 시스템 | 뉴스 항목, 뉴스레터, 에러 로그 저장 |
| Groq API | API | 영문 뉴스 요약 및 한국어 번역 |
| Gmail SMTP | API | HTML 뉴스레터 이메일 발송 |

### Python 라이브러리

```bash
pip install feedparser groq psycopg2-binary fuzzywuzzy python-Levenshtein jinja2 pyyaml requests beautifulsoup4
```

### 런타임 호환성

| 런타임 | 지원 |
|--------|:----:|
| Claude Code | ✅ |
| Codex CLI | 미검증 |
| Gemini CLI | 미검증 |

---

## 디렉토리 구조

```
ai-news-digest/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── .gitignore
├── install.yaml
├── runtime-mapping.yaml
├── skills/
│   ├── setup/
│   │   └── SKILL.md
│   ├── help/
│   │   └── SKILL.md
│   ├── run-daily-digest/
│   │   └── SKILL.md
│   ├── add-ext-skill/
│   │   └── SKILL.md
│   └── remove-ext-skill/
│       └── SKILL.md
├── agents/
│   ├── collector/
│   │   ├── AGENT.md
│   │   ├── agentcard.yaml
│   │   └── tools.yaml
│   ├── content-processor/
│   │   ├── AGENT.md
│   │   ├── agentcard.yaml
│   │   └── tools.yaml
│   ├── data-manager/
│   │   ├── AGENT.md
│   │   ├── agentcard.yaml
│   │   └── tools.yaml
│   └── newsletter-publisher/
│       ├── AGENT.md
│       ├── agentcard.yaml
│       └── tools.yaml
├── commands/
│   ├── setup.md
│   ├── help.md
│   ├── run-daily-digest.md
│   ├── add-ext-skill.md
│   └── remove-ext-skill.md
├── tools/
│   └── customs/
│       ├── apps/
│       │   ├── rss_collector.py
│       │   ├── groq_summarizer.py
│       │   ├── duplicate_checker.py
│       │   ├── db_client.py
│       │   ├── newsletter_generator.py
│       │   └── email_sender.py
│       └── templates/
│           └── newsletter.html
└── README.md
```

### 설정 파일 (setup 스킬에서 생성)

```
.dmap/
├── secrets/
│   ├── groq.yaml
│   └── gmail.yaml
└── config/
    ├── recipients.yaml
    └── db.yaml
```

---

## 트러블슈팅

### 일반적인 문제

| 문제 | 해결 방법 |
|------|----------|
| PostgreSQL 연결 실패 | `brew services restart postgresql@14` (macOS) 또는 `sudo systemctl restart postgresql` (Linux) |
| Groq API 오류 | API 키 유효성 확인, 요청 한도 확인 |
| 이메일 발송 실패 | Gmail 앱 비밀번호 재생성, SMTP 설정 확인 |
| cron job 미실행 | `crontab -l`로 등록 확인, 절대 경로 확인 |
| 중복 뉴스 수집 | RSS 피드 응답 지연, 다음 실행에서 자동 해결 |

### 로그 확인

- PostgreSQL 에러 로그: `error_logs` 테이블 조회
- 뉴스레터 발행 이력: `newsletters` 테이블 조회
- 시스템 로그: `/var/log/cron` (Linux) 또는 Console.app (macOS)

---

## 개발

### 로컬 개발 환경 설정

```bash
# 저장소 클론
git clone https://github.com/unicorn-plugins/ai-news-digest.git
cd ai-news-digest

# 의존성 설치
pip install -r requirements.txt  # 생성 예정

# 로컬 설정
/ai-news-digest:setup
```

### 기여 방법

1. Fork this repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 라이선스

MIT License

Copyright (c) 2024 유니콘주식회사

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
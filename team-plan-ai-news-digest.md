# 팀 기획서

## 기본 정보
- 플러그인명: ai-news-digest
- 목적: AI 관련 최신 뉴스를 자동 수집·요약하여 한국어 뉴스레터로 발행
- 대상 도메인: 뉴스 큐레이션, 콘텐츠 자동화
- 대상 사용자: AI 기술 관심자, 개발자, 연구자

## 핵심기능
- **정보수집**: 지정된 데이터 소스(RSS 피드)에서 지난 1일간 새로 올라온 글만 수집
- **중복검사**: 제목 유사도 평가로 동일한 내용은 한 개만 선택
- **원문요약**: 원문 읽기 → Groq의 llama-3.1-8b-instant 모델로 요약 → 한국어로 번역
- **DB저장**: 기본정보, 원문, 한글요약을 로컬 PostgreSQL에 저장
- **뉴스레터 작성**: 카테고리별로 제목, 한글요약, 원문링크 포함한 뉴스레터 생성
- **뉴스레터 송부**: 미리 지정한 수신자에게 이메일 발송

## 사용자 플로우
- Step 1. **데이터 수집**: 9개 RSS 피드에서 24시간 이내 게시글 수집
- Step 2. **중복 제거**: 제목 유사도 기반 중복 콘텐츠 필터링
- Step 3. **콘텐츠 요약**: 각 원문을 Groq API로 요약 후 한국어 번역
- Step 4. **데이터 저장**: PostgreSQL에 원문·요약·메타데이터 저장
- Step 5. **뉴스레터 생성**: 카테고리별(연구/빅테크/산업/논문/개발) 섹션 구성
- Step 6. **이메일 발송**: 수신자 목록에 HTML 이메일 발송

## 데이터 소스
- **연구 트렌드**
  - cs.AI: https://arxiv.org/rss/cs.AI
  - cs.LG: https://arxiv.org/rss/cs.LG
- **빅테크 트렌드**
  - Anthropic Blog: https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml
  - Google AI Blog: https://blog.google/technology/ai/rss/
  - OpenAI Blog: https://openai.com/blog/rss.xml
- **산업뉴스**
  - TechCrunch: https://techcrunch.com/feed/
  - VentureBeat: https://venturebeat.com/category/ai/feed/
- **산업뉴스**
  - Hugging Face Daily Papers: https://huggingface.co/blog/feed.xml
- **개발 실무**
  - LangChain Blog: https://blog.langchain.dev/rss/
  - InfoQ: https://feed.infoq.com/ai-ml-data-eng/

## 에이전트 구성 힌트
- **orchestrator** (HIGH): 전체 워크플로우 조율, 에러 처리, 재시도 로직 관리
  - *추천 근거*: 6단계 플로우를 순차 실행하고, 각 단계의 성공/실패를 관리하며, DB 연결 실패나 API 오류 시 재시도 로직이 필요하므로 고수준 의사결정 필요
- **collector** (MEDIUM): RSS 피드 수집 및 파싱, 날짜 필터링
  - *추천 근거*: 9개 피드를 병렬 수집하고, 각 피드의 형식 차이를 처리하며, 날짜 필터링 로직을 적용하는 중간 수준 작업
- **content-processor** (MEDIUM): 중복검사 + 원문 요약 + 한국어 번역
  - *추천 근거*: 제목 유사도 계산, Groq API 호출, 번역 처리를 연속적으로 수행하는 복합 작업이므로 단일 에이전트로 통합. 외부 API 연동 필요
- **data-manager** (LOW): PostgreSQL CRUD 연산 (저장, 조회)
  - *추천 근거*: 정형화된 DB 연산이므로 단순 작업
- **newsletter-publisher** (LOW): 뉴스레터 HTML 생성 및 이메일 발송
  - *추천 근거*: 템플릿 기반 포맷팅과 SMTP 발송은 정형화된 작업

## 참고 공유 자원
- **참고 도구**: email_sender (SMTP 이메일 발송용)
  - *적합성*: 뉴스레터 송부 단계에서 HTML 이메일 발송에 직접 활용 가능
- **참고 샘플**: plugin/README
  - *적합성*: 플러그인 README.md 작성 시 참고
- **참고 템플릿**: plugin/README-plugin-template
  - *적합성*: 플러그인 README.md 스켈레톤

## 기술 요건
- **프로그래밍 언어**: Python 3.9+
- **필수 라이브러리**:
  - feedparser (RSS 파싱)
  - groq (Groq API 클라이언트)
  - psycopg2 (PostgreSQL 연결)
  - fuzzywuzzy 또는 difflib (제목 유사도 계산)
  - smtplib (이메일 발송, email_sender 도구 활용)
  - requests (웹페이지 fetch)
  - beautifulsoup4 (HTML 파싱)
- **외부 시스템**:
  - Groq API (요약 모델: llama-3.1-8b-instant)
  - PostgreSQL 데이터베이스
  - SMTP 서버 (Gmail, SendGrid 등)

## 데이터 스키마 (PostgreSQL)
```sql
-- 뉴스 항목 테이블
CREATE TABLE news_items (
  id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  category VARCHAR(50) NOT NULL, -- '연구 트렌드', '빅테크 트렌드' 등
  source VARCHAR(100) NOT NULL,  -- 'arxiv cs.AI', 'OpenAI Blog' 등
  url TEXT NOT NULL UNIQUE,
  published_at TIMESTAMP NOT NULL,
  original_content TEXT,
  summary_ko TEXT,
  collected_at TIMESTAMP DEFAULT NOW(),
  is_duplicate BOOLEAN DEFAULT FALSE
);

-- 뉴스레터 발행 기록 테이블
CREATE TABLE newsletters (
  id SERIAL PRIMARY KEY,
  issue_date DATE NOT NULL,
  content TEXT NOT NULL, -- HTML 뉴스레터 전문
  sent_at TIMESTAMP,
  recipient_count INTEGER
);
```

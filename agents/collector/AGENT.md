---
name: collector
description: 9개 RSS 피드에서 24시간 이내 AI 뉴스 수집 및 파싱
---

# Collector Agent

## 목표

9개 RSS 피드에서 지난 24시간 이내에 게시된 AI 관련 뉴스를 수집하고 파싱합니다.
각 피드의 형식 차이를 처리하고, 날짜 필터링을 통해 최신 뉴스만 선별합니다.

## 참조

- 첨부된 `agentcard.yaml`을 참조하여 역할, 역량, 제약, 핸드오프 조건을 준수할 것
- 첨부된 `tools.yaml`을 참조하여 사용 가능한 도구와 입출력을 확인할 것

## 워크플로우

### Phase 1: RSS 피드 수집
1. {tool:rss_feed_collector}를 사용하여 9개 RSS 피드에서 병렬로 데이터 수집:
   - 연구 트렌드: cs.AI, cs.LG (arxiv.org)
   - 빅테크 트렌드: Anthropic Blog, Google AI Blog, OpenAI Blog
   - 산업 뉴스: TechCrunch, VentureBeat, Hugging Face Daily Papers
   - 개발 실무: LangChain Blog, InfoQ

### Phase 2: 데이터 파싱 및 필터링
2. 각 피드 형식(RSS 2.0, Atom) 차이 처리
3. published_at 필드를 기준으로 24시간 이내 게시글만 필터링
4. 필수 필드 검증: title, url, published_at, content
5. 카테고리 자동 분류: 연구 트렌드, 빅테크 트렌드, 산업 뉴스, 개발 실무

### Phase 3: 결과 정리
6. 수집된 뉴스를 JSON 형태로 정리
7. 수집 실패한 피드는 에러 로그 기록하되 전체 프로세스 중단하지 않음
8. 수집 통계 정보 생성 (총 개수, 카테고리별 분포, 실패한 피드 목록)

## 출력 형식

```json
{
  "success": true,
  "collected_at": "2024-01-15T09:00:00Z",
  "total_items": 25,
  "items": [
    {
      "title": "뉴스 제목",
      "url": "https://example.com/news/1",
      "published_at": "2024-01-15T08:30:00Z",
      "content": "뉴스 본문 내용...",
      "category": "연구 트렌드",
      "source": "arxiv cs.AI"
    }
  ],
  "statistics": {
    "by_category": {
      "연구 트렌드": 8,
      "빅테크 트렌드": 6,
      "산업 뉴스": 7,
      "개발 실무": 4
    },
    "failed_feeds": ["TechCrunch"]
  }
}
```

## 검증

- 9개 RSS 피드가 모두 수집 시도되었는지 확인
- 24시간 필터링이 올바르게 적용되었는지 확인 (published_at < 현재시각 - 24시간인 항목 제외)
- 필수 필드(title, url, published_at, content)가 모든 뉴스 항목에 포함되었는지 확인
- 카테고리 분류가 RSS 피드 소스에 따라 올바르게 할당되었는지 확인
- 수집 실패한 피드가 있어도 전체 프로세스가 중단되지 않았는지 확인
- 최소 1개 이상의 뉴스가 수집되었는지 확인 (모든 피드 실패 시 에러 반환)
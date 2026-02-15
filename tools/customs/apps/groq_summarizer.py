#!/usr/bin/env python3
"""
Groq Summarizer for AI News Digest

Groq API를 사용하여 영문 뉴스를 요약하고 한국어로 번역하는 도구.
llama-3.1-8b-instant 모델 사용.
"""

import sys
import json
import os
import yaml
import time
from datetime import datetime
from typing import List, Dict, Optional
from groq import Groq
import groq


def load_groq_config(config_path: str = ".dmap/secrets/groq.yaml") -> Dict[str, str]:
    """Groq API 설정을 YAML 파일에서 로드"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        return {
            'api_key': config['api_key'],
            'model': config.get('model', 'llama-3.1-8b-instant')
        }
    except FileNotFoundError:
        print(f"Error: Groq API 설정 파일을 찾을 수 없습니다: {config_path}", file=sys.stderr)
        sys.exit(1)
    except KeyError as e:
        print(f"Error: Groq API 설정에서 필수 키가 없습니다: {e}", file=sys.stderr)
        sys.exit(1)


def summarize_and_translate(content: str, api_key: str, model: str = "llama-3.1-8b-instant", max_retries: int = 3) -> Dict[str, any]:
    """
    Groq API로 원문 요약 및 한국어 번역

    Args:
        content: 원문 내용
        api_key: Groq API 키
        model: 사용할 모델명
        max_retries: 최대 재시도 횟수

    Returns:
        결과 딕셔너리
    """
    client = Groq(api_key=api_key)

    # 프롬프트 작성
    system_prompt = """You are a professional AI news summarizer and translator. Your task is to:
1. Summarize the given English news article into 4-6 detailed sentences (80-120 words)
2. Translate the summary into natural, fluent Korean (at least 4-5 sentences)
3. Focus on: what happened, why it's important, context/background, and potential impact
4. Use formal but accessible Korean language suitable for a tech-savvy audience
5. Ensure Korean translation is comprehensive and informative, not just a brief overview"""

    user_prompt = f"""Please summarize and translate this AI/tech news article:

{content}

Response format:
- First provide a 4-6 sentence English summary (80-120 words)
- Then provide a detailed Korean translation (at least 4-5 sentences covering all key points)"""

    for attempt in range(max_retries):
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=model,
                temperature=0.3,  # 일관된 요약을 위해 낮은 temperature
                max_tokens=800,   # 4-6문장 상세 요약을 위한 충분한 토큰
                top_p=1,
                stop=None,
                stream=False
            )

            response_content = chat_completion.choices[0].message.content

            # 응답에서 한국어 부분 추출
            korean_summary = extract_korean_summary(response_content)

            return {
                "success": True,
                "original_content": content[:200] + "..." if len(content) > 200 else content,
                "full_response": response_content,
                "summary_ko": korean_summary,
                "model_used": model,
                "tokens_used": chat_completion.usage.total_tokens,
                "attempt": attempt + 1
            }

        except groq.RateLimitError as e:
            wait_time = 2 ** attempt  # Exponential backoff
            print(f"Rate limit exceeded, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})", file=sys.stderr)
            if attempt < max_retries - 1:
                time.sleep(wait_time)
                continue
            else:
                return {
                    "success": False,
                    "error": f"Rate limit exceeded after {max_retries} attempts",
                    "error_type": "rate_limit",
                    "original_content": content[:200] + "..." if len(content) > 200 else content
                }

        except groq.APIConnectionError as e:
            wait_time = 2 ** attempt
            print(f"API connection error, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})", file=sys.stderr)
            if attempt < max_retries - 1:
                time.sleep(wait_time)
                continue
            else:
                return {
                    "success": False,
                    "error": f"Connection failed after {max_retries} attempts: {str(e)}",
                    "error_type": "connection",
                    "original_content": content[:200] + "..." if len(content) > 200 else content
                }

        except groq.AuthenticationError as e:
            return {
                "success": False,
                "error": "Invalid API key",
                "error_type": "authentication",
                "original_content": content[:200] + "..." if len(content) > 200 else content
            }

        except Exception as e:
            wait_time = 2 ** attempt
            print(f"Unexpected error, waiting {wait_time}s (attempt {attempt + 1}/{max_retries}): {e}", file=sys.stderr)
            if attempt < max_retries - 1:
                time.sleep(wait_time)
                continue
            else:
                return {
                    "success": False,
                    "error": str(e),
                    "error_type": "unknown",
                    "original_content": content[:200] + "..." if len(content) > 200 else content
                }

    # 모든 재시도 실패
    return {
        "success": False,
        "error": f"All {max_retries} attempts failed",
        "error_type": "max_retries_exceeded",
        "original_content": content[:200] + "..." if len(content) > 200 else content
    }


def extract_korean_summary(response: str) -> str:
    """응답에서 한국어 요약 부분 추출"""
    lines = response.split('\n')
    korean_lines = []

    # 한국어가 포함된 줄들을 찾기
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 한글이 포함된 줄인지 확인
        if any('\u3131' <= char <= '\u3163' or '\uac00' <= char <= '\ud7af' for char in line):
            # "- " 접두사 제거
            if line.startswith('- '):
                line = line[2:]
            korean_lines.append(line)

    if korean_lines:
        return ' '.join(korean_lines)
    else:
        # 한국어를 찾을 수 없으면 전체 응답에서 마지막 부분 사용
        return response.split('\n')[-1].strip() if response else "요약을 생성할 수 없습니다."


def summarize_and_translate_batch(items: List[Dict], api_key: str, model: str = "llama-3.1-8b-instant", chunk_size: int = 5, max_retries: int = 3) -> Dict[str, any]:
    """
    배치로 여러 뉴스를 한 번에 요약 및 번역 (토큰 절감)

    Args:
        items: 뉴스 항목 리스트
        api_key: Groq API 키
        model: 사용할 모델명
        chunk_size: 한 번에 처리할 뉴스 개수 (기본 5개)
        max_retries: 최대 재시도 횟수

    Returns:
        배치 처리 결과 딕셔너리
    """
    client = Groq(api_key=api_key)

    system_prompt = """You are a professional AI news summarizer and translator. Your task is to:
1. Summarize each given English news article into 4-6 detailed sentences (80-120 words)
2. Translate each summary into natural, fluent Korean (at least 4-5 sentences)
3. Focus on: what happened, why it's important, context/background, and potential impact
4. Use formal but accessible Korean language suitable for a tech-savvy audience
5. Ensure Korean translation is comprehensive and informative, not just a brief overview

You will receive multiple articles numbered. For each article, provide:
- A 4-6 sentence English summary (80-120 words)
- A detailed Korean translation (at least 4-5 sentences)

Format your response as:
Article N:
[Detailed Korean summary - 4-5 sentences minimum]

---"""

    combined_content = "\n\n".join([
        f"Article {i+1}: {item.get('title', 'Untitled')}\n{item.get('content', '')[:1000]}"
        for i, item in enumerate(items)
    ])

    user_prompt = f"""Please summarize and translate these {len(items)} AI/tech news articles:

{combined_content}

Provide detailed Korean summaries for each article (4-5 sentences minimum), separated by '---'."""

    for attempt in range(max_retries):
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=model,
                temperature=0.3,
                max_tokens=800 * len(items),
                top_p=1,
                stop=None,
                stream=False
            )

            response_content = chat_completion.choices[0].message.content

            # 배치 응답 파싱 개선
            summaries = []
            raw_splits = response_content.split('---')

            for s in raw_splits:
                stripped = s.strip()
                if stripped:
                    # "Article N:" 헤더 제거
                    lines = stripped.split('\n')
                    clean_lines = [line for line in lines if not line.strip().startswith('Article')]
                    summary_text = '\n'.join(clean_lines).strip()
                    if summary_text:
                        summaries.append(summary_text)

            # 응답 개수가 요청 개수보다 적으면 경고
            if len(summaries) < len(items):
                print(f"경고: 응답 개수({len(summaries)})가 요청 개수({len(items)})보다 적습니다", file=sys.stderr)
                print(f"원본 응답:\n{response_content[:500]}...", file=sys.stderr)

            return {
                "success": True,
                "summaries": summaries,
                "tokens_used": chat_completion.usage.total_tokens,
                "model_used": model,
                "chunk_size": len(items),
                "attempt": attempt + 1
            }

        except groq.RateLimitError as e:
            wait_time = 2 ** attempt
            print(f"Rate limit exceeded, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})", file=sys.stderr)
            if attempt < max_retries - 1:
                time.sleep(wait_time)
                continue
            else:
                return {
                    "success": False,
                    "error": f"Rate limit exceeded after {max_retries} attempts",
                    "error_type": "rate_limit"
                }

        except Exception as e:
            wait_time = 2 ** attempt
            print(f"Batch error, waiting {wait_time}s (attempt {attempt + 1}/{max_retries}): {e}", file=sys.stderr)
            if attempt < max_retries - 1:
                time.sleep(wait_time)
                continue
            else:
                return {
                    "success": False,
                    "error": str(e),
                    "error_type": "unknown"
                }

    return {
        "success": False,
        "error": f"All {max_retries} attempts failed",
        "error_type": "max_retries_exceeded"
    }


def process_news_items(items: List[Dict], use_batch: bool = True, batch_size: int = 5) -> Dict[str, any]:
    """뉴스 항목들을 배치 또는 개별 처리"""
    config = load_groq_config()

    processed_items = []
    total_items = len(items)
    successful_count = 0
    failed_count = 0
    total_tokens = 0

    print(f"Groq API 요약 시작: {total_items}개 항목 (배치 모드: {use_batch}, 배치 크기: {batch_size})", file=sys.stderr)

    if use_batch and total_items > 1:
        # 배치 처리 모드
        for i in range(0, total_items, batch_size):
            chunk = items[i:i+batch_size]
            chunk_num = i // batch_size + 1
            total_chunks = (total_items + batch_size - 1) // batch_size

            print(f"배치 {chunk_num}/{total_chunks} 처리 중 ({len(chunk)}개 뉴스)...", file=sys.stderr)

            batch_result = summarize_and_translate_batch(
                chunk,
                config['api_key'],
                config['model'],
                chunk_size=len(chunk)
            )

            if batch_result['success']:
                summaries = batch_result['summaries']
                tokens = batch_result['tokens_used']
                total_tokens += tokens

                for j, item in enumerate(chunk):
                    processed_item = item.copy()
                    if j < len(summaries):
                        processed_item['summary_ko'] = summaries[j]
                        processed_item['summarized'] = True
                        processed_item['tokens_used'] = tokens // len(chunk)
                        successful_count += 1
                    else:
                        processed_item['summary_ko'] = item.get('content', '')[:500] + "..."
                        processed_item['summarized'] = False
                        processed_item['summary_error'] = "Summary not found in batch response"
                        failed_count += 1
                    processed_items.append(processed_item)

                print(f"배치 {chunk_num} 성공: {len(chunk)}개 처리, {tokens} 토큰 사용", file=sys.stderr)
            else:
                # 배치 실패 시 개별 처리로 폴백
                print(f"배치 {chunk_num} 실패, 개별 처리로 전환: {batch_result.get('error', 'Unknown')}", file=sys.stderr)
                for item in chunk:
                    result = summarize_and_translate(
                        item.get('content', ''),
                        config['api_key'],
                        config['model']
                    )
                    processed_item = item.copy()
                    if result['success']:
                        processed_item['summary_ko'] = result['summary_ko']
                        processed_item['summarized'] = True
                        processed_item['tokens_used'] = result.get('tokens_used', 0)
                        successful_count += 1
                        total_tokens += result.get('tokens_used', 0)
                    else:
                        processed_item['summary_ko'] = item.get('content', '')[:500] + "..."
                        processed_item['summarized'] = False
                        processed_item['summary_error'] = result['error']
                        failed_count += 1
                    processed_items.append(processed_item)

            if i + batch_size < total_items:
                time.sleep(1)

    else:
        # 개별 처리 모드 (기존 로직)
        for i, item in enumerate(items):
            print(f"처리 중: {i+1}/{total_items} - {item['title'][:50]}...", file=sys.stderr)

            result = summarize_and_translate(
                item.get('content', ''),
                config['api_key'],
                config['model']
            )

            processed_item = item.copy()

            if result['success']:
                processed_item['summary_ko'] = result['summary_ko']
                processed_item['summarized'] = True
                processed_item['tokens_used'] = result.get('tokens_used', 0)
                successful_count += 1
                total_tokens += result.get('tokens_used', 0)
                print(f"성공: {item['title'][:30]}... ({result.get('tokens_used', 0)} tokens)", file=sys.stderr)
            else:
                processed_item['summary_ko'] = item.get('content', '')[:500] + "..."
                processed_item['summarized'] = False
                processed_item['summary_error'] = result['error']
                processed_item['error_type'] = result.get('error_type', 'unknown')
                failed_count += 1
                print(f"실패: {item['title'][:30]}... - {result['error']}", file=sys.stderr)

            processed_items.append(processed_item)

            if i < total_items - 1:
                time.sleep(0.5)

    return {
        "success": successful_count > 0,
        "processed_at": datetime.now().isoformat(),
        "original_count": total_items,
        "final_count": len(processed_items),
        "items": processed_items,
        "processing_stats": {
            "successfully_summarized": successful_count,
            "summary_failed": failed_count,
            "total_tokens_used": total_tokens,
            "batch_mode": use_batch,
            "batch_size": batch_size if use_batch else 1
        }
    }


def main():
    """CLI 진입점"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  groq_summarizer.py <json_file>  - Summarize items from JSON file")
        print("  groq_summarizer.py -            - Read items from stdin")
        print("  groq_summarizer.py test <text>  - Test single text summarization")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "test":
            if len(sys.argv) < 3:
                print("Usage: groq_summarizer.py test <text_to_summarize>")
                sys.exit(1)

            config = load_groq_config()
            text = sys.argv[2]
            result = summarize_and_translate(text, config['api_key'], config['model'])
            print(json.dumps(result, indent=2, ensure_ascii=False))

        else:
            # 입력 데이터 읽기
            if command == "-":
                # stdin에서 읽기
                input_data = sys.stdin.read()
            else:
                # 파일에서 읽기
                with open(command, 'r', encoding='utf-8') as f:
                    input_data = f.read()

            data = json.loads(input_data)

            # items 키가 있는 경우 (duplicate_checker 출력 형식)
            if isinstance(data, dict) and 'items' in data:
                items = data['items']
            # 직접 리스트인 경우
            elif isinstance(data, list):
                items = data
            else:
                raise ValueError("Invalid input format. Expected list or dict with 'items' key.")

            # 배치 처리 수행
            result = process_news_items(items)

            # 결과 출력
            print(json.dumps(result, indent=2, ensure_ascii=False))

            if not result["success"]:
                print("Warning: 일부 또는 모든 요약이 실패했습니다.", file=sys.stderr)
                sys.exit(1)

    except FileNotFoundError:
        print(f"Error: File not found: {command}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
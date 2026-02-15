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
1. Summarize the given English news article into 3-4 concise sentences
2. Translate the summary into natural, fluent Korean
3. Focus on the key points: what happened, why it's important, and potential impact
4. Use formal but accessible Korean language suitable for a tech-savvy audience"""

    user_prompt = f"""Please summarize and translate this AI/tech news article:

{content}

Response format:
- First provide a 3-4 sentence English summary
- Then provide a Korean translation of the summary"""

    for attempt in range(max_retries):
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=model,
                temperature=0.3,  # 일관된 요약을 위해 낮은 temperature
                max_tokens=512,   # 3-4문장 요약에 충분한 토큰
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


def process_news_items(items: List[Dict]) -> Dict[str, any]:
    """뉴스 항목들을 배치 처리"""
    config = load_groq_config()

    processed_items = []
    total_items = len(items)
    successful_count = 0
    failed_count = 0
    total_tokens = 0

    print(f"Groq API 요약 시작: {total_items}개 항목", file=sys.stderr)

    for i, item in enumerate(items):
        print(f"처리 중: {i+1}/{total_items} - {item['title'][:50]}...", file=sys.stderr)

        # 요약 및 번역 수행
        result = summarize_and_translate(
            item.get('content', ''),
            config['api_key'],
            config['model']
        )

        # 원본 항목 복사 후 결과 추가
        processed_item = item.copy()

        if result['success']:
            processed_item['summary_ko'] = result['summary_ko']
            processed_item['summarized'] = True
            processed_item['tokens_used'] = result.get('tokens_used', 0)
            successful_count += 1
            total_tokens += result.get('tokens_used', 0)
            print(f"성공: {item['title'][:30]}... ({result.get('tokens_used', 0)} tokens)", file=sys.stderr)
        else:
            processed_item['summary_ko'] = item.get('content', '')[:500] + "..."  # 요약 실패 시 원문 일부 사용
            processed_item['summarized'] = False
            processed_item['summary_error'] = result['error']
            processed_item['error_type'] = result.get('error_type', 'unknown')
            failed_count += 1
            print(f"실패: {item['title'][:30]}... - {result['error']}", file=sys.stderr)

        processed_items.append(processed_item)

        # 과도한 API 호출 방지를 위한 짧은 지연
        if i < total_items - 1:  # 마지막이 아니면 대기
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
            "avg_processing_time": "N/A"  # 실제로는 시간 측정 가능
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
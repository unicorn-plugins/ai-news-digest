#!/usr/bin/env python3
"""
Newsletter Generator for AI News Digest

Jinja2 템플릿을 사용하여 카테고리별 HTML 뉴스레터를 생성하는 도구.
"""

import sys
import json
import os
from datetime import datetime, date
from typing import List, Dict
from jinja2 import Environment, FileSystemLoader, BaseLoader, Template


DEFAULT_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 뉴스 다이제스트 - {{ issue_date }}</title>
    <style>
        /* 반응형 이메일 스타일 */
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }

        .container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }

        .header h1 {
            margin: 0;
            font-size: 24px;
            font-weight: bold;
        }

        .header p {
            margin: 5px 0 0 0;
            font-size: 14px;
            opacity: 0.9;
        }

        .content {
            padding: 20px;
        }

        .category {
            margin-bottom: 30px;
        }

        .category h2 {
            color: #4a5568;
            font-size: 18px;
            margin: 0 0 15px 0;
            padding: 10px 15px;
            background-color: #f7fafc;
            border-left: 4px solid #667eea;
            border-radius: 4px;
        }

        .news-item {
            margin-bottom: 20px;
            padding: 15px;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            background-color: #ffffff;
        }

        .news-item:hover {
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: box-shadow 0.2s;
        }

        .news-title {
            font-size: 16px;
            font-weight: bold;
            margin: 0 0 8px 0;
            color: #2d3748;
        }

        .news-title a {
            color: #667eea;
            text-decoration: none;
        }

        .news-title a:hover {
            text-decoration: underline;
        }

        .news-summary {
            font-size: 14px;
            color: #4a5568;
            margin: 0 0 8px 0;
        }

        .news-meta {
            font-size: 12px;
            color: #718096;
            border-top: 1px solid #e2e8f0;
            padding-top: 8px;
        }

        .no-news {
            color: #718096;
            font-style: italic;
            text-align: center;
            padding: 20px;
            background-color: #f7fafc;
            border-radius: 4px;
        }

        .footer {
            background-color: #2d3748;
            color: #a0aec0;
            padding: 20px;
            text-align: center;
            font-size: 12px;
        }

        .footer a {
            color: #63b3ed;
            text-decoration: none;
        }

        .footer .company {
            margin-bottom: 10px;
            font-weight: bold;
            color: #ffffff;
        }

        /* 모바일 최적화 */
        @media only screen and (max-width: 600px) {
            .container {
                width: 100% !important;
            }

            .header h1 {
                font-size: 20px;
            }

            .content {
                padding: 15px;
            }

            .news-item {
                padding: 12px;
            }

            .news-title {
                font-size: 15px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- 헤더 -->
        <div class="header">
            <h1>🤖 AI 뉴스 다이제스트</h1>
            <p>{{ issue_date }} | 이슈 #{{ issue_number }}</p>
        </div>

        <!-- 콘텐츠 -->
        <div class="content">
            <!-- 개요 -->
            <div style="margin-bottom: 25px; padding: 15px; background-color: #ebf4ff; border-radius: 8px; border-left: 4px solid #3182ce;">
                <p style="margin: 0; color: #2c5282; font-size: 14px;">
                    <strong>오늘의 AI 뉴스 {{ total_news }}건</strong>을 카테고리별로 정리했습니다.
                    각 뉴스는 한국어로 요약되어 있으며, 원문 링크를 통해 자세한 내용을 확인하실 수 있습니다.
                </p>
            </div>

            <!-- 카테고리별 뉴스 -->
            {% for category_name, category_items in categories.items() %}
            <div class="category">
                <h2>{{ category_name }}</h2>

                {% if category_items %}
                    {% for item in category_items %}
                    <div class="news-item">
                        <h3 class="news-title">
                            <a href="{{ item.url }}" target="_blank">{{ item.title }}</a>
                        </h3>

                        <p class="news-summary">{{ item.summary_ko or item.content[:200] + "..." }}</p>

                        <div class="news-meta">
                            <strong>출처:</strong> {{ item.source }} |
                            <strong>발행:</strong> {{ item.published_at | format_datetime }}
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <div class="no-news">이번 이슈에는 {{ category_name }} 뉴스가 없습니다.</div>
                {% endif %}
            </div>
            {% endfor %}

            <!-- 통계 정보 -->
            <div style="margin-top: 30px; padding: 15px; background-color: #f7fafc; border-radius: 8px; font-size: 12px; color: #4a5568;">
                <strong>📊 발행 통계</strong><br>
                총 뉴스: {{ total_news }}건 |
                발행 시각: {{ generated_at | format_datetime }} |
                수신자: {{ recipient_count }}명
            </div>
        </div>

        <!-- 푸터 -->
        <div class="footer">
            <div class="company">유니콘주식회사</div>
            <p>
                이 뉴스레터는 AI가 자동으로 수집하고 요약한 정보입니다.<br>
                <a href="https://github.com/unicorn-plugins/ai-news-digest">GitHub</a> |
                <a href="mailto:admin@unicorn-inc.com">문의하기</a>
            </p>
            <p style="margin-top: 15px; font-size: 11px; color: #718096;">
                © {{ current_year }} 유니콘주식회사. All rights reserved.
            </p>
        </div>
    </div>
</body>
</html>
"""


def format_datetime_filter(dt_str):
    """DateTime 포맷팅 필터"""
    try:
        if isinstance(dt_str, str):
            # ISO 형식 파싱
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        else:
            dt = dt_str

        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return str(dt_str)


def organize_by_category(items: List[Dict]) -> Dict[str, List[Dict]]:
    """뉴스 항목들을 카테고리별로 분류"""
    categories = {
        "연구 트렌드": [],
        "빅테크 트렌드": [],
        "산업 뉴스": [],
        "개발 실무": []
    }

    for item in items:
        category = item.get('category', '기타')
        if category in categories:
            categories[category].append(item)
        else:
            # 알 수 없는 카테고리는 '산업 뉴스'에 추가
            categories["산업 뉴스"].append(item)

    return categories


def generate_newsletter(
    items: List[Dict],
    template_path: Optional[str] = None,
    issue_date: Optional[str] = None,
    recipient_count: int = 0
) -> Dict[str, any]:
    """HTML 뉴스레터 생성"""

    try:
        # 템플릿 로드
        if template_path and os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
        else:
            template_content = DEFAULT_TEMPLATE

        # Jinja2 환경 설정
        env = Environment(loader=BaseLoader())
        env.filters['format_datetime'] = format_datetime_filter
        template = env.from_string(template_content)

        # 데이터 준비
        categories = organize_by_category(items)
        total_news = len(items)

        if not issue_date:
            issue_date = date.today().strftime('%Y년 %m월 %d일')

        # 이슈 번호 계산 (간단히 일자 기준)
        issue_number = date.today().strftime('%Y%m%d')

        # 템플릿 변수
        template_vars = {
            'categories': categories,
            'total_news': total_news,
            'issue_date': issue_date,
            'issue_number': issue_number,
            'generated_at': datetime.now().isoformat(),
            'recipient_count': recipient_count,
            'current_year': date.today().year
        }

        # HTML 렌더링
        html_content = template.render(**template_vars)

        # 결과 반환
        return {
            "success": True,
            "operation": "generate_newsletter",
            "generated_at": datetime.now().isoformat(),
            "html_content": html_content,
            "newsletter_size": f"{len(html_content) / 1024:.1f}KB",
            "total_news": total_news,
            "sections": {category: len(items) for category, items in categories.items()},
            "template_used": "custom" if template_path else "default"
        }

    except Exception as e:
        return {
            "success": False,
            "operation": "generate_newsletter",
            "error": str(e)
        }


def save_newsletter(html_content: str, output_path: str) -> Dict[str, any]:
    """뉴스레터 HTML 파일 저장"""
    try:
        # 출력 디렉토리 생성
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return {
            "success": True,
            "operation": "save_newsletter",
            "output_path": output_path,
            "file_size": os.path.getsize(output_path)
        }

    except Exception as e:
        return {
            "success": False,
            "operation": "save_newsletter",
            "error": str(e)
        }


def main():
    """CLI 진입점"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  newsletter_generator.py <json_file> [template_path] [output_path] [recipient_count]")
        print("  newsletter_generator.py - [template_path] [output_path] [recipient_count] (read from stdin)")
        print("")
        print("Arguments:")
        print("  json_file       - JSON file containing news items")
        print("  template_path   - Custom HTML template file (optional)")
        print("  output_path     - Output HTML file path (optional)")
        print("  recipient_count - Number of recipients (optional, default: 0)")
        sys.exit(1)

    try:
        # 인자 파싱
        input_file = sys.argv[1]
        template_path = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != 'none' else None
        output_path = sys.argv[3] if len(sys.argv) > 3 else None
        recipient_count = int(sys.argv[4]) if len(sys.argv) > 4 else 0

        # 입력 데이터 읽기
        if input_file == "-":
            input_data = sys.stdin.read()
        else:
            with open(input_file, 'r', encoding='utf-8') as f:
                input_data = f.read()

        data = json.loads(input_data)

        # items 키가 있는 경우 (다른 도구들의 출력 형식)
        if isinstance(data, dict) and 'items' in data:
            items = data['items']
        elif isinstance(data, list):
            items = data
        else:
            raise ValueError("Invalid input format. Expected list or dict with 'items' key.")

        # 뉴스레터 생성
        result = generate_newsletter(items, template_path, recipient_count=recipient_count)

        if result["success"]:
            # 출력 파일 저장 (지정된 경우)
            if output_path:
                save_result = save_newsletter(result["html_content"], output_path)
                result["save_result"] = save_result

            # HTML 콘텐츠 제외하고 결과 출력 (너무 길어서)
            output_result = result.copy()
            html_length = len(result["html_content"])
            output_result["html_content"] = f"[HTML content: {html_length} characters]"

            print(json.dumps(output_result, indent=2, ensure_ascii=False))

            # HTML 내용을 별도로 stdout에 출력하거나 파일로 저장
            if not output_path:
                print("\n" + "="*50)
                print("HTML CONTENT:")
                print("="*50)
                print(result["html_content"])

        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
            sys.exit(1)

    except FileNotFoundError:
        print(f"Error: File not found: {sys.argv[1]}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
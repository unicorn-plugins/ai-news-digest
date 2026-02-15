#!/usr/bin/env python3
"""
Send Newsletter

생성된 뉴스레터를 Gmail SMTP로 발송하는 도구.
"""

import sys
import json
from datetime import datetime
from email_sender import send_email, load_smtp_config, load_recipients
from db_client import DatabaseClient


def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print("Usage: send_newsletter.py <newsletter_html_file>")
        sys.exit(1)

    try:
        # HTML 파일 읽기
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            html_content = f.read()

        # 수신자 목록 로드
        recipients_config = load_recipients()
        recipients = recipients_config.get('recipients', [])

        if not recipients:
            print(json.dumps({
                'success': False,
                'error': 'No recipients configured'
            }))
            sys.exit(1)

        # 제목 생성
        subject = f"🤖 AI 뉴스 다이제스트 - {datetime.now().strftime('%Y년 %m월 %d일')}"

        # 텍스트 버전 생성 (간단한 안내 메시지)
        text_content = f"""AI 뉴스 다이제스트 - {datetime.now().strftime('%Y년 %m월 %d일')}

이메일 클라이언트가 HTML을 지원하지 않는 경우, 웹 브라우저에서 이 이메일을 확인해 주세요.

유니콘주식회사
"""

        # SMTP 설정 로드
        smtp_config = load_smtp_config()

        # 이메일 발송
        result = send_email(
            to=recipients,
            subject=subject,
            body_text=text_content,
            body_html=html_content,
            smtp_config=smtp_config
        )

        # 데이터베이스에 발송 기록 저장
        db_client = DatabaseClient()
        if db_client.connect():
            # newsletters 테이블에 저장
            insert_query = """
            INSERT INTO newsletters (
                subject, html_content, sent_at, recipient_count, status
            ) VALUES (
                %s, %s, %s, %s, %s
            ) RETURNING id
            """

            params = (
                subject,
                html_content,
                datetime.now(),
                len(result['successful_sends']),
                'sent' if result['successful_sends'] else 'failed'
            )

            db_result = db_client.execute_query(insert_query, params, fetch="one")

            if db_result['success']:
                newsletter_id = db_result['result']['id']
                result['newsletter_id'] = newsletter_id

            db_client.disconnect()

        # 결과 출력
        output_result = {
            'success': result['success'],
            'timestamp': datetime.now().isoformat(),
            'subject': subject,
            'total_recipients': len(recipients),
            'successful_sends': result.get('successful_sends', []),
            'failed_sends': result.get('failed_sends', [])
        }

        if 'newsletter_id' in result:
            output_result['newsletter_id'] = result['newsletter_id']

        print(json.dumps(output_result, indent=2, ensure_ascii=False))

        if not result['success']:
            sys.exit(1)

    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()
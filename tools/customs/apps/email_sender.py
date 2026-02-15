#!/usr/bin/env python3
"""
Email Sender for AI News Digest

smtplib를 사용하여 이메일을 발송하는 도구.
Gmail SMTP 설정을 YAML 파일에서 읽어옴.
"""

import sys
import json
import os
import yaml
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict


def load_smtp_config(config_path: str = ".dmap/secrets/gmail.yaml") -> Dict[str, str]:
    """Gmail SMTP 설정을 YAML 파일에서 로드"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        return {
            'smtp_server': config.get('smtp_server', 'smtp.gmail.com'),
            'smtp_port': config.get('smtp_port', 587),
            'username': config.get('username', config.get('email')),
            'password': config.get('password', config.get('app_password'))
        }
    except FileNotFoundError:
        print(f"Error: Gmail SMTP 설정 파일을 찾을 수 없습니다: {config_path}", file=sys.stderr)
        sys.exit(1)
    except KeyError as e:
        print(f"Error: Gmail SMTP 설정에서 필수 키가 없습니다: {e}", file=sys.stderr)
        sys.exit(1)


def load_recipients(config_path: str = ".dmap/config/recipients.yaml") -> Dict:
    """수신자 목록을 YAML 파일에서 로드"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"Error: 수신자 설정 파일을 찾을 수 없습니다: {config_path}", file=sys.stderr)
        sys.exit(1)


def send_email(
    to: List[str],
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
    smtp_config: Optional[Dict] = None
) -> Dict[str, any]:
    """
    이메일 발송

    Args:
        to: 수신자 이메일 목록
        subject: 제목
        body_text: 본문 (텍스트)
        body_html: 본문 (HTML, 선택)
        smtp_config: SMTP 설정 딕셔너리

    Returns:
        발송 결과 딕셔너리
    """
    if smtp_config is None:
        smtp_config = load_smtp_config()

    successful_sends = []
    failed_sends = []

    try:
        with smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port']) as server:
            server.starttls()
            server.login(smtp_config['username'], smtp_config['password'])

            for recipient in to:
                try:
                    msg = MIMEMultipart('alternative')
                    msg['Subject'] = subject
                    msg['From'] = smtp_config['username']
                    msg['To'] = recipient

                    part1 = MIMEText(body_text, 'plain')
                    msg.attach(part1)

                    if body_html:
                        part2 = MIMEText(body_html, 'html')
                        msg.attach(part2)

                    server.sendmail(smtp_config['username'], recipient, msg.as_string())
                    successful_sends.append(recipient)
                    print(f"Email sent successfully to {recipient}")

                except Exception as e:
                    failed_sends.append(recipient)
                    print(f"Failed to send email to {recipient}: {e}", file=sys.stderr)

    except Exception as e:
        print(f"SMTP connection error: {e}", file=sys.stderr)
        return {
            "success": False,
            "error": str(e),
            "successful_sends": 0,
            "failed_sends": len(to),
            "failed_addresses": to
        }

    return {
        "success": len(failed_sends) == 0,
        "total_recipients": len(to),
        "successful_sends": len(successful_sends),
        "failed_sends": len(failed_sends),
        "failed_addresses": failed_sends,
        "successful_addresses": successful_sends
    }


def send_newsletter(newsletter_html: str, issue_date: str) -> Dict[str, any]:
    """뉴스레터 발송"""
    recipients_config = load_recipients()
    # Handle both list of strings and list of dicts
    recipients_list = recipients_config['recipients']
    if recipients_list and isinstance(recipients_list[0], str):
        recipients = recipients_list
    else:
        recipients = [r['email'] for r in recipients_list]

    subject = f"AI 뉴스 다이제스트 - {issue_date}"
    body_text = f"AI 뉴스 다이제스트 {issue_date} 이슈입니다. HTML 지원 이메일 클라이언트에서 확인해주세요."

    return send_email(recipients, subject, body_text, newsletter_html)


def send_error_notification(error_type: str, error_message: str, occurred_at: str) -> Dict[str, any]:
    """관리자에게 에러 알림 이메일 발송"""
    recipients_config = load_recipients()
    admin_email = recipients_config.get('admin_email')

    if not admin_email:
        print("Error: 관리자 이메일이 설정되지 않았습니다.", file=sys.stderr)
        return {"success": False, "error": "No admin email configured"}

    subject = f"[AI 뉴스 다이제스트] 에러 알림 - {occurred_at.split('T')[0]}"
    body_text = f"""
AI 뉴스 다이제스트에서 에러가 발생했습니다.

에러 유형: {error_type}
에러 메시지: {error_message}
발생 시각: {occurred_at}

확인 후 적절한 조치를 취해주세요.
"""

    return send_email([admin_email], subject, body_text)


def main():
    """CLI 진입점"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  newsletter <html_file> <issue_date>    - Send newsletter")
        print("  error <error_type> <error_message> <occurred_at>  - Send error notification")
        print("  custom <to> <subject> <body_text> [<body_html>]   - Send custom email")
        sys.exit(1)

    command = sys.argv[1]

    if command == "newsletter":
        if len(sys.argv) < 4:
            print("Usage: email_sender.py newsletter <html_file> <issue_date>")
            sys.exit(1)

        html_file = sys.argv[2]
        issue_date = sys.argv[3]

        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                newsletter_html = f.read()
        except FileNotFoundError:
            print(f"Error: HTML 파일을 찾을 수 없습니다: {html_file}", file=sys.stderr)
            sys.exit(1)

        result = send_newsletter(newsletter_html, issue_date)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif command == "error":
        if len(sys.argv) < 5:
            print("Usage: email_sender.py error <error_type> <error_message> <occurred_at>")
            sys.exit(1)

        error_type = sys.argv[2]
        error_message = sys.argv[3]
        occurred_at = sys.argv[4]

        result = send_error_notification(error_type, error_message, occurred_at)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif command == "custom":
        if len(sys.argv) < 5:
            print("Usage: email_sender.py custom <to> <subject> <body_text> [<body_html>]")
            sys.exit(1)

        to = [sys.argv[2]]
        subject = sys.argv[3]
        body_text = sys.argv[4]
        body_html = sys.argv[5] if len(sys.argv) > 5 else None

        result = send_email(to, subject, body_text, body_html)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

    if not result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
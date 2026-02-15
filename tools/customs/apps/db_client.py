#!/usr/bin/env python3
"""
Database Client for AI News Digest

PostgreSQL 데이터베이스에 뉴스 항목, 뉴스레터, 에러 로그를 저장하고 조회하는 도구.
"""

import sys
import json
import os
import yaml
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date
from typing import List, Dict, Optional, Union


class DatabaseClient:
    """PostgreSQL 데이터베이스 클라이언트"""

    def __init__(self, config_path: str = ".dmap/config/db.yaml"):
        """데이터베이스 클라이언트 초기화"""
        self.config = self.load_db_config(config_path)
        self.connection = None

    def load_db_config(self, config_path: str) -> Dict[str, str]:
        """데이터베이스 설정을 YAML 파일에서 로드"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config
        except FileNotFoundError:
            # 기본 설정 사용
            return {
                'host': 'localhost',
                'port': 5432,
                'database': 'ai_news',
                'user': 'postgres',
                'password': ''
            }
        except Exception as e:
            print(f"Error loading DB config: {e}", file=sys.stderr)
            sys.exit(1)

    def connect(self) -> bool:
        """데이터베이스 연결"""
        try:
            self.connection = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config.get('password', ''),
                cursor_factory=RealDictCursor
            )
            return True
        except psycopg2.Error as e:
            print(f"Database connection failed: {e}", file=sys.stderr)
            return False

    def disconnect(self):
        """데이터베이스 연결 해제"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute_query(self, query: str, params: Optional[tuple] = None, fetch: str = "none") -> Dict[str, any]:
        """쿼리 실행"""
        if not self.connection:
            if not self.connect():
                return {"success": False, "error": "Database connection failed"}

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)

                if fetch == "one":
                    result = cursor.fetchone()
                elif fetch == "all":
                    result = cursor.fetchall()
                elif fetch == "none":
                    result = cursor.rowcount
                else:
                    result = None

                # INSERT/UPDATE/DELETE는 자동 커밋
                if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                    self.connection.commit()

                return {
                    "success": True,
                    "result": result,
                    "rowcount": cursor.rowcount
                }

        except psycopg2.Error as e:
            if self.connection:
                self.connection.rollback()
            return {
                "success": False,
                "error": str(e),
                "error_code": e.pgcode if hasattr(e, 'pgcode') else None
            }

    def insert_news_items(self, items: List[Dict]) -> Dict[str, any]:
        """뉴스 항목들을 news_items 테이블에 저장"""
        if not items:
            return {"success": True, "inserted": 0, "skipped_duplicates": 0, "inserted_ids": []}

        insert_query = """
        INSERT INTO news_items (title, category, source, url, published_at, summary, summary_ko)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (url) DO UPDATE SET
            summary_ko = EXCLUDED.summary_ko,
            updated_at = CURRENT_TIMESTAMP
        WHERE news_items.summary_ko LIKE '[요약 불가%'
        RETURNING id;
        """

        inserted_ids = []
        inserted_count = 0
        duplicate_count = 0

        try:
            if not self.connection:
                if not self.connect():
                    return {"success": False, "error": "Database connection failed"}

            with self.connection.cursor() as cursor:
                for item in items:
                    try:
                        # 날짜 파싱 (ISO 형식 문자열을 datetime으로 변환)
                        if isinstance(item['published_at'], str):
                            published_at = datetime.fromisoformat(item['published_at'].replace('Z', '+00:00'))
                        else:
                            published_at = item['published_at']

                        cursor.execute(insert_query, (
                            item['title'],
                            item['category'],
                            item['source'],
                            item['url'],
                            published_at,
                            item.get('content', ''),
                            item.get('summary_ko', '')
                        ))

                        if cursor.rowcount > 0:
                            result = cursor.fetchone()
                            if result:
                                inserted_ids.append(result['id'])
                                inserted_count += 1
                        else:
                            duplicate_count += 1

                    except Exception as item_error:
                        print(f"Error inserting item {item.get('title', 'Unknown')}: {item_error}", file=sys.stderr)
                        duplicate_count += 1
                        continue

                self.connection.commit()

                return {
                    "success": True,
                    "operation": "insert_news_items",
                    "total_items": len(items),
                    "inserted": inserted_count,
                    "skipped_duplicates": duplicate_count,
                    "inserted_ids": inserted_ids
                }

        except Exception as e:
            if self.connection:
                self.connection.rollback()
            return {
                "success": False,
                "operation": "insert_news_items",
                "error": str(e)
            }

    def insert_newsletter(self, content: str, recipient_count: int, news_item_ids: List[int] = None) -> Dict[str, any]:
        """뉴스레터 발행 기록을 newsletters 테이블에 저장하고 뉴스 항목 연결"""
        insert_query = """
        INSERT INTO newsletters (subject, html_content, sent_at, recipient_count, status)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        """

        link_query = """
        INSERT INTO newsletter_items (newsletter_id, news_item_id)
        VALUES (%s, %s)
        ON CONFLICT (newsletter_id, news_item_id) DO NOTHING;
        """

        try:
            result = self.execute_query(insert_query, (
                f"AI News Digest - {date.today()}",
                content,
                datetime.now(),
                recipient_count,
                'sent'
            ), fetch="one")

            if result["success"] and result["result"]:
                newsletter_id = result["result"]["id"]

                # 뉴스 항목 연결
                linked_count = 0
                if news_item_ids:
                    for item_id in news_item_ids:
                        link_result = self.execute_query(link_query, (newsletter_id, item_id))
                        if link_result["success"]:
                            linked_count += 1

                return {
                    "success": True,
                    "operation": "insert_newsletter",
                    "newsletter_id": newsletter_id,
                    "issue_date": str(date.today()),
                    "recipient_count": recipient_count,
                    "linked_news_items": linked_count
                }
            else:
                return {
                    "success": False,
                    "operation": "insert_newsletter",
                    "error": result.get("error", "Unknown error")
                }

        except Exception as e:
            return {
                "success": False,
                "operation": "insert_newsletter",
                "error": str(e)
            }

    def insert_error_log(self, error_type: str, error_message: str, stack_trace: str = "") -> Dict[str, any]:
        """에러 로그를 error_logs 테이블에 저장"""
        insert_query = """
        INSERT INTO error_logs (error_type, error_message, stack_trace, occurred_at, notified)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        """

        try:
            result = self.execute_query(insert_query, (
                error_type,
                error_message,
                stack_trace,
                datetime.now(),
                False
            ), fetch="one")

            if result["success"] and result["result"]:
                error_log_id = result["result"]["id"]
                return {
                    "success": True,
                    "operation": "insert_error_log",
                    "error_log_id": error_log_id,
                    "error_type": error_type,
                    "logged_at": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "operation": "insert_error_log",
                    "error": result.get("error", "Unknown error")
                }

        except Exception as e:
            return {
                "success": False,
                "operation": "insert_error_log",
                "error": str(e)
            }

    def get_today_news(self) -> Dict[str, any]:
        """오늘 수집된 뉴스 중 아직 발송되지 않은 목록 조회"""
        query = """
        SELECT DISTINCT n.id, n.title, n.category, n.source, n.url,
               n.published_at, n.summary, n.summary_ko
        FROM news_items n
        WHERE DATE(n.collected_at) = CURRENT_DATE
          AND NOT EXISTS (
              SELECT 1 FROM newsletter_items ni
              JOIN newsletters nl ON ni.newsletter_id = nl.id
              WHERE ni.news_item_id = n.id
                AND nl.sent_at IS NOT NULL
                AND DATE(nl.sent_at) = CURRENT_DATE
          )
        ORDER BY n.published_at DESC;
        """

        try:
            result = self.execute_query(query, fetch="all")

            if result["success"]:
                return {
                    "success": True,
                    "operation": "get_today_news",
                    "count": len(result["result"]) if result["result"] else 0,
                    "news_items": result["result"] or []
                }
            else:
                return {
                    "success": False,
                    "operation": "get_today_news",
                    "error": result.get("error", "Query failed")
                }

        except Exception as e:
            return {
                "success": False,
                "operation": "get_today_news",
                "error": str(e)
            }

    def get_recent_newsletters(self, limit: int = 5) -> Dict[str, any]:
        """최근 뉴스레터 발행 기록 조회"""
        query = """
        SELECT id, issue_date, sent_at, recipient_count
        FROM newsletters
        ORDER BY sent_at DESC
        LIMIT %s;
        """

        try:
            result = self.execute_query(query, (limit,), fetch="all")

            if result["success"]:
                return {
                    "success": True,
                    "operation": "get_recent_newsletters",
                    "count": len(result["result"]) if result["result"] else 0,
                    "newsletters": result["result"] or []
                }
            else:
                return {
                    "success": False,
                    "operation": "get_recent_newsletters",
                    "error": result.get("error", "Query failed")
                }

        except Exception as e:
            return {
                "success": False,
                "operation": "get_recent_newsletters",
                "error": str(e)
            }

    def __enter__(self):
        """컨텍스트 매니저 진입"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.disconnect()


def create_database_schema() -> Dict[str, any]:
    """데이터베이스 스키마 생성 (setup용)"""
    schema_queries = [
        """
        CREATE TABLE IF NOT EXISTS news_items (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            category VARCHAR(50) NOT NULL,
            source VARCHAR(100) NOT NULL,
            url TEXT NOT NULL UNIQUE,
            published_at TIMESTAMP NOT NULL,
            original_content TEXT,
            summary_ko TEXT,
            collected_at TIMESTAMP DEFAULT NOW(),
            is_duplicate BOOLEAN DEFAULT FALSE
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_news_items_url ON news_items (url);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_news_items_published_at ON news_items (published_at);
        """,
        """
        CREATE TABLE IF NOT EXISTS newsletters (
            id SERIAL PRIMARY KEY,
            issue_date DATE NOT NULL,
            content TEXT NOT NULL,
            sent_at TIMESTAMP,
            recipient_count INTEGER
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS error_logs (
            id SERIAL PRIMARY KEY,
            error_type VARCHAR(50) NOT NULL,
            error_message TEXT NOT NULL,
            stack_trace TEXT,
            occurred_at TIMESTAMP DEFAULT NOW(),
            notified BOOLEAN DEFAULT FALSE
        );
        """
    ]

    client = DatabaseClient()
    results = []

    try:
        if not client.connect():
            return {"success": False, "error": "Database connection failed"}

        for i, query in enumerate(schema_queries):
            result = client.execute_query(query)
            results.append({
                "query_index": i,
                "success": result["success"],
                "error": result.get("error") if not result["success"] else None
            })

        client.disconnect()

        success_count = sum(1 for r in results if r["success"])
        return {
            "success": success_count == len(schema_queries),
            "operation": "create_schema",
            "total_queries": len(schema_queries),
            "successful_queries": success_count,
            "results": results
        }

    except Exception as e:
        client.disconnect()
        return {
            "success": False,
            "operation": "create_schema",
            "error": str(e)
        }


def main():
    """CLI 진입점"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  db_client.py create-schema                    - Create database schema")
        print("  db_client.py insert-news <json_file>          - Insert news items")
        print("  db_client.py insert-newsletter <content> <count> - Insert newsletter record")
        print("  db_client.py insert-error <type> <message>    - Insert error log")
        print("  db_client.py get-today-news                   - Get today's news")
        print("  db_client.py get-recent-newsletters [limit]   - Get recent newsletters")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "create-schema":
            result = create_database_schema()
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif command == "insert-news":
            if len(sys.argv) < 3:
                print("Usage: db_client.py insert-news <json_file>")
                sys.exit(1)

            with open(sys.argv[2], 'r', encoding='utf-8') as f:
                data = json.load(f)

            # items 키가 있는 경우
            if isinstance(data, dict) and 'items' in data:
                items = data['items']
            elif isinstance(data, list):
                items = data
            else:
                print("Error: Invalid JSON format", file=sys.stderr)
                sys.exit(1)

            with DatabaseClient() as client:
                result = client.insert_news_items(items)
                print(json.dumps(result, indent=2, ensure_ascii=False))

        elif command == "insert-newsletter":
            if len(sys.argv) < 4:
                print("Usage: db_client.py insert-newsletter <content> <recipient_count>")
                sys.exit(1)

            content = sys.argv[2]
            recipient_count = int(sys.argv[3])

            with DatabaseClient() as client:
                result = client.insert_newsletter(content, recipient_count)
                print(json.dumps(result, indent=2, ensure_ascii=False))

        elif command == "insert-error":
            if len(sys.argv) < 4:
                print("Usage: db_client.py insert-error <error_type> <error_message> [stack_trace]")
                sys.exit(1)

            error_type = sys.argv[2]
            error_message = sys.argv[3]
            stack_trace = sys.argv[4] if len(sys.argv) > 4 else ""

            with DatabaseClient() as client:
                result = client.insert_error_log(error_type, error_message, stack_trace)
                print(json.dumps(result, indent=2, ensure_ascii=False))

        elif command == "get-today-news":
            with DatabaseClient() as client:
                result = client.get_today_news()
                print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

        elif command == "get-recent-newsletters":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5

            with DatabaseClient() as client:
                result = client.get_recent_newsletters(limit)
                print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

        # 성공 여부에 따른 종료 코드
        if 'result' in locals() and not result.get("success", True):
            sys.exit(1)

    except FileNotFoundError:
        print(f"Error: File not found: {sys.argv[2] if len(sys.argv) > 2 else 'N/A'}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
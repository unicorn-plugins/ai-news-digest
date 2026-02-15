#!/usr/bin/env python3
"""
Duplicate Checker for AI News Digest

뉴스 제목 유사도를 계산하여 중복 항목을 제거하는 도구.
fuzzywuzzy를 사용한 문자열 유사도 계산.
"""

import sys
import json
from datetime import datetime
from typing import List, Dict
from fuzzywuzzy import fuzz
import re


def normalize_title(title: str) -> str:
    """제목 정규화 (비교용)"""
    # 소문자 변환
    title = title.lower()

    # 특수 문자 제거 (알파벳, 숫자, 공백만 유지)
    title = re.sub(r'[^a-zA-Z0-9가-힣\s]', ' ', title)

    # 연속된 공백을 하나로 축약
    title = re.sub(r'\s+', ' ', title)

    # 앞뒤 공백 제거
    title = title.strip()

    return title


def calculate_similarity(title1: str, title2: str) -> float:
    """두 제목 간의 유사도 계산 (0-100)"""
    normalized_title1 = normalize_title(title1)
    normalized_title2 = normalize_title(title2)

    # fuzzywuzzy의 ratio 사용 (Levenshtein 거리 기반)
    similarity = fuzz.ratio(normalized_title1, normalized_title2)

    return similarity


def find_duplicate_groups(items: List[Dict], threshold: float = 85.0) -> List[List[int]]:
    """중복 그룹 찾기"""
    duplicate_groups = []
    processed_indices = set()

    for i, item1 in enumerate(items):
        if i in processed_indices:
            continue

        current_group = [i]

        for j, item2 in enumerate(items[i+1:], start=i+1):
            if j in processed_indices:
                continue

            similarity = calculate_similarity(item1['title'], item2['title'])

            if similarity >= threshold:
                current_group.append(j)
                processed_indices.add(j)

        if len(current_group) > 1:
            duplicate_groups.append(current_group)
            processed_indices.update(current_group)

    return duplicate_groups


def select_representative_from_group(items: List[Dict], group_indices: List[int]) -> int:
    """중복 그룹에서 대표 항목 선택 (가장 이른 발행 시간)"""
    group_items = [(idx, items[idx]) for idx in group_indices]

    # published_at 기준으로 정렬 (가장 이른 것이 먼저)
    group_items.sort(key=lambda x: x[1]['published_at'])

    return group_items[0][0]  # 인덱스 반환


def remove_duplicates(items: List[Dict], threshold: float = 85.0) -> Dict[str, any]:
    """중복 제거 메인 함수"""
    if not items:
        return {
            "success": True,
            "processed_at": datetime.now().isoformat(),
            "original_count": 0,
            "after_dedup_count": 0,
            "duplicates_removed": 0,
            "items": [],
            "duplicate_groups": []
        }

    original_count = len(items)
    print(f"중복 검사 시작: {original_count}개 항목", file=sys.stderr)

    # 중복 그룹 찾기
    duplicate_groups = find_duplicate_groups(items, threshold)
    print(f"중복 그룹 {len(duplicate_groups)}개 발견", file=sys.stderr)

    # 제거할 인덱스 집합
    indices_to_remove = set()

    # 그룹별 대표 선택 및 나머지 제거 마킹
    group_info = []
    for group_indices in duplicate_groups:
        representative_idx = select_representative_from_group(items, group_indices)

        # 그룹 정보 저장 (디버깅용)
        group_titles = [items[idx]['title'] for idx in group_indices]
        group_info.append({
            "representative_index": representative_idx,
            "representative_title": items[representative_idx]['title'],
            "duplicate_titles": [items[idx]['title'] for idx in group_indices if idx != representative_idx],
            "similarity_scores": []
        })

        # 대표가 아닌 항목들을 제거 대상으로 마킹
        for idx in group_indices:
            if idx != representative_idx:
                indices_to_remove.add(idx)

    # 중복이 아닌 항목들 + 각 그룹의 대표 항목들만 남김
    deduplicated_items = []
    for i, item in enumerate(items):
        if i not in indices_to_remove:
            # is_duplicate 플래그 추가
            item_copy = item.copy()
            item_copy['is_duplicate'] = False
            deduplicated_items.append(item_copy)

    duplicates_removed = original_count - len(deduplicated_items)

    result = {
        "success": True,
        "processed_at": datetime.now().isoformat(),
        "original_count": original_count,
        "after_dedup_count": len(deduplicated_items),
        "duplicates_removed": duplicates_removed,
        "items": deduplicated_items,
        "duplicate_groups_info": group_info,
        "threshold_used": threshold
    }

    print(f"중복 제거 완료: {duplicates_removed}개 제거, {len(deduplicated_items)}개 유지", file=sys.stderr)

    return result


def main():
    """CLI 진입점"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  duplicate_checker.py <json_file> [threshold]")
        print("  duplicate_checker.py - (read from stdin)")
        print("")
        print("Arguments:")
        print("  json_file  - JSON file containing news items")
        print("  threshold  - Similarity threshold (0-100, default: 85)")
        sys.exit(1)

    try:
        # 임계값 설정
        threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 85.0

        # 입력 데이터 읽기
        if sys.argv[1] == "-":
            # stdin에서 읽기
            input_data = sys.stdin.read()
        else:
            # 파일에서 읽기
            with open(sys.argv[1], 'r', encoding='utf-8') as f:
                input_data = f.read()

        data = json.loads(input_data)

        # items 키가 있는 경우 (RSS collector 출력 형식)
        if isinstance(data, dict) and 'items' in data:
            items = data['items']
        # 직접 리스트인 경우
        elif isinstance(data, list):
            items = data
        else:
            raise ValueError("Invalid input format. Expected list or dict with 'items' key.")

        # 중복 제거 수행
        result = remove_duplicates(items, threshold)

        # 결과 출력
        print(json.dumps(result, indent=2, ensure_ascii=False))

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
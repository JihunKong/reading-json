#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Golden Mini Dataset 테스트

중심문장 선택과 키워드 추출의 정확도를 검증하는 골든 스탠다드 테스트셋
"""

import pytest
import sys
import os

# 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '../generator'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../validator'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../grader'))

from topic_sentence import select_topic_sentence
from keywords import extract_keywords
from rule_validator import validate_content

# grader 모듈에서 EnhancedGrader import
grader_path = os.path.join(os.path.dirname(__file__), '../grader')
sys.path.insert(0, grader_path)
from cli import EnhancedGrader


# Golden Mini Dataset (교사가 수동으로 라벨링한 예시)
GOLDEN_CASES = [
    {
        "id": "golden_001",
        "sentences": [
            "도시 녹화는 환경 문제 해결의 핵심 방법이다.",  # 정답: 중심문장
            "많은 도시들이 공원과 녹지 공간을 확대하고 있다.",
            "이러한 노력은 대기 질 개선과 열섬 현상 완화에 도움이 된다.",
            "결과적으로 시민들의 삶의 질이 향상되고 있다."
        ],
        "expected_topic_sentence": 0,  # 첫 번째 문장이 중심문장
        "expected_keywords": ["도시", "녹화", "환경", "문제", "해결"],
        "genre": "설명문",
        "difficulty": "medium"
    },
    {
        "id": "golden_002",
        "sentences": [
            "디지털 기술의 발달로 교육 방식이 변화하고 있다.",
            "온라인 강의와 AI 튜터링 시스템이 널리 보급되었다.",
            "학습자들은 개인 맞춤형 학습 경험을 제공받는다.",
            "따라서 디지털 교육은 미래 교육의 주축이 될 것이다."  # 정답: 결론문장이 중심
        ],
        "expected_topic_sentence": 3,  # 마지막 문장이 중심문장 (결론 요약)
        "expected_keywords": ["디지털", "교육", "기술", "학습", "변화"],
        "genre": "논설문",
        "difficulty": "medium"
    },
    {
        "id": "golden_003",
        "sentences": [
            "기후 변화는 전 지구적 문제이다.",
            "온실가스 배출량이 지속적으로 증가하고 있다.",
            "극지방의 빙하가 녹고 해수면이 상승하고 있다.",
            "이에 대한 국제적 협력과 대응이 시급하다."
        ],
        "expected_topic_sentence": 0,  # 첫 번째 문장이 주제문
        "expected_keywords": ["기후", "변화", "지구", "온실가스", "문제"],
        "genre": "설명문",
        "difficulty": "hard"
    },
    {
        "id": "golden_004",
        "sentences": [
            "전통 시장은 지역 경제의 중요한 축이다.",
            "최근 온라인 쇼핑 증가로 매출이 감소하고 있다.",
            "정부와 지자체가 다양한 지원 정책을 펼치고 있다."
        ],
        "expected_topic_sentence": 0,  # 첫 번째 문장이 중심문장
        "expected_keywords": ["전통", "시장", "지역", "경제", "중요"],
        "genre": "설명문",
        "difficulty": "easy"
    },
    {
        "id": "golden_005",
        "sentences": [
            "인공지능 기술이 급속히 발전하고 있다.",
            "의료, 금융, 교육 등 다양한 분야에서 활용되고 있다.",
            "하지만 일자리 감소와 윤리적 문제가 대두되고 있다.",
            "결국 인공지능과 인간의 협력적 관계 구축이 중요하다."  # 정답: 결론이 중심
        ],
        "expected_topic_sentence": 3,  # 결론 문장이 중심문장
        "expected_keywords": ["인공지능", "기술", "발전", "활용", "협력"],
        "genre": "논설문",
        "difficulty": "hard"
    }
]


class TestTopicSentenceSelection:
    """중심문장 선택 테스트"""

    def test_topic_sentence_accuracy(self):
        """중심문장 선택 정확도 테스트"""
        correct_count = 0
        total_count = len(GOLDEN_CASES)

        for case in GOLDEN_CASES:
            result = select_topic_sentence(
                sentences=case["sentences"],
                keywords=case["expected_keywords"],
                genre=case["genre"]
            )

            # Top-1 정확도 측정
            if result.idx == case["expected_topic_sentence"]:
                correct_count += 1

            # 디버깅 정보 출력
            print(f"Case {case['id']}: Expected={case['expected_topic_sentence']}, "
                  f"Got={result.idx}, Score={result.total:.3f}")

        accuracy = correct_count / total_count
        print(f"Topic Sentence Accuracy: {accuracy:.2%} ({correct_count}/{total_count})")

        # 목표: 70% 이상 정확도
        assert accuracy >= 0.70, f"정확도가 목표치(70%)보다 낮습니다: {accuracy:.2%}"

    def test_topic_sentence_top2_accuracy(self):
        """중심문장 Top-2 포함 정확도 테스트"""
        top2_correct = 0
        total_count = len(GOLDEN_CASES)

        for case in GOLDEN_CASES:
            # 모든 문장에 대해 점수 계산
            all_results = []
            for i in range(len(case["sentences"])):
                # 각 문장을 후보로 해서 점수 계산
                temp_sentences = case["sentences"].copy()
                result = select_topic_sentence(
                    sentences=temp_sentences,
                    keywords=case["expected_keywords"],
                    genre=case["genre"]
                )
                all_results.append((i, result.total))

            # 점수 순으로 정렬
            all_results.sort(key=lambda x: x[1], reverse=True)
            top2_indices = [idx for idx, _ in all_results[:2]]

            if case["expected_topic_sentence"] in top2_indices:
                top2_correct += 1

        accuracy = top2_correct / total_count
        print(f"Topic Sentence Top-2 Accuracy: {accuracy:.2%} ({top2_correct}/{total_count})")

        # 목표: 88% 이상 Top-2 포함
        assert accuracy >= 0.88, f"Top-2 정확도가 목표치(88%)보다 낮습니다: {accuracy:.2%}"


class TestKeywordExtraction:
    """키워드 추출 테스트"""

    def test_keyword_extraction_coverage(self):
        """키워드 추출 커버율 테스트"""
        total_coverage = 0
        total_count = len(GOLDEN_CASES)

        for case in GOLDEN_CASES:
            extracted = extract_keywords(case["sentences"], topk=8)
            expected = set(case["expected_keywords"])
            extracted_set = set(extracted)

            # 커버율 계산 (교집합 / 기대값)
            coverage = len(expected & extracted_set) / len(expected) if expected else 0
            total_coverage += coverage

            print(f"Case {case['id']}: Expected={expected}, "
                  f"Extracted={extracted_set & expected}, Coverage={coverage:.2%}")

        avg_coverage = total_coverage / total_count
        print(f"Average Keyword Coverage: {avg_coverage:.2%}")

        # 목표: 60% 이상 키워드 커버율
        assert avg_coverage >= 0.60, f"키워드 커버율이 목표치(60%)보다 낮습니다: {avg_coverage:.2%}"

    def test_keyword_precision(self):
        """키워드 추출 정밀도 테스트 (추출된 것 중 얼마나 관련이 있는가)"""
        total_precision = 0
        total_count = len(GOLDEN_CASES)

        for case in GOLDEN_CASES:
            extracted = extract_keywords(case["sentences"], topk=5)

            # 간단한 관련성 체크: 문장에 실제로 나타나는 단어인지
            full_text = " ".join(case["sentences"])
            relevant_count = 0

            for keyword in extracted:
                if keyword in full_text and len(keyword) >= 2:
                    relevant_count += 1

            precision = relevant_count / len(extracted) if extracted else 0
            total_precision += precision

        avg_precision = total_precision / total_count
        print(f"Average Keyword Precision: {avg_precision:.2%}")

        # 목표: 80% 이상 정밀도
        assert avg_precision >= 0.80, f"키워드 정밀도가 목표치(80%)보다 낮습니다: {avg_precision:.2%}"


class TestContentValidation:
    """콘텐츠 검증 테스트"""

    def test_content_quality(self):
        """콘텐츠 품질 검증 테스트"""
        valid_count = 0
        total_count = len(GOLDEN_CASES)

        for case in GOLDEN_CASES:
            result = validate_content(
                sentences=case["sentences"],
                keywords=case["expected_keywords"]
            )

            if result.is_valid and result.score >= 0.7:
                valid_count += 1

            print(f"Case {case['id']}: Valid={result.is_valid}, "
                  f"Score={result.score:.2f}, Issues={len(result.issues)}")

        quality_rate = valid_count / total_count
        print(f"Content Quality Rate: {quality_rate:.2%} ({valid_count}/{total_count})")

        # 목표: 80% 이상 품질 통과
        assert quality_rate >= 0.80, f"콘텐츠 품질이 목표치(80%)보다 낮습니다: {quality_rate:.2%}"


class TestGradingSystem:
    """채점 시스템 테스트"""

    def test_partial_scoring(self):
        """부분점수 시스템 테스트"""
        grader = EnhancedGrader()

        # 테스트 케이스: 정답과 유사한 답변들
        test_cases = [
            {
                "user_answer": "도시 녹화는 환경 문제 해결의 핵심이다",
                "correct_answer": "도시 녹화는 환경 문제 해결의 핵심 방법이다",
                "expected_min_score": 85  # 거의 정확
            },
            {
                "user_answer": "환경을 개선하는 것이 중요하다",
                "correct_answer": "도시 녹화는 환경 문제 해결의 핵심 방법이다",
                "expected_min_score": 40  # 부분 관련
            },
            {
                "user_answer": "완전히 다른 내용이다",
                "correct_answer": "도시 녹화는 환경 문제 해결의 핵심 방법이다",
                "expected_max_score": 30  # 비관련
            }
        ]

        for i, case in enumerate(test_cases):
            result = grader.grade_topic_sentence(
                user_answer=case["user_answer"],
                correct_answer=case["correct_answer"],
                context_keywords=["도시", "녹화", "환경", "해결"]
            )

            print(f"Test Case {i+1}: Score={result.score}, Band={result.band}")
            print(f"  Components: {result.components}")
            print(f"  Feedback: {result.feedback}")

            # 점수 범위 검증
            if "expected_min_score" in case:
                assert result.score >= case["expected_min_score"], \
                    f"점수가 너무 낮습니다: {result.score} < {case['expected_min_score']}"

            if "expected_max_score" in case:
                assert result.score <= case["expected_max_score"], \
                    f"점수가 너무 높습니다: {result.score} > {case['expected_max_score']}"


class TestSystemIntegration:
    """시스템 통합 테스트"""

    def test_end_to_end_pipeline(self):
        """전체 파이프라인 테스트"""
        for case in GOLDEN_CASES[:2]:  # 처음 2개 케이스만 테스트
            print(f"\n=== Testing {case['id']} ===")

            # 1. 키워드 추출
            keywords = extract_keywords(case["sentences"])
            print(f"Extracted keywords: {keywords}")

            # 2. 중심문장 선택
            topic_result = select_topic_sentence(
                sentences=case["sentences"],
                keywords=keywords,
                genre=case["genre"]
            )
            print(f"Selected sentence: {topic_result.idx} (score: {topic_result.total:.3f})")

            # 3. 콘텐츠 검증
            validation_result = validate_content(case["sentences"], keywords)
            print(f"Validation: {validation_result.is_valid} (score: {validation_result.score:.3f})")

            # 4. 채점 테스트
            grader = EnhancedGrader()
            correct_sentence = case["sentences"][case["expected_topic_sentence"]]
            user_answer = case["sentences"][topic_result.idx]

            grading_result = grader.grade_topic_sentence(
                user_answer=user_answer,
                correct_answer=correct_sentence,
                context_keywords=keywords
            )
            print(f"Grading: {grading_result.score} ({grading_result.band})")

            # 기본 건전성 체크
            assert len(keywords) > 0, "키워드가 추출되지 않았습니다"
            assert 0 <= topic_result.idx < len(case["sentences"]), "중심문장 인덱스가 유효하지 않습니다"
            assert validation_result.score > 0, "검증 점수가 0입니다"
            assert grading_result.score >= 0, "채점 점수가 음수입니다"

        print("\n✅ 전체 파이프라인 테스트 완료!")


if __name__ == "__main__":
    # 개별 테스트 실행
    import subprocess

    print("🚀 Golden Mini Dataset 테스트 시작\n")

    # pytest로 테스트 실행
    result = subprocess.run([
        "python", "-m", "pytest", __file__, "-v", "--tb=short"
    ], capture_output=True, text=True)

    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)

    print(f"\n테스트 결과: {'✅ 성공' if result.returncode == 0 else '❌ 실패'}")
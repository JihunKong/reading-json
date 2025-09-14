#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
규칙 기반 품질 검증기

LLM으로 생성된 텍스트가 교육적 품질 기준을 만족하는지 검증합니다.
- 문장성 검증 (서술어 존재, 구문 완결성)
- 핵심어 커버율 검증
- 조사 고아 금지
- 길이 및 구조 검증
"""

import re
import statistics
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum


class ValidationLevel(Enum):
    """검증 수준"""
    BASIC = "basic"      # 기본 문법 검증
    MORPH = "morph"      # 형태소 분석 기반 검증
    SEMANTIC = "semantic"  # 의미 분석 기반 검증


@dataclass
class ValidationResult:
    """검증 결과"""
    is_valid: bool
    score: float         # 0~1 품질 점수
    issues: List[str]    # 발견된 문제들
    suggestions: List[str]  # 개선 제안
    details: Dict[str, Any]  # 상세 정보


@dataclass
class QualityMetrics:
    """품질 지표"""
    sentence_count: int
    avg_sentence_length: float
    keyword_coverage: float
    syntax_completeness: float
    particle_balance: float
    readability_score: float


class RuleValidator:
    """규칙 기반 검증기"""

    def __init__(self, morph_analyzer=None, level: ValidationLevel = ValidationLevel.BASIC):
        self.morph = morph_analyzer
        self.level = level

        # 검증 기준
        self.min_sentences = 3
        self.max_sentences = 6
        self.min_sentence_length = 10  # 어절 수
        self.max_sentence_length = 30
        self.min_keyword_coverage = 0.6
        self.min_syntax_score = 0.7

        # 한국어 패턴
        self.predicate_patterns = [
            r'[가-힣]+다$',      # ~다 (평서문)
            r'[가-힣]+는다$',    # ~는다
            r'[가-힣]+한다$',    # ~한다
            r'[가-힣]+된다$',    # ~된다
            r'[가-힣]+이다$',    # ~이다
            r'[가-힣]+있다$',    # ~있다
            r'[가-힣]+었다$',    # ~었다
            r'[가-힣]+았다$',    # ~았다
        ]

        self.particles = ['이', '가', '은', '는', '을', '를', '에', '에서', '으로', '로', '와', '과', '도']

        # 고아 조사 (문장 끝에 단독으로 나타나면 안 되는 조사)
        self.orphan_particles = ['이', '가', '을', '를', '의', '에서', '으로', '와', '과']

    def validate_content(self,
                        sentences: List[str],
                        keywords: List[str] = None,
                        topic: str = None) -> ValidationResult:
        """콘텐츠 품질 검증"""

        issues = []
        suggestions = []
        details = {}

        # 1. 기본 구조 검증
        structure_result = self._validate_structure(sentences)
        if not structure_result["is_valid"]:
            issues.extend(structure_result["issues"])
            suggestions.extend(structure_result["suggestions"])
        details["structure"] = structure_result

        # 2. 문장성 검증
        syntax_result = self._validate_syntax(sentences)
        if not syntax_result["is_valid"]:
            issues.extend(syntax_result["issues"])
            suggestions.extend(syntax_result["suggestions"])
        details["syntax"] = syntax_result

        # 3. 키워드 커버율 검증
        if keywords:
            coverage_result = self._validate_keyword_coverage(sentences, keywords)
            if not coverage_result["is_valid"]:
                issues.extend(coverage_result["issues"])
                suggestions.extend(coverage_result["suggestions"])
            details["coverage"] = coverage_result

        # 4. 조사 균형 검증
        particle_result = self._validate_particle_balance(sentences)
        if not particle_result["is_valid"]:
            issues.extend(particle_result["issues"])
            suggestions.extend(particle_result["suggestions"])
        details["particles"] = particle_result

        # 5. 가독성 검증
        readability_result = self._validate_readability(sentences)
        details["readability"] = readability_result

        # 품질 지표 계산
        metrics = self._calculate_metrics(sentences, keywords)
        details["metrics"] = metrics

        # 전체 점수 계산 (각 항목별 가중평균)
        weights = {
            "structure": 0.25,
            "syntax": 0.30,
            "coverage": 0.20,
            "particles": 0.15,
            "readability": 0.10
        }

        total_score = 0.0
        for category, weight in weights.items():
            if category in details and "score" in details[category]:
                total_score += details[category]["score"] * weight

        # 전체 유효성 판단
        critical_issues = [issue for issue in issues if "치명적" in issue or "필수" in issue]
        is_valid = len(critical_issues) == 0 and total_score >= 0.7

        return ValidationResult(
            is_valid=is_valid,
            score=total_score,
            issues=issues,
            suggestions=suggestions,
            details=details
        )

    def _validate_structure(self, sentences: List[str]) -> Dict[str, Any]:
        """기본 구조 검증"""
        issues = []
        suggestions = []

        sentence_count = len(sentences)

        # 문장 수 검증
        if sentence_count < self.min_sentences:
            issues.append(f"문장 수 부족: {sentence_count}개 (최소 {self.min_sentences}개 필요)")
            suggestions.append(f"{self.min_sentences - sentence_count}개 문장을 추가하세요.")
        elif sentence_count > self.max_sentences:
            issues.append(f"문장 수 과다: {sentence_count}개 (최대 {self.max_sentences}개 권장)")
            suggestions.append(f"{sentence_count - self.max_sentences}개 문장을 줄이거나 통합하세요.")

        # 문장 길이 검증
        lengths = [len(sentence.split()) for sentence in sentences]
        avg_length = statistics.mean(lengths) if lengths else 0

        short_sentences = [i for i, length in enumerate(lengths) if length < self.min_sentence_length]
        long_sentences = [i for i, length in enumerate(lengths) if length > self.max_sentence_length]

        if short_sentences:
            issues.append(f"너무 짧은 문장: {len(short_sentences)}개 (문장 {short_sentences})")
            suggestions.append("짧은 문장에 구체적인 설명을 추가하세요.")

        if long_sentences:
            issues.append(f"너무 긴 문장: {len(long_sentences)}개 (문장 {long_sentences})")
            suggestions.append("긴 문장을 두 개 이상으로 나누세요.")

        # 점수 계산
        structure_score = 1.0
        if sentence_count < self.min_sentences or sentence_count > self.max_sentences:
            structure_score *= 0.7
        if short_sentences or long_sentences:
            structure_score *= (1.0 - 0.1 * len(short_sentences + long_sentences))

        return {
            "is_valid": len(issues) == 0,
            "score": max(0.0, structure_score),
            "issues": issues,
            "suggestions": suggestions,
            "sentence_count": sentence_count,
            "avg_length": avg_length,
            "lengths": lengths
        }

    def _validate_syntax(self, sentences: List[str]) -> Dict[str, Any]:
        """문장성 검증"""
        issues = []
        suggestions = []

        incomplete_sentences = []
        orphan_particles_found = []

        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()

            # 서술어 존재 검증
            has_predicate = any(re.search(pattern, sentence) for pattern in self.predicate_patterns)

            if not has_predicate:
                incomplete_sentences.append(i + 1)

            # 고아 조사 검증
            for particle in self.orphan_particles:
                if sentence.endswith(particle):
                    orphan_particles_found.append((i + 1, particle))

        if incomplete_sentences:
            issues.append(f"서술어가 없는 문장: {incomplete_sentences}")
            suggestions.append("각 문장에 '~다', '~한다', '~이다' 등의 서술어를 추가하세요.")

        if orphan_particles_found:
            issues.append(f"고아 조사 발견: {orphan_particles_found}")
            suggestions.append("문장 끝의 조사 뒤에 적절한 서술어를 추가하세요.")

        # 점수 계산
        total_sentences = len(sentences)
        complete_sentences = total_sentences - len(incomplete_sentences)
        syntax_score = complete_sentences / total_sentences if total_sentences > 0 else 0

        if orphan_particles_found:
            syntax_score *= 0.8  # 고아 조사 페널티

        return {
            "is_valid": len(issues) == 0,
            "score": syntax_score,
            "issues": issues,
            "suggestions": suggestions,
            "incomplete_sentences": incomplete_sentences,
            "orphan_particles": orphan_particles_found
        }

    def _validate_keyword_coverage(self, sentences: List[str], keywords: List[str]) -> Dict[str, Any]:
        """키워드 커버율 검증"""
        if not keywords:
            return {"is_valid": True, "score": 1.0, "issues": [], "suggestions": []}

        issues = []
        suggestions = []

        # 전체 텍스트에서 키워드 출현 확인
        full_text = " ".join(sentences)
        covered_keywords = []
        missing_keywords = []

        for keyword in keywords:
            if keyword in full_text:
                covered_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)

        coverage_ratio = len(covered_keywords) / len(keywords) if keywords else 0

        if coverage_ratio < self.min_keyword_coverage:
            issues.append(f"키워드 커버율 부족: {coverage_ratio:.2f} (최소 {self.min_keyword_coverage} 필요)")
            suggestions.append(f"누락된 키워드를 포함하세요: {missing_keywords}")

        return {
            "is_valid": coverage_ratio >= self.min_keyword_coverage,
            "score": coverage_ratio,
            "issues": issues,
            "suggestions": suggestions,
            "covered_keywords": covered_keywords,
            "missing_keywords": missing_keywords,
            "coverage_ratio": coverage_ratio
        }

    def _validate_particle_balance(self, sentences: List[str]) -> Dict[str, Any]:
        """조사 균형 검증"""
        issues = []
        suggestions = []

        # 조사 빈도 계산
        particle_counts = {}
        total_words = 0

        for sentence in sentences:
            words = sentence.split()
            total_words += len(words)

            for word in words:
                for particle in self.particles:
                    if particle in word:
                        particle_counts[particle] = particle_counts.get(particle, 0) + 1

        # 조사 밀도 계산 (전체 어절 대비 조사 비율)
        total_particles = sum(particle_counts.values())
        particle_density = total_particles / total_words if total_words > 0 else 0

        # 적절한 조사 밀도: 0.3~0.7 (경험적 기준)
        if particle_density < 0.2:
            issues.append(f"조사 사용 부족: 밀도 {particle_density:.2f}")
            suggestions.append("주어, 목적어 표시를 위한 조사를 적절히 사용하세요.")
        elif particle_density > 0.8:
            issues.append(f"조사 사용 과다: 밀도 {particle_density:.2f}")
            suggestions.append("불필요한 조사를 줄이고 자연스러운 문장을 만드세요.")

        # 주요 조사 균형 (주격, 목적격, 부사격)
        subject_particles = particle_counts.get('이', 0) + particle_counts.get('가', 0)
        object_particles = particle_counts.get('을', 0) + particle_counts.get('를', 0)

        balance_score = 1.0
        if subject_particles == 0:
            balance_score *= 0.8
            suggestions.append("주어를 명시하는 조사('이', '가')를 사용하세요.")

        particle_score = min(1.0, 2.0 * particle_density) if particle_density <= 0.5 else min(1.0, 2.0 * (1.0 - particle_density))

        return {
            "is_valid": 0.2 <= particle_density <= 0.8,
            "score": particle_score * balance_score,
            "issues": issues,
            "suggestions": suggestions,
            "particle_density": particle_density,
            "particle_counts": particle_counts
        }

    def _validate_readability(self, sentences: List[str]) -> Dict[str, Any]:
        """가독성 검증"""
        # 단순한 가독성 지표
        total_chars = sum(len(sentence) for sentence in sentences)
        total_words = sum(len(sentence.split()) for sentence in sentences)

        avg_word_length = total_chars / total_words if total_words > 0 else 0

        # 한국어 적정 어절 길이: 2~4자
        readability_score = 1.0
        if avg_word_length < 2:
            readability_score = 0.7  # 너무 짧은 어절들
        elif avg_word_length > 5:
            readability_score = 0.8  # 너무 긴 어절들

        return {
            "score": readability_score,
            "avg_word_length": avg_word_length,
            "total_chars": total_chars,
            "total_words": total_words
        }

    def _calculate_metrics(self, sentences: List[str], keywords: List[str] = None) -> QualityMetrics:
        """품질 지표 계산"""
        sentence_count = len(sentences)
        lengths = [len(sentence.split()) for sentence in sentences]
        avg_length = statistics.mean(lengths) if lengths else 0

        # 키워드 커버율
        keyword_coverage = 0.0
        if keywords:
            full_text = " ".join(sentences)
            covered = sum(1 for keyword in keywords if keyword in full_text)
            keyword_coverage = covered / len(keywords)

        # 구문 완결성
        complete_sentences = 0
        for sentence in sentences:
            if any(re.search(pattern, sentence) for pattern in self.predicate_patterns):
                complete_sentences += 1
        syntax_completeness = complete_sentences / sentence_count if sentence_count > 0 else 0

        # 조사 균형
        total_words = sum(len(sentence.split()) for sentence in sentences)
        particle_count = 0
        for sentence in sentences:
            for word in sentence.split():
                if any(particle in word for particle in self.particles):
                    particle_count += 1
        particle_balance = min(1.0, particle_count / total_words * 2) if total_words > 0 else 0

        # 가독성
        total_chars = sum(len(sentence) for sentence in sentences)
        avg_word_length = total_chars / total_words if total_words > 0 else 0
        readability_score = 1.0 if 2 <= avg_word_length <= 4 else 0.8

        return QualityMetrics(
            sentence_count=sentence_count,
            avg_sentence_length=avg_length,
            keyword_coverage=keyword_coverage,
            syntax_completeness=syntax_completeness,
            particle_balance=particle_balance,
            readability_score=readability_score
        )


def validate_content(sentences: List[str],
                    keywords: List[str] = None,
                    topic: str = None,
                    morph_analyzer=None) -> ValidationResult:
    """편의 함수 - 콘텐츠 검증"""
    validator = RuleValidator(morph_analyzer)
    return validator.validate_content(sentences, keywords, topic)


# 테스트용 함수
if __name__ == "__main__":
    # 테스트 케이스
    good_sentences = [
        "도시 녹화는 환경 문제 해결에 중요한 역할을 한다.",
        "많은 도시들이 공원과 녹지 공간을 늘리고 있다.",
        "이러한 노력은 대기 질 개선에 도움이 된다."
    ]

    bad_sentences = [
        "도시 녹화가",  # 고아 조사
        "환경 문제 해결에 중요한",  # 서술어 없음
        "공원과 녹지 공간을 늘리고 있다."
    ]

    keywords = ["도시", "녹화", "환경", "공원"]

    print("=== 좋은 예시 검증 ===")
    result1 = validate_content(good_sentences, keywords)
    print(f"유효성: {result1.is_valid}")
    print(f"점수: {result1.score:.2f}")
    print(f"문제점: {result1.issues}")

    print("\n=== 나쁜 예시 검증 ===")
    result2 = validate_content(bad_sentences, keywords)
    print(f"유효성: {result2.is_valid}")
    print(f"점수: {result2.score:.2f}")
    print(f"문제점: {result2.issues}")
    print(f"제안: {result2.suggestions}")
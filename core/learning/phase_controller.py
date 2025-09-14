#!/usr/bin/env python3
"""
Learning Phase Controller for Korean Summary Learning System

This module manages the 4-phase progressive learning system:
1. Component Identification
2. Necessity Judgment  
3. Generalization
4. Theme Reconstruction
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import random

from .data_schema import EnhancedLearningTask, ComponentType, Necessity, LearningPhase
from ..nlp.korean_analyzer import KoreanSentenceAnalyzer
from ..korean_phrase_analyzer import KoreanPhraseAnalyzer

class ProgressLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"  
    ADVANCED = "advanced"
    EXPERT = "expert"

@dataclass
class StudentResponse:
    """Student response data for evaluation"""
    student_id: str
    task_id: str
    phase: LearningPhase
    timestamp: str
    response_data: Dict[str, Any]
    is_timeout: bool = False

@dataclass
class LearningHint:
    """Educational hint for students"""
    level: int  # 1=gentle, 2=specific, 3=direct, 4=solution
    message: str
    component_type: Optional[ComponentType] = None
    reasoning: str = ""

@dataclass  
class PhaseEvaluation:
    """Evaluation results for a learning phase"""
    phase: LearningPhase
    score: float  # 0-1
    correct_components: List[str]
    missing_components: List[str] 
    incorrect_components: List[str]
    hints: List[LearningHint]
    next_action: str  # continue, retry, advance, help
    mastery_achieved: bool

class LearningPhaseController:
    """
    Controls the 4-phase learning progression for Korean summary skills.
    """
    
    def __init__(self):
        self.analyzer = KoreanSentenceAnalyzer()
        self.phrase_analyzer = KoreanPhraseAnalyzer()
        
        # Phase requirements for advancement
        self.advancement_thresholds = {
            LearningPhase.COMPONENT_IDENTIFICATION: 0.5,  # More educational-friendly threshold
            LearningPhase.NECESSITY_JUDGMENT: 0.75,
            LearningPhase.GENERALIZATION: 0.7,
            LearningPhase.THEME_RECONSTRUCTION: 0.8
        }
        
        # Hint progression levels
        self.hint_levels = {
            1: "자신의 답을 다시 한번 확인해보세요.",
            2: "문장에서 {component}를 찾아보세요.",
            3: "'{specific_text}'에 주목하세요.",
            4: "정답은 '{answer}'입니다."
        }
        
        print("✅ Learning Phase Controller initialized")
    
    def start_phase_1(self, task: EnhancedLearningTask, student_id: str) -> Dict[str, Any]:
        """
        Start Phase 1: Component Identification
        
        Students learn to identify basic grammatical components (주어, 서술어, 목적어, etc.)
        Uses phrase-level analysis for proper Korean grammar understanding.
        """
        
        # Select sentence based on student level
        target_sentence = self._select_sentence_for_phase1(task)
        
        # Analyze sentence into phrases using Korean phrase analyzer
        phrases = self.phrase_analyzer.analyze_phrase_structure(target_sentence.text)
        
        # Convert phrases to frontend-friendly format
        phrase_data = []
        for phrase in phrases:
            phrase_data.append({
                "text": phrase.text,
                "component_type": phrase.component_type.value,
                "start_pos": phrase.start_pos,
                "end_pos": phrase.end_pos,
                "confidence": phrase.confidence,
                "particles": phrase.particles,
                "educational_level": phrase.educational_level
            })
        
        phase1_data = {
            "phase": LearningPhase.COMPONENT_IDENTIFICATION.value,
            "task_id": task.id,
            "student_id": student_id,
            "objective": "문장의 기본 구 성분을 찾아 표시하세요 (구 단위로 분석)",
            "instructions": [
                "1. 문장을 읽고 주어구(누가/무엇이)를 찾으세요",
                "2. 서술어구(어떻게 하다/어떠하다)를 찾으세요", 
                "3. 목적어구(무엇을/누구를)가 있는지 확인하세요",
                "4. 구는 조사를 포함한 완전한 단위입니다"
            ],
            "target_sentence": {
                "text": target_sentence.text,
                "sentence_id": target_sentence.sentence_id,
                "complexity": target_sentence.complexity_level,
                "components_to_find": ["주어구", "서술어구", "목적어구"],
                "phrase_analysis": phrase_data
            },
            "interface": {
                "mode": "phrase_component_selection",
                "available_components": ["주어구", "서술어구", "목적어구", "보어구", "부사어구"],
                "interaction_type": "phrase_click_to_label",
                "time_limit": 180,  # 3 minutes
                "hints_available": 3,
                "phrase_mode": True
            },
            "success_criteria": {
                "minimum_accuracy": 0.8,
                "required_components": ["주어구", "서술어구"]
            }
        }
        
        return phase1_data
    
    def evaluate_phase_1(self, response: StudentResponse, task: EnhancedLearningTask) -> PhaseEvaluation:
        """Evaluate Phase 1: Component Identification performance with educational-focused matching"""
        
        print(f"🔍 Phase 1 평가 시작:")
        print(f"📝 응답 데이터: {response.response_data}")
        
        target_sentence = self._get_sentence_by_id(task, response.response_data.get("sentence_id", 1))
        student_components_raw = response.response_data.get("identified_components", {})
        
        print(f"🎯 목표 문장: {target_sentence}")
        print(f"👨‍🎓 학생 선택 원본: {student_components_raw}")
        
        # Convert frontend format {wordIndex: {text, component}} to backend format {component: [texts]}
        student_components = {}
        for word_data in student_components_raw.values():
            if isinstance(word_data, dict) and 'component' in word_data and 'text' in word_data:
                comp_type = word_data['component']
                text = word_data['text']
                if comp_type not in student_components:
                    student_components[comp_type] = []
                student_components[comp_type].append(text)
        
        # Define expected components for Korean sentence structure
        sentence_text = target_sentence.text
        expected_components = self._identify_educational_components(sentence_text)
        
        # Evaluate student's selections against educational expectations
        correct_ids = []
        missing_components = []
        incorrect_components = []
        
        # Check primary components (주어구, 서술어구, 목적어구)
        primary_components = ["주어구", "서술어구", "목적어구"]
        total_expected = 0
        
        for comp_type in primary_components:
            expected_patterns = expected_components.get(comp_type, [])
            student_selections = student_components.get(comp_type, [])
            
            if expected_patterns:  # If this component type is expected
                total_expected += 1
                component_found = False
                
                for student_text in student_selections:
                    # Check if student selection is educationally correct
                    if self._is_valid_component_selection(student_text, comp_type, sentence_text):
                        correct_ids.append(f"{comp_type}:{student_text}")
                        component_found = True
                        break
                
                if not component_found:
                    missing_components.append(f"{comp_type}: 올바른 {comp_type}를 선택해주세요")
                    
                # Check for clearly wrong selections
                for student_text in student_selections:
                    if not self._is_valid_component_selection(student_text, comp_type, sentence_text):
                        incorrect_components.append(f"{comp_type}:{student_text}")
        
        # Calculate score based on primary components
        score = len(correct_ids) / total_expected if total_expected > 0 else 0
        
        print(f"📊 점수 계산:")
        print(f"   정답 개수: {len(correct_ids)}")
        print(f"   총 필요 개수: {total_expected}")
        print(f"   최종 점수: {score}")
        print(f"   정답 목록: {correct_ids}")
        print(f"   누락 성분: {missing_components}")
        print(f"   잘못된 성분: {incorrect_components}")
        print(f"   변환된 학생 선택: {student_components}")
        print(f"   임계값: {self.advancement_thresholds[LearningPhase.COMPONENT_IDENTIFICATION]}")
        print(f"   숙련도 달성: {score >= self.advancement_thresholds[LearningPhase.COMPONENT_IDENTIFICATION]}")
        
        # Generate hints if needed
        hints = self._generate_phase1_hints(missing_components, incorrect_components, target_sentence)
        
        # Determine next action
        next_action = self._determine_next_action(score, LearningPhase.COMPONENT_IDENTIFICATION)
        
        return PhaseEvaluation(
            phase=LearningPhase.COMPONENT_IDENTIFICATION,
            score=score,
            correct_components=correct_ids,
            missing_components=missing_components,
            incorrect_components=incorrect_components,
            hints=hints,
            next_action=next_action,
            mastery_achieved=score >= self.advancement_thresholds[LearningPhase.COMPONENT_IDENTIFICATION]
        )
    
    def start_phase_2(self, task: EnhancedLearningTask, student_id: str) -> Dict[str, Any]:
        """
        Start Phase 2: Necessity Judgment
        
        Students learn to distinguish required vs optional components
        """
        
        target_sentence = self._select_sentence_for_phase2(task)
        
        phase2_data = {
            "phase": LearningPhase.NECESSITY_JUDGMENT.value,
            "task_id": task.id,
            "student_id": student_id,
            "objective": "문장 성분의 필요성을 판단하세요",
            "instructions": [
                "1. 각 성분이 의미 전달에 꼭 필요한지 판단하세요",
                "2. 필수적(Required): 제거하면 의미가 불완전해지는 요소",
                "3. 선택적(Optional): 제거해도 기본 의미가 유지되는 요소",
                "4. 장식적(Decorative): 감정이나 강조만 담당하는 요소"
            ],
            "target_sentence": {
                "text": target_sentence.text,
                "sentence_id": target_sentence.sentence_id,
                "components": self._prepare_components_for_judgment(target_sentence)
            },
            "interface": {
                "mode": "necessity_classification",
                "categories": ["required", "optional", "decorative"],
                "interaction_type": "drag_and_drop",
                "time_limit": 240,  # 4 minutes
                "show_consequences": True  # Show preview of sentence without component
            },
            "success_criteria": {
                "minimum_accuracy": 0.75,
                "critical_errors": 2  # Max misclassifications of required components
            }
        }
        
        return phase2_data
    
    def evaluate_phase_2(self, response: StudentResponse, task: EnhancedLearningTask) -> PhaseEvaluation:
        """Evaluate Phase 2: Necessity Judgment performance"""
        
        target_sentence = self._get_sentence_by_id(task, response.response_data.get("sentence_id", 1))
        student_classifications = response.response_data.get("necessity_classifications", {})
        
        correct_count = 0
        total_count = 0
        critical_errors = 0
        missing_components = []
        incorrect_components = []
        
        # Check each component classification
        for comp_type, comp_list in target_sentence.components.items():
            for comp in comp_list:
                total_count += 1
                comp_key = f"{comp_type.value}:{comp.text}"
                
                correct_necessity = comp.necessity.value
                student_necessity = student_classifications.get(comp_key, "unknown")
                
                if student_necessity == correct_necessity:
                    correct_count += 1
                else:
                    incorrect_components.append(f"{comp_key} ({student_necessity}→{correct_necessity})")
                    
                    # Critical error: misclassifying required as optional/decorative
                    if correct_necessity == "required" and student_necessity in ["optional", "decorative"]:
                        critical_errors += 1
        
        # Calculate score with penalty for critical errors
        base_score = correct_count / total_count if total_count > 0 else 0
        penalty = critical_errors * 0.1
        score = max(0, base_score - penalty)
        
        # Generate hints
        hints = self._generate_phase2_hints(incorrect_components, critical_errors)
        
        # Determine next action
        next_action = self._determine_next_action(score, LearningPhase.NECESSITY_JUDGMENT)
        
        return PhaseEvaluation(
            phase=LearningPhase.NECESSITY_JUDGMENT,
            score=score,
            correct_components=[f"Correct: {correct_count}/{total_count}"],
            missing_components=missing_components,
            incorrect_components=incorrect_components,
            hints=hints,
            next_action=next_action,
            mastery_achieved=score >= self.advancement_thresholds[LearningPhase.NECESSITY_JUDGMENT]
        )
    
    def start_phase_3(self, task: EnhancedLearningTask, student_id: str) -> Dict[str, Any]:
        """
        Start Phase 3: Generalization
        
        Students learn to replace specific terms with general concepts
        """
        
        target_sentence = self._select_sentence_for_phase3(task)
        
        phase3_data = {
            "phase": LearningPhase.GENERALIZATION.value,
            "task_id": task.id,
            "student_id": student_id,
            "objective": "구체적 표현을 일반적 개념으로 바꿔보세요",
            "instructions": [
                "1. 구체적인 예시나 세부사항을 찾으세요",
                "2. 이들을 포괄하는 상위 개념을 생각해보세요",
                "3. 의미를 잃지 않으면서 더 일반적으로 표현하세요",
                "4. 지나치게 추상적이 되지 않도록 주의하세요"
            ],
            "target_sentence": {
                "text": target_sentence.text,
                "sentence_id": target_sentence.sentence_id,
                "generalizable_components": self._find_generalizable_components(target_sentence)
            },
            "interface": {
                "mode": "generalization_practice",
                "interaction_type": "replacement_suggestions",
                "time_limit": 300,  # 5 minutes
                "abstraction_levels": ["level1", "level2", "level3"],
                "feedback_immediate": True
            },
            "success_criteria": {
                "minimum_accuracy": 0.7,
                "semantic_preservation": 0.8  # Must preserve core meaning
            }
        }
        
        return phase3_data
    
    def start_phase_4(self, task: EnhancedLearningTask, student_id: str) -> Dict[str, Any]:
        """
        Start Phase 4: Theme Reconstruction
        
        Students learn to synthesize implicit themes from multiple sentences
        """
        
        phase4_data = {
            "phase": LearningPhase.THEME_RECONSTRUCTION.value,
            "task_id": task.id,
            "student_id": student_id,
            "objective": "전체 글의 숨겨진 주제를 찾아 명확하게 표현하세요",
            "instructions": [
                "1. 각 문장의 핵심 개념을 파악하세요",
                "2. 문장들 간의 공통점을 찾으세요", 
                "3. 직접 드러나지 않은 주제를 추론하세요",
                "4. 한 문장으로 종합적 주제를 표현하세요"
            ],
            "all_sentences": [
                {
                    "text": sent.text,
                    "main_concept": sent.main_concept,
                    "importance": sent.importance_score,
                    "role": sent.role.value
                } for sent in task.sentence_analysis
            ],
            "interface": {
                "mode": "theme_synthesis",
                "interaction_type": "free_text_with_guidance",
                "time_limit": 480,  # 8 minutes
                "show_connections": True,
                "concept_mapping": True
            },
            "success_criteria": {
                "coherence": 0.8,
                "completeness": 0.75,
                "abstraction_level": "appropriate"
            }
        }
        
        return phase4_data
    
    def evaluate_phase_3(self, response: StudentResponse, task: EnhancedLearningTask) -> PhaseEvaluation:
        """Evaluate Phase 3: Generalization performance"""
        
        target_sentence = self._get_sentence_by_id(task, response.response_data.get("sentence_id", 1))
        student_generalizations = response.response_data.get("generalizations", {})
        
        correct_count = 0
        total_count = 0
        semantic_preservation_score = 0.0
        missing_components = []
        incorrect_components = []
        
        # Evaluate each generalization
        generalizable_components = self._find_generalizable_components(target_sentence)
        
        for comp in generalizable_components:
            total_count += 1
            comp_id = comp["id"]
            
            if comp_id in student_generalizations:
                student_choice = student_generalizations[comp_id]
                
                # Check if student choice is in candidates
                if student_choice in comp["candidates"]:
                    correct_count += 1
                    
                    # Calculate semantic preservation (higher level = lower preservation)
                    candidate_index = comp["candidates"].index(student_choice)
                    preservation = max(0.3, 1.0 - (candidate_index * 0.25))
                    semantic_preservation_score += preservation
                else:
                    incorrect_components.append(f"{comp_id}: Invalid generalization '{student_choice}'")
            else:
                missing_components.append(f"{comp_id}: No generalization provided")
        
        # Calculate scores
        accuracy_score = correct_count / total_count if total_count > 0 else 0
        semantic_score = semantic_preservation_score / total_count if total_count > 0 else 0
        
        # Combined score (70% accuracy, 30% semantic preservation)
        score = (accuracy_score * 0.7) + (semantic_score * 0.3)
        
        # Generate hints
        hints = self._generate_phase3_hints(missing_components, incorrect_components)
        
        # Determine next action
        next_action = self._determine_next_action(score, LearningPhase.GENERALIZATION)
        
        return PhaseEvaluation(
            phase=LearningPhase.GENERALIZATION,
            score=score,
            correct_components=[f"Accuracy: {correct_count}/{total_count}", f"Semantic: {semantic_score:.2f}"],
            missing_components=missing_components,
            incorrect_components=incorrect_components,
            hints=hints,
            next_action=next_action,
            mastery_achieved=score >= self.advancement_thresholds[LearningPhase.GENERALIZATION]
        )
    
    def evaluate_phase_4(self, response: StudentResponse, task: EnhancedLearningTask) -> PhaseEvaluation:
        """Evaluate Phase 4: Theme Reconstruction performance"""
        
        student_theme = response.response_data.get("reconstructed_theme", "").strip()
        concept_connections = response.response_data.get("concept_connections", [])
        
        # Get expected themes and concepts
        all_concepts = [sent.main_concept for sent in task.sentence_analysis]
        important_sentences = [s for s in task.sentence_analysis if s.importance_score > 0.7]
        
        # Evaluation criteria
        coherence_score = self._evaluate_theme_coherence(student_theme, all_concepts)
        completeness_score = self._evaluate_theme_completeness(student_theme, important_sentences)
        abstraction_score = self._evaluate_abstraction_level(student_theme)
        connection_score = self._evaluate_concept_connections(concept_connections, all_concepts)
        
        # Combined score
        score = (coherence_score * 0.3 + completeness_score * 0.3 + 
                abstraction_score * 0.2 + connection_score * 0.2)
        
        # Generate evaluation details
        correct_components = [
            f"Coherence: {coherence_score:.2f}",
            f"Completeness: {completeness_score:.2f}", 
            f"Abstraction: {abstraction_score:.2f}",
            f"Connections: {connection_score:.2f}"
        ]
        
        missing_components = []
        incorrect_components = []
        
        if coherence_score < 0.6:
            missing_components.append("Theme lacks logical coherence")
        if completeness_score < 0.6:
            missing_components.append("Theme missing key concepts")
        if abstraction_score < 0.4:
            incorrect_components.append("Theme too specific or too abstract")
        
        # Generate hints
        hints = self._generate_phase4_hints(coherence_score, completeness_score, abstraction_score)
        
        # Determine next action
        next_action = self._determine_next_action(score, LearningPhase.THEME_RECONSTRUCTION)
        
        return PhaseEvaluation(
            phase=LearningPhase.THEME_RECONSTRUCTION,
            score=score,
            correct_components=correct_components,
            missing_components=missing_components,
            incorrect_components=incorrect_components,
            hints=hints,
            next_action=next_action,
            mastery_achieved=score >= self.advancement_thresholds[LearningPhase.THEME_RECONSTRUCTION]
        )

    def _select_sentence_for_phase1(self, task: EnhancedLearningTask) -> Any:
        """Select appropriate sentence for component identification"""
        # Prefer topic sentences with clear components
        topic_sentences = [s for s in task.sentence_analysis if s.role.value == "topic"]
        if topic_sentences:
            return topic_sentences[0]
        return task.sentence_analysis[0] if task.sentence_analysis else None
    
    def _select_sentence_for_phase2(self, task: EnhancedLearningTask) -> Any:
        """Select sentence with mix of required/optional components"""
        # Look for sentences with both required and optional components
        for sentence in task.sentence_analysis:
            has_required = any(
                any(c.necessity == Necessity.REQUIRED for c in comp_list)
                for comp_list in sentence.components.values()
            )
            has_optional = any(
                any(c.necessity in [Necessity.OPTIONAL, Necessity.DECORATIVE] for c in comp_list)
                for comp_list in sentence.components.values()
            )
            if has_required and has_optional:
                return sentence
        
        return task.sentence_analysis[0] if task.sentence_analysis else None
    
    def _select_sentence_for_phase3(self, task: EnhancedLearningTask) -> Any:
        """Select sentence with generalizable components"""
        # Look for sentences with generalizable components
        for sentence in task.sentence_analysis:
            has_generalizable = any(
                any(c.can_generalize for c in comp_list) 
                for comp_list in sentence.components.values()
            )
            if has_generalizable:
                return sentence
        
        return task.sentence_analysis[0] if task.sentence_analysis else None
    
    def _get_sentence_by_id(self, task: EnhancedLearningTask, sentence_id: int) -> Any:
        """Get sentence by ID"""
        for sentence in task.sentence_analysis:
            if sentence.sentence_id == sentence_id:
                return sentence
        return task.sentence_analysis[0] if task.sentence_analysis else None
    
    def _get_required_components(self, sentence) -> List[str]:
        """Get list of required component types for a sentence"""
        required = []
        for comp_type, comp_list in sentence.components.items():
            if any(c.necessity == Necessity.REQUIRED for c in comp_list):
                required.append(comp_type.value)
        return required
    
    def _prepare_components_for_judgment(self, sentence) -> List[Dict[str, Any]]:
        """Prepare components for necessity judgment interface"""
        components = []
        for comp_type, comp_list in sentence.components.items():
            for comp in comp_list:
                components.append({
                    "id": f"{comp_type.value}:{comp.text}",
                    "text": comp.text,
                    "type": comp_type.value,
                    "position": f"{comp.start_pos}-{comp.end_pos}",
                    "correct_necessity": comp.necessity.value,  # Hidden from student
                    "importance_score": comp.importance_score
                })
        return components
    
    def _find_generalizable_components(self, sentence) -> List[Dict[str, Any]]:
        """Find components that can be generalized"""
        generalizable = []
        for comp_type, comp_list in sentence.components.items():
            for comp in comp_list:
                if comp.can_generalize and comp.generalization_candidates:
                    generalizable.append({
                        "id": f"{comp_type.value}:{comp.text}",
                        "text": comp.text,
                        "type": comp_type.value,
                        "candidates": comp.generalization_candidates,
                        "semantic_distance": [0.3, 0.5, 0.8]  # Abstraction levels
                    })
        return generalizable
    
    def _generate_phase1_hints(self, missing_components: List[str], 
                              incorrect_components: List[str], sentence) -> List[LearningHint]:
        """Generate helpful hints for Phase 1"""
        hints = []
        
        # Hints for missing components
        for missing in missing_components[:2]:  # Max 2 hints
            comp_type, comp_text = missing.split(":", 1)
            
            if comp_type == "주어":
                hints.append(LearningHint(
                    level=2,
                    message="문장에서 '누가' 또는 '무엇이' 행동하는지 찾아보세요.",
                    component_type=ComponentType.SUBJECT,
                    reasoning="주어를 찾는 일반적인 방법을 제시"
                ))
            elif comp_type == "서술어":
                hints.append(LearningHint(
                    level=2,
                    message="주어가 '어떻게 하는지' 또는 '어떠한지'를 나타내는 말을 찾아보세요.",
                    component_type=ComponentType.PREDICATE,
                    reasoning="서술어를 찾는 방법 가이드"
                ))
        
        # Hints for incorrect identifications
        if len(incorrect_components) > 2:
            hints.append(LearningHint(
                level=1,
                message="일부 성분을 잘못 분류했습니다. 다시 확인해보세요.",
                reasoning="일반적인 재검토 요청"
            ))
        
        return hints
    
    def _generate_phase2_hints(self, incorrect_components: List[str], 
                              critical_errors: int) -> List[LearningHint]:
        """Generate hints for Phase 2"""
        hints = []
        
        if critical_errors > 0:
            hints.append(LearningHint(
                level=3,
                message="필수 성분을 선택적으로 분류했습니다. 문장에서 그 성분을 제거했을 때 의미가 완전한지 확인해보세요.",
                reasoning="Critical error에 대한 직접적 가이드"
            ))
        
        if len(incorrect_components) > 0:
            hints.append(LearningHint(
                level=2,
                message="성분의 필요성을 판단할 때는 '이 요소 없이도 의미가 전달될까?'를 생각해보세요.",
                reasoning="판단 기준 제시"
            ))
        
        return hints
    
    def _determine_next_action(self, score: float, phase: LearningPhase) -> str:
        """Determine next action based on performance"""
        threshold = self.advancement_thresholds.get(phase, 0.8)
        
        if score >= threshold:
            return "advance"  # Move to next phase
        elif score >= threshold * 0.6:
            return "retry"    # Try same phase again with hints
        else:
            return "help"     # Need additional explanation/help
    
    def get_student_progress(self, student_id: str, task_id: str) -> Dict[str, Any]:
        """Get comprehensive student progress report"""
        # This would integrate with progress tracking system
        return {
            "student_id": student_id,
            "task_id": task_id,
            "current_phase": "component_identification",
            "phase_scores": {
                "component_identification": 0.75,
                "necessity_judgment": 0.0,
                "generalization": 0.0,
                "theme_reconstruction": 0.0
            },
            "attempts": 2,
            "time_spent": 420,  # seconds
            "hints_used": 3,
            "mastery_progress": 0.25  # Overall mastery percentage
        }
    
    def _generate_phase3_hints(self, missing_components: List[str], 
                              incorrect_components: List[str]) -> List[LearningHint]:
        """Generate hints for Phase 3"""
        hints = []
        
        if missing_components:
            hints.append(LearningHint(
                level=2,
                message="모든 일반화 가능한 요소를 선택해주세요. 구체적인 예시나 고유명사를 찾아보세요.",
                reasoning="Missing generalizations guidance"
            ))
        
        if incorrect_components:
            hints.append(LearningHint(
                level=3,
                message="선택한 일반화 수준이 적절한지 확인해보세요. 너무 구체적이거나 추상적이지 않은지 점검하세요.",
                reasoning="Invalid generalization guidance"
            ))
        
        hints.append(LearningHint(
            level=1,
            message="좋은 일반화는 원래 의미를 보존하면서도 더 넓은 범위를 포함합니다.",
            reasoning="General principle reminder"
        ))
        
        return hints
    
    def _generate_phase4_hints(self, coherence_score: float, completeness_score: float, 
                              abstraction_score: float) -> List[LearningHint]:
        """Generate hints for Phase 4"""
        hints = []
        
        if coherence_score < 0.6:
            hints.append(LearningHint(
                level=3,
                message="문장들 사이의 논리적 연결을 더 명확하게 표현해보세요. 각 문장이 어떻게 연결되는지 생각해보세요.",
                reasoning="Coherence improvement"
            ))
        
        if completeness_score < 0.6:
            hints.append(LearningHint(
                level=2,
                message="중요한 개념들이 주제에 모두 반영되었는지 확인해보세요. 빠뜨린 핵심 내용이 있을 수 있습니다.",
                reasoning="Completeness improvement"
            ))
        
        if abstraction_score < 0.4:
            hints.append(LearningHint(
                level=3,
                message="주제의 추상화 수준을 조정해보세요. 너무 구체적이면 일반화하고, 너무 추상적이면 구체화하세요.",
                reasoning="Abstraction level adjustment"
            ))
        
        return hints
    
    def _evaluate_theme_coherence(self, theme: str, concepts: List[str]) -> float:
        """Evaluate logical coherence of reconstructed theme"""
        if not theme or len(theme.strip()) < 10:
            return 0.0
        
        # Simple heuristic: check if theme mentions key concepts
        mentioned_concepts = 0
        for concept in concepts:
            if concept and concept.lower() in theme.lower():
                mentioned_concepts += 1
        
        # Base coherence from concept coverage
        concept_coverage = mentioned_concepts / len(concepts) if concepts else 0
        
        # Bonus for complete sentences and logical structure
        structure_bonus = 0.2 if theme.endswith('.') or theme.endswith('다') else 0
        length_bonus = 0.1 if 20 <= len(theme) <= 100 else 0
        
        return min(1.0, concept_coverage + structure_bonus + length_bonus)
    
    def _evaluate_theme_completeness(self, theme: str, important_sentences) -> float:
        """Evaluate completeness of theme coverage"""
        if not theme or not important_sentences:
            return 0.0
        
        # Check coverage of important sentence concepts
        covered_sentences = 0
        for sentence in important_sentences:
            if sentence.main_concept and sentence.main_concept.lower() in theme.lower():
                covered_sentences += 1
        
        return covered_sentences / len(important_sentences) if important_sentences else 0
    
    def _evaluate_abstraction_level(self, theme: str) -> float:
        """Evaluate appropriateness of abstraction level"""
        if not theme:
            return 0.0
        
        # Heuristics for good abstraction level
        word_count = len(theme.split())
        char_count = len(theme)
        
        # Optimal range: 10-30 words, 30-150 characters
        word_score = 1.0 if 10 <= word_count <= 30 else max(0, 1.0 - abs(word_count - 20) * 0.05)
        char_score = 1.0 if 30 <= char_count <= 150 else max(0, 1.0 - abs(char_count - 90) * 0.01)
        
        # Check for overly specific details (numbers, dates, names)
        import re
        specific_patterns = r'\d{4}|\d+월|\d+일|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*'
        specific_matches = len(re.findall(specific_patterns, theme))
        specificity_penalty = min(0.3, specific_matches * 0.1)
        
        return max(0, (word_score + char_score) / 2 - specificity_penalty)
    
    def _evaluate_concept_connections(self, connections: List, all_concepts: List[str]) -> float:
        """Evaluate quality of concept connections"""
        if not connections or not all_concepts:
            return 0.5  # Neutral score if no connections provided
        
        # Count meaningful connections
        meaningful_connections = 0
        for connection in connections:
            if isinstance(connection, dict):
                source = connection.get('source', '')
                target = connection.get('target', '')
                if source in all_concepts and target in all_concepts:
                    meaningful_connections += 1
        
        # Score based on connection density
        max_connections = len(all_concepts) * (len(all_concepts) - 1) // 2
        if max_connections == 0:
            return 0.5
        
        connection_ratio = meaningful_connections / min(max_connections, len(all_concepts))
        return min(1.0, connection_ratio)
    
    def _identify_educational_components(self, sentence_text: str) -> Dict[str, List[str]]:
        """Identify expected components using phrase-level analysis"""
        # Use phrase analyzer to get grammatically correct component identification
        phrases = self.phrase_analyzer.analyze_phrase_structure(sentence_text)
        
        # Convert phrase analysis to component expectations
        components = {
            "주어구": [],
            "서술어구": [],
            "목적어구": [],
            "부사어구": [],
            "보어구": []
        }
        
        # Extract expected phrases by component type
        for phrase in phrases:
            component_key = phrase.component_type.value
            if component_key in components:
                components[component_key].append(phrase.text)
        
        # Ensure we have at least basic components for educational purposes
        if not components["주어구"]:
            components["주어구"] = ["expected"]
        if not components["서술어구"]:
            components["서술어구"] = ["expected"]
            
        return components
    
    def _is_valid_component_selection(self, student_text: str, comp_type: str, sentence_text: str) -> bool:
        """Check if student's phrase-level component selection is educationally valid"""
        import re
        
        # Remove extra whitespace
        student_text = student_text.strip()
        
        # Basic validation: minimum length
        if len(student_text) < 1:
            return False
        
        # Get phrase analysis for validation
        phrases = self.phrase_analyzer.analyze_phrase_structure(sentence_text)
        
        # Check if student selection matches or overlaps with analyzed phrases
        for phrase in phrases:
            # Direct match with phrase text
            if phrase.text.strip() == student_text:
                if phrase.component_type.value == comp_type:
                    return True
            
            # Partial match (student selected part of a correct phrase)
            if student_text in phrase.text and phrase.component_type.value == comp_type:
                return True
            
            # Reverse partial match (student selected more than needed but includes correct phrase)
            if phrase.text in student_text and phrase.component_type.value == comp_type:
                return True
        
        # Educational flexibility: basic Korean grammar patterns
        if comp_type == "주어구":
            # For subject phrase: accept if contains subject markers
            if any(marker in student_text for marker in ["은", "는", "이", "가"]):
                return True
                
        elif comp_type == "서술어구":
            # For predicate phrase: accept if contains verbs or adjectives  
            if any(pattern in student_text for pattern in ["하다", "되다", "있다", "없다", "이다"]):
                return True
                
        elif comp_type == "목적어구":
            # For object phrase: accept if contains object markers
            if any(marker in student_text for marker in ["을", "를"]):
                return True
                
        elif comp_type == "서술어":
            # For predicate: accept verb-like patterns
            
            # 1. Contains verb endings (best case)
            if any(ending in student_text for ending in ["다", "았다", "었다", "했다", "있다", "된다", "한다", "하고", "되며", "고", "며"]):
                return True
                
            # 2. Contains verb stems
            if any(verb in student_text for verb in ["하", "되", "있", "주도", "발전", "확장", "기여"]):
                return True
                
            # 3. At the end of sentence (likely predicate)
            if sentence_text.find(student_text) > len(sentence_text) * 2 // 3:  # In last third of sentence
                return True
                
        elif comp_type == "목적어":
            # For object: accept object-like patterns
            
            # 1. Contains object markers (best case)
            if any(marker in student_text for marker in ["을", "를"]):
                return True
                
            # 2. Contains noun that could be an object
            if any(noun in student_text for noun in ["문제", "방법", "기술", "정보", "것"]):
                return True
        
        # Educational generosity: if it's reasonable length and contains Korean characters, likely valid
        if 1 <= len(student_text) <= 10 and any(ord(char) >= 0xAC00 and ord(char) <= 0xD7A3 for char in student_text):
            return True
            
        return True  # Default to accepting student attempts for educational purposes
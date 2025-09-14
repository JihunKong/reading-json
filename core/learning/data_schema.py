#!/usr/bin/env python3
"""
Enhanced data schema for Korean Summary Learning System

This module defines the data structures needed for process-oriented summary learning,
including sentence component analysis, learning scaffolds, and progress tracking.
"""

from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

class TaskType(Enum):
    PARAGRAPH = "paragraph"
    ARTICLE = "article"

class ComponentType(Enum):
    SUBJECT = "주어"        # Subject
    PREDICATE = "서술어"    # Predicate
    OBJECT = "목적어"       # Object
    COMPLEMENT = "보어"     # Complement
    ADVERBIAL = "부사어"    # Adverbial
    MODIFIER = "관형어"     # Modifier

class Necessity(Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    DECORATIVE = "decorative"

class SentenceRole(Enum):
    TOPIC = "topic"
    SUPPORTING = "supporting"
    EXAMPLE = "example"
    CONCLUSION = "conclusion"
    TRANSITION = "transition"

class Difficulty(Enum):
    BASIC = "basic"
    MEDIUM = "medium"
    ADVANCED = "advanced"

class LearningPhase(Enum):
    COMPONENT_IDENTIFICATION = "component_identification"
    NECESSITY_JUDGMENT = "necessity_judgment"
    GENERALIZATION = "generalization"
    THEME_RECONSTRUCTION = "theme_reconstruction"

@dataclass
class ComponentData:
    """Enhanced component data with learning metadata"""
    text: str
    pos_tag: str
    necessity: Necessity
    importance_score: float  # 0-1 scale
    start_pos: int
    end_pos: int
    can_generalize: bool = False
    generalization_candidates: List[str] = field(default_factory=list)
    semantic_role: Optional[str] = None
    modifiers: List['ComponentData'] = field(default_factory=list)

@dataclass
class SentenceData:
    """Enhanced sentence data for learning"""
    sentence_id: int
    text: str
    role: SentenceRole
    components: Dict[ComponentType, List[ComponentData]]
    importance_score: float
    complexity_level: str  # simple, compound, complex
    main_concept: str
    dependency_tree: Optional[Dict] = None

@dataclass
class ConceptMapping:
    """Generalization mapping for learning phase 3"""
    specific_term: str
    general_terms: List[Dict[str, Union[str, int, float]]]
    context: str
    usage_examples: List[str]

@dataclass
class AbstractionRule:
    """Rules for concept abstraction"""
    rule_type: str
    pattern: str
    replacement: str
    confidence: float

@dataclass
class LearningScaffold:
    """Step-by-step learning guidance"""
    step_number: int
    phase: LearningPhase
    objective: str
    instruction: str
    focus_components: List[ComponentType]
    skills_practiced: List[str]
    hints: List[str]
    common_mistakes: List[str]
    success_criteria: Dict[str, Any]

@dataclass
class ProgressiveTask:
    """Progressive difficulty tasks within a phase"""
    level: int
    task_type: str
    complexity: str
    target_output: str
    evaluation_rubric: Dict[str, Any]

@dataclass
class SummaryProgression:
    """4-level summary progression"""
    level_1_extraction: Dict[str, Any]
    level_2_reduction: Dict[str, Any] 
    level_3_generalization: Dict[str, Any]
    level_4_synthesis: Dict[str, Any]

@dataclass
class EvaluationMetrics:
    """Comprehensive evaluation metrics"""
    component_identification: Dict[str, float] = field(default_factory=dict)
    necessity_judgment: Dict[str, int] = field(default_factory=dict)
    generalization_quality: Dict[str, float] = field(default_factory=dict)
    summary_quality: Dict[str, float] = field(default_factory=dict)
    progress_tracking: Dict[str, Union[int, float, str]] = field(default_factory=dict)

@dataclass
class EnhancedLearningTask:
    """Complete enhanced learning task with all educational metadata"""
    
    # Basic task info
    id: str
    version: str = "2.0.0"
    task_type: TaskType = TaskType.PARAGRAPH
    
    # Original content
    original_content: Dict[str, Any] = field(default_factory=dict)
    
    # NLP Analysis results
    sentence_analysis: List[SentenceData] = field(default_factory=list)
    component_structure: Dict[str, Any] = field(default_factory=dict)
    
    # Learning data
    generalization_mappings: Dict[str, List[Union[ConceptMapping, AbstractionRule]]] = field(default_factory=dict)
    learning_scaffolds: Dict[str, List[Union[LearningScaffold, ProgressiveTask]]] = field(default_factory=dict)
    summary_progression: SummaryProgression = None
    
    # Metrics
    evaluation_metrics: EvaluationMetrics = field(default_factory=EvaluationMetrics)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            "id": self.id,
            "version": self.version,
            "task_type": self.task_type.value if isinstance(self.task_type, TaskType) else self.task_type,
            "original_content": self.original_content,
            "sentence_analysis": [],
            "component_structure": self.component_structure,
            "generalization_mappings": {},
            "learning_scaffolds": {},
            "summary_progression": {},
            "evaluation_metrics": {}
        }
        
        # Convert sentence analysis
        for sentence in self.sentence_analysis:
            sentence_dict = {
                "sentence_id": sentence.sentence_id,
                "text": sentence.text,
                "role": sentence.role.value if isinstance(sentence.role, SentenceRole) else sentence.role,
                "components": {},
                "importance_score": sentence.importance_score,
                "complexity_level": sentence.complexity_level,
                "main_concept": sentence.main_concept
            }
            
            # Convert components
            for comp_type, comp_list in sentence.components.items():
                comp_type_key = comp_type.value if isinstance(comp_type, ComponentType) else comp_type
                sentence_dict["components"][comp_type_key] = []
                
                for comp in comp_list:
                    comp_dict = {
                        "text": comp.text,
                        "pos_tag": comp.pos_tag,
                        "necessity": comp.necessity.value if isinstance(comp.necessity, Necessity) else comp.necessity,
                        "importance_score": comp.importance_score,
                        "start_pos": comp.start_pos,
                        "end_pos": comp.end_pos,
                        "can_generalize": comp.can_generalize,
                        "generalization_candidates": comp.generalization_candidates
                    }
                    sentence_dict["components"][comp_type_key].append(comp_dict)
            
            result["sentence_analysis"].append(sentence_dict)
        
        # Convert other fields
        if self.summary_progression:
            result["summary_progression"] = {
                "level_1_extraction": self.summary_progression.level_1_extraction,
                "level_2_reduction": self.summary_progression.level_2_reduction,
                "level_3_generalization": self.summary_progression.level_3_generalization,
                "level_4_synthesis": self.summary_progression.level_4_synthesis
            }
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedLearningTask':
        """Create from dictionary (JSON deserialization)"""
        task = cls(
            id=data["id"],
            version=data.get("version", "2.0.0"),
            task_type=TaskType(data["task_type"]),
            original_content=data.get("original_content", {}),
            component_structure=data.get("component_structure", {}),
            generalization_mappings=data.get("generalization_mappings", {}),
            learning_scaffolds=data.get("learning_scaffolds", {})
        )
        
        # Convert sentence analysis
        for sentence_data in data.get("sentence_analysis", []):
            components = {}
            for comp_type_str, comp_list in sentence_data.get("components", {}).items():
                try:
                    comp_type = ComponentType(comp_type_str)
                except ValueError:
                    continue
                    
                components[comp_type] = []
                for comp_data in comp_list:
                    component = ComponentData(
                        text=comp_data["text"],
                        pos_tag=comp_data["pos_tag"],
                        necessity=Necessity(comp_data["necessity"]),
                        importance_score=comp_data["importance_score"],
                        start_pos=comp_data["start_pos"],
                        end_pos=comp_data["end_pos"],
                        can_generalize=comp_data.get("can_generalize", False),
                        generalization_candidates=comp_data.get("generalization_candidates", [])
                    )
                    components[comp_type].append(component)
            
            sentence = SentenceData(
                sentence_id=sentence_data["sentence_id"],
                text=sentence_data["text"],
                role=SentenceRole(sentence_data["role"]),
                components=components,
                importance_score=sentence_data["importance_score"],
                complexity_level=sentence_data["complexity_level"],
                main_concept=sentence_data["main_concept"]
            )
            task.sentence_analysis.append(sentence)
        
        # Convert summary progression
        if "summary_progression" in data and data["summary_progression"]:
            task.summary_progression = SummaryProgression(
                level_1_extraction=data["summary_progression"].get("level_1_extraction", {}),
                level_2_reduction=data["summary_progression"].get("level_2_reduction", {}),
                level_3_generalization=data["summary_progression"].get("level_3_generalization", {}),
                level_4_synthesis=data["summary_progression"].get("level_4_synthesis", {})
            )
        
        return task

def create_sample_enhanced_task() -> EnhancedLearningTask:
    """Create a sample enhanced learning task for testing"""
    
    # Create sample components
    subject_comp = ComponentData(
        text="민주주의는",
        pos_tag="Noun+Josa",
        necessity=Necessity.REQUIRED,
        importance_score=1.0,
        start_pos=0,
        end_pos=5
    )
    
    predicate_comp = ComponentData(
        text="힘이다",
        pos_tag="Noun+Josa",
        necessity=Necessity.REQUIRED,
        importance_score=0.95,
        start_pos=35,
        end_pos=38
    )
    
    # Create sample sentence
    sentence = SentenceData(
        sentence_id=1,
        text="민주주의는 자유와 평등을 바탕으로 사회적 영향력을 행사하는 강력한 힘이다.",
        role=SentenceRole.TOPIC,
        components={
            ComponentType.SUBJECT: [subject_comp],
            ComponentType.PREDICATE: [predicate_comp]
        },
        importance_score=0.95,
        complexity_level="compound",
        main_concept="민주주의"
    )
    
    # Create enhanced task
    task = EnhancedLearningTask(
        id="enhanced_para_20231015_3872",
        task_type=TaskType.PARAGRAPH,
        original_content={
            "text": "민주주의는 자유와 평등을 바탕으로 사회적 영향력을 행사하는 강력한 힘이다.",
            "topic": "민주주의의 특성",
            "difficulty": Difficulty.MEDIUM.value,
            "word_count": 38,
            "sentence_count": 1
        },
        sentence_analysis=[sentence]
    )
    
    # Add summary progression
    task.summary_progression = SummaryProgression(
        level_1_extraction={
            "target": "핵심 성분 식별",
            "output": ["민주주의", "힘", "자유", "평등", "사회적 영향력"],
            "retained_elements": ["주어", "서술어", "핵심 개념"],
            "removed_elements": ["수식어", "부사어구"]
        },
        level_2_reduction={
            "target": "불필요한 수식어 제거",
            "output": "민주주의는 자유와 평등을 바탕으로 하는 힘이다",
            "compression_ratio": 0.75
        },
        level_3_generalization={
            "target": "개념 일반화 적용",
            "output": "민주주의는 핵심 가치를 기반으로 하는 체제이다",
            "abstraction_level": 2
        },
        level_4_synthesis={
            "target": "최종 요약 완성",
            "output": "민주주의는 자유와 평등에 기반한 정치적 힘이다",
            "quality_score": 0.92
        }
    )
    
    return task

# JSON Schema validation
ENHANCED_TASK_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "EnhancedLearningTask",
    "required": ["id", "version", "task_type", "original_content"],
    "properties": {
        "id": {"type": "string"},
        "version": {"type": "string", "default": "2.0.0"},
        "task_type": {"type": "string", "enum": ["paragraph", "article"]},
        "original_content": {"type": "object"},
        "sentence_analysis": {"type": "array"},
        "component_structure": {"type": "object"},
        "generalization_mappings": {"type": "object"},
        "learning_scaffolds": {"type": "object"},
        "summary_progression": {"type": "object"},
        "evaluation_metrics": {"type": "object"}
    }
}
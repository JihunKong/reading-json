#!/usr/bin/env python3
"""
Data Migration Script for Korean Summary Learning System

Migrates existing parallel_sets tasks to the new enhanced format with
sentence component analysis and learning scaffolds.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import re
from datetime import datetime

# Add project root to path
sys.path.append('/Users/jihunkong/reading-json')

from core.nlp.korean_analyzer import KoreanSentenceAnalyzer
from core.learning.data_schema import (
    EnhancedLearningTask, TaskType, SentenceData, ComponentData,
    SentenceRole, ComponentType, Necessity, SummaryProgression
)

class TaskMigrationEngine:
    """
    Migrates existing Korean reading tasks to enhanced learning format.
    """
    
    def __init__(self, output_dir: str = "/Users/jihunkong/reading-json/data/enhanced_tasks"):
        self.analyzer = KoreanSentenceAnalyzer()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics tracking
        self.stats = {
            "total_processed": 0,
            "successful_migrations": 0,
            "failed_migrations": 0,
            "paragraph_tasks": 0,
            "article_tasks": 0
        }
        
        print(f"✅ Migration engine initialized")
        print(f"📁 Output directory: {self.output_dir}")
    
    def find_all_tasks(self, search_dirs: List[str]) -> List[Path]:
        """Find all existing task JSON files"""
        
        task_files = []
        
        for search_dir in search_dirs:
            search_path = Path(search_dir)
            if not search_path.exists():
                print(f"⚠️  Directory not found: {search_dir}")
                continue
            
            # Find all JSON files
            for json_file in search_path.rglob("*.json"):
                # Skip non-task files
                if any(skip in str(json_file) for skip in ['final_report', 'metadata', 'schema']):
                    continue
                
                task_files.append(json_file)
        
        print(f"📊 Found {len(task_files)} task files")
        return sorted(task_files)
    
    def load_original_task(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load and validate original task"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                task_data = json.load(f)
            
            # Basic validation
            if 'id' not in task_data:
                print(f"⚠️  Missing ID in {file_path}")
                return None
                
            return task_data
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error in {file_path}: {e}")
            return None
        except Exception as e:
            print(f"❌ Error loading {file_path}: {e}")
            return None
    
    def extract_content_text(self, task_data: Dict[str, Any]) -> str:
        """Extract text content from various task formats"""
        
        # Method 1: Direct content field
        if 'content' in task_data and isinstance(task_data['content'], str):
            return task_data['content']
        
        # Method 2: Paragraph text field
        if 'paragraph' in task_data and 'text' in task_data['paragraph']:
            return task_data['paragraph']['text']
        
        # Method 3: Article paragraphs
        if 'article' in task_data and 'paragraphs' in task_data['article']:
            paragraphs = task_data['article']['paragraphs']
            if isinstance(paragraphs, list):
                return ' '.join(paragraphs)
        
        # Method 4: Look for text in various locations
        for key in ['text', 'content_text', 'original_text']:
            if key in task_data and isinstance(task_data[key], str):
                return task_data[key]
        
        print(f"⚠️  Could not extract content from task {task_data.get('id', 'unknown')}")
        return ""
    
    def determine_task_type(self, task_data: Dict[str, Any]) -> TaskType:
        """Determine task type from original data"""
        
        task_type = task_data.get('task_type', '')
        
        if task_type in ['article', 'art']:
            return TaskType.ARTICLE
        elif task_type in ['paragraph', 'para']:
            return TaskType.PARAGRAPH
        
        # Fallback: check ID pattern
        task_id = task_data.get('id', '')
        if task_id.startswith('art_'):
            return TaskType.ARTICLE
        elif task_id.startswith('para_'):
            return TaskType.PARAGRAPH
        
        # Default to paragraph
        return TaskType.PARAGRAPH
    
    def create_original_content_metadata(self, task_data: Dict[str, Any], content_text: str) -> Dict[str, Any]:
        """Create original content metadata"""
        
        word_count = len(content_text.replace(' ', ''))
        sentence_count = len(re.split(r'[.!?]\s*', content_text.strip()))
        
        return {
            "text": content_text,
            "topic": task_data.get('topic', 'Unknown Topic'),
            "difficulty": task_data.get('difficulty', 'medium'),
            "word_count": word_count,
            "sentence_count": sentence_count,
            "source": task_data.get('source', 'parallel_sets_migration'),
            "original_format": task_data.get('task_type', 'paragraph')
        }
    
    def create_learning_scaffolds(self, task_type: TaskType, difficulty: str) -> Dict[str, Any]:
        """Create learning scaffolds based on task characteristics"""
        
        scaffolds = {
            "steps": [
                {
                    "step_number": 1,
                    "phase": "component_identification",
                    "objective": "핵심 문장 성분 파악",
                    "instruction": "문장에서 주어와 서술어를 찾아 표시하세요",
                    "focus_components": ["주어", "서술어"],
                    "skills_practiced": ["문장 구조 분석", "핵심 요소 식별"],
                    "hints": ["주어는 '무엇이/누가'에 해당", "서술어는 '어떠하다/무엇이다'에 해당"],
                    "common_mistakes": ["복잡한 수식어를 주어로 착각", "보조 서술어를 주 서술어로 혼동"],
                    "success_criteria": {
                        "minimum_accuracy": 0.8,
                        "time_limit": 120
                    }
                },
                {
                    "step_number": 2,
                    "phase": "necessity_judgment", 
                    "objective": "필수/선택 요소 구분",
                    "instruction": "문장의 의미 전달에 꼭 필요한 요소와 부가적 요소를 구분하세요",
                    "focus_components": ["목적어", "부사어", "관형어"],
                    "skills_practiced": ["중요도 판단", "요약 준비"],
                    "hints": ["제거해도 기본 의미가 유지되면 선택적 요소입니다"],
                    "common_mistakes": ["감정적 수식어를 필수로 분류"],
                    "success_criteria": {
                        "minimum_accuracy": 0.75
                    }
                },
                {
                    "step_number": 3,
                    "phase": "generalization",
                    "objective": "개념 일반화 적용",
                    "instruction": "구체적 표현을 상위 개념으로 바꿔보세요",
                    "focus_components": ["개념어", "상위어"],
                    "skills_practiced": ["추상화", "개념 계층 이해"],
                    "hints": ["구체적 예시를 일반적 범주로 변환하세요"],
                    "common_mistakes": ["과도한 일반화로 의미 손실"],
                    "success_criteria": {
                        "semantic_preservation": 0.8
                    }
                }
            ],
            "progressive_tasks": [
                {
                    "level": 1,
                    "task_type": "component_extraction",
                    "complexity": difficulty,
                    "target_output": "핵심 성분 추출",
                    "evaluation_rubric": {
                        "required_components": ["주어", "서술어"],
                        "max_words": 10
                    }
                },
                {
                    "level": 2,
                    "task_type": "structured_summary",
                    "complexity": difficulty,
                    "target_output": "구조화된 요약",
                    "evaluation_rubric": {
                        "required_elements": ["핵심 개념", "논리적 연결"],
                        "max_words": 20
                    }
                }
            ]
        }
        
        # Adjust for article vs paragraph
        if task_type == TaskType.ARTICLE:
            scaffolds["steps"][0]["instruction"] = "글 전체에서 각 문단의 핵심 성분을 파악하세요"
            scaffolds["progressive_tasks"][1]["evaluation_rubric"]["max_words"] = 30
        
        return scaffolds
    
    def extract_existing_answers(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract existing model answers for summary progression"""
        
        progression = {
            "level_1_extraction": {
                "target": "핵심 성분 식별", 
                "output": [],
                "retained_elements": ["주어", "서술어"],
                "removed_elements": ["수식어", "부가 설명"]
            },
            "level_2_reduction": {
                "target": "불필요 요소 제거",
                "output": "",
                "compression_ratio": 0.7
            },
            "level_3_generalization": {
                "target": "개념 일반화",
                "output": "",
                "abstraction_level": 1
            },
            "level_4_synthesis": {
                "target": "최종 요약",
                "output": "",
                "quality_score": 0.0
            }
        }
        
        # Try to extract from q_topic_free
        if 'q_topic_free' in task_data:
            topic_data = task_data['q_topic_free']
            
            # Model answer
            model_answer = (topic_data.get('answer') or 
                          topic_data.get('target_answer') or
                          topic_data.get('target_topic') or "")
            
            if model_answer:
                progression["level_4_synthesis"]["output"] = model_answer
                progression["level_4_synthesis"]["quality_score"] = 0.9
                
                # Generate intermediate levels based on model answer
                words = model_answer.split()
                progression["level_1_extraction"]["output"] = words[:len(words)//2]
                progression["level_2_reduction"]["output"] = model_answer
                progression["level_3_generalization"]["output"] = model_answer
        
        return progression
    
    def migrate_single_task(self, file_path: Path) -> Optional[EnhancedLearningTask]:
        """Migrate a single task to enhanced format"""
        
        try:
            # Load original task
            original_data = self.load_original_task(file_path)
            if not original_data:
                return None
            
            # Extract basic info
            task_id = original_data['id']
            task_type = self.determine_task_type(original_data)
            content_text = self.extract_content_text(original_data)
            
            if not content_text.strip():
                print(f"⚠️  Empty content in task {task_id}")
                return None
            
            print(f"📝 Processing: {task_id} ({task_type.value})")
            
            # Analyze content with NLP
            sentence_analyses = self.analyzer.analyze_paragraph(content_text)
            
            # Convert to enhanced format
            enhanced_sentence_data = []
            for analysis in sentence_analyses:
                # Convert components to new format
                enhanced_components = {}
                for comp_type_str, comp_list in analysis.components.items():
                    try:
                        comp_type = ComponentType(comp_type_str)
                    except ValueError:
                        continue
                    
                    enhanced_components[comp_type] = []
                    for comp in comp_list:
                        enhanced_comp = ComponentData(
                            text=comp.text,
                            pos_tag=comp.pos_tag,
                            necessity=comp.necessity,
                            importance_score=comp.importance_score,
                            start_pos=comp.start_pos,
                            end_pos=comp.end_pos
                        )
                        enhanced_components[comp_type].append(enhanced_comp)
                
                # Create enhanced sentence
                enhanced_sentence = SentenceData(
                    sentence_id=len(enhanced_sentence_data) + 1,
                    text=analysis.original_text,
                    role=SentenceRole(analysis.sentence_role),
                    components=enhanced_components,
                    importance_score=analysis.importance_score,
                    complexity_level=analysis.complexity_level,
                    main_concept=analysis.main_concept
                )
                enhanced_sentence_data.append(enhanced_sentence)
            
            # Create enhanced task
            enhanced_task = EnhancedLearningTask(
                id=f"enhanced_{task_id}",
                version="2.0.0",
                task_type=task_type,
                original_content=self.create_original_content_metadata(original_data, content_text),
                sentence_analysis=enhanced_sentence_data,
                component_structure={
                    "total_sentences": len(enhanced_sentence_data),
                    "complexity_distribution": {},
                    "main_concepts": [s.main_concept for s in enhanced_sentence_data]
                },
                learning_scaffolds=self.create_learning_scaffolds(task_type, 
                                                                original_data.get('difficulty', 'medium')),
                generalization_mappings={
                    "concept_hierarchy": [],
                    "abstraction_rules": []
                }
            )
            
            # Add summary progression
            progression_data = self.extract_existing_answers(original_data)
            enhanced_task.summary_progression = SummaryProgression(
                level_1_extraction=progression_data["level_1_extraction"],
                level_2_reduction=progression_data["level_2_reduction"],
                level_3_generalization=progression_data["level_3_generalization"],
                level_4_synthesis=progression_data["level_4_synthesis"]
            )
            
            return enhanced_task
            
        except Exception as e:
            print(f"❌ Error migrating {file_path}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_enhanced_task(self, task: EnhancedLearningTask) -> bool:
        """Save enhanced task to JSON file"""
        
        try:
            output_file = self.output_dir / f"{task.id}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(task.to_dict(), f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving {task.id}: {e}")
            return False
    
    def migrate_all_tasks(self, search_dirs: List[str], max_tasks: Optional[int] = None) -> Dict[str, int]:
        """Migrate all tasks in the given directories"""
        
        print("🚀 Starting task migration process...")
        
        # Find all task files
        task_files = self.find_all_tasks(search_dirs)
        
        if max_tasks:
            task_files = task_files[:max_tasks]
            print(f"📊 Limiting to first {max_tasks} tasks")
        
        # Process each task
        for i, file_path in enumerate(task_files, 1):
            print(f"\n[{i}/{len(task_files)}] Processing: {file_path.name}")
            
            self.stats["total_processed"] += 1
            
            # Migrate task
            enhanced_task = self.migrate_single_task(file_path)
            
            if enhanced_task:
                # Save enhanced task
                if self.save_enhanced_task(enhanced_task):
                    self.stats["successful_migrations"] += 1
                    
                    # Track task types
                    if enhanced_task.task_type == TaskType.PARAGRAPH:
                        self.stats["paragraph_tasks"] += 1
                    else:
                        self.stats["article_tasks"] += 1
                        
                    print(f"✅ Successfully migrated: {enhanced_task.id}")
                else:
                    self.stats["failed_migrations"] += 1
            else:
                self.stats["failed_migrations"] += 1
        
        # Print final statistics
        self.print_migration_summary()
        
        return self.stats
    
    def print_migration_summary(self):
        """Print migration statistics"""
        
        print("\n" + "="*60)
        print("📊 MIGRATION SUMMARY")
        print("="*60)
        print(f"Total processed:       {self.stats['total_processed']}")
        print(f"Successful migrations: {self.stats['successful_migrations']}")
        print(f"Failed migrations:     {self.stats['failed_migrations']}")
        print(f"Paragraph tasks:       {self.stats['paragraph_tasks']}")
        print(f"Article tasks:         {self.stats['article_tasks']}")
        
        if self.stats['total_processed'] > 0:
            success_rate = (self.stats['successful_migrations'] / self.stats['total_processed']) * 100
            print(f"Success rate:          {success_rate:.1f}%")
        
        print(f"Output directory:      {self.output_dir}")
        print("="*60)

def main():
    """Main migration function"""
    
    # Configuration
    search_directories = [
        "/Users/jihunkong/reading-json/generator/parallel_sets",
        "/Users/jihunkong/reading-json/generator/set_1",
        "/Users/jihunkong/reading-json/generator/set_2", 
        "/Users/jihunkong/reading-json/generator/set_3",
        "/Users/jihunkong/reading-json/generator/set_4"
    ]
    
    # Create migration engine
    migration_engine = TaskMigrationEngine()
    
    # Run migration (limit to 20 for testing)
    stats = migration_engine.migrate_all_tasks(search_directories, max_tasks=20)
    
    print(f"\n🎉 Migration completed!")
    print(f"📁 Enhanced tasks saved to: {migration_engine.output_dir}")

if __name__ == "__main__":
    main()
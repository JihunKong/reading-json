#!/usr/bin/env python3
"""
Educational Intervention System
- Automatic intervention triggers
- Personalized hint generation
- Adaptive difficulty adjustment
- Collaborative learning facilitation
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random
import threading

from app.teacher_data_manager import data_manager, StudentSession, StudentStatus
from app.analytics_engine import analytics_engine

class InterventionType(Enum):
    AUTOMATIC = "automatic"       # System-triggered
    TEACHER_INITIATED = "teacher_initiated"  # Teacher-triggered
    PEER_ASSISTANCE = "peer_assistance"      # Student-to-student
    ADAPTIVE_CONTENT = "adaptive_content"    # Content adjustment

class InterventionSeverity(Enum):
    LOW = "low"           # Gentle nudge
    MEDIUM = "medium"     # Active assistance
    HIGH = "high"         # Direct intervention
    CRITICAL = "critical" # Immediate teacher attention

class HintLevel(Enum):
    GENTLE = 1           # Encouraging reminder
    SPECIFIC = 2         # Point in right direction
    DETAILED = 3         # Show method/approach
    SOLUTION = 4         # Reveal answer

@dataclass
class InterventionAction:
    """Individual intervention action"""
    action_id: str
    student_id: str
    intervention_type: InterventionType
    severity: InterventionSeverity
    
    # Content
    title: str
    message: str
    
    # Context (non-default fields must come before default fields)
    phase: int
    trigger_reason: str
    
    # Optional fields with defaults
    hint_level: Optional[HintLevel] = None
    confidence: float = 1.0  # How confident we are in this intervention
    
    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    delivered_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    
    # Effectiveness tracking
    effectiveness_score: Optional[float] = None  # 0-1, measured after intervention
    student_feedback: Optional[str] = None

@dataclass
class CollaborativeSession:
    """Peer learning session"""
    session_id: str
    mentor_student_id: str
    mentee_student_id: str
    topic: str
    phase: int
    
    # Status
    status: str = "active"  # active, completed, cancelled
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    # Outcome
    success: Optional[bool] = None
    feedback: Dict[str, str] = field(default_factory=dict)

class EducationalInterventionSystem:
    """
    Comprehensive intervention system for struggling learners
    - Automatic detection of learning difficulties
    - Personalized intervention strategies
    - Peer collaboration facilitation
    - Adaptive content delivery
    """
    
    def __init__(self):
        self.active_interventions: Dict[str, InterventionAction] = {}
        self.intervention_history: List[InterventionAction] = []
        self.collaborative_sessions: Dict[str, CollaborativeSession] = {}
        
        # Intervention thresholds and rules
        self.intervention_rules = {
            'consecutive_wrong_threshold': 2,
            'time_stuck_threshold': 180,  # seconds
            'hint_overuse_threshold': 4,
            'inactivity_threshold': 300,  # seconds
            'performance_drop_threshold': 0.3
        }
        
        # Hint templates for different phases and situations
        self.hint_templates = self._initialize_hint_templates()
        
        # Start monitoring thread
        self.monitoring_active = True
        self._start_monitoring_thread()
        
        print("✅ Educational Intervention System initialized")
    
    def _initialize_hint_templates(self) -> Dict[str, Dict[int, List[str]]]:
        """Initialize hint templates for different phases and levels"""
        return {
            "component_identification": {
                1: [  # Gentle hints
                    "문장을 다시 한 번 천천히 읽어보세요.",
                    "주어와 서술어를 찾는 것부터 시작해보세요.",
                    "문장에서 '누가' 하는지 찾아보세요."
                ],
                2: [  # Specific hints
                    "이 문장에서 주어는 '{subject}'입니다.",
                    "동작을 나타내는 말을 찾아보세요.",
                    "'을/를'이 붙은 단어를 찾아보세요."
                ],
                3: [  # Detailed hints
                    "주어: {subject}, 서술어: {predicate}를 확인하세요.",
                    "문장 구조를 이렇게 나누어 생각해보세요: [주어] [목적어] [서술어]"
                ],
                4: [  # Solution hints
                    "정답: 주어는 '{subject}', 서술어는 '{predicate}'입니다."
                ]
            },
            "necessity_judgment": {
                1: [
                    "각 성분이 문장에 꼭 필요한지 생각해보세요.",
                    "이 말을 빼면 문장이 이상해질까요?",
                    "핵심 의미를 전달하는 데 필수적인 부분을 찾아보세요."
                ],
                2: [
                    "'{component}'를 제거했을 때 문장이 어떻게 될지 상상해보세요.",
                    "필수적인 성분과 부가적인 성분을 구분해보세요.",
                    "문장의 기본 뼈대를 이루는 부분을 찾아보세요."
                ],
                3: [
                    "필수: 없으면 문장이 불완전, 선택적: 있어도 없어도 의미 전달 가능",
                    "'{component}'는 {necessity_reason}이므로 {necessity_level}입니다."
                ],
                4: [
                    "정답: '{component}'는 {correct_necessity}입니다."
                ]
            },
            "generalization": {
                1: [
                    "구체적인 예시를 더 일반적인 개념으로 바꿔보세요.",
                    "이 단어를 포함하는 더 큰 범주가 있을까요?",
                    "비슷한 성격의 다른 것들과 묶을 수 있을까요?"
                ],
                2: [
                    "'{specific_term}'보다 더 포괄적인 말을 생각해보세요.",
                    "상위 개념으로 올라가되, 너무 추상적이 되지 않게 하세요.",
                    "의미를 유지하면서 더 일반적으로 표현해보세요."
                ],
                3: [
                    "'{specific_term}' → '{general_term}'로 바꿔보는 것은 어떨까요?",
                    "추상화 수준을 {level}정도로 조정해보세요."
                ],
                4: [
                    "정답: '{specific_term}'는 '{correct_generalization}'로 일반화할 수 있습니다."
                ]
            },
            "theme_reconstruction": {
                1: [
                    "각 문장의 핵심 내용을 먼저 파악해보세요.",
                    "전체적으로 무엇에 대한 이야기인지 생각해보세요.",
                    "모든 문장을 관통하는 공통 주제를 찾아보세요."
                ],
                2: [
                    "문장 간의 연결고리를 찾아보세요.",
                    "핵심 키워드들을 조합해서 주제를 만들어보세요.",
                    "글쓴이가 정말 말하고 싶은 것은 무엇일까요?"
                ],
                3: [
                    "이 글의 핵심 메시지는 '{theme_hint}'와 관련이 있습니다.",
                    "'{concept1}'과 '{concept2}'를 연결해서 생각해보세요."
                ],
                4: [
                    "이 글의 주제는 '{correct_theme}'입니다."
                ]
            }
        }
    
    def monitor_student_progress(self, student_id: str) -> List[InterventionAction]:
        """Monitor individual student and generate interventions if needed"""
        if student_id not in data_manager.sessions:
            return []
        
        session = data_manager.sessions[student_id]
        interventions = []
        
        # Check various intervention triggers
        interventions.extend(self._check_performance_triggers(session))
        interventions.extend(self._check_behavioral_triggers(session))
        interventions.extend(self._check_engagement_triggers(session))
        interventions.extend(self._check_collaboration_opportunities(session))
        
        # Execute interventions
        for intervention in interventions:
            self._execute_intervention(intervention)
        
        return interventions
    
    def _check_performance_triggers(self, session: StudentSession) -> List[InterventionAction]:
        """Check for performance-based intervention triggers"""
        interventions = []
        
        # Consecutive wrong answers
        if session.consecutive_wrong >= self.intervention_rules['consecutive_wrong_threshold']:
            severity = InterventionSeverity.MEDIUM if session.consecutive_wrong <= 3 else InterventionSeverity.HIGH
            
            intervention = self._create_hint_intervention(
                session=session,
                severity=severity,
                trigger_reason=f"consecutive_wrong_{session.consecutive_wrong}",
                hint_level=HintLevel.SPECIFIC if session.consecutive_wrong <= 3 else HintLevel.DETAILED
            )
            interventions.append(intervention)
        
        # Performance drop detection
        if len(session.accuracy_trend) >= 5:
            recent_avg = sum(session.accuracy_trend[-3:]) / 3
            earlier_avg = sum(session.accuracy_trend[-5:-2]) / 3
            
            if earlier_avg - recent_avg > self.intervention_rules['performance_drop_threshold']:
                intervention = self._create_performance_intervention(
                    session=session,
                    severity=InterventionSeverity.MEDIUM,
                    trigger_reason="performance_drop",
                    drop_amount=earlier_avg - recent_avg
                )
                interventions.append(intervention)
        
        # Stuck on same phase too long
        if session.current_question_start:
            time_stuck = (datetime.now() - session.current_question_start).total_seconds()
            if time_stuck > self.intervention_rules['time_stuck_threshold']:
                intervention = self._create_time_intervention(
                    session=session,
                    severity=InterventionSeverity.MEDIUM,
                    trigger_reason="time_stuck",
                    stuck_time=int(time_stuck)
                )
                interventions.append(intervention)
        
        return interventions
    
    def _check_behavioral_triggers(self, session: StudentSession) -> List[InterventionAction]:
        """Check for behavioral intervention triggers"""
        interventions = []
        
        # Hint overuse
        current_phase_hints = session.hints_used.get(session.current_phase, 0)
        if current_phase_hints >= self.intervention_rules['hint_overuse_threshold']:
            intervention = self._create_behavioral_intervention(
                session=session,
                severity=InterventionSeverity.HIGH,
                trigger_reason="hint_overuse",
                behavior_type="dependency"
            )
            interventions.append(intervention)
        
        # Help request pattern
        if session.help_requested and session.status == StudentStatus.STRUGGLING:
            intervention = self._create_teacher_notification(
                session=session,
                severity=InterventionSeverity.HIGH,
                trigger_reason="help_requested",
                message=f"{session.student_name}님이 도움을 요청했습니다"
            )
            interventions.append(intervention)
        
        return interventions
    
    def _check_engagement_triggers(self, session: StudentSession) -> List[InterventionAction]:
        """Check for engagement-related triggers"""
        interventions = []
        
        # Inactivity detection
        if session.last_activity:
            inactive_time = (datetime.now() - session.last_activity).total_seconds()
            if inactive_time > self.intervention_rules['inactivity_threshold']:
                intervention = self._create_engagement_intervention(
                    session=session,
                    severity=InterventionSeverity.LOW,
                    trigger_reason="inactivity",
                    inactive_time=int(inactive_time)
                )
                interventions.append(intervention)
        
        return interventions
    
    def _check_collaboration_opportunities(self, session: StudentSession) -> List[InterventionAction]:
        """Check for peer collaboration opportunities"""
        interventions = []
        
        # Only suggest collaboration if student is struggling but not critically
        if (session.status == StudentStatus.STRUGGLING and 
            session.consecutive_wrong >= 2 and 
            session.consecutive_wrong <= 4):
            
            # Find potential mentor
            mentor_id = self._find_peer_mentor(session)
            if mentor_id:
                intervention = self._create_collaboration_intervention(
                    session=session,
                    mentor_id=mentor_id,
                    severity=InterventionSeverity.MEDIUM,
                    trigger_reason="peer_assistance_opportunity"
                )
                interventions.append(intervention)
        
        return interventions
    
    def _create_hint_intervention(self, session: StudentSession, severity: InterventionSeverity,
                                trigger_reason: str, hint_level: HintLevel) -> InterventionAction:
        """Create a hint-based intervention"""
        
        phase_name = self._get_phase_name(session.current_phase)
        hint_templates = self.hint_templates.get(phase_name, {})
        
        # Get appropriate hint based on level
        hints = hint_templates.get(hint_level.value, ["계속해서 노력해보세요!"])
        hint_message = random.choice(hints)
        
        # Personalize hint with context
        hint_message = self._personalize_hint(hint_message, session)
        
        action_id = f"hint_{session.student_id}_{int(datetime.now().timestamp())}"
        
        return InterventionAction(
            action_id=action_id,
            student_id=session.student_id,
            intervention_type=InterventionType.AUTOMATIC,
            severity=severity,
            title=f"{session.current_phase}단계 학습 도움",
            message=hint_message,
            hint_level=hint_level,
            phase=session.current_phase,
            trigger_reason=trigger_reason,
            confidence=0.8
        )
    
    def _create_performance_intervention(self, session: StudentSession, severity: InterventionSeverity,
                                       trigger_reason: str, drop_amount: float) -> InterventionAction:
        """Create performance-focused intervention"""
        
        action_id = f"performance_{session.student_id}_{int(datetime.now().timestamp())}"
        
        message = f"최근 성과가 조금 낮아졌습니다. 기본기를 다시 한번 점검해보세요."
        if drop_amount > 0.5:
            message = "성과가 많이 떨어졌습니다. 잠시 휴식을 취하거나 이전 단계를 복습해보세요."
        
        return InterventionAction(
            action_id=action_id,
            student_id=session.student_id,
            intervention_type=InterventionType.AUTOMATIC,
            severity=severity,
            title="학습 성과 개선",
            message=message,
            phase=session.current_phase,
            trigger_reason=trigger_reason,
            confidence=0.7
        )
    
    def _create_time_intervention(self, session: StudentSession, severity: InterventionSeverity,
                                trigger_reason: str, stuck_time: int) -> InterventionAction:
        """Create time-based intervention"""
        
        action_id = f"time_{session.student_id}_{int(datetime.now().timestamp())}"
        
        minutes_stuck = stuck_time // 60
        if minutes_stuck < 5:
            message = "시간을 충분히 가지고 차근차근 생각해보세요."
        elif minutes_stuck < 10:
            message = "너무 오래 고민하고 있습니다. 힌트를 사용하거나 도움을 요청해보세요."
        else:
            message = "많이 어려워하고 있네요. 선생님께 도움을 요청하는 것이 좋겠습니다."
        
        return InterventionAction(
            action_id=action_id,
            student_id=session.student_id,
            intervention_type=InterventionType.AUTOMATIC,
            severity=severity,
            title="학습 시간 관리",
            message=message,
            phase=session.current_phase,
            trigger_reason=trigger_reason,
            confidence=0.9
        )
    
    def _create_behavioral_intervention(self, session: StudentSession, severity: InterventionSeverity,
                                      trigger_reason: str, behavior_type: str) -> InterventionAction:
        """Create behavior-focused intervention"""
        
        action_id = f"behavior_{session.student_id}_{int(datetime.now().timestamp())}"
        
        if behavior_type == "dependency":
            message = "힌트에 너무 의존하고 있습니다. 스스로 생각해보는 시간을 가져보세요."
            title = "독립적 학습 유도"
        else:
            message = "학습 방법을 조정해보세요."
            title = "학습 방법 개선"
        
        return InterventionAction(
            action_id=action_id,
            student_id=session.student_id,
            intervention_type=InterventionType.AUTOMATIC,
            severity=severity,
            title=title,
            message=message,
            phase=session.current_phase,
            trigger_reason=trigger_reason,
            confidence=0.6
        )
    
    def _create_engagement_intervention(self, session: StudentSession, severity: InterventionSeverity,
                                      trigger_reason: str, inactive_time: int) -> InterventionAction:
        """Create engagement-focused intervention"""
        
        action_id = f"engagement_{session.student_id}_{int(datetime.now().timestamp())}"
        
        minutes_inactive = inactive_time // 60
        if minutes_inactive < 3:
            message = "잠깐 멈춰 있네요. 계속해서 문제를 풀어보세요!"
        elif minutes_inactive < 8:
            message = "오랫동안 활동이 없습니다. 계속 참여하고 있나요?"
        else:
            message = "너무 오랫동안 반응이 없습니다. 도움이 필요하거나 문제가 있다면 알려주세요."
        
        return InterventionAction(
            action_id=action_id,
            student_id=session.student_id,
            intervention_type=InterventionType.AUTOMATIC,
            severity=severity,
            title="참여도 향상",
            message=message,
            phase=session.current_phase,
            trigger_reason=trigger_reason,
            confidence=0.8
        )
    
    def _create_collaboration_intervention(self, session: StudentSession, mentor_id: str,
                                         severity: InterventionSeverity, trigger_reason: str) -> InterventionAction:
        """Create peer collaboration intervention"""
        
        action_id = f"collab_{session.student_id}_{int(datetime.now().timestamp())}"
        
        mentor_session = data_manager.sessions.get(mentor_id)
        mentor_name = mentor_session.student_name if mentor_session else "동료"
        
        message = f"{mentor_name}님이 도움을 줄 수 있습니다. 함께 학습해보시겠어요?"
        
        return InterventionAction(
            action_id=action_id,
            student_id=session.student_id,
            intervention_type=InterventionType.PEER_ASSISTANCE,
            severity=severity,
            title="동료 학습 제안",
            message=message,
            phase=session.current_phase,
            trigger_reason=trigger_reason,
            confidence=0.7
        )
    
    def _create_teacher_notification(self, session: StudentSession, severity: InterventionSeverity,
                                   trigger_reason: str, message: str) -> InterventionAction:
        """Create teacher notification intervention"""
        
        action_id = f"teacher_{session.student_id}_{int(datetime.now().timestamp())}"
        
        return InterventionAction(
            action_id=action_id,
            student_id=session.student_id,
            intervention_type=InterventionType.TEACHER_INITIATED,
            severity=severity,
            title="교사 주의 필요",
            message=message,
            phase=session.current_phase,
            trigger_reason=trigger_reason,
            confidence=1.0
        )
    
    def _personalize_hint(self, hint_template: str, session: StudentSession) -> str:
        """Personalize hint message with student context"""
        # This would use actual NLP analysis in production
        # For now, simple template substitution
        
        personalized_hint = hint_template
        
        # Replace placeholders with actual data
        if "{subject}" in hint_template:
            personalized_hint = personalized_hint.replace("{subject}", "주어")  # Would be actual subject
        
        if "{predicate}" in hint_template:
            personalized_hint = personalized_hint.replace("{predicate}", "서술어")  # Would be actual predicate
        
        if "{component}" in hint_template:
            personalized_hint = personalized_hint.replace("{component}", "문장성분")
        
        return personalized_hint
    
    def _find_peer_mentor(self, struggling_student: StudentSession) -> Optional[str]:
        """Find a suitable peer mentor for struggling student"""
        # Find students in same class who are performing well
        potential_mentors = []
        
        for student_id, session in data_manager.sessions.items():
            if (session.class_id == struggling_student.class_id and
                session.student_id != struggling_student.student_id and
                session.mastery_level >= 0.8 and
                session.status != StudentStatus.STRUGGLING and
                session.current_phase >= struggling_student.current_phase):
                
                potential_mentors.append(student_id)
        
        # Return random mentor if available
        return random.choice(potential_mentors) if potential_mentors else None
    
    def _get_phase_name(self, phase: int) -> str:
        """Get phase name for hint template lookup"""
        phase_names = {
            1: "component_identification",
            2: "necessity_judgment", 
            3: "generalization",
            4: "theme_reconstruction"
        }
        return phase_names.get(phase, "general")
    
    def _execute_intervention(self, intervention: InterventionAction):
        """Execute an intervention action"""
        self.active_interventions[intervention.action_id] = intervention
        self.intervention_history.append(intervention)
        
        # Mark as delivered
        intervention.delivered_at = datetime.now()
        
        # Send intervention based on type
        if intervention.intervention_type == InterventionType.TEACHER_INITIATED:
            self._notify_teacher(intervention)
        elif intervention.intervention_type == InterventionType.PEER_ASSISTANCE:
            self._initiate_peer_session(intervention)
        else:
            self._send_student_intervention(intervention)
        
        print(f"🎯 Executed intervention: {intervention.title} for {intervention.student_id}")
    
    def _send_student_intervention(self, intervention: InterventionAction):
        """Send intervention message to student"""
        # This would integrate with the frontend WebSocket system
        # For now, log the intervention
        
        message_data = {
            "type": "intervention",
            "action_id": intervention.action_id,
            "title": intervention.title,
            "message": intervention.message,
            "severity": intervention.severity.value,
            "hint_level": intervention.hint_level.value if intervention.hint_level else None,
            "timestamp": intervention.delivered_at.isoformat()
        }
        
        # In production, this would use WebSocket
        print(f"📨 Intervention sent to student {intervention.student_id}: {intervention.message}")
    
    def _notify_teacher(self, intervention: InterventionAction):
        """Notify teacher about student needing attention"""
        # This would integrate with teacher dashboard
        print(f"🚨 Teacher notification: {intervention.message}")
    
    def _initiate_peer_session(self, intervention: InterventionAction):
        """Initiate peer learning session"""
        # Extract mentor ID from intervention trigger
        # This is simplified - would be more sophisticated in production
        
        session_id = f"peer_{intervention.student_id}_{int(datetime.now().timestamp())}"
        
        # Create collaborative session (simplified)
        collab_session = CollaborativeSession(
            session_id=session_id,
            mentor_student_id="potential_mentor",  # Would be actual mentor ID
            mentee_student_id=intervention.student_id,
            topic=f"Phase {intervention.phase} assistance",
            phase=intervention.phase
        )
        
        self.collaborative_sessions[session_id] = collab_session
        
        print(f"🤝 Initiated peer session: {session_id}")
    
    def acknowledge_intervention(self, action_id: str, student_feedback: Optional[str] = None) -> bool:
        """Student acknowledges receiving intervention"""
        if action_id in self.active_interventions:
            intervention = self.active_interventions[action_id]
            intervention.acknowledged_at = datetime.now()
            if student_feedback:
                intervention.student_feedback = student_feedback
            return True
        return False
    
    def evaluate_intervention_effectiveness(self, action_id: str, effectiveness_score: float) -> bool:
        """Evaluate how effective an intervention was"""
        if action_id in self.active_interventions:
            intervention = self.active_interventions[action_id]
            intervention.effectiveness_score = effectiveness_score
            
            # Move to completed interventions if effective
            if effectiveness_score >= 0.7:
                self.active_interventions.pop(action_id, None)
            
            return True
        return False
    
    def get_intervention_summary(self, class_id: str) -> Dict[str, Any]:
        """Get intervention summary for class"""
        class_interventions = [
            intervention for intervention in self.intervention_history
            if data_manager.sessions.get(intervention.student_id, {}).get('class_id') == class_id
        ]
        
        if not class_interventions:
            return {"total": 0, "by_type": {}, "by_severity": {}, "effectiveness": {}}
        
        # Count by type
        by_type = {}
        for intervention in class_interventions:
            intervention_type = intervention.intervention_type.value
            by_type[intervention_type] = by_type.get(intervention_type, 0) + 1
        
        # Count by severity
        by_severity = {}
        for intervention in class_interventions:
            severity = intervention.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # Calculate effectiveness
        effectiveness_scores = [
            i.effectiveness_score for i in class_interventions 
            if i.effectiveness_score is not None
        ]
        
        avg_effectiveness = sum(effectiveness_scores) / len(effectiveness_scores) if effectiveness_scores else 0
        
        return {
            "total": len(class_interventions),
            "by_type": by_type,
            "by_severity": by_severity,
            "effectiveness": {
                "average": avg_effectiveness,
                "total_evaluated": len(effectiveness_scores)
            },
            "recent_interventions": [
                {
                    "student_id": i.student_id,
                    "title": i.title,
                    "severity": i.severity.value,
                    "created_at": i.created_at.isoformat(),
                    "acknowledged": i.acknowledged_at is not None
                }
                for i in class_interventions[-10:]  # Last 10 interventions
            ]
        }
    
    def _start_monitoring_thread(self):
        """Start background monitoring thread"""
        def monitor_loop():
            while self.monitoring_active:
                try:
                    # Monitor all active students
                    for student_id in list(data_manager.sessions.keys()):
                        if data_manager.sessions[student_id].status != StudentStatus.OFFLINE:
                            self.monitor_student_progress(student_id)
                    
                    # Clean up old interventions
                    self._cleanup_old_interventions()
                    
                except Exception as e:
                    print(f"Error in monitoring thread: {e}")
                
                # Wait before next monitoring cycle
                time.sleep(30)  # Monitor every 30 seconds
        
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
        print("🔍 Started intervention monitoring thread")
    
    def _cleanup_old_interventions(self):
        """Clean up old interventions"""
        cutoff_time = datetime.now() - timedelta(hours=24)  # Keep 24 hours
        
        # Remove old active interventions
        expired_interventions = [
            action_id for action_id, intervention in self.active_interventions.items()
            if intervention.created_at < cutoff_time
        ]
        
        for action_id in expired_interventions:
            self.active_interventions.pop(action_id, None)
        
        # Limit history size
        if len(self.intervention_history) > 1000:
            self.intervention_history = self.intervention_history[-500:]  # Keep latest 500
    
    def stop_monitoring(self):
        """Stop intervention monitoring"""
        self.monitoring_active = False
        print("⏹️ Stopped intervention monitoring")

# Global intervention system instance
intervention_system = EducationalInterventionSystem()
#!/usr/bin/env python3
"""
한국어 읽기 이해 학습 시스템
생성된 JSON 과제 파일을 활용한 대화형 학습 도구
"""

import json
import os
import random
import glob
from typing import Dict, List, Optional
from datetime import datetime
import re

class StudySystem:
    """읽기 이해 학습 시스템"""
    
    def __init__(self, task_dir: str = "generator/out"):
        self.task_dir = task_dir
        self.tasks = self.load_tasks()
        self.current_task = None
        self.score_history = []
        self.session_start = datetime.now()
        
    def load_tasks(self) -> List[Dict]:
        """모든 과제 파일 로드"""
        tasks = []
        json_files = glob.glob(os.path.join(self.task_dir, "*.json"))
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    task = json.load(f)
                    task['file_path'] = file_path
                    tasks.append(task)
            except Exception as e:
                print(f"파일 로드 실패 {file_path}: {e}")
        
        return tasks
    
    def get_task_by_type(self, task_type: str) -> Optional[Dict]:
        """특정 타입의 과제 랜덤 선택"""
        filtered = [t for t in self.tasks if t.get('task_type') == task_type]
        return random.choice(filtered) if filtered else None
    
    def get_task_by_difficulty(self, difficulty: str) -> Optional[Dict]:
        """특정 난이도의 과제 랜덤 선택"""
        filtered = [t for t in self.tasks if t.get('metainfo', {}).get('difficulty') == difficulty]
        return random.choice(filtered) if filtered else None
    
    def display_task(self, task: Dict):
        """과제 내용 표시"""
        print("\n" + "=" * 80)
        
        if task['task_type'] == 'paragraph':
            print("📝 문단 읽기 과제")
            print("-" * 80)
            print(f"주제 힌트: {task['paragraph']['topic_hint']}")
            print("-" * 80)
            
            # 문단 표시 (줄바꿈 추가)
            text = task['paragraph']['text']
            words = text.split()
            line = ""
            for word in words:
                if len(line + word) > 70:
                    print(line)
                    line = word + " "
                else:
                    line += word + " "
            if line:
                print(line)
                
        else:  # article
            print("📚 글 읽기 과제")
            print("-" * 80)
            print(f"제목: {task['article']['title']}")
            print("-" * 80)
            
            for idx, para in enumerate(task['article']['paragraphs'], 1):
                print(f"\n[문단 {idx}]")
                # 문단별 줄바꿈
                words = para.split()
                line = ""
                for word in words:
                    if len(line + word) > 70:
                        print(line)
                        line = word + " "
                    else:
                        line += word + " "
                if line:
                    print(line)
        
        print("\n" + "=" * 80)
    
    def ask_keyword_question(self, task: Dict) -> bool:
        """핵심어 선택 문제"""
        q = task['q_keywords_mcq']
        print("\n[문제 1] " + q['stem'])
        print("-" * 40)
        
        for idx, choice in enumerate(q['choices'], 1):
            print(f"{idx}. {choice}")
        
        while True:
            try:
                answer = int(input("\n답을 선택하세요 (1-4): "))
                if 1 <= answer <= 4:
                    correct = (answer - 1) == q['answer_index']
                    if correct:
                        print("✅ 정답입니다!")
                    else:
                        print(f"❌ 틀렸습니다. 정답은 {q['answer_index']+1}번입니다.")
                        print(f"설명: {q['rationale']}")
                    return correct
            except ValueError:
                print("숫자를 입력해주세요.")
    
    def ask_center_sentence_question(self, task: Dict) -> bool:
        """중심문장 선택 문제"""
        if task['task_type'] == 'paragraph':
            q = task['q_center_sentence_mcq']
            print("\n[문제 2] " + q['stem'])
        else:
            q = task['q_center_paragraph_mcq']
            print("\n[문제 2] " + q['stem'])
        
        print("-" * 40)
        
        for sentence in q.get('sentences', q.get('choices', [])):
            print(f"{sentence['idx']}. {sentence['text']}")
        
        while True:
            try:
                max_choice = len(q.get('sentences', q.get('choices', [])))
                answer = int(input(f"\n답을 선택하세요 (1-{max_choice}): "))
                if 1 <= answer <= max_choice:
                    correct = answer == q['answer_idx']
                    if correct:
                        print("✅ 정답입니다!")
                    else:
                        print(f"❌ 틀렸습니다. 정답은 {q['answer_idx']}번입니다.")
                        print(f"설명: {q['rationale']}")
                    return correct
            except ValueError:
                print("숫자를 입력해주세요.")
    
    def ask_topic_question(self, task: Dict) -> float:
        """주제 서술형 문제"""
        q = task['q_topic_free']
        print("\n[문제 3] " + q['stem'])
        print("-" * 40)
        
        user_answer = input("\n답: ").strip()
        
        if not user_answer:
            print("❌ 답을 입력해주세요.")
            return 0.0
        
        # 간단한 유사도 계산 (실제로는 더 정교한 방법 필요)
        target = q['target_topic']
        score = self.calculate_similarity(user_answer, target)
        
        print(f"\n모범답안: {target}")
        
        if score >= q['evaluation']['min_similarity']:
            print(f"✅ 좋은 답변입니다! (유사도: {score:.2f})")
            return score
        else:
            print(f"⚠️ 더 구체적으로 작성해보세요. (유사도: {score:.2f})")
            for guide in q['feedback_guides']:
                print(f"  • {guide}")
            return score
    
    def calculate_similarity(self, answer: str, target: str) -> float:
        """간단한 유사도 계산"""
        # 단순 키워드 매칭 기반 (실제로는 KoNLPy나 임베딩 사용 권장)
        answer_words = set(re.findall(r'[가-힣]+', answer.lower()))
        target_words = set(re.findall(r'[가-힣]+', target.lower()))
        
        if not answer_words:
            return 0.0
        
        common = answer_words & target_words
        return len(common) / max(len(answer_words), len(target_words))
    
    def run_session(self):
        """학습 세션 실행"""
        print("\n" + "=" * 80)
        print("🎓 한국어 읽기 이해 학습 시스템")
        print("=" * 80)
        print(f"총 {len(self.tasks)}개 과제 로드 완료")
        
        while True:
            print("\n" + "-" * 80)
            print("학습 모드를 선택하세요:")
            print("1. 문단 읽기 연습")
            print("2. 글 읽기 연습")
            print("3. 난이도별 학습 (easy/medium/hard)")
            print("4. 랜덤 학습")
            print("5. 학습 통계 보기")
            print("0. 종료")
            
            choice = input("\n선택: ").strip()
            
            if choice == '0':
                self.show_statistics()
                print("\n학습을 종료합니다. 수고하셨습니다! 👋")
                break
            
            elif choice == '1':
                task = self.get_task_by_type('paragraph')
            elif choice == '2':
                task = self.get_task_by_type('article')
            elif choice == '3':
                diff = input("난이도 선택 (easy/medium/hard): ").strip()
                task = self.get_task_by_difficulty(diff)
            elif choice == '4':
                task = random.choice(self.tasks) if self.tasks else None
            elif choice == '5':
                self.show_statistics()
                continue
            else:
                print("잘못된 선택입니다.")
                continue
            
            if not task:
                print("해당하는 과제가 없습니다.")
                continue
            
            # 과제 수행
            self.current_task = task
            self.display_task(task)
            
            input("\n[Enter를 눌러 문제 풀기 시작]")
            
            score = 0
            total = 3
            
            # 문제 1: 핵심어
            if self.ask_keyword_question(task):
                score += 1
            
            # 문제 2: 중심문장/문단
            if self.ask_center_sentence_question(task):
                score += 1
            
            # 문제 3: 주제 서술
            topic_score = self.ask_topic_question(task)
            if topic_score >= 0.68:
                score += 1
            
            # 결과 저장
            result = {
                'task_id': task['id'],
                'task_type': task['task_type'],
                'difficulty': task['metainfo']['difficulty'],
                'score': score,
                'total': total,
                'timestamp': datetime.now().isoformat()
            }
            self.score_history.append(result)
            
            print("\n" + "=" * 80)
            print(f"📊 결과: {score}/{total} ({score/total*100:.0f}%)")
            print("=" * 80)
            
            if score == total:
                print("🎉 완벽합니다! 모든 문제를 맞췄습니다!")
            elif score >= 2:
                print("👍 잘했습니다! 계속 연습하세요.")
            else:
                print("💪 더 연습이 필요합니다. 다시 도전해보세요!")
    
    def show_statistics(self):
        """학습 통계 표시"""
        if not self.score_history:
            print("\n아직 학습 기록이 없습니다.")
            return
        
        print("\n" + "=" * 80)
        print("📈 학습 통계")
        print("=" * 80)
        
        total_tasks = len(self.score_history)
        avg_score = sum(h['score'] for h in self.score_history) / total_tasks
        
        print(f"총 학습 과제: {total_tasks}개")
        print(f"평균 점수: {avg_score:.1f}/3 ({avg_score/3*100:.0f}%)")
        
        # 난이도별 통계
        for diff in ['easy', 'medium', 'hard']:
            diff_tasks = [h for h in self.score_history if h['difficulty'] == diff]
            if diff_tasks:
                diff_avg = sum(h['score'] for h in diff_tasks) / len(diff_tasks)
                print(f"{diff} 난이도: {len(diff_tasks)}개, 평균 {diff_avg:.1f}/3")
        
        # 타입별 통계
        para_tasks = [h for h in self.score_history if h['task_type'] == 'paragraph']
        art_tasks = [h for h in self.score_history if h['task_type'] == 'article']
        
        if para_tasks:
            para_avg = sum(h['score'] for h in para_tasks) / len(para_tasks)
            print(f"문단 과제: {len(para_tasks)}개, 평균 {para_avg:.1f}/3")
        
        if art_tasks:
            art_avg = sum(h['score'] for h in art_tasks) / len(art_tasks)
            print(f"글 과제: {len(art_tasks)}개, 평균 {art_avg:.1f}/3")
        
        # 학습 시간
        duration = datetime.now() - self.session_start
        minutes = int(duration.total_seconds() / 60)
        print(f"\n학습 시간: {minutes}분")

def main():
    """메인 실행 함수"""
    system = StudySystem()
    
    if not system.tasks:
        print("❌ 과제 파일을 찾을 수 없습니다.")
        print("먼저 과제를 생성해주세요: python3 mass_generate.py")
        return
    
    system.run_session()

if __name__ == "__main__":
    main()
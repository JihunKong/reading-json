#!/usr/bin/env python3
"""
학습 데이터 분석 및 성능 평가 시스템
학습 결과를 분석하고 시각화하는 도구
"""

import json
import os
import glob
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple
import numpy as np

# 한글 폰트 설정
plt.rcParams['font.family'] = 'AppleGothic' if os.uname().sysname == 'Darwin' else 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False

class LearningAnalytics:
    """학습 분석 시스템"""
    
    def __init__(self, sessions_dir: str = "study_sessions", tasks_dir: str = "generator/out"):
        self.sessions_dir = sessions_dir
        self.tasks_dir = tasks_dir
        self.all_sessions = self.load_all_sessions()
        self.all_tasks = self.load_all_tasks()
        
    def load_all_sessions(self) -> List[Dict]:
        """모든 세션 데이터 로드"""
        sessions = []
        session_files = glob.glob(os.path.join(self.sessions_dir, "*.json"))
        
        for file_path in session_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    user_sessions = json.load(f)
                    user_id = os.path.basename(file_path).replace('.json', '')
                    for session in user_sessions:
                        session['user_id'] = user_id
                        sessions.append(session)
            except Exception as e:
                print(f"세션 로드 실패 {file_path}: {e}")
        
        return sessions
    
    def load_all_tasks(self) -> List[Dict]:
        """모든 과제 데이터 로드"""
        tasks = []
        task_files = glob.glob(os.path.join(self.tasks_dir, "*.json"))
        
        for file_path in task_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    task = json.load(f)
                    tasks.append(task)
            except Exception as e:
                print(f"과제 로드 실패 {file_path}: {e}")
        
        return tasks
    
    def generate_report(self) -> Dict:
        """종합 분석 보고서 생성"""
        if not self.all_sessions:
            return {
                "status": "no_data",
                "message": "분석할 학습 데이터가 없습니다."
            }
        
        # 데이터프레임 생성
        df = pd.DataFrame(self.all_sessions)
        
        # 타임스탬프 변환
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        report = {
            "overall_stats": self._calculate_overall_stats(df),
            "difficulty_analysis": self._analyze_by_difficulty(df),
            "task_type_analysis": self._analyze_by_task_type(df),
            "temporal_analysis": self._analyze_temporal_patterns(df),
            "user_performance": self._analyze_user_performance(df),
            "task_effectiveness": self._analyze_task_effectiveness(df),
            "recommendations": self._generate_recommendations(df)
        }
        
        return report
    
    def _calculate_overall_stats(self, df: pd.DataFrame) -> Dict:
        """전체 통계 계산"""
        return {
            "total_sessions": len(df),
            "unique_users": df['user_id'].nunique(),
            "unique_tasks": df['task_id'].nunique(),
            "avg_score": df['score'].mean(),
            "avg_percentage": (df['score'] / df['total']).mean() * 100,
            "perfect_scores": len(df[df['score'] == df['total']]),
            "completion_rate": (df['score'] >= 2).mean() * 100
        }
    
    def _analyze_by_difficulty(self, df: pd.DataFrame) -> Dict:
        """난이도별 분석"""
        analysis = {}
        
        for difficulty in ['easy', 'medium', 'hard']:
            diff_df = df[df['difficulty'] == difficulty]
            if not diff_df.empty:
                analysis[difficulty] = {
                    "count": len(diff_df),
                    "avg_score": diff_df['score'].mean(),
                    "avg_percentage": (diff_df['score'] / diff_df['total']).mean() * 100,
                    "std_dev": diff_df['score'].std(),
                    "perfect_rate": (diff_df['score'] == diff_df['total']).mean() * 100
                }
        
        return analysis
    
    def _analyze_by_task_type(self, df: pd.DataFrame) -> Dict:
        """과제 유형별 분석"""
        analysis = {}
        
        for task_type in ['paragraph', 'article']:
            type_df = df[df['task_type'] == task_type]
            if not type_df.empty:
                analysis[task_type] = {
                    "count": len(type_df),
                    "avg_score": type_df['score'].mean(),
                    "avg_percentage": (type_df['score'] / type_df['total']).mean() * 100,
                    "q1_accuracy": self._calculate_question_accuracy(type_df, 1),
                    "q2_accuracy": self._calculate_question_accuracy(type_df, 2),
                    "q3_accuracy": self._calculate_question_accuracy(type_df, 3)
                }
        
        return analysis
    
    def _calculate_question_accuracy(self, df: pd.DataFrame, question_num: int) -> float:
        """특정 문제 정답률 계산 (추정)"""
        # 실제로는 각 문제별 점수를 저장해야 하지만, 
        # 현재는 전체 점수로 추정
        if question_num == 1:  # 핵심어 문제
            return (df['score'] >= 1).mean() * 100
        elif question_num == 2:  # 중심문장 문제
            return (df['score'] >= 2).mean() * 100
        else:  # 주제 서술 문제
            return (df['score'] == 3).mean() * 100
    
    def _analyze_temporal_patterns(self, df: pd.DataFrame) -> Dict:
        """시간대별 패턴 분석"""
        df['hour'] = df['timestamp'].dt.hour
        df['weekday'] = df['timestamp'].dt.dayofweek
        df['date'] = df['timestamp'].dt.date
        
        return {
            "peak_hours": df.groupby('hour')['score'].mean().idxmax(),
            "peak_day": ['월', '화', '수', '목', '금', '토', '일'][df.groupby('weekday')['score'].mean().idxmax()],
            "daily_average": df.groupby('date').size().mean(),
            "trend": self._calculate_trend(df)
        }
    
    def _calculate_trend(self, df: pd.DataFrame) -> str:
        """학습 추세 계산"""
        if len(df) < 10:
            return "데이터 부족"
        
        # 최근 절반과 이전 절반 비교
        mid_point = len(df) // 2
        recent_avg = df.iloc[mid_point:]['score'].mean()
        past_avg = df.iloc[:mid_point]['score'].mean()
        
        if recent_avg > past_avg * 1.1:
            return "상승 추세 📈"
        elif recent_avg < past_avg * 0.9:
            return "하락 추세 📉"
        else:
            return "안정적 →"
    
    def _analyze_user_performance(self, df: pd.DataFrame) -> List[Dict]:
        """사용자별 성과 분석"""
        user_stats = []
        
        for user_id in df['user_id'].unique():
            user_df = df[df['user_id'] == user_id]
            user_stats.append({
                "user_id": user_id,
                "total_tasks": len(user_df),
                "avg_score": user_df['score'].mean(),
                "improvement": self._calculate_improvement(user_df),
                "favorite_type": user_df['task_type'].mode()[0] if not user_df['task_type'].mode().empty else None,
                "strongest_difficulty": self._find_strongest_difficulty(user_df)
            })
        
        return sorted(user_stats, key=lambda x: x['avg_score'], reverse=True)[:10]
    
    def _calculate_improvement(self, user_df: pd.DataFrame) -> float:
        """개인 향상도 계산"""
        if len(user_df) < 5:
            return 0.0
        
        early_scores = user_df.iloc[:3]['score'].mean()
        recent_scores = user_df.iloc[-3:]['score'].mean()
        
        if early_scores > 0:
            return ((recent_scores - early_scores) / early_scores) * 100
        return 0.0
    
    def _find_strongest_difficulty(self, user_df: pd.DataFrame) -> str:
        """가장 잘하는 난이도 찾기"""
        diff_scores = user_df.groupby('difficulty')['score'].mean()
        if not diff_scores.empty:
            return diff_scores.idxmax()
        return "unknown"
    
    def _analyze_task_effectiveness(self, df: pd.DataFrame) -> List[Dict]:
        """과제별 효과성 분석"""
        task_stats = []
        
        for task_id in df['task_id'].unique()[:20]:  # 상위 20개만
            task_df = df[df['task_id'] == task_id]
            
            # 해당 과제 정보 찾기
            task_info = next((t for t in self.all_tasks if t['id'] == task_id), None)
            
            if task_info:
                topic = (task_info.get('paragraph', {}).get('topic_hint') or 
                        task_info.get('article', {}).get('title', 'Unknown'))
            else:
                topic = "Unknown"
            
            task_stats.append({
                "task_id": task_id,
                "topic": topic,
                "attempt_count": len(task_df),
                "avg_score": task_df['score'].mean(),
                "difficulty": task_df['difficulty'].iloc[0] if not task_df.empty else "unknown",
                "task_type": task_df['task_type'].iloc[0] if not task_df.empty else "unknown"
            })
        
        return sorted(task_stats, key=lambda x: x['attempt_count'], reverse=True)
    
    def _generate_recommendations(self, df: pd.DataFrame) -> List[str]:
        """학습 권장사항 생성"""
        recommendations = []
        
        # 전체 성과 기반
        avg_percentage = (df['score'] / df['total']).mean() * 100
        if avg_percentage < 60:
            recommendations.append("📚 기초 개념 복습이 필요합니다. Easy 난이도부터 차근차근 학습하세요.")
        elif avg_percentage < 80:
            recommendations.append("👍 좋은 성과를 보이고 있습니다. Medium 난이도를 집중적으로 연습하세요.")
        else:
            recommendations.append("🎯 우수한 성과입니다! Hard 난이도에 도전해보세요.")
        
        # 난이도별 분석
        for difficulty in ['easy', 'medium', 'hard']:
            diff_df = df[df['difficulty'] == difficulty]
            if not diff_df.empty and (diff_df['score'] / diff_df['total']).mean() < 0.6:
                recommendations.append(f"⚠️ {difficulty.upper()} 난이도 과제를 더 연습하세요.")
        
        # 과제 유형별 분석
        para_df = df[df['task_type'] == 'paragraph']
        art_df = df[df['task_type'] == 'article']
        
        if not para_df.empty and not art_df.empty:
            para_avg = (para_df['score'] / para_df['total']).mean()
            art_avg = (art_df['score'] / art_df['total']).mean()
            
            if para_avg > art_avg * 1.2:
                recommendations.append("📖 글(article) 과제를 더 연습하면 좋겠습니다.")
            elif art_avg > para_avg * 1.2:
                recommendations.append("📝 문단(paragraph) 과제를 더 연습하면 좋겠습니다.")
        
        # 시간 패턴
        if len(df) > 10:
            recent_df = df.tail(10)
            if (recent_df['score'] / recent_df['total']).mean() < 0.5:
                recommendations.append("💪 최근 성과가 저조합니다. 잠시 휴식 후 다시 도전해보세요.")
        
        return recommendations
    
    def visualize_performance(self, save_path: str = "analytics_report.png"):
        """성과 시각화"""
        if not self.all_sessions:
            print("시각화할 데이터가 없습니다.")
            return
        
        df = pd.DataFrame(self.all_sessions)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['percentage'] = (df['score'] / df['total']) * 100
        
        # 그래프 설정
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle('학습 성과 분석 리포트', fontsize=16, fontweight='bold')
        
        # 1. 난이도별 평균 점수
        diff_scores = df.groupby('difficulty')['percentage'].mean()
        axes[0, 0].bar(diff_scores.index, diff_scores.values, color=['green', 'orange', 'red'])
        axes[0, 0].set_title('난이도별 평균 정답률')
        axes[0, 0].set_ylabel('정답률 (%)')
        axes[0, 0].set_ylim(0, 100)
        
        # 2. 과제 유형별 분포
        type_counts = df['task_type'].value_counts()
        axes[0, 1].pie(type_counts.values, labels=type_counts.index, autopct='%1.1f%%')
        axes[0, 1].set_title('과제 유형별 학습 비율')
        
        # 3. 시간별 학습 추이
        df['date'] = df['timestamp'].dt.date
        daily_avg = df.groupby('date')['percentage'].mean()
        axes[0, 2].plot(daily_avg.index, daily_avg.values, marker='o')
        axes[0, 2].set_title('일별 평균 정답률 추이')
        axes[0, 2].set_ylabel('정답률 (%)')
        axes[0, 2].tick_params(axis='x', rotation=45)
        
        # 4. 점수 분포 히스토그램
        axes[1, 0].hist(df['score'], bins=[0, 1, 2, 3, 4], edgecolor='black')
        axes[1, 0].set_title('점수 분포')
        axes[1, 0].set_xlabel('점수')
        axes[1, 0].set_ylabel('빈도')
        axes[1, 0].set_xticks([0, 1, 2, 3])
        
        # 5. 난이도별 박스플롯
        df_boxplot = df[['difficulty', 'percentage']]
        df_boxplot.boxplot(by='difficulty', ax=axes[1, 1])
        axes[1, 1].set_title('난이도별 점수 분포')
        axes[1, 1].set_ylabel('정답률 (%)')
        axes[1, 1].set_xlabel('난이도')
        
        # 6. 학습량 히트맵 (요일별)
        df['weekday'] = df['timestamp'].dt.dayofweek
        df['hour'] = df['timestamp'].dt.hour
        heatmap_data = df.pivot_table(values='score', index='hour', columns='weekday', aggfunc='count', fill_value=0)
        
        if not heatmap_data.empty:
            sns.heatmap(heatmap_data, cmap='YlOrRd', ax=axes[1, 2], cbar_kws={'label': '학습 횟수'})
            axes[1, 2].set_title('요일/시간별 학습 빈도')
            axes[1, 2].set_xlabel('요일 (0=월, 6=일)')
            axes[1, 2].set_ylabel('시간')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"📊 분석 리포트가 {save_path}에 저장되었습니다.")
    
    def export_to_csv(self, output_path: str = "learning_data.csv"):
        """학습 데이터를 CSV로 내보내기"""
        if not self.all_sessions:
            print("내보낼 데이터가 없습니다.")
            return
        
        df = pd.DataFrame(self.all_sessions)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"📁 데이터가 {output_path}에 저장되었습니다.")
    
    def print_summary_report(self):
        """요약 보고서 출력"""
        report = self.generate_report()
        
        if report.get("status") == "no_data":
            print(report["message"])
            return
        
        print("\n" + "=" * 80)
        print("📊 학습 분석 요약 보고서")
        print("=" * 80)
        
        # 전체 통계
        overall = report['overall_stats']
        print(f"\n📈 전체 통계")
        print(f"  • 총 학습 세션: {overall['total_sessions']}회")
        print(f"  • 참여 사용자: {overall['unique_users']}명")
        print(f"  • 사용된 과제: {overall['unique_tasks']}개")
        print(f"  • 평균 점수: {overall['avg_score']:.1f}/3 ({overall['avg_percentage']:.1f}%)")
        print(f"  • 만점 달성: {overall['perfect_scores']}회")
        print(f"  • 완료율: {overall['completion_rate']:.1f}%")
        
        # 난이도별 분석
        print(f"\n📚 난이도별 성과")
        for diff, stats in report['difficulty_analysis'].items():
            print(f"  • {diff.upper()}: {stats['count']}회, 평균 {stats['avg_percentage']:.1f}%, 만점률 {stats['perfect_rate']:.1f}%")
        
        # 과제 유형별 분석
        print(f"\n📖 과제 유형별 성과")
        for task_type, stats in report['task_type_analysis'].items():
            type_name = "문단" if task_type == "paragraph" else "글"
            print(f"  • {type_name}: {stats['count']}회, 평균 {stats['avg_percentage']:.1f}%")
            print(f"    - 문제1 정답률: {stats['q1_accuracy']:.1f}%")
            print(f"    - 문제2 정답률: {stats['q2_accuracy']:.1f}%")
            print(f"    - 문제3 정답률: {stats['q3_accuracy']:.1f}%")
        
        # 시간 패턴
        temporal = report['temporal_analysis']
        print(f"\n⏰ 학습 패턴")
        print(f"  • 최고 성과 시간: {temporal['peak_hours']}시")
        print(f"  • 최고 성과 요일: {temporal['peak_day']}요일")
        print(f"  • 일일 평균 학습: {temporal['daily_average']:.1f}회")
        print(f"  • 성과 추세: {temporal['trend']}")
        
        # 상위 사용자
        print(f"\n🏆 상위 학습자 (상위 3명)")
        for i, user in enumerate(report['user_performance'][:3], 1):
            print(f"  {i}. User {user['user_id'][:8]}: {user['total_tasks']}회, 평균 {user['avg_score']:.1f}점")
            if user['improvement'] > 0:
                print(f"     향상도: +{user['improvement']:.1f}%")
        
        # 인기 과제
        print(f"\n📝 가장 많이 푼 과제 (상위 3개)")
        for i, task in enumerate(report['task_effectiveness'][:3], 1):
            print(f"  {i}. {task['topic'][:30]}")
            print(f"     - {task['attempt_count']}회 시도, 평균 {task['avg_score']:.1f}점")
        
        # 권장사항
        print(f"\n💡 학습 권장사항")
        for rec in report['recommendations']:
            print(f"  {rec}")
        
        print("\n" + "=" * 80)

def main():
    """메인 실행 함수"""
    analytics = LearningAnalytics()
    
    while True:
        print("\n" + "=" * 60)
        print("📊 학습 분석 시스템")
        print("=" * 60)
        print("1. 요약 보고서 보기")
        print("2. 성과 그래프 생성")
        print("3. 데이터 CSV 내보내기")
        print("4. 상세 JSON 보고서 생성")
        print("0. 종료")
        
        choice = input("\n선택: ").strip()
        
        if choice == '0':
            print("분석을 종료합니다.")
            break
        elif choice == '1':
            analytics.print_summary_report()
        elif choice == '2':
            analytics.visualize_performance()
        elif choice == '3':
            analytics.export_to_csv()
        elif choice == '4':
            report = analytics.generate_report()
            with open('detailed_report.json', 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            print("📁 상세 보고서가 detailed_report.json에 저장되었습니다.")
        else:
            print("잘못된 선택입니다.")

if __name__ == "__main__":
    main()
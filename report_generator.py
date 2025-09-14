#!/usr/bin/env python3
"""
Report Generator Module
Generate comprehensive PDF/HTML reports with visualizations
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
import plotly.graph_objects as go
import plotly.express as px
from jinja2 import Template
import base64
from io import BytesIO


class ReportGenerator:
    """Generate visual reports for learning analytics"""
    
    def __init__(self, output_dir: str = "./reports"):
        self.output_dir = output_dir
        self.ensure_directories()
        self.setup_styles()
        
    def ensure_directories(self):
        """Create necessary directories"""
        dirs = [
            self.output_dir,
            os.path.join(self.output_dir, "pdf"),
            os.path.join(self.output_dir, "html"),
            os.path.join(self.output_dir, "charts"),
            os.path.join(self.output_dir, "data")
        ]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    def setup_styles(self):
        """Setup visualization styles"""
        sns.set_style("whitegrid")
        plt.rcParams['font.sans-serif'] = ['AppleGothic', 'Malgun Gothic', 'NanumGothic']
        plt.rcParams['axes.unicode_minus'] = False
        self.color_palette = {
            'primary': '#2E86AB',
            'secondary': '#A23B72',
            'success': '#73AB84',
            'warning': '#F18F01',
            'danger': '#C73E1D',
            'info': '#6C91BF'
        }
    
    def generate_student_report(self, 
                               student_data: Dict,
                               format: str = 'html') -> str:
        """
        Generate individual student report
        
        Args:
            student_data: Dictionary containing student metrics and progress
            format: Output format ('html' or 'pdf')
            
        Returns:
            Path to generated report
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        student_id = student_data.get('student_id', 'unknown')
        
        if format == 'html':
            return self._generate_html_student_report(student_data, timestamp)
        elif format == 'pdf':
            return self._generate_pdf_student_report(student_data, timestamp)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_html_student_report(self, data: Dict, timestamp: str) -> str:
        """Generate HTML report for student"""
        student_id = data.get('student_id', 'unknown')
        
        # Create visualizations
        charts = self._create_student_charts(data)
        
        # HTML template
        html_template = """
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>학습 분석 보고서 - {{ student_name }}</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                body {
                    font-family: 'Noto Sans KR', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.1);
                    overflow: hidden;
                }
                .header {
                    background: linear-gradient(135deg, #2E86AB 0%, #6C91BF 100%);
                    color: white;
                    padding: 40px;
                    text-align: center;
                }
                .header h1 {
                    font-size: 2.5em;
                    margin-bottom: 10px;
                }
                .header p {
                    font-size: 1.1em;
                    opacity: 0.9;
                }
                .content {
                    padding: 40px;
                }
                .section {
                    margin-bottom: 40px;
                }
                .section-title {
                    font-size: 1.8em;
                    color: #2E86AB;
                    margin-bottom: 20px;
                    padding-bottom: 10px;
                    border-bottom: 2px solid #e0e0e0;
                }
                .metrics-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }
                .metric-card {
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                    transition: transform 0.3s;
                }
                .metric-card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 5px 20px rgba(0,0,0,0.1);
                }
                .metric-value {
                    font-size: 2em;
                    font-weight: bold;
                    color: #2E86AB;
                }
                .metric-label {
                    color: #666;
                    margin-top: 5px;
                }
                .chart-container {
                    margin: 30px 0;
                    padding: 20px;
                    background: #f8f9fa;
                    border-radius: 10px;
                }
                .skills-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }
                .skills-table th,
                .skills-table td {
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #e0e0e0;
                }
                .skills-table th {
                    background: #f0f0f0;
                    font-weight: bold;
                }
                .skill-bar {
                    background: #e0e0e0;
                    height: 20px;
                    border-radius: 10px;
                    overflow: hidden;
                    position: relative;
                }
                .skill-progress {
                    height: 100%;
                    background: linear-gradient(90deg, #73AB84, #2E86AB);
                    border-radius: 10px;
                    transition: width 1s ease;
                }
                .recommendations {
                    background: #fff3cd;
                    border-left: 4px solid #F18F01;
                    padding: 20px;
                    border-radius: 5px;
                    margin-top: 20px;
                }
                .recommendations h3 {
                    color: #F18F01;
                    margin-bottom: 10px;
                }
                .recommendations ul {
                    list-style-position: inside;
                    color: #666;
                }
                .footer {
                    background: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    color: #666;
                    font-size: 0.9em;
                }
                .badge {
                    display: inline-block;
                    padding: 5px 10px;
                    border-radius: 15px;
                    font-size: 0.9em;
                    margin: 5px;
                }
                .badge-success {
                    background: #d4edda;
                    color: #155724;
                }
                .badge-warning {
                    background: #fff3cd;
                    color: #856404;
                }
                .badge-danger {
                    background: #f8d7da;
                    color: #721c24;
                }
                @media (max-width: 768px) {
                    .metrics-grid {
                        grid-template-columns: 1fr;
                    }
                    .header h1 {
                        font-size: 1.8em;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>학습 분석 보고서</h1>
                    <p>{{ student_name }} | {{ report_date }}</p>
                </div>
                
                <div class="content">
                    <!-- Performance Overview -->
                    <div class="section">
                        <h2 class="section-title">📊 전체 성과 요약</h2>
                        <div class="metrics-grid">
                            <div class="metric-card">
                                <div class="metric-value">{{ overall_accuracy }}%</div>
                                <div class="metric-label">전체 정답률</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">{{ total_sessions }}</div>
                                <div class="metric-label">학습 세션</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">{{ total_time }}시간</div>
                                <div class="metric-label">총 학습 시간</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">{{ current_streak }}일</div>
                                <div class="metric-label">연속 학습</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Skill Analysis -->
                    <div class="section">
                        <h2 class="section-title">🎯 영역별 실력 분석</h2>
                        <table class="skills-table">
                            <thead>
                                <tr>
                                    <th>영역</th>
                                    <th>현재 수준</th>
                                    <th>진행 상황</th>
                                    <th>상태</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for skill in skills %}
                                <tr>
                                    <td>{{ skill.name }}</td>
                                    <td>{{ skill.level }}%</td>
                                    <td>
                                        <div class="skill-bar">
                                            <div class="skill-progress" style="width: {{ skill.level }}%"></div>
                                        </div>
                                    </td>
                                    <td>
                                        {% if skill.trend == 'improving' %}
                                        <span class="badge badge-success">↑ 향상중</span>
                                        {% elif skill.trend == 'declining' %}
                                        <span class="badge badge-danger">↓ 하락중</span>
                                        {% else %}
                                        <span class="badge badge-warning">→ 유지중</span>
                                        {% endif %}
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                    
                    <!-- Progress Charts -->
                    <div class="section">
                        <h2 class="section-title">📈 학습 진도 차트</h2>
                        <div class="chart-container">
                            <div id="progress-chart"></div>
                        </div>
                        <div class="chart-container">
                            <div id="skill-radar"></div>
                        </div>
                    </div>
                    
                    <!-- Learning Patterns -->
                    <div class="section">
                        <h2 class="section-title">🔍 학습 패턴 분석</h2>
                        <div class="chart-container">
                            <div id="time-pattern-chart"></div>
                        </div>
                        <div class="chart-container">
                            <div id="accuracy-trend-chart"></div>
                        </div>
                    </div>
                    
                    <!-- Recommendations -->
                    <div class="section">
                        <h2 class="section-title">💡 맞춤형 학습 권장사항</h2>
                        <div class="recommendations">
                            <h3>개선이 필요한 영역</h3>
                            <ul>
                                {% for rec in weaknesses %}
                                <li>{{ rec }}</li>
                                {% endfor %}
                            </ul>
                        </div>
                        <div class="recommendations" style="background: #d4edda; border-color: #73AB84;">
                            <h3 style="color: #155724;">강점 영역</h3>
                            <ul>
                                {% for strength in strengths %}
                                <li>{{ strength }}</li>
                                {% endfor %}
                            </ul>
                        </div>
                    </div>
                    
                    <!-- Achievements -->
                    <div class="section">
                        <h2 class="section-title">🏆 획득한 성취</h2>
                        <div class="metrics-grid">
                            {% for achievement in achievements %}
                            <div class="metric-card">
                                <div style="font-size: 3em;">{{ achievement.icon }}</div>
                                <div class="metric-label">{{ achievement.name }}</div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
                
                <div class="footer">
                    <p>생성일: {{ report_date }} | Korean Reading Comprehension Learning Analytics System</p>
                </div>
            </div>
            
            <script>
                {{ chart_scripts }}
            </script>
        </body>
        </html>
        """
        
        # Prepare template data
        template_data = self._prepare_template_data(data)
        template_data['chart_scripts'] = charts['scripts']
        
        # Render template
        template = Template(html_template)
        html_content = template.render(**template_data)
        
        # Save report
        filepath = os.path.join(self.output_dir, 'html', f'student_{student_id}_{timestamp}.html')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filepath
    
    def _prepare_template_data(self, data: Dict) -> Dict:
        """Prepare data for template rendering"""
        metrics = data.get('metrics', {})
        profile = data.get('profile', {})
        
        # Process skills data
        skills = []
        skill_levels = metrics.get('skill_levels', {})
        for skill_name, level in skill_levels.items():
            skills.append({
                'name': self._translate_skill_name(skill_name),
                'level': round(level, 1),
                'trend': self._determine_trend(data, skill_name)
            })
        
        # Process achievements
        achievements = []
        for achievement in metrics.get('achievements', []):
            achievements.append({
                'icon': self._get_achievement_icon(achievement),
                'name': achievement
            })
        
        # Add default achievements if none
        if not achievements:
            achievements = [
                {'icon': '🌟', 'name': '첫 걸음'},
                {'icon': '📚', 'name': '꾸준한 학습자'}
            ]
        
        return {
            'student_name': profile.get('name', '학생'),
            'student_id': profile.get('student_id', 'unknown'),
            'report_date': datetime.now().strftime('%Y년 %m월 %d일'),
            'overall_accuracy': round(metrics.get('accuracy', 0) * 100, 1),
            'total_sessions': metrics.get('total_sessions', 0),
            'total_time': round(metrics.get('total_time_spent', 0) / 60, 1),
            'current_streak': metrics.get('current_streak', 0),
            'skills': skills,
            'weaknesses': metrics.get('weaknesses', ['추가 데이터 필요']),
            'strengths': metrics.get('strengths', ['계속 노력하세요!']),
            'achievements': achievements
        }
    
    def _translate_skill_name(self, skill_name: str) -> str:
        """Translate skill names to Korean"""
        translations = {
            'keyword_identification': '키워드 식별',
            'center_sentence': '중심 문장 파악',
            'center_paragraph': '중심 단락 파악',
            'topic_comprehension': '주제 이해',
            'vocabulary': '어휘력',
            'inference': '추론 능력',
            'summary': '요약 능력'
        }
        return translations.get(skill_name, skill_name)
    
    def _determine_trend(self, data: Dict, skill_name: str) -> str:
        """Determine skill trend"""
        # This would be enhanced with actual trend analysis
        return 'stable'
    
    def _get_achievement_icon(self, achievement: str) -> str:
        """Get icon for achievement"""
        icons = {
            '일주일 연속 학습': '🔥',
            '첫 만점': '💯',
            '10문제 연속 정답': '🎯',
            '학습 마스터': '👑',
            '빠른 학습자': '⚡',
            '꾸준한 학습자': '📚'
        }
        return icons.get(achievement, '🌟')
    
    def _create_student_charts(self, data: Dict) -> Dict:
        """Create interactive charts for student report"""
        charts = {'scripts': ''}
        
        # Progress over time chart
        progress_chart = self._create_progress_chart(data)
        charts['scripts'] += progress_chart
        
        # Skill radar chart
        radar_chart = self._create_skill_radar_chart(data)
        charts['scripts'] += radar_chart
        
        # Time pattern chart
        time_chart = self._create_time_pattern_chart(data)
        charts['scripts'] += time_chart
        
        # Accuracy trend chart
        accuracy_chart = self._create_accuracy_trend_chart(data)
        charts['scripts'] += accuracy_chart
        
        return charts
    
    def _create_progress_chart(self, data: Dict) -> str:
        """Create progress over time chart"""
        # Sample data - would be replaced with actual data
        dates = pd.date_range(end=datetime.now(), periods=30).tolist()
        progress = np.random.walk2d((30, 1)).cumsum(axis=0) + 50
        progress = np.clip(progress, 0, 100)
        
        script = f"""
        var progressData = {{
            x: {[d.strftime('%Y-%m-%d') for d in dates]},
            y: {progress.flatten().tolist()},
            type: 'scatter',
            mode: 'lines+markers',
            name: '학습 진도',
            line: {{color: '#2E86AB', width: 3}},
            marker: {{size: 8}}
        }};
        
        var progressLayout = {{
            title: '시간별 학습 진도',
            xaxis: {{title: '날짜'}},
            yaxis: {{title: '진도 (%)', range: [0, 100]}},
            height: 400
        }};
        
        Plotly.newPlot('progress-chart', [progressData], progressLayout);
        """
        return script
    
    def _create_skill_radar_chart(self, data: Dict) -> str:
        """Create skill radar chart"""
        metrics = data.get('metrics', {})
        skills = metrics.get('skill_levels', {})
        
        skill_names = list(skills.keys())
        skill_values = list(skills.values())
        
        script = f"""
        var radarData = {{
            type: 'scatterpolar',
            r: {skill_values},
            theta: {[self._translate_skill_name(s) for s in skill_names]},
            fill: 'toself',
            name: '현재 실력',
            line: {{color: '#2E86AB'}},
            fillcolor: 'rgba(46, 134, 171, 0.3)'
        }};
        
        var radarLayout = {{
            title: '영역별 실력 분포',
            polar: {{
                radialaxis: {{
                    visible: true,
                    range: [0, 100]
                }}
            }},
            height: 400
        }};
        
        Plotly.newPlot('skill-radar', [radarData], radarLayout);
        """
        return script
    
    def _create_time_pattern_chart(self, data: Dict) -> str:
        """Create time pattern heatmap"""
        # Sample data - would be replaced with actual data
        hours = list(range(24))
        days = ['월', '화', '수', '목', '금', '토', '일']
        activity = np.random.rand(7, 24) * 10
        
        script = f"""
        var heatmapData = {{
            z: {activity.tolist()},
            x: {hours},
            y: {days},
            type: 'heatmap',
            colorscale: 'Blues',
            showscale: true
        }};
        
        var heatmapLayout = {{
            title: '요일/시간별 학습 패턴',
            xaxis: {{title: '시간', dtick: 1}},
            yaxis: {{title: '요일'}},
            height: 300
        }};
        
        Plotly.newPlot('time-pattern-chart', [heatmapData], heatmapLayout);
        """
        return script
    
    def _create_accuracy_trend_chart(self, data: Dict) -> str:
        """Create accuracy trend chart"""
        # Sample data - would be replaced with actual data
        sessions = list(range(1, 21))
        accuracy = np.random.beta(8, 3, 20) * 100
        
        script = f"""
        var accuracyData = {{
            x: {sessions},
            y: {accuracy.tolist()},
            type: 'scatter',
            mode: 'lines+markers',
            name: '정답률',
            line: {{color: '#73AB84', width: 3}},
            marker: {{size: 8}}
        }};
        
        var trendline = {{
            x: {sessions},
            y: {np.polyval(np.polyfit(sessions, accuracy, 1), sessions).tolist()},
            type: 'scatter',
            mode: 'lines',
            name: '추세선',
            line: {{color: '#F18F01', width: 2, dash: 'dash'}}
        }};
        
        var accuracyLayout = {{
            title: '정답률 추이',
            xaxis: {{title: '세션'}},
            yaxis: {{title: '정답률 (%)', range: [0, 100]}},
            height: 400
        }};
        
        Plotly.newPlot('accuracy-trend-chart', [accuracyData, trendline], accuracyLayout);
        """
        return script
    
    def _generate_pdf_student_report(self, data: Dict, timestamp: str) -> str:
        """Generate PDF report for student"""
        student_id = data.get('student_id', 'unknown')
        filepath = os.path.join(self.output_dir, 'pdf', f'student_{student_id}_{timestamp}.pdf')
        
        with PdfPages(filepath) as pdf:
            # Page 1: Overview
            fig = plt.figure(figsize=(11, 8.5))
            self._create_overview_page(fig, data)
            pdf.savefig(fig)
            plt.close()
            
            # Page 2: Skill Analysis
            fig = plt.figure(figsize=(11, 8.5))
            self._create_skill_analysis_page(fig, data)
            pdf.savefig(fig)
            plt.close()
            
            # Page 3: Progress Charts
            fig = plt.figure(figsize=(11, 8.5))
            self._create_progress_charts_page(fig, data)
            pdf.savefig(fig)
            plt.close()
            
            # Page 4: Recommendations
            fig = plt.figure(figsize=(11, 8.5))
            self._create_recommendations_page(fig, data)
            pdf.savefig(fig)
            plt.close()
        
        return filepath
    
    def _create_overview_page(self, fig, data):
        """Create overview page for PDF"""
        fig.suptitle('학습 분석 보고서 - 전체 요약', fontsize=16, fontweight='bold')
        
        # Add metrics
        ax = fig.add_subplot(111)
        ax.axis('off')
        
        metrics = data.get('metrics', {})
        text = f"""
        학생 ID: {data.get('student_id', 'unknown')}
        보고서 생성일: {datetime.now().strftime('%Y년 %m월 %d일')}
        
        전체 정답률: {metrics.get('accuracy', 0) * 100:.1f}%
        총 학습 세션: {metrics.get('total_sessions', 0)}회
        총 학습 시간: {metrics.get('total_time_spent', 0) / 60:.1f}시간
        연속 학습일: {metrics.get('current_streak', 0)}일
        """
        
        ax.text(0.1, 0.9, text, transform=ax.transAxes, fontsize=12,
                verticalalignment='top', fontfamily='monospace')
    
    def _create_skill_analysis_page(self, fig, data):
        """Create skill analysis page for PDF"""
        fig.suptitle('영역별 실력 분석', fontsize=16, fontweight='bold')
        
        metrics = data.get('metrics', {})
        skills = metrics.get('skill_levels', {})
        
        if skills:
            # Create bar chart
            ax = fig.add_subplot(211)
            skill_names = [self._translate_skill_name(s) for s in skills.keys()]
            skill_values = list(skills.values())
            
            bars = ax.bar(skill_names, skill_values, color=self.color_palette['primary'])
            ax.set_ylabel('실력 수준 (%)')
            ax.set_ylim(0, 100)
            ax.grid(True, alpha=0.3)
            
            # Add value labels on bars
            for bar, value in zip(bars, skill_values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{value:.1f}%', ha='center', va='bottom')
            
            # Create radar chart
            ax2 = fig.add_subplot(212, projection='polar')
            angles = np.linspace(0, 2 * np.pi, len(skills), endpoint=False).tolist()
            values = skill_values + [skill_values[0]]  # Complete the circle
            angles += angles[:1]
            
            ax2.plot(angles, values, 'o-', linewidth=2, color=self.color_palette['primary'])
            ax2.fill(angles, values, alpha=0.25, color=self.color_palette['primary'])
            ax2.set_xticks(angles[:-1])
            ax2.set_xticklabels(skill_names)
            ax2.set_ylim(0, 100)
            ax2.grid(True)
    
    def _create_progress_charts_page(self, fig, data):
        """Create progress charts page for PDF"""
        fig.suptitle('학습 진도 분석', fontsize=16, fontweight='bold')
        
        # Progress over time
        ax1 = fig.add_subplot(211)
        dates = pd.date_range(end=datetime.now(), periods=30)
        progress = np.random.walk2d((30, 1)).cumsum(axis=0) + 50
        progress = np.clip(progress, 0, 100)
        
        ax1.plot(dates, progress, marker='o', color=self.color_palette['success'])
        ax1.set_xlabel('날짜')
        ax1.set_ylabel('진도 (%)')
        ax1.set_title('시간별 학습 진도')
        ax1.grid(True, alpha=0.3)
        
        # Accuracy trend
        ax2 = fig.add_subplot(212)
        sessions = np.arange(1, 21)
        accuracy = np.random.beta(8, 3, 20) * 100
        
        ax2.plot(sessions, accuracy, marker='o', color=self.color_palette['info'])
        z = np.polyfit(sessions, accuracy, 1)
        p = np.poly1d(z)
        ax2.plot(sessions, p(sessions), '--', color=self.color_palette['warning'], alpha=0.8)
        
        ax2.set_xlabel('세션')
        ax2.set_ylabel('정답률 (%)')
        ax2.set_title('정답률 추이')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
    
    def _create_recommendations_page(self, fig, data):
        """Create recommendations page for PDF"""
        fig.suptitle('맞춤형 학습 권장사항', fontsize=16, fontweight='bold')
        
        ax = fig.add_subplot(111)
        ax.axis('off')
        
        metrics = data.get('metrics', {})
        
        recommendations_text = """
        【강점 영역】
        """
        for strength in metrics.get('strengths', ['계속 노력하세요!']):
            recommendations_text += f"  ✓ {strength}\n"
        
        recommendations_text += """
        
        【개선 필요 영역】
        """
        for weakness in metrics.get('weaknesses', ['추가 데이터 필요']):
            recommendations_text += f"  ⚠ {weakness}\n"
        
        recommendations_text += """
        
        【학습 전략】
        1. 약점 영역 집중 학습 (하루 30분)
        2. 강점 영역 심화 학습 (주 2회)
        3. 규칙적인 복습 스케줄 유지
        4. 다양한 난이도 문제 도전
        """
        
        ax.text(0.1, 0.9, recommendations_text, transform=ax.transAxes,
                fontsize=11, verticalalignment='top')
    
    def generate_class_report(self,
                             class_data: Dict,
                             format: str = 'html') -> str:
        """Generate class-level report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        class_id = class_data.get('class_id', 'unknown')
        
        if format == 'html':
            return self._generate_html_class_report(class_data, timestamp)
        elif format == 'pdf':
            return self._generate_pdf_class_report(class_data, timestamp)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_html_class_report(self, data: Dict, timestamp: str) -> str:
        """Generate HTML report for class"""
        class_id = data.get('class_id', 'unknown')
        
        # Simplified HTML template for class report
        html_template = """
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <title>학급 분석 보고서</title>
            <style>
                body { font-family: 'Noto Sans KR', sans-serif; padding: 20px; }
                .header { text-align: center; padding: 20px; background: #2E86AB; color: white; }
                .content { max-width: 1200px; margin: 0 auto; padding: 20px; }
                .metric { display: inline-block; padding: 20px; margin: 10px; background: #f0f0f0; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>학급 분석 보고서</h1>
                <p>{{ class_id }} | {{ report_date }}</p>
            </div>
            <div class="content">
                <h2>학급 통계</h2>
                <div class="metric">
                    <h3>{{ total_students }}</h3>
                    <p>전체 학생</p>
                </div>
                <div class="metric">
                    <h3>{{ avg_accuracy }}%</h3>
                    <p>평균 정답률</p>
                </div>
                <div class="metric">
                    <h3>{{ active_students }}</h3>
                    <p>활동 학생</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        template = Template(html_template)
        html_content = template.render(
            class_id=class_id,
            report_date=datetime.now().strftime('%Y년 %m월 %d일'),
            total_students=data.get('total_students', 0),
            avg_accuracy=round(data.get('avg_accuracy', 0) * 100, 1),
            active_students=data.get('active_students', 0)
        )
        
        filepath = os.path.join(self.output_dir, 'html', f'class_{class_id}_{timestamp}.html')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filepath
    
    def _generate_pdf_class_report(self, data: Dict, timestamp: str) -> str:
        """Generate PDF report for class"""
        class_id = data.get('class_id', 'unknown')
        filepath = os.path.join(self.output_dir, 'pdf', f'class_{class_id}_{timestamp}.pdf')
        
        with PdfPages(filepath) as pdf:
            fig = plt.figure(figsize=(11, 8.5))
            fig.suptitle(f'학급 분석 보고서 - {class_id}', fontsize=16, fontweight='bold')
            
            # Add basic class metrics
            ax = fig.add_subplot(111)
            ax.axis('off')
            
            text = f"""
            학급 ID: {class_id}
            보고서 생성일: {datetime.now().strftime('%Y년 %m월 %d일')}
            
            전체 학생 수: {data.get('total_students', 0)}명
            활동 학생 수: {data.get('active_students', 0)}명
            평균 정답률: {data.get('avg_accuracy', 0) * 100:.1f}%
            표준 편차: {data.get('std_deviation', 0):.2f}
            """
            
            ax.text(0.1, 0.9, text, transform=ax.transAxes, fontsize=12,
                   verticalalignment='top', fontfamily='monospace')
            
            pdf.savefig(fig)
            plt.close()
        
        return filepath
    
    def generate_comparative_report(self,
                                   student_ids: List[str],
                                   data: Dict[str, Dict],
                                   format: str = 'html') -> str:
        """Generate comparative report for multiple students"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'html':
            # Create comparison charts
            comparison_html = self._create_comparison_html(student_ids, data)
            filepath = os.path.join(self.output_dir, 'html', f'comparison_{timestamp}.html')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(comparison_html)
            return filepath
        else:
            return self._create_comparison_pdf(student_ids, data, timestamp)
    
    def _create_comparison_html(self, student_ids: List[str], data: Dict[str, Dict]) -> str:
        """Create HTML comparison report"""
        html = """
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <title>학생 비교 분석</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        </head>
        <body>
            <h1>학생 비교 분석 보고서</h1>
            <div id="comparison-chart"></div>
            <script>
                // Comparison chart would be generated here
            </script>
        </body>
        </html>
        """
        return html
    
    def _create_comparison_pdf(self, student_ids: List[str], data: Dict[str, Dict], timestamp: str) -> str:
        """Create PDF comparison report"""
        filepath = os.path.join(self.output_dir, 'pdf', f'comparison_{timestamp}.pdf')
        
        with PdfPages(filepath) as pdf:
            fig = plt.figure(figsize=(11, 8.5))
            fig.suptitle('학생 비교 분석', fontsize=16, fontweight='bold')
            
            # Create comparison visualizations
            ax = fig.add_subplot(111)
            
            # Sample comparison bar chart
            students = student_ids[:5]  # Limit to 5 students
            accuracies = [data.get(sid, {}).get('metrics', {}).get('accuracy', 0) * 100 for sid in students]
            
            ax.bar(students, accuracies, color=self.color_palette['primary'])
            ax.set_ylabel('정답률 (%)')
            ax.set_title('학생별 정답률 비교')
            ax.grid(True, alpha=0.3)
            
            pdf.savefig(fig)
            plt.close()
        
        return filepath


def main():
    """Test the report generator"""
    generator = ReportGenerator()
    
    print("Report Generator System")
    print("=" * 60)
    
    # Sample student data
    student_data = {
        'student_id': 'student_001',
        'profile': {
            'name': '김철수',
            'student_id': 'student_001'
        },
        'metrics': {
            'accuracy': 0.75,
            'total_sessions': 15,
            'total_time_spent': 450,  # minutes
            'current_streak': 5,
            'skill_levels': {
                'keyword_identification': 80,
                'center_sentence': 70,
                'center_paragraph': 65,
                'topic_comprehension': 75,
                'vocabulary': 85,
                'inference': 60,
                'summary': 70
            },
            'strengths': ['키워드 식별', '어휘력'],
            'weaknesses': ['추론 능력', '중심 단락 파악'],
            'achievements': ['일주일 연속 학습', '첫 만점']
        }
    }
    
    # Generate HTML report
    html_path = generator.generate_student_report(student_data, format='html')
    print(f"HTML report generated: {html_path}")
    
    # Generate PDF report
    pdf_path = generator.generate_student_report(student_data, format='pdf')
    print(f"PDF report generated: {pdf_path}")
    
    # Sample class data
    class_data = {
        'class_id': 'class_A',
        'total_students': 30,
        'active_students': 25,
        'avg_accuracy': 0.72,
        'std_deviation': 0.15
    }
    
    # Generate class report
    class_html = generator.generate_class_report(class_data, format='html')
    print(f"Class HTML report generated: {class_html}")
    
    class_pdf = generator.generate_class_report(class_data, format='pdf')
    print(f"Class PDF report generated: {class_pdf}")


if __name__ == "__main__":
    main()
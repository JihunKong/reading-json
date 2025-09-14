#!/usr/bin/env python3
"""
Comprehensive Data Export System
- Multi-format data export (CSV, Excel, JSON, PDF)
- Custom report generation
- Performance analytics export
- Privacy-compliant data handling
"""

import json
import csv
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict, field
from io import StringIO, BytesIO
import zipfile
import tempfile
import os
from pathlib import Path

try:
    import pandas as pd
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.chart import BarChart, LineChart, Reference
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    print("⚠️ Excel export requires: pip install pandas openpyxl")

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️ PDF export requires: pip install reportlab")

from app.teacher_data_manager import data_manager, StudentSession, StudentStatus
from app.analytics_engine import analytics_engine
from app.classroom_manager import classroom_manager
from app.intervention_system import intervention_system

from enum import Enum

class ExportFormat(Enum):
    CSV = "csv"
    JSON = "json"
    EXCEL = "xlsx"
    PDF = "pdf"

class ReportType(Enum):
    STUDENT_PROGRESS = "student_progress"
    CLASS_SUMMARY = "class_summary"
    PERFORMANCE_ANALYTICS = "performance_analytics"
    INTERVENTION_LOG = "intervention_log"
    LEARNING_PATTERNS = "learning_patterns"
    COMPLETE_EXPORT = "complete_export"

@dataclass
class ExportRequest:
    """Export request configuration"""
    report_type: ReportType
    format_type: ExportFormat
    class_id: str
    
    # Filters
    student_ids: Optional[List[str]] = None
    date_range: Optional[Tuple[datetime, datetime]] = None
    include_personal_data: bool = True
    include_performance_data: bool = True
    include_intervention_data: bool = True
    
    # Customization
    custom_fields: Optional[List[str]] = None
    group_by: Optional[str] = None
    sort_by: Optional[str] = None
    
    # Metadata
    requested_by: str = ""
    request_timestamp: datetime = field(default_factory=datetime.now)

class ComprehensiveDataExportSystem:
    """
    Advanced data export system for educational analytics
    - Multiple output formats
    - Customizable reports
    - Privacy compliance
    - Batch export capabilities
    """
    
    def __init__(self, export_dir: str = "exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(exist_ok=True)
        
        # Export templates and configurations
        self.report_configs = self._initialize_report_configs()
        
        print(f"✅ Data Export System initialized (exports: {self.export_dir})")
    
    def _initialize_report_configs(self) -> Dict[str, Dict[str, Any]]:
        """Initialize report configuration templates"""
        return {
            "student_progress": {
                "title": "학생 학습 진행 보고서",
                "description": "개별 학생의 4단계 학습 진행 상황 및 성과 분석",
                "required_data": ["sessions", "progress", "scores"],
                "privacy_level": "high"
            },
            "class_summary": {
                "title": "학급 종합 현황 보고서",
                "description": "학급 전체의 학습 현황 및 통계 요약",
                "required_data": ["class_info", "student_summary", "analytics"],
                "privacy_level": "medium"
            },
            "performance_analytics": {
                "title": "성과 분석 보고서",
                "description": "상세한 학습 성과 분석 및 패턴 인사이트",
                "required_data": ["performance_metrics", "trends", "predictions"],
                "privacy_level": "low"
            },
            "intervention_log": {
                "title": "교육 개입 기록",
                "description": "자동/수동 교육 개입 이력 및 효과 분석",
                "required_data": ["interventions", "effectiveness", "patterns"],
                "privacy_level": "medium"
            }
        }
    
    def export_data(self, request: ExportRequest) -> Dict[str, Any]:
        """Export data according to request specifications"""
        try:
            # Validate request
            if not self._validate_export_request(request):
                raise ValueError("Invalid export request")
            
            # Gather data
            export_data = self._gather_export_data(request)
            
            # Generate export file
            export_result = self._generate_export_file(export_data, request)
            
            # Log export activity
            self._log_export_activity(request, export_result)
            
            return {
                "success": True,
                "export_path": export_result["file_path"],
                "file_size": export_result["file_size"],
                "record_count": export_result["record_count"],
                "generated_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=7)).isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _validate_export_request(self, request: ExportRequest) -> bool:
        """Validate export request parameters"""
        # Check if class exists
        if request.class_id not in classroom_manager.classes:
            return False
        
        # Check format availability
        if request.format_type == ExportFormat.EXCEL and not EXCEL_AVAILABLE:
            return False
        if request.format_type == ExportFormat.PDF and not PDF_AVAILABLE:
            return False
        
        # Validate date range
        if request.date_range:
            start_date, end_date = request.date_range
            if start_date > end_date:
                return False
        
        return True
    
    def _gather_export_data(self, request: ExportRequest) -> Dict[str, Any]:
        """Gather all required data for export"""
        export_data = {
            "metadata": {
                "report_type": request.report_type.value,
                "class_id": request.class_id,
                "generated_at": datetime.now().isoformat(),
                "requested_by": request.requested_by,
                "class_name": classroom_manager.classes[request.class_id].class_name
            }
        }
        
        # Get base class and student data
        if request.report_type in [ReportType.STUDENT_PROGRESS, ReportType.CLASS_SUMMARY, ReportType.COMPLETE_EXPORT]:
            export_data.update(self._get_student_data(request))
        
        # Get analytics data
        if request.report_type in [ReportType.PERFORMANCE_ANALYTICS, ReportType.CLASS_SUMMARY, ReportType.COMPLETE_EXPORT]:
            export_data.update(self._get_analytics_data(request))
        
        # Get intervention data
        if request.report_type in [ReportType.INTERVENTION_LOG, ReportType.COMPLETE_EXPORT]:
            export_data.update(self._get_intervention_data(request))
        
        return export_data
    
    def _get_student_data(self, request: ExportRequest) -> Dict[str, Any]:
        """Gather student session and progress data"""
        # Get class roster
        class_roster = classroom_manager.get_class_roster(request.class_id)
        
        # Filter students if specified
        if request.student_ids:
            class_roster = [s for s in class_roster if s["student_id"] in request.student_ids]
        
        # Get detailed student data
        detailed_students = []
        for student_info in class_roster:
            student_id = student_info["student_id"]
            
            # Get current session
            current_session = data_manager.sessions.get(student_id)
            
            # Get learning profile
            learning_profile = analytics_engine.get_student_learning_profile(student_id)
            
            # Combine all student data
            student_data = {
                "basic_info": student_info,
                "current_session": current_session.to_dict() if current_session else None,
                "learning_profile": learning_profile,
                "assignments": classroom_manager.get_student_assignments(student_id)
            }
            
            # Apply privacy filters
            if not request.include_personal_data:
                student_data["basic_info"]["parent_contact"] = "[REDACTED]"
                student_data["basic_info"]["notes"] = "[REDACTED]"
            
            detailed_students.append(student_data)
        
        return {
            "students": detailed_students,
            "class_roster": class_roster,
            "student_count": len(detailed_students)
        }
    
    def _get_analytics_data(self, request: ExportRequest) -> Dict[str, Any]:
        """Gather analytics and performance data"""
        # Get comprehensive class analytics
        class_analytics = analytics_engine.analyze_class(request.class_id)
        
        # Get performance report
        performance_report = analytics_engine.generate_performance_report(request.class_id)
        
        # Get class overview from data manager
        class_overview = data_manager.get_class_overview(request.class_id)
        
        return {
            "analytics": {
                "class_analytics": asdict(class_analytics),
                "performance_report": performance_report,
                "class_overview": class_overview
            }
        }
    
    def _get_intervention_data(self, request: ExportRequest) -> Dict[str, Any]:
        """Gather intervention and support data"""
        # Get intervention summary
        intervention_summary = intervention_system.get_intervention_summary(request.class_id)
        
        # Get detailed intervention history
        intervention_history = []
        for intervention in intervention_system.intervention_history:
            student_session = data_manager.sessions.get(intervention.student_id)
            if student_session and student_session.class_id == request.class_id:
                intervention_data = asdict(intervention)
                intervention_data["created_at"] = intervention.created_at.isoformat()
                if intervention.delivered_at:
                    intervention_data["delivered_at"] = intervention.delivered_at.isoformat()
                if intervention.acknowledged_at:
                    intervention_data["acknowledged_at"] = intervention.acknowledged_at.isoformat()
                
                intervention_history.append(intervention_data)
        
        return {
            "interventions": {
                "summary": intervention_summary,
                "history": intervention_history
            }
        }
    
    def _generate_export_file(self, export_data: Dict[str, Any], request: ExportRequest) -> Dict[str, Any]:
        """Generate export file in requested format"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{request.report_type.value}_{request.class_id}_{timestamp}"
        
        if request.format_type == ExportFormat.CSV:
            return self._export_to_csv(export_data, request, base_filename)
        elif request.format_type == ExportFormat.JSON:
            return self._export_to_json(export_data, request, base_filename)
        elif request.format_type == ExportFormat.EXCEL:
            return self._export_to_excel(export_data, request, base_filename)
        elif request.format_type == ExportFormat.PDF:
            return self._export_to_pdf(export_data, request, base_filename)
        else:
            raise ValueError(f"Unsupported format: {request.format_type}")
    
    def _export_to_csv(self, export_data: Dict[str, Any], request: ExportRequest, base_filename: str) -> Dict[str, Any]:
        """Export data to CSV format"""
        if request.report_type == ReportType.STUDENT_PROGRESS:
            # Student progress CSV
            csv_file = self.export_dir / f"{base_filename}.csv"
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                
                # Header
                writer.writerow([
                    'Student ID', 'Student Name', 'Current Phase', 'Status',
                    'Mastery Level', 'Total Time (min)', 'Phase 1 Score', 'Phase 2 Score',
                    'Phase 3 Score', 'Phase 4 Score', 'Hints Used', 'Help Requests',
                    'Last Activity', 'Learning Style', 'Recommendations'
                ])
                
                # Data rows
                record_count = 0
                for student_data in export_data.get("students", []):
                    session = student_data.get("current_session")
                    profile = student_data.get("learning_profile", {})
                    basic_info = student_data.get("basic_info", {})
                    
                    if session:
                        phase_scores = session.get("phase_scores", {})
                        total_hints = sum(session.get("hints_used", {}).values())
                        
                        writer.writerow([
                            basic_info.get("student_id", ""),
                            basic_info.get("student_name", ""),
                            session.get("current_phase", ""),
                            session.get("status", ""),
                            f"{session.get('mastery_level', 0):.2f}",
                            f"{session.get('total_time', 0) / 60:.1f}",
                            phase_scores.get("1", ""),
                            phase_scores.get("2", ""),
                            phase_scores.get("3", ""),
                            phase_scores.get("4", ""),
                            total_hints,
                            1 if session.get("help_requested") else 0,
                            session.get("last_activity", ""),
                            profile.get("learning_behavior", {}).get("learning_style", ""),
                            "; ".join(profile.get("recommendations", {}).get("immediate_actions", []))
                        ])
                        record_count += 1
            
            return {
                "file_path": str(csv_file),
                "file_size": csv_file.stat().st_size,
                "record_count": record_count
            }
        
        elif request.report_type == ReportType.CLASS_SUMMARY:
            # Class summary CSV
            csv_file = self.export_dir / f"{base_filename}.csv"
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                
                # Class overview section
                writer.writerow(["Class Summary Report"])
                writer.writerow(["Generated:", export_data["metadata"]["generated_at"]])
                writer.writerow(["Class:", export_data["metadata"]["class_name"]])
                writer.writerow([])
                
                # Statistics section
                analytics = export_data.get("analytics", {})
                overview = analytics.get("class_overview", {})
                
                writer.writerow(["Class Statistics"])
                writer.writerow(["Total Students", overview.get("total_students", 0)])
                writer.writerow(["Active Students", overview.get("status_distribution", {}).get("active", 0)])
                writer.writerow(["Struggling Students", overview.get("status_distribution", {}).get("struggling", 0)])
                writer.writerow(["Completed Students", overview.get("status_distribution", {}).get("completed", 0)])
                
            return {
                "file_path": str(csv_file),
                "file_size": csv_file.stat().st_size,
                "record_count": 1
            }
    
    def _export_to_json(self, export_data: Dict[str, Any], request: ExportRequest, base_filename: str) -> Dict[str, Any]:
        """Export data to JSON format"""
        json_file = self.export_dir / f"{base_filename}.json"
        
        with open(json_file, 'w', encoding='utf-8') as file:
            json.dump(export_data, file, ensure_ascii=False, indent=2, default=str)
        
        # Count records
        record_count = 0
        if "students" in export_data:
            record_count = len(export_data["students"])
        elif "interventions" in export_data:
            record_count = len(export_data["interventions"].get("history", []))
        
        return {
            "file_path": str(json_file),
            "file_size": json_file.stat().st_size,
            "record_count": record_count
        }
    
    def _export_to_excel(self, export_data: Dict[str, Any], request: ExportRequest, base_filename: str) -> Dict[str, Any]:
        """Export data to Excel format with formatting and charts"""
        if not EXCEL_AVAILABLE:
            raise ValueError("Excel export not available - install pandas and openpyxl")
        
        excel_file = self.export_dir / f"{base_filename}.xlsx"
        
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            record_count = 0
            
            if request.report_type == ReportType.STUDENT_PROGRESS:
                # Student data sheet
                student_rows = []
                for student_data in export_data.get("students", []):
                    session = student_data.get("current_session")
                    profile = student_data.get("learning_profile", {})
                    basic_info = student_data.get("basic_info", {})
                    
                    if session:
                        phase_scores = session.get("phase_scores", {})
                        student_rows.append({
                            'Student ID': basic_info.get("student_id", ""),
                            'Student Name': basic_info.get("student_name", ""),
                            'Current Phase': session.get("current_phase", ""),
                            'Status': session.get("status", ""),
                            'Mastery Level': session.get('mastery_level', 0),
                            'Total Time (min)': session.get('total_time', 0) / 60,
                            'Phase 1 Score': phase_scores.get("1", ""),
                            'Phase 2 Score': phase_scores.get("2", ""),
                            'Phase 3 Score': phase_scores.get("3", ""),
                            'Phase 4 Score': phase_scores.get("4", ""),
                            'Hints Used': sum(session.get("hints_used", {}).values()),
                            'Help Requested': 1 if session.get("help_requested") else 0,
                            'Learning Style': profile.get("learning_behavior", {}).get("learning_style", "")
                        })
                
                if student_rows:
                    df = pd.DataFrame(student_rows)
                    df.to_excel(writer, sheet_name='Student Progress', index=False)
                    record_count = len(student_rows)
                    
                    # Format Excel sheet
                    worksheet = writer.sheets['Student Progress']
                    self._format_excel_worksheet(worksheet, df)
            
            elif request.report_type == ReportType.CLASS_SUMMARY:
                # Class summary data
                analytics = export_data.get("analytics", {})
                overview = analytics.get("class_overview", {})
                
                summary_data = {
                    'Metric': ['Total Students', 'Active Students', 'Struggling Students', 'Completed Students'],
                    'Count': [
                        overview.get("total_students", 0),
                        overview.get("status_distribution", {}).get("active", 0),
                        overview.get("status_distribution", {}).get("struggling", 0),
                        overview.get("status_distribution", {}).get("completed", 0)
                    ]
                }
                
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name='Class Summary', index=False)
                record_count = len(summary_data['Metric'])
        
        return {
            "file_path": str(excel_file),
            "file_size": excel_file.stat().st_size,
            "record_count": record_count
        }
    
    def _format_excel_worksheet(self, worksheet, df):
        """Apply formatting to Excel worksheet"""
        # Header formatting
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        
        for cell in worksheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")
        
        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    def _export_to_pdf(self, export_data: Dict[str, Any], request: ExportRequest, base_filename: str) -> Dict[str, Any]:
        """Export data to PDF format with professional formatting"""
        if not PDF_AVAILABLE:
            raise ValueError("PDF export not available - install reportlab")
        
        pdf_file = self.export_dir / f"{base_filename}.pdf"
        
        doc = SimpleDocTemplate(
            str(pdf_file),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build PDF content
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center
        )
        
        report_config = self.report_configs.get(request.report_type.value, {})
        title = report_config.get("title", "학습 보고서")
        story.append(Paragraph(title, title_style))
        
        # Metadata
        metadata = export_data.get("metadata", {})
        story.append(Paragraph(f"<b>학급:</b> {metadata.get('class_name', '')}", styles['Normal']))
        story.append(Paragraph(f"<b>생성일:</b> {datetime.now().strftime('%Y년 %m월 %d일')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Content based on report type
        if request.report_type == ReportType.STUDENT_PROGRESS:
            story.extend(self._build_student_progress_pdf_content(export_data, styles))
        elif request.report_type == ReportType.CLASS_SUMMARY:
            story.extend(self._build_class_summary_pdf_content(export_data, styles))
        
        doc.build(story)
        
        return {
            "file_path": str(pdf_file),
            "file_size": pdf_file.stat().st_size,
            "record_count": len(export_data.get("students", []))
        }
    
    def _build_student_progress_pdf_content(self, export_data: Dict[str, Any], styles) -> List:
        """Build PDF content for student progress report"""
        content = []
        
        # Summary section
        content.append(Paragraph("학습 진행 요약", styles['Heading2']))
        
        students = export_data.get("students", [])
        if students:
            # Create summary table
            summary_data = [['항목', '값']]
            summary_data.append(['총 학생 수', str(len(students))])
            
            active_count = sum(1 for s in students 
                             if s.get("current_session", {}).get("status") == "active")
            struggling_count = sum(1 for s in students 
                                 if s.get("current_session", {}).get("status") == "struggling")
            
            summary_data.append(['활동 중인 학생', str(active_count)])
            summary_data.append(['도움이 필요한 학생', str(struggling_count)])
            
            summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            content.append(summary_table)
            content.append(Spacer(1, 20))
        
        return content
    
    def _build_class_summary_pdf_content(self, export_data: Dict[str, Any], styles) -> List:
        """Build PDF content for class summary report"""
        content = []
        
        # Class overview
        content.append(Paragraph("학급 현황", styles['Heading2']))
        
        analytics = export_data.get("analytics", {})
        overview = analytics.get("class_overview", {})
        
        if overview:
            overview_data = [['상태', '학생 수']]
            status_dist = overview.get("status_distribution", {})
            
            for status, count in status_dist.items():
                status_korean = {
                    'active': '학습 중',
                    'struggling': '도움 필요',
                    'completed': '완료',
                    'idle': '대기',
                    'offline': '오프라인'
                }.get(status, status)
                
                overview_data.append([status_korean, str(count)])
            
            overview_table = Table(overview_data, colWidths=[3*inch, 2*inch])
            overview_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            content.append(overview_table)
        
        return content
    
    def _log_export_activity(self, request: ExportRequest, result: Dict[str, Any]):
        """Log export activity for audit purposes"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "report_type": request.report_type.value,
            "format": request.format_type.value,
            "class_id": request.class_id,
            "requested_by": request.requested_by,
            "success": result.get("success", False),
            "file_path": result.get("file_path", ""),
            "record_count": result.get("record_count", 0)
        }
        
        # Log to file (in production, use proper logging system)
        log_file = self.export_dir / "export_log.json"
        
        try:
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(log_entry)
            
            # Keep only last 1000 entries
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2, default=str)
                
        except Exception as e:
            print(f"Error logging export activity: {e}")
    
    def create_bulk_export(self, class_id: str, export_formats: List[ExportFormat]) -> Dict[str, Any]:
        """Create bulk export with multiple formats in a ZIP file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"bulk_export_{class_id}_{timestamp}.zip"
        zip_path = self.export_dir / zip_filename
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                export_results = []
                
                for format_type in export_formats:
                    # Create export request for each format
                    request = ExportRequest(
                        report_type=ReportType.COMPLETE_EXPORT,
                        format_type=format_type,
                        class_id=class_id,
                        requested_by="bulk_export"
                    )
                    
                    # Generate export
                    result = self.export_data(request)
                    
                    if result["success"]:
                        # Add file to ZIP
                        file_path = Path(result["export_path"])
                        zipf.write(file_path, file_path.name)
                        
                        # Clean up individual file
                        file_path.unlink()
                        
                        export_results.append({
                            "format": format_type.value,
                            "success": True,
                            "record_count": result["record_count"]
                        })
                    else:
                        export_results.append({
                            "format": format_type.value,
                            "success": False,
                            "error": result.get("error", "Unknown error")
                        })
            
            return {
                "success": True,
                "zip_path": str(zip_path),
                "zip_size": zip_path.stat().st_size,
                "exports": export_results,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def cleanup_old_exports(self, days_old: int = 7):
        """Clean up export files older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        cleaned_count = 0
        
        for file_path in self.export_dir.glob("*"):
            if file_path.is_file() and file_path.name != "export_log.json":
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime < cutoff_date:
                    try:
                        file_path.unlink()
                        cleaned_count += 1
                    except Exception as e:
                        print(f"Error cleaning up {file_path}: {e}")
        
        print(f"🧹 Cleaned up {cleaned_count} old export files")
        return cleaned_count

# Global export system instance
export_system = ComprehensiveDataExportSystem()
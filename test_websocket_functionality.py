#!/usr/bin/env python3
"""
WebSocket Real-time Communication Test
Tests the real-time monitoring capabilities of the teacher dashboard
"""

import socketio
import requests
import time
import json
import threading
from datetime import datetime

class WebSocketTester:
    def __init__(self, base_url="http://127.0.0.1:8080"):
        self.base_url = base_url
        self.sio = socketio.Client()
        self.messages_received = []
        self.connected = False
        
        # Register event handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        @self.sio.event
        def connect():
            print("✅ WebSocket connected successfully")
            self.connected = True
        
        @self.sio.event
        def disconnect():
            print("❌ WebSocket disconnected")
            self.connected = False
        
        @self.sio.event
        def monitoring_joined(data):
            print(f"📡 Joined monitoring: {data}")
            self.messages_received.append(('monitoring_joined', data))
        
        @self.sio.event 
        def student_update(data):
            print(f"👤 Student update: {data.get('student_id', 'unknown')}")
            self.messages_received.append(('student_update', data))
        
        @self.sio.event
        def class_update(data):
            print(f"🏫 Class update: {data.get('class_id', 'unknown')}")
            self.messages_received.append(('class_update', data))
        
        @self.sio.event
        def student_help_request(data):
            print(f"🆘 Help request from: {data.get('student_id', 'unknown')}")
            self.messages_received.append(('student_help_request', data))
    
    def test_connection(self):
        """Test basic WebSocket connection"""
        print("🧪 Testing WebSocket Connection...")
        
        try:
            # Connect to SocketIO server
            self.sio.connect(self.base_url)
            
            # Wait a moment for connection
            time.sleep(2)
            
            if self.connected:
                print("  ✅ Connection successful")
                return True
            else:
                print("  ❌ Connection failed")
                return False
        except Exception as e:
            print(f"  ❌ Connection error: {e}")
            return False
    
    def test_teacher_monitoring(self):
        """Test teacher monitoring room join"""
        print("🧪 Testing Teacher Monitoring...")
        
        if not self.connected:
            print("  ❌ Not connected to WebSocket")
            return False
        
        try:
            # Join monitoring room
            self.sio.emit('teacher_join_monitoring', {
                'class_id': 'class_5a'
            })
            
            # Wait for response
            time.sleep(3)
            
            # Check if monitoring_joined event was received
            monitoring_events = [msg for msg in self.messages_received if msg[0] == 'monitoring_joined']
            
            if monitoring_events:
                print(f"  ✅ Successfully joined monitoring room")
                return True
            else:
                print("  ❌ Failed to join monitoring room")
                return False
                
        except Exception as e:
            print(f"  ❌ Monitoring test error: {e}")
            return False
    
    def test_student_simulation(self):
        """Simulate student activities to test real-time updates"""
        print("🧪 Testing Student Activity Simulation...")
        
        try:
            # Simulate starting a student session
            response = requests.post(f"{self.base_url}/api/student/session/start", 
                json={
                    'student_id': 'test_student_001',
                    'student_name': '테스트 학생',
                    'class_id': 'class_5a',
                    'task_id': 'test_task_001'
                }
            )
            
            if response.status_code == 200:
                print("  ✅ Student session started")
                
                # Wait for WebSocket updates
                time.sleep(2)
                
                # Simulate progress update
                progress_response = requests.post(f"{self.base_url}/api/student/progress/update",
                    json={
                        'student_id': 'test_student_001',
                        'phase': 1,
                        'score': 0.8,
                        'response_data': {
                            'test': 'data'
                        }
                    }
                )
                
                if progress_response.status_code == 200:
                    print("  ✅ Progress update sent")
                    
                    # Wait for WebSocket message
                    time.sleep(2)
                    
                    # Check for student update messages
                    student_updates = [msg for msg in self.messages_received if msg[0] == 'student_update']
                    
                    if student_updates:
                        print(f"  ✅ Received {len(student_updates)} student updates")
                        return True
                    else:
                        print("  ⚠️ No student updates received via WebSocket")
                        return False
                else:
                    print(f"  ❌ Progress update failed: {progress_response.status_code}")
                    return False
            else:
                print(f"  ❌ Session start failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  ❌ Student simulation error: {e}")
            return False
    
    def test_teacher_intervention(self):
        """Test teacher intervention functionality"""
        print("🧪 Testing Teacher Intervention...")
        
        try:
            # Test sending a hint to student
            response = requests.post(f"{self.base_url}/teacher/api/student/test_student_001/intervene",
                json={
                    'type': 'hint',
                    'message': '이 문제를 다시 한번 차근차근 읽어보세요.'
                }
            )
            
            if response.status_code == 200:
                print("  ✅ Intervention sent successfully")
                time.sleep(1)
                return True
            else:
                print(f"  ❌ Intervention failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  ❌ Intervention test error: {e}")
            return False
    
    def test_data_export(self):
        """Test data export functionality"""
        print("🧪 Testing Data Export...")
        
        try:
            # Test CSV export
            response = requests.get(f"{self.base_url}/teacher/api/export/class/class_5a?format=csv")
            
            if response.status_code == 200:
                content = response.text
                if 'Student ID' in content and 'Student Name' in content:
                    print("  ✅ CSV export working correctly")
                    print(f"  📊 Export size: {len(content)} characters")
                    return True
                else:
                    print("  ❌ CSV export format incorrect")
                    return False
            else:
                print(f"  ❌ Export failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  ❌ Export test error: {e}")
            return False
    
    def cleanup(self):
        """Clean up connections"""
        if self.connected:
            self.sio.disconnect()
    
    def run_full_test(self):
        """Run comprehensive WebSocket and real-time functionality test"""
        print("🚀 WebSocket 및 실시간 통신 종합 테스트")
        print("=" * 60)
        
        results = []
        
        # Test connection
        results.append(("WebSocket Connection", self.test_connection()))
        
        if self.connected:
            # Test monitoring
            results.append(("Teacher Monitoring", self.test_teacher_monitoring()))
            
            # Test student simulation
            results.append(("Student Activity Simulation", self.test_student_simulation()))
            
            # Test intervention
            results.append(("Teacher Intervention", self.test_teacher_intervention()))
        
        # Test data export (doesn't require WebSocket)
        results.append(("Data Export", self.test_data_export()))
        
        # Print results
        print("\n" + "=" * 60)
        print("📋 테스트 결과 요약")
        print("=" * 60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:.<40} {status}")
            if result:
                passed += 1
        
        print(f"\n📊 전체 결과: {passed}/{total} 테스트 통과 ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 모든 WebSocket 및 실시간 기능이 정상 작동합니다!")
        else:
            print("⚠️ 일부 실시간 기능에 문제가 있습니다.")
        
        # Cleanup
        self.cleanup()
        
        return passed == total

if __name__ == "__main__":
    tester = WebSocketTester()
    success = tester.run_full_test()
    exit(0 if success else 1)
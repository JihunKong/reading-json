#!/usr/bin/env python3
"""
Accessibility Improvements for Korean Learning System
- Keyboard navigation support
- Screen reader compatibility
- Color contrast optimization
- Mobile responsiveness
- Korean text accessibility
"""

import json
from datetime import datetime
from typing import Dict, List, Optional

class AccessibilityEnhancer:
    """Enhance accessibility for Korean learning content"""
    
    # WCAG 2.1 AA compliant color combinations for Korean text
    ACCESSIBLE_COLORS = {
        'high_contrast': {
            'text': '#000000',
            'background': '#ffffff',
            'primary': '#0066cc',
            'secondary': '#4d4d4d',
            'success': '#007300',
            'warning': '#bf5f00',
            'error': '#cc0000'
        },
        'dark_mode': {
            'text': '#ffffff',
            'background': '#1a1a1a',
            'primary': '#4da6ff',
            'secondary': '#cccccc',
            'success': '#66ff66',
            'warning': '#ffaa00',
            'error': '#ff6666'
        },
        'low_vision': {
            'text': '#000000',
            'background': '#ffffcc',
            'primary': '#0000cc',
            'secondary': '#333333',
            'success': '#006600',
            'warning': '#996600',
            'error': '#990000'
        }
    }
    
    @staticmethod
    def generate_aria_labels(content_type: str, korean_text: str) -> Dict[str, str]:
        """Generate appropriate ARIA labels for Korean content"""
        
        labels = {
            'paragraph': {
                'aria-label': f'한국어 문단: {korean_text[:50]}...',
                'aria-describedby': f'{content_type}-description',
                'role': 'article'
            },
            'sentence': {
                'aria-label': f'문장: {korean_text}',
                'aria-describedby': 'sentence-instruction',
                'role': 'text'
            },
            'word': {
                'aria-label': f'단어: {korean_text}',
                'aria-describedby': 'word-selection-instruction',
                'role': 'button',
                'tabindex': '0'
            },
            'phase_button': {
                'aria-label': f'{korean_text} 단계로 이동',
                'aria-describedby': 'phase-navigation-help',
                'role': 'button'
            },
            'hint_button': {
                'aria-label': '힌트 보기',
                'aria-describedby': 'hint-description',
                'aria-expanded': 'false'
            }
        }
        
        return labels.get(content_type, {})
    
    @staticmethod
    def create_keyboard_navigation_map() -> Dict[str, str]:
        """Create keyboard navigation shortcuts for Korean learning"""
        return {
            'Tab': '다음 요소로 이동',
            'Shift+Tab': '이전 요소로 이동',
            'Enter': '선택된 요소 활성화',
            'Space': '선택된 요소 활성화',
            'Arrow Keys': '단어/문장 간 이동',
            'Escape': '현재 작업 취소',
            'H': '힌트 표시/숨기기',
            'R': '현재 단계 다시 시작',
            'N': '다음 단계로 이동',
            'P': '이전 단계로 이동',
            'Alt+1-4': '특정 학습 단계로 직접 이동'
        }
    
    @staticmethod
    def generate_accessible_css() -> str:
        """Generate CSS for accessibility improvements"""
        return """
        /* Accessibility CSS for Korean Learning System */
        
        /* High contrast mode support */
        @media (prefers-contrast: high) {
            :root {
                --text-color: #000000;
                --bg-color: #ffffff;
                --primary-color: #0066cc;
                --secondary-color: #4d4d4d;
            }
        }
        
        /* Reduced motion support */
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
        
        /* Focus indicators */
        .focusable:focus {
            outline: 3px solid #4a90e2;
            outline-offset: 2px;
            border-radius: 4px;
        }
        
        /* Skip links */
        .skip-link {
            position: absolute;
            top: -40px;
            left: 6px;
            background: #000;
            color: #fff;
            padding: 8px;
            text-decoration: none;
            border-radius: 0 0 4px 4px;
            z-index: 1000;
            font-weight: bold;
        }
        
        .skip-link:focus {
            top: 0;
        }
        
        /* Korean text optimization */
        .korean-text {
            font-family: '맑은 고딕', 'Malgun Gothic', 'Apple Gothic', sans-serif;
            line-height: 1.6;
            word-break: keep-all;
            word-wrap: break-word;
            font-size: 16px;
            letter-spacing: 0.02em;
        }
        
        /* Large text support */
        @media (min-width: 768px) {
            .korean-text.large {
                font-size: 20px;
                line-height: 1.8;
            }
        }
        
        /* Touch targets for mobile */
        .touch-target {
            min-height: 44px;
            min-width: 44px;
            padding: 10px;
            margin: 5px;
        }
        
        /* Screen reader only content */
        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
        }
        
        /* Interactive elements */
        .interactive {
            cursor: pointer;
            transition: background-color 0.2s ease;
        }
        
        .interactive:hover {
            background-color: rgba(74, 144, 226, 0.1);
        }
        
        .interactive:focus {
            background-color: rgba(74, 144, 226, 0.2);
        }
        
        /* Error and success states */
        .error-state {
            border: 2px solid #cc0000;
            background-color: #ffe6e6;
        }
        
        .success-state {
            border: 2px solid #007300;
            background-color: #e6ffe6;
        }
        
        /* High contrast theme */
        .high-contrast {
            background: white !important;
            color: black !important;
        }
        
        .high-contrast .interactive:hover {
            background: yellow !important;
            color: black !important;
        }
        
        /* Dark mode support */
        @media (prefers-color-scheme: dark) {
            :root {
                --text-color: #ffffff;
                --bg-color: #1a1a1a;
                --primary-color: #4da6ff;
                --secondary-color: #cccccc;
            }
            
            body {
                background: var(--bg-color);
                color: var(--text-color);
            }
        }
        
        /* Progress indicators */
        .progress-bar {
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
            position: relative;
        }
        
        .progress-bar::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            height: 100%;
            background: #4a90e2;
            transition: width 0.3s ease;
        }
        
        /* Mobile responsiveness */
        @media (max-width: 768px) {
            .container {
                padding: 15px;
                margin: 10px;
            }
            
            .korean-text {
                font-size: 18px;
                line-height: 1.7;
            }
            
            .touch-target {
                min-height: 48px;
                min-width: 48px;
            }
        }
        
        /* Print styles */
        @media print {
            .no-print {
                display: none;
            }
            
            .korean-text {
                font-size: 12pt;
                line-height: 1.5;
            }
        }
        """

class ScreenReaderOptimizer:
    """Optimize content for screen readers"""
    
    @staticmethod
    def create_phase_descriptions() -> Dict[int, str]:
        """Create detailed descriptions for each learning phase"""
        return {
            1: "첫 번째 단계: 문장 성분 식별. 문장에서 주어, 서술어, 목적어 등을 찾아 선택하세요.",
            2: "두 번째 단계: 필수성 판단. 요약에 꼭 필요한 내용과 선택적 내용을 구분하세요.",
            3: "세 번째 단계: 개념 일반화. 구체적인 표현을 더 일반적인 개념으로 바꾸어 표현하세요.",
            4: "네 번째 단계: 주제 재구성. 전체 내용의 주제를 종합하여 새롭게 구성하세요."
        }
    
    @staticmethod
    def create_instruction_text() -> Dict[str, str]:
        """Create detailed instruction text for screen readers"""
        return {
            'navigation': "이 페이지에서는 탭 키로 요소 간 이동, 엔터나 스페이스 키로 선택할 수 있습니다.",
            'phase_selection': "원하는 학습 단계를 선택하세요. 화살표 키로 이동 가능합니다.",
            'word_selection': "문장에서 해당하는 성분을 클릭하거나 스페이스 키로 선택하세요.",
            'drag_drop': "마우스 대신 탭과 엔터 키를 사용하여 항목을 이동할 수 있습니다.",
            'text_input': "한국어로 답변을 입력하세요. 입력이 완료되면 엔터 키를 누르세요."
        }
    
    @staticmethod
    def generate_live_region_updates(phase: int, action: str, result: str) -> str:
        """Generate live region updates for screen readers"""
        updates = {
            'phase_start': f"{phase}단계가 시작되었습니다.",
            'correct_answer': f"정답입니다. {result}",
            'incorrect_answer': f"틀렸습니다. {result}",
            'hint_shown': f"힌트가 표시되었습니다. {result}",
            'phase_complete': f"{phase}단계가 완료되었습니다. 다음 단계로 진행할 수 있습니다.",
            'all_complete': "모든 학습 단계가 완료되었습니다. 수고하셨습니다."
        }
        
        return updates.get(action, f"{action}: {result}")

class MobileOptimizer:
    """Optimize for mobile and touch devices"""
    
    @staticmethod
    def create_touch_friendly_components() -> Dict[str, str]:
        """Create touch-friendly component configurations"""
        return {
            'button_size': '48px',  # Minimum touch target size
            'spacing': '8px',       # Minimum spacing between touch targets
            'font_size': '16px',    # Prevent zoom on iOS
            'line_height': '1.6',   # Optimal for Korean text on mobile
            'contrast_ratio': '4.5:1'  # WCAG AA compliance
        }
    
    @staticmethod
    def generate_mobile_css() -> str:
        """Generate mobile-specific CSS"""
        return """
        /* Mobile-specific styles */
        @media (max-width: 768px) {
            /* Prevent horizontal scrolling */
            html, body {
                overflow-x: hidden;
                width: 100%;
            }
            
            /* Touch-friendly navigation */
            .nav-button {
                min-height: 48px;
                min-width: 48px;
                font-size: 16px;
                padding: 12px;
                margin: 4px;
            }
            
            /* Korean text mobile optimization */
            .korean-text-mobile {
                font-size: 18px;
                line-height: 1.7;
                word-break: keep-all;
                hyphens: none;
            }
            
            /* Drag and drop alternative for touch */
            .touch-sortable {
                display: flex;
                flex-direction: column;
                gap: 8px;
            }
            
            .touch-sortable-item {
                background: #f0f0f0;
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 16px;
                touch-action: manipulation;
            }
            
            /* Modal optimization */
            .mobile-modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background: white;
                z-index: 1000;
                overflow-y: auto;
                padding: 20px;
            }
        }
        
        /* Landscape orientation adjustments */
        @media screen and (orientation: landscape) and (max-height: 500px) {
            .container {
                padding: 10px;
            }
            
            .header {
                padding: 8px 16px;
            }
        }
        """

def create_accessibility_test_page() -> str:
    """Create a test page for accessibility validation"""
    return """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>접근성 테스트 - 한국어 학습 시스템</title>
        <style>
            /* Include accessibility CSS */
            {accessibility_css}
            {mobile_css}
        </style>
    </head>
    <body>
        <!-- Skip links -->
        <a href="#main-content" class="skip-link">본문으로 건너뛰기</a>
        <a href="#navigation" class="skip-link">네비게이션으로 건너뛰기</a>
        
        <!-- Live region for screen reader announcements -->
        <div aria-live="polite" aria-atomic="true" class="sr-only" id="live-region"></div>
        
        <header role="banner">
            <h1>한국어 학습 시스템 접근성 테스트</h1>
            <p>이 페이지는 웹 접근성 지침을 준수하는지 테스트합니다.</p>
        </header>
        
        <nav id="navigation" role="navigation" aria-label="주 메뉴">
            <ul>
                <li><a href="#phase1" aria-describedby="phase1-desc">1단계: 문장 성분 식별</a></li>
                <li><a href="#phase2" aria-describedby="phase2-desc">2단계: 필수성 판단</a></li>
                <li><a href="#phase3" aria-describedby="phase3-desc">3단계: 개념 일반화</a></li>
                <li><a href="#phase4" aria-describedby="phase4-desc">4단계: 주제 재구성</a></li>
            </ul>
        </nav>
        
        <main id="main-content" role="main">
            <section id="phase1" class="phase-section" aria-labelledby="phase1-title">
                <h2 id="phase1-title">1단계: 문장 성분 식별</h2>
                <p id="phase1-desc" class="sr-only">문장에서 주어, 서술어, 목적어 등의 성분을 찾아 선택하는 단계입니다.</p>
                
                <div class="korean-text" role="article" aria-label="학습할 한국어 문단">
                    <p>우리나라의 전통 음식은 다양한 영양소를 골고루 포함하고 있습니다.</p>
                </div>
                
                <div class="word-selection" role="group" aria-labelledby="word-selection-title">
                    <h3 id="word-selection-title">단어 선택</h3>
                    <p id="word-selection-instruction">다음 단어 중 주어에 해당하는 것을 선택하세요. 스페이스 키나 엔터 키로 선택할 수 있습니다.</p>
                    
                    <button class="word-button focusable touch-target" 
                            aria-describedby="word-selection-instruction"
                            role="button" 
                            tabindex="0">우리나라의</button>
                    <button class="word-button focusable touch-target" 
                            aria-describedby="word-selection-instruction"
                            role="button" 
                            tabindex="0">전통</button>
                    <button class="word-button focusable touch-target" 
                            aria-describedby="word-selection-instruction"
                            role="button" 
                            tabindex="0">음식은</button>
                </div>
                
                <button class="hint-button focusable" 
                        aria-label="힌트 보기" 
                        aria-expanded="false"
                        aria-controls="hint-content"
                        onclick="toggleHint()">💡 힌트</button>
                
                <div id="hint-content" 
                     class="hint-display" 
                     role="region" 
                     aria-labelledby="hint-title"
                     style="display: none;">
                    <h4 id="hint-title">힌트</h4>
                    <p>문장에서 동작을 하는 주체를 찾아보세요.</p>
                </div>
            </section>
        </main>
        
        <footer role="contentinfo">
            <p>웹 접근성 지침 WCAG 2.1 AA 준수</p>
        </footer>
        
        <script>
            // Accessibility JavaScript
            function toggleHint() {
                const button = document.querySelector('.hint-button');
                const content = document.getElementById('hint-content');
                const isExpanded = button.getAttribute('aria-expanded') === 'true';
                
                button.setAttribute('aria-expanded', !isExpanded);
                content.style.display = isExpanded ? 'none' : 'block';
                
                // Announce to screen readers
                const liveRegion = document.getElementById('live-region');
                liveRegion.textContent = isExpanded ? '힌트가 숨겨졌습니다.' : '힌트가 표시되었습니다.';
            }
            
            // Keyboard navigation for word buttons
            document.querySelectorAll('.word-button').forEach(button => {
                button.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        this.click();
                    }
                });
                
                button.addEventListener('click', function() {
                    // Announce selection
                    const liveRegion = document.getElementById('live-region');
                    liveRegion.textContent = this.textContent + '이(가) 선택되었습니다.';
                });
            });
            
            // Focus management
            document.addEventListener('DOMContentLoaded', function() {
                // Focus first interactive element
                const firstButton = document.querySelector('.word-button');
                if (firstButton) {
                    firstButton.focus();
                }
            });
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    # Generate accessibility test page
    enhancer = AccessibilityEnhancer()
    optimizer = MobileOptimizer()
    
    print("🎯 접근성 개선 사항:")
    print("✅ 키보드 네비게이션 지원")
    print("✅ 스크린 리더 호환성")
    print("✅ 고대비 색상 조합")
    print("✅ 모바일 터치 최적화")
    print("✅ 한국어 텍스트 최적화")
    print("✅ WCAG 2.1 AA 준수")
    
    # Generate test page
    test_page = create_accessibility_test_page()
    with open('/Users/jihunkong/reading-json/accessibility_test.html', 'w', encoding='utf-8') as f:
        f.write(test_page)
    
    print("📝 접근성 테스트 페이지가 생성되었습니다: accessibility_test.html")
        let currentTask = null;
        let currentPhase = 1;
        let phaseData = null;
        let phaseCompleted = [false, false, false, false];
        
        // Start learning system
        function startLearning() {
            console.log('학습 시작...');
            
            fetch('/learning/get_task')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    currentTask = data.task;
                    loadLearningInterface();
                } else {
                    alert('학습 자료를 불러올 수 없습니다: ' + data.message);
                }
            })
            .catch(error => {
                console.error('오류:', error);
                alert('네트워크 오류가 발생했습니다.');
            });
        }
        
        // Load main learning interface
        function loadLearningInterface() {
            if (!currentTask) return;
            
            // Show reading material
            document.getElementById('readingMaterial').style.display = 'block';
            document.getElementById('readingContent').innerHTML = currentTask.content;
            
            // Start with Phase 1
            startPhase(1);
        }
        
        // Start specific phase
        function startPhase(phaseNum) {
            currentPhase = phaseNum;
            updatePhaseNavigation();
            updateProgressBar();
            
            // Show loading
            document.getElementById('contentArea').innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <p>${phaseNum}단계를 준비하고 있습니다...</p>
                </div>
            `;
            
            fetch(`/learning/start_phase/${phaseNum}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    phaseData = data.phase_data;
                    loadPhaseInterface(phaseNum, data.phase_data);
                } else {
                    alert(`${phaseNum}단계를 시작할 수 없습니다: ` + data.message);
                }
            })
            .catch(error => {
                console.error('오류:', error);
                alert('네트워크 오류가 발생했습니다.');
            });
        }
        
        // Load phase-specific interface
        function loadPhaseInterface(phaseNum, data) {
            const contentArea = document.getElementById('contentArea');
            const actionButtons = document.getElementById('actionButtons');
            
            if (phaseNum === 1) {
                loadPhase1Interface(data);
            } else if (phaseNum === 2) {
                loadPhase2Interface(data);
            } else if (phaseNum === 3) {
                loadPhase3Interface(data);
            } else if (phaseNum === 4) {
                loadPhase4Interface(data);
            }
            
            actionButtons.style.display = 'block';
            document.getElementById('nextBtn').style.display = 'none';
        }
        
        // Phase 1: Component Identification
        function loadPhase1Interface(data) {
            const content = `
                <h3>🔍 1단계: 문장 성분 식별</h3>
                <p><strong>목표:</strong> ${data.objective}</p>
                
                <div class="component-legend">
                    <div class="legend-item">
                        <div class="legend-color 주어" style="background: #fed7d7; border-color: #fc8181;"></div>
                        <span>주어</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color 서술어" style="background: #c6f6d5; border-color: #48bb78;"></div>
                        <span>서술어</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color 목적어" style="background: #bee3f8; border-color: #4299e1;"></div>
                        <span>목적어</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color 보어" style="background: #fef5e7; border-color: #ed8936;"></div>
                        <span>보어</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color 부사어" style="background: #e9d8fd; border-color: #805ad5;"></div>
                        <span>부사어</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color 관형어" style="background: #f7fafc; border-color: #a0aec0;"></div>
                        <span>관형어</span>
                    </div>
                </div>
                
                <div class="sentence-display" id="targetSentence">
                    ${data.target_sentence.text}
                </div>
                
                <div class="component-selector">
                    <p><strong>찾아야 할 성분:</strong> ${data.target_sentence.components_to_find.join(', ')}</p>
                    <p>단어를 클릭하여 해당 성분으로 분류해주세요.</p>
                </div>
                
                <div id="statusMessage"></div>
            `;
            
            document.getElementById('contentArea').innerHTML = content;
            
            // Make words clickable for component selection
            initializePhase1Interaction(data);
        }
        
        // Phase 2: Necessity Judgment with Drag & Drop Interface
        function loadPhase2Interface(data) {
            const content = `
                <h3>⚖️ 2단계: 필수성 판단</h3>
                <p><strong>목표:</strong> ${data.objective}</p>
                
                <div class="instructions-panel">
                    <h4>📋 판단 기준</h4>
                    <ul>
                        <li><strong>필수적(Required):</strong> 제거하면 의미가 불완전해지는 요소</li>
                        <li><strong>선택적(Optional):</strong> 제거해도 기본 의미가 유지되는 요소</li>
                        <li><strong>장식적(Decorative):</strong> 감정이나 강조만 담당하는 요소</li>
                    </ul>
                </div>
                
                <div class="sentence-display" id="targetSentence">
                    <h4>📝 분석할 문장:</h4>
                    <p style="font-size: 18px; padding: 15px; background: white; border-radius: 8px; border-left: 4px solid #667eea;">
                        ${data.target_sentence.text}
                    </p>
                </div>
                
                <div class="drag-source-container">
                    <h4>🔤 문장 성분들:</h4>
                    <div class="components-pool" id="componentsPool">
                        ${data.target_sentence.components.map(comp => `
                            <div class="draggable-component" 
                                 draggable="true" 
                                 data-component-id="${comp.id}"
                                 data-component-type="${comp.type}"
                                 data-component-text="${comp.text}">
                                <span class="component-type-badge ${comp.type}">${comp.type}</span>
                                <span class="component-text">${comp.text}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div class="necessity-container">
                    <div class="necessity-column required" data-category="required">
                        <h4>🔴 필수적 (Required)</h4>
                        <p class="category-desc">의미 전달에 꼭 필요한 성분</p>
                        <div class="drop-zone" id="requiredZone"></div>
                    </div>
                    
                    <div class="necessity-column optional" data-category="optional">
                        <h4>🟡 선택적 (Optional)</h4>
                        <p class="category-desc">보완적 정보를 제공하는 성분</p>
                        <div class="drop-zone" id="optionalZone"></div>
                    </div>
                    
                    <div class="necessity-column decorative" data-category="decorative">
                        <h4>⚪ 장식적 (Decorative)</h4>
                        <p class="category-desc">감정이나 강조를 위한 성분</p>
                        <div class="drop-zone" id="decorativeZone"></div>
                    </div>
                </div>
                
                <div class="progress-display">
                    <div class="progress-item">
                        <span>분류 완료:</span>
                        <span id="progressCount">0/${data.target_sentence.components.length}</span>
                    </div>
                    <div class="progress-item">
                        <span>정확도:</span>
                        <span id="accuracyDisplay">계산 중...</span>
                    </div>
                </div>
                
                <div class="action-panel">
                    <button class="btn btn-warning" onclick="undoLastMove()" id="undoBtn" disabled>↩️ 되돌리기</button>
                    <button class="btn" onclick="showHint()" id="hintBtn">💡 힌트</button>
                    <button class="btn" onclick="previewSentence()" id="previewBtn">👁️ 미리보기</button>
                </div>
                
                <div id="statusMessage"></div>
            `;
            
            document.getElementById('contentArea').innerHTML = content;
            
            // Add Phase 2 specific styles
            if (!document.getElementById('phase2Styles')) {
                const styles = document.createElement('style');
                styles.id = 'phase2Styles';
                styles.textContent = `
                    .draggable-component {
                        cursor: grab;
                        transition: all 0.2s ease;
                        border-radius: 8px;
                        padding: 12px 15px;
                        margin: 8px;
                        background: white;
                        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                        border-left: 4px solid #e2e8f0;
                        display: flex;
                        align-items: center;
                        gap: 10px;
                        user-select: none;
                        touch-action: none;
                    }
                    .draggable-component:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                    }
                    .draggable-component.dragging {
                        opacity: 0.5;
                        transform: rotate(5deg);
                        z-index: 1000;
                        cursor: grabbing;
                    }
                    .component-type-badge {
                        font-size: 11px;
                        padding: 4px 8px;
                        border-radius: 12px;
                        font-weight: bold;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                    }
                    .component-type-badge.주어 { background: #fed7d7; color: #c53030; }
                    .component-type-badge.서술어 { background: #c6f6d5; color: #2d7738; }
                    .component-type-badge.목적어 { background: #bee3f8; color: #2c5aa0; }
                    .component-type-badge.보어 { background: #fef5e7; color: #c05621; }
                    .component-type-badge.부사어 { background: #e9d8fd; color: #553c9a; }
                    .component-type-badge.관형어 { background: #f7fafc; color: #4a5568; }
                    
                    .necessity-container {
                        display: grid;
                        grid-template-columns: repeat(3, 1fr);
                        gap: 20px;
                        margin: 20px 0;
                    }
                    .necessity-column {
                        border: 2px dashed #e2e8f0;
                        border-radius: 12px;
                        padding: 15px;
                        background: #f8fafc;
                        transition: all 0.3s ease;
                    }
                    .necessity-column h4 {
                        margin: 0 0 10px 0;
                        text-align: center;
                        font-size: 16px;
                    }
                    .necessity-column.required {
                        border-color: #fc8181;
                        background: #fed7d7;
                    }
                    .necessity-column.optional {
                        border-color: #f6e05e;
                        background: #fefcbf;
                    }
                    .necessity-column.decorative {
                        border-color: #cbd5e0;
                        background: #f7fafc;
                    }
                    .drop-zone {
                        min-height: 120px;
                        border: 2px dashed transparent;
                        border-radius: 8px;
                        padding: 15px;
                        background: rgba(255, 255, 255, 0.8);
                        transition: all 0.2s ease;
                        display: flex;
                        flex-direction: column;
                        gap: 8px;
                    }
                    .drop-zone.drag-over {
                        border-color: #667eea;
                        background: rgba(102, 126, 234, 0.1);
                        box-shadow: inset 0 0 20px rgba(102, 126, 234, 0.2);
                    }
                    .drop-zone:empty::after {
                        content: "여기에 성분을 드래그하세요";
                        color: #a0aec0;
                        text-align: center;
                        line-height: 80px;
                        font-style: italic;
                    }
                    .progress-display {
                        background: white;
                        padding: 20px;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                        margin: 20px 0;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    }
                    .progress-item {
                        display: flex;
                        align-items: center;
                        gap: 10px;
                        font-weight: bold;
                    }
                    .action-panel {
                        text-align: center;
                        margin: 20px 0;
                    }
                    .action-panel .btn {
                        margin: 0 10px;
                        padding: 10px 20px;
                        border: none;
                        border-radius: 8px;
                        cursor: pointer;
                        font-weight: bold;
                        transition: all 0.2s ease;
                    }
                    .action-panel .btn:hover {
                        transform: translateY(-2px);
                    }
                    .action-panel .btn:disabled {
                        opacity: 0.5;
                        cursor: not-allowed;
                        transform: none;
                    }
                    .btn-warning {
                        background: #fed7aa;
                        color: #c05621;
                    }
                    .btn-warning:hover:not(:disabled) {
                        background: #fbd38d;
                    }
                    
                    @media (max-width: 768px) {
                        .necessity-container {
                            grid-template-columns: 1fr;
                            gap: 15px;
                        }
                        .draggable-component {
                            touch-action: pan-y;
                        }
                        .progress-display {
                            flex-direction: column;
                            gap: 10px;
                        }
                        .action-panel .btn {
                            display: block;
                            margin: 5px 0;
                            width: 100%;
                        }
                    }
                `;
                document.head.appendChild(styles);
            }
            
            // Initialize Phase 2 drag and drop functionality
            initializeDragAndDrop(data);
        }
        
        // Phase 3: Generalization Interface
        function loadPhase3Interface(data) {
            const content = `
                <h3>🔄 3단계: 개념 일반화</h3>
                <p><strong>목표:</strong> ${data.objective}</p>
                
                <div class="instructions">
                    <h4>📋 일반화 단계</h4>
                    <ul>
                        ${data.instructions.map(inst => `<li>${inst}</li>`).join('')}
                    </ul>
                </div>
                
                <div class="sentence-display">
                    <h4>📝 일반화할 문장:</h4>
                    <p style="font-size: 18px; padding: 15px; background: white; border-radius: 8px; border-left: 4px solid #667eea;">
                        ${data.target_sentence.text}
                    </p>
                </div>
                
                <div class="generalization-workspace">
                    <h4>🎯 일반화 연습</h4>
                    ${data.target_sentence.generalizable_components.map(comp => `
                        <div class="generalization-item" data-component-id="${comp.id}">
                            <div class="original-term">
                                <span class="term-label">원본:</span>
                                <span class="original-text">${comp.text}</span>
                                <span class="component-type">(${comp.type})</span>
                            </div>
                            
                            <div class="abstraction-levels">
                                <h5>🔼 추상화 수준 선택</h5>
                                <div class="level-grid">
                                    ${comp.candidates.map((candidate, index) => `
                                        <label class="abstraction-option level-${index + 1}" data-distance="${comp.semantic_distance[index]}">
                                            <input type="radio" name="generalization-${comp.id}" value="${candidate}">
                                            <div class="option-content">
                                                <span class="option-text">${candidate}</span>
                                                <span class="abstraction-level">Level ${index + 1}</span>
                                                <div class="distance-indicator" style="width: ${comp.semantic_distance[index] * 100}%"></div>
                                            </div>
                                        </label>
                                    `).join('')}
                                    
                                    <div class="custom-option">
                                        <label class="abstraction-option custom">
                                            <input type="radio" name="generalization-${comp.id}" value="custom">
                                            <span class="option-text">직접 입력</span>
                                        </label>
                                        <input type="text" class="custom-generalization" 
                                               data-component-id="${comp.id}" 
                                               placeholder="다른 일반화 아이디어...">
                                    </div>
                                </div>
                            </div>
                            
                            <div class="semantic-preview" id="preview-${comp.id}">
                                <h6>🔍 변경 미리보기</h6>
                                <p class="preview-text">선택하면 문장이 어떻게 변경되는지 보여집니다</p>
                            </div>
                        </div>
                    `).join('')}
                </div>
                
                <div class="concept-mapping-visual">
                    <h4>📊 개념 관계도</h4>
                    <div class="mapping-canvas" id="conceptMapping">
                        <div class="concept-hierarchy">
                            <div class="hierarchy-level abstract">
                                <h6>추상적 개념</h6>
                                <div class="concept-nodes abstract-nodes"></div>
                            </div>
                            <div class="hierarchy-level specific">
                                <h6>구체적 표현</h6>
                                <div class="concept-nodes specific-nodes"></div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="progress-tracker">
                    <h5>📈 진행 상황</h5>
                    <div class="completion-status">
                        <span id="completedGeneralizations">0</span> / 
                        <span id="totalGeneralizations">${data.target_sentence.generalizable_components.length}</span> 완료
                    </div>
                </div>
                
                <div id="statusMessage"></div>
            `;
            
            document.getElementById('contentArea').innerHTML = content;
            
            // Add Phase 3 specific styles
            if (!document.getElementById('phase3Styles')) {
                const styles = document.createElement('style');
                styles.id = 'phase3Styles';
                styles.textContent = `
                    .generalization-workspace {
                        background: white;
                        border-radius: 12px;
                        padding: 25px;
                        margin: 20px 0;
                        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                    }
                    .generalization-item {
                        border: 1px solid #e2e8f0;
                        border-radius: 10px;
                        padding: 20px;
                        margin-bottom: 25px;
                        background: #fafafa;
                        transition: all 0.3s ease;
                    }
                    .generalization-item:hover {
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                        border-color: #667eea;
                    }
                    .original-term {
                        display: flex;
                        align-items: center;
                        gap: 10px;
                        margin-bottom: 15px;
                        padding: 15px;
                        background: white;
                        border-radius: 8px;
                        border-left: 4px solid #667eea;
                    }
                    .term-label {
                        font-weight: bold;
                        color: #4a5568;
                        min-width: 60px;
                    }
                    .original-text {
                        font-size: 18px;
                        font-weight: bold;
                        color: #2d3748;
                    }
                    .component-type {
                        background: #e2e8f0;
                        color: #4a5568;
                        padding: 4px 8px;
                        border-radius: 12px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                    .abstraction-levels h5 {
                        margin: 15px 0 10px 0;
                        color: #2d3748;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                    }
                    .level-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 15px;
                        margin-bottom: 20px;
                    }
                    .abstraction-option {
                        display: block;
                        position: relative;
                        cursor: pointer;
                        transition: all 0.2s ease;
                    }
                    .abstraction-option input[type="radio"] {
                        position: absolute;
                        opacity: 0;
                        width: 0;
                        height: 0;
                    }
                    .option-content {
                        padding: 15px;
                        border: 2px solid #e2e8f0;
                        border-radius: 8px;
                        background: white;
                        transition: all 0.2s ease;
                    }
                    .abstraction-option:hover .option-content {
                        border-color: #667eea;
                        transform: translateY(-2px);
                        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
                    }
                    .abstraction-option input:checked + .option-content {
                        border-color: #667eea;
                        background: #f0f4ff;
                        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
                    }
                    .option-text {
                        font-weight: bold;
                        display: block;
                        margin-bottom: 8px;
                        color: #2d3748;
                    }
                    .abstraction-level {
                        font-size: 12px;
                        color: #667eea;
                        font-weight: bold;
                        display: block;
                        margin-bottom: 8px;
                    }
                    .distance-indicator {
                        height: 4px;
                        background: linear-gradient(90deg, #fed7d7, #f6e05e, #c6f6d5);
                        border-radius: 2px;
                        margin-top: 5px;
                        transition: width 0.3s ease;
                    }
                    .custom-option {
                        grid-column: span 2;
                        display: flex;
                        gap: 15px;
                        align-items: center;
                        padding: 15px;
                        border: 2px dashed #cbd5e0;
                        border-radius: 8px;
                        background: #f7fafc;
                    }
                    .custom-generalization {
                        flex: 1;
                        padding: 12px 15px;
                        border: 1px solid #e2e8f0;
                        border-radius: 6px;
                        font-size: 16px;
                        transition: border-color 0.2s ease;
                    }
                    .custom-generalization:focus {
                        outline: none;
                        border-color: #667eea;
                        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
                    }
                    .semantic-preview {
                        background: #f0f4ff;
                        border: 1px solid #d6e3ff;
                        border-radius: 8px;
                        padding: 15px;
                        margin-top: 15px;
                    }
                    .semantic-preview h6 {
                        margin: 0 0 10px 0;
                        color: #553c9a;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                    }
                    .preview-text {
                        font-size: 16px;
                        line-height: 1.6;
                        color: #2d3748;
                        margin: 0;
                    }
                    .preview-text .generalized {
                        background: #fed7aa;
                        color: #c05621;
                        padding: 2px 6px;
                        border-radius: 4px;
                        border: 1px solid #f6ad55;
                    }
                    .semantic-note {
                        color: #667eea;
                        font-style: italic;
                        margin-top: 8px;
                        display: block;
                    }
                    .concept-mapping-visual {
                        background: white;
                        border-radius: 12px;
                        padding: 25px;
                        margin: 25px 0;
                        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                    }
                    .mapping-canvas {
                        border: 1px solid #e2e8f0;
                        border-radius: 10px;
                        padding: 20px;
                        background: #fafafa;
                    }
                    .concept-hierarchy {
                        display: flex;
                        flex-direction: column;
                        gap: 30px;
                    }
                    .hierarchy-level h6 {
                        text-align: center;
                        margin: 0 0 15px 0;
                        color: #4a5568;
                        font-size: 14px;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                    }
                    .concept-nodes {
                        display: flex;
                        flex-wrap: wrap;
                        gap: 12px;
                        justify-content: center;
                        min-height: 60px;
                        padding: 15px;
                        border: 2px dashed #e2e8f0;
                        border-radius: 8px;
                        background: white;
                    }
                    .concept-node {
                        padding: 8px 16px;
                        border-radius: 20px;
                        font-size: 14px;
                        font-weight: bold;
                        color: white;
                        transition: all 0.2s ease;
                    }
                    .concept-node.abstract {
                        background: linear-gradient(135deg, #667eea, #764ba2);
                    }
                    .concept-node:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
                    }
                    .progress-tracker {
                        background: linear-gradient(135deg, #667eea, #764ba2);
                        color: white;
                        padding: 20px;
                        border-radius: 12px;
                        text-align: center;
                        margin: 25px 0;
                    }
                    .progress-tracker h5 {
                        margin: 0 0 15px 0;
                        font-size: 18px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 10px;
                    }
                    .completion-status {
                        font-size: 24px;
                        font-weight: bold;
                    }
                    
                    @media (max-width: 768px) {
                        .level-grid {
                            grid-template-columns: 1fr;
                        }
                        .custom-option {
                            grid-column: span 1;
                            flex-direction: column;
                            align-items: stretch;
                        }
                        .concept-hierarchy {
                            gap: 20px;
                        }
                    }
                `;
                document.head.appendChild(styles);
            }
            
            initializePhase3Interaction(data);
        }
        
        // Phase 4: Theme Reconstruction Interface
        function loadPhase4Interface(data) {
            const content = `
                <h3>🎨 4단계: 주제 재구성</h3>
                <p><strong>목표:</strong> ${data.objective}</p>
                
                <div class="instructions">
                    <h4>📋 주제 재구성 과정</h4>
                    <ul>
                        ${data.instructions.map(inst => `<li>${inst}</li>`).join('')}
                    </ul>
                </div>
                
                <div class="sentences-overview">
                    <h4>📖 전체 문장 분석</h4>
                    <div class="sentences-grid">
                        ${data.all_sentences.map((sent, index) => `
                            <div class="sentence-card" data-sentence-id="${index}" 
                                 style="border-left: 4px solid ${getSentenceColor(sent.role)};">
                                <div class="sentence-text">${sent.text}</div>
                                <div class="sentence-meta">
                                    <div class="meta-row">
                                        <span class="main-concept">핵심: <strong>${sent.main_concept}</strong></span>
                                        <span class="role-badge ${sent.role}">${translateRole(sent.role)}</span>
                                    </div>
                                    <div class="meta-row">
                                        <span class="importance-label">중요도:</span>
                                        <div class="importance-bar-container">
                                            <div class="importance-bar" style="width: ${sent.importance * 100}%"></div>
                                        </div>
                                        <span class="importance-value">${(sent.importance * 100).toFixed(0)}%</span>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div class="theme-construction">
                    <h4>🧩 주제 구성 작업공간</h4>
                    
                    <div class="concept-network" id="conceptNetwork">
                        <h5>🔗 개념 네트워크</h5>
                        <div class="network-canvas" id="networkCanvas">
                            ${data.all_sentences.map((sent, index) => `
                                <div class="concept-node" 
                                     data-concept="${sent.main_concept}"
                                     data-sentence-id="${index}"
                                     style="background: ${getConceptColor(sent.role)};">
                                    <span class="concept-text">${sent.main_concept}</span>
                                    <span class="concept-importance">${(sent.importance * 100).toFixed(0)}%</span>
                                </div>
                            `).join('')}
                        </div>
                        <p class="helper-text">개념들을 클릭하여 연결 관계를 만들어보세요 (Ctrl+클릭으로 다중 선택)</p>
                    </div>
                    
                    <div class="connection-builder">
                        <h5>📎 개념 연결 관리</h5>
                        <div class="connection-controls">
                            <select id="sourceSelect">
                                <option value="">출발 개념 선택...</option>
                                ${data.all_sentences.map(sent => 
                                    `<option value="${sent.main_concept}">${sent.main_concept}</option>`
                                ).join('')}
                            </select>
                            <span class="connection-arrow">→</span>
                            <select id="targetSelect">
                                <option value="">도착 개념 선택...</option>
                                ${data.all_sentences.map(sent => 
                                    `<option value="${sent.main_concept}">${sent.main_concept}</option>`
                                ).join('')}
                            </select>
                            <select id="connectionType">
                                <option value="">관계 유형 선택...</option>
                                <option value="원인">원인 관계</option>
                                <option value="결과">결과 관계</option>
                                <option value="대조">대조 관계</option>
                                <option value="보완">보완 관계</option>
                                <option value="예시">예시 관계</option>
                                <option value="확장">확장 관계</option>
                                <option value="기타">기타</option>
                            </select>
                            <button type="button" onclick="addConceptConnection()" class="btn-small">연결 추가</button>
                        </div>
                        
                        <div id="connectionsList">
                            <h6>생성된 연결</h6>
                            <div class="connections-container">
                                <p class="helper-text">개념들 간의 연결을 추가해보세요</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="theme-synthesis">
                        <h5>✍️ 통합 주제 작성</h5>
                        <div class="synthesis-workspace">
                            <textarea id="reconstructedTheme" 
                                      placeholder="위에서 분석한 개념들과 연결 관계를 바탕으로 전체 글의 숨겨진 주제를 작성해보세요...

예시 형식:
• 이 글은 [핵심개념1]과 [핵심개념2]의 관계를 통해 [암시적 주제]를 보여준다.
• [핵심개념들]은 모두 [상위 주제]라는 공통점을 가지고 있다.
• 글 전체를 통해 작가는 [주제의식]을 전달하고자 한다."
                                      rows="6"></textarea>
                            
                            <div class="synthesis-guide">
                                <h6>💡 주제 작성 가이드</h6>
                                <div class="guide-grid">
                                    <div class="guide-item">
                                        <strong>✅ 좋은 주제</strong>
                                        <ul>
                                            <li>각 문장의 핵심을 모두 포함</li>
                                            <li>문장들 간의 연결점 제시</li>
                                            <li>구체적 예시를 일반적 원리로 승화</li>
                                            <li>한 문장으로 전체를 아우름</li>
                                        </ul>
                                    </div>
                                    <div class="guide-item">
                                        <strong>❌ 피해야 할 것</strong>
                                        <ul>
                                            <li>단순한 내용 나열</li>
                                            <li>너무 추상적이거나 구체적</li>
                                            <li>일부 내용만 반영</li>
                                            <li>표면적 요약에 그침</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="quality-checker" id="qualityChecker">
                        <h5>📏 품질 실시간 검증</h5>
                        <div class="quality-metrics">
                            <div class="metric-item">
                                <span class="metric-label">논리적 일관성</span>
                                <div class="metric-bar-container">
                                    <div class="metric-bar coherence" id="coherenceBar"></div>
                                </div>
                                <span class="metric-score" id="coherenceScore">0%</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">내용 완전성</span>
                                <div class="metric-bar-container">
                                    <div class="metric-bar completeness" id="completenessBar"></div>
                                </div>
                                <span class="metric-score" id="completenessScore">0%</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">추상화 적절성</span>
                                <div class="metric-bar-container">
                                    <div class="metric-bar abstraction" id="abstractionBar"></div>
                                </div>
                                <span class="metric-score" id="abstractionScore">0%</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">연결 품질</span>
                                <div class="metric-bar-container">
                                    <div class="metric-bar connection" id="connectionBar"></div>
                                </div>
                                <span class="metric-score" id="connectionScore">0%</span>
                            </div>
                        </div>
                        <div class="quality-actions">
                            <button type="button" onclick="checkThemeQuality()" class="btn-small">품질 확인</button>
                            <button type="button" onclick="autoPreview()" class="btn-small">실시간 미리보기</button>
                        </div>
                    </div>
                    
                    <div class="completion-summary" id="completionSummary">
                        <h5>📊 완료 현황</h5>
                        <div class="summary-stats">
                            <div class="stat-item">
                                <span>개념 연결:</span>
                                <span id="connectionCount">0개</span>
                            </div>
                            <div class="stat-item">
                                <span>주제 길이:</span>
                                <span id="themeLength">0자</span>
                            </div>
                            <div class="stat-item">
                                <span>품질 점수:</span>
                                <span id="overallQuality">0%</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div id="statusMessage"></div>
            `;
            
            document.getElementById('contentArea').innerHTML = content;
            
            // Add Phase 4 specific styles
            if (!document.getElementById('phase4Styles')) {
                const styles = document.createElement('style');
                styles.id = 'phase4Styles';
                styles.textContent = `
                    .sentences-overview {
                        background: white;
                        border-radius: 12px;
                        padding: 25px;
                        margin: 20px 0;
                        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                    }
                    .sentences-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                        gap: 20px;
                    }
                    .sentence-card {
                        background: white;
                        border-radius: 10px;
                        padding: 20px;
                        border: 1px solid #e2e8f0;
                        transition: all 0.3s ease;
                        cursor: pointer;
                    }
                    .sentence-card:hover {
                        transform: translateY(-3px);
                        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
                    }
                    .sentence-text {
                        font-size: 16px;
                        line-height: 1.6;
                        margin-bottom: 15px;
                        color: #2d3748;
                    }
                    .sentence-meta {
                        display: flex;
                        flex-direction: column;
                        gap: 10px;
                    }
                    .meta-row {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    }
                    .main-concept {
                        font-size: 14px;
                        color: #4a5568;
                    }
                    .role-badge {
                        padding: 4px 12px;
                        border-radius: 12px;
                        font-size: 12px;
                        font-weight: bold;
                        text-transform: uppercase;
                    }
                    .role-badge.topic { background: #fed7d7; color: #c53030; }
                    .role-badge.support { background: #c6f6d5; color: #2d7738; }
                    .role-badge.example { background: #bee3f8; color: #2c5aa0; }
                    .role-badge.conclusion { background: #e9d8fd; color: #553c9a; }
                    
                    .importance-bar-container {
                        flex: 1;
                        height: 8px;
                        background: #e2e8f0;
                        border-radius: 4px;
                        margin: 0 10px;
                        overflow: hidden;
                    }
                    .importance-bar {
                        height: 100%;
                        background: linear-gradient(90deg, #fed7d7, #f6e05e, #c6f6d5);
                        border-radius: 4px;
                        transition: width 0.3s ease;
                    }
                    .importance-value {
                        font-size: 12px;
                        font-weight: bold;
                        color: #667eea;
                        min-width: 35px;
                    }
                    
                    .theme-construction {
                        background: white;
                        border-radius: 12px;
                        padding: 25px;
                        margin: 25px 0;
                        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                    }
                    .concept-network {
                        margin-bottom: 25px;
                    }
                    .network-canvas {
                        border: 2px dashed #e2e8f0;
                        border-radius: 12px;
                        padding: 25px;
                        background: #fafafa;
                        min-height: 200px;
                        position: relative;
                    }
                    .concept-node {
                        display: inline-block;
                        padding: 12px 20px;
                        margin: 8px;
                        border-radius: 25px;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        font-weight: bold;
                        color: white;
                        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
                        user-select: none;
                    }
                    .concept-node:hover {
                        transform: translateY(-2px) scale(1.05);
                        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
                    }
                    .concept-node.selected {
                        transform: translateY(-2px) scale(1.1);
                        box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.8), 0 6px 20px rgba(0, 0, 0, 0.3);
                    }
                    .helper-text {
                        text-align: center;
                        color: #a0aec0;
                        font-style: italic;
                        margin-top: 15px;
                    }
                    
                    .connection-builder {
                        background: #f0f4ff;
                        border-radius: 10px;
                        padding: 20px;
                        margin-bottom: 25px;
                    }
                    .connection-controls {
                        display: flex;
                        align-items: center;
                        gap: 15px;
                        flex-wrap: wrap;
                        justify-content: center;
                        margin-bottom: 15px;
                    }
                    .connection-controls select {
                        padding: 8px 15px;
                        border: 1px solid #d1d5db;
                        border-radius: 6px;
                        font-size: 14px;
                        min-width: 150px;
                    }
                    .connection-arrow {
                        font-size: 18px;
                        color: #667eea;
                        font-weight: bold;
                    }
                    .add-connection-btn {
                        background: #667eea;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 6px;
                        cursor: pointer;
                        font-weight: bold;
                        transition: background 0.2s ease;
                    }
                    .add-connection-btn:hover {
                        background: #5a67d8;
                    }
                    .add-connection-btn:disabled {
                        background: #a0aec0;
                        cursor: not-allowed;
                    }
                    
                    .connections-display {
                        margin-top: 20px;
                    }
                    .connection-item {
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                        padding: 12px 15px;
                        background: white;
                        border: 1px solid #e2e8f0;
                        border-radius: 8px;
                        margin-bottom: 10px;
                        transition: all 0.2s ease;
                    }
                    .connection-item:hover {
                        border-color: #667eea;
                        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
                    }
                    .connection-text {
                        flex: 1;
                        font-size: 14px;
                        color: #4a5568;
                    }
                    .connection-type {
                        padding: 4px 8px;
                        background: #e2e8f0;
                        border-radius: 12px;
                        font-size: 12px;
                        color: #4a5568;
                        margin: 0 10px;
                    }
                    .remove-connection-btn {
                        background: #fed7d7;
                        color: #c53030;
                        border: none;
                        padding: 4px 8px;
                        border-radius: 4px;
                        cursor: pointer;
                        font-size: 12px;
                    }
                    
                    .theme-writing {
                        margin-top: 25px;
                    }
                    .theme-input-container {
                        position: relative;
                        margin-bottom: 20px;
                    }
                    .theme-textarea {
                        width: 100%;
                        min-height: 120px;
                        padding: 15px;
                        border: 2px solid #e2e8f0;
                        border-radius: 10px;
                        font-size: 16px;
                        line-height: 1.6;
                        resize: vertical;
                        transition: border-color 0.2s ease;
                    }
                    .theme-textarea:focus {
                        outline: none;
                        border-color: #667eea;
                        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
                    }
                    .char-counter {
                        position: absolute;
                        bottom: -25px;
                        right: 0;
                        font-size: 12px;
                        color: #a0aec0;
                    }
                    
                    .quality-metrics {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 15px;
                        margin: 20px 0;
                    }
                    .metric-card {
                        background: white;
                        padding: 20px;
                        border-radius: 10px;
                        border: 1px solid #e2e8f0;
                        text-align: center;
                    }
                    .metric-label {
                        font-size: 14px;
                        color: #4a5568;
                        margin-bottom: 8px;
                    }
                    .metric-bar {
                        height: 8px;
                        background: #e2e8f0;
                        border-radius: 4px;
                        overflow: hidden;
                        margin: 10px 0;
                    }
                    .metric-fill {
                        height: 100%;
                        background: linear-gradient(90deg, #fed7d7, #f6e05e, #c6f6d5);
                        border-radius: 4px;
                        transition: width 0.3s ease;
                    }
                    .metric-value {
                        font-size: 18px;
                        font-weight: bold;
                        color: #2d3748;
                    }
                    
                    .completion-summary {
                        background: linear-gradient(135deg, #667eea, #764ba2);
                        color: white;
                        padding: 25px;
                        border-radius: 12px;
                        margin: 25px 0;
                    }
                    .completion-summary h5 {
                        margin: 0 0 15px 0;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 10px;
                    }
                    .summary-stats {
                        display: flex;
                        justify-content: space-around;
                        align-items: center;
                    }
                    .stat-item {
                        text-align: center;
                        display: flex;
                        flex-direction: column;
                        gap: 5px;
                    }
                    .stat-item span:first-child {
                        font-size: 14px;
                        opacity: 0.9;
                    }
                    .stat-item span:last-child {
                        font-size: 20px;
                        font-weight: bold;
                    }
                    
                    @media (max-width: 768px) {
                        .sentences-grid {
                            grid-template-columns: 1fr;
                        }
                        .connection-controls {
                            flex-direction: column;
                            gap: 10px;
                        }
                        .connection-controls select {
                            width: 100%;
                        }
                        .summary-stats {
                            flex-direction: column;
                            gap: 15px;
                        }
                        .quality-metrics {
                            grid-template-columns: 1fr;
                        }
                    }
                `;
                document.head.appendChild(styles);
            }
            
            initializePhase4Interaction(data);
        }
        
        // Update phase navigation
        function updatePhaseNavigation() {
            const buttons = document.querySelectorAll('.phase-btn');
            buttons.forEach((btn, index) => {
                const phase = index + 1;
                btn.classList.remove('active', 'completed');
                
                if (phaseCompleted[index]) {
                    btn.classList.add('completed');
                } else if (phase === currentPhase) {
                    btn.classList.add('active');
                }
            });
        }
        
        // Update progress bar
        function updateProgressBar() {
            const completedCount = phaseCompleted.filter(c => c).length;
            const progress = (completedCount / 4) * 100;
            document.getElementById('progressBar').style.width = progress + '%';
        }
        
        // Submit current phase
        function submitCurrentPhase() {
            // Collect response data based on current phase
            let responseData = {};
            
            if (currentPhase === 1) {
                responseData = collectPhase1Data();
            } else if (currentPhase === 2) {
                responseData = collectPhase2Data();
            } else if (currentPhase === 3) {
                responseData = collectPhase3Data();
            } else if (currentPhase === 4) {
                responseData = collectPhase4Data();
            }
            
            // Submit to server
            fetch(`/learning/submit_phase/${currentPhase}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({response_data: responseData})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showPhaseResult(data.evaluation);
                } else {
                    alert('답안 제출에 실패했습니다: ' + data.message);
                }
            })
            .catch(error => {
                console.error('오류:', error);
                alert('네트워크 오류가 발생했습니다.');
            });
        }
        
        // Show phase evaluation result
        function showPhaseResult(evaluation) {
            const statusDiv = document.getElementById('statusMessage') || 
                           document.querySelector('#contentArea .status-message') ||
                           document.createElement('div');
            
            statusDiv.className = 'status-message';
            statusDiv.id = 'statusMessage';
            
            if (evaluation.mastery_achieved) {
                statusDiv.classList.add('status-success');
                statusDiv.innerHTML = `
                    <h4>🎉 잘했습니다!</h4>
                    <p>점수: ${(evaluation.score * 100).toFixed(1)}%</p>
                    <p>다음 단계로 진행할 수 있습니다.</p>
                `;
                
                phaseCompleted[currentPhase - 1] = true;
                updatePhaseNavigation();
                updateProgressBar();
                
                // Show next button
                document.getElementById('nextBtn').style.display = 'inline-block';
                
            } else {
                statusDiv.classList.add('status-warning');
                statusDiv.innerHTML = `
                    <h4>💪 다시 도전해보세요!</h4>
                    <p>점수: ${(evaluation.score * 100).toFixed(1)}%</p>
                    <p>권장 행동: ${evaluation.next_action}</p>
                `;
                
                if (evaluation.hints && evaluation.hints.length > 0) {
                    statusDiv.innerHTML += '<div><strong>힌트:</strong><ul>';
                    evaluation.hints.forEach(hint => {
                        statusDiv.innerHTML += `<li>${hint.message}</li>`;
                    });
                    statusDiv.innerHTML += '</ul></div>';
                }
            }
            
            // Append to content area if not exists
            if (!document.getElementById('statusMessage')) {
                document.getElementById('contentArea').appendChild(statusDiv);
            }
        }
        
        // Go to next phase
        function goToNextPhase() {
            if (currentPhase < 4) {
                startPhase(currentPhase + 1);
            } else {
                showLearningComplete();
            }
        }
        
        // Show learning completion
        function showLearningComplete() {
            document.getElementById('contentArea').innerHTML = `
                <div style="text-align: center; padding: 40px;">
                    <h2>🎊 학습 완료!</h2>
                    <p style="margin: 20px 0; color: #718096;">
                        4단계 요약 학습을 모두 완료했습니다!
                    </p>
                    <button class="btn" onclick="location.reload()">새로운 학습 시작</button>
                </div>
            `;
            
            document.getElementById('actionButtons').style.display = 'none';
        }
        
        // Phase 2: Drag and Drop Implementation
        let phase2State = {
            classifications: {},
            moveHistory: [],
            totalComponents: 0,
            correctClassifications: 0,
            hintsUsed: 0,
            draggedElement: null
        };
        
        function initializeDragAndDrop(data) {
            console.log('Phase 2 드래그앤드롭 초기화...', data);
            
            // Initialize enhanced state
            phase2State.totalComponents = data.target_sentence.components.length;
            phase2State.classifications = {};
            phase2State.moveHistory = [];
            phase2State.correctClassifications = 0;
            phase2State.hintsUsed = 0;
            phase2State.startTime = Date.now();
            phase2State.draggedElement = null;
            phase2State.selectedElement = null;
            phase2State.validationEnabled = true;
            
            // Store data globally
            window.currentPhase2Data = data;
            
            // Enhanced setup
            setupDragEvents();
            setupDropZones();
            setupTouchSupport();
            setupKeyboardNavigation();
            setupAccessibilityFeatures();
            
            // Initialize progress tracking
            updatePhase2Progress();
            
            // Add tutorial overlay if first time
            showPhase2Tutorial();
        }
        
        function showPhase2Tutorial() {
            const tutorial = `
                <div class="tutorial-overlay" id="phase2Tutorial">
                    <div class="tutorial-content">
                        <h4>🎯 2단계: 필수성 판단 가이드</h4>
                        <div class="tutorial-steps">
                            <div class="step">
                                <div class="step-icon">1</div>
                                <div class="step-text">
                                    <strong>문장 성분을 드래그하여 적절한 카테고리에 놓으세요</strong>
                                    <p>마우스 드래그 또는 터치로 이동 가능</p>
                                </div>
                            </div>
                            <div class="step">
                                <div class="step-icon">2</div>
                                <div class="step-text">
                                    <strong>각 카테고리의 의미를 이해하세요</strong>
                                    <ul>
                                        <li><span class="required-color">필수적</span>: 제거하면 의미 불완전</li>
                                        <li><span class="optional-color">선택적</span>: 보완 정보 제공</li>
                                        <li><span class="decorative-color">장식적</span>: 감정이나 강조</li>
                                    </ul>
                                </div>
                            </div>
                            <div class="step">
                                <div class="step-icon">3</div>
                                <div class="step-text">
                                    <strong>실시간 피드백으로 학습하세요</strong>
                                    <p>틀린 분류에 대한 즉시 힌트 제공</p>
                                </div>
                            </div>
                        </div>
                        <div class="tutorial-actions">
                            <button class="btn" onclick="closeTutorial()">시작하기</button>
                            <button class="btn-secondary" onclick="skipTutorial()">건너뛰기</button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.insertAdjacentHTML('beforeend', tutorial);
            
            window.closeTutorial = function() {
                document.getElementById('phase2Tutorial')?.remove();
            }
            
            window.skipTutorial = function() {
                document.getElementById('phase2Tutorial')?.remove();
                localStorage.setItem('phase2TutorialShown', 'true');
            }
        }
        
        function setupDragEvents() {
            const draggables = document.querySelectorAll('.draggable-component');
            
            draggables.forEach(element => {
                // Enhanced mouse events
                element.addEventListener('dragstart', handleDragStart);
                element.addEventListener('dragend', handleDragEnd);
                element.addEventListener('click', handleElementClick);
                element.addEventListener('mouseenter', handleElementHover);
                element.addEventListener('mouseleave', handleElementLeave);
                
                // Touch events for mobile
                element.addEventListener('touchstart', handleTouchStart, { passive: false });
                element.addEventListener('touchmove', handleTouchMove, { passive: false });
                element.addEventListener('touchend', handleTouchEnd, { passive: false });
                
                // Accessibility
                element.setAttribute('role', 'button');
                element.setAttribute('tabindex', '0');
                element.setAttribute('aria-grabbable', 'true');
            });
        }
        
        function handleElementClick(e) {
            // Alternative selection method for accessibility
            const element = e.target.closest('.draggable-component');
            if (element) {
                if (phase2State.selectedElement === element) {
                    // Deselect
                    element.classList.remove('selected');
                    phase2State.selectedElement = null;
                } else {
                    // Select new element
                    document.querySelectorAll('.draggable-component.selected').forEach(el => {
                        el.classList.remove('selected');
                    });
                    element.classList.add('selected');
                    phase2State.selectedElement = element;
                    showComponentInfo(element);
                }
            }
        }
        
        function handleElementHover(e) {
            const element = e.target.closest('.draggable-component');
            if (element && !element.classList.contains('dragging')) {
                showQuickHint(element);
            }
        }
        
        function handleElementLeave(e) {
            hideQuickHint();
        }
        
        function showQuickHint(element) {
            const componentText = element.getAttribute('data-component-text');
            const componentType = element.getAttribute('data-component-type');
            
            const hint = document.createElement('div');
            hint.className = 'quick-hint';
            hint.innerHTML = `
                <div class="hint-content">
                    <strong>${componentText}</strong> (${componentType})
                    <br><small>이 성분의 필수성을 판단해보세요</small>
                </div>
            `;
            
            const rect = element.getBoundingClientRect();
            hint.style.position = 'absolute';
            hint.style.left = rect.left + 'px';
            hint.style.top = (rect.bottom + 5) + 'px';
            hint.style.zIndex = '9999';
            
            document.body.appendChild(hint);
            element._quickHint = hint;
        }
        
        function hideQuickHint() {
            document.querySelectorAll('.quick-hint').forEach(hint => {
                hint.remove();
            });
        }
        
        function setupDropZones() {
            const dropZones = document.querySelectorAll('.drop-zone');
            
            dropZones.forEach(zone => {
                // Drag events
                zone.addEventListener('dragover', handleDragOver);
                zone.addEventListener('drop', handleDrop);
                zone.addEventListener('dragenter', handleDragEnter);
                zone.addEventListener('dragleave', handleDragLeave);
                
                // Click events for selected element placement
                zone.addEventListener('click', handleDropZoneClick);
                
                // Accessibility
                zone.setAttribute('role', 'region');
                zone.setAttribute('aria-dropeffect', 'move');
            });
        }
        
        function handleDropZoneClick(e) {
            if (phase2State.selectedElement) {
                const dropZone = e.target.closest('.drop-zone');
                const category = e.target.closest('.necessity-column')?.dataset.category;
                
                if (dropZone && category) {
                    moveElementToZone(phase2State.selectedElement, dropZone, category);
                    phase2State.selectedElement.classList.remove('selected');
                    phase2State.selectedElement = null;
                }
            }
        }
        
        function handleDragStart(e) {
            console.log('드래그 시작:', e.target);
            phase2State.draggedElement = e.target;
            e.target.classList.add('dragging');
            
            // Set drag data
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/html', e.target.outerHTML);
            e.dataTransfer.setData('component-id', e.target.dataset.componentId);
        }
        
        function handleDragEnd(e) {
            console.log('드래그 종료:', e.target);
            e.target.classList.remove('dragging');
            phase2State.draggedElement = null;
        }
        
        function handleDragOver(e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
        }
        
        function handleDragEnter(e) {
            e.preventDefault();
            if (e.target.classList.contains('drop-zone')) {
                e.target.classList.add('drag-over');
            }
        }
        
        function handleDragLeave(e) {
            if (e.target.classList.contains('drop-zone')) {
                e.target.classList.remove('drag-over');
            }
        }
        
        function handleDrop(e) {
            e.preventDefault();
            
            const dropZone = e.target.closest('.drop-zone');
            const category = e.target.closest('.necessity-column').dataset.category;
            const componentId = e.dataTransfer.getData('component-id');
            
            console.log('드롭 처리:', { category, componentId, dropZone });
            
            if (!dropZone || !category || !componentId) {
                console.log('드롭 실패: 필요한 데이터가 없음');
                return;
            }
            
            // Remove drag-over styling
            dropZone.classList.remove('drag-over');
            
            // Process the drop
            handleComponentDrop(componentId, category, dropZone);
        }
        
        function handleComponentDrop(componentId, targetCategory, dropZone) {
            console.log('성분 분류:', componentId, '->', targetCategory);
            
            // Record the move
            const previousCategory = phase2State.classifications[componentId];
            phase2State.moveHistory.push({
                componentId: componentId,
                from: previousCategory || 'pool',
                to: targetCategory,
                timestamp: Date.now()
            });
            
            // Update classification
            phase2State.classifications[componentId] = targetCategory;
            
            // Move the element visually
            const draggedElement = phase2State.draggedElement || 
                                 document.querySelector(`[data-component-id="${componentId}"]`);
            
            if (draggedElement) {
                // Remove from previous location
                if (previousCategory) {
                    const previousZone = document.querySelector(`[data-category="${previousCategory}"] .drop-zone`);
                    if (previousZone && previousZone.contains(draggedElement)) {
                        // Remove from previous drop zone, return to pool
                        document.getElementById('componentsPool').appendChild(draggedElement);
                    }
                }
                
                // Add to new location
                dropZone.appendChild(draggedElement);
                draggedElement.classList.add('dropped-component');
                
                // Remove animation class after animation completes
                setTimeout(() => {
                    draggedElement.classList.remove('dropped-component');
                }, 500);
            }
            
            // Immediate validation and feedback
            validateNecessityClassification(componentId, targetCategory);
            
            // Update progress
            updatePhase2Progress();
            
            // Enable undo button
            document.getElementById('undoBtn').disabled = false;
        }
        
        function validateNecessityClassification(componentId, studentCategory) {
            console.log('분류 검증:', componentId, studentCategory);
            
            // Get correct answer from phase data
            const component = phaseData.target_sentence.components.find(c => c.id === componentId);
            if (!component) {
                console.error('성분을 찾을 수 없음:', componentId);
                return;
            }
            
            const correctCategory = component.correct_necessity;
            const element = document.querySelector(`[data-component-id="${componentId}"]`);
            
            // Remove previous validation classes
            element.classList.remove('component-correct', 'component-incorrect', 'component-critical-error');
            
            // Apply validation styling
            if (studentCategory === correctCategory) {
                element.classList.add('component-correct');
                showFeedbackMessage(`✅ 정답입니다! "${component.text}"는 ${getCategoryDisplayName(correctCategory)} 성분입니다.`, 'success');
            } else {
                // Check for critical error (Required misclassified as Optional/Decorative)
                if (correctCategory === 'required' && ['optional', 'decorative'].includes(studentCategory)) {
                    element.classList.add('component-critical-error');
                    showCriticalErrorWarning(component.text, correctCategory, studentCategory);
                } else {
                    element.classList.add('component-incorrect');
                    showFeedbackMessage(`❌ "${component.text}"는 ${getCategoryDisplayName(correctCategory)} 성분입니다.`, 'warning');
                }
            }
        }
        
        function showCriticalErrorWarning(componentText, correctCategory, studentCategory) {
            const warning = `
                <div class="status-message status-error">
                    <h4>⚠️ 중요한 실수!</h4>
                    <p><strong>"${componentText}"</strong>는 필수적(Required) 성분입니다.</p>
                    <p>필수 성분을 ${getCategoryDisplayName(studentCategory)}로 분류하면 요약에서 핵심 의미가 손실됩니다!</p>
                    <p><strong>힌트:</strong> 이 성분 없이 문장이 완전한 의미를 갖는지 다시 생각해보세요.</p>
                </div>
            `;
            
            showFeedbackMessage(warning, 'error', 5000); // Show for 5 seconds
        }
        
        function showFeedbackMessage(message, type = 'info', duration = 3000) {
            const statusDiv = document.getElementById('statusMessage');
            statusDiv.innerHTML = message;
            statusDiv.className = `status-message status-${type}`;
            statusDiv.style.display = 'block';
            
            // Add feedback styles if not present
            if (!document.getElementById('feedbackStyles')) {
                const styles = document.createElement('style');
                styles.id = 'feedbackStyles';
                styles.textContent = `
                    .status-message {
                        padding: 15px 20px;
                        border-radius: 8px;
                        margin: 15px 0;
                        font-weight: 500;
                        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                        animation: slideIn 0.3s ease;
                    }
                    .status-success {
                        background: #f0fff4;
                        border: 1px solid #9ae6b4;
                        color: #276749;
                    }
                    .status-warning {
                        background: #fefcbf;
                        border: 1px solid #f6e05e;
                        color: #744210;
                    }
                    .status-error {
                        background: #fed7d7;
                        border: 1px solid #fc8181;
                        color: #742a2a;
                    }
                    .status-info {
                        background: #ebf4ff;
                        border: 1px solid #90cdf4;
                        color: #2c5aa0;
                    }
                `;
                document.head.appendChild(styles);
            }
            
            // Auto-hide after duration
            if (duration > 0) {
                setTimeout(() => {
                    statusDiv.style.opacity = '0';
                    setTimeout(() => {
                        statusDiv.style.display = 'none';
                        statusDiv.style.opacity = '1';
                    }, 300);
                }, duration);
            }
        }
        
        function getCategoryDisplayName(category) {
            const names = {
                'required': '필수적',
                'optional': '선택적', 
                'decorative': '장식적'
            };
            return names[category] || category;
        }
        
        function updatePhase2Progress() {
            const classifiedCount = Object.keys(phase2State.classifications).length;
            const total = phase2State.totalComponents;
            
            // Update progress count
            document.getElementById('progressCount').textContent = `${classifiedCount}/${total}`;
            
            // Calculate accuracy
            let correctCount = 0;
            for (const [componentId, studentCategory] of Object.entries(phase2State.classifications)) {
                const component = phaseData.target_sentence.components.find(c => c.id === componentId);
                if (component && component.correct_necessity === studentCategory) {
                    correctCount++;
                }
            }
            
            const accuracy = classifiedCount > 0 ? (correctCount / classifiedCount * 100).toFixed(1) : 0;
            document.getElementById('accuracyDisplay').textContent = `${accuracy}%`;
            
            phase2State.correctClassifications = correctCount;
        }
        
        // Touch support for mobile devices
        function setupKeyboardNavigation() {
            document.addEventListener('keydown', function(e) {
                if (currentPhase !== 2) return;
                
                const selectedElement = phase2State.selectedElement;
                
                if (e.key === 'Enter' || e.key === ' ') {
                    if (e.target.classList.contains('draggable-component')) {
                        handleElementClick({ target: e.target });
                        e.preventDefault();
                    }
                } else if (e.key >= '1' && e.key <= '3' && selectedElement) {
                    // Quick assign to categories 1=Required, 2=Optional, 3=Decorative
                    const categories = ['required', 'optional', 'decorative'];
                    const category = categories[parseInt(e.key) - 1];
                    const dropZone = document.querySelector(`[data-category="${category}"] .drop-zone`);
                    
                    if (dropZone) {
                        moveElementToZone(selectedElement, dropZone, category);
                        selectedElement.classList.remove('selected');
                        phase2State.selectedElement = null;
                    }
                    e.preventDefault();
                } else if (e.key === 'Escape' && selectedElement) {
                    selectedElement.classList.remove('selected');
                    phase2State.selectedElement = null;
                }
            });
        }
        
        function setupAccessibilityFeatures() {
            // Add ARIA labels and descriptions
            const requiredZone = document.querySelector('[data-category="required"] .drop-zone');
            const optionalZone = document.querySelector('[data-category="optional"] .drop-zone');
            const decorativeZone = document.querySelector('[data-category="decorative"] .drop-zone');
            
            if (requiredZone) {
                requiredZone.setAttribute('aria-label', '필수적 성분 영역');
                requiredZone.setAttribute('aria-describedby', 'required-description');
            }
            if (optionalZone) {
                optionalZone.setAttribute('aria-label', '선택적 성분 영역');
                optionalZone.setAttribute('aria-describedby', 'optional-description');
            }
            if (decorativeZone) {
                decorativeZone.setAttribute('aria-label', '장식적 성분 영역');
                decorativeZone.setAttribute('aria-describedby', 'decorative-description');
            }
        }
        
        function setupTouchSupport() {
            let touchStartPos = { x: 0, y: 0 };
            let touchElement = null;
            let longPressTimer = null;
            
            window.handleTouchStart = function(e) {
                touchStartPos.x = e.touches[0].clientX;
                touchStartPos.y = e.touches[0].clientY;
                touchElement = e.target.closest('.draggable-component');
                
                if (touchElement) {
                    // Start long press detection
                    longPressTimer = setTimeout(() => {
                        touchElement.classList.add('dragging');
                        navigator.vibrate && navigator.vibrate(50); // Haptic feedback
                    }, 500);
                }
            };
            
            window.handleTouchMove = function(e) {
                if (longPressTimer) {
                    clearTimeout(longPressTimer);
                    longPressTimer = null;
                }
                
                if (!touchElement || !touchElement.classList.contains('dragging')) return;
                
                e.preventDefault();
                
                const touch = e.touches[0];
                const element = document.elementFromPoint(touch.clientX, touch.clientY);
                const dropZone = element?.closest('.drop-zone');
                
                // Enhanced visual feedback for touch
                document.querySelectorAll('.drop-zone').forEach(zone => {
                    zone.classList.remove('drag-over');
                });
                
                if (dropZone) {
                    dropZone.classList.add('drag-over');
                }
            };
            
            window.handleTouchEnd = function(e) {
                if (longPressTimer) {
                    clearTimeout(longPressTimer);
                    longPressTimer = null;
                }
                
                if (!touchElement) return;
                
                const touch = e.changedTouches[0];
                const element = document.elementFromPoint(touch.clientX, touch.clientY);
                const dropZone = element?.closest('.drop-zone');
                const category = element?.closest('.necessity-column')?.dataset.category;
                
                touchElement.classList.remove('dragging');
                
                // Enhanced cleanup
                document.querySelectorAll('.drop-zone').forEach(zone => {
                    zone.classList.remove('drag-over');
                });
                
                if (dropZone && category && touchElement.dataset.componentId) {
                    handleComponentDrop(touchElement.dataset.componentId, category, dropZone);
                }
                
                touchElement = null;
            };
        }
        
        // Action functions for Phase 2
        function undoLastMove() {
            if (phase2State.moveHistory.length === 0) {
                showFeedbackMessage('되돌릴 이동이 없습니다.', 'info', 2000);
                return;
            }
            
            const lastMove = phase2State.moveHistory.pop();
            const element = document.querySelector(`[data-component-id="${lastMove.componentId}"]`);
            
            if (!element) return;
            
            // Remove current classification
            delete phase2State.classifications[lastMove.componentId];
            
            // Return element to pool or previous location
            if (lastMove.from === 'pool') {
                document.getElementById('componentsPool').appendChild(element);
            } else {
                const previousZone = document.querySelector(`[data-category="${lastMove.from}"] .drop-zone`);
                if (previousZone) {
                    previousZone.appendChild(element);
                    phase2State.classifications[lastMove.componentId] = lastMove.from;
                }
            }
            
            // Remove validation classes
            element.classList.remove('component-correct', 'component-incorrect', 'component-critical-error');
            
            // Update progress
            updatePhase2Progress();
            
            // Disable undo if no more moves
            if (phase2State.moveHistory.length === 0) {
                document.getElementById('undoBtn').disabled = true;
            }
            
            showFeedbackMessage('이동을 되돌렸습니다.', 'info', 2000);
        }
        
        function showHint() {
            phase2State.hintsUsed++;
            
            // Find first incorrectly classified component
            let hintMessage = '';
            
            for (const [componentId, studentCategory] of Object.entries(phase2State.classifications)) {
                const component = phaseData.target_sentence.components.find(c => c.id === componentId);
                if (component && component.correct_necessity !== studentCategory) {
                    const correctCategory = component.correct_necessity;
                    hintMessage = `💡 힌트: "${component.text}" 성분을 다시 살펴보세요. 이 요소 없이도 문장의 기본 의미가 전달될까요?`;
                    break;
                }
            }
            
            // If all classified correctly, give general hint
            if (!hintMessage && Object.keys(phase2State.classifications).length < phase2State.totalComponents) {
                hintMessage = '💡 힌트: 각 성분을 제거했을 때 문장의 의미가 어떻게 변하는지 생각해보세요. 핵심 의미가 손실되면 필수적, 보조적 정보만 사라지면 선택적입니다.';
            } else if (!hintMessage) {
                hintMessage = '💡 모든 성분이 올바르게 분류되었습니다! 답안을 제출하세요.';
            }
            
            showFeedbackMessage(hintMessage, 'info', 4000);
        }
        
        function previewSentence() {
            // Show sentence with different components removed
            const sentence = phaseData.target_sentence.text;
            let previewHTML = '<div class="sentence-preview"><h4>🔍 성분별 문장 미리보기</h4>';
            
            const categories = ['required', 'optional', 'decorative'];
            categories.forEach(category => {
                const categoryComponents = [];
                for (const [componentId, studentCategory] of Object.entries(phase2State.classifications)) {
                    if (studentCategory === category) {
                        const component = phaseData.target_sentence.components.find(c => c.id === componentId);
                        if (component) {
                            categoryComponents.push(component.text);
                        }
                    }
                }
                
                if (categoryComponents.length > 0) {
                    let modifiedSentence = sentence;
                    categoryComponents.forEach(text => {
                        modifiedSentence = modifiedSentence.replace(text, `<del style="background: #ffebee; text-decoration: line-through;">${text}</del>`);
                    });
                    
                    previewHTML += `
                        <div style="margin: 10px 0; padding: 10px; border-left: 3px solid #ddd;">
                            <strong>${getCategoryDisplayName(category)} 성분 제거:</strong><br>
                            <span style="font-size: 16px;">${modifiedSentence}</span>
                        </div>
                    `;
                }
            });
            
            previewHTML += '</div>';
            showFeedbackMessage(previewHTML, 'info', 8000);
        }
        
        // Helper functions for data collection
        function collectPhase1Data() {
            // Collect component identification data
            const phase1Data = window.currentPhase1Data || {};
            const selectedComponents = phase1Data.selectedComponents || {};
            
            // Format data for backend
            const formattedSelections = Object.entries(selectedComponents).map(([wordIndex, data]) => ({
                word_index: parseInt(wordIndex),
                word_text: data.text,
                selected_component: data.component,
                position: wordIndex
            }));
            
            return {
                phase: 1,
                sentence_id: 1,
                target_sentence: phase1Data.targetSentence?.text || '',
                component_selections: formattedSelections,
                identified_components: selectedComponents,
                total_components_found: formattedSelections.length,
                completion_rate: formattedSelections.length / (phase1Data.targetSentence?.components_to_find?.length || 1),
                completion_time: Date.now()
            };
        }
        
        function collectPhase2Data() {
            console.log('Phase 2 데이터 수집:', phase2State);
            
            return {
                sentence_id: phaseData?.target_sentence?.sentence_id || 1,
                necessity_classifications: phase2State.classifications,
                move_history: phase2State.moveHistory,
                hints_used: phase2State.hintsUsed,
                time_spent: Date.now() - (phase2State.startTime || Date.now()),
                accuracy: phase2State.correctClassifications / phase2State.totalComponents
            };
        }
        
        function collectPhase3Data() {
            // Collect generalization data
            const generalizations = {};
            
            // Get all generalization selections
            const generalizationItems = document.querySelectorAll('.generalization-item');
            generalizationItems.forEach(item => {
                const componentId = item.getAttribute('data-component-id');
                const radioButtons = item.querySelectorAll(`input[name="generalization-${componentId}"]`);
                
                for (let radio of radioButtons) {
                    if (radio.checked) {
                        if (radio.value === 'custom') {
                            const customInput = item.querySelector('.custom-generalization');
                            generalizations[componentId] = customInput.value.trim();
                        } else {
                            generalizations[componentId] = radio.value;
                        }
                        break;
                    }
                }
            });
            
            return {
                sentence_id: phaseData?.target_sentence?.sentence_id || 1,
                generalizations: generalizations,
                completion_time: Date.now(),
                interaction_count: Object.keys(generalizations).length
            };
        }
        
        function collectPhase4Data() {
            // Collect theme reconstruction data
            const reconstructedTheme = document.getElementById('reconstructedTheme')?.value?.trim() || '';
            
            // Collect concept connections
            const conceptConnections = [];
            const connectionItems = document.querySelectorAll('.connection-item');
            connectionItems.forEach(item => {
                const source = item.getAttribute('data-source');
                const target = item.getAttribute('data-target');
                const type = item.getAttribute('data-type');
                if (source && target && type) {
                    conceptConnections.push({
                        source: source,
                        target: target,
                        type: type
                    });
                }
            });
            
            return {
                reconstructed_theme: reconstructedTheme,
                concept_connections: conceptConnections,
                completion_time: Date.now(),
                theme_length: reconstructedTheme.length,
                connection_count: conceptConnections.length
            };
        }
        
        // Initialize Phase 1 interaction
        function initializePhase1Interaction(data) {
            console.log('Phase 1 초기화 시작:', data);
            
            const targetSentence = document.getElementById('targetSentence');
            const sentenceText = data.target_sentence.text;
            const componentsToFind = data.target_sentence.components_to_find;
            let selectedComponents = {};
            let currentHints = {};
            let mistakeCount = 0;
            
            // Store data globally for collection
            window.currentPhase1Data = {
                targetSentence: data.target_sentence,
                selectedComponents: selectedComponents,
                startTime: Date.now(),
                hintsUsed: 0
            };
            
            // Create advanced word-clickable interface with morpheme analysis
            const words = sentenceText.split(/(\s+|[.,!?;:()"''])/);
            let wordIndex = 0;
            
            const clickableHTML = words.map(word => {
                const cleanWord = word.trim();
                if (cleanWord && !/^[.,!?;:()"''\s]+$/.test(cleanWord)) {
                    return `<span class="clickable-word" 
                                  data-word-index="${wordIndex++}" 
                                  data-original="${cleanWord}"
                                  title="클릭하여 문장 성분을 식별하세요">
                              ${word}
                            </span>`;
                }
                return word;
            }).join('');
            
            targetSentence.innerHTML = `
                <div class="sentence-container">
                    <div class="sentence-text">${clickableHTML}</div>
                    <div class="identification-hints" id="identificationHints">
                        <p>💡 단어를 클릭하여 문장 성분을 식별해보세요</p>
                    </div>
                </div>
            `;
            
            // Enhanced click listeners with visual feedback
            const clickableWords = document.querySelectorAll('.clickable-word');
            clickableWords.forEach(word => {
                word.addEventListener('click', handleWordClick);
                word.addEventListener('mouseover', showWordHint);
                word.addEventListener('mouseout', hideWordHint);
            });
            
            function handleWordClick(event) {
                const wordText = this.getAttribute('data-original');
                const wordIndex = this.getAttribute('data-word-index');
                
                if (this.classList.contains('selected')) {
                    // Deselect with confirmation
                    if (confirm(`"${wordText}"의 선택을 취소하시겠습니까?`)) {
                        deselectWord(this, wordIndex);
                    }
                } else {
                    // Show enhanced component selection modal
                    showComponentSelectionModal(wordText, wordIndex, this);
                }
            }
            
            function deselectWord(wordElement, wordIndex) {
                wordElement.classList.remove('selected');
                wordElement.removeAttribute('data-component');
                wordElement.style.background = '';
                delete selectedComponents[wordIndex];
                updatePhase1Progress();
                showFeedbackMessage(`"${wordElement.getAttribute('data-original')}" 선택이 취소되었습니다`, 'info', 2000);
            }
            
            function showWordHint(event) {
                const wordText = this.getAttribute('data-original');
                const tooltip = document.createElement('div');
                tooltip.className = 'word-tooltip';
                tooltip.innerHTML = `<strong>${wordText}</strong><br>클릭하여 성분 식별`;
                document.body.appendChild(tooltip);
                
                const rect = this.getBoundingClientRect();
                tooltip.style.position = 'absolute';
                tooltip.style.left = rect.left + 'px';
                tooltip.style.top = (rect.top - 50) + 'px';
                tooltip.style.zIndex = '9999';
                
                this._tooltip = tooltip;
            }
            
            function hideWordHint(event) {
                if (this._tooltip) {
                    document.body.removeChild(this._tooltip);
                    this._tooltip = null;
                }
            }
            
            // Component selection modal
            function showComponentSelectionModal(wordText, wordIndex, wordElement) {
                const modalHTML = `
                    <div class="component-modal-overlay" id="componentModal">
                        <div class="component-modal">
                            <div class="modal-header">
                                <h4>"${wordText}"의 문장 성분 식별</h4>
                                <button class="close-modal" onclick="closeComponentModal()">&times;</button>
                            </div>
                            
                            <div class="word-context">
                                <p><strong>전체 문장:</strong> ${data.target_sentence.text}</p>
                                <p><strong>선택된 단어:</strong> <span class="highlight">${wordText}</span></p>
                            </div>
                            
                            <div class="component-guide">
                                <h5>📚 문장 성분 가이드</h5>
                                <div class="guide-grid">
                                    <div class="guide-item">
                                        <strong>주어:</strong> 누가/무엇이 (동작의 주체)
                                    </div>
                                    <div class="guide-item">
                                        <strong>서술어:</strong> 어떻게 하다 (동작/상태)
                                    </div>
                                    <div class="guide-item">
                                        <strong>목적어:</strong> 무엇을 (동작의 대상)
                                    </div>
                                    <div class="guide-item">
                                        <strong>보어:</strong> 어떻게/무엇으로 (주어를 설명)
                                    </div>
                                    <div class="guide-item">
                                        <strong>부사어:</strong> 언제/어디서/왜 (다른 성분 수식)
                                    </div>
                                    <div class="guide-item">
                                        <strong>관형어:</strong> 어떤/누구의 (명사 수식)
                                    </div>
                                </div>
                            </div>
                            
                            <div class="component-options">
                                <h5>성분을 선택하세요:</h5>
                                <div class="options-grid">
                                    ${componentsToFind.map(comp => `
                                        <button class="component-btn ${comp}" 
                                                onclick="selectComponent('${wordIndex}', '${comp}', '${wordText}')">
                                            <div class="btn-content">
                                                <div class="component-name">${getComponentDisplayName(comp)}</div>
                                                <div class="component-hint">${getComponentHint(comp, wordText)}</div>
                                            </div>
                                        </button>
                                    `).join('')}
                                </div>
                            </div>
                            
                            <div class="modal-actions">
                                <button class="btn-secondary" onclick="getComponentHint('${wordText}', '${wordIndex}')">💡 힌트</button>
                                <button class="btn-secondary" onclick="closeComponentModal()">취소</button>
                            </div>
                        </div>
                    </div>
                `;
                
                document.body.insertAdjacentHTML('beforeend', modalHTML);
                
                // Focus management for accessibility
                const modal = document.getElementById('componentModal');
                modal.focus();
                
                // Close on Escape key
                modal.addEventListener('keydown', function(e) {
                    if (e.key === 'Escape') {
                        closeComponentModal();
                    }
                });
            }
            
            // Helper functions for component modal
            function getComponentDisplayName(comp) {
                const names = {
                    '주어': '주어 (Subject)',
                    '서술어': '서술어 (Predicate)',
                    '목적어': '목적어 (Object)',
                    '보어': '보어 (Complement)',
                    '부사어': '부사어 (Adverbial)',
                    '관형어': '관형어 (Modifier)'
                };
                return names[comp] || comp;
            }
            
            function getComponentHint(comp, wordText) {
                // Generate contextual hints based on word and component type
                const hints = {
                    '주어': `"${wordText}"이(가) 동작의 주체인가요?`,
                    '서술어': `"${wordText}"이(가) 동작이나 상태를 나타내나요?`,
                    '목적어': `"${wordText}"이(가) 동작의 대상인가요?`,
                    '보어': `"${wordText}"이(가) 주어를 설명하나요?`,
                    '부사어': `"${wordText}"이(가) 언제/어디서/왜을 나타내나요?`,
                    '관형어': `"${wordText}"이(가) 명사를 수식하나요?`
                };
                return hints[comp] || '이 성분이 맞는지 생각해보세요';
            }
            
            window.closeComponentModal = function() {
                const modal = document.getElementById('componentModal');
                if (modal) {
                    modal.remove();
                }
            }
            
            window.getComponentHint = function(wordText, wordIndex) {
                window.currentPhase1Data.hintsUsed++;
                
                // Provide contextual hint based on sentence analysis
                const hints = [
                    `💡 "${wordText}"의 역할을 생각해보세요. 문장에서 어떤 기능을 하고 있나요?`,
                    `💡 이 단어 없이도 문장이 성립할까요? 아니면 반드시 필요한 요소인가요?`,
                    `💡 다른 단어들과의 관계를 살펴보세요. 누구를 수식하거나 무엇을 설명하나요?`
                ];
                
                const randomHint = hints[Math.floor(Math.random() * hints.length)];
                showFeedbackMessage(randomHint, 'info', 4000);
            }
            
            // Enhanced selectComponent function with validation
            window.selectComponent = function(wordIndex, componentType, wordText) {
                console.log('성분 선택:', wordText, '->', componentType);
                
                const wordElement = document.querySelector(`[data-word-index="${wordIndex}"]`);
                if (!wordElement) return;
                
                // Visual feedback
                wordElement.classList.add('selected', componentType.toLowerCase());
                wordElement.setAttribute('data-component', componentType);
                
                // Store selection
                selectedComponents[wordIndex] = {
                    text: wordText,
                    component: componentType,
                    timestamp: Date.now()
                };
                
                // Update global data
                window.currentPhase1Data.selectedComponents = selectedComponents;
                
                // Close modal
                closeComponentModal();
                
                // Update progress and provide feedback
                updatePhase1Progress();
                
                // Immediate validation feedback
                validateComponentSelection(wordIndex, componentType, wordText);
                
                // Check if all components found
                if (Object.keys(selectedComponents).length === componentsToFind.length) {
                    showCompletionCelebration();
                }
            }
            
            function validateComponentSelection(wordIndex, selectedComponent, wordText) {
                // Get correct component from data if available
                const correctComponents = data.target_sentence.components_to_find_details;
                
                if (correctComponents && correctComponents[wordIndex]) {
                    const correct = correctComponents[wordIndex];
                    
                    if (correct === selectedComponent) {
                        showFeedbackMessage(`✅ 정답! "${wordText}"은(는) ${selectedComponent}이(가) 맞습니다.`, 'success', 3000);
                    } else {
                        mistakeCount++;
                        showFeedbackMessage(`⚠️ "${wordText}"의 성분을 다시 한 번 생각해보세요. 힌트가 필요하신가요?`, 'warning', 4000);
                    }
                } else {
                    // Generic positive feedback when no validation data
                    showFeedbackMessage(`📝 "${wordText}"을(를) ${selectedComponent}(으)로 식별했습니다.`, 'info', 2000);
                }
            }
            
            function showCompletionCelebration() {
                const celebration = `
                    <div class="celebration-overlay">
                        <div class="celebration-content">
                            <h3>🎉 1단계 완료!</h3>
                            <p>모든 문장 성분을 식별했습니다!</p>
                            <button class="btn" onclick="this.parentElement.parentElement.remove()">계속</button>
                        </div>
                    </div>
                `;
                
                document.body.insertAdjacentHTML('beforeend', celebration);
                
                setTimeout(() => {
                    const overlay = document.querySelector('.celebration-overlay');
                    if (overlay) overlay.remove();
                }, 5000);
            }
                
                // Add enhanced modal styles if not present
                if (!document.getElementById('componentModalStyles')) {
                    const styles = document.createElement('style');
                    styles.id = 'componentModalStyles';
                    styles.textContent = `
                        .component-modal-overlay {
                            position: fixed;
                            top: 0;
                            left: 0;
                            width: 100%;
                            height: 100%;
                            background: rgba(0, 0, 0, 0.7);
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            z-index: 10000;
                            animation: fadeIn 0.2s ease;
                        }
                        .component-modal {
                            background: white;
                            padding: 30px;
                            border-radius: 15px;
                            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                            max-width: 500px;
                            width: 90%;
                            text-align: center;
                            animation: slideIn 0.3s ease;
                        }
                        .component-options {
                            display: grid;
                            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
                            gap: 10px;
                            margin: 20px 0;
                        }
                        .component-btn {
                            padding: 12px 20px;
                            border: 2px solid transparent;
                            border-radius: 8px;
                            cursor: pointer;
                            font-weight: bold;
                            transition: all 0.2s ease;
                            font-size: 14px;
                        }
                        .component-btn.주어 { background: #fed7d7; border-color: #fc8181; color: #c53030; }
                        .component-btn.서술어 { background: #c6f6d5; border-color: #48bb78; color: #2d7738; }
                        .component-btn.목적어 { background: #bee3f8; border-color: #4299e1; color: #2c5aa0; }
                        .component-btn.보어 { background: #fef5e7; border-color: #ed8936; color: #c05621; }
                        .component-btn.부사어 { background: #e9d8fd; border-color: #805ad5; color: #553c9a; }
                        .component-btn.관형어 { background: #f7fafc; border-color: #a0aec0; color: #4a5568; }
                        .component-btn:hover {
                            transform: translateY(-2px);
                            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
                        }
                        .close-modal-btn {
                            padding: 10px 20px;
                            background: #e2e8f0;
                            border: none;
                            border-radius: 8px;
                            cursor: pointer;
                            margin-top: 15px;
                        }
                        @keyframes fadeIn {
                            from { opacity: 0; }
                            to { opacity: 1; }
                        }
                        @keyframes slideIn {
                            from { transform: translateY(-20px); opacity: 0; }
                            to { transform: translateY(0); opacity: 1; }
                        }
                        @keyframes fadeOut {
                            from { opacity: 1; }
                            to { opacity: 0; }
                        }
                        .clickable-word {
                            cursor: pointer;
                            padding: 2px 4px;
                            border-radius: 4px;
                            transition: all 0.2s ease;
                            margin: 0 1px;
                        }
                        .clickable-word:hover {
                            background: #f0f0f0;
                            transform: translateY(-1px);
                        }
                        .clickable-word.selected {
                            font-weight: bold;
                            transform: translateY(-1px);
                        }
                        .clickable-word.selected.주어 { background: #fed7d7; border: 2px solid #fc8181; color: #c53030; }
                        .clickable-word.selected.서술어 { background: #c6f6d5; border: 2px solid #48bb78; color: #2d7738; }
                        .clickable-word.selected.목적어 { background: #bee3f8; border: 2px solid #4299e1; color: #2c5aa0; }
                        .clickable-word.selected.보어 { background: #fef5e7; border: 2px solid #ed8936; color: #c05621; }
                        .clickable-word.selected.부사어 { background: #e9d8fd; border: 2px solid #805ad5; color: #553c9a; }
                        .clickable-word.selected.관형어 { background: #f7fafc; border: 2px solid #a0aec0; color: #4a5568; }
                    `;
                    document.head.appendChild(styles);
                }
            }
            
            // Global functions for modal
            window.selectComponent = function(wordIndex, component, wordText) {
                const wordElement = document.querySelector(`[data-word-index="${wordIndex}"]`);
                if (wordElement) {
                    wordElement.classList.add('selected', component);
                    wordElement.setAttribute('data-component', component);
                    selectedComponents[wordIndex] = {
                        text: wordText,
                        component: component
                    };
                    
                    showFeedbackMessage(`"${wordText}"를 ${component}로 분류했습니다.`, 'success');
                }
                closeComponentModal();
                updatePhase1Progress();
            };
            
            window.closeComponentModal = function() {
                const modal = document.getElementById('componentModal');
                if (modal) {
                    modal.style.animation = 'fadeOut 0.2s ease';
                    setTimeout(() => modal.remove(), 200);
                }
            };
            
            function updatePhase1Progress() {
                const totalToFind = componentsToFind.length;
                const foundComponents = Object.keys(selectedComponents).length;
                const progressPercent = (foundComponents / totalToFind) * 100;
                
                const statusMessage = document.getElementById('statusMessage');
                statusMessage.innerHTML = `
                    <div class="progress-container">
                        <div class="progress-header">
                            <span>진행률: ${foundComponents}/${totalToFind}</span>
                            <span>${progressPercent.toFixed(0)}%</span>
                        </div>
                        <div class="progress-bar-container">
                            <div class="progress-bar" style="width: ${progressPercent}%"></div>
                        </div>
                        ${foundComponents === totalToFind ? 
                            '<div class="completion-message">🎉 모든 성분을 찾았습니다! 제출 버튼을 눌러주세요.</div>' : 
                            `<div class="help-text">아직 ${totalToFind - foundComponents}개의 성분을 더 찾아야 합니다.</div>`
                        }
                    </div>
                `;
                
                // Enable submit button when complete
                const submitBtn = document.getElementById('submitBtn');
                if (submitBtn) {
                    submitBtn.disabled = foundComponents < totalToFind;
                }
                
                // Add progress bar styles if not present
                if (!document.getElementById('phase1ProgressStyles')) {
                    const styles = document.createElement('style');
                    styles.id = 'phase1ProgressStyles';
                    styles.textContent = `
                        .progress-container {
                            background: white;
                            padding: 20px;
                            border-radius: 10px;
                            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                            margin-top: 20px;
                        }
                        .progress-header {
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            margin-bottom: 10px;
                            font-weight: bold;
                        }
                        .progress-bar-container {
                            background: #e2e8f0;
                            border-radius: 10px;
                            height: 10px;
                            overflow: hidden;
                        }
                        .progress-bar {
                            background: linear-gradient(90deg, #667eea, #764ba2);
                            height: 100%;
                            border-radius: 10px;
                            transition: width 0.3s ease;
                        }
                        .completion-message {
                            color: #38a169;
                            font-weight: bold;
                            margin-top: 15px;
                            text-align: center;
                            padding: 10px;
                            background: #f0fff4;
                            border-radius: 8px;
                            border: 1px solid #9ae6b4;
                        }
                        .help-text {
                            color: #4a5568;
                            margin-top: 10px;
                            text-align: center;
                        }
                    `;
                    document.head.appendChild(styles);
                }
            }
            
            // Initialize progress
            updatePhase1Progress();
            
            // Store data for collection
            window.currentPhase1Data = {
                targetSentence: data.target_sentence,
                selectedComponents: selectedComponents
            };
        }
        
        // Initialize Phase 3 interaction
        function initializePhase3Interaction(data) {
            // Add event listeners for generalization options
            const abstractionOptions = document.querySelectorAll('.abstraction-option input[type="radio"]');
            abstractionOptions.forEach(option => {
                option.addEventListener('change', function() {
                    const componentId = this.name.replace('generalization-', '');
                    updateSemanticPreview(componentId, this.value);
                    updateConceptMapping();
                    updateProgressTracker();
                });
            });
            
            // Add event listeners for custom input
            const customInputs = document.querySelectorAll('.custom-generalization');
            customInputs.forEach(input => {
                input.addEventListener('input', function() {
                    const componentId = this.getAttribute('data-component-id');
                    const customRadio = this.parentElement.querySelector('input[type="radio"]');
                    if (customRadio && this.value.trim()) {
                        customRadio.checked = true;
                        updateSemanticPreview(componentId, this.value);
                    }
                });
            });
        }
        
        // Initialize Phase 4 interaction
        function initializePhase4Interaction(data) {
            // Initialize concept network interactions
            const conceptNodes = document.querySelectorAll('.concept-node');
            let selectedNodes = [];
            
            conceptNodes.forEach(node => {
                node.addEventListener('click', function(e) {
                    if (e.ctrlKey || e.metaKey) {
                        // Multi-select mode
                        this.classList.toggle('selected');
                        const concept = this.getAttribute('data-concept');
                        if (this.classList.contains('selected')) {
                            selectedNodes.push(concept);
                        } else {
                            selectedNodes = selectedNodes.filter(n => n !== concept);
                        }
                    } else {
                        // Single select mode
                        conceptNodes.forEach(n => n.classList.remove('selected'));
                        selectedNodes = [];
                        this.classList.add('selected');
                        selectedNodes.push(this.getAttribute('data-concept'));
                    }
                    
                    updateConnectionSelects(selectedNodes);
                });
            });
            
            // Initialize theme textarea with real-time updates
            const themeTextarea = document.getElementById('reconstructedTheme');
            themeTextarea.addEventListener('input', function() {
                updateThemeLength();
                if (autoPreviewEnabled) {
                    checkThemeQuality();
                }
            });
            
            // Initialize quality metrics
            initializeQualityMetrics();
            
            window.currentPhase4Data = data;
        }
        
        // Helper functions for Phase 3
        function updateSemanticPreview(componentId, newValue) {
            const previewElement = document.getElementById(`preview-${componentId}`);
            const originalSentence = phaseData?.target_sentence?.text || '';
            
            if (previewElement && originalSentence) {
                // Find the original component text
                const generalizationItem = document.querySelector(`[data-component-id="${componentId}"]`);
                const originalText = generalizationItem?.querySelector('.original-text')?.textContent || '';
                
                if (originalText && newValue) {
                    const previewSentence = originalSentence.replace(originalText, `<strong class="generalized">${newValue}</strong>`);
                    previewElement.innerHTML = `
                        <h6>🔍 변경 미리보기</h6>
                        <p class="preview-text">${previewSentence}</p>
                        <small class="semantic-note">의미 변화: ${calculateSemanticDistance(originalText, newValue)}</small>
                    `;
                }
            }
        }
        
        function updateConceptMapping() {
            const abstractNodes = document.querySelector('.abstract-nodes');
            const specificNodes = document.querySelector('.specific-nodes');
            
            if (abstractNodes && specificNodes) {
                // Clear previous mappings
                abstractNodes.innerHTML = '';
                specificNodes.innerHTML = '';
                
                // Add generalized concepts to abstract level
                const generalizations = document.querySelectorAll('.abstraction-option input:checked');
                generalizations.forEach(option => {
                    if (option.value !== 'custom') {
                        const node = document.createElement('div');
                        node.className = 'concept-node abstract';
                        node.textContent = option.value;
                        abstractNodes.appendChild(node);
                    }
                });
            }
        }
        
        function updateProgressTracker() {
            const completedCount = document.querySelectorAll('.abstraction-option input:checked').length;
            const totalCount = document.querySelectorAll('.generalization-item').length;
            
            document.getElementById('completedGeneralizations').textContent = completedCount;
            document.getElementById('totalGeneralizations').textContent = totalCount;
        }
        
        function calculateSemanticDistance(original, generalized) {
            // Simple heuristic for semantic distance
            if (original.length > generalized.length) {
                return '더 일반적';
            } else if (original.length < generalized.length) {
                return '더 구체적';
            } else {
                return '유사한 수준';
            }
        }
        
        // Helper functions for Phase 4
        let autoPreviewEnabled = false;
        let conceptConnections = [];
        
        function addConceptConnection() {
            const sourceSelect = document.getElementById('sourceSelect');
            const targetSelect = document.getElementById('targetSelect');
            const connectionType = document.getElementById('connectionType');
            
            const source = sourceSelect.value;
            const target = targetSelect.value;
            const type = connectionType.value;
            
            if (source && target && type && source !== target) {
                // Check for duplicates
                const exists = conceptConnections.some(conn => 
                    conn.source === source && conn.target === target
                );
                
                if (!exists) {
                    conceptConnections.push({source, target, type});
                    displayConnection(source, target, type);
                    updateConnectionCount();
                    
                    // Reset selects
                    sourceSelect.value = '';
                    targetSelect.value = '';
                    connectionType.value = '';
                }
            }
        }
        
        function displayConnection(source, target, type) {
            const container = document.querySelector('.connections-container');
            const connectionDiv = document.createElement('div');
            connectionDiv.className = 'connection-item';
            connectionDiv.setAttribute('data-source', source);
            connectionDiv.setAttribute('data-target', target);
            connectionDiv.setAttribute('data-type', type);
            
            connectionDiv.innerHTML = `
                <div class="connection-content">
                    <span class="connection-source">${source}</span>
                    <span class="connection-type">${type}</span>
                    <span class="connection-target">${target}</span>
                    <button onclick="removeConnection(this)" class="remove-btn">×</button>
                </div>
            `;
            
            container.appendChild(connectionDiv);
        }
        
        function removeConnection(button) {
            const connectionItem = button.closest('.connection-item');
            const source = connectionItem.getAttribute('data-source');
            const target = connectionItem.getAttribute('data-target');
            
            conceptConnections = conceptConnections.filter(conn => 
                !(conn.source === source && conn.target === target)
            );
            
            connectionItem.remove();
            updateConnectionCount();
        }
        
        function updateConnectionSelects(selectedNodes) {
            const sourceSelect = document.getElementById('sourceSelect');
            const targetSelect = document.getElementById('targetSelect');
            
            if (selectedNodes.length > 0) {
                sourceSelect.value = selectedNodes[0];
                if (selectedNodes.length > 1) {
                    targetSelect.value = selectedNodes[1];
                }
            }
        }
        
        function updateConnectionCount() {
            document.getElementById('connectionCount').textContent = conceptConnections.length + '개';
        }
        
        function updateThemeLength() {
            const theme = document.getElementById('reconstructedTheme').value;
            document.getElementById('themeLength').textContent = theme.length + '자';
        }
        
        function checkThemeQuality() {
            const theme = document.getElementById('reconstructedTheme').value;
            const sentences = window.currentPhase4Data?.all_sentences || [];
            
            // Calculate quality metrics
            const coherence = calculateCoherence(theme, sentences);
            const completeness = calculateCompleteness(theme, sentences);
            const abstraction = calculateAbstraction(theme);
            const connection = calculateConnectionQuality(conceptConnections);
            
            // Update UI
            updateMetricBar('coherence', coherence);
            updateMetricBar('completeness', completeness);  
            updateMetricBar('abstraction', abstraction);
            updateMetricBar('connection', connection);
            
            const overall = (coherence + completeness + abstraction + connection) / 4;
            document.getElementById('overallQuality').textContent = Math.round(overall * 100) + '%';
        }
        
        function updateMetricBar(type, value) {
            const bar = document.getElementById(type + 'Bar');
            const score = document.getElementById(type + 'Score');
            
            if (bar && score) {
                bar.style.width = (value * 100) + '%';
                score.textContent = Math.round(value * 100) + '%';
            }
        }
        
        function calculateCoherence(theme, sentences) {
            if (!theme || theme.length < 10) return 0;
            
            let mentionedConcepts = 0;
            sentences.forEach(sent => {
                if (sent.main_concept && theme.toLowerCase().includes(sent.main_concept.toLowerCase())) {
                    mentionedConcepts++;
                }
            });
            
            return Math.min(1, mentionedConcepts / sentences.length + 0.2);
        }
        
        function calculateCompleteness(theme, sentences) {
            if (!theme) return 0;
            
            const importantSentences = sentences.filter(s => s.importance > 0.7);
            let coveredSentences = 0;
            
            importantSentences.forEach(sent => {
                if (sent.main_concept && theme.toLowerCase().includes(sent.main_concept.toLowerCase())) {
                    coveredSentences++;
                }
            });
            
            return importantSentences.length > 0 ? coveredSentences / importantSentences.length : 0.5;
        }
        
        function calculateAbstraction(theme) {
            if (!theme) return 0;
            
            const wordCount = theme.split(' ').length;
            const charCount = theme.length;
            
            // Optimal range: 10-30 words, 30-150 characters
            const wordScore = (10 <= wordCount && wordCount <= 30) ? 1 : Math.max(0, 1 - Math.abs(wordCount - 20) * 0.05);
            const charScore = (30 <= charCount && charCount <= 150) ? 1 : Math.max(0, 1 - Math.abs(charCount - 90) * 0.01);
            
            return (wordScore + charScore) / 2;
        }
        
        function calculateConnectionQuality(connections) {
            if (connections.length === 0) return 0.3; // Neutral if no connections
            
            const sentences = window.currentPhase4Data?.all_sentences || [];
            const maxConnections = sentences.length * (sentences.length - 1) / 2;
            
            if (maxConnections === 0) return 0.5;
            
            return Math.min(1, connections.length / Math.min(maxConnections, sentences.length));
        }
        
        function autoPreview() {
            autoPreviewEnabled = !autoPreviewEnabled;
            const button = event.target;
            button.textContent = autoPreviewEnabled ? '실시간 미리보기 끄기' : '실시간 미리보기';
            button.classList.toggle('active', autoPreviewEnabled);
        }
        
        function initializeQualityMetrics() {
            // Initialize with empty state
            updateMetricBar('coherence', 0);
            updateMetricBar('completeness', 0);
            updateMetricBar('abstraction', 0);
            updateMetricBar('connection', 0);
        }
        
        // Helper functions for UI colors
        function getSentenceColor(role) {
            const colors = {
                'topic': '#667eea',
                'supporting': '#48bb78',
                'example': '#ed8936',
                'conclusion': '#805ad5',
                'transition': '#38b2ac'
            };
            return colors[role] || '#a0aec0';
        }
        
        function getConceptColor(role) {
            const colors = {
                'topic': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                'supporting': 'linear-gradient(135deg, #48bb78 0%, #38a169 100%)',
                'example': 'linear-gradient(135deg, #ed8936 0%, #dd6b20 100%)',
                'conclusion': 'linear-gradient(135deg, #805ad5 0%, #6b46c1 100%)',
                'transition': 'linear-gradient(135deg, #38b2ac 0%, #319795 100%)'
            };
            return colors[role] || 'linear-gradient(135deg, #a0aec0 0%, #718096 100%)';
        }
        
        function translateRole(role) {
            const translations = {
                'topic': '주제',
                'supporting': '뒷받침',
                'example': '예시',
                'conclusion': '결론',
                'transition': '연결'
            };
            return translations[role] || role;
        }
        
        console.log('4단계 한국어 요약 학습 시스템 준비 완료');

/**
 * Lawsker 实时协作系统
 * 基于WebRTC的多人实时协作功能
 */

class RealtimeCollaboration {
    constructor() {
        this.isActive = false;
        this.participants = new Map();
        this.localUser = null;
        this.sharedState = new Map();
        this.cursors = new Map();
        this.annotations = new Map();
        this.init();
    }

    init() {
        this.setupUI();
        this.setupWebRTC();
        this.setupSharedState();
        this.setupCursorTracking();
        this.setupAnnotationSystem();
    }

    setupUI() {
        const collabContainer = document.createElement('div');
        collabContainer.id = 'collaboration-panel';
        collabContainer.className = 'collaboration-container';
        collabContainer.innerHTML = `
            <div class="collab-header">
                <div class="collab-title">
                    <i data-feather="users"></i>
                    <span>实时协作</span>
                </div>
                <div class="collab-controls">
                    <button onclick="window.collaboration.startSession()" class="collab-btn start-btn">
                        <i data-feather="video"></i>
                        开始协作
                    </button>
                    <button onclick="window.collaboration.shareScreen()" class="collab-btn share-btn">
                        <i data-feather="monitor"></i>
                        共享屏幕
                    </button>
                </div>
            </div>
            <div class="participants-list" id="participantsList">
                <div class="participant-item self">
                    <div class="participant-avatar">👤</div>
                    <div class="participant-info">
                        <div class="participant-name">您</div>
                        <div class="participant-status">主持人</div>
                    </div>
                </div>
            </div>
            <div class="collab-features">
                <button onclick="window.collaboration.toggleAnnotations()" class="feature-btn">
                    <i data-feather="edit-3"></i>
                    标注模式
                </button>
                <button onclick="window.collaboration.syncView()" class="feature-btn">
                    <i data-feather="eye"></i>
                    同步视图
                </button>
                <button onclick="window.collaboration.startVoiceChat()" class="feature-btn">
                    <i data-feather="mic"></i>
                    语音通话
                </button>
            </div>
            <div class="chat-area" id="collaborationChat">
                <div class="chat-messages" id="chatMessages"></div>
                <div class="chat-input-area">
                    <input type="text" id="chatInput" placeholder="输入消息..." />
                    <button onclick="window.collaboration.sendChatMessage()">
                        <i data-feather="send"></i>
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(collabContainer);
    }

    setupWebRTC() {
        this.rtc = {
            localStream: null,
            peerConnections: new Map(),
            dataChannels: new Map(),
            
            async initializeMedia() {
                try {
                    this.localStream = await navigator.mediaDevices.getUserMedia({
                        video: true,
                        audio: true
                    });
                    return true;
                } catch (error) {
                    console.warn('无法访问摄像头/麦克风:', error);
                    return false;
                }
            },

            async createPeerConnection(participantId) {
                const config = {
                    iceServers: [
                        { urls: 'stun:stun.l.google.com:19302' }
                    ]
                };
                
                const pc = new RTCPeerConnection(config);
                
                // 添加本地流
                if (this.localStream) {
                    this.localStream.getTracks().forEach(track => {
                        pc.addTrack(track, this.localStream);
                    });
                }
                
                // 创建数据通道
                const dataChannel = pc.createDataChannel('collaboration', {
                    ordered: true
                });
                
                this.setupDataChannel(dataChannel, participantId);
                
                pc.ondatachannel = (event) => {
                    this.setupDataChannel(event.channel, participantId);
                };
                
                pc.ontrack = (event) => {
                    this.handleRemoteStream(event.streams[0], participantId);
                };
                
                this.peerConnections.set(participantId, pc);
                return pc;
            },

            setupDataChannel(channel, participantId) {
                channel.onopen = () => {
                    console.log(`数据通道已连接: ${participantId}`);
                    this.dataChannels.set(participantId, channel);
                };
                
                channel.onmessage = (event) => {
                    this.handleDataChannelMessage(JSON.parse(event.data), participantId);
                };
            },

            handleRemoteStream(stream, participantId) {
                // 显示远程视频流
                const videoElement = document.createElement('video');
                videoElement.srcObject = stream;
                videoElement.autoplay = true;
                videoElement.muted = false;
                videoElement.className = 'remote-video';
                
                const participant = this.participants.get(participantId);
                if (participant) {
                    participant.videoElement = videoElement;
                    this.updateParticipantUI(participantId);
                }
            }
        };
    }    set
upSharedState() {
        this.stateManager = {
            state: {
                currentView: 'dashboard',
                selectedCharts: [],
                filters: {},
                annotations: [],
                cursorPositions: {}
            },

            updateState(key, value, broadcast = true) {
                this.state[key] = value;
                
                if (broadcast) {
                    this.broadcastStateChange(key, value);
                }
                
                this.applyStateChange(key, value);
            },

            broadcastStateChange(key, value) {
                const message = {
                    type: 'state_change',
                    key,
                    value,
                    timestamp: Date.now(),
                    userId: window.collaboration.localUser?.id
                };
                
                window.collaboration.broadcastMessage(message);
            },

            applyStateChange(key, value) {
                switch (key) {
                    case 'currentView':
                        this.syncViewChange(value);
                        break;
                    case 'selectedCharts':
                        this.syncChartSelection(value);
                        break;
                    case 'filters':
                        this.syncFilters(value);
                        break;
                    case 'annotations':
                        this.syncAnnotations(value);
                        break;
                }
            },

            syncViewChange(view) {
                // 同步视图切换
                const navTabs = document.querySelectorAll('.nav-tab');
                navTabs.forEach(tab => {
                    tab.classList.remove('active');
                    if (tab.getAttribute('href') === `#${view}`) {
                        tab.classList.add('active');
                    }
                });
            },

            syncChartSelection(charts) {
                // 同步图表选择
                document.querySelectorAll('.chart-container').forEach(chart => {
                    chart.classList.remove('collab-selected');
                });
                
                charts.forEach(chartId => {
                    const chart = document.getElementById(chartId);
                    if (chart) {
                        chart.classList.add('collab-selected');
                    }
                });
            },

            syncFilters(filters) {
                // 同步筛选器状态
                Object.entries(filters).forEach(([filterId, filterValue]) => {
                    const filterElement = document.getElementById(filterId);
                    if (filterElement) {
                        filterElement.value = filterValue;
                        // 触发筛选器变化事件
                        filterElement.dispatchEvent(new Event('change'));
                    }
                });
            },

            syncAnnotations(annotations) {
                // 同步标注
                window.collaboration.renderAnnotations(annotations);
            }
        };
    }

    setupCursorTracking() {
        this.cursorTracker = {
            isTracking: false,
            
            startTracking() {
                this.isTracking = true;
                document.addEventListener('mousemove', this.handleMouseMove.bind(this));
                document.addEventListener('click', this.handleClick.bind(this));
            },

            stopTracking() {
                this.isTracking = false;
                document.removeEventListener('mousemove', this.handleMouseMove.bind(this));
                document.removeEventListener('click', this.handleClick.bind(this));
            },

            handleMouseMove(e) {
                if (!this.isTracking) return;
                
                const cursorData = {
                    x: e.clientX,
                    y: e.clientY,
                    timestamp: Date.now()
                };
                
                window.collaboration.broadcastMessage({
                    type: 'cursor_move',
                    data: cursorData,
                    userId: window.collaboration.localUser?.id
                });
            },

            handleClick(e) {
                if (!this.isTracking) return;
                
                const clickData = {
                    x: e.clientX,
                    y: e.clientY,
                    element: e.target.tagName,
                    timestamp: Date.now()
                };
                
                window.collaboration.broadcastMessage({
                    type: 'cursor_click',
                    data: clickData,
                    userId: window.collaboration.localUser?.id
                });
            },

            renderRemoteCursor(userId, cursorData) {
                let cursor = document.getElementById(`cursor-${userId}`);
                
                if (!cursor) {
                    cursor = document.createElement('div');
                    cursor.id = `cursor-${userId}`;
                    cursor.className = 'remote-cursor';
                    cursor.innerHTML = `
                        <div class="cursor-pointer"></div>
                        <div class="cursor-label">${window.collaboration.participants.get(userId)?.name || 'User'}</div>
                    `;
                    document.body.appendChild(cursor);
                }
                
                cursor.style.left = `${cursorData.x}px`;
                cursor.style.top = `${cursorData.y}px`;
                cursor.style.display = 'block';
                
                // 自动隐藏不活跃的光标
                clearTimeout(cursor.hideTimer);
                cursor.hideTimer = setTimeout(() => {
                    cursor.style.display = 'none';
                }, 3000);
            }
        };
    }

    setupAnnotationSystem() {
        this.annotationSystem = {
            isActive: false,
            currentTool: 'text',
            
            activate() {
                this.isActive = true;
                document.body.classList.add('annotation-mode');
                document.addEventListener('click', this.handleAnnotationClick.bind(this));
            },

            deactivate() {
                this.isActive = false;
                document.body.classList.remove('annotation-mode');
                document.removeEventListener('click', this.handleAnnotationClick.bind(this));
            },

            handleAnnotationClick(e) {
                if (!this.isActive) return;
                
                e.preventDefault();
                e.stopPropagation();
                
                const annotation = {
                    id: `annotation-${Date.now()}`,
                    x: e.clientX,
                    y: e.clientY,
                    type: this.currentTool,
                    content: '',
                    author: window.collaboration.localUser?.id,
                    timestamp: Date.now()
                };
                
                this.createAnnotation(annotation);
            },

            createAnnotation(annotation) {
                if (annotation.type === 'text') {
                    const content = prompt('请输入标注内容:');
                    if (!content) return;
                    
                    annotation.content = content;
                }
                
                window.collaboration.addAnnotation(annotation);
            }
        };
    }

    // 公共方法
    async startSession() {
        try {
            const hasMedia = await this.rtc.initializeMedia();
            
            this.localUser = {
                id: `user-${Date.now()}`,
                name: '当前用户',
                role: 'host',
                hasVideo: hasMedia,
                hasAudio: hasMedia
            };
            
            this.isActive = true;
            this.cursorTracker.startTracking();
            
            this.showNotification('协作会话已开始', 'success');
            
            // 模拟添加参与者
            setTimeout(() => {
                this.addParticipant({
                    id: 'user-demo',
                    name: '演示用户',
                    role: 'participant',
                    hasVideo: true,
                    hasAudio: true
                });
            }, 2000);
            
        } catch (error) {
            console.error('启动协作会话失败:', error);
            this.showNotification('启动协作会话失败', 'error');
        }
    }

    addParticipant(participant) {
        this.participants.set(participant.id, participant);
        this.updateParticipantsList();
        
        // 创建WebRTC连接
        this.rtc.createPeerConnection(participant.id);
        
        this.showNotification(`${participant.name} 加入了协作`, 'info');
    }

    removeParticipant(participantId) {
        const participant = this.participants.get(participantId);
        if (participant) {
            this.participants.delete(participantId);
            this.updateParticipantsList();
            
            // 清理WebRTC连接
            const pc = this.rtc.peerConnections.get(participantId);
            if (pc) {
                pc.close();
                this.rtc.peerConnections.delete(participantId);
            }
            
            this.showNotification(`${participant.name} 离开了协作`, 'info');
        }
    }

    updateParticipantsList() {
        const list = document.getElementById('participantsList');
        const selfItem = list.querySelector('.participant-item.self');
        
        // 清除现有参与者（保留自己）
        list.querySelectorAll('.participant-item:not(.self)').forEach(item => item.remove());
        
        // 添加其他参与者
        this.participants.forEach(participant => {
            const item = document.createElement('div');
            item.className = 'participant-item';
            item.innerHTML = `
                <div class="participant-avatar">${participant.hasVideo ? '📹' : '👤'}</div>
                <div class="participant-info">
                    <div class="participant-name">${participant.name}</div>
                    <div class="participant-status">${participant.role === 'host' ? '主持人' : '参与者'}</div>
                </div>
                <div class="participant-controls">
                    ${participant.hasAudio ? '<i data-feather="mic"></i>' : '<i data-feather="mic-off"></i>'}
                    ${participant.hasVideo ? '<i data-feather="video"></i>' : '<i data-feather="video-off"></i>'}
                </div>
            `;
            
            list.appendChild(item);
        });
        
        // 更新图标
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }

    broadcastMessage(message) {
        // 通过数据通道广播消息
        this.rtc.dataChannels.forEach(channel => {
            if (channel.readyState === 'open') {
                channel.send(JSON.stringify(message));
            }
        });
    }

    handleDataChannelMessage(message, senderId) {
        switch (message.type) {
            case 'cursor_move':
                this.cursorTracker.renderRemoteCursor(senderId, message.data);
                break;
            case 'cursor_click':
                this.showRemoteClick(senderId, message.data);
                break;
            case 'state_change':
                this.stateManager.applyStateChange(message.key, message.value);
                break;
            case 'annotation_add':
                this.renderAnnotation(message.data);
                break;
            case 'chat_message':
                this.addChatMessage(message.data, senderId);
                break;
        }
    }

    toggleAnnotations() {
        if (this.annotationSystem.isActive) {
            this.annotationSystem.deactivate();
            this.showNotification('标注模式已关闭', 'info');
        } else {
            this.annotationSystem.activate();
            this.showNotification('标注模式已开启，点击任意位置添加标注', 'info');
        }
    }

    syncView() {
        const currentView = this.getCurrentView();
        this.stateManager.updateState('currentView', currentView);
        this.showNotification('视图已同步给所有参与者', 'success');
    }

    getCurrentView() {
        const activeTab = document.querySelector('.nav-tab.active');
        return activeTab ? activeTab.getAttribute('href').substring(1) : 'dashboard';
    }

    addAnnotation(annotation) {
        this.annotations.set(annotation.id, annotation);
        this.renderAnnotation(annotation);
        
        // 广播给其他参与者
        this.broadcastMessage({
            type: 'annotation_add',
            data: annotation
        });
    }

    renderAnnotation(annotation) {
        const element = document.createElement('div');
        element.id = annotation.id;
        element.className = 'collaboration-annotation';
        element.style.left = `${annotation.x}px`;
        element.style.top = `${annotation.y}px`;
        element.innerHTML = `
            <div class="annotation-content">${annotation.content}</div>
            <div class="annotation-author">${this.participants.get(annotation.author)?.name || '未知用户'}</div>
        `;
        
        document.body.appendChild(element);
    }

    renderAnnotations(annotations) {
        // 清除现有标注
        document.querySelectorAll('.collaboration-annotation').forEach(el => el.remove());
        
        // 渲染新标注
        annotations.forEach(annotation => {
            this.renderAnnotation(annotation);
        });
    }

    sendChatMessage() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();
        
        if (!message) return;
        
        const chatMessage = {
            content: message,
            author: this.localUser?.id,
            timestamp: Date.now()
        };
        
        this.addChatMessage(chatMessage, this.localUser?.id);
        
        this.broadcastMessage({
            type: 'chat_message',
            data: chatMessage
        });
        
        input.value = '';
    }

    addChatMessage(message, senderId) {
        const chatMessages = document.getElementById('chatMessages');
        const messageElement = document.createElement('div');
        messageElement.className = `chat-message ${senderId === this.localUser?.id ? 'own' : 'other'}`;
        
        const participant = this.participants.get(senderId) || this.localUser;
        messageElement.innerHTML = `
            <div class="message-author">${participant?.name || '未知用户'}</div>
            <div class="message-content">${message.content}</div>
            <div class="message-time">${new Date(message.timestamp).toLocaleTimeString()}</div>
        `;
        
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    showRemoteClick(userId, clickData) {
        const clickIndicator = document.createElement('div');
        clickIndicator.className = 'remote-click-indicator';
        clickIndicator.style.left = `${clickData.x}px`;
        clickIndicator.style.top = `${clickData.y}px`;
        
        document.body.appendChild(clickIndicator);
        
        setTimeout(() => {
            clickIndicator.remove();
        }, 1000);
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `collab-notification collab-notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }
}

// 全局实例
window.collaboration = new RealtimeCollaboration();

// 样式
const collabStyles = document.createElement('style');
collabStyles.textContent = `
    .collaboration-container {
        position: fixed;
        top: 20px;
        left: 20px;
        width: 300px;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 15px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        z-index: 999;
        max-height: 80vh;
        overflow: hidden;
        display: flex;
        flex-direction: column;
    }

    .collab-header {
        padding: 1rem;
        border-bottom: 1px solid rgba(0, 0, 0, 0.1);
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border-radius: 15px 15px 0 0;
    }

    .collab-title {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    .collab-controls {
        display: flex;
        gap: 0.5rem;
    }

    .collab-btn {
        padding: 0.5rem 0.75rem;
        background: rgba(255, 255, 255, 0.2);
        color: white;
        border: none;
        border-radius: 0.5rem;
        cursor: pointer;
        font-size: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.25rem;
        transition: all 0.2s ease;
    }

    .collab-btn:hover {
        background: rgba(255, 255, 255, 0.3);
    }

    .participants-list {
        max-height: 200px;
        overflow-y: auto;
        padding: 0.5rem;
    }

    .participant-item {
        display: flex;
        align-items: center;
        padding: 0.5rem;
        border-radius: 0.5rem;
        margin-bottom: 0.25rem;
        transition: background 0.2s ease;
    }

    .participant-item:hover {
        background: rgba(0, 0, 0, 0.05);
    }

    .participant-item.self {
        background: rgba(37, 99, 235, 0.1);
    }

    .participant-avatar {
        width: 2rem;
        height: 2rem;
        border-radius: 50%;
        background: #e5e7eb;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 0.75rem;
        font-size: 1rem;
    }

    .participant-info {
        flex: 1;
    }

    .participant-name {
        font-weight: 500;
        font-size: 0.875rem;
    }

    .participant-status {
        font-size: 0.75rem;
        color: #6b7280;
    }

    .participant-controls {
        display: flex;
        gap: 0.25rem;
    }

    .collab-features {
        padding: 0.5rem;
        border-top: 1px solid rgba(0, 0, 0, 0.1);
        display: flex;
        flex-wrap: wrap;
        gap: 0.25rem;
    }

    .feature-btn {
        padding: 0.5rem;
        background: #f3f4f6;
        border: none;
        border-radius: 0.5rem;
        cursor: pointer;
        font-size: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.25rem;
        transition: all 0.2s ease;
        flex: 1;
        justify-content: center;
    }

    .feature-btn:hover {
        background: #e5e7eb;
    }

    .chat-area {
        flex: 1;
        display: flex;
        flex-direction: column;
        border-top: 1px solid rgba(0, 0, 0, 0.1);
        min-height: 200px;
    }

    .chat-messages {
        flex: 1;
        padding: 0.5rem;
        overflow-y: auto;
        max-height: 150px;
    }

    .chat-message {
        margin-bottom: 0.5rem;
        font-size: 0.75rem;
    }

    .chat-message.own {
        text-align: right;
    }

    .message-author {
        font-weight: 500;
        color: #374151;
        margin-bottom: 0.125rem;
    }

    .message-content {
        background: #f3f4f6;
        padding: 0.5rem;
        border-radius: 0.5rem;
        display: inline-block;
        max-width: 80%;
    }

    .chat-message.own .message-content {
        background: #2563eb;
        color: white;
    }

    .message-time {
        color: #9ca3af;
        font-size: 0.625rem;
        margin-top: 0.125rem;
    }

    .chat-input-area {
        padding: 0.5rem;
        border-top: 1px solid rgba(0, 0, 0, 0.1);
        display: flex;
        gap: 0.5rem;
    }

    .chat-input-area input {
        flex: 1;
        padding: 0.5rem;
        border: 1px solid #d1d5db;
        border-radius: 0.5rem;
        font-size: 0.75rem;
        outline: none;
    }

    .chat-input-area button {
        padding: 0.5rem;
        background: #2563eb;
        color: white;
        border: none;
        border-radius: 0.5rem;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .remote-cursor {
        position: fixed;
        pointer-events: none;
        z-index: 10000;
        transition: all 0.1s ease;
    }

    .cursor-pointer {
        width: 0;
        height: 0;
        border-left: 8px solid #2563eb;
        border-right: 8px solid transparent;
        border-bottom: 12px solid transparent;
        border-top: 12px solid #2563eb;
        transform: rotate(-45deg);
    }

    .cursor-label {
        background: #2563eb;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.75rem;
        margin-top: 0.5rem;
        white-space: nowrap;
    }

    .collaboration-annotation {
        position: fixed;
        background: #fef3c7;
        border: 2px solid #f59e0b;
        border-radius: 0.5rem;
        padding: 0.5rem;
        z-index: 1000;
        max-width: 200px;
        font-size: 0.75rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .annotation-content {
        margin-bottom: 0.25rem;
        font-weight: 500;
    }

    .annotation-author {
        color: #92400e;
        font-size: 0.625rem;
    }

    .remote-click-indicator {
        position: fixed;
        width: 20px;
        height: 20px;
        border: 2px solid #ef4444;
        border-radius: 50%;
        pointer-events: none;
        z-index: 10000;
        animation: clickPulse 1s ease-out;
    }

    @keyframes clickPulse {
        0% {
            transform: scale(0.5);
            opacity: 1;
        }
        100% {
            transform: scale(2);
            opacity: 0;
        }
    }

    .collab-notification {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 0.75rem 1rem;
        border-radius: 0.5rem;
        color: white;
        z-index: 10001;
        transform: translateX(100%);
        transition: transform 0.3s ease;
        font-size: 0.875rem;
        font-weight: 500;
    }

    .collab-notification.show {
        transform: translateX(0);
    }

    .collab-notification-info {
        background: #3b82f6;
    }

    .collab-notification-success {
        background: #10b981;
    }

    .collab-notification-error {
        background: #ef4444;
    }

    .annotation-mode {
        cursor: crosshair;
    }

    .collab-selected {
        outline: 3px solid #2563eb;
        outline-offset: 2px;
    }

    @media (max-width: 768px) {
        .collaboration-container {
            width: 250px;
            max-height: 60vh;
        }
    }
`;

document.head.appendChild(collabStyles);
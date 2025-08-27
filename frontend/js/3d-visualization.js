/**
 * Lawsker 3D数据可视化引擎
 * 基于WebGL的高级3D数据展示
 */

class ThreeDVisualization {
    constructor() {
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.charts = new Map();
        this.animations = [];
        this.isVRSupported = false;
        this.init();
    }

    init() {
        this.checkWebGLSupport();
        this.checkVRSupport();
        this.setupUI();
        this.initializeThreeJS();
        this.setupControls();
        this.setupLighting();
        this.startRenderLoop();
    }

    checkWebGLSupport() {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        
        if (!gl) {
            console.warn('WebGL不支持，3D功能将被禁用');
            return false;
        }
        
        return true;
    }

    checkVRSupport() {
        if ('xr' in navigator) {
            navigator.xr.isSessionSupported('immersive-vr').then((supported) => {
                this.isVRSupported = supported;
                if (supported) {
                    this.setupVRControls();
                }
            });
        }
    }

    setupUI() {
        const container = document.createElement('div');
        container.id = '3d-visualization-panel';
        container.className = '3d-viz-container';
        container.innerHTML = `
            <div class="3d-viz-header">
                <div class="3d-viz-title">
                    <i data-feather="box"></i>
                    <span>3D数据可视化</span>
                </div>
                <div class="3d-viz-controls">
                    <button onclick="window.threeDViz.create3DChart('bar')" class="3d-btn">
                        <i data-feather="bar-chart"></i>
                        3D柱状图
                    </button>
                    <button onclick="window.threeDViz.create3DChart('scatter')" class="3d-btn">
                        <i data-feather="scatter-chart"></i>
                        3D散点图
                    </button>
                    <button onclick="window.threeDViz.create3DChart('surface')" class="3d-btn">
                        <i data-feather="layers"></i>
                        3D曲面图
                    </button>
                    ${this.isVRSupported ? `
                        <button onclick="window.threeDViz.enterVR()" class="3d-btn vr-btn">
                            <i data-feather="eye"></i>
                            VR模式
                        </button>
                    ` : ''}
                </div>
            </div>
            <div class="3d-canvas-container" id="threeDCanvasContainer">
                <canvas id="threeDCanvas"></canvas>
                <div class="3d-loading" id="threeDLoading">
                    <div class="loading-spinner"></div>
                    <div>正在加载3D场景...</div>
                </div>
            </div>
            <div class="3d-viz-settings">
                <div class="setting-group">
                    <label>视角控制</label>
                    <div class="setting-controls">
                        <button onclick="window.threeDViz.resetCamera()">重置视角</button>
                        <button onclick="window.threeDViz.toggleAutoRotate()">自动旋转</button>
                    </div>
                </div>
                <div class="setting-group">
                    <label>渲染质量</label>
                    <select onchange="window.threeDViz.setRenderQuality(this.value)">
                        <option value="low">低质量</option>
                        <option value="medium" selected>中等质量</option>
                        <option value="high">高质量</option>
                    </select>
                </div>
                <div class="setting-group">
                    <label>动画效果</label>
                    <div class="setting-controls">
                        <button onclick="window.threeDViz.playAnimation()">播放动画</button>
                        <button onclick="window.threeDViz.pauseAnimation()">暂停动画</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(container);
    }

    initializeThreeJS() {
        // 创建场景
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0xf0f0f0);
        
        // 创建相机
        const canvas = document.getElementById('threeDCanvas');
        const aspect = canvas.clientWidth / canvas.clientHeight;
        this.camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 1000);
        this.camera.position.set(10, 10, 10);
        
        // 创建渲染器
        this.renderer = new THREE.WebGLRenderer({
            canvas: canvas,
            antialias: true,
            alpha: true
        });
        
        this.renderer.setSize(canvas.clientWidth, canvas.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        
        // 响应式处理
        window.addEventListener('resize', () => {
            this.handleResize();
        });
    }
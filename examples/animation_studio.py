from fasthtml.common import *
from datetime import datetime
import json
import os

# File path for persistent storage of animations
ANIMATIONS_DIR = "animations"
FRAMES_DIR = "animation_frames"
os.makedirs(ANIMATIONS_DIR, exist_ok=True)
os.makedirs(FRAMES_DIR, exist_ok=True)

# In-memory storage for current session
stroke_history = []  # List of stroke entries for deletion/management
saved_frames = []  # Frames saved for video compilation

# CSS for the animation studio
animation_styles = Style("""
    /* Main layout */
    .app-container {
        display: grid;
        grid-template-columns: 1fr 400px;
        gap: 1.5rem;
        margin-top: 1rem;
        min-height: calc(100vh - 150px);
    }

    @media (max-width: 1100px) {
        .app-container {
            grid-template-columns: 1fr;
        }
    }

    /* Canvas section */
    .canvas-section {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .canvas-container {
        position: relative;
        border: 2px solid var(--pico-muted-border-color);
        border-radius: 8px;
        background: white;
        overflow: hidden;
    }

    #drawing-canvas {
        display: block;
        cursor: crosshair;
    }

    /* Mode indicator on canvas */
    .canvas-mode-indicator {
        position: absolute;
        top: 10px;
        left: 10px;
        padding: 0.25rem 0.5rem;
        background: rgba(0, 0, 0, 0.7);
        color: white;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
        pointer-events: none;
        display: none;
    }

    .canvas-mode-indicator.active {
        display: block;
    }

    .canvas-mode-indicator.motion-mode {
        background: rgba(52, 152, 219, 0.9);
    }

    /* Toolbar */
    .toolbar {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        padding: 0.75rem;
        background: var(--pico-card-background-color);
        border: 1px solid var(--pico-muted-border-color);
        border-radius: 8px;
        align-items: center;
    }

    .toolbar-group {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding-right: 1rem;
        border-right: 1px solid var(--pico-muted-border-color);
    }

    .toolbar-group:last-child {
        border-right: none;
        padding-right: 0;
    }

    .toolbar label {
        font-size: 0.85rem;
        color: var(--pico-muted-color);
        margin: 0;
    }

    .toolbar input[type="color"] {
        width: 40px;
        height: 32px;
        padding: 2px;
        border: 1px solid var(--pico-muted-border-color);
        border-radius: 4px;
        cursor: pointer;
    }

    .toolbar input[type="range"] {
        width: 80px;
        margin: 0;
    }

    .toolbar button {
        padding: 0.4rem 0.8rem;
        font-size: 0.85rem;
    }

    .toolbar button.active {
        background: var(--pico-primary);
        color: white;
    }

    .toolbar button.danger {
        background: #e74c3c;
        border-color: #c0392b;
    }

    .toolbar button.danger:hover {
        background: #c0392b;
    }

    .toolbar button.warning {
        background: #f39c12;
        border-color: #d68910;
    }

    /* Side panel */
    .side-panel {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .panel-section {
        border: 1px solid var(--pico-muted-border-color);
        border-radius: 8px;
        background: var(--pico-card-background-color);
        overflow: hidden;
    }

    .panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.75rem 1rem;
        background: var(--pico-secondary-background);
        border-bottom: 1px solid var(--pico-muted-border-color);
        font-weight: bold;
        font-size: 0.9rem;
    }

    .panel-header button {
        padding: 0.25rem 0.5rem;
        font-size: 0.75rem;
    }

    .panel-content {
        padding: 0.75rem;
        max-height: 280px;
        overflow-y: auto;
    }

    /* Stroke history items */
    .stroke-item {
        display: flex;
        align-items: center;
        padding: 0.5rem;
        margin-bottom: 0.5rem;
        background: var(--pico-background-color);
        border-radius: 4px;
        font-size: 0.85rem;
        border: 2px solid transparent;
        transition: all 0.2s;
    }

    .stroke-item:last-child {
        margin-bottom: 0;
    }

    .stroke-item.selected {
        border-color: var(--pico-primary);
        background: rgba(var(--pico-primary-rgb), 0.1);
    }

    .stroke-item.is-motion-object {
        border-color: #9b59b6;
        background: rgba(155, 89, 182, 0.1);
    }

    .stroke-item.is-motion-object.has-path {
        border-color: #27ae60;
        background: rgba(39, 174, 96, 0.1);
    }

    .stroke-preview {
        width: 24px;
        height: 24px;
        border-radius: 4px;
        border: 1px solid var(--pico-muted-border-color);
        flex-shrink: 0;
    }

    .stroke-info {
        flex: 1;
        margin: 0 0.5rem;
        font-family: monospace;
        font-size: 0.7rem;
        color: var(--pico-muted-color);
    }

    .stroke-type-badge {
        font-size: 0.6rem;
        padding: 0.1rem 0.3rem;
        border-radius: 3px;
        margin-left: 0.25rem;
        font-weight: bold;
    }

    .stroke-type-badge.motion-object {
        background: #9b59b6;
        color: white;
    }

    .stroke-type-badge.has-path {
        background: #27ae60;
        color: white;
    }

    .stroke-buttons {
        display: flex;
        gap: 0.2rem;
        flex-shrink: 0;
    }

    .stroke-item button {
        padding: 0.15rem 0.35rem;
        font-size: 0.6rem;
        white-space: nowrap;
    }

    .stroke-item button.delete-btn {
        background: #e74c3c;
        border-color: #c0392b;
        color: white;
    }

    .stroke-item button.motion-obj-btn {
        background: #9b59b6;
        border-color: #8e44ad;
        color: white;
    }

    .stroke-item button.motion-obj-btn.active {
        background: #27ae60;
        border-color: #1e8449;
    }

    .stroke-item button.set-path-btn {
        background: #3498db;
        border-color: #2980b9;
        color: white;
    }

    .stroke-item button.set-path-btn:disabled {
        background: #95a5a6;
        border-color: #7f8c8d;
        cursor: not-allowed;
    }

    /* Playback controls */
    .playback-controls {
        display: flex;
        gap: 0.5rem;
        padding: 0.75rem;
        background: var(--pico-card-background-color);
        border: 1px solid var(--pico-muted-border-color);
        border-radius: 8px;
        align-items: center;
        justify-content: center;
        flex-wrap: wrap;
    }

    .playback-controls button {
        padding: 0.5rem 1rem;
        font-size: 0.9rem;
    }

    .playback-controls input[type="range"] {
        width: 100px;
    }

    .playback-controls input[type="number"] {
        width: 60px;
        padding: 0.3rem;
        font-size: 0.8rem;
    }

    .speed-label {
        font-size: 0.8rem;
        color: var(--pico-muted-color);
        min-width: 40px;
    }

    /* Frame panel */
    .frame-list {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        padding: 0.5rem;
    }

    .frame-thumbnail {
        width: 50px;
        height: 38px;
        border: 2px solid var(--pico-muted-border-color);
        border-radius: 4px;
        cursor: pointer;
        object-fit: cover;
        background: #f0f0f0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.6rem;
        color: var(--pico-muted-color);
    }

    .frame-thumbnail:hover {
        border-color: var(--pico-primary);
    }

    .frame-info {
        padding: 0.5rem;
        font-size: 0.8rem;
        color: var(--pico-muted-color);
        border-bottom: 1px solid var(--pico-muted-border-color);
    }

    /* Status bar */
    .status-bar {
        display: flex;
        gap: 1rem;
        padding: 0.5rem 1rem;
        background: var(--pico-card-background-color);
        border: 1px solid var(--pico-muted-border-color);
        border-radius: 8px;
        font-size: 0.8rem;
        flex-wrap: wrap;
    }

    .status-item {
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }

    .status-label {
        color: var(--pico-muted-color);
    }

    .status-value {
        font-weight: bold;
        color: var(--pico-primary);
    }

    /* Recording indicator */
    .recording-indicator {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .recording-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #27ae60;
    }

    .recording-dot.playing {
        background: #3498db;
        animation: pulse-recording 1s infinite;
    }

    .recording-dot.generating {
        background: #f39c12;
        animation: pulse-recording 0.5s infinite;
    }

    .recording-dot.path-mode {
        background: #9b59b6;
        animation: pulse-recording 0.5s infinite;
    }

    @keyframes pulse-recording {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(0.9); }
    }

    /* Progress bar */
    .progress-container {
        width: 100%;
        padding: 0.5rem 1rem;
        background: var(--pico-card-background-color);
        border: 1px solid var(--pico-muted-border-color);
        border-radius: 8px;
        display: none;
    }

    .progress-container.active {
        display: block;
    }

    .progress-bar {
        width: 100%;
        height: 8px;
        background: var(--pico-muted-border-color);
        border-radius: 4px;
        overflow: hidden;
    }

    .progress-fill {
        height: 100%;
        background: var(--pico-primary);
        transition: width 0.1s;
    }

    .progress-text {
        font-size: 0.8rem;
        color: var(--pico-muted-color);
        margin-top: 0.25rem;
        text-align: center;
    }

    /* Empty states */
    .empty-state {
        text-align: center;
        padding: 1.5rem;
        color: var(--pico-muted-color);
        font-size: 0.85rem;
    }

    /* Modal overlay for dialogs */
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    }

    .modal-overlay.hidden {
        display: none;
    }

    .modal-content {
        background: var(--pico-card-background-color);
        padding: 1.5rem;
        border-radius: 8px;
        min-width: 300px;
        max-width: 90%;
    }

    .modal-content h3 {
        margin-top: 0;
    }

    .modal-buttons {
        display: flex;
        gap: 0.5rem;
        justify-content: flex-end;
        margin-top: 1rem;
    }

    /* Feature badge */
    .feature-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.25rem 0.75rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Description */
    .feature-description {
        padding: 1rem;
        background: var(--pico-card-background-color);
        border: 1px solid var(--pico-muted-border-color);
        border-radius: 8px;
        margin-bottom: 1rem;
    }

    .feature-description p {
        margin: 0;
        color: var(--pico-muted-color);
        font-size: 0.9rem;
    }

    /* Instructions text */
    .instructions {
        font-size: 0.75rem;
        color: var(--pico-muted-color);
        padding: 0.5rem;
        background: rgba(var(--pico-primary-rgb), 0.05);
        border-radius: 4px;
        margin-bottom: 0.5rem;
        line-height: 1.4;
    }

    .instructions strong {
        color: var(--pico-color);
    }

    /* Legend */
    .legend {
        display: flex;
        gap: 0.75rem;
        flex-wrap: wrap;
        font-size: 0.7rem;
        padding: 0.5rem;
        border-top: 1px solid var(--pico-muted-border-color);
        margin-top: 0.5rem;
    }

    .legend-item {
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }

    .legend-color {
        width: 12px;
        height: 12px;
        border-radius: 2px;
    }

    .legend-color.normal {
        background: var(--pico-background-color);
        border: 1px solid var(--pico-muted-border-color);
    }

    .legend-color.motion-obj {
        background: rgba(155, 89, 182, 0.3);
        border: 2px solid #9b59b6;
    }

    .legend-color.with-path {
        background: rgba(39, 174, 96, 0.3);
        border: 2px solid #27ae60;
    }
""")

# JavaScript for canvas drawing, stroke recording, and animation playback
animation_js = Script("""
// Animation Studio State
const AnimationStudio = {
    canvas: null,
    ctx: null,
    isDrawing: false,
    currentStroke: [],
    strokes: [],
    savedFrames: [],
    currentColor: '#3CDD8C',
    brushSize: 5,
    playbackSpeed: 1,
    isPlaying: false,
    isGeneratingFrames: false,
    animationFrame: null,
    mode: 'draw', // 'draw', 'set-path'
    selectedStrokeId: null, // Stroke selected for setting motion path
    motionPath: [],
    frameRate: 30,

    init() {
        this.canvas = document.getElementById('drawing-canvas');
        if (!this.canvas) return;

        this.ctx = this.canvas.getContext('2d');
        this.setupCanvas();
        this.attachListeners();
        this.loadFromStorage();
        this.render();
        this.updateStrokeHistory();
        this.updateStatus();
        console.log('[AnimationStudio] Initialized');
    },

    setupCanvas() {
        const container = this.canvas.parentElement;
        this.canvas.width = container.clientWidth || 800;
        this.canvas.height = 500;
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';
    },

    attachListeners() {
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', () => this.handleMouseUp());
        this.canvas.addEventListener('mouseleave', () => this.handleMouseUp());

        // Touch support
        this.canvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
            this.handleMouseDown(e.touches[0]);
        });
        this.canvas.addEventListener('touchmove', (e) => {
            e.preventDefault();
            this.handleMouseMove(e.touches[0]);
        });
        this.canvas.addEventListener('touchend', () => this.handleMouseUp());

        const colorPicker = document.getElementById('color-picker');
        if (colorPicker) {
            colorPicker.addEventListener('change', (e) => {
                this.currentColor = e.target.value;
            });
        }

        const brushSize = document.getElementById('brush-size');
        if (brushSize) {
            brushSize.addEventListener('input', (e) => {
                this.brushSize = parseInt(e.target.value, 10);
                document.getElementById('brush-size-value').textContent = this.brushSize + 'px';
            });
        }

        const speedSlider = document.getElementById('playback-speed');
        if (speedSlider) {
            speedSlider.addEventListener('input', (e) => {
                this.playbackSpeed = parseFloat(e.target.value);
                document.getElementById('speed-value').textContent = this.playbackSpeed + 'x';
            });
        }

        const fpsInput = document.getElementById('frame-rate');
        if (fpsInput) {
            fpsInput.addEventListener('change', (e) => {
                this.frameRate = parseInt(e.target.value, 10) || 30;
            });
        }

        window.addEventListener('resize', () => {
            const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
            this.setupCanvas();
            this.ctx.putImageData(imageData, 0, 0);
        });
    },

    getCanvasCoords(e) {
        const rect = this.canvas.getBoundingClientRect();
        return {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
    },

    // Handle mouse/touch events based on current mode
    handleMouseDown(e) {
        if (this.isPlaying || this.isGeneratingFrames) return;

        if (this.mode === 'set-path' && this.selectedStrokeId) {
            this.startMotionPath(e);
        } else {
            this.startDrawing(e);
        }
    },

    handleMouseMove(e) {
        if (this.isPlaying || this.isGeneratingFrames) return;
        if (!this.isDrawing) return;

        if (this.mode === 'set-path' && this.selectedStrokeId) {
            this.continueMotionPath(e);
        } else {
            this.continueDrawing(e);
        }
    },

    handleMouseUp() {
        if (!this.isDrawing) return;

        if (this.mode === 'set-path' && this.selectedStrokeId) {
            this.finishMotionPath();
        } else {
            this.finishDrawing();
        }
    },

    // Normal drawing mode
    startDrawing(e) {
        this.isDrawing = true;
        const coords = this.getCanvasCoords(e);
        this.currentStroke = [{
            x: coords.x,
            y: coords.y,
            time: Date.now(),
            color: this.currentColor,
            size: this.brushSize
        }];

        this.ctx.beginPath();
        this.ctx.moveTo(coords.x, coords.y);
    },

    continueDrawing(e) {
        const coords = this.getCanvasCoords(e);
        this.currentStroke.push({
            x: coords.x,
            y: coords.y,
            time: Date.now(),
            color: this.currentColor,
            size: this.brushSize
        });

        this.ctx.strokeStyle = this.currentColor;
        this.ctx.lineWidth = this.brushSize;
        this.ctx.lineTo(coords.x, coords.y);
        this.ctx.stroke();
    },

    finishDrawing() {
        this.isDrawing = false;

        if (this.currentStroke.length > 1) {
            const stroke = {
                id: Date.now(),
                points: [...this.currentStroke],
                color: this.currentColor,
                size: this.brushSize,
                timestamp: new Date().toISOString(),
                isMotionObject: false,  // Not a motion object by default
                motionPath: null        // No motion path by default
            };

            this.strokes.push(stroke);
            this.saveToStorage();
            this.updateStrokeHistory();
            this.updateStatus();
            this.sendStrokeToServer(stroke);
        }

        this.currentStroke = [];
    },

    // Motion path drawing for motion objects
    startMotionPath(e) {
        this.isDrawing = true;
        const coords = this.getCanvasCoords(e);
        this.motionPath = [{ x: coords.x, y: coords.y, time: Date.now() }];
    },

    continueMotionPath(e) {
        const coords = this.getCanvasCoords(e);
        this.motionPath.push({ x: coords.x, y: coords.y, time: Date.now() });

        // Draw motion path preview
        this.render();
        this.ctx.save();
        this.ctx.strokeStyle = '#3498db';
        this.ctx.lineWidth = 3;
        this.ctx.setLineDash([8, 4]);
        this.ctx.beginPath();
        this.motionPath.forEach((point, i) => {
            if (i === 0) this.ctx.moveTo(point.x, point.y);
            else this.ctx.lineTo(point.x, point.y);
        });
        this.ctx.stroke();

        // Draw arrow heads along path
        if (this.motionPath.length > 1) {
            const lastIdx = this.motionPath.length - 1;
            this.drawArrowHead(
                this.motionPath[lastIdx - 1],
                this.motionPath[lastIdx]
            );
        }
        this.ctx.restore();
    },

    drawArrowHead(from, to) {
        const angle = Math.atan2(to.y - from.y, to.x - from.x);
        const headLength = 12;

        this.ctx.save();
        this.ctx.fillStyle = '#3498db';
        this.ctx.beginPath();
        this.ctx.moveTo(to.x, to.y);
        this.ctx.lineTo(
            to.x - headLength * Math.cos(angle - Math.PI / 6),
            to.y - headLength * Math.sin(angle - Math.PI / 6)
        );
        this.ctx.lineTo(
            to.x - headLength * Math.cos(angle + Math.PI / 6),
            to.y - headLength * Math.sin(angle + Math.PI / 6)
        );
        this.ctx.closePath();
        this.ctx.fill();
        this.ctx.restore();
    },

    finishMotionPath() {
        this.isDrawing = false;

        if (this.motionPath.length > 1 && this.selectedStrokeId) {
            // Assign motion path to selected stroke
            const stroke = this.strokes.find(s => s.id === this.selectedStrokeId);
            if (stroke && stroke.isMotionObject) {
                stroke.motionPath = {
                    points: [...this.motionPath],
                    duration: this.motionPath[this.motionPath.length - 1].time - this.motionPath[0].time
                };
                this.saveToStorage();
                this.updateStrokeHistory();
                this.sendMotionPathToServer(stroke.id, stroke.motionPath);
                console.log('[AnimationStudio] Motion path set for stroke:', stroke.id);
            }
        }

        // Exit path-setting mode
        this.motionPath = [];
        this.selectedStrokeId = null;
        this.mode = 'draw';
        this.updateModeIndicator();
        this.render();
    },

    // Toggle motion object classification for a stroke
    toggleMotionObject(strokeId) {
        const stroke = this.strokes.find(s => s.id === strokeId);
        if (!stroke) return;

        stroke.isMotionObject = !stroke.isMotionObject;

        // Clear motion path if un-classifying
        if (!stroke.isMotionObject) {
            stroke.motionPath = null;
        }

        this.saveToStorage();
        this.updateStrokeHistory();
        this.updateStatus();
        this.render();

        // Notify server
        fetch('/animation/toggle-motion-object', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stroke_id: strokeId, is_motion_object: stroke.isMotionObject })
        });
    },

    // Enter mode to set motion path for a stroke
    startSettingPath(strokeId) {
        const stroke = this.strokes.find(s => s.id === strokeId);
        if (!stroke || !stroke.isMotionObject) {
            alert('First mark the stroke as a Motion Object before setting its path.');
            return;
        }

        this.selectedStrokeId = strokeId;
        this.mode = 'set-path';
        this.motionPath = [];
        this.updateModeIndicator();
        this.updateStrokeHistory();
        this.render();

        console.log('[AnimationStudio] Setting motion path for stroke:', strokeId);
    },

    // Cancel path setting mode
    cancelPathSetting() {
        this.selectedStrokeId = null;
        this.mode = 'draw';
        this.motionPath = [];
        this.updateModeIndicator();
        this.updateStrokeHistory();
        this.render();
    },

    // Clear motion path from a stroke
    clearMotionPath(strokeId) {
        const stroke = this.strokes.find(s => s.id === strokeId);
        if (stroke) {
            stroke.motionPath = null;
            this.saveToStorage();
            this.updateStrokeHistory();
            this.render();
        }
    },

    updateModeIndicator() {
        const indicator = document.getElementById('mode-indicator');
        if (indicator) {
            if (this.mode === 'set-path') {
                indicator.textContent = 'DRAW MOTION PATH - Draw the path this stroke will follow';
                indicator.classList.add('active', 'motion-mode');
            } else {
                indicator.classList.remove('active', 'motion-mode');
            }
        }

        // Update status dot
        const dot = document.querySelector('.recording-dot');
        if (dot) {
            dot.classList.toggle('path-mode', this.mode === 'set-path');
        }
    },

    clearCanvas() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.strokes = [];
        this.selectedStrokeId = null;
        this.mode = 'draw';
        this.saveToStorage();
        this.updateStrokeHistory();
        this.updateStatus();
        this.updateModeIndicator();
        fetch('/animation/clear', { method: 'POST' });
        console.log('[AnimationStudio] Canvas cleared');
    },

    deleteStroke(strokeId) {
        this.strokes = this.strokes.filter(s => s.id !== strokeId);
        if (this.selectedStrokeId === strokeId) {
            this.selectedStrokeId = null;
            this.mode = 'draw';
            this.updateModeIndicator();
        }
        this.saveToStorage();
        this.render();
        this.updateStrokeHistory();
        this.updateStatus();

        fetch('/animation/delete-stroke', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stroke_id: strokeId })
        });
    },

    render() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        this.strokes.forEach(stroke => {
            const isSelected = stroke.id === this.selectedStrokeId;
            this.drawStroke(stroke, isSelected);
        });
    },

    drawStroke(stroke, highlight = false) {
        if (stroke.points.length < 2) return;

        this.ctx.beginPath();
        this.ctx.strokeStyle = stroke.color;
        this.ctx.lineWidth = stroke.size;
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';

        stroke.points.forEach((point, i) => {
            if (i === 0) this.ctx.moveTo(point.x, point.y);
            else this.ctx.lineTo(point.x, point.y);
        });

        this.ctx.stroke();

        // Highlight if selected for path setting
        if (highlight) {
            this.ctx.save();
            this.ctx.strokeStyle = '#3498db';
            this.ctx.lineWidth = stroke.size + 6;
            this.ctx.globalAlpha = 0.3;
            this.ctx.beginPath();
            stroke.points.forEach((point, i) => {
                if (i === 0) this.ctx.moveTo(point.x, point.y);
                else this.ctx.lineTo(point.x, point.y);
            });
            this.ctx.stroke();
            this.ctx.restore();
        }

        // Draw motion path indicator if exists
        if (stroke.motionPath && stroke.motionPath.points && stroke.motionPath.points.length > 0) {
            this.ctx.save();
            this.ctx.strokeStyle = '#27ae60';
            this.ctx.lineWidth = 2;
            this.ctx.setLineDash([5, 3]);
            this.ctx.globalAlpha = 0.6;
            this.ctx.beginPath();
            stroke.motionPath.points.forEach((point, i) => {
                if (i === 0) this.ctx.moveTo(point.x, point.y);
                else this.ctx.lineTo(point.x, point.y);
            });
            this.ctx.stroke();
            this.ctx.restore();
        }
    },

    // Replay animation with automatic frame generation
    async startReplay(generateFrames = false) {
        if (this.isPlaying || this.isGeneratingFrames) return;
        if (this.strokes.length === 0) {
            alert('Nothing to replay! Draw something first.');
            return;
        }

        // Exit any special mode
        this.mode = 'draw';
        this.selectedStrokeId = null;
        this.updateModeIndicator();

        this.isPlaying = true;
        this.isGeneratingFrames = generateFrames;

        if (generateFrames) {
            this.savedFrames = [];
            this.showProgress(true);
        }

        this.updatePlaybackUI();
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Sort strokes by timestamp
        const sortedStrokes = [...this.strokes].sort((a, b) =>
            a.points[0].time - b.points[0].time
        );

        // Calculate total duration
        const firstTime = sortedStrokes[0].points[0].time;
        let lastTime = firstTime;

        sortedStrokes.forEach(stroke => {
            const strokeEnd = stroke.points[stroke.points.length - 1].time;
            if (strokeEnd > lastTime) lastTime = strokeEnd;

            // For motion objects, extend duration by motion path duration
            if (stroke.isMotionObject && stroke.motionPath && stroke.motionPath.duration) {
                const motionEnd = stroke.points[stroke.points.length - 1].time + stroke.motionPath.duration;
                if (motionEnd > lastTime) lastTime = motionEnd;
            }
        });

        const totalDuration = lastTime - firstTime;

        // Frame generation settings
        const frameInterval = generateFrames ? (1000 / this.frameRate) : 0;
        let lastFrameTime = -frameInterval; // Capture first frame immediately
        let frameCount = 0;
        const expectedFrames = generateFrames ? Math.ceil((totalDuration / this.playbackSpeed) / frameInterval) + 1 : 0;

        const startTime = Date.now();

        const animate = () => {
            if (!this.isPlaying) {
                this.finishReplay(generateFrames);
                return;
            }

            const elapsed = (Date.now() - startTime) * this.playbackSpeed;
            const currentTime = firstTime + elapsed;

            // Clear and redraw
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

            // Draw each stroke
            sortedStrokes.forEach(stroke => {
                const strokeStartTime = stroke.points[0].time;
                const strokeEndTime = stroke.points[stroke.points.length - 1].time;

                if (currentTime < strokeStartTime) return; // Stroke hasn't started

                if (stroke.isMotionObject && stroke.motionPath && stroke.motionPath.points) {
                    // MOTION OBJECT: Draw complete stroke, translated along motion path
                    const strokeDrawnTime = strokeEndTime; // After stroke is fully drawn

                    if (currentTime >= strokeDrawnTime) {
                        // Stroke is complete, now animate along path
                        const motionElapsed = currentTime - strokeDrawnTime;
                        const motionProgress = Math.min(motionElapsed / stroke.motionPath.duration, 1);
                        const pathIndex = Math.floor(motionProgress * (stroke.motionPath.points.length - 1));
                        const pathPoint = stroke.motionPath.points[Math.min(pathIndex, stroke.motionPath.points.length - 1)];
                        const startPoint = stroke.motionPath.points[0];

                        const offsetX = pathPoint.x - startPoint.x;
                        const offsetY = pathPoint.y - startPoint.y;

                        // Draw complete stroke at offset position
                        this.drawStrokeAtOffset(stroke, offsetX, offsetY);
                    } else {
                        // Stroke still drawing progressively
                        const pointsToDraw = stroke.points.filter(p => p.time <= currentTime);
                        if (pointsToDraw.length > 1) {
                            this.drawPartialStroke(stroke, pointsToDraw);
                        }
                    }
                } else {
                    // REGULAR STROKE: Draw progressively
                    let pointsToDraw = stroke.points;
                    if (currentTime < strokeEndTime) {
                        pointsToDraw = stroke.points.filter(p => p.time <= currentTime);
                    }

                    if (pointsToDraw.length > 1) {
                        this.drawPartialStroke(stroke, pointsToDraw);
                    }
                }
            });

            // Capture frame if generating
            if (generateFrames && elapsed - lastFrameTime >= frameInterval) {
                this.captureFrame(frameCount);
                frameCount++;
                lastFrameTime = elapsed;
                this.updateProgress(frameCount, expectedFrames);
            }

            // Continue or finish
            if (elapsed < totalDuration) {
                this.animationFrame = requestAnimationFrame(animate);
            } else {
                // Capture final frame
                if (generateFrames && frameCount < expectedFrames) {
                    this.captureFrame(frameCount);
                    frameCount++;
                }
                this.finishReplay(generateFrames);
            }
        };

        animate();
    },

    drawPartialStroke(stroke, points) {
        if (points.length < 2) return;

        this.ctx.beginPath();
        this.ctx.strokeStyle = stroke.color;
        this.ctx.lineWidth = stroke.size;
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';

        points.forEach((point, i) => {
            if (i === 0) this.ctx.moveTo(point.x, point.y);
            else this.ctx.lineTo(point.x, point.y);
        });

        this.ctx.stroke();
    },

    drawStrokeAtOffset(stroke, offsetX, offsetY) {
        if (stroke.points.length < 2) return;

        this.ctx.beginPath();
        this.ctx.strokeStyle = stroke.color;
        this.ctx.lineWidth = stroke.size;
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';

        stroke.points.forEach((point, i) => {
            if (i === 0) this.ctx.moveTo(point.x + offsetX, point.y + offsetY);
            else this.ctx.lineTo(point.x + offsetX, point.y + offsetY);
        });

        this.ctx.stroke();
    },

    captureFrame(index) {
        const frameData = this.canvas.toDataURL('image/png');
        const frame = {
            id: Date.now() + index,
            index: index,
            data: frameData,
            timestamp: new Date().toISOString()
        };
        this.savedFrames.push(frame);

        // Send to server
        fetch('/animation/save-frame', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                index: index,
                data: frameData,
                timestamp: frame.timestamp
            })
        });
    },

    finishReplay(wasGenerating) {
        this.isPlaying = false;
        this.isGeneratingFrames = false;

        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }

        this.render();
        this.updatePlaybackUI();
        this.showProgress(false);

        if (wasGenerating) {
            this.updateFrameList();
            this.updateStatus();
            alert(`Generated ${this.savedFrames.length} frames for video compilation!`);
        }
    },

    stopReplay() {
        this.isPlaying = false;
        this.isGeneratingFrames = false;
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }
        this.render();
        this.updatePlaybackUI();
        this.showProgress(false);
    },

    showProgress(show) {
        const container = document.getElementById('progress-container');
        if (container) {
            container.classList.toggle('active', show);
        }
    },

    updateProgress(current, total) {
        const fill = document.getElementById('progress-fill');
        const text = document.getElementById('progress-text');
        if (fill && text) {
            const percent = Math.min(Math.round((current / total) * 100), 100);
            fill.style.width = percent + '%';
            text.textContent = `Generating frames: ${current} / ${total}`;
        }
    },

    async exportFrames() {
        if (this.savedFrames.length === 0) {
            alert('No frames to export! Use "Generate Frames" first.');
            return;
        }

        for (let i = 0; i < this.savedFrames.length; i++) {
            const frame = this.savedFrames[i];
            const link = document.createElement('a');
            link.href = frame.data;
            link.download = `frame_${String(i + 1).padStart(4, '0')}.png`;
            link.click();
            await new Promise(r => setTimeout(r, 50));
        }

        console.log('[AnimationStudio] Exported', this.savedFrames.length, 'frames');
    },

    clearFrames() {
        this.savedFrames = [];
        this.updateFrameList();
        this.updateStatus();
        fetch('/animation/clear-frames', { method: 'POST' });
    },

    async saveAnimation(name) {
        const animationData = {
            name: name || `animation_${Date.now()}`,
            strokes: this.strokes,
            canvasWidth: this.canvas.width,
            canvasHeight: this.canvas.height,
            timestamp: new Date().toISOString()
        };

        try {
            const response = await fetch('/animation/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(animationData)
            });

            const result = await response.json();
            if (result.status === 'ok') {
                alert(`Animation saved as: ${result.filename}`);
                this.loadAnimationList();
            }
        } catch (e) {
            console.error('[AnimationStudio] Error saving animation:', e);
        }
    },

    async loadAnimation(filename) {
        try {
            const response = await fetch(`/animation/load/${filename}`);
            const data = await response.json();

            if (data.strokes) {
                this.strokes = data.strokes;
            }

            this.selectedStrokeId = null;
            this.mode = 'draw';
            this.updateModeIndicator();
            this.saveToStorage();
            this.render();
            this.updateStrokeHistory();
            this.updateStatus();

            console.log('[AnimationStudio] Animation loaded:', filename);
        } catch (e) {
            console.error('[AnimationStudio] Error loading animation:', e);
        }
    },

    // UI updates
    updateStrokeHistory() {
        htmx.ajax('GET', '/animation/stroke-history', {
            target: '#stroke-history',
            swap: 'innerHTML'
        });
    },

    updateFrameList() {
        htmx.ajax('GET', '/animation/frame-list', {
            target: '#frame-list',
            swap: 'innerHTML'
        });
    },

    updateStatus() {
        htmx.ajax('GET', '/animation/status', {
            target: '#status-bar',
            swap: 'innerHTML'
        });
    },

    updatePlaybackUI() {
        const playBtn = document.getElementById('play-btn');
        const genBtn = document.getElementById('generate-btn');
        const stopBtn = document.getElementById('stop-btn');
        const recordDot = document.querySelector('.recording-dot');

        if (playBtn) playBtn.disabled = this.isPlaying || this.isGeneratingFrames;
        if (genBtn) genBtn.disabled = this.isPlaying || this.isGeneratingFrames;
        if (stopBtn) stopBtn.disabled = !this.isPlaying && !this.isGeneratingFrames;

        if (recordDot) {
            recordDot.classList.toggle('playing', this.isPlaying && !this.isGeneratingFrames);
            recordDot.classList.toggle('generating', this.isGeneratingFrames);
        }
    },

    loadAnimationList() {
        htmx.ajax('GET', '/animation/list', {
            target: '#animation-list',
            swap: 'innerHTML'
        });
    },

    saveToStorage() {
        try {
            localStorage.setItem('animationStudio_strokes', JSON.stringify(this.strokes));
        } catch (e) {
            console.warn('[AnimationStudio] Failed to save to localStorage:', e);
        }
    },

    loadFromStorage() {
        try {
            const strokes = localStorage.getItem('animationStudio_strokes');
            if (strokes) {
                this.strokes = JSON.parse(strokes);
            }
        } catch (e) {
            console.warn('[AnimationStudio] Failed to load from localStorage:', e);
        }
    },

    async sendStrokeToServer(stroke) {
        try {
            await fetch('/animation/record-stroke', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(stroke)
            });
        } catch (e) {
            console.warn('[AnimationStudio] Failed to send stroke to server:', e);
        }
    },

    async sendMotionPathToServer(strokeId, motionPath) {
        try {
            await fetch('/animation/set-motion-path', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ stroke_id: strokeId, motion_path: motionPath })
            });
        } catch (e) {
            console.warn('[AnimationStudio] Failed to send motion path to server:', e);
        }
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => AnimationStudio.init());
} else {
    AnimationStudio.init();
}

window.AnimationStudio = AnimationStudio;
""", type='module')

app, rt = fast_app(hdrs=[animation_styles, animation_js])


def Toolbar():
    """Create the drawing toolbar."""
    return Div(
        Div(
            Label("Color:"),
            Input(type='color', id='color-picker', value='#3CDD8C'),
            cls='toolbar-group'
        ),
        Div(
            Label("Size:"),
            Input(type='range', id='brush-size', min='1', max='30', value='5'),
            Span("5px", id='brush-size-value', style='font-size: 0.8rem; min-width: 35px;'),
            cls='toolbar-group'
        ),
        Div(
            Button("Clear Canvas", cls='danger', onclick="AnimationStudio.clearCanvas()"),
            cls='toolbar-group'
        ),
        cls='toolbar'
    )


def PlaybackControls():
    """Create playback control buttons."""
    return Div(
        Button("Play", id='play-btn', onclick="AnimationStudio.startReplay(false)"),
        Button("Generate Frames", id='generate-btn', cls='warning',
               onclick="AnimationStudio.startReplay(true)"),
        Button("Stop", id='stop-btn', onclick="AnimationStudio.stopReplay()", disabled=True),
        Span("Speed:", cls='speed-label'),
        Input(type='range', id='playback-speed', min='0.25', max='4', step='0.25', value='1'),
        Span("1x", id='speed-value', cls='speed-label'),
        Span("FPS:", cls='speed-label'),
        Input(type='number', id='frame-rate', value='30', min='1', max='60'),
        cls='playback-controls'
    )


def ProgressBar():
    """Progress bar for frame generation."""
    return Div(
        Div(
            Div(id='progress-fill', cls='progress-fill', style='width: 0%'),
            cls='progress-bar'
        ),
        Div("Generating frames...", id='progress-text', cls='progress-text'),
        id='progress-container',
        cls='progress-container'
    )


def StrokeHistoryPanel():
    """Panel showing stroke history with motion object controls."""
    return Div(
        Div(
            Span("Stroke History"),
            Button("Clear All", onclick="AnimationStudio.clearCanvas()", style='font-size: 0.7rem;'),
            cls='panel-header'
        ),
        Div(id='stroke-history', cls='panel-content'),
        cls='panel-section'
    )


def FramePanel():
    """Panel for saved frames."""
    return Div(
        Div(
            Span("Generated Frames"),
            Div(
                Button("Export All", onclick="AnimationStudio.exportFrames()", style='font-size: 0.7rem;'),
                Button("Clear", onclick="AnimationStudio.clearFrames()", style='font-size: 0.7rem;'),
            ),
            cls='panel-header'
        ),
        Div(id='frame-list', cls='panel-content'),
        cls='panel-section'
    )


def SaveLoadPanel():
    """Panel for saving and loading animations."""
    return Div(
        Div(
            Span("Saved Animations"),
            Button("Save", onclick="document.getElementById('save-dialog').classList.remove('hidden')",
                   style='font-size: 0.7rem;'),
            cls='panel-header'
        ),
        Div(id='animation-list', cls='panel-content',
            hx_get='/animation/list', hx_trigger='load'),
        cls='panel-section'
    )


def StatusBar():
    """Status bar showing current stats."""
    return Div(
        Div(
            Span(cls='recording-dot'),
            Span("Ready", style='font-size: 0.8rem;'),
            cls='recording-indicator'
        ),
        Div(
            Span("Strokes:", cls='status-label'),
            Span("0", cls='status-value'),
            cls='status-item'
        ),
        Div(
            Span("Motion Objects:", cls='status-label'),
            Span("0", cls='status-value'),
            cls='status-item'
        ),
        Div(
            Span("Frames:", cls='status-label'),
            Span("0", cls='status-value'),
            cls='status-item'
        ),
        id='status-bar',
        cls='status-bar'
    )


def SaveDialog():
    """Dialog for saving animations."""
    return Div(
        Div(
            H3("Save Animation"),
            Div(
                Label("Name:"),
                Input(type='text', id='animation-name', placeholder='my_animation'),
            ),
            Div(
                Button("Save", onclick="""
                    AnimationStudio.saveAnimation(document.getElementById('animation-name').value);
                    document.getElementById('save-dialog').classList.add('hidden');
                """),
                Button("Cancel", onclick="document.getElementById('save-dialog').classList.add('hidden')",
                       style='background: #95a5a6;'),
                cls='modal-buttons'
            ),
            cls='modal-content'
        ),
        id='save-dialog',
        cls='modal-overlay hidden'
    )


@rt("/")
def get():
    """Main page."""
    return Titled(
        "Animation Studio",
        Div(
            P("Draw strokes on the canvas. Mark any stroke as a 'Motion Object' to make it move along a path during playback. "
              "Regular strokes animate by drawing progressively. Motion objects draw first, then move along their defined path."),
            Span("Agentic AI", cls='feature-badge'),
            cls='feature-description'
        ),
        Div(
            Div(
                Toolbar(),
                Div(
                    Canvas(id='drawing-canvas'),
                    Div(id='mode-indicator', cls='canvas-mode-indicator'),
                    cls='canvas-container'
                ),
                PlaybackControls(),
                ProgressBar(),
                StatusBar(),
                cls='canvas-section'
            ),
            Div(
                StrokeHistoryPanel(),
                FramePanel(),
                SaveLoadPanel(),
                cls='side-panel'
            ),
            cls='app-container'
        ),
        SaveDialog()
    )


@rt("/animation/stroke-history")
def get():
    """Get stroke history HTML with motion object controls."""
    instructions = Div(
        P(
            Strong("How to use:"), " Draw strokes normally. Click ", Strong("'Motion Obj'"),
            " to mark a stroke as a motion object. Then click ", Strong("'Set Path'"),
            " and draw the path it should follow during animation.",
            cls='instructions'
        ),
        Div(
            Div(Div(cls='legend-color normal'), Span("Regular Stroke"), cls='legend-item'),
            Div(Div(cls='legend-color motion-obj'), Span("Motion Object"), cls='legend-item'),
            Div(Div(cls='legend-color with-path'), Span("Has Path"), cls='legend-item'),
            cls='legend'
        )
    )

    if not stroke_history:
        return Div(
            instructions,
            P("No strokes yet. Start drawing on the canvas!", cls='empty-state')
        )

    items = [instructions]

    for stroke in reversed(stroke_history[-20:]):
        stroke_id = stroke.get('id', 0)
        color = stroke.get('color', '#000')
        points = stroke.get('points', [])
        size = stroke.get('size', 5)
        is_motion_obj = stroke.get('isMotionObject', False)
        has_path = stroke.get('motionPath') is not None

        # Build class list
        item_classes = ['stroke-item']
        if is_motion_obj:
            item_classes.append('is-motion-object')
            if has_path:
                item_classes.append('has-path')

        # Build badges
        badges = []
        if is_motion_obj:
            if has_path:
                path_pts = len(stroke.get('motionPath', {}).get('points', []))
                badges.append(Span(f"PATH ({path_pts}pts)", cls='stroke-type-badge has-path'))
            else:
                badges.append(Span("MOTION OBJ", cls='stroke-type-badge motion-object'))

        # Build buttons
        buttons = []

        # Motion Object toggle button
        motion_btn_text = "Unmark" if is_motion_obj else "Motion Obj"
        motion_btn_cls = 'motion-obj-btn active' if is_motion_obj else 'motion-obj-btn'
        buttons.append(
            Button(motion_btn_text, cls=motion_btn_cls,
                   onclick=f"event.stopPropagation(); AnimationStudio.toggleMotionObject({stroke_id})")
        )

        # Set Path button (only for motion objects)
        if is_motion_obj:
            if has_path:
                buttons.append(
                    Button("Clear Path", cls='set-path-btn',
                           onclick=f"event.stopPropagation(); AnimationStudio.clearMotionPath({stroke_id})")
                )
            else:
                buttons.append(
                    Button("Set Path", cls='set-path-btn',
                           onclick=f"event.stopPropagation(); AnimationStudio.startSettingPath({stroke_id})")
                )

        # Delete button
        buttons.append(
            Button("x", cls='delete-btn',
                   onclick=f"event.stopPropagation(); AnimationStudio.deleteStroke({stroke_id})")
        )

        items.append(
            Div(
                Div(style=f'background: {color};', cls='stroke-preview'),
                Span(f"{len(points)} pts, {size}px", *badges, cls='stroke-info'),
                Div(*buttons, cls='stroke-buttons'),
                cls=' '.join(item_classes)
            )
        )

    return Div(*items)


@rt("/animation/frame-list")
def get():
    """Get frame list HTML."""
    if not saved_frames:
        return Div(
            Div("Use 'Generate Frames' to capture the entire animation as image frames for video compilation.",
                cls='frame-info'),
            P("No frames generated yet.", cls='empty-state')
        )

    frame_count = len(saved_frames)
    return Div(
        Div(f"{frame_count} frames generated. Export and use ffmpeg to compile: ",
            Code("ffmpeg -framerate 30 -i frame_%04d.png output.mp4", style='font-size: 0.7rem;'),
            cls='frame-info'),
        Div(
            *[Span(f"{i + 1}", cls='frame-thumbnail') for i in range(min(frame_count, 50))],
            Span(f"+{frame_count - 50}", cls='frame-thumbnail') if frame_count > 50 else "",
            cls='frame-list'
        )
    )


@rt("/animation/status")
def get():
    """Get status bar HTML."""
    motion_objects = sum(1 for s in stroke_history if s.get('isMotionObject', False))
    with_paths = sum(1 for s in stroke_history if s.get('isMotionObject', False) and s.get('motionPath'))

    return Div(
        Div(
            Span(cls='recording-dot'),
            Span("Ready", style='font-size: 0.8rem;'),
            cls='recording-indicator'
        ),
        Div(
            Span("Strokes:", cls='status-label'),
            Span(str(len(stroke_history)), cls='status-value'),
            cls='status-item'
        ),
        Div(
            Span("Motion Objects:", cls='status-label'),
            Span(f"{with_paths}/{motion_objects}", cls='status-value'),
            cls='status-item'
        ),
        Div(
            Span("Frames:", cls='status-label'),
            Span(str(len(saved_frames)), cls='status-value'),
            cls='status-item'
        ),
        id='status-bar',
        cls='status-bar'
    )


@rt("/animation/list")
def get():
    """Get list of saved animations."""
    try:
        files = [f for f in os.listdir(ANIMATIONS_DIR) if f.endswith('.json')]
        if not files:
            return Div(P("No saved animations."), cls='empty-state')

        items = []
        for f in sorted(files, reverse=True)[:10]:
            items.append(
                Div(
                    Span(f.replace('.json', ''), style='flex: 1; font-size: 0.85rem;'),
                    Button("Load", onclick=f"AnimationStudio.loadAnimation('{f}')",
                           style='font-size: 0.7rem; padding: 0.2rem 0.4rem;'),
                    cls='stroke-item'
                )
            )

        return Div(*items)
    except Exception as e:
        return Div(P(f"Error: {e}"), cls='empty-state')


@rt("/animation/record-stroke")
async def post(request):
    """Record a stroke from the client."""
    try:
        data = await request.json()
        stroke_history.append(data)
        return {"status": "ok", "count": len(stroke_history)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@rt("/animation/toggle-motion-object")
async def post(request):
    """Toggle motion object status for a stroke."""
    global stroke_history
    try:
        data = await request.json()
        stroke_id = data.get('stroke_id')
        is_motion_object = data.get('is_motion_object', False)

        for stroke in stroke_history:
            if stroke.get('id') == stroke_id:
                stroke['isMotionObject'] = is_motion_object
                if not is_motion_object:
                    stroke['motionPath'] = None
                break

        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@rt("/animation/set-motion-path")
async def post(request):
    """Set motion path for a stroke."""
    global stroke_history
    try:
        data = await request.json()
        stroke_id = data.get('stroke_id')
        motion_path = data.get('motion_path')

        for stroke in stroke_history:
            if stroke.get('id') == stroke_id:
                stroke['motionPath'] = motion_path
                break

        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@rt("/animation/save-frame")
async def post(request):
    """Save a generated frame."""
    try:
        data = await request.json()
        frame = {
            'index': data.get('index'),
            'timestamp': data.get('timestamp'),
            'data': data.get('data')
        }
        saved_frames.append(frame)
        return {"status": "ok", "count": len(saved_frames)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@rt("/animation/delete-stroke")
async def post(request):
    """Delete a stroke."""
    global stroke_history
    try:
        data = await request.json()
        stroke_id = data.get('stroke_id')
        stroke_history = [s for s in stroke_history if s.get('id') != stroke_id]
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@rt("/animation/clear")
def post():
    """Clear all strokes."""
    global stroke_history
    stroke_history = []
    return {"status": "ok"}


@rt("/animation/clear-frames")
def post():
    """Clear all saved frames."""
    global saved_frames
    saved_frames = []
    return {"status": "ok"}


@rt("/animation/save")
async def post(request):
    """Save animation to file."""
    try:
        data = await request.json()
        name = data.get('name', f'animation_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        filename = f"{name}.json"
        filepath = os.path.join(ANIMATIONS_DIR, filename)

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        return {"status": "ok", "filename": filename}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@rt("/animation/load/{filename}")
def get(filename: str):
    """Load animation from file."""
    try:
        filepath = os.path.join(ANIMATIONS_DIR, filename)
        if not os.path.exists(filepath):
            return {"error": "File not found"}

        with open(filepath, 'r') as f:
            data = json.load(f)

        global stroke_history
        stroke_history = data.get('strokes', [])

        return data
    except Exception as e:
        return {"error": str(e)}


serve()

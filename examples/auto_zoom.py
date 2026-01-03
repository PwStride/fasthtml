from fasthtml.common import *
from datetime import datetime
import json

# CSS for the automated zoom accessibility feature
auto_zoom_styles = Style("""
    /* Root and body setup for zoom functionality */
    :root {
        --zoom-level: 1;
        --zoom-duration: 0.3s;
        --edge-threshold: 30px;
        --max-zoom: 3;
        --zoom-increment: 0.5;
        --auto-scroll-speed: 40;
    }

    html, body {
        margin: 0;
        padding: 0;
        overflow: hidden;
        width: 100vw;
        height: 100vh;
    }

    /* Main zoom container */
    .zoom-viewport {
        width: 100vw;
        height: 100vh;
        overflow: hidden;
        position: relative;
        cursor: zoom-in;
    }

    .zoom-viewport.zoomed {
        cursor: grab;
    }

    .zoom-viewport.zoomed:active {
        cursor: grabbing;
    }

    .zoom-viewport.auto-scrolling {
        cursor: ns-resize;
    }

    .zoom-content {
        transform-origin: center center;
        transition: transform var(--zoom-duration) ease-out;
        width: 100%;
        min-height: 100vh;
        padding: 2rem;
        box-sizing: border-box;
    }

    /* Disable transition during auto-scroll for smoothness */
    .zoom-content.scrolling {
        transition: none;
    }

    /* Edge detection visual indicators */
    .edge-indicator {
        position: fixed;
        background: linear-gradient(to var(--direction),
            rgba(74, 144, 226, 0.6),
            transparent);
        opacity: 0;
        transition: opacity 0.2s ease;
        pointer-events: none;
        z-index: 9998;
    }

    .edge-indicator.active {
        opacity: 1;
    }

    .edge-indicator.top {
        --direction: bottom;
        top: 0;
        left: 0;
        right: 0;
        height: 30px;
    }

    .edge-indicator.bottom {
        --direction: top;
        bottom: 0;
        left: 0;
        right: 0;
        height: 30px;
    }

    .edge-indicator.left {
        --direction: right;
        top: 0;
        bottom: 0;
        left: 0;
        width: 30px;
    }

    .edge-indicator.right {
        --direction: left;
        top: 0;
        bottom: 0;
        right: 0;
        width: 30px;
    }

    /* Scroll zone indicators (top/bottom thirds) */
    .scroll-zone {
        position: fixed;
        left: 0;
        right: 0;
        height: 33.33vh;
        pointer-events: none;
        z-index: 9996;
        opacity: 0;
        transition: opacity 0.3s ease;
    }

    .scroll-zone.top {
        top: 0;
        background: linear-gradient(to bottom,
            rgba(74, 144, 226, 0.15),
            transparent);
    }

    .scroll-zone.bottom {
        bottom: 0;
        background: linear-gradient(to top,
            rgba(74, 144, 226, 0.15),
            transparent);
    }

    .scroll-zone.active {
        opacity: 1;
    }

    /* Scroll direction indicator */
    .scroll-indicator {
        position: fixed;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(0, 0, 0, 0.7);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        opacity: 0;
        transition: opacity 0.2s ease;
        pointer-events: none;
        z-index: 9999;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .scroll-indicator.top {
        top: 50px;
    }

    .scroll-indicator.bottom {
        bottom: 50px;
    }

    .scroll-indicator.visible {
        opacity: 1;
    }

    .scroll-indicator .arrow {
        font-size: 1.2rem;
        animation: bounce 0.6s infinite alternate;
    }

    @keyframes bounce {
        from { transform: translateY(-3px); }
        to { transform: translateY(3px); }
    }

    /* Reset notification */
    .zoom-reset-notification {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%) scale(0.8);
        background: rgba(0, 0, 0, 0.85);
        color: white;
        padding: 1.5rem 2.5rem;
        border-radius: 12px;
        font-size: 1.1rem;
        font-weight: 500;
        opacity: 0;
        transition: all 0.3s ease;
        pointer-events: none;
        z-index: 10000;
        text-align: center;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
    }

    .zoom-reset-notification.visible {
        opacity: 1;
        transform: translate(-50%, -50%) scale(1);
    }

    .zoom-reset-notification .icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
        display: block;
    }

    /* Zoom level indicator */
    .zoom-indicator {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 0.75rem 1.25rem;
        border-radius: 8px;
        font-family: monospace;
        font-size: 0.9rem;
        z-index: 9999;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }

    .zoom-indicator .zoom-value {
        font-weight: bold;
        color: #4a90e2;
        min-width: 45px;
    }

    .zoom-indicator .zoom-bar {
        width: 80px;
        height: 6px;
        background: #333;
        border-radius: 3px;
        overflow: hidden;
    }

    .zoom-indicator .zoom-bar-fill {
        height: 100%;
        background: linear-gradient(90deg, #4a90e2, #67b26f);
        border-radius: 3px;
        transition: width 0.3s ease;
    }

    .zoom-indicator .scroll-status {
        font-size: 0.75rem;
        color: #67b26f;
        margin-left: 0.5rem;
    }

    /* AI Areas of Interest markers */
    .ai-interest-marker {
        position: absolute;
        pointer-events: none;
        z-index: 100;
    }

    .ai-interest-marker::before {
        content: '';
        position: absolute;
        top: -10px;
        left: -10px;
        right: -10px;
        bottom: -10px;
        border: 3px solid #f59e0b;
        border-radius: 8px;
        animation: interest-pulse 2s infinite;
        pointer-events: none;
    }

    .ai-interest-marker .marker-label {
        position: absolute;
        top: -35px;
        left: 50%;
        transform: translateX(-50%);
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
        white-space: nowrap;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    }

    @keyframes interest-pulse {
        0%, 100% {
            opacity: 1;
            transform: scale(1);
        }
        50% {
            opacity: 0.6;
            transform: scale(1.02);
        }
    }

    /* Click ripple effect */
    .zoom-ripple {
        position: fixed;
        pointer-events: none;
        border: 2px solid #4a90e2;
        border-radius: 50%;
        animation: ripple-expand 0.6s ease-out forwards;
        z-index: 9997;
    }

    @keyframes ripple-expand {
        0% {
            width: 0;
            height: 0;
            opacity: 1;
        }
        100% {
            width: 100px;
            height: 100px;
            opacity: 0;
        }
    }

    /* Demo content styling */
    .demo-container {
        max-width: 1200px;
        margin: 0 auto;
    }

    .demo-header {
        text-align: center;
        margin-bottom: 2rem;
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        color: white;
    }

    .demo-header h1 {
        margin: 0 0 0.5rem 0;
        font-size: 2rem;
    }

    .demo-header p {
        margin: 0;
        opacity: 0.9;
    }

    .feature-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 20px;
        font-size: 0.85rem;
        margin-top: 1rem;
    }

    /* Instructions panel */
    .instructions-panel {
        background: var(--pico-card-background-color);
        border: 1px solid var(--pico-muted-border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 2rem;
    }

    .instructions-panel h3 {
        margin: 0 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .instruction-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
    }

    .instruction-item {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        padding: 1rem;
        background: var(--pico-secondary-background);
        border-radius: 8px;
    }

    .instruction-icon {
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--pico-primary);
        color: white;
        border-radius: 8px;
        font-size: 1.2rem;
        flex-shrink: 0;
    }

    .instruction-text h4 {
        margin: 0 0 0.25rem 0;
        font-size: 0.95rem;
    }

    .instruction-text p {
        margin: 0;
        font-size: 0.85rem;
        color: var(--pico-muted-color);
    }

    /* Sample content areas */
    .content-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
        margin-bottom: 2rem;
    }

    .content-card {
        background: var(--pico-card-background-color);
        border: 1px solid var(--pico-muted-border-color);
        border-radius: 12px;
        padding: 1.5rem;
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .content-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    }

    .content-card h4 {
        margin: 0 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .content-card p {
        margin: 0 0 1rem 0;
        color: var(--pico-muted-color);
        font-size: 0.9rem;
        line-height: 1.6;
    }

    /* AI Integration section */
    .ai-section {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        border-radius: 12px;
        padding: 1.5rem;
        color: white;
        margin-bottom: 2rem;
    }

    .ai-section h3 {
        margin: 0 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .ai-section p {
        margin: 0 0 1rem 0;
        opacity: 0.95;
    }

    .ai-controls {
        display: flex;
        gap: 0.75rem;
        flex-wrap: wrap;
    }

    .ai-controls button {
        background: rgba(255, 255, 255, 0.2);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 0.5rem 1rem;
        border-radius: 6px;
        cursor: pointer;
        transition: background 0.2s;
        font-size: 0.9rem;
    }

    .ai-controls button:hover {
        background: rgba(255, 255, 255, 0.3);
    }

    /* Accessibility controls */
    .accessibility-controls {
        position: fixed;
        top: 20px;
        left: 20px;
        background: rgba(0, 0, 0, 0.8);
        padding: 1rem;
        border-radius: 12px;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .accessibility-controls label {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: white;
        font-size: 0.85rem;
        cursor: pointer;
    }

    .accessibility-controls input[type="checkbox"] {
        width: 18px;
        height: 18px;
    }

    .accessibility-controls input[type="range"] {
        width: 100px;
    }

    /* Toggle button for controls */
    .controls-toggle {
        position: fixed;
        top: 20px;
        left: 20px;
        width: 45px;
        height: 45px;
        background: rgba(0, 0, 0, 0.8);
        color: white;
        border: none;
        border-radius: 50%;
        cursor: pointer;
        z-index: 10001;
        font-size: 1.2rem;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: background 0.2s;
    }

    .controls-toggle:hover {
        background: rgba(0, 0, 0, 0.9);
    }

    .accessibility-controls.hidden {
        display: none;
    }

    /* Fine detail content styles */
    .microprint-card {
        background: #fafafa;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
    }

    .microprint-text {
        font-size: 4px;
        line-height: 1.4;
        color: #333;
        font-family: 'Times New Roman', serif;
        text-align: justify;
        margin-bottom: 0.5rem;
    }

    .fine-print-legal {
        font-size: 5px;
        color: #666;
        line-height: 1.3;
        border-top: 1px solid #ddd;
        padding-top: 0.5rem;
        margin-top: 0.5rem;
    }

    /* Circuit diagram styles */
    .circuit-diagram {
        background: #1a1a2e;
        border-radius: 8px;
        padding: 1rem;
        font-family: monospace;
    }

    .circuit-grid {
        display: grid;
        grid-template-columns: repeat(20, 1fr);
        gap: 1px;
        font-size: 3px;
        color: #00ff88;
        line-height: 1;
    }

    .circuit-cell {
        width: 8px;
        height: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 0.5px solid #333;
    }

    .circuit-cell.active {
        background: rgba(0, 255, 136, 0.2);
    }

    .circuit-labels {
        display: flex;
        justify-content: space-between;
        font-size: 3px;
        color: #888;
        margin-top: 4px;
    }

    /* Detailed data visualization */
    .data-matrix {
        font-family: monospace;
        font-size: 4px;
        line-height: 1.2;
        background: #f5f5f5;
        padding: 0.5rem;
        border-radius: 4px;
        overflow: hidden;
    }

    .matrix-row {
        display: flex;
        gap: 2px;
    }

    .matrix-cell {
        width: 12px;
        text-align: right;
        color: #333;
    }

    .matrix-header {
        font-weight: bold;
        color: #0066cc;
        border-bottom: 0.5px solid #ccc;
        margin-bottom: 2px;
        padding-bottom: 2px;
    }

    /* Fine map details */
    .map-container {
        background: #e8f4e8;
        border-radius: 8px;
        padding: 0.5rem;
        position: relative;
    }

    .map-grid {
        display: grid;
        grid-template-columns: repeat(30, 1fr);
        grid-template-rows: repeat(20, 1fr);
        gap: 0;
        height: 150px;
        border: 1px solid #999;
        background: linear-gradient(135deg, #d4e4d4 0%, #c4d4c4 100%);
    }

    .map-point {
        font-size: 2px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #333;
    }

    .map-point.city {
        background: #ff6b6b;
        color: white;
        font-weight: bold;
    }

    .map-point.road {
        background: #ffd93d;
    }

    .map-point.water {
        background: #6bcfff;
    }

    .map-legend {
        display: flex;
        gap: 8px;
        margin-top: 4px;
        font-size: 4px;
    }

    .legend-item {
        display: flex;
        align-items: center;
        gap: 2px;
    }

    .legend-color {
        width: 6px;
        height: 6px;
        border-radius: 1px;
    }

    /* Microscopic text sample */
    .specimen-card {
        background: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
    }

    .specimen-header {
        font-size: 6px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #333;
        border-bottom: 0.5px solid #ccc;
        padding-bottom: 4px;
        margin-bottom: 6px;
    }

    .specimen-data {
        font-size: 3.5px;
        line-height: 1.5;
        color: #444;
    }

    .specimen-row {
        display: flex;
        justify-content: space-between;
        border-bottom: 0.25px dotted #ddd;
        padding: 1px 0;
    }

    .specimen-label {
        color: #666;
    }

    .specimen-value {
        font-weight: bold;
        color: #222;
    }

    /* DNA sequence display */
    .dna-sequence {
        font-family: 'Courier New', monospace;
        font-size: 3px;
        letter-spacing: 0.5px;
        line-height: 1.4;
        background: #1e1e1e;
        color: #00ff00;
        padding: 0.5rem;
        border-radius: 4px;
        word-break: break-all;
    }

    .dna-sequence .adenine { color: #ff6b6b; }
    .dna-sequence .thymine { color: #4ecdc4; }
    .dna-sequence .guanine { color: #ffe66d; }
    .dna-sequence .cytosine { color: #95e1d3; }

    .sequence-position {
        color: #666;
        font-size: 2.5px;
    }

    /* Currency detail */
    .currency-detail {
        background: linear-gradient(135deg, #f0f7f0 0%, #e8f0e8 100%);
        border: 2px solid #2d5a2d;
        border-radius: 8px;
        padding: 1rem;
        position: relative;
    }

    .currency-pattern {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-image: repeating-linear-gradient(
            45deg,
            transparent,
            transparent 2px,
            rgba(0,100,0,0.03) 2px,
            rgba(0,100,0,0.03) 4px
        );
        pointer-events: none;
    }

    .currency-serial {
        font-family: 'OCR A Extended', monospace;
        font-size: 4px;
        letter-spacing: 1px;
        color: #1a3a1a;
    }

    .currency-microtext {
        font-size: 2px;
        color: #2d5a2d;
        text-transform: uppercase;
        letter-spacing: 0.3px;
        line-height: 1.2;
        margin-top: 6px;
    }

    .security-thread {
        height: 3px;
        background: repeating-linear-gradient(
            90deg,
            #2d5a2d 0px,
            #2d5a2d 4px,
            transparent 4px,
            transparent 6px
        );
        margin: 4px 0;
        font-size: 1.5px;
        color: #fff;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* Fingerprint pattern */
    .fingerprint-container {
        background: #f5f5f5;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }

    .fingerprint-svg {
        max-width: 100%;
        height: auto;
    }

    .fingerprint-data {
        font-size: 3px;
        color: #666;
        margin-top: 6px;
        font-family: monospace;
    }
""")

# JavaScript for zoom functionality with auto-scroll
auto_zoom_js = Script("""
// Automated Zoom Accessibility Feature with Auto-Scroll
const AutoZoom = {
    // Configuration
    config: {
        zoomEnabled: true,
        zoomLevel: 1,
        maxZoom: 3,
        minZoom: 1,
        zoomIncrement: 0.5,
        edgeThreshold: 30,
        edgeReset: true,
        panEnabled: true,
        autoScrollEnabled: true,
        autoScrollSpeed: 2
    },

    // State
    state: {
        isZoomed: false,
        isDragging: false,
        lastMouseX: 0,
        lastMouseY: 0,
        translateX: 0,
        translateY: 0,
        zoomOriginX: 50,
        zoomOriginY: 50,
        aiMarkers: [],
        // Auto-scroll state
        isAutoScrolling: false,
        scrollDirection: null,
        scrollAnimationId: null,
        contentScrollY: 0,
        maxScrollY: 0
    },

    // DOM elements
    elements: {
        viewport: null,
        content: null,
        indicator: null,
        notification: null,
        edges: {},
        scrollZones: {},
        scrollIndicators: {}
    },

    // Initialize the zoom feature
    init() {
        this.cacheElements();
        this.calculateScrollBounds();
        this.bindEvents();
        this.updateIndicator();
        console.log('[AutoZoom] Initialized - Click to zoom, edges to reset, top/bottom zones to scroll');
    },

    // Cache DOM elements
    cacheElements() {
        this.elements.viewport = document.querySelector('.zoom-viewport');
        this.elements.content = document.querySelector('.zoom-content');
        this.elements.indicator = document.querySelector('.zoom-indicator');
        this.elements.notification = document.querySelector('.zoom-reset-notification');
        this.elements.edges = {
            top: document.querySelector('.edge-indicator.top'),
            bottom: document.querySelector('.edge-indicator.bottom'),
            left: document.querySelector('.edge-indicator.left'),
            right: document.querySelector('.edge-indicator.right')
        };
        this.elements.scrollZones = {
            top: document.querySelector('.scroll-zone.top'),
            bottom: document.querySelector('.scroll-zone.bottom')
        };
        this.elements.scrollIndicators = {
            top: document.querySelector('.scroll-indicator.top'),
            bottom: document.querySelector('.scroll-indicator.bottom')
        };
    },

    // Calculate maximum scroll bounds
    calculateScrollBounds() {
        if (!this.elements.content || !this.elements.viewport) return;

        const contentHeight = this.elements.content.scrollHeight;
        const viewportHeight = this.elements.viewport.clientHeight;
        this.state.maxScrollY = Math.max(0, contentHeight - viewportHeight);
    },

    // Bind all event listeners
    bindEvents() {
        // Click to zoom
        this.elements.viewport.addEventListener('click', (e) => this.handleClick(e));

        // Mouse move for edge detection, panning, and auto-scroll zones
        document.addEventListener('mousemove', (e) => this.handleMouseMove(e));

        // Drag events for panning when zoomed
        this.elements.viewport.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        document.addEventListener('mouseup', () => this.handleMouseUp());

        // Mouse leave to stop auto-scroll
        document.addEventListener('mouseleave', () => this.stopAutoScroll());

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));

        // Touch events for mobile
        this.elements.viewport.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: false });
        this.elements.viewport.addEventListener('touchmove', (e) => this.handleTouchMove(e), { passive: false });
        this.elements.viewport.addEventListener('touchend', () => this.handleTouchEnd());

        // Settings checkboxes
        document.querySelectorAll('.zoom-setting').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => this.handleSettingChange(e));
        });

        // Zoom slider
        const zoomSlider = document.getElementById('zoom-increment-slider');
        if (zoomSlider) {
            zoomSlider.addEventListener('input', (e) => {
                this.config.zoomIncrement = parseFloat(e.target.value);
                document.getElementById('zoom-increment-value').textContent = e.target.value + 'x';
            });
        }

        // Scroll speed slider
        const scrollSlider = document.getElementById('scroll-speed-slider');
        if (scrollSlider) {
            scrollSlider.addEventListener('input', (e) => {
                this.config.autoScrollSpeed = parseFloat(e.target.value);
                document.getElementById('scroll-speed-value').textContent = e.target.value + 'x';
            });
        }

        // Recalculate bounds on resize
        window.addEventListener('resize', () => this.calculateScrollBounds());
    },

    // Handle click to zoom - uses exact pixel coordinates for transform origin
    handleClick(e) {
        if (!this.config.zoomEnabled) return;
        if (this.state.isDragging) return;
        if (this.state.isAutoScrolling) return;

        // Prevent zoom on buttons/links
        if (e.target.closest('button, a, input, .ai-controls')) return;

        // Get the exact click position relative to the content element
        const contentRect = this.elements.content.getBoundingClientRect();

        // Calculate exact pixel position within the content
        // This is where the mouse clicked, accounting for current scroll
        const clickX = e.clientX - contentRect.left;
        const clickY = e.clientY - contentRect.top + this.state.contentScrollY;

        // Create ripple effect at click location
        this.createRipple(e.clientX, e.clientY);

        // Zoom in at exact click point using pixel coordinates
        if (this.config.zoomLevel < this.config.maxZoom) {
            this.config.zoomLevel = Math.min(this.config.maxZoom, this.config.zoomLevel + this.config.zoomIncrement);

            // Store exact pixel coordinates for transform origin
            this.state.zoomOriginX = clickX;
            this.state.zoomOriginY = clickY;
            this.state.isZoomed = true;
            this.elements.viewport.classList.add('zoomed');
        }

        this.applyZoom();
        this.updateIndicator();
    },

    // Create visual ripple effect on click
    createRipple(x, y) {
        const ripple = document.createElement('div');
        ripple.className = 'zoom-ripple';
        ripple.style.left = (x - 50) + 'px';
        ripple.style.top = (y - 50) + 'px';
        document.body.appendChild(ripple);

        setTimeout(() => ripple.remove(), 600);
    },

    // Handle mouse movement for edge detection, panning, and auto-scroll
    handleMouseMove(e) {
        // Panning when zoomed and dragging
        if (this.state.isZoomed && this.state.isDragging && this.config.panEnabled) {
            const deltaX = e.clientX - this.state.lastMouseX;
            const deltaY = e.clientY - this.state.lastMouseY;

            this.state.translateX += deltaX;
            this.state.translateY += deltaY;

            this.state.lastMouseX = e.clientX;
            this.state.lastMouseY = e.clientY;

            this.applyZoom();
            return;
        }

        // Edge detection for zoom reset (only when zoomed)
        if (this.config.edgeReset && this.state.isZoomed) {
            if (this.checkEdgesForReset(e.clientX, e.clientY)) {
                return; // Reset triggered, don't process auto-scroll
            }
        }

        // Auto-scroll zones (when NOT zoomed)
        if (this.config.autoScrollEnabled && !this.state.isZoomed) {
            this.checkAutoScrollZones(e.clientY);
        }
    },

    // Check if mouse is near edges for zoom reset (all four edges)
    checkEdgesForReset(mouseX, mouseY) {
        const threshold = this.config.edgeThreshold;
        const width = window.innerWidth;
        const height = window.innerHeight;

        const nearTop = mouseY <= threshold;
        const nearBottom = mouseY >= height - threshold;
        const nearLeft = mouseX <= threshold;
        const nearRight = mouseX >= width - threshold;

        // Update edge indicators
        this.elements.edges.top?.classList.toggle('active', nearTop);
        this.elements.edges.bottom?.classList.toggle('active', nearBottom);
        this.elements.edges.left?.classList.toggle('active', nearLeft);
        this.elements.edges.right?.classList.toggle('active', nearRight);

        // Reset zoom when touching any edge
        if (nearTop || nearBottom || nearLeft || nearRight) {
            this.resetZoom();
            return true;
        }
        return false;
    },

    // Check auto-scroll zones (top/bottom thirds of screen)
    checkAutoScrollZones(mouseY) {
        const height = window.innerHeight;
        const topZoneEnd = height / 3;
        const bottomZoneStart = height * 2 / 3;

        const inTopZone = mouseY < topZoneEnd;
        const inBottomZone = mouseY > bottomZoneStart;

        // Update zone visuals
        this.elements.scrollZones.top?.classList.toggle('active', inTopZone && this.state.contentScrollY > 0);
        this.elements.scrollZones.bottom?.classList.toggle('active', inBottomZone && this.state.contentScrollY < this.state.maxScrollY);

        if (inTopZone && this.state.contentScrollY > 0) {
            this.startAutoScroll('up');
        } else if (inBottomZone && this.state.contentScrollY < this.state.maxScrollY) {
            this.startAutoScroll('down');
        } else {
            this.stopAutoScroll();
        }
    },

    // Start auto-scrolling
    startAutoScroll(direction) {
        if (this.state.isAutoScrolling && this.state.scrollDirection === direction) return;

        this.state.isAutoScrolling = true;
        this.state.scrollDirection = direction;
        this.elements.viewport.classList.add('auto-scrolling');
        this.elements.content.classList.add('scrolling');

        // Show scroll indicator
        const indicator = direction === 'up' ? this.elements.scrollIndicators.top : this.elements.scrollIndicators.bottom;
        indicator?.classList.add('visible');

        // Update indicator status
        const statusEl = this.elements.indicator?.querySelector('.scroll-status');
        if (statusEl) {
            statusEl.textContent = direction === 'up' ? 'Scrolling up' : 'Scrolling down';
            statusEl.style.display = 'inline';
        }

        this.animateScroll();
    },

    // Stop auto-scrolling
    stopAutoScroll() {
        if (!this.state.isAutoScrolling) return;

        this.state.isAutoScrolling = false;
        this.state.scrollDirection = null;
        this.elements.viewport.classList.remove('auto-scrolling');
        this.elements.content.classList.remove('scrolling');

        if (this.state.scrollAnimationId) {
            cancelAnimationFrame(this.state.scrollAnimationId);
            this.state.scrollAnimationId = null;
        }

        // Hide scroll indicators
        this.elements.scrollIndicators.top?.classList.remove('visible');
        this.elements.scrollIndicators.bottom?.classList.remove('visible');
        this.elements.scrollZones.top?.classList.remove('active');
        this.elements.scrollZones.bottom?.classList.remove('active');

        // Update indicator status
        const statusEl = this.elements.indicator?.querySelector('.scroll-status');
        if (statusEl) {
            statusEl.style.display = 'none';
        }
    },

    // Animate the scroll
    animateScroll() {
        if (!this.state.isAutoScrolling) return;

        const speed = this.config.autoScrollSpeed;
        const delta = this.state.scrollDirection === 'up' ? -speed : speed;

        this.state.contentScrollY = Math.max(0, Math.min(this.state.maxScrollY, this.state.contentScrollY + delta));

        // Apply scroll via transform
        this.elements.content.style.transform = `translateY(${-this.state.contentScrollY}px)`;

        // Check bounds and stop if at limits
        if ((this.state.scrollDirection === 'up' && this.state.contentScrollY <= 0) ||
            (this.state.scrollDirection === 'down' && this.state.contentScrollY >= this.state.maxScrollY)) {
            this.stopAutoScroll();
            return;
        }

        this.state.scrollAnimationId = requestAnimationFrame(() => this.animateScroll());
    },

    // Handle mouse down for panning
    handleMouseDown(e) {
        if (this.state.isZoomed && this.config.panEnabled) {
            this.state.isDragging = true;
            this.state.lastMouseX = e.clientX;
            this.state.lastMouseY = e.clientY;
            e.preventDefault();
        }
    },

    // Handle mouse up
    handleMouseUp() {
        this.state.isDragging = false;
    },

    // Handle touch events
    handleTouchStart(e) {
        if (!this.config.zoomEnabled) return;

        if (e.touches.length === 1) {
            const touch = e.touches[0];

            if (!this.state.isZoomed) {
                // Zoom in on tap
                this.handleClick({ clientX: touch.clientX, clientY: touch.clientY, target: e.target });
            } else {
                // Start panning
                this.state.isDragging = true;
                this.state.lastMouseX = touch.clientX;
                this.state.lastMouseY = touch.clientY;
            }
        }
    },

    handleTouchMove(e) {
        if (!this.state.isZoomed || !this.state.isDragging) return;

        if (e.touches.length === 1) {
            const touch = e.touches[0];
            const deltaX = touch.clientX - this.state.lastMouseX;
            const deltaY = touch.clientY - this.state.lastMouseY;

            this.state.translateX += deltaX;
            this.state.translateY += deltaY;

            this.state.lastMouseX = touch.clientX;
            this.state.lastMouseY = touch.clientY;

            this.applyZoom();

            // Check edges for reset
            this.checkEdgesForReset(touch.clientX, touch.clientY);

            e.preventDefault();
        }
    },

    handleTouchEnd() {
        this.state.isDragging = false;
    },

    // Handle keyboard shortcuts
    handleKeyboard(e) {
        switch(e.key) {
            case 'Escape':
                this.resetZoom();
                break;
            case '+':
            case '=':
                if (this.config.zoomEnabled && this.config.zoomLevel < this.config.maxZoom) {
                    this.config.zoomLevel = Math.min(this.config.maxZoom, this.config.zoomLevel + this.config.zoomIncrement);
                    this.state.isZoomed = true;
                    this.elements.viewport.classList.add('zoomed');
                    this.applyZoom();
                    this.updateIndicator();
                }
                break;
            case '-':
                if (this.config.zoomLevel > this.config.minZoom) {
                    this.config.zoomLevel = Math.max(this.config.minZoom, this.config.zoomLevel - this.config.zoomIncrement);
                    if (this.config.zoomLevel === 1) {
                        this.resetZoom();
                    } else {
                        this.applyZoom();
                        this.updateIndicator();
                    }
                }
                break;
            case '0':
                this.resetZoom();
                break;
            case 'ArrowUp':
                if (!this.state.isZoomed) {
                    this.state.contentScrollY = Math.max(0, this.state.contentScrollY - 50);
                    this.elements.content.style.transform = `translateY(${-this.state.contentScrollY}px)`;
                    e.preventDefault();
                }
                break;
            case 'ArrowDown':
                if (!this.state.isZoomed) {
                    this.state.contentScrollY = Math.min(this.state.maxScrollY, this.state.contentScrollY + 50);
                    this.elements.content.style.transform = `translateY(${-this.state.contentScrollY}px)`;
                    e.preventDefault();
                }
                break;
        }
    },

    // Apply zoom transformation using exact pixel coordinates for transform origin
    applyZoom() {
        if (!this.elements.content) return;

        const zoom = this.config.zoomLevel;
        const originX = this.state.zoomOriginX;
        const originY = this.state.zoomOriginY;
        const translateX = this.state.translateX;
        const translateY = this.state.translateY;

        if (this.state.isZoomed) {
            // Set transform origin to exact pixel coordinates where user clicked
            // This ensures the zoom centers precisely on the clicked location
            this.elements.content.style.transformOrigin = `${originX}px ${originY}px`;
            this.elements.content.style.transform = `scale(${zoom}) translate(${translateX / zoom}px, ${translateY / zoom}px)`;
        } else {
            // In normal view, reset origin and apply scroll translation
            this.elements.content.style.transformOrigin = '0 0';
            this.elements.content.style.transform = `translateY(${-this.state.contentScrollY}px)`;
        }
    },

    // Reset zoom to normal view
    resetZoom() {
        if (!this.state.isZoomed) return;

        this.config.zoomLevel = 1;
        this.state.isZoomed = false;
        this.state.translateX = 0;
        this.state.translateY = 0;
        this.state.zoomOriginX = 0;
        this.state.zoomOriginY = 0;

        this.elements.viewport?.classList.remove('zoomed');

        // Clear edge indicators
        Object.values(this.elements.edges).forEach(edge => {
            edge?.classList.remove('active');
        });

        this.applyZoom();
        this.updateIndicator();
        this.showNotification('View Reset');
    },

    // Update zoom level indicator
    updateIndicator() {
        if (!this.elements.indicator) return;

        const zoomValue = this.elements.indicator.querySelector('.zoom-value');
        const zoomBarFill = this.elements.indicator.querySelector('.zoom-bar-fill');

        if (zoomValue) {
            zoomValue.textContent = this.config.zoomLevel.toFixed(1) + 'x';
        }

        if (zoomBarFill) {
            const percentage = ((this.config.zoomLevel - 1) / (this.config.maxZoom - 1)) * 100;
            zoomBarFill.style.width = percentage + '%';
        }
    },

    // Show notification
    showNotification(message) {
        if (!this.elements.notification) return;

        this.elements.notification.querySelector('.message').textContent = message;
        this.elements.notification.classList.add('visible');

        setTimeout(() => {
            this.elements.notification.classList.remove('visible');
        }, 1500);
    },

    // Handle settings change
    handleSettingChange(e) {
        const setting = e.target.dataset.setting;
        const value = e.target.checked;

        switch(setting) {
            case 'zoomEnabled':
                this.config.zoomEnabled = value;
                if (!value) this.resetZoom();
                break;
            case 'edgeReset':
                this.config.edgeReset = value;
                break;
            case 'panEnabled':
                this.config.panEnabled = value;
                break;
            case 'autoScrollEnabled':
                this.config.autoScrollEnabled = value;
                if (!value) this.stopAutoScroll();
                break;
        }
    },

    // AI Agent Integration Methods

    // Register an area of interest (for AI agents to call)
    registerAreaOfInterest(elementSelector, label = 'Area of Interest') {
        const element = document.querySelector(elementSelector);
        if (!element) {
            console.warn('[AutoZoom] Element not found:', elementSelector);
            return null;
        }

        const marker = document.createElement('div');
        marker.className = 'ai-interest-marker';
        marker.innerHTML = `<span class="marker-label">${label}</span>`;

        // Position relative to element
        const rect = element.getBoundingClientRect();
        const contentRect = this.elements.content.getBoundingClientRect();

        marker.style.left = (rect.left - contentRect.left) + 'px';
        marker.style.top = (rect.top - contentRect.top) + 'px';
        marker.style.width = rect.width + 'px';
        marker.style.height = rect.height + 'px';

        element.style.position = 'relative';
        element.appendChild(marker);

        const markerId = 'ai-marker-' + Date.now();
        marker.id = markerId;
        this.state.aiMarkers.push({ id: markerId, element, marker, label });

        return markerId;
    },

    // Auto-zoom to an area of interest using exact pixel coordinates
    zoomToElement(elementSelector, zoomLevel = 2) {
        const element = document.querySelector(elementSelector);
        if (!element) {
            console.warn('[AutoZoom] Element not found:', elementSelector);
            return;
        }

        const rect = element.getBoundingClientRect();
        const contentRect = this.elements.content.getBoundingClientRect();

        // Calculate exact pixel position of element center within content
        const elementCenterX = rect.left - contentRect.left + rect.width / 2;
        const elementCenterY = rect.top - contentRect.top + this.state.contentScrollY + rect.height / 2;

        this.config.zoomLevel = Math.min(zoomLevel, this.config.maxZoom);
        // Store exact pixel coordinates for transform origin
        this.state.zoomOriginX = elementCenterX;
        this.state.zoomOriginY = elementCenterY;
        this.state.isZoomed = true;
        this.state.translateX = 0;
        this.state.translateY = 0;

        this.elements.viewport.classList.add('zoomed');
        this.applyZoom();
        this.updateIndicator();

        this.showNotification('AI: Focusing on area');
    },

    // Clear all AI markers
    clearMarkers() {
        this.state.aiMarkers.forEach(({ marker }) => {
            marker.remove();
        });
        this.state.aiMarkers = [];
    },

    // Get current zoom state (for AI agents to query)
    getState() {
        return {
            isZoomed: this.state.isZoomed,
            zoomLevel: this.config.zoomLevel,
            origin: { x: this.state.zoomOriginX, y: this.state.zoomOriginY },
            translate: { x: this.state.translateX, y: this.state.translateY },
            scrollY: this.state.contentScrollY
        };
    },

    // Toggle controls panel
    toggleControls() {
        const controls = document.querySelector('.accessibility-controls');
        if (controls) {
            controls.classList.toggle('hidden');
        }
    }
};

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => AutoZoom.init());
} else {
    AutoZoom.init();
}

// Expose to global scope for AI agent integration
window.AutoZoom = AutoZoom;
""", type='module')

app, rt = fast_app(hdrs=[auto_zoom_styles, auto_zoom_js])


def ZoomIndicator():
    """Zoom level indicator widget."""
    return Div(
        Span("Zoom: "),
        Span("1.0x", cls='zoom-value'),
        Div(
            Div(cls='zoom-bar-fill', style='width: 0%'),
            cls='zoom-bar'
        ),
        Span("", cls='scroll-status', style='display: none;'),
        cls='zoom-indicator'
    )


def EdgeIndicators():
    """Edge detection visual indicators for zoom reset."""
    return (
        Div(cls='edge-indicator top'),
        Div(cls='edge-indicator bottom'),
        Div(cls='edge-indicator left'),
        Div(cls='edge-indicator right')
    )


def ScrollZones():
    """Auto-scroll zone indicators."""
    return (
        Div(cls='scroll-zone top'),
        Div(cls='scroll-zone bottom'),
        Div(
            Span("^", cls='arrow'),
            Span("Scrolling Up"),
            cls='scroll-indicator top'
        ),
        Div(
            Span("Scrolling Down"),
            Span("v", cls='arrow'),
            cls='scroll-indicator bottom'
        )
    )


def ResetNotification():
    """Notification shown when zoom resets."""
    return Div(
        Span("", cls='icon'),
        Span("View Reset", cls='message'),
        cls='zoom-reset-notification'
    )


def AccessibilityControls():
    """Floating accessibility control panel with simplified settings."""
    return (
        Button("", onclick="AutoZoom.toggleControls()", cls='controls-toggle', title='Toggle Controls'),
        Div(
            H4("Accessibility Settings", style='margin: 0 0 0.75rem 0; color: white;'),
            Label(
                Input(type='checkbox', checked=True, cls='zoom-setting', data_setting='zoomEnabled'),
                "Enable Click-to-Zoom"
            ),
            Label(
                Input(type='checkbox', checked=True, cls='zoom-setting', data_setting='edgeReset'),
                "Edge Reset (all edges)"
            ),
            Label(
                Input(type='checkbox', checked=True, cls='zoom-setting', data_setting='panEnabled'),
                "Pan When Zoomed"
            ),
            Label(
                Input(type='checkbox', checked=True, cls='zoom-setting', data_setting='autoScrollEnabled'),
                "Auto-Scroll (top/bottom zones)"
            ),
            Div(
                Label("Zoom Step: ", Span("0.5x", id='zoom-increment-value'), style='margin-bottom: 0.25rem;'),
                Input(type='range', min='0.25', max='1', step='0.25', value='0.5', id='zoom-increment-slider'),
                style='margin-top: 0.5rem;'
            ),
            Div(
                Label("Scroll Speed: ", Span("2x", id='scroll-speed-value'), style='margin-bottom: 0.25rem;'),
                Input(type='range', min='1', max='5', step='0.5', value='2', id='scroll-speed-slider'),
                style='margin-top: 0.5rem;'
            ),
            cls='accessibility-controls'
        )
    )


def InstructionsPanel():
    """Panel showing usage instructions."""
    return Div(
        H3("How to Use"),
        Div(
            Div(
                Div("+", cls='instruction-icon'),
                Div(
                    H4("Click to Zoom"),
                    P("Click anywhere on the page to zoom into that area for detailed viewing."),
                    cls='instruction-text'
                ),
                cls='instruction-item'
            ),
            Div(
                Div("[ ]", cls='instruction-icon'),
                Div(
                    H4("Edge Reset"),
                    P("Move mouse to any screen edge to instantly reset zoom to normal view."),
                    cls='instruction-text'
                ),
                cls='instruction-item'
            ),
            Div(
                Div("^v", cls='instruction-icon'),
                Div(
                    H4("Auto-Scroll"),
                    P("In normal view, move mouse to top or bottom third of screen to auto-scroll."),
                    cls='instruction-text'
                ),
                cls='instruction-item'
            ),
            Div(
                Div("", cls='instruction-icon'),
                Div(
                    H4("Pan Around"),
                    P("When zoomed, click and drag to navigate the magnified view."),
                    cls='instruction-text'
                ),
                cls='instruction-item'
            ),
            cls='instruction-grid'
        ),
        cls='instructions-panel'
    )


def AIIntegrationSection():
    """Section demonstrating AI agent integration."""
    return Div(
        H3("AI Agent Integration"),
        P("AI agents can programmatically zoom to areas of interest, helping users discover "
          "important details they might otherwise miss."),
        Div(
            Button("Zoom to Microprint", onclick="AutoZoom.zoomToElement('.microprint-card', 3)"),
            Button("Zoom to Circuit", onclick="AutoZoom.zoomToElement('.circuit-diagram', 3)"),
            Button("Zoom to DNA Sequence", onclick="AutoZoom.zoomToElement('.dna-sequence', 3)"),
            Button("Zoom to Currency Detail", onclick="AutoZoom.zoomToElement('.currency-detail', 3)"),
            Button("Mark Fine Print", onclick="AutoZoom.registerAreaOfInterest('.fine-print-legal', 'Legal Text')"),
            Button("Clear Markers", onclick="AutoZoom.clearMarkers()"),
            Button("Reset View", onclick="AutoZoom.resetZoom()"),
            cls='ai-controls'
        ),
        cls='ai-section',
        id='ai-section'
    )


def MicroprintSample():
    """Sample with extremely small text that requires zoom to read."""
    return Div(
        H4("Legal Document with Microprint"),
        P("This card contains text so small it cannot be read without zooming. Click to magnify."),
        Div(
            Div(
                "TERMS AND CONDITIONS: By accessing this document, you acknowledge and agree to be bound by all terms herein. "
                "Section 1.1: The licensor grants to licensee a non-exclusive, non-transferable right to use the software. "
                "Section 1.2: Licensee shall not reverse engineer, decompile, or disassemble the software. "
                "Section 2.1: This agreement shall be governed by the laws of the jurisdiction. "
                "Section 2.2: Any disputes arising shall be resolved through binding arbitration. "
                "Section 3.1: The software is provided 'as is' without warranty of any kind. "
                "Section 3.2: In no event shall the licensor be liable for any damages whatsoever. "
                "Section 4.1: This agreement constitutes the entire understanding between parties. "
                "Section 4.2: No modification shall be effective unless in writing signed by both parties.",
                cls='microprint-text'
            ),
            Div(
                "FINE PRINT NOTICE: This notice contains important information regarding your rights and obligations. "
                "Failure to read and understand these terms does not release you from your obligations hereunder. "
                "All rights reserved. Patent pending. Void where prohibited. Some restrictions may apply. "
                "See official rules for complete details. No purchase necessary to enter or win. "
                "Estimated retail value varies by location. Allow 6-8 weeks for delivery.",
                cls='fine-print-legal'
            ),
            cls='microprint-card'
        ),
        cls='content-card',
        id='microprint-card'
    )


def CircuitDiagramSample():
    """Sample circuit diagram with fine details."""
    circuit_chars = ['R', 'C', 'L', '+', '-', '|', '-', 'o', 'T', 'D', 'G', 'S', 'V', 'I', 'A', 'W']
    cells = []
    for i in range(400):  # 20x20 grid
        is_active = i % 7 == 0 or i % 13 == 0
        char = circuit_chars[i % len(circuit_chars)] if is_active else '.'
        cells.append(Div(char, cls=f'circuit-cell{"" if not is_active else " active"}'))

    return Div(
        H4("Integrated Circuit Schematic"),
        P("Detailed IC pinout diagram. Zoom in to read component values and trace connections."),
        Div(
            Div(*cells, cls='circuit-grid'),
            Div(
                Span("PIN 1-20: VCC GND D0-D7 A0-A7 CLK RST"),
                Span("REV 2.3.1 | 45nm CMOS"),
                cls='circuit-labels'
            ),
            cls='circuit-diagram'
        ),
        cls='content-card',
        id='circuit-card'
    )


def DataMatrixSample():
    """Dense data matrix that requires zoom."""
    rows = []
    headers = ['ID', 'X', 'Y', 'Z', 'Val', 'Err', 'Sig', 'P', 'N', 'Conf']
    rows.append(Div(*[Span(h, cls='matrix-cell') for h in headers], cls='matrix-row matrix-header'))

    import random
    random.seed(42)
    for i in range(25):
        row_data = [f'{i+1:03d}'] + [f'{random.uniform(-1, 1):.3f}' for _ in range(9)]
        rows.append(Div(*[Span(d, cls='matrix-cell') for d in row_data], cls='matrix-row'))

    return Div(
        H4("Scientific Data Matrix"),
        P("Statistical analysis results. Contains 250 data points across 10 variables."),
        Div(*rows, cls='data-matrix'),
        cls='content-card',
        id='data-card'
    )


def DNASequenceSample():
    """DNA sequence with color-coded bases."""
    sequence = "ATGCGATCGATCGATCGAATTCCGGAATTCCGGAATTCCGGAATTCCGGATGCGATCGATCGATCGAATTCCGGAATTCCGGAATTCCGGAATTCCGGATGCGATCGATCGATCGAATTCCGGAATTCCGGAATTCCGGAATTCCGGATGCGATCGATCGATCGAATTCCGGAATTCCGGAATTCCGGAATTCCGGATGCGATCGATCGATCGAATTCCGGAATTCCGG"

    elements = [Span("001: ", cls='sequence-position')]
    for i, base in enumerate(sequence):
        cls_map = {'A': 'adenine', 'T': 'thymine', 'G': 'guanine', 'C': 'cytosine'}
        elements.append(Span(base, cls=cls_map.get(base, '')))
        if (i + 1) % 60 == 0 and i < len(sequence) - 1:
            elements.append(Br())
            elements.append(Span(f"{i+2:03d}: ", cls='sequence-position'))

    return Div(
        H4("Genomic Sequence Data"),
        P("BRCA1 gene fragment. Color-coded nucleotides require magnification to distinguish."),
        Div(*elements, cls='dna-sequence'),
        cls='content-card',
        id='dna-card'
    )


def CurrencyDetailSample():
    """Currency with security features that need zoom."""
    return Div(
        H4("Currency Security Features"),
        P("Examine microprinting and security thread details used in authentication."),
        Div(
            Div(cls='currency-pattern'),
            Div("SERIAL: FW 84729163 B", cls='currency-serial'),
            Div(
                "UNITED STATES OF AMERICA UNITED STATES OF AMERICA UNITED STATES OF AMERICA "
                "THIS NOTE IS LEGAL TENDER FOR ALL DEBTS PUBLIC AND PRIVATE THIS NOTE IS LEGAL TENDER "
                "FEDERAL RESERVE NOTE THE UNITED STATES OF AMERICA WILL PAY TO THE BEARER ON DEMAND",
                cls='currency-microtext'
            ),
            Div("USA TWENTY USA TWENTY USA TWENTY USA TWENTY", cls='security-thread'),
            Div(
                "MICROPRINTED SECURITY FEATURES: EMBEDDED POLYESTER STRIP WITH DENOMINATION VALUE "
                "COLOR-SHIFTING INK ON DENOMINATION NUMERAL WATERMARK PORTRAIT VISIBLE FROM BOTH SIDES "
                "FINE-LINE PRINTING PATTERNS CONCENTRIC CIRCLES AROUND PORTRAIT UV FLUORESCENT FEATURES",
                cls='currency-microtext'
            ),
            cls='currency-detail'
        ),
        cls='content-card',
        id='currency-card'
    )


def SpecimenDataSample():
    """Scientific specimen card with tiny data."""
    return Div(
        H4("Laboratory Specimen Record"),
        P("Complete specimen analysis data. Requires magnification for detailed review."),
        Div(
            Div("SPECIMEN ANALYSIS REPORT - CONFIDENTIAL", cls='specimen-header'),
            Div(
                Div(Span("Sample ID:", cls='specimen-label'), Span("SPM-2024-00847", cls='specimen-value'), cls='specimen-row'),
                Div(Span("Collection Date:", cls='specimen-label'), Span("2024-01-15 09:23:41 UTC", cls='specimen-value'), cls='specimen-row'),
                Div(Span("Analyst:", cls='specimen-label'), Span("Dr. M. Chen, PhD", cls='specimen-value'), cls='specimen-row'),
                Div(Span("Method:", cls='specimen-label'), Span("HPLC-MS/MS", cls='specimen-value'), cls='specimen-row'),
                Div(Span("pH:", cls='specimen-label'), Span("7.42 +/- 0.02", cls='specimen-value'), cls='specimen-row'),
                Div(Span("Concentration:", cls='specimen-label'), Span("0.0023 mg/mL", cls='specimen-value'), cls='specimen-row'),
                Div(Span("Purity:", cls='specimen-label'), Span("99.7%", cls='specimen-value'), cls='specimen-row'),
                Div(Span("Molecular Weight:", cls='specimen-label'), Span("342.17 g/mol", cls='specimen-value'), cls='specimen-row'),
                Div(Span("Storage:", cls='specimen-label'), Span("-80C, N2 atmosphere", cls='specimen-value'), cls='specimen-row'),
                Div(Span("Status:", cls='specimen-label'), Span("VERIFIED - QC PASSED", cls='specimen-value'), cls='specimen-row'),
                cls='specimen-data'
            ),
            cls='specimen-card'
        ),
        cls='content-card',
        id='specimen-card'
    )


@rt("/")
def get():
    """Main page with zoom viewport."""
    return (
        Div(
            Div(
                Div(
                    Div(
                        H1("Automated Zoom Accessibility"),
                        P("Click to zoom | Any edge to reset | Auto-scroll in normal view"),
                        Span("Accessibility Feature", cls='feature-badge'),
                        cls='demo-header'
                    ),
                    InstructionsPanel(),
                    AIIntegrationSection(),
                    Div(
                        MicroprintSample(),
                        CircuitDiagramSample(),
                        cls='content-grid'
                    ),
                    Div(
                        DataMatrixSample(),
                        DNASequenceSample(),
                        cls='content-grid'
                    ),
                    Div(
                        CurrencyDetailSample(),
                        SpecimenDataSample(),
                        cls='content-grid'
                    ),
                    cls='demo-container'
                ),
                cls='zoom-content'
            ),
            cls='zoom-viewport'
        ),
        *EdgeIndicators(),
        *ScrollZones(),
        ZoomIndicator(),
        ResetNotification(),
        *AccessibilityControls()
    )


@rt("/api/zoom-state")
def get():
    """API endpoint for AI agents to query zoom state."""
    return {"status": "ok", "message": "Use window.AutoZoom.getState() in browser"}


@rt("/api/register-interest")
async def post(request):
    """API endpoint for AI agents to register areas of interest."""
    try:
        data = await request.json()
        selector = data.get('selector', '')
        label = data.get('label', 'Area of Interest')
        return {
            "status": "ok",
            "instruction": f"Call window.AutoZoom.registerAreaOfInterest('{selector}', '{label}') in browser"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@rt("/api/zoom-to")
async def post(request):
    """API endpoint for AI agents to zoom to specific elements."""
    try:
        data = await request.json()
        selector = data.get('selector', '')
        zoom_level = data.get('zoom_level', 2)
        return {
            "status": "ok",
            "instruction": f"Call window.AutoZoom.zoomToElement('{selector}', {zoom_level}) in browser"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


serve()

from fasthtml.common import *
from datetime import datetime
import json

# CSS for the click recorder overlay and markers
click_styles = Style("""
    /* Click overlay that captures all clicks - uses absolute positioning
       so markers stay anchored to page content, not viewport */
    .click-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        min-height: 100%;
        pointer-events: none;
        z-index: 9998;
    }

    /* Click marker square */
    .click-marker {
        position: absolute;
        width: 40px;
        height: 40px;
        border: 3px solid #e74c3c;
        background: rgba(231, 76, 60, 0.2);
        border-radius: 4px;
        transform: translate(-50%, -50%);
        pointer-events: none;
        animation: click-pulse 0.5s ease-out;
        z-index: 9999;
    }

    /* Numbered label for click markers */
    .click-marker::after {
        content: attr(data-index);
        position: absolute;
        top: -20px;
        left: 50%;
        transform: translateX(-50%);
        background: #e74c3c;
        color: white;
        font-size: 12px;
        font-weight: bold;
        padding: 2px 6px;
        border-radius: 10px;
        min-width: 18px;
        text-align: center;
    }

    /* Animation for new clicks */
    @keyframes click-pulse {
        0% {
            transform: translate(-50%, -50%) scale(0.5);
            opacity: 0;
        }
        50% {
            transform: translate(-50%, -50%) scale(1.2);
        }
        100% {
            transform: translate(-50%, -50%) scale(1);
            opacity: 1;
        }
    }

    /* Fade older clicks */
    .click-marker.faded {
        opacity: 0.5;
        border-color: #95a5a6;
        background: rgba(149, 165, 166, 0.15);
    }

    .click-marker.faded::after {
        background: #95a5a6;
    }

    /* Controls panel */
    .click-controls {
        position: fixed;
        top: 10px;
        right: 10px;
        background: var(--pico-card-background-color, #fff);
        border: 1px solid var(--pico-muted-border-color, #ccc);
        border-radius: 8px;
        padding: 12px;
        z-index: 10000;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        min-width: 200px;
    }

    .click-controls h4 {
        margin: 0 0 10px 0;
        font-size: 14px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .click-controls .status-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #27ae60;
        animation: pulse-dot 2s infinite;
    }

    .click-controls .status-dot.paused {
        background: #f39c12;
        animation: none;
    }

    @keyframes pulse-dot {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    .click-controls .stats {
        font-size: 12px;
        color: var(--pico-muted-color, #666);
        margin-bottom: 10px;
    }

    .click-controls .btn-group {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
    }

    .click-controls button {
        padding: 6px 12px;
        font-size: 12px;
        cursor: pointer;
        border: 1px solid var(--pico-muted-border-color, #ccc);
        border-radius: 4px;
        background: var(--pico-background-color, #f8f9fa);
        transition: all 0.2s;
    }

    .click-controls button:hover {
        background: var(--pico-primary, #007bff);
        color: white;
        border-color: var(--pico-primary, #007bff);
    }

    .click-controls button.active {
        background: var(--pico-primary, #007bff);
        color: white;
        border-color: var(--pico-primary, #007bff);
    }

    /* Click history panel */
    .click-history {
        margin-top: 1rem;
        border: 1px solid var(--pico-muted-border-color, #ccc);
        border-radius: 8px;
        padding: 1rem;
        max-height: 300px;
        overflow-y: auto;
    }

    .click-history h3 {
        margin: 0 0 0.5rem 0;
        font-size: 1rem;
    }

    .click-history-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px;
        border-bottom: 1px solid var(--pico-muted-border-color, #eee);
        font-size: 13px;
    }

    .click-history-item:last-child {
        border-bottom: none;
    }

    .click-history-item .index {
        background: #e74c3c;
        color: white;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 11px;
    }

    .click-history-item .coords {
        font-family: monospace;
        color: var(--pico-muted-color, #666);
    }

    .click-history-item .time {
        margin-left: auto;
        color: var(--pico-muted-color, #888);
        font-size: 11px;
    }

    /* Main content area */
    .main-content {
        padding: 2rem;
        min-height: calc(100vh - 200px);
    }

    .demo-area {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 3rem;
        color: white;
        text-align: center;
        margin: 2rem 0;
    }

    .demo-area h2 {
        margin: 0 0 1rem 0;
    }

    .demo-area p {
        opacity: 0.9;
    }

    .demo-buttons {
        display: flex;
        gap: 1rem;
        justify-content: center;
        margin-top: 2rem;
    }

    .demo-buttons button {
        padding: 12px 24px;
        font-size: 16px;
        border-radius: 8px;
        border: 2px solid white;
        background: rgba(255,255,255,0.2);
        color: white;
        cursor: pointer;
        transition: all 0.3s;
    }

    .demo-buttons button:hover {
        background: white;
        color: #667eea;
    }

    /* Empty state */
    .empty-history {
        text-align: center;
        color: var(--pico-muted-color, #888);
        padding: 2rem;
        font-style: italic;
    }
""")

# JavaScript for capturing and displaying clicks
click_js = Script("""
// Click Recorder State
const ClickRecorder = {
    clicks: [],
    isRecording: true,
    maxClicks: 100,

    init() {
        this.loadFromStorage();
        this.attachListeners();
        this.renderMarkers();
        this.updateUI();
        console.log('[ClickRecorder] Initialized with', this.clicks.length, 'stored clicks');
    },

    attachListeners() {
        // Capture all clicks on document
        document.addEventListener('click', (e) => {
            // Ignore clicks on control panel
            if (e.target.closest('.click-controls')) return;

            if (this.isRecording) {
                this.recordClick(e);
            }
        }, true);
    },

    recordClick(e) {
        // Use pageX/pageY for document-relative coordinates
        // This ensures clicking the same content produces same coordinates
        // regardless of scroll position
        const click = {
            id: Date.now(),
            x: e.pageX,
            y: e.pageY,
            viewportX: e.clientX,
            viewportY: e.clientY,
            timestamp: new Date().toISOString(),
            target: e.target.tagName.toLowerCase(),
            targetId: e.target.id || null,
            targetClass: e.target.className || null
        };

        this.clicks.push(click);

        // Limit stored clicks
        if (this.clicks.length > this.maxClicks) {
            this.clicks.shift();
        }

        this.saveToStorage();
        this.addMarker(click, this.clicks.length);
        this.updateUI();
        this.sendToServer(click);

        console.log('[ClickRecorder] Recorded click at page coordinates:', click.x, click.y);
    },

    addMarker(click, index) {
        const overlay = document.getElementById('click-overlay');
        if (!overlay) return;

        // Fade older markers
        overlay.querySelectorAll('.click-marker:not(.faded)').forEach((marker, i) => {
            if (i < overlay.children.length - 5) {
                marker.classList.add('faded');
            }
        });

        const marker = document.createElement('div');
        marker.className = 'click-marker';
        marker.dataset.index = index;
        marker.dataset.id = click.id;
        // Use page coordinates (x, y) for absolute positioning within document
        marker.style.left = click.x + 'px';
        marker.style.top = click.y + 'px';

        overlay.appendChild(marker);
    },

    renderMarkers() {
        const overlay = document.getElementById('click-overlay');
        if (!overlay) return;

        overlay.innerHTML = '';

        this.clicks.forEach((click, i) => {
            const marker = document.createElement('div');
            marker.className = 'click-marker' + (i < this.clicks.length - 5 ? ' faded' : '');
            marker.dataset.index = i + 1;
            marker.dataset.id = click.id;
            // Use page coordinates (x, y) for absolute positioning within document
            marker.style.left = click.x + 'px';
            marker.style.top = click.y + 'px';
            overlay.appendChild(marker);
        });
    },

    updateUI() {
        // Update stats
        const stats = document.getElementById('click-stats');
        if (stats) {
            stats.textContent = `${this.clicks.length} clicks recorded`;
        }

        // Update status dot
        const dot = document.querySelector('.status-dot');
        if (dot) {
            dot.classList.toggle('paused', !this.isRecording);
        }

        // Update history panel via HTMX
        const historyPanel = document.getElementById('click-history-list');
        if (historyPanel && typeof htmx !== 'undefined') {
            htmx.ajax('GET', '/clicks/history', {target: '#click-history-list', swap: 'innerHTML'});
        }
    },

    toggleRecording() {
        this.isRecording = !this.isRecording;
        this.updateUI();
        console.log('[ClickRecorder] Recording:', this.isRecording ? 'ON' : 'OFF');
    },

    clearClicks() {
        this.clicks = [];
        this.saveToStorage();
        this.renderMarkers();
        this.updateUI();

        // Also clear on server
        fetch('/clicks/clear', { method: 'POST' });

        console.log('[ClickRecorder] Cleared all clicks');
    },

    exportClicks() {
        const data = JSON.stringify(this.clicks, null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `click-recording-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
    },

    saveToStorage() {
        try {
            localStorage.setItem('clickRecorder_clicks', JSON.stringify(this.clicks));
        } catch (e) {
            console.warn('[ClickRecorder] Failed to save to localStorage:', e);
        }
    },

    loadFromStorage() {
        try {
            const stored = localStorage.getItem('clickRecorder_clicks');
            if (stored) {
                this.clicks = JSON.parse(stored);
            }
        } catch (e) {
            console.warn('[ClickRecorder] Failed to load from localStorage:', e);
            this.clicks = [];
        }
    },

    async sendToServer(click) {
        try {
            await fetch('/clicks/record', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(click)
            });
        } catch (e) {
            console.warn('[ClickRecorder] Failed to send to server:', e);
        }
    },

    // Get click data for AI agent analysis
    getClickAnalysis() {
        return {
            totalClicks: this.clicks.length,
            recentClicks: this.clicks.slice(-10),
            clicksByTarget: this.groupBy(this.clicks, 'target'),
            averagePosition: this.getAveragePosition(),
            timeRange: this.getTimeRange()
        };
    },

    groupBy(arr, key) {
        return arr.reduce((acc, item) => {
            const k = item[key];
            acc[k] = (acc[k] || 0) + 1;
            return acc;
        }, {});
    },

    getAveragePosition() {
        if (this.clicks.length === 0) return { x: 0, y: 0 };
        // x and y are now page coordinates (document-relative)
        const sum = this.clicks.reduce((acc, c) => ({ x: acc.x + c.x, y: acc.y + c.y }), { x: 0, y: 0 });
        return { x: Math.round(sum.x / this.clicks.length), y: Math.round(sum.y / this.clicks.length) };
    },

    getTimeRange() {
        if (this.clicks.length === 0) return null;
        return {
            first: this.clicks[0].timestamp,
            last: this.clicks[this.clicks.length - 1].timestamp
        };
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => ClickRecorder.init());
} else {
    ClickRecorder.init();
}

// Expose to global scope for AI agent access
window.ClickRecorder = ClickRecorder;
""", type='module')

# In-memory storage for clicks (in production, use a database)
click_storage = []

app, rt = fast_app(hdrs=[click_styles, click_js])


def ControlPanel():
    """Floating control panel for the click recorder."""
    return Div(
        H4(
            Span(cls='status-dot'),
            "Click Recorder"
        ),
        Div(id='click-stats', cls='stats'),
        Div(
            Button("Pause", onclick="ClickRecorder.toggleRecording()"),
            Button("Clear", onclick="ClickRecorder.clearClicks()"),
            Button("Export", onclick="ClickRecorder.exportClicks()"),
            cls='btn-group'
        ),
        cls='click-controls'
    )


def ClickOverlay():
    """Overlay div for displaying click markers."""
    return Div(id='click-overlay', cls='click-overlay')


def ClickHistoryItem(click, index):
    """Render a single click history item."""
    timestamp = click.get('timestamp', '')
    try:
        time_str = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%H:%M:%S')
    except:
        time_str = timestamp[:8] if timestamp else 'N/A'

    # x/y are now page coordinates (document-relative)
    x = click.get('x', 0)
    y = click.get('y', 0)

    return Div(
        Span(str(index), cls='index'),
        Span(f"({x}, {y})", cls='coords'),
        Span(click.get('target', 'unknown')),
        Span(time_str, cls='time'),
        cls='click-history-item'
    )


def ClickHistoryPanel():
    """Panel showing click history."""
    return Div(
        H3("Click History"),
        Div(id='click-history-list', hx_get='/clicks/history', hx_trigger='load'),
        cls='click-history'
    )


def DemoArea():
    """Demo area for testing click recording."""
    return Div(
        H2("Click Anywhere to Record"),
        P("This area demonstrates the click recorder. Every click on this page is captured and marked with a square."),
        Div(
            Button("Button 1"),
            Button("Button 2"),
            Button("Button 3"),
            cls='demo-buttons'
        ),
        cls='demo-area'
    )


@rt("/")
def get():
    """Main page with click recorder."""
    return Titled(
        "Agentic Click Recorder",
        ClickOverlay(),
        ControlPanel(),
        Div(
            P("This tool records and visualizes mouse clicks in real-time. Use it to assist AI agents in understanding user interaction patterns."),
            DemoArea(),
            ClickHistoryPanel(),
            Div(
                H3("Features"),
                Ul(
                    Li("Real-time click recording with visual markers"),
                    Li("Numbered squares showing click sequence"),
                    Li("Click history with coordinates and timestamps"),
                    Li("Export click data as JSON for AI analysis"),
                    Li("Persistent storage in browser localStorage"),
                    Li("Server-side recording for cross-session analysis")
                )
            ),
            Div(
                H3("AI Agent Integration"),
                P("Access click data programmatically via the global ", Code("ClickRecorder"), " object:"),
                Pre(Code("""// Get all recorded clicks
const clicks = ClickRecorder.clicks;

// Get click analysis for AI
const analysis = ClickRecorder.getClickAnalysis();

// Access via API
fetch('/clicks/data').then(r => r.json());""")),
            ),
            cls='main-content'
        )
    )


@rt("/clicks/record")
async def post(request):
    """Record a click from the client."""
    try:
        data = await request.json()
        click_storage.append(data)
        # Keep only last 100 clicks
        if len(click_storage) > 100:
            click_storage.pop(0)
        return {"status": "ok", "count": len(click_storage)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@rt("/clicks/history")
def get():
    """Get click history HTML for HTMX update."""
    if not click_storage:
        return Div(P("No clicks recorded yet. Start clicking!"), cls='empty-history')

    # Show most recent clicks first
    items = []
    for i, click in enumerate(reversed(click_storage[-20:]), 1):
        items.append(ClickHistoryItem(click, len(click_storage) - i + 1))

    return Div(*items)


@rt("/clicks/data")
def get():
    """Get click data as JSON for AI agent analysis."""
    return {
        "clicks": click_storage,
        "count": len(click_storage),
        "analysis": {
            "total": len(click_storage),
            "targets": _count_targets(),
            "average_position": _get_average_position()
        }
    }


@rt("/clicks/clear")
def post():
    """Clear all recorded clicks."""
    global click_storage
    click_storage = []
    return {"status": "ok"}


def _count_targets():
    """Count clicks by target element."""
    targets = {}
    for click in click_storage:
        target = click.get('target', 'unknown')
        targets[target] = targets.get(target, 0) + 1
    return targets


def _get_average_position():
    """Calculate average click position."""
    if not click_storage:
        return {"x": 0, "y": 0}

    total_x = sum(c.get('x', 0) for c in click_storage)
    total_y = sum(c.get('y', 0) for c in click_storage)
    count = len(click_storage)

    return {
        "x": round(total_x / count),
        "y": round(total_y / count)
    }


serve()

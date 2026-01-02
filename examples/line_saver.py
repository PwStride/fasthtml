from fasthtml.common import *
from datetime import datetime
import os
import re

# File path for persistent storage of clicked words
SAVE_FILE = "clicked_words.txt"

# In-memory storage for real-time display
clicked_words_memory = []

# CSS for the line saver application
line_saver_styles = Style("""
    /* Main layout */
    .app-container {
        display: grid;
        grid-template-columns: 1fr 350px;
        gap: 1.5rem;
        margin-top: 1rem;
        min-height: calc(100vh - 200px);
    }

    @media (max-width: 1000px) {
        .app-container {
            grid-template-columns: 1fr;
        }
    }

    /* Input section */
    .input-section {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .input-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        flex-wrap: wrap;
    }

    .input-header h3 {
        margin: 0;
    }

    .file-upload-wrapper {
        position: relative;
        display: inline-block;
    }

    .file-upload-wrapper input[type="file"] {
        position: absolute;
        inset: 0;
        opacity: 0;
        cursor: pointer;
    }

    .file-upload-btn {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        background: var(--pico-primary);
        color: white;
        border-radius: var(--pico-border-radius);
        font-size: 0.9rem;
        cursor: pointer;
        transition: background 0.2s;
    }

    .file-upload-btn:hover {
        background: var(--pico-primary-hover);
    }

    /* Text area styling */
    .text-input-area {
        position: relative;
        min-height: 200px;
    }

    .text-input-area textarea {
        min-height: 200px;
        font-family: monospace;
        font-size: 0.9rem;
        line-height: 1.5;
        resize: vertical;
        width: 100%;
    }

    /* Drop zone overlay */
    .drop-overlay {
        position: absolute;
        inset: 0;
        border: 3px dashed var(--pico-primary);
        border-radius: var(--pico-border-radius);
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(var(--pico-primary-rgb), 0.1);
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.2s;
        z-index: 10;
    }

    .drop-overlay.active {
        opacity: 1;
    }

    .drop-text {
        font-size: 1.2rem;
        font-weight: bold;
        color: var(--pico-primary);
    }

    /* Code display section */
    .code-display-section {
        border: 1px solid var(--pico-muted-border-color);
        border-radius: var(--pico-border-radius);
        background: var(--pico-card-background-color);
        overflow: hidden;
    }

    .code-display-header {
        padding: 0.75rem 1rem;
        background: var(--pico-secondary-background);
        border-bottom: 1px solid var(--pico-muted-border-color);
        font-weight: bold;
        font-size: 0.9rem;
    }

    .code-lines-container {
        max-height: 500px;
        overflow-y: auto;
        padding: 0.5rem;
    }

    /* Individual code lines */
    .code-line {
        display: flex;
        align-items: flex-start;
        gap: 0.5rem;
        padding: 0.25rem 0.5rem;
        font-family: monospace;
        font-size: 0.85rem;
        line-height: 1.6;
        border-radius: 4px;
        transition: background 0.2s;
    }

    .code-line:hover {
        background: rgba(var(--pico-primary-rgb), 0.05);
    }

    .line-number {
        min-width: 40px;
        text-align: right;
        color: var(--pico-muted-color);
        user-select: none;
        flex-shrink: 0;
        padding-right: 0.5rem;
        border-right: 1px solid var(--pico-muted-border-color);
    }

    .line-content {
        flex: 1;
        display: flex;
        flex-wrap: wrap;
        gap: 0;
        white-space: pre-wrap;
        word-break: break-word;
    }

    /* Clickable words */
    .clickable-word {
        cursor: pointer;
        padding: 1px 2px;
        border-radius: 3px;
        transition: all 0.15s;
        display: inline;
    }

    .clickable-word:hover {
        background: var(--pico-primary);
        color: white;
        transform: scale(1.05);
    }

    .clickable-word.clicked {
        background: rgba(var(--pico-primary-rgb), 0.2);
        border-bottom: 2px solid var(--pico-primary);
    }

    /* Whitespace preservation */
    .whitespace {
        white-space: pre;
    }

    /* Record panel (right side) */
    .record-panel {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .record-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .record-header h3 {
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .status-indicator {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #22c55e;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    /* Record display */
    .record-display {
        flex: 1;
        border: 1px solid var(--pico-muted-border-color);
        border-radius: var(--pico-border-radius);
        background: #1e1e1e;
        color: #d4d4d4;
        font-family: monospace;
        font-size: 0.85rem;
        padding: 1rem;
        min-height: 300px;
        max-height: 500px;
        overflow-y: auto;
        white-space: pre-wrap;
        word-break: break-word;
    }

    .record-empty {
        color: #666;
        font-style: italic;
        text-align: center;
        padding: 2rem;
    }

    /* Bracketed words in record display */
    .bracketed-word {
        color: #4ec9b0;
    }

    .record-line {
        margin: 0.25rem 0;
        padding: 0.25rem;
        border-radius: 3px;
    }

    .record-line:hover {
        background: rgba(255, 255, 255, 0.05);
    }

    .record-timestamp {
        color: #6a9955;
        font-size: 0.75rem;
    }

    .record-word {
        color: #ce9178;
    }

    .record-context {
        color: #808080;
        font-size: 0.8rem;
    }

    /* Control buttons */
    .control-buttons {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
    }

    .control-buttons button {
        padding: 0.4rem 0.8rem;
        font-size: 0.85rem;
    }

    /* Stats bar */
    .stats-bar {
        display: flex;
        gap: 1rem;
        padding: 0.75rem 1rem;
        background: var(--pico-card-background-color);
        border: 1px solid var(--pico-muted-border-color);
        border-radius: var(--pico-border-radius);
        font-size: 0.85rem;
        flex-wrap: wrap;
    }

    .stat-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .stat-label {
        color: var(--pico-muted-color);
    }

    .stat-value {
        font-weight: bold;
        color: var(--pico-primary);
    }

    /* Empty state */
    .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 3rem;
        text-align: center;
        color: var(--pico-muted-color);
    }

    .empty-state-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        opacity: 0.5;
    }

    /* Agentic header badge */
    .agentic-badge {
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

    /* Feature description */
    .feature-description {
        padding: 1rem;
        background: var(--pico-card-background-color);
        border: 1px solid var(--pico-muted-border-color);
        border-radius: var(--pico-border-radius);
        margin-bottom: 1rem;
    }

    .feature-description p {
        margin: 0;
        color: var(--pico-muted-color);
        font-size: 0.9rem;
    }
""")

# JavaScript for file handling and click interactions
line_saver_js = Script("""
// Line Saver State
const LineSaver = {
    clickedWords: [],

    init() {
        this.setupFileUpload();
        this.setupDragDrop();
        console.log('[LineSaver] Initialized');
    },

    setupFileUpload() {
        const fileInput = document.getElementById('file-upload');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    this.readFile(file);
                }
            });
        }
    },

    setupDragDrop() {
        const inputArea = document.querySelector('.text-input-area');
        const dropOverlay = document.getElementById('drop-overlay');

        if (!inputArea || !dropOverlay) return;

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            inputArea.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            }, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            inputArea.addEventListener(eventName, () => {
                dropOverlay.classList.add('active');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            inputArea.addEventListener(eventName, () => {
                dropOverlay.classList.remove('active');
            }, false);
        });

        inputArea.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.readFile(files[0]);
            }
        }, false);
    },

    readFile(file) {
        const reader = new FileReader();
        reader.onload = (event) => {
            const textarea = document.getElementById('source-input');
            if (textarea) {
                textarea.value = event.target.result;
                htmx.trigger(textarea, 'input');
            }
        };
        reader.readAsText(file);
    },

    recordWord(word, lineNum, position) {
        // Send to server
        fetch('/record-word', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                word: word,
                line_num: lineNum,
                position: position,
                timestamp: new Date().toISOString()
            })
        }).then(response => response.json())
          .then(data => {
              // Refresh the record display
              htmx.ajax('GET', '/record-display', {target: '#record-display', swap: 'innerHTML'});
              // Mark word as clicked
              event.target.classList.add('clicked');
          })
          .catch(err => console.error('[LineSaver] Error recording word:', err));

        console.log('[LineSaver] Recorded:', word, 'at line', lineNum);
    },

    clearRecords() {
        fetch('/clear-records', { method: 'POST' })
            .then(() => {
                htmx.ajax('GET', '/record-display', {target: '#record-display', swap: 'innerHTML'});
            });
    },

};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => LineSaver.init());
} else {
    LineSaver.init();
}

// Re-initialize after HTMX swaps
document.body.addEventListener('htmx:afterSwap', () => {
    LineSaver.setupDragDrop();
});

// Expose to global scope
window.LineSaver = LineSaver;
""", type='module')

app, rt = fast_app(hdrs=[line_saver_styles, line_saver_js])


def load_records_from_file():
    """Load previously saved records from file."""
    global clicked_words_memory
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, 'r') as f:
                lines = f.readlines()
                clicked_words_memory = []
                for line in lines:
                    line = line.strip()
                    if line:
                        # Parse the stored format: [timestamp] [word] (line:position)
                        clicked_words_memory.append({'raw': line})
        except Exception as e:
            print(f"Error loading records: {e}")


def save_record_to_file(word, line_num, position, timestamp):
    """Append a new record to the growing file."""
    try:
        with open(SAVE_FILE, 'a') as f:
            f.write(f"[{timestamp}] [{word}] (line:{line_num}, pos:{position})\n")
    except Exception as e:
        print(f"Error saving record: {e}")


def tokenize_line(line):
    """Split a line into words and whitespace, preserving structure."""
    tokens = []
    current_pos = 0

    # Pattern to match words (including special chars like operators)
    # This matches sequences of alphanumeric chars, or individual special chars
    pattern = r'(\s+)|(\w+)|([^\s\w])'

    for match in re.finditer(pattern, line):
        text = match.group()
        start = match.start()

        if match.group(1):  # Whitespace
            tokens.append({'type': 'whitespace', 'text': text, 'position': start})
        elif match.group(2):  # Word
            tokens.append({'type': 'word', 'text': text, 'position': start})
        elif match.group(3):  # Special character
            tokens.append({'type': 'word', 'text': text, 'position': start})

    return tokens


def render_code_line(line_num, line_text):
    """Render a single code line with clickable words."""
    tokens = tokenize_line(line_text)

    line_elements = []
    for token in tokens:
        if token['type'] == 'whitespace':
            line_elements.append(Span(token['text'], cls='whitespace'))
        else:
            # Make words clickable
            word = token['text']
            position = token['position']
            line_elements.append(
                Span(
                    word,
                    cls='clickable-word',
                    onclick=f"LineSaver.recordWord('{word.replace(chr(39), chr(92)+chr(39))}', {line_num}, {position})"
                )
            )

    # Handle empty lines
    if not line_elements:
        line_elements.append(Span('\u00A0'))  # Non-breaking space for empty lines

    return Div(
        Span(str(line_num), cls='line-number'),
        Div(*line_elements, cls='line-content'),
        cls='code-line'
    )


def CodeDisplay(code):
    """Generate the clickable code display."""
    if not code or not code.strip():
        return Div(
            Div(
                Div("[ ]", cls='empty-state-icon'),
                P("Enter or upload source code to begin"),
                P("Click on any word to record it", style="font-size: 0.85rem;"),
                cls='empty-state'
            ),
            id='code-display'
        )

    lines = code.split('\n')
    line_elements = [render_code_line(i + 1, line) for i, line in enumerate(lines)]

    return Div(
        Div("Click Words to Record", cls='code-display-header'),
        Div(*line_elements, cls='code-lines-container'),
        id='code-display'
    )


def RecordDisplay():
    """Generate the real-time record display."""
    if not clicked_words_memory:
        return Div(
            Span("No words recorded yet...", cls='record-empty'),
            P("Click on words in the code to start recording.",
              style="color: #666; font-size: 0.8rem; text-align: center; margin-top: 1rem;")
        )

    # Build the display content
    record_lines = []
    for record in clicked_words_memory:
        if 'raw' in record:
            # Loaded from file
            record_lines.append(Div(record['raw'], cls='record-line'))
        else:
            # In-memory record
            timestamp = record.get('timestamp', '')[:19].replace('T', ' ')
            word = record.get('word', '')
            line_num = record.get('line_num', 0)
            position = record.get('position', 0)

            record_lines.append(
                Div(
                    Span(f"[{timestamp}] ", cls='record-timestamp'),
                    Span(f"[", style='color: #d4d4d4;'),
                    Span(word, cls='bracketed-word'),
                    Span(f"]", style='color: #d4d4d4;'),
                    Span(f" (line:{line_num}, pos:{position})", cls='record-context'),
                    cls='record-line'
                )
            )

    return Div(*record_lines)


def StatsBar():
    """Display statistics about the recorded words."""
    total = len(clicked_words_memory)

    # Count unique words
    unique_words = set()
    for record in clicked_words_memory:
        if 'word' in record:
            unique_words.add(record['word'])
        elif 'raw' in record:
            # Try to extract word from raw format
            match = re.search(r'\[([^\]]+)\]', record['raw'])
            if match:
                # Get the second bracketed item (the word)
                matches = re.findall(r'\[([^\]]+)\]', record['raw'])
                if len(matches) >= 2:
                    unique_words.add(matches[1])

    # Get absolute path for display
    abs_path = os.path.abspath(SAVE_FILE)

    return Div(
        Div(
            Span("Total Recorded:", cls='stat-label'),
            Span(str(total), cls='stat-value'),
            cls='stat-item'
        ),
        Div(
            Span("Unique Words:", cls='stat-label'),
            Span(str(len(unique_words)), cls='stat-value'),
            cls='stat-item'
        ),
        Div(
            Span("Local File:", cls='stat-label'),
            Span(abs_path, cls='stat-value', style='font-size: 0.75rem; word-break: break-all;'),
            cls='stat-item',
            style='flex: 1;'
        ),
        cls='stats-bar',
        id='stats-bar',
        hx_get='/stats-bar',
        hx_trigger='every 2s'
    )


def InputSection():
    """Create the input section with text area and file upload."""
    return Div(
        Div(
            H3("Source Content"),
            Div(
                Span("Upload File", cls='file-upload-btn'),
                Input(type='file', id='file-upload', accept='.py,.js,.ts,.java,.c,.cpp,.h,.go,.rs,.rb,.php,.html,.css,.json,.xml,.yaml,.yml,.md,.txt'),
                cls='file-upload-wrapper'
            ),
            cls='input-header'
        ),
        Div(
            Textarea(
                placeholder="Enter your source code here, or upload/drag-drop a file...",
                name="code",
                id="source-input",
                hx_post="/render-code",
                hx_trigger="input changed delay:300ms",
                hx_target="#code-display",
                hx_swap="outerHTML"
            ),
            Div(
                Span("Drop file here", cls='drop-text'),
                cls='drop-overlay',
                id='drop-overlay'
            ),
            cls='text-input-area'
        ),
        cls='input-section'
    )


def RecordPanel():
    """Create the record panel on the right side."""
    return Div(
        Div(
            H3(
                Span(cls='status-indicator'),
                "Live Record"
            ),
            Span("Agentic AI", cls='agentic-badge'),
            cls='record-header'
        ),
        Div(
            Button("Clear", onclick="LineSaver.clearRecords()"),
            cls='control-buttons'
        ),
        Div(
            RecordDisplay(),
            id='record-display',
            cls='record-display'
        ),
        StatsBar(),
        cls='record-panel'
    )


@rt("/")
def get():
    """Main page."""
    # Load any existing records on startup
    load_records_from_file()

    return Titled(
        "Agentic Line Saver",
        Div(
            P("An AI-inspired feature that records clicked words from source code lines. Words are saved locally with brackets to a growing file that other tools can monitor for collaborative, real-time workflows."),
            cls='feature-description'
        ),
        Div(
            Div(
                InputSection(),
                Div(
                    CodeDisplay(""),
                    cls='code-display-section'
                ),
                style='display: flex; flex-direction: column; gap: 1rem;'
            ),
            RecordPanel(),
            cls='app-container'
        )
    )


@rt("/render-code")
def post(code: str = ""):
    """Render the code display with clickable words."""
    return CodeDisplay(code)


@rt("/record-word")
async def post(request):
    """Record a clicked word."""
    try:
        data = await request.json()
        word = data.get('word', '')
        line_num = data.get('line_num', 0)
        position = data.get('position', 0)
        timestamp = data.get('timestamp', datetime.now().isoformat())

        # Add to memory
        record = {
            'word': word,
            'line_num': line_num,
            'position': position,
            'timestamp': timestamp
        }
        clicked_words_memory.append(record)

        # Save to file (append)
        save_record_to_file(word, line_num, position, timestamp)

        return {"status": "ok", "count": len(clicked_words_memory)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@rt("/record-display")
def get():
    """Get the record display HTML."""
    return RecordDisplay()


@rt("/stats-bar")
def get():
    """Get the stats bar HTML."""
    return StatsBar()


@rt("/clear-records")
def post():
    """Clear all recorded words."""
    global clicked_words_memory
    clicked_words_memory = []

    # Clear the file
    try:
        with open(SAVE_FILE, 'w') as f:
            f.write("")
    except Exception as e:
        print(f"Error clearing file: {e}")

    return {"status": "ok"}


serve()

from fasthtml.common import *
import re

# Custom CSS for source code visualization
viz_styles = Style("""
    .viz-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1.5rem;
        margin-top: 1rem;
    }
    .viz-panel {
        display: flex;
        flex-direction: column;
    }
    .viz-panel label {
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .input-area {
        position: relative;
        min-height: 400px;
    }
    .input-area textarea {
        min-height: 400px;
        font-family: monospace;
        font-size: 0.85rem;
        line-height: 1.4;
        resize: vertical;
        width: 100%;
    }
    .drop-zone {
        position: absolute;
        inset: 0;
        border: 2px dashed var(--pico-muted-border-color);
        border-radius: var(--pico-border-radius);
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(var(--pico-primary-rgb), 0.05);
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.2s;
        z-index: 10;
    }
    .drop-zone.active {
        opacity: 1;
        border-color: var(--pico-primary);
        background: rgba(var(--pico-primary-rgb), 0.1);
    }
    .drop-zone-text {
        font-size: 1.1rem;
        color: var(--pico-primary);
        font-weight: bold;
    }

    /* Visualization output */
    .viz-output {
        min-height: 400px;
        border: 1px solid var(--pico-muted-border-color);
        border-radius: var(--pico-border-radius);
        padding: 0.75rem;
        background: var(--pico-card-background-color);
        overflow-y: auto;
        overflow-x: hidden;
    }
    .viz-row {
        display: flex;
        align-items: center;
        height: 18px;
        margin: 1px 0;
        gap: 4px;
        font-size: 0.7rem;
    }
    .line-num {
        width: 35px;
        text-align: right;
        color: var(--pico-muted-color);
        font-family: monospace;
        flex-shrink: 0;
    }

    /* Line type indicators */
    .line-type {
        width: 14px;
        height: 14px;
        border-radius: 2px;
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.6rem;
        font-weight: bold;
        color: white;
    }
    .type-code { background: #3b82f6; }
    .type-comment { background: #22c55e; }
    .type-blank { background: #94a3b8; }

    /* Depth bar - no container, just the bar itself */
    .depth-bar {
        height: 12px;
        min-width: 2px;
        max-width: 60px;
        background: linear-gradient(90deg, #8b5cf6, #a855f7);
        border-radius: 2px;
        flex-shrink: 0;
    }

    /* Length bar - no container, just the bar itself */
    .length-bar {
        height: 12px;
        min-width: 2px;
        max-width: 120px;
        background: linear-gradient(90deg, #06b6d4, #0ea5e9);
        border-radius: 2px;
        flex-shrink: 0;
    }

    /* Control/logic indicator */
    .control-indicator {
        width: 14px;
        height: 14px;
        border-radius: 50%;
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .control-active {
        background: #f59e0b;
    }
    .control-inactive {
        background: #e2e8f0;
    }
    .control-marker {
        font-size: 0.55rem;
        font-weight: bold;
        color: white;
    }

    /* Block start indicator */
    .block-indicator {
        width: 14px;
        height: 14px;
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .block-start {
        color: #ef4444;
        font-weight: bold;
        font-size: 0.9rem;
    }
    .block-none {
        color: #e2e8f0;
    }

    /* Line preview */
    .line-preview {
        flex: 1;
        font-family: monospace;
        font-size: 0.7rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        color: var(--pico-muted-color);
        padding-left: 8px;
    }

    /* Legend */
    .legend {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        margin-bottom: 1.5rem;
        padding: 1rem;
        background: var(--pico-card-background-color);
        border: 1px solid var(--pico-muted-border-color);
        border-radius: var(--pico-border-radius);
        font-size: 0.85rem;
    }
    .legend-title {
        width: 100%;
        font-weight: bold;
        margin-bottom: 0.25rem;
        font-size: 0.9rem;
    }
    .legend-item {
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .legend-box {
        width: 14px;
        height: 14px;
        border-radius: 2px;
    }
    .legend-bar {
        width: 40px;
        height: 10px;
        border-radius: 2px;
    }

    /* Statistics panel */
    .stats-panel {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
        gap: 0.75rem;
        margin-top: 1rem;
        padding: 1rem;
        background: var(--pico-card-background-color);
        border: 1px solid var(--pico-muted-border-color);
        border-radius: var(--pico-border-radius);
    }
    .stat-item {
        text-align: center;
    }
    .stat-value {
        font-size: 1.5rem;
        font-weight: bold;
        color: var(--pico-primary);
    }
    .stat-label {
        font-size: 0.75rem;
        color: var(--pico-muted-color);
    }

    .empty-viz {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        color: var(--pico-muted-color);
        font-style: italic;
    }

    @media (max-width: 900px) {
        .viz-container {
            grid-template-columns: 1fr;
        }
        .input-area textarea, .viz-output {
            min-height: 300px;
        }
    }
""")

# JavaScript for file drop functionality
drop_js = Script("""
document.addEventListener('DOMContentLoaded', function() {
    setupDropZone();
});

// Re-setup after HTMX swaps
document.body.addEventListener('htmx:afterSwap', function() {
    setupDropZone();
});

function setupDropZone() {
    const textarea = document.getElementById('code-input');
    const dropZone = document.getElementById('drop-zone');

    if (!textarea || !dropZone) return;

    const inputArea = textarea.parentElement;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        inputArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        inputArea.addEventListener(eventName, () => {
            dropZone.classList.add('active');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        inputArea.addEventListener(eventName, () => {
            dropZone.classList.remove('active');
        }, false);
    });

    inputArea.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;

        if (files.length > 0) {
            const file = files[0];
            const reader = new FileReader();

            reader.onload = function(event) {
                textarea.value = event.target.result;
                // Trigger HTMX update
                htmx.trigger(textarea, 'input');
            };

            reader.readAsText(file);
        }
    }
}
""")

app, rt = fast_app(hdrs=[viz_styles, drop_js])

# Comment patterns for different languages
COMMENT_PATTERNS = [
    # Single-line comments
    r'^\s*//.*$',           # C, C++, Java, JavaScript, Go, Rust, etc.
    r'^\s*#.*$',            # Python, Ruby, Shell, Perl
    r'^\s*--.*$',           # SQL, Haskell, Lua
    r'^\s*;.*$',            # Assembly, Lisp
    r'^\s*\'.*$',           # VB
    r'^\s*%.*$',            # MATLAB, LaTeX
    r'^\s*/\*.*\*/\s*$',    # Single-line block comment
    r'^\s*<!--.*-->\s*$',   # HTML comment
    r'^\s*\{-.*-\}\s*$',    # Haskell block
]

# Control/logic heavy constructs - expanded for many languages
CONTROL_PATTERNS = [
    # Conditionals
    r'\b(if|else|elif|elsif|unless|then|fi)\b',
    # Loops
    r'\b(for|foreach|while|do|until|loop|repeat|each)\b',
    # Switch/match constructs
    r'\b(switch|case|when|match|default|select)\b',
    # Exception handling
    r'\b(try|catch|except|finally|raise|throw|throws|rescue|ensure|panic|recover)\b',
    # Control flow
    r'\b(return|yield|break|continue|pass|goto|fallthrough|resume)\b',
    # Logical operators
    r'\b(and|or|not|xor)\b',
    r'(&&|\|\||!(?!=))',
    # Async/concurrent
    r'\b(async|await|spawn|go|select|chan|defer|promise|future)\b',
    # Guards and assertions
    r'\b(guard|assert|require|ensure|check|verify|assume|invariant|precondition|postcondition)\b',
    # Rust specific
    r'\b(unwrap|expect|ok_or|map_err|and_then|or_else|is_some|is_none|is_ok|is_err)\b',
    # Pattern matching helpers
    r'\b(Some|None|Ok|Err|Just|Nothing|Left|Right)\b',
    # Null/optional handling
    r'\b(null|nil|undefined|void|nullptr|NULL|None)\b',
    r'\?\?',  # Null coalescing
    r'\?\.', # Optional chaining
    r'\?.*:',  # Ternary operator
    # Type checking
    r'\b(instanceof|typeof|is|as|into|from)\b',
    # Memory/lifecycle
    r'\b(new|delete|alloc|malloc|free|drop|move|copy|clone|borrow|ref|deref)\b',
]

# Block start patterns - expanded for many languages
BLOCK_START_PATTERNS = [
    # Function/method definitions
    r'^\s*(def|function|func|fn|fun|sub|procedure|method)\s+\w+',
    r'^\s*(public|private|protected|internal|static|final|abstract|virtual|override)\s+(def|function|func|fn|fun|void|int|string|bool|async)',
    r'^\s*(pub|priv)\s+(fn|async\s+fn|unsafe\s+fn|const\s+fn)\s+\w+',  # Rust
    r'^\s*impl\s+',  # Rust impl blocks
    r'^\s*(async\s+)?(function|def|fn)\s+\w+',
    r'^\s*(export\s+)?(default\s+)?(async\s+)?function',  # JavaScript exports
    r'^\s*(const|let|var)\s+\w+\s*=\s*(async\s+)?\(',  # Arrow functions
    r'^\s*\w+\s*=\s*(async\s+)?\([^)]*\)\s*=>',  # Arrow functions

    # Class/type definitions
    r'^\s*(class|struct|interface|enum|trait|type|union|record)\s+\w+',
    r'^\s*(public|private|protected|internal|abstract|sealed|final|static)\s+(class|struct|interface|enum|record)\s+',
    r'^\s*(pub|priv)\s+(struct|enum|trait|type|union)\s+\w+',  # Rust visibility
    r'^\s*impl\s+(<[^>]+>\s+)?\w+',  # Rust impl
    r'^\s*(data|newtype|type)\s+\w+',  # Haskell

    # Conditionals
    r'^\s*(if|elif|else|elsif|elseif)\b',
    r'^\s*(guard|unless)\s+',  # Swift guard, Ruby unless

    # Loops
    r'^\s*(for|foreach|while|do|loop|until|repeat)\b',
    r'^\s*(for|while)\s*\(',  # C-style

    # Exception handling
    r'^\s*(try|catch|except|finally|rescue|ensure)\b',

    # Switch/match
    r'^\s*(switch|case|match|when|select)\b',

    # Context managers and scope
    r'^\s*(with|using|let|where)\b',

    # Modules/namespaces/packages
    r'^\s*(module|namespace|package|import|from|use|extern|require)\b',
    r'^\s*(mod|crate|extern\s+crate)\s+\w+',  # Rust modules

    # Visibility/access modifiers as block starters
    r'^\s*(public|private|protected|internal|pub|priv|export)\s*:',
    r'^\s*(public|private|protected)\s*$',  # C++ access specifiers

    # Decorators/attributes
    r'^\s*@\w+',  # Python/Java decorators
    r'^\s*#\[',   # Rust attributes
    r'^\s*\[\w+',  # C# attributes

    # Async/concurrent blocks
    r'^\s*(async|spawn|go|task|thread)\s+(def|fn|function|\{)',
    r'^\s*(unsafe|const)\s+(fn|impl|trait)\s+',  # Rust unsafe/const

    # Closures and lambdas
    r'^\s*\|[^|]*\|\s*\{',  # Rust closures
    r'^\s*->\s*\{',  # Various arrow blocks
    r'^\s*=>\s*\{',  # Fat arrow blocks

    # Test/spec blocks
    r'^\s*(describe|context|it|test|spec|scenario|feature|given|when|then)\s*[(\']',
    r'^\s*#\[test\]',  # Rust test attribute
    r'^\s*@(Test|Before|After|BeforeEach|AfterEach)',  # Java/JUnit

    # Documentation blocks
    r'^\s*(///|//!|/\*\*|\"\"\"|\'\'\')',  # Doc comments

    # Generic block starters
    r'[{:]\s*$',  # Ends with { or :
    r'^\s*\{',    # Starts with {
    r'^\s*begin\b',  # Pascal/Ruby begin
    r'^\s*do\s*$',   # Ruby/Elixir do
]


def analyze_line(line: str) -> dict:
    """Analyze a single line of code and return its characteristics."""
    stripped = line.rstrip()

    # Determine line type
    if not stripped or stripped.isspace():
        line_type = 'blank'
    elif any(re.match(pattern, stripped) for pattern in COMMENT_PATTERNS):
        line_type = 'comment'
    else:
        line_type = 'code'

    # Calculate nesting depth (count leading spaces/tabs)
    leading_whitespace = len(line) - len(line.lstrip())
    # Normalize: 1 tab = 4 spaces
    normalized_depth = line[:leading_whitespace].replace('\t', '    ')
    depth = len(normalized_depth) // 4

    # Check for control/logic constructs
    has_control = any(re.search(pattern, stripped, re.IGNORECASE) for pattern in CONTROL_PATTERNS)

    # Check if line starts a block
    is_block_start = any(re.search(pattern, stripped) for pattern in BLOCK_START_PATTERNS)

    return {
        'type': line_type,
        'depth': depth,
        'length': len(stripped),
        'has_control': has_control and line_type == 'code',
        'is_block_start': is_block_start and line_type == 'code',
        'content': stripped[:50] if stripped else ''
    }


def analyze_code(code: str) -> list:
    """Analyze all lines of code."""
    lines = code.split('\n')
    results = []

    for i, line in enumerate(lines, 1):
        analysis = analyze_line(line)
        analysis['line_num'] = i
        results.append(analysis)

    return results


def compute_stats(analyses: list) -> dict:
    """Compute statistics from analyzed lines."""
    total = len(analyses)
    code_lines = sum(1 for a in analyses if a['type'] == 'code')
    comment_lines = sum(1 for a in analyses if a['type'] == 'comment')
    blank_lines = sum(1 for a in analyses if a['type'] == 'blank')
    control_lines = sum(1 for a in analyses if a['has_control'])
    block_starts = sum(1 for a in analyses if a['is_block_start'])
    max_depth = max((a['depth'] for a in analyses), default=0)
    max_length = max((a['length'] for a in analyses), default=0)
    avg_length = sum(a['length'] for a in analyses) / total if total > 0 else 0

    return {
        'total': total,
        'code': code_lines,
        'comments': comment_lines,
        'blank': blank_lines,
        'control': control_lines,
        'blocks': block_starts,
        'max_depth': max_depth,
        'max_length': max_length,
        'avg_length': round(avg_length, 1)
    }


def render_viz_row(analysis: dict, max_depth: int, max_length: int):
    """Render a single visualization row."""
    line_num = analysis['line_num']
    line_type = analysis['type']
    depth = analysis['depth']
    length = analysis['length']
    has_control = analysis['has_control']
    is_block_start = analysis['is_block_start']
    content = analysis['content']

    # Line type indicator
    type_labels = {'code': 'C', 'comment': '#', 'blank': ' '}
    type_class = f'type-{line_type}'

    # Calculate bar widths in pixels (no empty space, just the bar)
    # Depth: scale from 0 to 60px max
    depth_px = int((depth / max_depth * 60)) if max_depth > 0 and depth > 0 else 2
    # Length: scale from 0 to 120px max
    length_px = int((length / max_length * 120)) if max_length > 0 and length > 0 else 2

    return Div(
        # Line number
        Span(str(line_num), cls='line-num'),

        # Line type indicator
        Span(type_labels[line_type], cls=f'line-type {type_class}', title=f'Type: {line_type}'),

        # Depth bar - direct bar without container
        Div(
            style=f'width: {depth_px}px',
            cls='depth-bar',
            title=f'Depth: {depth}'
        ),

        # Length bar - direct bar without container
        Div(
            style=f'width: {length_px}px',
            cls='length-bar',
            title=f'Length: {length} chars'
        ),

        # Control/logic indicator
        Div(
            Span('!' if has_control else '', cls='control-marker'),
            cls=f'control-indicator {"control-active" if has_control else "control-inactive"}',
            title='Control/logic construct' if has_control else 'No control construct'
        ),

        # Block start indicator
        Div(
            Span('>' if is_block_start else '-', cls='block-start' if is_block_start else 'block-none'),
            cls='block-indicator',
            title='Block start' if is_block_start else ''
        ),

        # Line preview
        Span(content, cls='line-preview', title=content),

        cls='viz-row'
    )


def Legend():
    """Render the legend explaining the visualization."""
    return Div(
        Div("Visualization Legend", cls='legend-title'),
        Div(
            Div(cls='legend-box type-code'),
            Span('Code Line'),
            cls='legend-item'
        ),
        Div(
            Div(cls='legend-box type-comment'),
            Span('Comment Line'),
            cls='legend-item'
        ),
        Div(
            Div(cls='legend-box type-blank'),
            Span('Blank Line'),
            cls='legend-item'
        ),
        Div(
            Div(style='background: linear-gradient(90deg, #8b5cf6, #a855f7)', cls='legend-bar'),
            Span('Nesting Depth'),
            cls='legend-item'
        ),
        Div(
            Div(style='background: linear-gradient(90deg, #06b6d4, #0ea5e9)', cls='legend-bar'),
            Span('Line Length'),
            cls='legend-item'
        ),
        Div(
            Div(style='background: #f59e0b; width: 14px; height: 14px; border-radius: 50%;'),
            Span('Control/Logic Construct'),
            cls='legend-item'
        ),
        Div(
            Span('>', style='color: #ef4444; font-weight: bold;'),
            Span('Block/Section Start'),
            cls='legend-item'
        ),
        cls='legend'
    )


def StatsPanel(stats: dict):
    """Render the statistics panel."""
    return Div(
        Div(Div(str(stats['total']), cls='stat-value'), Div('Total Lines', cls='stat-label'), cls='stat-item'),
        Div(Div(str(stats['code']), cls='stat-value'), Div('Code', cls='stat-label'), cls='stat-item'),
        Div(Div(str(stats['comments']), cls='stat-value'), Div('Comments', cls='stat-label'), cls='stat-item'),
        Div(Div(str(stats['blank']), cls='stat-value'), Div('Blank', cls='stat-label'), cls='stat-item'),
        Div(Div(str(stats['control']), cls='stat-value'), Div('Control', cls='stat-label'), cls='stat-item'),
        Div(Div(str(stats['blocks']), cls='stat-value'), Div('Blocks', cls='stat-label'), cls='stat-item'),
        Div(Div(str(stats['max_depth']), cls='stat-value'), Div('Max Depth', cls='stat-label'), cls='stat-item'),
        Div(Div(str(stats['avg_length']), cls='stat-value'), Div('Avg Length', cls='stat-label'), cls='stat-item'),
        cls='stats-panel',
        id='stats-panel'
    )


def Visualization(code: str):
    """Generate the full visualization for the given code."""
    if not code or not code.strip():
        return Div(
            Div(
                P("Enter or drop code to see visualization..."),
                cls='viz-output empty-viz'
            ),
            id='viz-result'
        )

    analyses = analyze_code(code)
    stats = compute_stats(analyses)

    # Get max values for scaling
    max_depth = stats['max_depth'] if stats['max_depth'] > 0 else 1
    max_length = stats['max_length'] if stats['max_length'] > 0 else 1

    return Div(
        Div(
            *[render_viz_row(a, max_depth, max_length) for a in analyses],
            cls='viz-output'
        ),
        StatsPanel(stats),
        id='viz-result'
    )


# Sample code for demonstration
sample_code = '''def fibonacci(n):
    """Calculate the nth Fibonacci number."""
    # Base cases
    if n <= 0:
        return 0
    elif n == 1:
        return 1

    # Initialize variables
    prev, curr = 0, 1

    # Calculate iteratively
    for i in range(2, n + 1):
        prev, curr = curr, prev + curr

    return curr


class Calculator:
    """A simple calculator class."""

    def __init__(self):
        self.result = 0

    def add(self, x, y):
        # Add two numbers
        return x + y

    def multiply(self, x, y):
        return x * y


# Main execution
if __name__ == "__main__":
    calc = Calculator()
    print(calc.add(5, 3))
'''


def CodeInput(code: str = ""):
    """Create the code input area with drag-and-drop support."""
    return Div(
        Div(
            Label("Source Code Input", _for="code-input"),
            P("Type or paste code below, or drag and drop a file",
              style="font-size: 0.85rem; color: var(--pico-muted-color); margin-bottom: 0.5rem;"),
            Div(
                Textarea(
                    code,
                    name="code",
                    id="code-input",
                    placeholder="Enter your source code here or drop a file...",
                    hx_post="/visualize",
                    hx_trigger="input changed delay:300ms",
                    hx_target="#viz-result",
                    hx_swap="outerHTML"
                ),
                Div(
                    Span("Drop file here", cls='drop-zone-text'),
                    cls='drop-zone',
                    id='drop-zone'
                ),
                cls='input-area'
            ),
            cls='viz-panel'
        ),
        Div(
            Label("Structure Visualization"),
            Visualization(code),
            cls='viz-panel'
        ),
        cls='viz-container'
    )


@rt("/")
def get():
    return Titled(
        "Source Code Visualizer",
        P("Visualize the structure of source code by line type, nesting depth, length, control constructs, and block starts."),
        Legend(),
        CodeInput(sample_code)
    )


@rt("/visualize")
def post(code: str = ""):
    return Visualization(code)


serve()

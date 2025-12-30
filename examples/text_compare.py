from fasthtml.common import *
import difflib

# Custom CSS for diff visualization
diff_styles = Style("""
    .diff-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
        margin-top: 1rem;
    }
    .diff-panel {
        border: 1px solid var(--pico-muted-border-color);
        border-radius: var(--pico-border-radius);
        padding: 1rem;
        background: var(--pico-card-background-color);
        overflow-x: auto;
    }
    .diff-panel h4 {
        margin-top: 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--pico-muted-border-color);
    }
    .diff-content {
        font-family: monospace;
        white-space: pre-wrap;
        word-break: break-word;
        line-height: 1.6;
    }
    .diff-line {
        display: block;
        padding: 2px 4px;
        margin: 1px 0;
        border-radius: 2px;
    }
    .diff-added {
        background-color: rgba(46, 160, 67, 0.2);
        border-left: 3px solid #2ea043;
    }
    .diff-removed {
        background-color: rgba(248, 81, 73, 0.2);
        border-left: 3px solid #f85149;
    }
    .diff-unchanged {
        color: var(--pico-muted-color);
    }
    .input-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
    }
    .input-panel textarea {
        min-height: 200px;
        font-family: monospace;
    }
    .input-panel label {
        font-weight: bold;
    }
    .no-diff {
        text-align: center;
        padding: 2rem;
        color: var(--pico-muted-color);
    }
    .diff-stats {
        display: flex;
        gap: 1rem;
        margin-bottom: 1rem;
        font-size: 0.9rem;
    }
    .stat-added {
        color: #2ea043;
    }
    .stat-removed {
        color: #f85149;
    }
""")

app, rt = fast_app(hdrs=[diff_styles])


def compute_side_by_side_diff(text1: str, text2: str):
    """Compute side-by-side diff using difflib."""
    lines1 = text1.splitlines(keepends=True) if text1 else []
    lines2 = text2.splitlines(keepends=True) if text2 else []

    # Use SequenceMatcher for detailed comparison
    matcher = difflib.SequenceMatcher(None, lines1, lines2)

    left_lines = []
    right_lines = []
    added_count = 0
    removed_count = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            for line in lines1[i1:i2]:
                left_lines.append(('unchanged', line.rstrip('\n\r')))
                right_lines.append(('unchanged', line.rstrip('\n\r')))
        elif tag == 'replace':
            # Lines that were changed
            left_chunk = lines1[i1:i2]
            right_chunk = lines2[j1:j2]
            max_len = max(len(left_chunk), len(right_chunk))

            for idx in range(max_len):
                if idx < len(left_chunk):
                    left_lines.append(('removed', left_chunk[idx].rstrip('\n\r')))
                    removed_count += 1
                else:
                    left_lines.append(('empty', ''))

                if idx < len(right_chunk):
                    right_lines.append(('added', right_chunk[idx].rstrip('\n\r')))
                    added_count += 1
                else:
                    right_lines.append(('empty', ''))
        elif tag == 'delete':
            for line in lines1[i1:i2]:
                left_lines.append(('removed', line.rstrip('\n\r')))
                right_lines.append(('empty', ''))
                removed_count += 1
        elif tag == 'insert':
            for line in lines2[j1:j2]:
                left_lines.append(('empty', ''))
                right_lines.append(('added', line.rstrip('\n\r')))
                added_count += 1

    return left_lines, right_lines, added_count, removed_count


def render_diff_line(status: str, content: str):
    """Render a single diff line with appropriate styling."""
    if status == 'empty':
        return Span('\u00A0', cls='diff-line')  # Non-breaking space for empty lines

    css_class = f'diff-line diff-{status}'
    display_content = content if content else '\u00A0'
    return Span(display_content, cls=css_class)


def render_diff_panel(title: str, lines: list):
    """Render a diff panel with lines."""
    return Div(
        H4(title),
        Div(
            *[render_diff_line(status, content) for status, content in lines],
            cls='diff-content'
        ),
        cls='diff-panel'
    )


def DiffResult(text1: str, text2: str):
    """Generate the diff result display showing only differences."""
    if not text1 and not text2:
        return Div(
            P("Enter text in both fields to see differences."),
            cls='no-diff',
            id='diff-result'
        )

    left_lines, right_lines, added, removed = compute_side_by_side_diff(text1, text2)

    # Filter to show only lines with differences
    filtered_left = []
    filtered_right = []

    for (left_status, left_content), (right_status, right_content) in zip(left_lines, right_lines):
        if left_status != 'unchanged' or right_status != 'unchanged':
            filtered_left.append((left_status, left_content))
            filtered_right.append((right_status, right_content))

    if not filtered_left and not filtered_right:
        return Div(
            P("No differences found. The texts are identical."),
            cls='no-diff',
            id='diff-result'
        )

    stats = Div(
        Span(f"+{added} additions", cls='stat-added'),
        Span(f"-{removed} removals", cls='stat-removed'),
        cls='diff-stats'
    )

    return Div(
        stats,
        Div(
            render_diff_panel("Original (Left)", filtered_left),
            render_diff_panel("Modified (Right)", filtered_right),
            cls='diff-container'
        ),
        id='diff-result'
    )


def InputForm(text1: str = "", text2: str = ""):
    """Create the input form for text comparison with real-time updates."""
    return Div(
        Div(
            Div(
                Label("Original Text", _for="text1"),
                Textarea(
                    text1,
                    name="text1",
                    id="text1",
                    placeholder="Enter the original text here...",
                    hx_post="/compare",
                    hx_trigger="input changed delay:300ms",
                    hx_target="#diff-result",
                    hx_swap="outerHTML",
                    hx_include="#text2"
                ),
                cls='input-panel'
            ),
            Div(
                Label("Modified Text", _for="text2"),
                Textarea(
                    text2,
                    name="text2",
                    id="text2",
                    placeholder="Enter the modified text here...",
                    hx_post="/compare",
                    hx_trigger="input changed delay:300ms",
                    hx_target="#diff-result",
                    hx_swap="outerHTML",
                    hx_include="#text1"
                ),
                cls='input-panel'
            ),
            cls='input-container'
        ),
        id='input-form'
    )


@rt("/")
def get():
    return Titled(
        "Text Comparison Tool",
        P("Compare two texts side-by-side and highlight the differences."),
        InputForm(),
        Div(id='diff-result')
    )


@rt("/compare")
def post(text1: str = "", text2: str = ""):
    return DiffResult(text1, text2)


serve()

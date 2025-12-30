from fasthtml.common import *

# Custom CSS for markdown visualizer
md_styles = Style("""
    .md-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1.5rem;
        margin-top: 1rem;
    }
    .md-panel {
        display: flex;
        flex-direction: column;
    }
    .md-panel label {
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .md-input textarea {
        min-height: 400px;
        font-family: monospace;
        font-size: 0.9rem;
        line-height: 1.5;
        resize: vertical;
    }
    .md-preview {
        min-height: 400px;
        border: 1px solid var(--pico-muted-border-color);
        border-radius: var(--pico-border-radius);
        padding: 1rem;
        background: var(--pico-card-background-color);
        overflow-y: auto;
    }
    .md-preview h1 { font-size: 2rem; margin-top: 0; }
    .md-preview h2 { font-size: 1.5rem; }
    .md-preview h3 { font-size: 1.25rem; }
    .md-preview h4 { font-size: 1rem; }
    .md-preview h5 { font-size: 0.875rem; }
    .md-preview h6 { font-size: 0.75rem; }
    .md-preview pre {
        background: var(--pico-code-background-color);
        padding: 1rem;
        border-radius: var(--pico-border-radius);
        overflow-x: auto;
    }
    .md-preview code {
        background: var(--pico-code-background-color);
        padding: 0.125rem 0.25rem;
        border-radius: 3px;
        font-size: 0.875em;
    }
    .md-preview pre code {
        background: none;
        padding: 0;
    }
    .md-preview blockquote {
        border-left: 4px solid var(--pico-primary);
        margin-left: 0;
        padding-left: 1rem;
        color: var(--pico-muted-color);
    }
    .md-preview table {
        width: 100%;
        border-collapse: collapse;
    }
    .md-preview th, .md-preview td {
        border: 1px solid var(--pico-muted-border-color);
        padding: 0.5rem;
        text-align: left;
    }
    .md-preview th {
        background: var(--pico-card-background-color);
    }
    .md-preview img {
        max-width: 100%;
        height: auto;
    }
    .md-preview hr {
        border: none;
        border-top: 1px solid var(--pico-muted-border-color);
        margin: 1rem 0;
    }
    .md-preview ul, .md-preview ol {
        padding-left: 1.5rem;
    }
    .md-preview a {
        color: var(--pico-primary);
    }
    .empty-preview {
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--pico-muted-color);
        font-style: italic;
    }
    @media (max-width: 768px) {
        .md-container {
            grid-template-columns: 1fr;
        }
        .md-input textarea, .md-preview {
            min-height: 300px;
        }
    }
""")

# JavaScript for client-side markdown rendering with marked.js
markdown_js = Script("""
import { marked } from "https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js";

// Configure marked options
marked.setOptions({
    breaks: true,
    gfm: true
});

// Process markdown elements using proc_htmx for HTMX compatibility
proc_htmx('.marked', e => {
    if (e.textContent.trim()) {
        e.innerHTML = marked.parse(e.textContent);
    }
});
""", type='module')

app, rt = fast_app(hdrs=[md_styles, markdown_js])

# Sample markdown for demonstration
sample_markdown = """# Hello Markdown!

Write **bold**, *italic*, or `code` here.

- List item one
- List item two

> A simple blockquote

Start typing to see live preview!
"""


def MarkdownPreview(content: str = ""):
    """Render the markdown preview area."""
    if not content.strip():
        return Div(
            P("Start typing markdown to see the preview..."),
            cls='md-preview empty-preview',
            id='md-preview'
        )
    return Div(
        content,
        cls='marked md-preview',
        id='md-preview'
    )


def MarkdownEditor():
    """Create the markdown editor with real-time preview."""
    return Div(
        Div(
            Label("Markdown Input", _for="md-input"),
            Textarea(
                sample_markdown,
                name="content",
                id="md-input",
                placeholder="Enter your markdown here...",
                hx_post="/preview",
                hx_trigger="input changed delay:200ms",
                hx_target="#md-preview",
                hx_swap="outerHTML"
            ),
            cls='md-panel md-input'
        ),
        Div(
            Label("Preview"),
            MarkdownPreview(sample_markdown),
            cls='md-panel'
        ),
        cls='md-container'
    )


@rt("/")
def get():
    return Titled(
        "Markdown Visualizer",
        P("Enter markdown text on the left and see the rendered preview on the right in real-time."),
        MarkdownEditor()
    )


@rt("/preview")
def post(content: str = ""):
    return MarkdownPreview(content)


serve()

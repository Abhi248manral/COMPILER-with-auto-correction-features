/**
 * EditorManager — Monaco Editor wrapper with multi-language support.
 * REFACTORED: Added setLanguage(), per-language default code snippets, and language-to-Monaco mapping.
 */

const DEFAULT_CODE = {
    c: `#include <stdio.h>

int main() {
    printf("Hello, World!\\n");
    return 0;
}`,
    cpp: `#include <iostream>
using namespace std;

int main() {
    cout << "Hello, World!" << endl;
    return 0;
}`,
    python: `# Python Example
def greet(name):
    print(f"Hello, {name}!")

greet("World")`,
    java: `public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}`,
    html: `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>My Page</title>
</head>
<body>
    <h1>Hello, World!</h1>
    <p>This is a sample HTML page.</p>
</body>
</html>`,
    css: `/* CSS Example */
body {
    font-family: 'Inter', sans-serif;
    background-color: #121212;
    color: #e0e0e0;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
}

h1 {
    font-size: 2.5rem;
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}`
};

// Monaco language IDs
const MONACO_LANG_MAP = {
    c: 'c',
    cpp: 'cpp',
    python: 'python',
    java: 'java',
    html: 'html',
    css: 'css'
};

export class EditorManager {
    constructor() {
        this.editor = null;
        this.decorations = [];
    }

    async init(language = 'c') {
        return new Promise((resolve) => {
            require.config({ paths: { 'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor@0.33.0/min/vs' } });
            require(['vs/editor/editor.main'], () => {
                this.editor = monaco.editor.create(document.getElementById('monaco-editor'), {
                    value: DEFAULT_CODE[language] || DEFAULT_CODE.c,
                    language: MONACO_LANG_MAP[language] || 'c',
                    theme: 'vs-dark',
                    automaticLayout: true,
                    minimap: { enabled: false },
                    fontSize: 14,
                    padding: { top: 12 },
                    smoothScrolling: true,
                    cursorBlinking: 'smooth',
                    cursorSmoothCaretAnimation: true,
                    renderLineHighlight: 'all',
                    bracketPairColorization: { enabled: true }
                });

                resolve(this.editor);
            });
        });
    }

    getValue() {
        return this.editor.getValue();
    }

    setValue(code) {
        this.editor.setValue(code);
    }

    setTheme(theme) {
        monaco.editor.setTheme(theme === 'dark' ? 'vs-dark' : 'vs');
    }

    setLanguage(language) {
        const monacoLang = MONACO_LANG_MAP[language] || 'plaintext';
        const model = this.editor.getModel();
        monaco.editor.setModelLanguage(model, monacoLang);
        // Set default code snippet for new language
        this.editor.setValue(DEFAULT_CODE[language] || '');
    }

    revealLine(line) {
        this.editor.revealLineInCenter(line);
        this.editor.setPosition({ column: 1, lineNumber: line });
        this.editor.focus();
    }

    updateDecorations(errors) {
        if (!errors || errors.length === 0) {
            monaco.editor.setModelMarkers(this.editor.getModel(), "owner", []);
            return;
        }
        const markers = errors.filter(err => err.start_point && err.end_point).map(err => ({
            startLineNumber: (err.start_point[0] || 0) + 1,
            startColumn: (err.start_point[1] || 0) + 1,
            endLineNumber: (err.end_point[0] || 0) + 1,
            endColumn: (err.end_point[1] || 0) + 1,
            message: err.message || `Error: ${err.type}`,
            severity: monaco.MarkerSeverity.Error
        }));

        monaco.editor.setModelMarkers(this.editor.getModel(), "owner", markers);
    }
}

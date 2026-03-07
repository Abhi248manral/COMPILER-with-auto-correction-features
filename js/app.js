import { compileCode } from './api.js';
import { EditorManager } from './editor.js';
import { UIManager } from './ui.js';
import { DiffViewer } from './diff.js';

class App {
    constructor() {
        this.editor = new EditorManager();
        this.ui = new UIManager();
        this.diff = new DiffViewer();

        this.currentTheme = 'dark';
        this.currentLanguage = 'c';
        this.lastResponse = null;

        this.init();
    }

    async init() {
        // Read language from URL params (e.g., /editor?lang=python)
        const params = new URLSearchParams(window.location.search);
        const langParam = params.get('lang');
        if (langParam) {
            this.currentLanguage = langParam;
            const sel = document.getElementById('language-select');
            if (sel) sel.value = langParam;
        }

        // Initialize Editor
        await this.editor.init(this.currentLanguage);

        // Bind Events
        document.getElementById('btn-compile').addEventListener('click', () => this.handleCompile());
        document.getElementById('btn-fix').addEventListener('click', () => this.handleCompile(true));
        document.getElementById('theme-toggle').addEventListener('click', () => this.toggleTheme());
        document.getElementById('btn-clear-output').addEventListener('click', () => this.ui.updateOutput('', true));

        // Toggle output panel
        document.getElementById('btn-toggle-output').addEventListener('click', () => {
            document.querySelector('.bottom-panel').classList.toggle('expanded');
        });

        // Language switching
        document.getElementById('language-select').addEventListener('change', (e) => {
            this.currentLanguage = e.target.value;
            this.editor.setLanguage(this.currentLanguage);
        });

        // Jump to line event
        window.addEventListener('jumpToLine', (e) => {
            this.editor.revealLine(e.detail);
        });

        // Preview close
        const closePreview = document.querySelector('.btn-close-preview');
        if (closePreview) {
            closePreview.addEventListener('click', () => {
                document.getElementById('preview-view').classList.add('hidden');
            });
        }

        // Show logged-in user
        const user = localStorage.getItem('compilerfix_user');
        if (user) {
            const badge = document.getElementById('user-badge');
            badge.textContent = user;
            badge.style.display = 'inline-flex';
            const loginBtn = document.getElementById('nav-login-btn');
            loginBtn.innerHTML = '<i class="fa-solid fa-right-from-bracket"></i>';
            loginBtn.title = 'Logout';
            loginBtn.href = '#';
            loginBtn.addEventListener('click', (e) => {
                e.preventDefault();
                localStorage.removeItem('compilerfix_token');
                localStorage.removeItem('compilerfix_user');
                window.location.reload();
            });
        }
    }

    async handleCompile(isAutoFix = false) {
        const code = this.editor.getValue();
        this.ui.setLoading(true);
        this.ui.updateOutput("Compiling...", true);

        const result = await compileCode(code, this.currentLanguage, isAutoFix);
        this.lastResponse = result;

        this.ui.setLoading(false);
        this.ui.updateOutput(result.final_compile_output, result.success, result);
        this.ui.renderErrors(result.original_errors || []);
        this.ui.renderFixes(result.fixes_applied || []);

        // Update editor decorations (only for C — tree-sitter markers)
        if (this.currentLanguage === 'c' && result.original_errors) {
            this.editor.updateDecorations(result.original_errors);
        }

        // Handle autofix diff view
        if (isAutoFix && result.fixes_applied && result.fixes_applied.length > 0) {
            this.diff.show(code, result.fixed_code);
        } else if (isAutoFix) {
            this.ui.updateOutput(
                "No auto-fixes could be applied.\n" + (result.final_compile_output || ""),
                result.success,
                result
            );
        }

        // Handle HTML/CSS preview
        if (result.preview && (this.currentLanguage === 'html' || this.currentLanguage === 'css')) {
            const previewView = document.getElementById('preview-view');
            const iframe = document.getElementById('preview-frame');
            previewView.classList.remove('hidden');
            iframe.srcdoc = result.preview;
        }
    }

    toggleTheme() {
        this.currentTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        document.body.className = `theme-${this.currentTheme}`;
        this.editor.setTheme(this.currentTheme);

        const icon = document.querySelector('#theme-toggle i');
        icon.className = this.currentTheme === 'dark' ? 'fa-solid fa-moon' : 'fa-solid fa-sun';
    }
}

// Start App
window.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});

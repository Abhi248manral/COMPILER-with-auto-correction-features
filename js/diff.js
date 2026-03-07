/**
 * DiffViewer — Shows before/after comparison when auto-fix is applied.
 *
 * SCROLL FIX: All critical layout styles are applied INLINE via JavaScript.
 * The container is moved to document.body so no parent can block overflow.
 * This guarantees scrolling works regardless of CSS cache or parent layout.
 */

export class DiffViewer {
    constructor() {
        this.container = null;
        this.content = null;
        this.header = null;
        this._bound = false;
        this._movedToBody = false;
    }

    _ensureBound() {
        if (this._bound) return;
        this.container = document.getElementById('diff-view');
        this.content = document.getElementById('diff-content');
        this.header = this.container?.querySelector('.diff-header');

        const closeBtn = document.querySelector('.btn-close-diff');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.hide());
        }
        this._bound = true;

        // Move #diff-view out of .editor-container → directly into <body>
        // so NO parent can clip or block scrolling.
        if (this.container && !this._movedToBody) {
            document.body.appendChild(this.container);
            this._movedToBody = true;
        }
    }

    show(original, fixed) {
        this._ensureBound();
        if (!this.container) return;

        // ── Force all critical styles INLINE (cannot be overridden by cache) ──

        // Container: fullscreen fixed overlay
        Object.assign(this.container.style, {
            position: 'fixed',
            top: '0',
            left: '0',
            width: '100vw',
            height: '100vh',
            display: 'flex',
            flexDirection: 'column',
            zIndex: '9999',
            background: 'var(--bg-app, #121212)',
            overflow: 'hidden',
        });
        this.container.classList.remove('hidden');

        // Header: fixed at top
        if (this.header) {
            Object.assign(this.header.style, {
                flexShrink: '0',
                padding: '10px 15px',
                borderBottom: '1px solid var(--border-color, rgba(255,255,255,0.1))',
                background: 'var(--bg-panel, rgba(30,30,30,0.7))',
            });
        }

        // Render the diff content
        this.render(original, fixed);

        // Content: THE scroll container — force styles AFTER render
        if (this.content) {
            Object.assign(this.content.style, {
                flex: '1',
                minHeight: '0',
                maxHeight: 'calc(100vh - 52px)',
                overflowY: 'auto',
                overflowX: 'auto',
                WebkitOverflowScrolling: 'touch',
            });
        }
    }

    hide() {
        this._ensureBound();
        if (!this.container) return;
        this.container.classList.add('hidden');
        this.container.style.display = 'none';
    }

    render(original, fixed) {
        if (!this.content) return;

        const lines1 = original.split('\n');
        const lines2 = fixed.split('\n');

        // Inner wrapper: NO overflow (parent handles scrolling), NO flex sizing
        let html = '<div style="padding:20px; font-family:monospace; display:flex; gap:20px;">';

        // Left side (Original)
        html += '<div style="flex:1; min-width:0">';
        html += '<h4 style="margin-bottom:8px; position:sticky; top:0; background:var(--bg-app, #121212); padding:4px 0; z-index:1;">Original</h4>';
        lines1.forEach((line, i) => {
            const mod = (lines2[i] !== line) ? 'background:var(--diff-bg-del)' : '';
            html += `<div style="${mod}; padding:2px 4px; white-space:pre;">${String(i + 1).padStart(3)}  ${this.escape(line)}</div>`;
        });
        html += '</div>';

        // Right side (Fixed)
        html += '<div style="flex:1; min-width:0">';
        html += '<h4 style="margin-bottom:8px; position:sticky; top:0; background:var(--bg-app, #121212); padding:4px 0; z-index:1;">Fixed</h4>';
        lines2.forEach((line, i) => {
            const mod = (lines2[i] !== lines1[i]) ? 'background:var(--diff-bg-add)' : '';
            html += `<div style="${mod}; padding:2px 4px; white-space:pre;">${String(i + 1).padStart(3)}  ${this.escape(line)}</div>`;
        });
        html += '</div></div>';

        this.content.innerHTML = html;
    }

    escape(str) {
        return str.replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

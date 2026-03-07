/**
 * UIManager — Renders errors, fixes, and output console.
 * FIXED: Deferred DOM queries to avoid crashes when constructed before DOM is ready.
 */

export class UIManager {
    constructor() {
        this.errorList = null;
        this.fixList = null;
        this.outputConsole = null;
        this.errorCountBadge = null;
        this._bound = false;
    }

    _ensureBound() {
        if (this._bound) return;
        this.errorList = document.getElementById('error-list');
        this.fixList = document.getElementById('fix-list');
        this.outputConsole = document.getElementById('output-console');
        this.errorCountBadge = document.getElementById('error-count');
        this._bound = true;
    }

    renderErrors(errors) {
        this._ensureBound();
        if (!this.errorList) return;

        this.errorList.innerHTML = '';
        if (this.errorCountBadge) this.errorCountBadge.textContent = errors.length;

        if (errors.length === 0) {
            this.errorList.innerHTML = '<div class="empty-state">No errors detected</div>';
            return;
        }

        errors.forEach(err => {
            const el = document.createElement('div');
            el.className = 'error-item';
            const line = err.start_point ? err.start_point[0] + 1 : (err.line || '?');
            el.innerHTML = `
                <div style="font-weight:600; color:var(--error)">Line ${line}</div>
                <div style="font-size:0.85rem; color:var(--text-muted)">${err.type || ''}: ${err.message || ''}</div>
            `;
            el.onclick = () => {
                window.dispatchEvent(new CustomEvent('jumpToLine', { detail: line }));
            };
            this.errorList.appendChild(el);
        });
    }

    renderFixes(fixes) {
        this._ensureBound();
        if (!this.fixList) return;

        this.fixList.innerHTML = '';

        if (fixes.length === 0) {
            this.fixList.innerHTML = '<div class="empty-state">No fixes applied</div>';
            return;
        }

        fixes.forEach(fix => {
            const el = document.createElement('div');
            el.className = 'fix-item';
            el.innerHTML = `
                <div style="font-weight:600; color:var(--success)">${fix.rule}</div>
                <div style="font-size:0.85rem">Line ${fix.line}: ${fix.description}</div>
                <div style="font-size:0.8rem; font-family:var(--font-mono); margin-top:4px; opacity:0.7">
                   ${fix.before} <i class="fa-solid fa-arrow-right"></i> ${fix.after}
                </div>
            `;
            this.fixList.appendChild(el);
        });
    }

    updateOutput(output, success, result = null) {
        this._ensureBound();
        if (!this.outputConsole) return;

        // Clear previous content
        this.outputConsole.innerHTML = '';

        // Show status label if we have a result with error status
        if (result && result.status && result.status !== 'success') {
            const label = document.createElement('div');
            label.style.cssText = 'font-weight:700; margin-bottom:6px; font-size:0.95rem;';
            const statusMap = {
                'linker_error': { icon: '🔗', text: 'Linker Error', color: '#f59e0b' },
                'compile_error': { icon: '⚠️', text: 'Compile Error', color: '#ef4444' },
                'runtime_error': { icon: '💥', text: 'Runtime Error', color: '#ef4444' },
                'timeout_error': { icon: '⏱', text: 'Timeout Error', color: '#f97316' },
                'connection_error': { icon: '🔌', text: 'Connection Error', color: '#ef4444' },
            };
            const info = statusMap[result.status] || { icon: '❌', text: result.status, color: '#ef4444' };
            label.style.color = info.color;
            label.textContent = `${info.icon} ${info.text}`;
            this.outputConsole.appendChild(label);

            // Show user-friendly message if available
            if (result.message) {
                const msg = document.createElement('div');
                msg.style.cssText = 'font-size:0.85rem; margin-bottom:6px; opacity:0.9;';
                msg.textContent = result.message;
                this.outputConsole.appendChild(msg);
            }
        }

        // Show main output text
        const pre = document.createElement('pre');
        pre.style.cssText = 'margin:0; white-space:pre-wrap; word-break:break-word;';
        pre.textContent = output || (success ? 'No output.' : '');
        pre.style.color = success ? 'var(--console-text)' : 'var(--error)';
        this.outputConsole.appendChild(pre);
    }

    setLoading(active) {
        const btn = document.getElementById('btn-compile');
        if (!btn) return;
        if (active) {
            btn.innerHTML = '<div class="loading-spinner"></div> Compiling...';
            btn.disabled = true;
        } else {
            btn.innerHTML = '<i class="fa-solid fa-play"></i> Run';
            btn.disabled = false;
        }
    }
}

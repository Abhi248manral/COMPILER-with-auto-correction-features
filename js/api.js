/**
 * API Module — Communicates with the CompilerFix backend.
 * Uses relative URLs so it works regardless of host/port.
 */

export async function compileCode(code, language = 'c', autofix = true) {
    try {
        const response = await fetch('/compile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, language, autofix })
        });

        if (!response.ok) {
            const errText = await response.text();
            throw new Error(`Server Error ${response.status}: ${errText}`);
        }

        return await response.json();
    } catch (error) {
        console.error("API Call failed:", error);
        return {
            success: false,
            final_compile_output: `Connection Error: Could not reach server.\n${error.message}\n\nMake sure the server is running:\n  python -m uvicorn backend.app:app --port 8001\n\nThen open http://127.0.0.1:8001/editor`,
            original_errors: [],
            fixes_applied: [],
            fixed_code: code,
            original_code: code,
            status: "connection_error",
            exitCode: -1,
            signal: "",
            message: error.message
        };
    }
}

# Grammar-Aware Online Compiler - Frontend

A modern, glassmorphism-styled frontend for the Online Compiler. It visualizes the compilation pipeline, showing errors, applied fixes, and the resulting code diffs.

## 🎨 UI/UX & Compiler Visualization

The interface is designed to map directly to the compiler's feedback loop:

1.  **Input (Monaco Editor)**: Represents the source buffer.
2.  **Lexical/Syntax Analysis (Left Panel)**: Displays errors found by the parser. Clicking an error jumps to the specific line/token, aiding in **Error Localization**.
3.  **Optimization/Recovery (Right Panel)**: Lists the "transformations" applied by the auto-fix engine. This visualizes the **Error Recovery** phase.
4.  **Code Generation (Bottom Panel)**: Displays the final output from the machine code execution (GCC output).
5.  **Diff View**: A side-by-side comparison of the Source vs. Fixed code, visualizing the specific changes made by the rule engine.

## 🛠️ Tech Stack
- **HTML5 / CSS3**: Custom responsive layout with Flexbox/Grid and Glassmorphism effects.
- **JavaScript (ES6)**: Modular architecture (`api.js`, `editor.js`, `ui.js`).
- **Monaco Editor**: The same editor engine used in VS Code.

## 🚀 How to Run

1.  **Start Backend**: Ensure the backend API is running on `http://localhost:8000`.
2.  **Open Frontend**:
    Simply open `index.html` in any modern web browser.
    
    *Note: For Monaco Editor to load workers correctly without CORS issues locally, it's best to run a simple HTTP server:*
    ```bash
    npx http-server .
    ```

## Features
- **Auto-Fix Visualization**: See exactly what the compiler changed to fix your code.
- **Real-time Compilation**: Instant feedback on syntax correctness.
- **Modern Themes**: Light and Dark mode support.

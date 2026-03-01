# Grammar-Aware Online Compiler - Backend

This project implements a backend for an online C compiler capable of detecting and automatically fixing common syntax errors. It leverages **Tree-sitter** for robust parsing and a **Rule-Based Engine** for error recovery, simulating phases of a modern compiler.

## 🎓 Academic Concepts & Compiler Design Mapping

This system demonstrates several core compiler design concepts:

### 1. Lexical & Phrase-Level Correction
- **Levenshtein Distance (Edit Distance)**: Used to correct typo-ed keywords (e.g., `whlie` -> `while`). This operates at the lexical level, identifying tokens that are "close" to valid keywords.
- **String Literal Recovery**: Detects unclosed string literals (lexical error) and attempts to close them to allow parsing to continue.

### 2. Syntax Error Detection
- We use **Tree-sitter**, an incremental parser, to generate a Concrete Syntax Tree (CST).
- **Error Nodes**: When the parser encounters an unexpected token, it generates an `ERROR` node or a `MISSING` node. We traverse the tree to locate these nodes precisely.

### 3. Error Recovery Loop
The system implements a feedback loop for error recovery:
1.  **Parse**: Code is parsed to find error locations.
2.  **Analyze**: The `AutoFixEngine` matches error patterns (Missing Semicolon, Unbalanced Brackets) against the context.
3.  **Patch**: A fix is applied to the source code.
4.  **Re-compile**: The modified code is passed to `GCC` to verify if it compiles successfully.

## 🛠️ Tech Stack
- **Framework**: FastAPI (Python)
- **Parser**: Tree-sitter (Python bindings) + C Grammar
- **Compiler**: GCC
- **Isolation**: Subprocess limits + Temporary directories

## 🚀 Setup & Run

1.  **Install Rules**:
    Ensure you have `gcc` installed and in your system PATH.

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run Server**:
    ```bash
    uvicorn app:app --reload
    ```
    The server runs on `http://localhost:8000`.

## API Usage

**POST /compile**

Request:
```json
{
  "language": "c",
  "code": "int main() { return 0 }"
}
```

Response:
```json
{
  "original_errors": [...],
  "fixes_applied": [
    {
      "line": 1,
      "rule": "MissingSemicolonRule",
      "description": "Added missing semicolon"
    }
  ],
  "fixed_code": "int main() { return 0; }",
  "success": true
}
```

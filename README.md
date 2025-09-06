# CompilerProject-Obfuscator-SadeghHeidari

This project is a **code obfuscator tool** for a simplified C-like language called **CMini**.  
The main goal of this tool is to **transform the structure of the code** without affecting its functionality, in order to make it harder to read, analyze, or reverse-engineer.

##  Features

This tool supports several code obfuscation techniques:

1. **Variable and Function Renaming**  
   All identifiers (except `main`) are replaced with random names.

2. **Dead Code Insertion**  
   Unused and harmless code is randomly injected into code blocks.

3. **Expression Complication**  
   Simple arithmetic expressions (e.g., `a + b`) are transformed into more complex equivalents (e.g., `(-1*-((a + b)))`).

## Phase 2

1. **How to Run**
   The De-Obfuscator takes an obfuscated Mini-C program (e.g., mc.output) and produces a cleaned version (cleaned.mc).The tool also compiles and executes both versions to verify functional equivalence.

2. **Techniques Used**
   The de-obfuscator applies multiple reverse transformations to recover readability:

   Expression Simplification

   Converts redundant expressions like (-1*-(a + b)) → a + b

   Converts x - (-y) → x + y

   Dead Code Elimination

   Removes unused variables and dummy assignments (e.g., int unused = 123;).

   Control Flow Simplification

   Rewrites unnecessary flattened control flows such as while + switch patterns back into linear execution.

   Renaming Identifiers

   Replaces meaningless names with meaningful ones (e.g., fxz → sum, var1 → x, obf_result → total).

3. **Input/Output Comparison**
   Size: The tool compares the file sizes of the obfuscated vs. cleaned code.

   Execution: Both versions are compiled and executed using gcc.

   Functional Equivalence: Standard output (stdout) from both programs is compared.

   If outputs match → ✅ confirmed equivalence.

   If not → ⚠️ warning about mismatch.

### Prerequisites

- Python 3.6+
- ANTLR4 installed and CMini grammar compiled to generate Lexer and Parser files
- `gcc` compiler installed for compiling C programs

### Run the Program

```bash
python main.py

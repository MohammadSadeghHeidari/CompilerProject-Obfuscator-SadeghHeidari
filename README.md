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

##  How to Run

### Prerequisites

- Python 3.6+
- ANTLR4 installed and CMini grammar compiled to generate Lexer and Parser files
- `gcc` compiler installed for compiling C programs

### Run the Program

```bash
python main.py

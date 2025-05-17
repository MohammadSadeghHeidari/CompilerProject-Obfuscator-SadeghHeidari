
import sys
from antlr4 import *
from CMiniLexer import CMiniLexer
from CMiniParser import CMiniParser
from CMiniListener import CMiniListener

import random
import string
import re

obf_map = {}


def random_name(length=6):
    return ''.join(random.choices(string.ascii_lowercase, k=length))


class ObfuscatingListener(CMiniListener):
    def __init__(self, tokens: CommonTokenStream):
        self.tokens = tokens

    def replace(self, ctx, new_text):
        interval = ctx.getSourceInterval()
        start = self.tokens.get(interval[0])
        stop = self.tokens.get(interval[1])
        for i in range(start.tokenIndex, stop.tokenIndex + 1):
            self.tokens.tokens[i].text = ""
        self.tokens.tokens[start.tokenIndex].text = new_text

    def enterFunctionDecl(self, ctx):
        func_name = ctx.ID().getText()
        new_name = obf_map.get(func_name, random_name())
        obf_map[func_name] = new_name
        self.replace(ctx.ID(), new_name)

    def enterParam(self, ctx):
        var_name = ctx.ID().getText()
        new_name = obf_map.get(var_name, random_name())
        obf_map[var_name] = new_name
        self.replace(ctx.ID(), new_name)

    def enterVarDecl(self, ctx):
        var_name = ctx.ID().getText()
        new_name = obf_map.get(var_name, random_name())
        obf_map[var_name] = new_name
        self.replace(ctx.ID(), new_name)

    def enterExpr(self, ctx):
        # پنهان‌سازی ساده‌ی جمع
        if ctx.getChildCount() == 3:
            op = ctx.getChild(1).getText()
            if op == '+':
                left = ctx.getChild(0).getText()
                right = ctx.getChild(2).getText()
                complex_expr = f"(-1*-({left} + {right}))"
                self.replace(ctx, complex_expr)
        # جایگزینی نام متغیرها در عبارات
        if ctx.getText() in obf_map:
            self.replace(ctx, obf_map[ctx.getText()])

    def enterFunctionCall(self, ctx):
        fname = ctx.ID().getText()
        if fname in obf_map:
            self.replace(ctx.ID(), obf_map[fname])

    def enterBlock(self, ctx):
        # درج dead code
        if random.random() < 0.4:
            dead_code = f"int unused_{random_name(4)} = {random.randint(1, 100)};"
            open_brace = ctx.getChild(0)
            self.tokens.tokens[open_brace.symbol.tokenIndex].text += "\n    " + dead_code


# فرمت‌بندی نهایی

def format_code(code):
    code = re.sub(r'(?<!\s)return(?!\s)', 'return ', code)
    code = code.replace('{', '{\n')
    code = code.replace('}', '}\n')
    code = re.sub(r';', ';\n', code)
    code = re.sub(r'\n+', '\n', code)

    lines = code.split('\n')
    formatted = []
    indent = 0

    for line in lines:
        stripped = line.strip()
        if stripped == '':
            continue
        if stripped == '}':
            indent -= 1
        formatted.append('    ' * indent + stripped)
        if stripped.endswith('{'):
            indent += 1

    return '\n'.join(formatted)


# Control Flow Flattening

def apply_control_flow_flattening(code):
    pattern = re.compile(r'(int\s+main\s*\(\s*\)\s*{)(.*?)(return\s+\d+;)', re.DOTALL)
    match = pattern.search(code)
    if not match:
        return code

    header, body, ret = match.groups()
    body_lines = [line.strip() for line in body.strip().split(';') if line.strip()]
    switch_cases = ""
    dispatch_table = list(enumerate(body_lines))
    random.shuffle(dispatch_table)
    label_map = {i: random.randint(100, 999) for i, _ in dispatch_table}

    for i, line in dispatch_table:
        next_label = label_map.get(i + 1, 0)
        switch_cases += f"        case {label_map[i]}: {line}; state = {next_label}; break;\n"

    new_body = f'''
    int state = {label_map[0]};
    while (state != 0) {{
        switch (state) {{
{switch_cases}        }}
    }}
    {ret}
'''
    return pattern.sub(r'\1' + new_body + '}', code)


def main():
    input_file = "mc.input"
    output_file = "mc.output"

    input_stream = FileStream(input_file)
    lexer = CMiniLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = CMiniParser(token_stream)
    tree = parser.program()

    listener = ObfuscatingListener(token_stream)
    walker = ParseTreeWalker()
    walker.walk(listener, tree)

    raw_code = token_stream.getText()
    formatted = format_code(raw_code)
    final_code = apply_control_flow_flattening(formatted)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_code)


if __name__ == '__main__':
    main()


'''
import sys
from antlr4 import *
from CMiniLexer import CMiniLexer
from CMiniParser import CMiniParser
from CMiniListener import CMiniListener

import random
import string
import re

obf_map = {}

def random_name(length=6):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

class ObfuscatingListener(CMiniListener):
    def __init__(self, tokens: CommonTokenStream):
        self.tokens = tokens

    def replace(self, ctx, new_text):
        interval = ctx.getSourceInterval()
        start = self.tokens.get(interval[0])
        stop = self.tokens.get(interval[1])
        for i in range(start.tokenIndex, stop.tokenIndex + 1):
            self.tokens.tokens[i].text = ""  # حذف محتوای قبلی
        self.tokens.tokens[start.tokenIndex].text = new_text  # جایگزینی

    def enterFunctionDecl(self, ctx):
        func_name = ctx.ID().getText()
        new_name = obf_map.get(func_name, random_name())
        obf_map[func_name] = new_name
        self.replace(ctx.ID(), new_name)

    def enterParam(self, ctx):
        var_name = ctx.ID().getText()
        new_name = obf_map.get(var_name, random_name())
        obf_map[var_name] = new_name
        self.replace(ctx.ID(), new_name)

    def enterVarDecl(self, ctx):
        var_name = ctx.ID().getText()
        new_name = obf_map.get(var_name, random_name())
        obf_map[var_name] = new_name
        self.replace(ctx.ID(), new_name)

    def enterAssignment(self, ctx):
        var_name = ctx.ID().getText()
        if var_name in obf_map:
            self.replace(ctx.ID(), obf_map[var_name])

    def enterExpr(self, ctx):
        if ctx.getChildCount() == 3:
            op = ctx.getChild(1).getText()
            if op == '+':
                left = ctx.getChild(0).getText()
                right = ctx.getChild(2).getText()
                complex_expr = f"(-1*-({left} + {right}))"
                self.replace(ctx, complex_expr)

    def enterFunctionCall(self, ctx):
        fname = ctx.ID().getText()
        if fname in obf_map:
            self.replace(ctx.ID(), obf_map[fname])

    def enterBlock(self, ctx):
        # درج کد مرده با احتمال 30٪
        if random.random() < 0.3:
            dead_code = "int unused_var_" + random_name(3) + " = 1234;"
            open_brace = ctx.getChild(0)
            self.tokens.tokens[open_brace.symbol.tokenIndex].text += "\n    " + dead_code


def format_code(code):
    # افزودن خط جدید بعد از ; و { و }
    code = code.replace('{', '{\n')
    code = code.replace('}', '}\n')
    code = re.sub(r';', ';\n', code)
    code = re.sub(r'\n+', '\n', code)  # حذف خطوط خالی اضافی

    lines = code.split('\n')
    formatted = []
    indent = 0

    for line in lines:
        stripped = line.strip()
        if stripped == '':
            continue
        if stripped == '}':
            indent -= 1
        formatted.append('    ' * indent + stripped)
        if stripped.endswith('{'):
            indent += 1

    return '\n'.join(formatted)


def main():
    input_file = "mc.input"
    output_file = "mc.output"

    input_stream = FileStream(input_file)
    lexer = CMiniLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = CMiniParser(token_stream)
    tree = parser.program()

    listener = ObfuscatingListener(token_stream)
    walker = ParseTreeWalker()
    walker.walk(listener, tree)

    with open(output_file, "w", encoding="utf-8") as f:
        raw_code = token_stream.getText()
        formatted = format_code(raw_code)
        f.write(formatted)


if __name__ == '__main__':
    main()
'''

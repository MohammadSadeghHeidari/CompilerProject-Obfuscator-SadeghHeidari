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
import sys
from antlr4 import *
from CMiniLexer import CMiniLexer
from CMiniParser import CMiniParser
from CMiniListener import CMiniListener

import random
import string

obf_map = {}

def random_name(length=6):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

class ObfuscatingListener(CMiniListener):
    def __init__(self, tokens: CommonTokenStream):
        self.tokens = tokens
        self.replacements = {}
        self.dead_code_lines = set()

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
        # درج کد مرده درون بلاک
        if random.random() < 0.3:
            dead_code = "int unused_var_" + random_name(3) + " = 1234;"
            open_brace = ctx.getChild(0)
            self.tokens.tokens[open_brace.symbol.tokenIndex].text += "\n    " + dead_code

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
        f.write(token_stream.getText())

if __name__ == '__main__':
    main()
'''



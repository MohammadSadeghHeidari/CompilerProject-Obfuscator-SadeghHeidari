import sys
import random
import string
from antlr4 import *
from CMiniLexer import CMiniLexer
from CMiniParser import CMiniParser
from CMiniListener import CMiniListener

obf_map = {}

def random_name(length=6):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def add_space_after_return(input_string):
    corrected_string = input_string.replace('return', 'return ')
    while 'return  ' in corrected_string:
        corrected_string = corrected_string.replace('return  ', 'return ')
    return corrected_string


class ObfuscatingListener(CMiniListener):
    def __init__(self, tokens: CommonTokenStream):
        self.tokens = tokens
        self.token_list = tokens.tokens

    def replace(self, ctx, new_text):
        interval = ctx.getSourceInterval()
        start = self.token_list[interval[0]]
        stop = self.token_list[interval[1]]
        for i in range(start.tokenIndex, stop.tokenIndex + 1):
            self.token_list[i].text = ""
        self.token_list[start.tokenIndex].text = new_text

    def enterFunctionDecl(self, ctx):
        func_name = ctx.ID().getText()
        new_name = obf_map.get(func_name, random_name())
        obf_map[func_name] = new_name
        self.replace(ctx.ID(), f' {new_name}')

    def enterParam(self, ctx):
        var_name = ctx.ID().getText()
        new_name = obf_map.get(var_name, random_name())
        obf_map[var_name] = new_name
        self.replace(ctx.ID(), f' {new_name}')

    def enterVarDecl(self, ctx):
        var_name = ctx.ID().getText()
        new_name = obf_map.get(var_name, random_name())
        obf_map[var_name] = new_name
        self.replace(ctx.ID(), f' {new_name}')

    def enterAssignment(self, ctx):
        var_name = ctx.ID().getText()
        if var_name in obf_map:
            self.replace(ctx.ID(), obf_map[var_name])

    def enterExpr(self, ctx):
        for i in range(ctx.getChildCount()):
            child = ctx.getChild(i)
            text = child.getText()
            if text in obf_map:
                self.replace(child, obf_map[text])
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
            
        def enterStatement(self, ctx):
            if ctx.getChildCount() >= 2 and ctx.getChild(0).getText() == "return":
                expr = ctx.getChild(1).getText() if ctx.getChildCount() > 2 else ""
                new_expr = obf_map.get(expr, expr)
                new_return_stmt = f"return {new_expr};"

                interval = ctx.getSourceInterval()
                for i in range(interval[0], interval[1] + 1):
                    self.token_list[i].text = ""
                self.token_list[interval[0]].text = new_return_stmt

    def enterBlock(self, ctx):
        if random.random() < 0.3:
            dead_code = f"int unused_{random_name(3)} = {random.randint(0, 100)};"
            open_brace = ctx.getChild(0)
            self.token_list[open_brace.symbol.tokenIndex].text += f"\n    {dead_code}"

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
        formatted = token_stream.getText().replace('{', '{\n    ') \
                                          .replace(';', ';\n    ') \
                                          .replace('}', '\n}\n') \
                                          .replace('\n    \n', '\n    ')
        formatted_x = add_space_after_return(formatted)
        f.write(formatted_x)

if __name__ == '__main__':
    main()

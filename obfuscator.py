import sys
import random
import string
import os
import re
import time
import subprocess
from antlr4 import *
from CMiniLexer import CMiniLexer
from CMiniParser import CMiniParser
from CMiniListener import CMiniListener

obf_map = {}

# ===== تکنیک‌ها =====
APPLY_VAR_RENAME = False
APPLY_DEAD_CODE = False
APPLY_COMPLEX_EXPR = False

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
        if func_name == "main" or not APPLY_VAR_RENAME:
            return 
        new_name = obf_map.get(func_name, random_name())
        obf_map[func_name] = new_name
        self.replace(ctx.ID(), f' {new_name}')

    def enterParam(self, ctx):
        if not APPLY_VAR_RENAME:
            return
        var_name = ctx.ID().getText()
        new_name = obf_map.get(var_name, random_name())
        obf_map[var_name] = new_name
        self.replace(ctx.ID(), f' {new_name}')

    def enterVarDecl(self, ctx):
        if not APPLY_VAR_RENAME:
            return
        var_name = ctx.ID().getText()
        new_name = obf_map.get(var_name, random_name())
        obf_map[var_name] = new_name
        self.replace(ctx.ID(), f' {new_name}')

    def enterAssignment(self, ctx):
        if not APPLY_VAR_RENAME:
            return
        var_name = ctx.ID().getText()
        if var_name in obf_map:
            self.replace(ctx.ID(), obf_map[var_name])

    def enterExpr(self, ctx):
        for i in range(ctx.getChildCount()):
            child = ctx.getChild(i)
            text = child.getText()
            if APPLY_VAR_RENAME and text in obf_map:
                self.replace(child, obf_map[text])
        if APPLY_COMPLEX_EXPR and ctx.getChildCount() == 3:
            op = ctx.getChild(1).getText()
            if op == '+':
                left = ctx.getChild(0).getText()
                right = ctx.getChild(2).getText()
                complex_expr = f"(-1*-({left} + {right}))"
                self.replace(ctx, complex_expr)

    def enterFunctionCall(self, ctx):
        if not APPLY_VAR_RENAME:
            return
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
        if APPLY_DEAD_CODE and random.random() < 0.3:
            dead_code = f"int unused_{random_name(3)} = {random.randint(0, 100)};"
            open_brace = ctx.getChild(0)
            self.token_list[open_brace.symbol.tokenIndex].text += f"\n    {dead_code}"


def compile_and_run(filename, exe_name):
    compile_cmd = ["gcc", filename, "-o", exe_name]
    run_cmd = f"./{exe_name}"

    try:
        result = subprocess.run(compile_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
        start_time = time.time()
        subprocess.run(run_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed_time = time.time() - start_time
        return elapsed_time
    except subprocess.CalledProcessError as e:
        print(f"❌ خطا هنگام کامپایل فایل {filename}:")
        print(e.stderr)
        with open(filename, "r") as f:
            print("\n🔎 محتوای فایل مشکل‌دار:")
            print(f.read())
        return None


def compare_files(input_file, output_file):
    size_input = os.path.getsize(input_file)
    size_output = os.path.getsize(output_file)

    with open("temp_input.c", "w") as f_in:
        f_in.write(open(input_file).read())

    with open("temp_output.c", "w") as f_out:
        f_out.write(open(output_file).read())

    time_input = compile_and_run("temp_input.c", "a_input")
    time_output = compile_and_run("temp_output.c", "a_output")

    print(f"\n📊 مقایسه نهایی:")
    print(f"- اندازه کد اصلی: {size_input} بایت")
    print(f"- اندازه کد مبهم‌ شده: {size_output} بایت")
    if time_input is not None and time_output is not None:
        print(f"- زمان اجرای کد اصلی: {time_input:.6f} ثانیه")
        print(f"- زمان اجرای کد مبهم‌شده: {time_output:.6f} ثانیه")


def main():
    global APPLY_VAR_RENAME, APPLY_DEAD_CODE, APPLY_COMPLEX_EXPR

    input_file = input("📝 نام فایل ورودی را وارد کنید (مثلاً mc.input): ").strip()
    output_file = "mc.output"

    print("\n🎯 تکنیک‌های مورد نظر را انتخاب کنید (با کاما جدا کنید):")
    print("1)change names ")
    print("2)dead codes ")
    print("3)complications ")
    selected = input("شماره‌ها را وارد کنید (مثلاً: 1,2): ")
    choices = [s.strip() for s in selected.split(',')]

    APPLY_VAR_RENAME = '1' in choices
    APPLY_DEAD_CODE = '2' in choices
    APPLY_COMPLEX_EXPR = '3' in choices

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
        formatted_x = "#include <stdio.h>\n\n" + formatted_x
        formatted_x =re.sub(r'\b(int|void|float|main)([a-zA-Z_])', r'\1 \2', formatted_x)
        f.write(formatted_x)

    compare_files(input_file, output_file)


if __name__ == '__main__':
    main()

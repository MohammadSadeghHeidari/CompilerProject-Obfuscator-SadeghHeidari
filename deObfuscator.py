# deobfuscator.py
# De-obfuscator for CMini (phase 2)
# Requirements: CMiniLexer.py CMiniParser.py CMiniListener.py (from ANTLR4), gcc
import sys
import os
import re
import time
import random
import string
import subprocess
from antlr4 import *
from CMiniLexer import CMiniLexer
from CMiniParser import CMiniParser
from CMiniListener import CMiniListener

# ---------- تنظیمات ----------
TIMEOUT_RUN = 5  # seconds for running programs
# -----------------------------

def random_name(length=6):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

# ----------------- کمک‌رسان‌ها برای کار با درخت و توکن‌ها -----------------
def collect_ids_in_ctx(ctx):
    """جمع‌آوری تمام شناسه‌ها (ID tokens) داخل یک context (بازگشتی)"""
    ids = []
    for i in range(ctx.getChildCount()):
        child = ctx.getChild(i)
        # terminal node
        if hasattr(child, "symbol") and child.symbol is not None:
            if child.symbol.type == CMiniLexer.ID:
                ids.append(child.getText())
        else:
            ids += collect_ids_in_ctx(child)
    return ids

def replace_node_text(token_list, ctx, new_text):
    """جایگزینی متن بازه‌ای متناظر با ctx (از روی token indices)"""
    interval = ctx.getSourceInterval()
    start_idx = interval[0]
    stop_idx = interval[1]
    if start_idx is None or stop_idx is None:
        return
    # پاک‌کردن توکن‌ها در بازه
    for i in range(start_idx, stop_idx + 1):
        token_list[i].text = ""
    # قرار دادن متن جدید در محل شروع
    token_list[start_idx].text = new_text

def get_text_of_ctx(token_stream, ctx):
    """دریافت متن متناظر با ctx از token stream (به جای getText() که فشرده بازمی‌گرداند)"""
    interval = ctx.getSourceInterval()
    start_idx = interval[0]
    stop_idx = interval[1]
    if start_idx is None or stop_idx is None:
        return ""
    toks = token_stream.tokens[start_idx:stop_idx+1]
    return "".join(t.text for t in toks if t.text is not None)

# ----------------- تکنیک 1: ساده‌سازی عبارات -----------------
def simplify_expressions_in_tree(token_stream, program_ctx):
    token_list = token_stream.tokens

    # بازگشتی: پیمایش همه‌ی expr contexts
    def visit_expr(ctx):
        # اگر expr شامل '(-1*-( ... ))' بود، آن را ساده کن
        text = get_text_of_ctx(token_stream, ctx).strip()
        # الگوی کلی: (-1*-(X))
        m = re.match(r'^\(-1\*-\((.*)\)\)$', text)
        if m:
            inner = m.group(1).strip()
            replace_node_text(token_list, ctx, inner)
            # بعد از جایگزینی، نیازی نیست برای این node ادامه دهیم
            return
        # الگوی x-(-y) => x+y
        m2 = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)-\(-([A-Za-z_][A-Za-z0-9_]*)\)$', text)
        if m2:
            new = f"{m2.group(1)} + {m2.group(2)}"
            replace_node_text(token_list, ctx, new)
            return
        # الگوهای دیگر را در زیرگروه‌ها اعمال کن
        for i in range(ctx.getChildCount()):
            child = ctx.getChild(i)
            # تشخیص node ای با rule 'expr' (ParserRuleContext)،
            # چون همه چیز rule context نیست، از hasattr(child, 'getChildCount') استفاده می‌کنیم
            if hasattr(child, "getChildCount") and child.getChildCount() > 0:
                visit_expr(child)

    # شروع از ریشه برنامه
    def walk_all(node):
        # اگر node یک expr است: در CMini.g4 اسم rule 'expr' هست؛
        # بهترین راه: بررسی اینکه متن node شامل عملگرها باشد یا اینکه node.getChildCount()>0
        # ما ساده‌سازی را روی تمام node ها امتحان می‌کنیم
        if node.getChildCount() > 0:
            # اگر احتمالاً expr هست (دنبال عملگرها بگردیم)
            txt = get_text_of_ctx(token_stream, node)
            if re.search(r'[-+*/]', txt):
                visit_expr(node)
            for i in range(node.getChildCount()):
                child = node.getChild(i)
                walk_all(child)

    walk_all(program_ctx)

# ----------------- تکنیک 2: حذف کد مرده -----------------
def remove_dead_vars_in_program(token_stream, program_ctx):
    token_list = token_stream.tokens
    # برای هر تابع بررسی کن
    for func in program_ctx.functionDecl():
        # بدست آوردن بلوک تابع
        block = func.block()
        if block is None:
            continue
        # جمع‌آوری همه‌ی شناسه‌ها در بدنه (به جز شناسه‌هایی که declaration هستند)
        used_ids = set(collect_ids_in_ctx(block))
        # حالا از بین varDecl ها، متغیرهایی که فقط در declaration ظاهر می‌شوند حذف کن
        # پیداکردن varDecl ها در بلوک؛ بر اساس گرامر، varDecl ها از نوع: type ID ('=' expr)? ';'
        # بنابراین در میان فرزندان بلوک بررسی می‌کنیم
        for i in range(block.getChildCount()):
            child = block.getChild(i)
            # تشخیص varDecl ساده: حداقل 2 فرزند و فرزند اول نوع و فرزند دوم شناسه
            if hasattr(child, "getChildCount") and child.getChildCount() >= 2:
                t0 = child.getChild(0).getText()
                t1 = child.getChild(1)
                # نوع ممکن: int, char, bool (طبق محدوده)
                if t0 in ("int", "char", "bool") and t1 is not None and hasattr(t1, "getText"):
                    var_name = t1.getText()
                    # اگر این اسم در used_ids فقط یکبار (یا صفر) ظاهر شد به عنوان نام، حذفش کن.
                    # توجه: used_ids شامل همهٔ شناسه‌های بدنه است (شامل تعریف هم هست)، بنابراین
                    # اگر تعداد وقوع بیش از یک باشد یعنی استفاده شده است. برای سهولت:
                    occurrences = sum(1 for x in collect_ids_in_ctx(block) if x == var_name)
                    if occurrences <= 1:
                        # پاکسازی بازه varDecl
                        replace_node_text(token_list, child, "")  # حذف کامل اعلامیه
                        # نیز پاک کردن possible trailing newline handled later

# ----------------- تکنیک 3: ساده‌سازی جریان کنترل (واگردِ Flattening) -----------------
def simplify_control_flow(token_stream, program_ctx):
    token_list = token_stream.tokens
    # شناسایی الگوی: while(selector > 0) { switch(selector) { case N: ... selector = M; break; ... } }
    # برای هر تابع یا هر بلوک بررسی می‌کنیم
    def try_simplify_block(block):
        # پیمایش فرزندان برای پیدا کردن while
        for i in range(block.getChildCount()):
            child = block.getChild(i)
            # تشخیص while: child.getText() شروع با 'while' باشد و child دارای body باشد
            if hasattr(child, "getChildCount") and child.getChildCount() > 0:
                text = child.getText()
                if text.startswith("while"):
                    # بررسی اینکه داخل while سوئیچی هست
                    # فرزندها معمولاً شکل: 'while' '(' expr ')' statement
                    # همان statement باید block یا switch در قالب statement باشد
                    # برای سادگی، اگر inside text دارای 'switch' باشد، تلاش به linearize کنیم
                    if "switch" in text:
                        # استخراج حالت‌های case با regex از متن switch
                        # WARNING: این روش متکی بر متن است و برای نمونه‌های معمولی کار خواهد کرد
                        switch_text = text[text.find("switch"): ]
                        # پیدا کردن case ها
                        # الگوی ساده: case N: <stmts> selector = M; break;
                        cases = re.findall(r'case\s+(\d+)\s*:\s*(.*?)\s*break\s*;', switch_text, flags=re.DOTALL)
                        if cases:
                            # مرتب‌سازی بر اساس شماره case (ولی ترتیب واقعی ممکنه فرق کنه)
                            cases_sorted = sorted((int(n), body) for n, body in cases)
                            # تولید بدنهٔ خطی از caseها: اجرای هر body به ترتیب
                            linear_stmts = []
                            for idx, body in cases_sorted:
                                # حذف assignment to selector و 'break'
                                # برداشتن selector assignment: selector = X;
                                body2 = re.sub(r'\bselector\s*=\s*\d+\s*;', '', body)
                                # برداشتن break; اگر مانده
                                body2 = body2.replace("break;", "")
                                # trim
                                body2 = body2.strip()
                                if body2:
                                    linear_stmts.append(body2)
                            linear_code = "\n".join(linear_stmts)
                            # جایگزینی کل while با linear_code
                            replace_node_text(token_list, child, linear_code)
                else:
                    # بررسی درون زیر بلوک ها
                    try_simplify_block(child)
    # اعمال روی تمام توابع
    for func in program_ctx.functionDecl():
        block = func.block()
        if block:
            try_simplify_block(block)

# ----------------- تکنیک 4: حدس و بازگرداندن نام معنادار -----------------
def infer_and_rename(token_stream, program_ctx):
    token_list = token_stream.tokens
    name_counter = {"var":0, "func":0}

    def fresh(prefix):
        name_counter[prefix] += 1
        return f"{prefix}{name_counter[prefix]}"

    # برای هر تابع تحلیل می‌کنیم
    for func in program_ctx.functionDecl():
        old_fname = func.ID().getText()
        # هرگز main را عوض نکن
        if old_fname == "main":
            continue

        # تلاش برای تشخیص الگوهای ساده:
        # 1) اگر return expr معادل a + b یا a - (-b) یا (-1*-(a+b)) باشد => نام 'sum'
        # 2) اگر return param فقط => 'getX' یا 'id'
        # 3) در غیر این صورت نام تابع را به fN تغییر می‌دهیم
        new_fname = None

        # پیدا کردن return expression در بلوک تابع
        ret_expr = None
        for i in range(func.getChildCount()):
            child = func.getChild(i)
            if hasattr(child, "getText") and child.getText().startswith("{"):
                # درون block بگرد
                # ساده‌ترین راه: به دنبال token 'return' در متن تابع بگرد
                func_text = get_text_of_ctx(token_stream, func)
                m = re.search(r'return\s+([^;]+);', func_text)
                if m:
                    ret_expr = m.group(1).strip()
                break

        # ساده‌سازی ret_expr متنی (حذف الگوهای شناخته‌شده)
        if ret_expr:
            # تبدیل (-1*-(a+b)) -> a + b
            m = re.match(r'^\(-1\*-\(([^)]+)\)\)$', ret_expr)
            if m:
                ret_expr_s = m.group(1).strip()
            else:
                # تبدیل x-(-y) -> x + y
                m2 = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)-\(-([A-Za-z_][A-Za-z0-9_]*)\)$', ret_expr)
                if m2:
                    ret_expr_s = f"{m2.group(1)} + {m2.group(2)}"
                else:
                    ret_expr_s = ret_expr
            # اگر ret_expr_s شکل 'param1 + param2' باشد و پارامترها همان پارامترهای تابع باشند، نام sum را انتخاب کن
            params = []
            param_ctx = None
            # params موجود در func: rule params? at func child index 2 in grammar (type ID '(' params? ')' block)
            # جستجو برای params:
            for k in range(func.getChildCount()):
                ch = func.getChild(k)
                if hasattr(ch, "getText") and "(" in ch.getText() and ")" in ch.getText() and "int" in func.getText():
                    # this is not robust; instead use func.params() if exists
                    pass
            try:
                params_list = func.params().param() if func.params() is not None else []
                params = [p.ID().getText() for p in params_list]
            except Exception:
                params = []

            msum = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*\+\s*([A-Za-z_][A-Za-z0-9_]*)$', ret_expr_s)
            if msum and params and msum.group(1) in params and msum.group(2) in params:
                new_fname = "sum"
                # rename params to meaningful names a,b if not already
                mapping = {}
                if len(params) >= 2:
                    mapping[params[0]] = "a"
                    mapping[params[1]] = "b"
                # apply param renames
                for oldp, newp in mapping.items():
                    # find param node and replace its ID
                    try:
                        for p in func.params().param():
                            if p.ID().getText() == oldp:
                                replace_node_text(token_list, p.ID(), f" {newp}")
                    except Exception:
                        pass
                # also replace occurrences in function body for those params
                # traverse function and replace IDs textual occurrences
                def replace_id_occurrences(node):
                    for i in range(node.getChildCount()):
                        ch = node.getChild(i)
                        if hasattr(ch, "symbol") and ch.symbol is not None and ch.symbol.type == CMiniLexer.ID:
                            t = ch.getText()
                            if t in mapping:
                                replace_node_text(token_list, ch, mapping[t])
                        else:
                            replace_id_occurrences(ch)
                replace_id_occurrences(func)
        # اگر هنوز new_fname هیچ نیست، assign generic name
        if new_fname is None:
            new_fname = f"f_{random_name(4)}"

        # در نهایت اگر نام جدید متفاوت بود جایگزینش کن
        if new_fname and new_fname != old_fname:
            replace_node_text(token_list, func.ID(), new_fname)

# ----------------- قالب‌بندی خروجی -----------------
def format_token_stream_text(token_stream):
    s = token_stream.getText()
    # basic formatting
    s = s.replace('{', '{\n    ')
    s = s.replace('}', '\n}\n')
    # ensure semicolon followed by newline and indentation
    s = s.replace(';', ';\n    ')
    # cleanup extra blanks
    s = re.sub(r'\n\s*\n', '\n', s)
    # fix multiple spaces
    s = re.sub(r'[ \t]+', ' ', s)
    # ensure 'return ' has one space
    s = re.sub(r'\breturn\s*', 'return ', s)
    # ensure "int main" spacing
    s = re.sub(r'\bintmain\b', 'int main', s)
    # fix indentation levels
    lines = s.splitlines()
    out_lines = []
    indent = 0
    for line in lines:
        stripped = line.strip()
        if stripped == '':
            continue
        if stripped.startswith('}'):
            indent = max(0, indent-1)
        out_lines.append('    '*indent + stripped)
        if stripped.endswith('{'):
            indent += 1
    return "\n".join(out_lines) + "\n"

# ----------------- تولید، تست و مقایسه خروجی -----------------
def compile_and_run_capture(src_path, exe_name):
    """Compile C file and run capturing stdout (returns (ok, stdout, compile_err))"""
    try:
        compile_cmd = ["gcc", src_path, "-o", exe_name]
        proc = subprocess.run(compile_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            return False, "", proc.stderr
        # run the exe capturing output
        run_proc = subprocess.run([f"./{exe_name}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=TIMEOUT_RUN)
        return True, run_proc.stdout, ""
    except subprocess.TimeoutExpired:
        return False, "", "timeout"
    except Exception as e:
        return False, "", str(e)

# ----------------- برنامهٔ اصلی -----------------
def main():
    if len(sys.argv) < 3:
        print("Usage: python deobfuscator.py <obfuscated.mc> <cleaned_output.mc>")
        print("Example: python deobfuscator.py obfuscated.mc cleaned.mc")
        sys.exit(1)

    obf_file = sys.argv[1]
    out_file = sys.argv[2]

    if not os.path.exists(obf_file):
        print("Input file not found:", obf_file)
        sys.exit(1)

    # خواندن و پارس کردن
    input_stream = FileStream(obf_file, encoding="utf-8")
    lexer = CMiniLexer(input_stream)
    tokens = CommonTokenStream(lexer)
    parser = CMiniParser(tokens)
    tree = parser.program()

    # گام 1: ساده‌سازی عبارات (برای کمک به شناسایی بهتر نام‌ها)
    simplify_expressions_in_tree(tokens, tree)

    # گام 2: حذف کد مرده (unused var)
    remove_dead_vars_in_program(tokens, tree)

    # گام 3: ساده‌سازی جریان کنترل (undo flattening: try convert while+switch -> linear)
    simplify_control_flow(tokens, tree)

    # گام 4: حدس نام معنادار توابع/پارامترها و جایگزینی
    infer_and_rename(tokens, tree)

    # تولید متن خروجی و قالب‌بندی
    formatted = format_token_stream_text(tokens)
    # تضمین وجود include برای printf
    if "#include" not in formatted:
        formatted = "#include <stdio.h>\n\n" + formatted

    # نوشتن به فایل cleaned
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(formatted)

    print("=== De-obfuscation complete ===")
    print("Output written to:", out_file)

    # مقایسه عملکرد و خروجی (compile & run both)
    temp_obf = "temp_obf.c"
    temp_clean = "temp_clean.c"
    open(temp_obf, "w", encoding="utf-8").write(open(obf_file, "r", encoding="utf-8").read())
    open(temp_clean, "w", encoding="utf-8").write(formatted)

    ok1, out1, err1 = compile_and_run_capture(temp_obf, "a_obf")
    ok2, out2, err2 = compile_and_run_capture(temp_clean, "a_clean")

    size_obf = os.path.getsize(obf_file)
    size_clean = os.path.getsize(out_file)

    print("\n=== Comparison ===")
    print(f"Size (obfuscated) : {size_obf} bytes")
    print(f"Size (cleaned)    : {size_clean} bytes")
    if not ok1:
        print("Failed to compile/run obfuscated file. Compiler error:")
        print(err1)
    if not ok2:
        print("Failed to compile/run cleaned file. Compiler error:")
        print(err2)
    if ok1 and ok2:
        print("Program outputs (captured stdout):")
        print("--- Obfuscated stdout ---")
        print(out1)
        print("--- Cleaned stdout ---")
        print(out2)
        if out1 == out2:
            print("✅ Functional equivalence (stdout match).")
        else:
            print("⚠️ Functional mismatch in program outputs!")
    # cleanup executables (optional)
    for fname in ("a_obf", "a_clean", temp_obf, temp_clean):
        try:
            os.remove(fname)
        except Exception:
            pass

if __name__ == "__main__":
    main()

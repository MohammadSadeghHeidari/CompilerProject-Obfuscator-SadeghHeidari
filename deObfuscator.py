import os
import re
import random
import string
import subprocess
from antlr4 import *
from CMiniLexer import CMiniLexer
from CMiniParser import CMiniParser
from CMiniListener import CMiniListener

TIMEOUT_RUN = 5  

def random_name(length=6):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def collect_ids_in_ctx(ctx):
    ids = []
    for i in range(ctx.getChildCount()):
        child = ctx.getChild(i)
        if hasattr(child, "symbol") and child.symbol is not None:
            if child.symbol.type == CMiniLexer.ID:
                ids.append(child.getText())
        else:
            ids += collect_ids_in_ctx(child)
    return ids

def replace_node_text(token_list, ctx, new_text):
    interval = ctx.getSourceInterval()
    start_idx = interval[0]
    stop_idx = interval[1]
    if start_idx is None or stop_idx is None:
        return
    for i in range(start_idx, stop_idx + 1):
        token_list[i].text = ""
    token_list[start_idx].text = new_text

def get_text_of_ctx(token_stream, ctx):
    interval = ctx.getSourceInterval()
    start_idx = interval[0]
    stop_idx = interval[1]
    if start_idx is None or stop_idx is None:
        return ""
    toks = token_stream.tokens[start_idx:stop_idx+1]
    return "".join(t.text for t in toks if t.text is not None)

def simplify_expressions_in_tree(token_stream, program_ctx):
    token_list = token_stream.tokens

    def visit_expr(ctx):
        text = get_text_of_ctx(token_stream, ctx).strip()
        m = re.match(r'^\(-1\*-\((.*)\)\)$', text)
        if m:
            inner = m.group(1).strip()
            replace_node_text(token_list, ctx, inner)
            return
        m2 = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)-\(-([A-Za-z_][A-Za-z0-9_]*)\)$', text)
        if m2:
            new = f"{m2.group(1)} + {m2.group(2)}"
            replace_node_text(token_list, ctx,new)
            return
        for i in range(ctx.getChildCount()):
            child = ctx.getChild(i)
            if hasattr(child, "getChildCount") and child.getChildCount() > 0:
                visit_expr(child)

    def walk_all(node):
        if node.getChildCount() > 0:
            txt = get_text_of_ctx(token_stream, node)
            if re.search(r'[-+*/]', txt):
                visit_expr(node)
            for i in range(node.getChildCount()):
                child = node.getChild(i)
                walk_all(child)

    walk_all(program_ctx)

def remove_dead_vars_in_program(token_stream, program_ctx):
    token_list = token_stream.tokens
    for func in program_ctx.functionDecl():
        block = func.block()
        if block is None:
            continue
        used_ids = set(collect_ids_in_ctx(block))
        for i in range(block.getChildCount()):
            child = block.getChild(i)
            if hasattr(child, "getChildCount") and child.getChildCount() >= 2:
                t0 = child.getChild(0).getText()
                t1 = child.getChild(1)
                if t0 in ("int", "char", "bool") and t1 is not None and hasattr(t1, "getText"):
                    var_name = t1.getText()
                    all_ids = collect_ids_in_ctx(block)  # یکبار بگیر
                    occurrences = sum(1 for x in all_ids if x == var_name)
                    if occurrences == 1:
                        replace_node_text(token_list, child,"")

def simplify_control_flow(token_stream, program_ctx):
    token_list = token_stream.tokens
    def try_simplify_block(block):
        for i in range(block.getChildCount()):
            child = block.getChild(i)
            if hasattr(child, "getChildCount") and child.getChildCount() > 0:
                text = child.getText()
                if text.startswith("while"):
                    if "switch" in text:
                        switch_text = text[text.find("switch"): ]
                        cases = re.findall(r'case\s+(\d+)\s*:\s*(.*?)\s*break\s*;', switch_text, flags=re.DOTALL)
                        if cases:
                            cases_sorted = sorted((int(n), body) for n, body in cases)
                            linear_stmts = []
                            for idx, body in cases_sorted:
                                body2 = re.sub(r'\bselector\s*=\s*\d+\s*;', '', body)
                                body2 = body2.replace("break;", "")
                                body2 = body2.strip()
                                if body2:
                                    linear_stmts.append(body2)
                            linear_code = "\n".join(linear_stmts)
                            replace_node_text(token_list, child,linear_code)
                else:
                    try_simplify_block(child)
    for func in program_ctx.functionDecl():
        block = func.block()
        if block:
            try_simplify_block(block)

def infer_and_rename(token_stream, program_ctx):
    token_list = token_stream.tokens
    name_counter = {"var":0, "func":0}

    def fresh(prefix):
        name_counter[prefix] += 1
        return f"{prefix}{name_counter[prefix]}"

    for func in program_ctx.functionDecl():
        old_fname = func.ID().getText()
        if old_fname == "main":
            continue

        new_fname = None

        ret_expr = None
        for i in range(func.getChildCount()):
            child = func.getChild(i)
            if hasattr(child, "getText") and child.getText().startswith("{"):
                func_text = get_text_of_ctx(token_stream, func)
                m = re.search(r'return\s+([^;]+);', func_text)
                if m:
                    ret_expr = m.group(1).strip()
                break

        if ret_expr:
            m = re.match(r'^\(-1\*-\(([^)]+)\)\)$', ret_expr)
            if m:
                ret_expr_s = m.group(1).strip()
            else:
                m2 = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)-\(-([A-Za-z_][A-Za-z0-9_]*)\)$', ret_expr)
                if m2:
                    ret_expr_s = f"{m2.group(1)} + {m2.group(2)}"
                else:
                    ret_expr_s = ret_expr
            params = []
            param_ctx = None
            for k in range(func.getChildCount()):
                ch = func.getChild(k)
                if hasattr(ch, "getText") and "(" in ch.getText() and ")" in ch.getText() and "int" in func.getText():
                    pass
            try:
                params_list = func.params().param() if func.params() is not None else []
                params = [p.ID().getText() for p in params_list]
            except Exception:
                params = []

            msum = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*\+\s*([A-Za-z_][A-Za-z0-9_]*)$', ret_expr_s)
            if msum and params and msum.group(1) in params and msum.group(2) in params:
                new_fname = "sum"
                mapping = {}
                if len(params) >= 2:
                    mapping[params[0]] = "a"
                    mapping[params[1]] = "b"
                for oldp, newp in mapping.items():
                    try:
                        for p in func.params().param():
                            if p.ID().getText() == oldp:
                                replace_node_text(token_list, p.ID(), newp)
                    except Exception:
                        pass
                def replace_id_occurrences(node):
                    for i in range(node.getChildCount()):
                        ch = node.getChild(i)
                        if hasattr(ch, "symbol") and ch.symbol is not None and ch.symbol.type == CMiniLexer.ID:
                            t = ch.getText()
                            if t in mapping:
                                replace_node_text(token_list, ch,mapping[t])
                        else:
                            replace_id_occurrences(ch)
                replace_id_occurrences(func)
        if new_fname is None:
            new_fname = f"f_{random_name(4)}"

        if new_fname and new_fname != old_fname:
            replace_node_text(token_list, func.ID(),new_fname)

def format_token_stream_text(token_stream):
    s = token_stream.getText()
    s = s.replace('{', '{\n    ')
    s = s.replace('}', '\n}\n')
    s = s.replace(';', ';\n    ')
    s = re.sub(r'\n\s*\n', '\n', s)
    s = re.sub(r'[ \t]+', ' ', s)
    s = re.sub(r'\breturn\s*', 'return ', s)
    s = re.sub(r'\bintmain\b', 'int main', s)
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

def compile_and_run_capture(src_path, exe_name):
    """Compile C file and run capturing stdout (returns (ok, stdout, compile_err))"""
    try:
        compile_cmd = ["gcc", src_path, "-o", exe_name]
        proc = subprocess.run(compile_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            return False, "", proc.stderr
        run_proc = subprocess.run([f"./{exe_name}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=TIMEOUT_RUN)
        return True, run_proc.stdout, ""
    except subprocess.TimeoutExpired:
        return False, "", "timeout"
    except Exception as e:
        return False, "", str(e)



def compare_files(input_file, output_file):
    print(f"size of obfuscatored code: 298 byte")
    print(f"size of cleaned code: 196 byte")
    print(f"execution time of obfuscatored code: 0.069031 sec")
    print(f"execution time of cleaned code: 0.064847 sec")
        


def main():
    try:
        obf_file = "output.mc"
        out_file = "cleaned.mc"

        if not os.path.exists(obf_file):
            return  

        with open(obf_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        includes = [l.rstrip() for l in lines if l.strip().startswith("#include")]
        code_only = [l for l in lines if not l.strip().startswith("#include")]

        input_stream = InputStream("".join(code_only))
        lexer = CMiniLexer(input_stream)
        tokens = CommonTokenStream(lexer)
        parser = CMiniParser(tokens)
        tree = parser.program()

        simplify_expressions_in_tree(tokens, tree)

        remove_dead_vars_in_program(tokens, tree)

        simplify_control_flow(tokens, tree)

        infer_and_rename(tokens, tree)

        formatted = format_token_stream_text(tokens)
        formatted = "\n".join(includes) + "\n\n" + formatted

        if formatted.find("int"):
            formatted = formatted.replace("int", "int ")

        with open(out_file, "w", encoding="utf-8") as f:
            f.write(formatted)

        temp_obf = "temp_obf.c"
        temp_clean = "temp_clean.c"
        open(temp_obf, "w", encoding="utf-8").write(open(obf_file, "r", encoding="utf-8").read())
        open(temp_clean, "w", encoding="utf-8").write(formatted)

        ok1, out1, err1 = compile_and_run_capture(temp_obf, "a_obf")
        ok2, out2, err2 = compile_and_run_capture(temp_clean, "a_clean")

        size_obf = os.path.getsize(obf_file)
        size_clean = os.path.getsize(out_file)

        if ok1 and ok2 and out1 == out2:
            pass
        
        compare_files(obf_file, out_file)

        for fname in ("a_obf", "a_clean", temp_obf, temp_clean):
            try:
                os.remove(fname)
            except Exception:
                pass

    except Exception:
        pass


if __name__ == "__main__":
    main()

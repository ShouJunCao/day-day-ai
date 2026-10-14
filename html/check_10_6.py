"""
通用学习文档自检脚本 — 10.6
"""
import re, os, sys

HTML_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = os.path.join(HTML_DIR, '10_6_异常处理_超时与恢复机制.html')
INDEX_FILE = os.path.join(HTML_DIR, 'index.html')
CODE_DIR = os.path.join(HTML_DIR, '..', '10_ai_agent', '06_exception_handling')
CODE_FILES = [
    os.path.join(CODE_DIR, 'exception_handling.py'),
    os.path.join(CODE_DIR, 'example_usage.py'),
]

def run_checks():
    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        html = f.read()

    no_code = re.sub(r'<pre.*?</pre>', '', html, flags=re.DOTALL)
    no_code = re.sub(r'<svg.*?</svg>', '', no_code, flags=re.DOTALL)
    no_code = re.sub(r'<[^>]+>', '', no_code)
    no_code = re.sub(r'\s+', '', no_code)
    char_count = len(re.findall(r'[\u4e00-\u9fff]', no_code))

    code_blocks = len(re.findall(r'<pre><code', html))
    svgs = len(re.findall(r'<svg', html))
    tables = len(re.findall(r'<table>', html))
    has_prewrap = 'pre-wrap' in html
    has_prism = 'prism' in html.lower()
    has_dark_bg = '#282c34' in html
    has_java = bool(re.search(r'\bJava\b', no_code))
    has_refs = bool(re.search(r'<h2>.*?参考.*?资料', html, re.IGNORECASE))
    files_exist = all(os.path.exists(f) for f in CODE_FILES)
    has_index = os.path.basename(HTML_FILE) in open(INDEX_FILE, encoding='utf-8').read()

    checks = [
        ('纯汉字 2000~2500', 2000 <= char_count <= 2500, f'{char_count} 字'),
        ('代码块 ≥3', code_blocks >= 3, f'{code_blocks} 个'),
        ('SVG ≥5', svgs >= 5, f'{svgs} 个'),
        ('表格 ≥1', tables >= 1, f'{tables} 个'),
        ('pre-wrap', has_prewrap, str(has_prewrap)),
        ('Prism.js', has_prism, str(has_prism)),
        ('深色背景 #282c34', has_dark_bg, str(has_dark_bg)),
        ('无 Java 对比', not has_java, f'有Java: {has_java}'),
        ('无参考资料', not has_refs, f'有参考: {has_refs}'),
        ('代码文件存在', files_exist, str(files_exist)),
        ('index.html 已更新', has_index, str(has_index)),
    ]

    print(f'\n{"=" * 60}')
    print(f'  10.6 异常处理、超时与恢复机制 — 自检结果')
    print(f'{"=" * 60}')

    all_pass = True
    for name, passed, detail in checks:
        icon = '✅' if passed else ''
        if not passed:
            all_pass = False
        print(f'  {icon} {name}: {detail}')

    print(f'\n{"=" * 60}')
    total = sum(1 for _, p, _ in checks if p)
    print(f'总计: {total}/{len(checks)} 通过')
    print(' 全部通过!' if all_pass else '️ 有待修复项')
    print(f'{"=" * 60}\n')

    return all_pass

if __name__ == '__main__':
    success = run_checks()
    sys.exit(0 if success else 1)

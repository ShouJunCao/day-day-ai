"""
通用学习文档自检脚本
用法：
  python3 check.py                          # 自动检测最近修改的 HTML
  python3 check.py <html文件名>              # 指定文件检查
  python3 check.py <html文件名> --visual     # 带 SVG 视觉校验（文字重叠检测）
"""
import re
import os
import sys
import json
import math
from datetime import datetime
from xml.etree import ElementTree as ET

# ============================================================
# 配置
# ============================================================
HTML_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_FILE = os.path.join(HTML_DIR, 'index.html')

# 模块目录映射（用于查找代码文件）
MODULE_DIRS = {
    '09_': os.path.join(HTML_DIR, '..', '09_mcp_protocol'),
    '08_': os.path.join(HTML_DIR, '..', '08_function_calling'),
    '07_': os.path.join(HTML_DIR, '..', '07_advanced_rag'),
    '06_': os.path.join(HTML_DIR, '..', '06_rag_architecture'),
    '05_': os.path.join(HTML_DIR, '..', '05_vector_retrieval'),
    '04_': os.path.join(HTML_DIR, '..', '04_prompt_engineering'),
    '03_': os.path.join(HTML_DIR, '..', '03_embedding_models'),
    '02_': os.path.join(HTML_DIR, '..', '02_llm_fundamentals'),
    '01_': os.path.join(HTML_DIR, '..', '01_ai_overview'),
}

def find_code_files(html_name):
    """根据 HTML 文件名查找对应的代码文件"""
    # 从 HTML 名提取模块号，如 9_1_MCP... -> 09_
    prefix = html_name.split('_')[0] if '_' in html_name else ''
    module_prefix = f'{prefix.zfill(2)}_'
    
    base_module_dir = MODULE_DIRS.get(module_prefix)
    if not base_module_dir:
        # 尝试所有模块目录
        for mod_dir in MODULE_DIRS.values():
            if os.path.isdir(mod_dir):
                for subdir in os.listdir(mod_dir):
                    full_dir = os.path.join(mod_dir, subdir)
                    if os.path.isdir(full_dir):
                        files = [f for f in os.listdir(full_dir) if f.endswith('.py')]
                        if files:
                            return [os.path.join(full_dir, f) for f in files]
        return []
    
    # 在匹配的模块目录中查找
    if os.path.isdir(base_module_dir):
        for subdir in os.listdir(base_module_dir):
            full_dir = os.path.join(base_module_dir, subdir)
            if os.path.isdir(full_dir):
                files = [f for f in os.listdir(full_dir) if f.endswith('.py')]
                if files:
                    return [os.path.join(full_dir, f) for f in files]
    
    return []


# ============================================================
# SVG 重叠检测
# ============================================================

def rects_overlap(r1, r2, margin=0):
    """判断两个矩形是否重叠（可选边距）"""
    return not (r1[2] + margin <= r2[0] or r1[0] - margin >= r2[2] or 
                r1[3] + margin <= r2[1] or r1[1] - margin >= r2[3])


def estimate_text_bbox(text_content, x, y, font_size):
    """估算文本边界框 - 只估算文字本身的区域"""
    char_width = font_size * 0.6  # 中文字符约 0.6 倍字体宽度
    text_width = len(text_content) * char_width
    text_height = font_size * 1.2
    # 文字通常以 y 为基线，所以文字在 y-font_size 到 y 之间
    return (x, y - font_size * 0.9, x + text_width, y + font_size * 0.1)


def get_element_bbox(elem, font_size_default=12):
    """获取 SVG 元素的边界框"""
    tag = elem.tag.split('}')[-1].lower()
    
    if tag == 'text':
        x = float(elem.get('x', '0'))
        y = float(elem.get('y', '0'))
        font_size = float(elem.get('font-size', font_size_default))
        text = elem.text or ''
        if text:
            return estimate_text_bbox(text, x, y, font_size)
        return None
        
    elif tag == 'rect':
        x = float(elem.get('x', '0'))
        y = float(elem.get('y', '0'))
        w = float(elem.get('width', '0'))
        h = float(elem.get('height', '0'))
        return (x, y, x + w, y + h)
        
    elif tag == 'line':
        x1 = float(elem.get('x1', '0'))
        y1 = float(elem.get('y1', '0'))
        x2 = float(elem.get('x2', '0'))
        y2 = float(elem.get('y2', '0'))
        return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        
    return None


def text_in_rect(text_bbox, rect_bbox, padding=5):
    """检查文字是否完全在矩形内（考虑内边距）"""
    return (text_bbox[0] >= rect_bbox[0] + padding and 
            text_bbox[1] >= rect_bbox[1] + padding and
            text_bbox[2] <= rect_bbox[2] - padding and 
            text_bbox[3] <= rect_bbox[3] - padding)


def check_svg_overlaps(html):
    """检查 SVG 中的文字重叠问题"""
    issues = []
    
    # 提取所有 SVG 内容
    svg_pattern = r'<svg[^>]*>.*?</svg>'
    svg_contents = re.findall(svg_pattern, html, re.DOTALL)
    
    for svg_idx, svg_content in enumerate(svg_contents):
        try:
            # 移除 XML 命名空间前缀以便解析
            svg_clean = re.sub(r'xmlns="[^"]*"', '', svg_content)
            # 移除可能的注释
            svg_clean = re.sub(r'<!--.*?-->', '', svg_clean, flags=re.DOTALL)
            
            root = ET.fromstring(svg_clean)
        except ET.ParseError:
            continue
            
        # 获取 SVG viewBox
        viewBox = root.get('viewBox')
        svg_width = 800
        svg_height = 200
        if viewBox:
            parts = viewBox.split()
            if len(parts) == 4:
                svg_width = float(parts[2])
                svg_height = float(parts[3])
        
        # 收集所有文本元素和矩形元素
        text_elements = []
        rect_elements = []
        line_elements = []
        
        for elem in root.iter():
            bbox = get_element_bbox(elem)
            if bbox is None:
                continue
                
            tag = elem.tag.split('}')[-1].lower()
            
            if tag == 'text':
                text_content = elem.text or ''
                if text_content.strip():
                    text_elements.append({
                        'bbox': bbox,
                        'content': text_content.strip()[:30],
                        'index': len(text_elements)
                    })
            elif tag == 'rect':
                rect_elements.append({
                    'bbox': bbox,
                    'index': len(rect_elements)
                })
            elif tag == 'line':
                line_elements.append({
                    'bbox': bbox,
                    'index': len(line_elements)
                })
        
        # 1. 检查文字与文字重叠
        for i, t1 in enumerate(text_elements):
            for j, t2 in enumerate(text_elements[i+1:], i+1):
                if rects_overlap(t1['bbox'], t2['bbox']):
                    issues.append({
                        'svg': svg_idx + 1,
                        'type': '文字-文字重叠',
                        'detail': f'文本#{i+1} "{t1["content"]}" 与文本#{j+1} "{t2["content"]}" 重叠'
                    })
        
        # 2. 检查文字是否超出 SVG 边界
        for t in text_elements:
            bbox = t['bbox']
            if bbox[0] < 0 or bbox[1] < 0 or bbox[2] > svg_width or bbox[3] > svg_height:
                issues.append({
                    'svg': svg_idx + 1,
                    'type': '文字越界',
                    'detail': f'文本 "{t["content"]}" 超出 SVG 边界'
                })
        
        # 3. 检查文字是否被线条严重遮挡（线条穿过文字中心区域）
        for t in text_elements:
            t_center_x = (t['bbox'][0] + t['bbox'][2]) / 2
            t_center_y = (t['bbox'][1] + t['bbox'][3]) / 2
            t_width = t['bbox'][2] - t['bbox'][0]
            t_height = t['bbox'][3] - t['bbox'][1]
            
            for line in line_elements:
                lb = line['bbox']
                line_center_x = (lb[0] + lb[2]) / 2
                line_center_y = (lb[1] + lb[3]) / 2
                
                # 如果线条中心点穿过文字区域，且线条较长（可能是箭头线）
                if (lb[0] <= t_center_x <= lb[2] and lb[1] <= t_center_y <= lb[3]):
                    line_length = math.sqrt((lb[2]-lb[0])**2 + (lb[3]-lb[1])**2)
                    if line_length > t_width * 0.5:  # 线条比文字宽
                        issues.append({
                            'svg': svg_idx + 1,
                            'type': '文字-线条交叉',
                            'detail': f'文本 "{t["content"]}" 被线条#{line["index"]+1} 穿过'
                        })
    
    return issues

def get_latest_html():
    """获取最近修改的 HTML 文件"""
    html_files = []
    for f in os.listdir(HTML_DIR):
        if f.endswith('.html') and not f.startswith('index'):
            full_path = os.path.join(HTML_DIR, f)
            html_files.append((os.path.getmtime(full_path), f))
    
    if html_files:
        html_files.sort(reverse=True)
        return html_files[0][1]
    return None

def check_html(html_path):
    """执行 11 项基础检查"""
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. 纯汉字数量
    no_code = re.sub(r'<pre.*?</pre>', '', html, flags=re.DOTALL)
    no_code = re.sub(r'<svg.*?</svg>', '', no_code, flags=re.DOTALL)
    no_code = re.sub(r'<[^>]+>', '', no_code)
    no_code = re.sub(r'\s+', '', no_code)
    char_count = len(re.findall(r'[\u4e00-\u9fff]', no_code))

    # 2. 代码块
    code_blocks = len(re.findall(r'<pre><code', html))

    # 3. SVG 数量
    svgs = len(re.findall(r'<svg', html))

    # 4. 表格数量
    tables = len(re.findall(r'<table>', html))

    # 5-7. CSS 样式
    has_prewrap = 'pre-wrap' in html
    has_prism = 'prism' in html.lower()
    has_dark_bg = '#282c34' in html

    # 8-9. 内容规范
    has_java = bool(re.search(r'\bJava\b', no_code))
    has_refs = bool(re.search(r'<h2>.*?参考.*?资料', html, re.IGNORECASE))

    # 10. 代码文件存在
    html_name = os.path.basename(html_path)
    code_files = find_code_files(html_name)
    files_exist = len(code_files) > 0 and all(os.path.exists(f) for f in code_files)

    # 11. index.html 已更新
    has_index = False
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            index_content = f.read()
        has_index = html_name in index_content

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
        ('代码文件存在', files_exist, f'{len(code_files)} 个文件'),
        ('index.html 已更新', has_index, str(has_index)),
    ]

    # SVG 视觉校验
    svg_issues = check_svg_overlaps(html)

    return checks, html_path, svg_issues

def main():
    # 确定要检查的文件
    target = None
    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        target = sys.argv[1]
    
    if target:
        html_path = os.path.join(HTML_DIR, target)
        if not os.path.exists(html_path):
            print(f"错误：找不到文件 {html_path}")
            sys.exit(1)
    else:
        latest = get_latest_html()
        if not latest:
            print("错误：html 目录下没有找到 HTML 文件")
            sys.exit(1)
        html_path = os.path.join(HTML_DIR, latest)
        print(f"自动检测到最近文件：{latest}\n")

    # 执行检查
    print(f'{"=" * 60}')
    print(f'  学习文档自检: {os.path.basename(html_path)}')
    print(f'{"=" * 60}\n')

    checks, _, svg_issues = check_html(html_path)

    all_pass = True
    for name, passed, detail in checks:
        icon = '✅' if passed else '❌'
        if not passed:
            all_pass = False
        print(f'  {icon} {name}: {detail}')

    # SVG 视觉校验结果
    svg_count = 0
    for name, _, detail in checks:
        if 'SVG' in name:
            try:
                svg_count = int(detail.replace(' 个', ''))
            except ValueError:
                pass
            break

    print(f'\n  🎨 SVG 视觉校验 ({svg_count} 个图表):')
    if svg_issues:
        all_pass = False
        print(f'   发现 {len(svg_issues)} 个问题:')
        for issue in svg_issues:
            print(f'     ⚠️  [SVG #{issue["svg"]}] {issue["type"]}: {issue["detail"]}')
    else:
        print(f'  ✅ 文字重叠检测通过')

    print(f'\n{"=" * 60}')
    total = sum(1 for _, p, _ in checks if p)
    visual_fail = len(svg_issues) > 0
    final_pass = all_pass and not visual_fail
    print(f'总计: {total}/{len(checks)} 通过' + (f' (+{len(svg_issues)} 个 SVG 问题)' if svg_issues else ''))

    if final_pass:
        print(' 全部通过！')
    else:
        failed = [name for name, p, _ in checks if not p]
        msgs = [', '.join(failed)] if failed else []
        if svg_issues:
            msgs.append(f'{len(svg_issues)} 个 SVG 布局问题')
        print(f'⚠️  有待修复: {"; ".join(msgs)}')

    print(f'{"=" * 60}\n')

    sys.exit(0 if all_pass else 1)

if __name__ == '__main__':
    main()

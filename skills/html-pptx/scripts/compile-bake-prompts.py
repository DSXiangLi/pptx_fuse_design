#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三形态 M2 · 子技能 A：页面烙入生图指令编译器（docs/design/page-render-mode.md §4）。

消费 extract-manifest.py 产出的 manifest.json，为用户逐页选定的烙入页
按七节模板（Canvas / Deck Goal / Global Style / Style Anchor / Text /
Layout / Constraints）确定性拼装生图指令，落盘到 prompts/ 工作区目录。

用法：
  python3 compile-bake-prompts.py <manifest.json> --pages cover,closing \
      --out-dir <deck目录>/prompts \
      [--goal "deck 主题与受众一句话"] [--style "全 deck 统一风格段"] \
      [--plan plan.json] [--anchor cover.png]

输入来源（确定性拼装，禁即兴）：
  - Text 段：100% 逐字来自 manifest 该页 texts[].content（防幻觉硬规则，
    harness 校验精确子串），脚本不增删改任何字符；
  - Global Style：manifest 的 theme（id/variant/tokens 具体色值）自动拼装，
    风格描述文字（G7 或缺省推导 + G9 母题 + 明暗）由 --style / plan 提供；
  - Deck Goal / Layout：--goal / plan.json 提供（页计划表的呈现方案 +
    叙事角色）。plan.json 形状：
      {"goal": "…", "style": "…", "anchor": "cover.png",
       "pages": {"<slide_id>": {"layout": "本页构图指令"}}}
    CLI 参数优先于 plan 同名字段。goal 与每个选定页的 layout 为必填。

幂等：同一输入重跑，产物字节一致（覆盖写）。退出码：成功 0，任一失败 1。
"""
import argparse
import json
import os
import sys

ROLE_LABEL = {'title': '标题', 'body': '正文', 'annotation': '标注', 'furniture': '家具'}

CANVAS = '16:9 整页幻灯片，2560×1440，无页码无水印'
ANCHOR_LINE = '附件图 = 真实 HTML 页截图（%s）：匹配其配色 / 字排 / 密度 / 质感，版式按本页内容组织'
CONSTRAINTS = [
    '中文必须清晰可读，不乱码、不缺字',
    '文字逐字渲染，不得增删改（含标点与数字）',
    '不出血、不裁切内容',
    '不渲染页码与水印',
    '整页即幻灯片本体，不留白边、不加画框',
]


def fail(msg):
    print('[compile-bake-prompts] ERROR: %s' % msg, file=sys.stderr)
    return 1


def global_style_lines(manifest, style_text):
    """Global Style 段：风格描述文字（提供时前置）+ theme tokens 逐字拼装。"""
    lines = []
    if style_text:
        lines.append(style_text)
        lines.append('')
    theme = manifest.get('theme') or {}
    if theme.get('id'):
        line = '主题：%s' % theme['id']
        if theme.get('variant'):
            line += '（配色变体：%s）' % theme['variant']
        lines.append(line)
    tokens = theme.get('tokens') or {}
    if tokens:
        lines.append('主题 token 色系（逐字来自 manifest）：')
        for k in sorted(tokens):
            lines.append('- %s: %s' % (k, tokens[k]))
    return lines


def compile_page(page, goal, style_text, layout, anchor, manifest):
    lines = []
    lines.append('# 生图指令：%s' % page.get('slide_id', ''))
    lines.append('')
    lines.append('## Canvas')
    lines.append(CANVAS)
    lines.append('')
    lines.append('## Deck Goal')
    lines.append(goal)
    lines.append('')
    lines.append('## Global Style')
    lines.extend(global_style_lines(manifest, style_text))
    lines.append('')
    lines.append('## Style Anchor')
    lines.append(ANCHOR_LINE % anchor)
    lines.append('')
    lines.append('## Text')
    lines.append('以下为本页全部文字，逐字摘自 deck manifest。文字必须逐字渲染，不得增删改：')
    for t in page.get('texts') or []:
        content = (t.get('content') or '').strip()
        if not content:
            continue
        label = ROLE_LABEL.get(t.get('role'), '正文')
        lines.append('- [%s] %s' % (label, content))
    lines.append('')
    lines.append('## Layout')
    lines.append(layout)
    lines.append('')
    lines.append('## Constraints')
    for c in CONSTRAINTS:
        lines.append('- %s' % c)
    lines.append('')
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser(description='页面烙入生图指令编译器（三形态 M2）')
    ap.add_argument('manifest', help='extract-manifest.py 产出的 manifest.json 路径')
    ap.add_argument('--pages', required=True,
                    help='逗号分隔的 slide_id 清单（用户逐页选定的烙入页）')
    ap.add_argument('--out-dir', required=True, help='指令文件输出目录（prompts/ 工作区）')
    ap.add_argument('--goal', help='deck 主题与受众一句话（覆盖 plan.goal）')
    ap.add_argument('--style', help='全 deck 统一风格段（覆盖 plan.style）')
    ap.add_argument('--plan', help='页计划 JSON（goal/style/anchor/各页 layout）')
    ap.add_argument('--anchor', help='风格锚截图文件名（覆盖 plan.anchor，缺省 cover.png）')
    args = ap.parse_args()

    try:
        with open(args.manifest, encoding='utf-8') as f:
            manifest = json.load(f)
    except Exception as e:
        return fail('manifest 读取失败：%s（%s）' % (args.manifest, e))

    plan = {}
    if args.plan:
        try:
            with open(args.plan, encoding='utf-8') as f:
                plan = json.load(f)
        except Exception as e:
            return fail('plan 读取失败：%s（%s）' % (args.plan, e))

    goal = args.goal or plan.get('goal')
    style_text = args.style or plan.get('style')
    anchor = args.anchor or plan.get('anchor') or 'cover.png'
    plan_pages = plan.get('pages') or {}

    page_ids = [p.strip() for p in args.pages.split(',') if p.strip()]
    if not page_ids:
        return fail('--pages 为空：烙入页由用户逐页选定，必须显式给出')
    if not goal:
        return fail('缺 Deck Goal：经 --goal 或 plan.goal 提供（deck 主题与受众一句话）')

    by_id = {p.get('slide_id'): p for p in manifest.get('pages') or []}
    errors = []
    compiled = []
    for pid in page_ids:
        page = by_id.get(pid)
        if not page:
            errors.append('manifest 中不存在页：%s' % pid)
            continue
        layout = (plan_pages.get(pid) or {}).get('layout')
        if not layout:
            errors.append('页 %s 缺 Layout（plan.pages.%s.layout：页计划表的呈现方案 + 叙事角色）' % (pid, pid))
            continue
        compiled.append((pid, compile_page(page, goal, style_text, layout, anchor, manifest)))
    if errors:
        for e in errors:
            print('[compile-bake-prompts] ERROR: %s' % e, file=sys.stderr)
        return 1

    os.makedirs(args.out_dir, exist_ok=True)
    for pid, text in compiled:
        path = os.path.join(args.out_dir, '%s.md' % pid)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
    print('[compile-bake-prompts] 已编译 %d 页生图指令 → %s（%s）'
          % (len(compiled), args.out_dir, '、'.join(pid for pid, _ in compiled)))
    return 0


if __name__ == '__main__':
    sys.exit(main())

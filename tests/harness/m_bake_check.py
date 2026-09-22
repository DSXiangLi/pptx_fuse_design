#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三形态 M2 验收：页面烙入模式（docs/design/page-render-mode.md §6）。

用法：python3 tests/harness/m_bake_check.py

fixture：tests/decks/bake-mix/（skeleton v7.3，4 页混合 deck——封面目录 +
两页普通 HTML 章节页 + 一页整页烙入页 ch-baked）。

检查项（全部硬断言）：
  ① 契约 v7 三要素静态校验：data-render-mode="baked" / 页面级槽位
     page-baked-16x9 三属性 / .baked-source hidden 源层；check-images 扩展
     对合规页零错误、对缺 render-mode 的负例报错；
  ② 源层保留：extract-manifest 对烙入页提取的 texts 与源层 data-editable
     逐字一致（querySelectorAll 天然含 hidden 子树）；模拟回退（摘除 img 与
     render-mode、解 hidden）后 j_render_check 通过且文本提取不变；
  ③ 指令合规：compile-bake-prompts.py 编译产物七节齐全，Text 段每行是
     manifest 该页文本的精确子串，Global Style 含 manifest token 具体色值，
     重跑幂等；
  ④ 编辑器行为：harness.html 驱动 editor.html 加载混合 deck——注册表无
     .baked-source 内元素（整页 img 仍在）、保存产物源层字节保留、重载再
     保存幂等、产物每页 hash 与 extractor 重算双端一致；
  ⑤ hash 翻转：文件级改烙入页源层文字 → 该页 hash 翻转、其余页不变；
  ⑥ 混合 deck 回归：j_render_check / k_nav_check 通过；骨架运行时跳过
     源层（.baked-source 内无 .sp-unit、无 --i 注入），普通页动效照常；
  ⑦ 失败回退演练：placeholder 残留的页面级槽位在 --mode illustration 下
     报错；诚实回退（摘除 img/render-mode、解 hidden）后渲染与校验全过。
退出码：全过 0，任一失败 1。
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXTRACTOR = os.path.join(ROOT, 'skills/html-pptx/scripts/extract-manifest.py')
COMPILER = os.path.join(ROOT, 'skills/html-pptx/scripts/compile-bake-prompts.py')
CHECK_IMAGES = os.path.join(ROOT, 'skills/html-pptx/scripts/check-images.mjs')
J_RENDER = os.path.join(ROOT, 'tests/harness/j_render_check.py')
K_NAV = os.path.join(ROOT, 'tests/harness/k_nav_check.py')
FIXTURE = os.path.join(ROOT, 'tests/decks/bake-mix')
BAKED_ID = 'ch-baked'
PORT = 8933
BASE = 'http://127.0.0.1:%d' % PORT
HASH_RE = re.compile(r'^[0-9a-f]{12}$')

FAILURES = []


def check(label, cond, detail=''):
    print('%s  %s%s' % ('PASS' if cond else 'FAIL', label,
                        (' — ' + detail) if (detail and not cond) else ''))
    if not cond:
        FAILURES.append(label)


def run_extractor(deck_html, out=None):
    cmd = [sys.executable, EXTRACTOR, deck_html]
    if out:
        cmd += ['--out', out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError('extractor 失败：%s%s' % (r.stdout, r.stderr))
    if out:
        with open(out, encoding='utf-8') as f:
            return json.load(f)
    return json.loads(r.stdout)


def hashes_of(manifest):
    return {p['slide_id']: p['content_hash'] for p in manifest['pages']}


def run_py(script, *args):
    return subprocess.run([sys.executable, script, *args], capture_output=True, text=True)


BOOLEAN_ATTRS = ['data-editable', 'data-editable-image', 'data-editable-skip',
                 'data-anim', 'data-ig-item', 'data-rotate', 'data-rotate-item', 'hidden']


def source_block(html):
    """提取 .baked-source 源层块（布尔属性 ="" 化规范化后比较，同 run_e2e 白名单口径）。"""
    i = html.find('<div class="baked-source"')
    if i < 0:
        return None
    j = html.index('</div>', i) + len('</div>')
    block = html[i:j]
    for a in BOOLEAN_ATTRS:
        block = block.replace(' %s=""' % a, ' ' + a)
    return block


def main():
    tmp = tempfile.mkdtemp(prefix='pptx-bake-check-')
    serve = os.path.join(tmp, 'serve')
    os.makedirs(serve)
    deck_dir = os.path.join(tmp, 'deck')
    shutil.copytree(FIXTURE, deck_dir)
    deck_html = os.path.join(deck_dir, 'index.html')
    os.symlink(os.path.join(ROOT, 'editor.html'), os.path.join(serve, 'editor.html'))
    shutil.copy(os.path.join(ROOT, 'tests/harness/harness.html'),
                os.path.join(serve, 'harness.html'))
    with open(deck_html, encoding='utf-8') as f:
        src = f.read()

    srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT),
                            '--bind', '127.0.0.1', '-d', serve],
                           stdout=open(os.path.join(tmp, 'srv.log'), 'w'),
                           stderr=subprocess.STDOUT)
    try:
        up = False
        for _ in range(50):
            if srv.poll() is not None:
                raise RuntimeError('静态服务启动失败（端口 %d）' % PORT)
            try:
                urllib.request.urlopen(BASE + '/harness.html', timeout=1)
                up = True
                break
            except Exception:
                time.sleep(0.2)
        if not up:
            raise RuntimeError('静态服务 10s 内未就绪')

        # ---------- ① 契约 v7 三要素静态校验 ----------
        sec_m = re.search(r'<section\b[^>]*\bdata-slide-id="%s"[^>]*>' % BAKED_ID, src)
        check('①a 烙入页 section 存在', sec_m is not None)
        sec_tag = sec_m.group(0)
        check('①b data-render-mode="baked"', 'data-render-mode="baked"' in sec_tag)
        check('①c 烙入页 data-content-hash 合法（12 位 hex）',
              bool(re.search(r'\bdata-content-hash="[0-9a-f]{12}"', sec_tag)))
        img_m = re.search(r'<img\b[^>]*\bdata-image-slot="page-baked-16x9"[^>]*>', src)
        check('①d 页面级槽位 img 存在且三属性齐备',
              img_m is not None and all(k in img_m.group(0) for k in
                  ('data-editable-image', 'data-image-intent=', 'data-image-state="generated"',
                   'src="assets/')))
        check('①e .baked-source hidden 源层存在',
              '<div class="baked-source" hidden>' in src)
        other_secs = [t for t in re.findall(r'<section\b[^>]*\bdata-slide-id="(?!%s)' % BAKED_ID + r'[^"]+"[^>]*>', src)]
        check('①f 其余页无 data-render-mode（缺省 html）', len(other_secs) == 3)
        r = subprocess.run(['node', CHECK_IMAGES, deck_html], capture_output=True, text=True)
        check('①g check-images 默认模式零错误', r.returncode == 0, r.stderr.strip()[:200])
        r = subprocess.run(['node', CHECK_IMAGES, deck_html, '--mode', 'illustration'],
                           capture_output=True, text=True)
        check('①h check-images 插画模式零错误（generated 页级槽位）', r.returncode == 0,
              r.stderr.strip()[:200])
        # 负例：摘除 render-mode → 结构校验报错
        neg_dir = os.path.join(tmp, 'neg')
        shutil.copytree(deck_dir, neg_dir)
        neg_html = os.path.join(neg_dir, 'index.html')
        with open(neg_html, 'w', encoding='utf-8') as f:
            f.write(src.replace(' data-render-mode="baked"', ''))
        r = subprocess.run(['node', CHECK_IMAGES, neg_html], capture_output=True, text=True)
        check('①i 负例：缺 render-mode 的页面级槽位报错',
              r.returncode != 0 and 'data-render-mode' in r.stderr, r.stderr.strip()[:200])

        # ---------- ② 源层保留 ----------
        m1 = run_extractor(deck_html)
        baked = next(p for p in m1['pages'] if p['slide_id'] == BAKED_ID)
        check('②a manifest 中烙入页 render_mode=baked', baked['render_mode'] == 'baked')
        src_texts = re.findall(r'data-editable[^>]*>([^<]+)<', source_block(src) or '')
        src_texts = [re.sub(r'\s+', ' ', t).strip() for t in src_texts if t.strip()]
        mf_texts = [t['content'] for t in baked['texts'] if t['content']]
        check('②b 烙入页 manifest texts 与源层逐字一致（%d 条）' % len(mf_texts),
              mf_texts == src_texts, 'manifest=%r vs 源层=%r' % (mf_texts, src_texts))
        # 模拟回退：摘除 img 与 render-mode、解 hidden → 完整回退为 HTML 页
        rev_dir = os.path.join(tmp, 'reverted')
        shutil.copytree(deck_dir, rev_dir)
        rev_html = os.path.join(rev_dir, 'index.html')
        reverted = src.replace(' data-render-mode="baked"', '')
        reverted = re.sub(r'\n\s*<img\b[^>]*\bdata-image-slot="page-baked-16x9"[^>]*>', '', reverted)
        reverted = reverted.replace('<div class="baked-source" hidden>', '<div class="baked-source">')
        with open(rev_html, 'w', encoding='utf-8') as f:
            f.write(reverted)
        r = run_py(J_RENDER, rev_html)
        check('②c 回退后 j_render_check 通过', r.returncode == 0,
              (r.stdout + r.stderr).strip()[-300:])
        m_rev = run_extractor(rev_html)
        rev_baked = next(p for p in m_rev['pages'] if p['slide_id'] == BAKED_ID)
        check('②d 回退页文本提取与烙入态一致',
              [t['content'] for t in rev_baked['texts']] == [t['content'] for t in baked['texts']])
        check('②e 回退页 render_mode 回落 html', rev_baked['render_mode'] == 'html')

        # ---------- ③ 指令合规 ----------
        manifest_path = os.path.join(tmp, 'manifest.json')
        run_extractor(deck_html, out=manifest_path)
        plan_path = os.path.join(tmp, 'plan.json')
        with open(plan_path, 'w', encoding='utf-8') as f:
            json.dump({
                'goal': '面向技术团队的混合形态演示 deck',
                'style': '深蓝夜空科技感，发光网格线，冷峻克制',
                'pages': {BAKED_ID: {'layout': '仪式页构图：标题巨字位于上三分之一留白区'}},
            }, f, ensure_ascii=False)
        prompts_dir = os.path.join(tmp, 'prompts')
        r = run_py(COMPILER, manifest_path, '--pages', BAKED_ID,
                   '--plan', plan_path, '--anchor', 'cover.png', '--out-dir', prompts_dir)
        check('③a 编译器运行成功', r.returncode == 0, r.stderr.strip()[:200])
        prompt_file = os.path.join(prompts_dir, BAKED_ID + '.md')
        prompt_text = ''
        if os.path.isfile(prompt_file):
            with open(prompt_file, encoding='utf-8') as f:
                prompt_text = f.read()
        check('③b 指令文件存在', bool(prompt_text))
        for sec in ('## Canvas', '## Deck Goal', '## Global Style', '## Style Anchor',
                    '## Text', '## Layout', '## Constraints'):
            check('③c 七节齐全：%s' % sec, sec in prompt_text)
        text_m = re.search(r'## Text\n(.*?)## Layout', prompt_text, re.S)
        text_sec = text_m.group(1) if text_m else ''
        missing = [c for c in mf_texts if c not in text_sec]
        check('③d Text 段每行是 manifest 文本的精确子串（%d 条）' % len(mf_texts),
              not missing and bool(mf_texts), '缺失=%r' % missing)
        tokens = (m1.get('theme') or {}).get('tokens') or {}
        gs_m = re.search(r'## Global Style\n(.*?)## Style Anchor', prompt_text, re.S)
        gs_sec = gs_m.group(1) if gs_m else ''
        missing_tok = ['%s: %s' % (k, v) for k, v in tokens.items()
                       if '%s: %s' % (k, v) not in gs_sec]
        check('③e Global Style 含 manifest token 具体色值', not missing_tok and bool(tokens),
              '缺失=%r' % missing_tok)
        prompts_dir2 = os.path.join(tmp, 'prompts2')
        r = run_py(COMPILER, manifest_path, '--pages', BAKED_ID,
                   '--plan', plan_path, '--anchor', 'cover.png', '--out-dir', prompts_dir2)
        with open(os.path.join(prompts_dir2, BAKED_ID + '.md'), encoding='utf-8') as f:
            prompt_text2 = f.read()
        check('③f 编译幂等（重跑字节一致）', r.returncode == 0 and prompt_text2 == prompt_text)
        r = run_py(COMPILER, manifest_path, '--pages', 'no-such-page',
                   '--plan', plan_path, '--out-dir', os.path.join(tmp, 'prompts3'))
        check('③g 负例：选定页不在 manifest 中非零退出', r.returncode != 0)

        # ---------- ④ 编辑器行为（harness.html 驱动） ----------
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            ctx = browser.new_context(viewport={'width': 1440, 'height': 900})
            page = ctx.new_page()
            page.on('pageerror', lambda e: print('[pageerror]', e))
            page.goto(BASE + '/harness.html')
            page.wait_for_function("""() => {
              const w = document.getElementById('ed').contentWindow;
              return w && w.state !== undefined && w.document.getElementById('btnSave');
            }""", timeout=8000)
            page.evaluate('([h, n]) => window.loadDeck(h, n)', [src, 'bake-mix/index.html'])
            page.wait_for_function("""() => {
              const w = document.getElementById('ed').contentWindow;
              return w && w.state && w.state.loaded === true && w.registry.length > 0 &&
                     w.frame && w.frame.contentDocument &&
                     w.frame.contentDocument.querySelectorAll('.slide').length > 0;
            }""", timeout=10000)
            page.wait_for_timeout(400)

            reg = page.evaluate("""() => {
              const w = document.getElementById('ed').contentWindow;
              return w.registry.map(r => ({
                slide: r.slideId, kind: r.kind,
                inBaked: !!r.el.closest('.baked-source'),
                slot: r.el.getAttribute && r.el.getAttribute('data-image-slot') }));
            }""")
            in_baked = [r for r in reg if r['inBaked']]
            check('④a 注册表无 .baked-source 内元素（源层文字不进编辑扫描）',
                  not in_baked, '误注册=%r' % in_baked)
            page_imgs = [r for r in reg if r.get('slot') == 'page-baked-16x9']
            check('④b 烙入页整页 img 在注册表内（换图/页级批注可用）', len(page_imgs) == 1)
            n_expected = 18   # cover 5 + ch-now 6 + ch-end 6 + 整页 img 1
            check('④c 注册表条目数=%d（源层 3 条被排除）' % n_expected,
                  len(reg) == n_expected, '实际=%d' % len(reg))

            # 保存 → 源层字节保留；重载再保存幂等
            n0 = page.evaluate('window.saveCount()')
            page.frame_locator('#ed').locator('#btnSave').click()
            page.wait_for_function('(n) => window.saveCount() > n', arg=n0, timeout=8000)
            saved = page.evaluate('window.lastSave().html')
            check('④d 保存产物源层字节保留', source_block(saved) == source_block(src))
            check('④e 保存产物保留 data-render-mode="baked" 与页面级槽位',
                  'data-render-mode="baked"' in saved and 'page-baked-16x9' in saved)
            page.evaluate('([h, n]) => window.loadDeck(h, n)', [saved, 'bake-mix/index.html'])
            page.wait_for_function("""() => {
              const w = document.getElementById('ed').contentWindow;
              return w && w.state && w.state.loaded === true && w.registry.length > 0;
            }""", timeout=10000)
            page.wait_for_timeout(400)
            n1 = page.evaluate('window.saveCount()')
            page.frame_locator('#ed').locator('#btnSave').click()
            page.wait_for_function('(n) => window.saveCount() > n', arg=n1, timeout=8000)
            saved2 = page.evaluate('window.lastSave().html')
            check('④f 重载再保存幂等', saved2 == saved)
            ctx.close()
            browser.close()

        # 双端一致：保存产物每页 hash 属性 == extractor 重算
        saved_path = os.path.join(tmp, 'saved.html')
        with open(saved_path, 'w', encoding='utf-8') as f:
            f.write(saved)
        m_saved = run_extractor(saved_path)
        re_hashes = hashes_of(m_saved)
        sv = {}
        for mm in re.finditer(r'<section\b[^>]*\bdata-slide-id="([^"]+)"[^>]*>', saved):
            hm = re.search(r'\bdata-content-hash="([^"]*)"', mm.group(0))
            sv[mm.group(1)] = hm.group(1) if hm else None
        mism = [sid for sid in sv if sv[sid] != re_hashes.get(sid)]
        check('④g 双端一致：产物每页 hash == extractor 重算（含烙入页）',
              not mism and all(v and HASH_RE.match(v) for v in sv.values()),
              '不一致页=%r' % mism)

        # ---------- ⑤ 文件级改源层文字 → hash 翻转 ----------
        base_hashes = hashes_of(m1)
        old, new = '>整页烙入示例</h1>', '>整页烙入示例改</h1>'
        assert src.count(old) == 1, 'fixture 假设失效'
        edited_path = os.path.join(tmp, 'edited.html')
        with open(edited_path, 'w', encoding='utf-8') as f:
            f.write(src.replace(old, new))
        m2 = run_extractor(edited_path)
        edited_hashes = hashes_of(m2)
        flipped = [sid for sid in base_hashes if base_hashes[sid] != edited_hashes.get(sid)]
        check('⑤ 改源层文字：恰好烙入页 hash 翻转、其余 3 页不变',
              flipped == [BAKED_ID], '翻转页=%r' % flipped)

        # ---------- ⑥ 混合 deck 回归 ----------
        r = run_py(J_RENDER, deck_html)
        check('⑥a 混合 deck 过 j_render_check', r.returncode == 0,
              (r.stdout + r.stderr).strip()[-300:])
        r = run_py(K_NAV, deck_html)
        check('⑥b 混合 deck 过 k_nav_check（章节跳转不受 v7.3 影响）', r.returncode == 0,
              (r.stdout + r.stderr).strip()[-300:])
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.on('pageerror', lambda e: print('[pageerror]', e))
            page.goto('file://' + deck_html)
            page.wait_for_timeout(600)
            n_slots = page.evaluate("document.querySelectorAll('.slide-slot').length")
            for i in range(n_slots):
                page.evaluate("(i) => document.querySelectorAll('.slide-slot')[i]"
                              ".scrollIntoView({block:'start'})", i)
                page.wait_for_timeout(200)
            page.wait_for_timeout(2600)
            rt = page.evaluate("""() => ({
              srcSpans: document.querySelectorAll('.baked-source .sp-unit').length,
              srcI: Array.from(document.querySelectorAll('.baked-source [data-anim]'))
                         .filter(e => e.style.getPropertyValue('--i') !== '').length,
              srcHidden: getComputedStyle(document.querySelector('.baked-source')).display,
              liveSpans: document.querySelectorAll('.slide:not([data-render-mode="baked"]) .sp-unit').length,
              coverText: document.querySelector('[data-slide-id="cover"] h1').textContent,
              nowText: document.querySelector('[data-slide-id="ch-now"] h2').textContent })""")
            check('⑥c 骨架运行时跳过源层：无 .sp-unit、无 --i 注入、源层保持 hidden',
                  rt['srcSpans'] == 0 and rt['srcI'] == 0 and rt['srcHidden'] == 'none',
                  repr(rt))
            check('⑥d 普通页拆字动效照常执行并还原',
                  rt['liveSpans'] == 0 and rt['coverText'] == '混合形态演示'
                  and rt['nowText'] == '现状：内容仍在 HTML 层', repr(rt))
            browser.close()

        # ---------- ⑦ 失败回退演练 ----------
        ph_dir = os.path.join(tmp, 'placeholder')
        shutil.copytree(deck_dir, ph_dir)
        ph_html = os.path.join(ph_dir, 'index.html')
        with open(ph_html, 'w', encoding='utf-8') as f:
            f.write(src.replace('data-image-state="generated"', 'data-image-state="placeholder"'))
        r = subprocess.run(['node', CHECK_IMAGES, ph_html, '--mode', 'illustration'],
                           capture_output=True, text=True)
        check('⑦a 模拟生图失败：placeholder 页级槽位在插画模式下报错',
              r.returncode != 0 and 'placeholder' in r.stderr, r.stderr.strip()[:200])
        r = subprocess.run(['node', CHECK_IMAGES, rev_html], capture_output=True, text=True)
        check('⑦b 诚实回退页（HTML 形态）默认模式校验通过', r.returncode == 0,
              r.stderr.strip()[:200])
    finally:
        srv.terminate()
        shutil.rmtree(tmp, ignore_errors=True)

    print('RESULT:', 'ALL PASS' if not FAILURES else '%d FAILURES: %s' % (len(FAILURES), FAILURES))
    return 0 if not FAILURES else 1


if __name__ == '__main__':
    sys.exit(main())

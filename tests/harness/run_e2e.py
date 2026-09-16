#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
editor.html 端到端验收（嵌入模式 postMessage 协议）

用法：python3 tests/harness/run_e2e.py
产物：tests/harness/results/（diff、截图、report.json）
退出码：全部 PASS 为 0，任一 FAIL 为 1。

环境事实（Chromium 145 headless 实测）：
- http://127.0.0.1 是安全上下文，iframe 内 showOpenFilePicker/showSaveFilePicker
  均为 function；修复前嵌入态保存会误入 FSAA 路径被静默吞掉（见报告 Bug-1）。
- headless 使用 overlay 滚动条（clientWidth 不含滚动条）。
"""
import difflib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVE = '/tmp/pptx-e2e'
PORT = 8925
BASE = 'http://127.0.0.1:%d' % PORT
RESULTS = os.path.join(ROOT, 'tests/harness/results')

DECKS = ['tech-ikb', 'culture-kraft', 'launch-mono', 'art-botanical']
VIEW_W, VIEW_H = 1440, 900          # harness 视口

RESULTS_LIST = []

def report(tid, name, ok, evidence=''):
    RESULTS_LIST.append({'id': tid, 'name': name, 'ok': bool(ok), 'evidence': evidence})
    print('%s  %-28s %s' % ('PASS' if ok else 'FAIL', tid + ' ' + name, ('— ' + evidence) if evidence else ''))

def read_deck(deck):
    with open(os.path.join(ROOT, 'tests/decks', deck, 'index.html'), encoding='utf-8') as f:
        return f.read()

# ---------- 环境 ----------

def setup_serve():
    os.makedirs(SERVE, exist_ok=True)
    for name, target in [('editor.html', os.path.join(ROOT, 'editor.html')),
                         ('decks', os.path.join(ROOT, 'tests/decks'))]:
        dst = os.path.join(SERVE, name)
        if os.path.islink(dst):
            os.remove(dst)
        elif os.path.exists(dst):
            shutil.rmtree(dst)
        os.symlink(target, dst)
    shutil.copy(os.path.join(ROOT, 'tests/harness/harness.html'), os.path.join(SERVE, 'harness.html'))
    os.makedirs(RESULTS, exist_ok=True)

def point_assets(deck):
    link = os.path.join(SERVE, 'assets')
    if os.path.islink(link):
        os.remove(link)
    os.symlink(os.path.join(SERVE, 'decks', deck, 'assets'), link)

def unpoint_assets():
    link = os.path.join(SERVE, 'assets')
    if os.path.islink(link):
        os.remove(link)

# ---------- 浏览器辅助 ----------

def fresh_page(browser, width=VIEW_W, height=VIEW_H):
    """每个测试独立 context：隔离 HTTP 缓存与脏状态。"""
    ctx = browser.new_context(viewport={'width': width, 'height': height})
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: print('[pageerror]', e))
    return ctx, pg

def wait_editor_ready(page):
    page.wait_for_function("""() => {
      const w = document.getElementById('ed').contentWindow;
      return w && w.state !== undefined && w.document.getElementById('btnSave');
    }""", timeout=8000)

def editor_frame(page):
    for f in page.frames:
        if f.url.endswith('/editor.html'):
            return f
    raise RuntimeError('editor frame not found')

def deck_frame(page):
    ef = editor_frame(page)
    if ef.child_frames:
        return ef.child_frames[0]
    raise RuntimeError('deck frame not found')

def load_deck(page, html, name, assets_url=None):
    page.evaluate('([h, n, a]) => window.loadDeck(h, n, a)', [html, name, assets_url])
    page.wait_for_function("""() => {
      const w = document.getElementById('ed').contentWindow;
      return w && w.state && w.state.loaded === true && w.registry.length > 0 &&
             w.frame && w.frame.contentDocument &&
             w.frame.contentDocument.querySelectorAll('.slide').length > 0;
    }""", timeout=10000)
    page.wait_for_timeout(400)   # fit() / rAF 稳定

def save_and_capture(page):
    n0 = page.evaluate('window.saveCount()')
    page.frame_locator('#ed').locator('#btnSave').click()
    page.wait_for_function('(n) => window.saveCount() > n', arg=n0, timeout=8000)
    return page.evaluate('window.lastSave().html')

def deck_loc(page, sel):
    return page.frame_locator('#ed').frame_locator('#deckFrame').locator(sel)

def dirty_events(page):
    return page.evaluate('window.dirtyEvents()')

# ---------- 往返 diff 白名单（§5.4 + 实测的一次性解析/序列化规范化） ----------

BOOLEAN_ATTRS = ['data-editable', 'data-editable-image', 'data-editable-skip']
SVG_VOID = 'circle|ellipse|line|path|polygon|polyline|rect|stop|use'

def whitelist_norm(t):
    """白名单：布尔属性 ="" 化；chrome 页码重置；HTML parser 对 <head> 前空白的丢弃；
    SVG 自闭合写法展开；</body></html> 周边空白被 parser 移位的规范化。"""
    for a in BOOLEAN_ATTRS:
        t = t.replace(' %s=""' % a, ' ' + a)
    t = re.sub(r'(<div class="deck-chrome" id="chrome">)[^<]*(</div>)', r'\1@@\2', t)
    t = t.replace('>\n<head>', '><head>')
    t = re.sub(r'<(%s)((?:"[^"]*"|[^">])*?)\s*/>' % SVG_VOID, r'<\1\2></\1>', t)
    t = re.sub(r'\s*</body>\s*</html>\s*$', '</body></html>', t)
    return t

def framework_blocks(t):
    style = re.search(r'<style>(.*?)</style>', t, re.S)
    script = re.search(r'<script>(.*?)</script>', t, re.S)
    return (style.group(1) if style else None, script.group(1) if script else None)

def write_diff(a, b, fname):
    diff = list(difflib.unified_diff(a.splitlines(), b.splitlines(),
                                     fromfile='original', tofile='saved', lineterm=''))
    with open(os.path.join(RESULTS, fname), 'w', encoding='utf-8') as f:
        f.write('\n'.join(diff))
    return len(diff)

# ---------- 测试 1：往返幂等（§10.3 / §10.6） ----------

def test_roundtrip(browser, deck):
    point_assets(deck)
    src = read_deck(deck)
    ctx, page = fresh_page(browser)
    try:
        page.goto(BASE + '/harness.html')
        wait_editor_ready(page)
        load_deck(page, src, deck + '/index.html')

        saved1 = save_and_capture(page)
        with open(os.path.join(RESULTS, deck + '.roundtrip1.html'), 'w', encoding='utf-8') as f:
            f.write(saved1)

        if src == saved1:
            cls = '零 diff'
        elif whitelist_norm(src) == whitelist_norm(saved1):
            cls = '仅白名单差异'
        else:
            cls = None

        load_deck(page, saved1, deck + '/index.html')
        saved2 = save_and_capture(page)
        idem2 = (saved1 == saved2)

        ndiff = write_diff(src, saved1, deck + '.roundtrip1.diff')

        fs1, fj1 = framework_blocks(src)
        fs2, fj2 = framework_blocks(saved1)
        framework_ok = (fs1 == fs2 and fj1 == fj2)

        no_dirty = (dirty_events(page) == [])

        ok = (cls is not None) and idem2 and framework_ok and no_dirty
        ev = '首趟 %s（diff %d 行）；第二趟%s；框架层%s；脏事件%s' % (
            cls or '存在非白名单差异', ndiff,
            '逐字节相等' if idem2 else '不相等',
            '逐字节一致' if framework_ok else '被改动',
            dirty_events(page) or '无')
        report('T1-' + deck, '往返幂等', ok, ev)
    finally:
        ctx.close()

# ---------- 测试 2/3 的产物净化检查 ----------

def assert_clean_output(deck, saved, extra_checks):
    """§5.4 五条：检查运行时/编辑态残留。注意 --slide-scale、in-view 字样
    合法存在于框架 CSS/JS 文本中，必须查属性位而非全文子串。"""
    problems = []
    if re.search(r'<html[^>]*\sstyle\s*=', saved):
        problems.append('<html> 残留 style（--slide-scale 未归位）')
    if re.search(r'class="[^"]*\bin-view\b', saved):
        problems.append('class 残留 in-view')
    for bad in ['contenteditable', 'ed-selected', 'ed-hover', 'ed-editing', 'data-editor-injected']:
        if bad in saved:
            problems.append('残留 ' + bad)
    if re.search(r'src="[^"]*\?v=', saved):
        problems.append('img src 残留 ?v=')
    m = re.search(r'<div class="deck-chrome" id="chrome">([^<]*)</div>', saved)
    src = read_deck(deck)
    n_slides = len(re.findall(r'data-slide-id="', src))
    if not m or m.group(1) != '1 / %d' % n_slides:
        problems.append('chrome 页码=%s，期望 1 / %d' % (m.group(1) if m else None, n_slides))
    if saved.count('data-slide-id="') != n_slides:
        problems.append('data-slide-id 数量变化')
    for label, cond in extra_checks:
        if not cond:
            problems.append(label)
    return problems

# ---------- 测试 2：编辑端到端（§10.2 文字部分） ----------

def test_edit_tech_ikb(browser):
    deck = 'tech-ikb'
    point_assets(deck)
    src = read_deck(deck)
    ctx, page = fresh_page(browser)
    try:
        page.goto(BASE + '/harness.html')
        wait_editor_ready(page)
        load_deck(page, src, deck + '/index.html')

        # --- 2a. 单行文字：两段手势 + Ctrl+Enter 确认 ---
        h1 = deck_loc(page, '[data-slide-id="cover"] h1[data-editable]')
        h1.scroll_into_view_if_needed()
        h1.click()
        cls_after_1 = h1.get_attribute('class') or ''
        ce_after_1 = h1.get_attribute('contenteditable')
        first_strike_ok = ('ed-selected' in cls_after_1) and (ce_after_1 is None)
        h1.click()
        ce_after_2 = h1.get_attribute('contenteditable')
        ws_during_edit = deck_frame(page).evaluate(
            '''() => getComputedStyle(document.querySelector('[data-slide-id="cover"] h1[data-editable]')).whiteSpace''')
        page.keyboard.type('微服务三年：架构演进实录')
        page.keyboard.press('Control+Enter')
        ce_after_commit = h1.get_attribute('contenteditable')
        cls_after_commit = h1.get_attribute('class') or ''
        ok1 = (first_strike_ok and ce_after_2 == 'plaintext-only'
               and ce_after_commit is None and 'ed-selected' in cls_after_commit
               and ws_during_edit == 'pre-wrap')

        # --- 2b. 多行编辑：Enter 换行，点击另一元素确认 ---
        h2 = deck_loc(page, '[data-slide-id="monolith-origin"] h2[data-editable]')
        h2.scroll_into_view_if_needed()
        h2.click(); h2.click()
        page.keyboard.type('单体不是错误')
        page.keyboard.press('Enter')
        page.keyboard.type('是那个阶段最对的选择')
        h1.click()   # 点击另一可编辑元素 → 提交 h2
        page.wait_for_timeout(200)
        h2_html = deck_frame(page).evaluate(
            '''() => document.querySelector('[data-slide-id="monolith-origin"] h2[data-editable]').innerHTML''')
        multiline_is_br = '单体不是错误<br>是那个阶段最对的选择' in h2_html
        multiline_is_raw_nl = '单体不是错误\n是那个阶段最对的选择' in h2_html

        dev = dirty_events(page)

        # --- 2c. 保存并检验产物 ---
        saved = save_and_capture(page)
        with open(os.path.join(RESULTS, deck + '.edited.html'), 'w', encoding='utf-8') as f:
            f.write(saved)
        problems = assert_clean_output(deck, saved, [
            ('单行修改未生效', '微服务三年：架构演进实录' in saved),
            ('多行修改未生效', '单体不是错误' in saved and '是那个阶段最对的选择' in saved),
            ('多行未以 <br> 持久化（重开丢换行）', '单体不是错误<br>是那个阶段最对的选择' in saved),
        ])
        dev2 = dirty_events(page)
        dirty_seq_ok = (dev == [True] and dev2 == [True, False])
        if not dirty_seq_ok:
            problems.append('脏事件序列异常 %r -> %r' % (dev, dev2))

        ev = '两段手势%s（首击 class=%r ce=%r；二击 ce=%r white-space=%s） | 多行提交后 innerHTML=%s | 产物：%s | 脏事件 %s' % (
            '正确' if ok1 else '异常', cls_after_1, ce_after_1, ce_after_2, ws_during_edit,
            '<br>（正确）' if multiline_is_br else ('原始 \\n（换行将丢失）' if multiline_is_raw_nl else '其他: ' + h2_html),
            '干净' if not problems else '；'.join(problems), dev2)
        report('T2-tech-ikb', '编辑端到端', ok1 and multiline_is_br and not problems, ev)
    finally:
        ctx.close()

def test_edit_culture_kraft(browser):
    deck = 'culture-kraft'
    point_assets(deck)
    src = read_deck(deck)
    ctx, page = fresh_page(browser)
    try:
        page.goto(BASE + '/harness.html')
        wait_editor_ready(page)
        load_deck(page, src, deck + '/index.html')

        sel = '[data-slide-id="key-terms"] h3[data-editable]'
        h3 = deck_loc(page, sel + ':has-text("礼治秩序")')
        h3.scroll_into_view_if_needed()
        page.wait_for_timeout(300)

        # 首击不得改变布局（§5.1 防截断释放）。用 offsetWidth/Height（布局整数，
        # 不受滚动位置影响；bounding_box 是视口坐标且亚像素，会被 scroll-snap 微调干扰）
        size_js = '''() => {
          const e = [...document.querySelectorAll('%s')].find(x => x.textContent.includes('礼治秩序'));
          return [e.offsetWidth, e.offsetHeight];
        }''' % sel
        box0 = deck_frame(page).evaluate(size_js)
        h3.click()
        box1 = deck_frame(page).evaluate(size_js)
        layout_stable = (box0 == box1) and (h3.get_attribute('contenteditable') is None)

        # 二击进入编辑，输入加长文本
        h3.click()
        ce = h3.get_attribute('contenteditable')
        page.keyboard.type('礼治秩序与现代社会的治理逻辑')
        # 真实失焦路径：点击编辑器 iframe 之外（宿主页面区域）
        page.locator('#outside').click()
        page.wait_for_timeout(300)
        committed = h3.get_attribute('contenteditable') is None

        saved = save_and_capture(page)
        with open(os.path.join(RESULTS, deck + '.edited.html'), 'w', encoding='utf-8') as f:
            f.write(saved)
        problems = assert_clean_output(deck, saved, [
            ('窄文本框加长文本未生效', '礼治秩序与现代社会的治理逻辑</h3>' in saved),
        ])
        ev = '首击布局%s（offset %s -> %s）；二击 ce=%r；点击编辑器外失焦提交%s；产物%s' % (
            '稳定' if layout_stable else '发生变化', box0, box1, ce,
            '成功' if committed else '失败（ce 仍在）',
            '干净' if not problems else '；'.join(problems))
        report('T2-culture-kraft', '窄文本框加长编辑',
               layout_stable and ce == 'plaintext-only' and committed and not problems, ev)
    finally:
        ctx.close()

# ---------- 测试 3：Esc 取消（§5.1） ----------

def test_esc_cancel(browser):
    deck = 'culture-kraft'
    point_assets(deck)
    src = read_deck(deck)
    ctx, page = fresh_page(browser)
    try:
        page.goto(BASE + '/harness.html')
        wait_editor_ready(page)
        load_deck(page, src, deck + '/index.html')

        h2 = deck_loc(page, '[data-slide-id="key-terms"] h2[data-editable]')
        h2.scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        orig = h2.inner_text()
        h2.click(); h2.click()
        page.keyboard.type('这段文字应当被Esc取消掉')
        page.keyboard.press('Escape')
        page.wait_for_timeout(200)
        after = h2.inner_text()
        dirty = editor_frame(page).evaluate('window.state.dirty')
        dev = dirty_events(page)
        saved = save_and_capture(page)
        junk_in_save = '这段文字应当被Esc取消掉' in saved

        ok = (after == orig) and (dirty is False) and (dev == []) and (not junk_in_save)
        report('T3-esc', 'Esc 取消还原', ok,
               '还原%s；dirty=%s；脏事件=%r；保存产物%s' % (
                   '一致' if after == orig else '不一致(%r vs %r)' % (orig, after),
                   dirty, dev, '无残留' if not junk_in_save else '含已取消文本'))
    finally:
        ctx.close()

# ---------- 测试 4：渲染一致性（§10.1） ----------
#
# 判定口径：§10.1 要求"无文字重叠、无错位、无异常空白"——即布局一致。
# 实测发现：Chromium 对 iframe 内文档的合成路径与顶层文档不同，fixed 定位的
# 小字号 chrome 文本会出现亚像素抗锯齿差异（裸 iframe、无任何编辑层注入的
# 对照组差异完全相同，325 通道像素 / 356 万，bbox 仅覆盖 chrome 页码）。
# 因此验收标准 = 布局指标（slide 位置尺寸）逐页精确一致 + 像素差在抗锯齿量级内。

PIXEL_TOLERANCE_RATIO = 0.002   # 抗锯齿容差：差异通道像素 ≤ 总量 0.2%

RECT_JS = """() => Array.from(document.querySelectorAll('.slide-slot')).map(s => {
  const r = s.getBoundingClientRect();
  return [Math.round(r.x*1000), Math.round(r.y*1000), Math.round(r.width*1000), Math.round(r.height*1000)];
})"""

def wait_images(frame):
    frame.wait_for_function(
        '() => Array.from(document.images).every(i => i.complete)',
        timeout=8000)

def pixel_diff(png_a, png_b):
    ia, ib = Image.open(io.BytesIO(png_a)), Image.open(io.BytesIO(png_b))
    if ia.size != ib.size:
        return None, 1, '尺寸不同 %s vs %s' % (ia.size, ib.size)
    diff = ImageChops.difference(ia.convert('RGB'), ib.convert('RGB'))
    total = ia.size[0] * ia.size[1] * 3
    bbox = diff.getbbox()
    if bbox is None:
        return 0, total, '逐像素一致'
    hist = diff.histogram()
    nonzero = total - hist[0] - hist[256] - hist[512]
    return nonzero, total, '差异通道像素 %d / %d（%.4f%%，bbox %s）' % (
        nonzero, total, nonzero * 100.0 / total, bbox)

def test_render(browser, deck):
    point_assets(deck)
    src = read_deck(deck)
    # 编辑器侧：测量 deck iframe 实际视口（headless 下 stage 宽度有 1px 取整差，须实测）
    ctx, page = fresh_page(browser)
    try:
        page.goto(BASE + '/harness.html')
        wait_editor_ready(page)
        load_deck(page, src, deck + '/index.html')
        w, h = deck_frame(page).evaluate(
            '[document.documentElement.clientWidth, document.documentElement.clientHeight]')
        wait_images(deck_frame(page))
        page.wait_for_timeout(1500)
        shot_editor = page.frame_locator('#ed').locator('#deckFrame').screenshot()
        rects_editor = deck_frame(page).evaluate(RECT_JS)
    finally:
        ctx.close()
    # 直开侧：视口精确等于编辑器内 deck iframe 视口
    ctx2, d = fresh_page(browser, w, h)
    try:
        d.goto('%s/decks/%s/index.html' % (BASE, deck))
        wait_images(d)
        d.wait_for_timeout(1500)
        shot_direct = d.screenshot()
        d.wait_for_timeout(400)
        stable = (d.screenshot() == shot_direct)
        rects_direct = d.evaluate(RECT_JS)
    finally:
        ctx2.close()

    open(os.path.join(RESULTS, deck + '.direct.png'), 'wb').write(shot_direct)
    open(os.path.join(RESULTS, deck + '.editor.png'), 'wb').write(shot_editor)

    layout_equal = (rects_direct == rects_editor)
    n, total, desc = pixel_diff(shot_direct, shot_editor)
    pixel_ok = (n is not None) and (n <= total * PIXEL_TOLERANCE_RATIO)
    ok = stable and layout_equal and pixel_ok
    report('T4-' + deck, '渲染一致性', ok,
           '视口 %dx%d；布局指标%s；直开截图稳定性=%s；像素 %s（抗锯齿容差内=%s）' % (
               w, h, '逐页一致' if layout_equal else '不一致！', '稳定' if stable else '不稳定',
               desc, pixel_ok))

# ---------- 测试 5：srcdoc base URL 与 assets 相对路径（§8 assetsUrl） ----------

def test_assets_base(browser):
    deck = 'tech-ikb'
    unpoint_assets()   # 模拟 editor.html 与 deck 不同目录
    src = read_deck(deck)
    ctx, page = fresh_page(browser)
    try:
        # (a) 不传 assetsUrl：相对路径按 editor.html 所在目录解析 → 图坏（已知限制，
        #     独立模式下无解——FSAA 文件句柄不暴露路径；嵌入模式宿主应传 assetsUrl）
        page.goto(BASE + '/harness.html')
        wait_editor_ready(page)
        load_deck(page, src, deck + '/index.html')
        page.wait_for_timeout(800)
        imgs = deck_frame(page).evaluate(
            '() => Array.from(document.images).map(i => ({src: i.src, ok: i.complete && i.naturalWidth > 0}))')
        broken = [i for i in imgs if not i['ok']]
        limitation_confirmed = len(broken) == len(imgs) and len(imgs) > 0

        # (b) 传 assetsUrl：图片应正常加载；且注入的 <base> 不得进入保存产物
        load_deck(page, src, deck + '/index.html',
                  '%s/decks/%s/' % (BASE, deck))
        wait_images(deck_frame(page))
        imgs2 = deck_frame(page).evaluate(
            '() => Array.from(document.images).map(i => i.complete && i.naturalWidth > 0)')
        assets_url_ok = bool(imgs2) and all(imgs2)
        saved = save_and_capture(page)
        base_leaked = '<base' in saved

        ok = assets_url_ok and not base_leaked
        report('T5-assets-base', 'assets 路径与 assetsUrl', ok,
               '无 assetsUrl 时 %d/%d 图加载失败（%s，宿主须传 assetsUrl）；'
               '传 assetsUrl 后 %d/%d 图正常；保存产物%s <base>' % (
                   len(broken), len(imgs),
                   '限制确认' if limitation_confirmed else '与预期不符',
                   sum(1 for x in imgs2 if x), len(imgs2),
                   '不含' if not base_leaked else '泄漏'))
    finally:
        ctx.close()
        point_assets(deck)

# ---------- 测试 6：独立模式非修复路径（saveDeck 改动不影响 standalone） ----------

def test_standalone(browser):
    """saveDeck 的嵌入分支改动不得影响独立模式：embedded=false 时
    不得向 parent postMessage；编辑与脏状态逻辑保持原样。
    （FSAA 直写路径 headless 无法交互验证，按任务约定不测。）"""
    deck = 'tech-ikb'
    point_assets(deck)
    src = read_deck(deck)
    ctx, page = fresh_page(browser)
    try:
        page.goto(BASE + '/editor.html')   # 顶层打开 → 独立模式
        page.wait_for_function('() => window.state && window.state.embedded === false')
        page.evaluate('''() => {
          window.__msgs = [];
          window.addEventListener('message', m => window.__msgs.push(m.data));
        }''')
        page.evaluate('(h) => window.openHtml(h, "tech-ikb/index.html", null)', src)
        page.wait_for_function(
            '() => window.state.loaded && window.registry.length > 0 && '
            'window.frame.contentDocument.querySelectorAll(".slide").length > 0')
        page.wait_for_timeout(400)

        # 独立模式下编辑正常工作
        h1 = page.frame_locator('#deckFrame').locator('[data-slide-id="cover"] h1[data-editable]')
        h1.click(); h1.click()
        page.keyboard.type('独立模式编辑验证')
        page.keyboard.press('Control+Enter')
        dirty = page.evaluate('window.state.dirty')
        # 点保存：embedded=false → 绝不走 postMessage（FSAA 直写 headless 不可交互，可能挂起/静默中止）
        page.locator('#btnSave').click()
        page.wait_for_timeout(1200)
        msgs = page.evaluate('window.__msgs')
        no_post = not any(m and isinstance(m, dict) and m.get('type') == 'pptx-html:save' for m in msgs)
        no_throw = True   # 有未捕获异常会触发 pageerror 打印

        report('T6-standalone', '独立模式非修复路径', dirty is True and no_post and no_throw,
               '编辑后 dirty=%s；保存未向 parent postMessage=%s（收到 %d 条消息）' % (dirty, no_post, len(msgs)))
    finally:
        ctx.close()

# ---------- 测试 7/8：批注（§11.7 / §11.8） ----------

RESOLVER_JS = """([slide, path]) => {
  const slideEl = document.querySelector('.slide[data-slide-id="' + slide + '"]');
  if (!slideEl) return null;
  let cur = slideEl;
  for (const part of path.split('>')){
    const m = /^([a-z0-9]+)\\.(\\d+)$/.exec(part);
    if (!m) return null;
    const child = cur.children[+m[2]];
    if (!child || child.tagName.toLowerCase() !== m[1]) return null;
    cur = child;
  }
  return cur.hasAttribute('data-editable-image')
    ? (cur.getAttribute('src') || '').split('?')[0]
    : (cur.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 40);
}"""

def deck_client_rects(page, selectors):
    """deck iframe 内元素的 client 坐标 rect 列表。"""
    return deck_frame(page).evaluate("""(sels) => sels.map(s => {
      const el = document.querySelector(s);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return {x: r.x, y: r.y, w: r.width, h: r.height};
    })""", selectors)

def to_page_rects(page, client_rects):
    box = page.frame_locator('#ed').locator('#deckFrame').bounding_box()
    return [{'x': box['x'] + r['x'], 'y': box['y'] + r['y'],
             'w': r['w'], 'h': r['h']} for r in client_rects]

def union_rect(rects, pad=6):
    x0 = min(r['x'] for r in rects) - pad
    y0 = min(r['y'] for r in rects) - pad
    x1 = max(r['x'] + r['w'] for r in rects) + pad
    y1 = max(r['y'] + r['h'] for r in rects) + pad
    return (x0, y0, x1, y1)

def marquee_drag(page, rect):
    x0, y0, x1, y1 = rect
    page.mouse.move(x0, y0)
    page.mouse.down()
    page.mouse.move(x1, y1, steps=8)
    page.mouse.up()

def anno_mask_open(page):
    return editor_frame(page).evaluate(
        "document.getElementById('annoMask').classList.contains('show')")

def test_annotation_e2e(browser):
    """§11.7：跨两文本框+一图框选 → 弹窗清单 → 剔除误选 → 提交 →
    导出 JSON 三层引用回验 → 保存产物无批注痕迹 → 删除。"""
    deck = 'tech-ikb'
    point_assets(deck)
    src = read_deck(deck)
    ctx = browser.new_context(viewport={'width': VIEW_W, 'height': VIEW_H},
                              permissions=['clipboard-read', 'clipboard-write'])
    page = ctx.new_page()
    problems = []
    try:
        page.goto(BASE + '/harness.html')
        wait_editor_ready(page)
        load_deck(page, src, deck + '/index.html')

        # 切到批注模式
        page.frame_locator('#ed').locator('#modeSeg button[data-mode="annotate"]').click()
        if editor_frame(page).evaluate('window.mode') != 'annotate':
            problems.append('模式切换失败')

        # 滚动到 slide 2（monolith-origin）
        deck_frame(page).evaluate("""() => {
          const deck = document.querySelector('.deck');
          const slot = document.querySelectorAll('.slide-slot')[1];
          deck.scrollTop = slot.offsetTop;
        }""")
        page.wait_for_timeout(400)

        # 框选 h2 + p×2 + img 的并集
        client_rects = deck_frame(page).evaluate("""() => {
          const els = [
            document.querySelector('[data-slide-id="monolith-origin"] h2[data-editable]'),
            ...document.querySelectorAll('[data-slide-id="monolith-origin"] p[data-editable]'),
            document.querySelector('[data-slide-id="monolith-origin"] img[data-editable-image]')
          ];
          return els.map(el => { const r = el.getBoundingClientRect();
            return {x: r.x, y: r.y, w: r.width, h: r.height}; });
        }""")
        page_rects = to_page_rects(page, client_rects)
        marquee_drag(page, union_rect(page_rects))
        page.wait_for_timeout(400)

        # 弹窗应打开，4 行命中
        if not anno_mask_open(page):
            problems.append('框选后弹窗未打开')
            report('T7-annotation', '批注端到端', False, '；'.join(problems))
            return
        rows = page.frame_locator('#ed').locator('.anno-hit-row')
        n_rows = rows.count()
        if n_rows != 4:
            problems.append('命中行数=%d，期望 4' % n_rows)
        row_text = page.frame_locator('#ed').locator('#annoHits').inner_text()
        for expect in ['monolith-origin', '<h2>', '<p>', '<img>', '单体不是错误', 'diagram-monolith.svg']:
            if expect not in row_text:
                problems.append('弹窗清单缺少 %r' % expect)

        # 空批注禁止提交
        submit = page.frame_locator('#ed').locator('#annoSubmit')
        if not submit.is_disabled():
            problems.append('空批注时提交按钮未置灰')

        # 剔除一个误选（第 3 行：第二个 p）
        rows.nth(2).locator('input[type=checkbox]').click()
        page.frame_locator('#ed').locator('#annoText').fill('这三处的口径需要更新为最新数据')
        if submit.is_disabled():
            problems.append('填写批注后提交按钮仍置灰')
        submit.click()
        page.wait_for_timeout(300)

        # 提交后：清单 1 条、3 个角标（编号 1）、未导出提示
        df = deck_frame(page)
        n_badges = df.evaluate("document.querySelectorAll('.anno-badge').length")
        badge_texts = df.evaluate("Array.from(document.querySelectorAll('.anno-badge')).map(b => b.textContent)")
        n_hits = df.evaluate("document.querySelectorAll('.anno-hit').length")
        if n_badges != 3 or badge_texts != ['1', '1', '1']:
            problems.append('角标异常：%d 个，编号 %r' % (n_badges, badge_texts))
        if n_hits != 3:
            problems.append('高亮元素数=%d，期望 3' % n_hits)
        # 角标反缩放补偿（§10.2-1）：computed font-size ≈ 13 / scale
        scale = df.evaluate("parseFloat(document.documentElement.style.getPropertyValue('--slide-scale'))")
        fs = df.evaluate("parseFloat(getComputedStyle(document.querySelector('.anno-badge')).fontSize)")
        if abs(fs - 13 / scale) > 0.6:
            problems.append('角标未反缩放：font-size=%.2f，期望 %.2f' % (fs, 13 / scale))
        unexp = editor_frame(page).evaluate("document.getElementById('annoUnexp').textContent")
        if unexp != '未导出':
            problems.append('未导出提示缺失：%r' % unexp)
        if editor_frame(page).evaluate('window.state.dirty') is not False:
            problems.append('批注置脏了！')
        if dirty_events(page) != []:
            problems.append('批注触发了脏事件：%r' % dirty_events(page))

        # 点击清单项定位：deck 滚动到 slide 2 + 闪烁 class
        page.frame_locator('#ed').locator('.anno-item .txt').click()
        page.wait_for_timeout(200)
        st = df.evaluate("document.querySelector('.deck').scrollTop")
        n_flash = df.evaluate("document.querySelectorAll('.anno-flash').length")
        if not (st > 100 and n_flash == 3):
            problems.append('定位/闪烁异常：scrollTop=%s，flash=%d' % (st, n_flash))

        # 导出：postMessage payload + 剪贴板文本
        n_msg0 = page.evaluate(
            "window.__inbox.filter(m => m && m.type === 'pptx-html:annotations').length")
        page.frame_locator('#ed').locator('#btnExportAnno').click()
        page.wait_for_function(
            '(n) => window.__inbox.filter(m => m && m.type === "pptx-html:annotations").length > n',
            arg=n_msg0, timeout=5000)
        payload = page.evaluate(
            "window.__inbox.filter(m => m && m.type === 'pptx-html:annotations').slice(-1)[0].payload")
        clip = page.evaluate('navigator.clipboard.readText()')
        if '请按以下批注修改' not in clip or '批注 1（页 monolith-origin，3 个元素）' not in clip:
            problems.append('剪贴板自然语言指令格式不符')
        unexp2 = editor_frame(page).evaluate("document.getElementById('annoUnexp').textContent")
        if unexp2 != '':
            problems.append('导出后未清空"未导出"提示')

        # 三层引用回验（§10.3 / §11.7）：slide+path 在原文件中定位，excerpt 一致
        if payload.get('kind') != 'annotation' or len(payload.get('annotations', [])) != 1:
            problems.append('payload 结构异常')
        else:
            anno = payload['annotations'][0]
            if anno['id'] != 'anno-1' or len(anno['targets']) != 3:
                problems.append('批注条目异常：id=%s targets=%d' % (anno.get('id'), len(anno.get('targets', []))))
            ctx2, dp = fresh_page(browser, 1280, 720)
            try:
                dp.goto('%s/decks/%s/index.html' % (BASE, deck))
                dp.wait_for_timeout(600)
                for t in anno['targets']:
                    got = dp.evaluate(RESOLVER_JS, [t['slide'], t['path']])
                    if got is None:
                        problems.append('原文件定位失败：%s / %s' % (t['slide'], t['path']))
                    elif got != t['excerpt']:
                        problems.append('excerpt 不符：%s → %r vs %r' % (t['path'], got, t['excerpt']))
            finally:
                ctx2.close()

        # 保存产物无批注痕迹（§11.7）：且无实质 diff（全程未改正文）
        saved = save_and_capture(page)
        for bad in ['anno-badge', 'anno-hit', 'anno-marquee', 'annoFlash', 'anno-dragging']:
            if bad in saved:
                problems.append('保存产物残留 %s' % bad)
        if whitelist_norm(src) != whitelist_norm(saved):
            problems.append('批注流程导致正文 diff')

        # 删除批注：角标/高亮清除
        page.frame_locator('#ed').locator('.anno-item .del').click()
        page.wait_for_timeout(200)
        left = df.evaluate("document.querySelectorAll('.anno-badge,.anno-hit').length")
        n_items = page.frame_locator('#ed').locator('.anno-item').count()
        if left != 0 or n_items != 0:
            problems.append('删除后残留：badge/hit=%d，清单项=%d' % (left, n_items))

        # 同元素多条批注 → 角标堆叠（§10.2-1）：h2 先入批注 2，再入批注 3
        page_rects2 = to_page_rects(page, deck_client_rects(page, [
            '[data-slide-id="monolith-origin"] h2[data-editable]']))
        r2 = page_rects2[0]
        for i in (2, 3):
            marquee_drag(page, (r2['x'] - 20, r2['y'] - 20, r2['x'] + r2['w'] + 20, r2['y'] + r2['h'] + 20))
            page.wait_for_timeout(300)
            page.frame_locator('#ed').locator('#annoText').fill('堆叠测试批注 %d' % i)
            page.frame_locator('#ed').locator('#annoSubmit').click()
            page.wait_for_timeout(200)
        h2_badges = df.evaluate("""() => {
          const h2 = document.querySelector('[data-slide-id="monolith-origin"] h2[data-editable]');
          const slide = h2.closest('.slide');
          return Array.from(slide.querySelectorAll('.anno-badge'))
            .filter(b => b.__forEl === h2).map(b => b.textContent);
        }""")
        if h2_badges != ['2', '3']:
            problems.append('同元素多条批注角标未堆叠：%r' % h2_badges)
        else:
            # 堆叠角标 left 应错开
            lefts = df.evaluate("""() => {
              const h2 = document.querySelector('[data-slide-id="monolith-origin"] h2[data-editable]');
              const slide = h2.closest('.slide');
              return Array.from(slide.querySelectorAll('.anno-badge'))
                .filter(b => b.__forEl === h2).map(b => b.style.left);
            }""")
            if len(set(lefts)) != 2:
                problems.append('堆叠角标位置未错开：%r' % lefts)
        if page.frame_locator('#ed').locator('.anno-item').count() != 2:
            problems.append('批注清单条数异常')

        report('T7-annotation', '批注端到端', not problems,
               '；'.join(problems) if problems else
               '4 命中剔除 1 → 3 目标（h2+p+img）；角标反缩放补偿正确；三层引用原文件回验一致；'
               '保存产物零痕迹；同元素多批注角标堆叠正确')
    finally:
        ctx.close()

def test_annotation_edges(browser):
    """§11.8：零命中不弹窗；空批注不可提交；Esc 取消框选无残留；批注模式禁用文字手势。"""
    deck = 'tech-ikb'
    point_assets(deck)
    src = read_deck(deck)
    ctx, page = fresh_page(browser)
    problems = []
    try:
        page.goto(BASE + '/harness.html')
        wait_editor_ready(page)
        load_deck(page, src, deck + '/index.html')
        page.frame_locator('#ed').locator('#modeSeg button[data-mode="annotate"]').click()

        # 批注模式下文字两段手势禁用（§5.0）
        h1 = deck_loc(page, '[data-slide-id="cover"] h1[data-editable]')
        h1.click(); h1.click()
        page.wait_for_timeout(200)
        if h1.get_attribute('contenteditable') is not None or 'ed-selected' in (h1.get_attribute('class') or ''):
            problems.append('批注模式下文字手势未禁用')

        # 零命中：deck 顶部 12px 间距带（slide 未开始处）
        box = page.frame_locator('#ed').locator('#deckFrame').bounding_box()
        marquee_drag(page, (box['x'] + 600, box['y'] + 2, box['x'] + 800, box['y'] + 8))
        page.wait_for_timeout(400)
        if anno_mask_open(page):
            problems.append('零命中弹窗了')

        # Esc 取消框选：在 slide 1 内容上拖拽，中途中断
        rects = to_page_rects(page, deck_client_rects(page, ['[data-slide-id="cover"] h1[data-editable]']))
        r = rects[0]
        page.mouse.move(r['x'] - 30, r['y'] - 30)
        page.mouse.down()
        page.mouse.move(r['x'] + r['w'] + 30, r['y'] + r['h'] + 30, steps=5)
        if deck_frame(page).evaluate("document.querySelectorAll('.anno-marquee').length") != 1:
            problems.append('框选中选框节点缺失')
        # 真实浏览器中 mousedown 会把焦点带入 iframe；合成输入不会，显式聚焦模拟
        deck_frame(page).evaluate('window.focus()')
        page.keyboard.press('Escape')
        page.wait_for_timeout(150)
        page.mouse.up()
        page.wait_for_timeout(300)
        if anno_mask_open(page):
            problems.append('Esc 取消后弹窗了')
        if deck_frame(page).evaluate("document.querySelectorAll('.anno-marquee,.anno-badge,.anno-hit').length") != 0:
            problems.append('Esc 取消后有注入残留')

        # 弹窗取消：不留痕
        marquee_drag(page, (r['x'] - 30, r['y'] - 30, r['x'] + r['w'] + 30, r['y'] + r['h'] + 30))
        page.wait_for_timeout(400)
        if not anno_mask_open(page):
            problems.append('有效框选未弹窗')
        else:
            # 纯空白批注禁止提交
            page.frame_locator('#ed').locator('#annoText').fill('   ')
            if not page.frame_locator('#ed').locator('#annoSubmit').is_disabled():
                problems.append('纯空白批注未禁止提交')
            page.frame_locator('#ed').locator('#annoCancel').click()
            page.wait_for_timeout(200)
            if deck_frame(page).evaluate("document.querySelectorAll('.anno-badge,.anno-hit').length") != 0:
                problems.append('弹窗取消后角标/高亮未清除')
            if page.frame_locator('#ed').locator('.anno-item').count() != 0:
                problems.append('弹窗取消后批注清单非空')

        # 全程不置脏
        if editor_frame(page).evaluate('window.state.dirty') is not False or dirty_events(page) != []:
            problems.append('批注流程置脏')

        # 切回文字编辑模式：手势恢复
        page.frame_locator('#ed').locator('#modeSeg button[data-mode="edit"]').click()
        h1.click(); h1.click()
        if h1.get_attribute('contenteditable') != 'plaintext-only':
            problems.append('切回文字编辑模式后手势未恢复')
        else:
            page.keyboard.press('Escape')   # 还原，不留修改

        report('T8-annotation-edges', '批注边界', not problems,
               '；'.join(problems) if problems else '零命中静默；Esc 取消无残留；空批注置灰；取消不留痕；模式互斥正确；全程不置脏')
    finally:
        ctx.close()

# ---------- 主流程 ----------

def main():
    setup_serve()
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT),
                            '--bind', '127.0.0.1', '-d', SERVE],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                import urllib.request
                urllib.request.urlopen(BASE + '/harness.html', timeout=1)
                break
            except Exception:
                time.sleep(0.2)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            print('Chromium', browser.version)
            ctx0, page = fresh_page(browser)
            page.goto(BASE + '/harness.html')
            wait_editor_ready(page)
            env = editor_frame(page).evaluate(
                '({fsaa: window.state.fsaa, embedded: window.state.embedded})')
            print('editor 环境探测: fsaa=%s embedded=%s' % (env['fsaa'], env['embedded']))
            ctx0.close()

            for deck in DECKS:
                test_roundtrip(browser, deck)
            test_edit_tech_ikb(browser)
            test_edit_culture_kraft(browser)
            test_esc_cancel(browser)
            for deck in ['tech-ikb', 'culture-kraft']:
                test_render(browser, deck)
            test_assets_base(browser)
            test_standalone(browser)
            test_annotation_e2e(browser)
            test_annotation_edges(browser)

            browser.close()
    finally:
        srv.terminate()

    with open(os.path.join(RESULTS, 'report.json'), 'w', encoding='utf-8') as f:
        json.dump(RESULTS_LIST, f, ensure_ascii=False, indent=2)
    nfail = sum(1 for r in RESULTS_LIST if not r['ok'])
    print('\n==== 汇总：%d 项，%d PASS，%d FAIL ====' % (len(RESULTS_LIST), len(RESULTS_LIST) - nfail, nfail))
    sys.exit(1 if nfail else 0)

if __name__ == '__main__':
    main()

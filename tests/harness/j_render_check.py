#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J 期终验渲染自检：Playwright 1920×1080 逐页检查单个 deck。

用法：python3 tests/harness/j_render_check.py tests/decks/<deck>/index.html

检查项（全部硬）：
  1. 零溢出——每个 data-editable 元素的包围盒不得越出所在 1920×1080 画布
     （画布坐标系，容差 2px；装饰件 data-editable-skip 不参与）；
  2. 零重叠——同页 data-editable 元素两两交集面积 ≤16px²（画布坐标）；
  3. 正文字号 ≥18px（画布坐标 = 计算样式 px）——例外：.masthead/.mastfoot
     框架家具（meta 槽位，typography §2 下限 14px）与 mono meta 小字（≥14px）。
退出码：全过 0，任一失败 1。
"""
import os
import sys

from playwright.sync_api import sync_playwright

MEASURE_JS = """(idx) => {
  const slot = document.querySelectorAll('.slide-slot')[idx];
  const slide = slot.querySelector('.slide');
  const scale = parseFloat(document.documentElement.style.getPropertyValue('--slide-scale')) || 1;
  const sr = slide.getBoundingClientRect();
  const toCanvas = (r) => ({
    left: (r.left - sr.left) / scale, top: (r.top - sr.top) / scale,
    right: (r.right - sr.left) / scale, bottom: (r.bottom - sr.top) / scale,
    width: r.width / scale, height: r.height / scale,
  });
  const els = Array.from(slide.querySelectorAll('[data-editable]'));
  const items = els.map((el) => {
    const cs = getComputedStyle(el);
    return {
      text: (el.textContent || '').trim().slice(0, 24),
      rect: toCanvas(el.getBoundingClientRect()),
      fontSize: parseFloat(cs.fontSize),
      fontFamily: cs.fontFamily,
      inFurniture: !!el.closest('.masthead,.mastfoot'),
      visible: cs.visibility !== 'hidden' && parseFloat(cs.opacity) > 0.02,
    };
  }).filter((it) => it.visible && it.rect.width > 0 && it.rect.height > 0);

  const overflow = [];
  for (const it of items) {
    if (it.rect.left < -2 || it.rect.top < -2 || it.rect.right > 1922 || it.rect.bottom > 1082) {
      overflow.push(it);
    }
  }
  const overlaps = [];
  for (let i = 0; i < items.length; i++) {
    for (let j = i + 1; j < items.length; j++) {
      const a = items[i].rect, b = items[j].rect;
      const w = Math.min(a.right, b.right) - Math.max(a.left, b.left);
      const h = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      if (w > 0 && h > 0 && w * h > 16) {
        overlaps.push({ a: items[i].text, b: items[j].text, area: Math.round(w * h) });
      }
    }
  }
  const small = [];
  for (const it of items) {
    if (it.fontSize >= 18) continue;
    const monoMeta = /mono/i.test(it.fontFamily) && it.fontSize >= 14;
    if (!it.inFurniture && !monoMeta) small.push(it);
  }
  return { overflow, overlaps, small, count: items.length, scale };
}"""


def main():
    target = os.path.abspath(sys.argv[1])
    url = 'file://' + target
    failures = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})
        page.goto(url)
        page.wait_for_timeout(800)
        n = page.evaluate("document.querySelectorAll('.slide-slot').length")
        print('deck: %s  pages: %d' % (target, n))
        for i in range(n):
            page.evaluate(
                "(i) => document.querySelectorAll('.slide-slot')[i].scrollIntoView({block:'start'})", i)
            page.wait_for_timeout(2600)  # 等入场/运行时动效完成并还原终态
            sid = page.evaluate(
                "(i) => document.querySelectorAll('.slide-slot')[i].querySelector('.slide').dataset.slideId", i)
            r = page.evaluate(MEASURE_JS, i)
            ok = not (r['overflow'] or r['overlaps'] or r['small'])
            print('%s  p%d %-12s editable=%d' % ('PASS' if ok else 'FAIL', i + 1, sid, r['count']))
            for it in r['overflow']:
                print('    溢出: "%s" rect=%s' % (it['text'], {k: round(v, 1) for k, v in it['rect'].items()}))
                failures += 1
            for ov in r['overlaps']:
                print('    重叠: "%s" × "%s" area=%dpx²' % (ov['a'], ov['b'], ov['area']))
                failures += 1
            for it in r['small']:
                print('    小字: "%s" %.1fpx' % (it['text'], it['fontSize']))
                failures += 1
        browser.close()
    print('RESULT:', 'ALL PASS' if failures == 0 else '%d FAILURES' % failures)
    return 0 if failures == 0 else 1


if __name__ == '__main__':
    sys.exit(main())

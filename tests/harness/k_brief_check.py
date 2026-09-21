#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
需求脑暴页快速检查（editor.html v2.5，技能 Step 0.5 / references/briefing.md）。

用法：python3 tests/harness/k_brief_check.py

流程（全部硬断言）：
  ① 打开 editor.html（独立模式，本地静态服务）→ 点「需求脑暴」→ 覆盖层打开；
  ② 选场景「现场演讲」+ 主题 B1 变体「柠檬黄」+ 封面多选（加勾 主标题/日期）；
  ③ 生成简报 → 断言预览文本含「需求简报」「现场演讲」「B1」「柠檬黄」
     「design-brief」，且未作答组标注（缺省）；
  ④ 状态隔离：脑暴页选择不得污染设计决策抽屉的 answers（theme 仍为 null）；
  ⑤ Esc 关闭覆盖层。
退出码：全过 0，任一失败 1。
"""
import os
import subprocess
import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PORT = 8931
BASE = 'http://127.0.0.1:%d' % PORT


def main():
    failures = []

    def check(label, cond, detail=''):
        print('%s  %s%s' % ('PASS' if cond else 'FAIL', label,
                            (' — ' + detail) if (detail and not cond) else ''))
        if not cond:
            failures.append(label)

    srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT),
                            '--bind', '127.0.0.1', '-d', ROOT],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                urllib.request.urlopen(BASE + '/editor.html', timeout=1)
                break
            except Exception:
                time.sleep(0.2)

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            ctx = browser.new_context(viewport={'width': 1440, 'height': 900})
            page = ctx.new_page()
            page.on('pageerror', lambda e: print('[pageerror]', e))
            page.goto(BASE + '/editor.html')
            page.wait_for_function('() => window.state !== undefined')

            # ① 打开脑暴页（覆盖层内容应在此刻才首次渲染）
            n_cards_before = page.evaluate("document.querySelectorAll('.theme-card').length")
            page.click('#btnBrief')
            page.wait_for_selector('#briefOverlay.show')
            n_cards_after = page.evaluate("document.querySelectorAll('.theme-card').length")
            check('① 覆盖层打开；主题卡懒渲染（开前 %d → 开后 %d）'
                  % (n_cards_before, n_cards_after),
                  n_cards_before == 20 and n_cards_after == 40)

            # 缺省项视觉标注
            n_def = page.evaluate("document.querySelectorAll('#briefOverlay .def-tag').length")
            check('①b 缺省项带「缺省」标注（%d 处）' % n_def, n_def >= 6)
            narr_hidden = page.evaluate(
                "document.getElementById('briefNarrative').style.display === 'none'")
            check('①c 叙事弧追问默认隐藏', narr_hidden)

            # ② 作答：场景=现场演讲；内容来源=从 0 到 1 → 叙事弧出现；
            #    主题 B1 + 变体柠檬黄；封面加勾 主标题/日期
            page.click('#briefOverlay .opt[data-id="keynote"]')
            page.click('#briefOverlay .opt[data-id="scratch"]')
            narr_shown = page.evaluate(
                "document.getElementById('briefNarrative').style.display !== 'none'")
            check('②a 选「从 0 到 1」后叙事弧条件显示', narr_shown)
            page.click('#briefOverlay .theme-card[data-id="b1"] .variants i[data-vid="b1-v1"]')
            page.click('#briefOverlay .chip[data-id="title"]')
            page.click('#briefOverlay .chip[data-id="date"]')
            ba = page.evaluate('window.briefAnswers')
            check('②b 状态落定', ba['scene'] == 'keynote' and ba['theme'] == 'b1'
                  and ba['themeVariant'] == 'b1-v1'
                  and sorted(ba['cover']) == ['date', 'title', 'toc'],
                  repr(ba))

            # ③ 生成简报
            page.click('#btnBriefGen')
            page.wait_for_selector('#briefResult:not([hidden])')
            text = page.inner_text('#briefPreview')
            for kw in ['需求简报', '现场演讲', 'B1', '柠檬黄', 'design-brief',
                       '请按以下需求简报制作 HTML 幻灯片', '章节目录',
                       'SLOT: theme tokens', 'SLOT: theme css']:
                check('③ 简报含 %r' % kw, kw in text)
            check('③b 未作答组标注（缺省）', '（缺省）' in text)
            check('③c 密度按场景推导', '低密度' in text)
            check('③d 封面多选生效', '主标题' in text and '日期' in text)

            # ④ 与设计决策抽屉状态隔离
            drawer_theme = page.evaluate('window.answers.theme')
            check('④ 抽屉 answers 未被脑暴页污染（theme=%r）' % drawer_theme,
                  drawer_theme is None)

            # ⑤ Esc 关闭
            page.keyboard.press('Escape')
            page.wait_for_timeout(200)
            closed = page.evaluate(
                "!document.getElementById('briefOverlay').classList.contains('show')")
            check('⑤ Esc 关闭覆盖层', closed)

            ctx.close()
            browser.close()
    finally:
        srv.terminate()

    print('RESULT:', 'ALL PASS' if not failures else '%d FAILURES: %s' % (len(failures), failures))
    return 0 if not failures else 1


if __name__ == '__main__':
    sys.exit(main())

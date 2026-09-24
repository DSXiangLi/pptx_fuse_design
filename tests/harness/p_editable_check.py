#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
子技能 C · C1 验收：可编辑 PPTX 导出（文本 + 简单形状，docs/design/pptx-export-editable.md §7）。

用法：python3 tests/harness/p_editable_check.py

fixture：bake-mix（4 页，含烙入页直通分支）+ smartforge-c1（8 页，文本/
形状丰富）临时副本（copytree 排除 export/ 与 prompts/，fixture 只读）。

检查项（全部硬断言）：
  ① 出口 0；postflight 重开包页数一致（bake-mix=4 / smartforge-c1=8 /
     charts-a3=10 / infographic-d1=7）；
  ② 文本逐字【硬校验】：extract-manifest 提取的全部 [data-editable] 文本，
     逐字出现在该页 slide XML 的 <a:t> 串联文本中（规范化空白后比对，
     防幻觉"逐字引用"在可编辑轨的落点；烙入页豁免——文字烧死在整页图中）；
  ③ 几何抽验：抽文本叶，slide XML 中对应 textbox 的 a:off/a:ext
     与渲染快照（report items）× 6350 EMU/px 误差 ≤2%；
  ④ wrap=square 断言：全部文本框 bodyPr wrap="square"，且框宽=渲染宽度
     （±2%）——改字按原宽重排不溢出；
  ⑤ 字号映射：run rPr sz = 渲染 px × 50（1px = 0.5pt，sz 单位 1/100pt）抽验；
  ⑥ 字体双 typeface：含 CJK 字符的 run 的 rPr 必含非空 <a:ea typeface>；
  ⑦ 烙入页 = 满幅 p:pic（off 0,0 / ext=12192000×6858000）；图片槽位 → p:pic；
  ⑧ 单向纪律：导出前后 index.html 字节一致（sha256）；
  ⑨ native_text_ratio = 1.0；uncovered 清单落盘可读；
  ⑩ C2·L3 原生图表（charts-a3）：5 个 chart part（doughnut/line/bar×3），
     workbook 数据与 DOM 逐字一致（亦庄/10.4、骑行/38、2025 Q2/348 抽验）；
     合成不一致副本（改数值文本不改几何）→ 该图降级烙图且 report 列明
     chart-verify-fail；
  ⑪ C2·L4 信息图（infographic-d1）：grpSp 分组 ≥5 且组名含 data-ig 族名；
     嵌套 chart-progress → 组内 graphicFrame；native_infographic_ratio=1.0；
  ⑫ C2·L5 烙图（motion-v5）：canvas[data-fx] 页 → 满幅 p:pic 烙图且
     report rasterized 含 canvas-fx；d1 的箭头 svg → rasterized。
退出码：全过 0，任一失败 1。
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXPORTER = os.path.join(ROOT, 'skills/html-pptx/scripts/export-pptx-editable.py')
EXTRACTOR = os.path.join(ROOT, 'skills/html-pptx/scripts/extract-manifest.py')
EMU_PER_PX = 6350
NS = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}
CJK_RE = re.compile(r'[一-鿿　-〿＀-￯]')

FAILURES = []


def check(label, cond, detail=''):
    print('%s  %s%s' % ('PASS' if cond else 'FAIL', label,
                        (' — ' + detail) if (detail and not cond) else ''))
    if not cond:
        FAILURES.append(label)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def fresh_deck(tmp, name, src_name=None):
    src = os.path.join(ROOT, 'tests/decks', src_name or name)
    dst = os.path.join(tmp, name)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns('export', 'prompts'))
    return os.path.join(dst, 'index.html')


def slide_xmls(pptx_path):
    import zipfile
    z = zipfile.ZipFile(pptx_path)
    names = sorted([n for n in z.namelist() if re.match(r'ppt/slides/slide\d+\.xml$', n)],
                   key=lambda n: int(re.search(r'(\d+)', n).group(1)))
    return [z.read(n).decode('utf-8') for n in names]


def norm(s):
    return re.sub(r'\s+', '', s or '')   # 去全部空白后比对（分行/分 run 不改变逐字性）


def sp_text(sp):
    return ''.join(t.text or '' for t in sp.findall('.//a:t', NS))


def check_deck(tmp, name, expect_pages, tag):
    deck = fresh_deck(tmp, name)
    before = sha256(deck)
    r = subprocess.run([sys.executable, EXPORTER, deck], capture_output=True, text=True)
    check('%s① 出口 0' % tag, r.returncode == 0, (r.stdout + r.stderr).strip()[-300:])
    if r.returncode != 0:
        return
    check('%s⑧ 单向纪律：字节一致' % tag, sha256(deck) == before)

    out = os.path.join(os.path.dirname(deck), 'export', 'deck-editable.pptx')
    rep_path = os.path.splitext(out)[0] + '.report.json'
    from pptx import Presentation
    prs = Presentation(out)
    check('%s①b postflight 页数=%d' % (tag, expect_pages), len(list(prs.slides)) == expect_pages)
    with open(rep_path, encoding='utf-8') as f:
        rep = json.load(f)

    xmls = slide_xmls(out)
    # ② 文本逐字（extractor 逐字文本 vs slide XML 串联文本）
    m_out = os.path.join(tmp, name + '-manifest.json')
    r2 = subprocess.run([sys.executable, EXTRACTOR, deck, '--out', m_out],
                        capture_output=True, text=True)
    check('%s②a manifest 提取成功' % tag, r2.returncode == 0, r2.stderr.strip()[:200])
    with open(m_out, encoding='utf-8') as f:
        manifest = json.load(f)
    missing = []
    for i, page in enumerate(manifest['pages']):
        if page.get('render_mode') == 'baked':
            continue   # 烙入页文字烧死在整页图中，不走原生文本（⑦ 专查满幅 pic）
        joined = norm(''.join(re.findall(r'<a:t>([^<]*)</a:t>', xmls[i])))
        joined = joined.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>') \
                       .replace('&quot;', '"').replace('&apos;', "'")
        for t in page.get('texts', []):
            c = norm(t.get('content'))
            if c and c not in joined:
                missing.append('%s:"%s…"' % (page['slide_id'], t['content'][:16]))
    check('%s②b 全部 data-editable 文本逐字出现于 slide XML（缺失 %d）' % (tag, len(missing)),
          not missing, '缺失=%s' % missing[:5])

    # ③④⑤ 几何 / wrap=square / 字号映射（对照 report items 与 slide XML 的 sp）
    geo_checked = wrap_bad = sz_checked = 0
    geo_bad = []
    for i, page_items in enumerate(rep['items']):
        root = ET.fromstring(xmls[i])
        sps = root.findall('.//p:sp', NS)
        text_sps = [sp for sp in sps if sp.find('.//a:t', NS) is not None]
        # 按发射序：report 的 text items 与 slide XML 的含文本 sp 一一对应
        text_items = [it for it in page_items['items'] if it['kind'] == 'text']
        if len(text_sps) != len(text_items):
            geo_bad.append('页%d text sp 数 %d ≠ report %d' % (i + 1, len(text_sps), len(text_items)))
            continue
        for sp, it in zip(text_sps, text_items):
            body_pr = sp.find('.//p:txBody/a:bodyPr', NS)
            if body_pr is None or body_pr.get('wrap') != 'square':
                wrap_bad += 1
            off = sp.find('.//a:xfrm/a:off', NS)
            ext = sp.find('.//a:xfrm/a:ext', NS)
            if off is None or ext is None:
                geo_bad.append('页%d sp 缺 xfrm' % (i + 1))
                continue
            exp_x = it['rect']['left'] * EMU_PER_PX
            exp_y = it['rect']['top'] * EMU_PER_PX
            exp_w = it['rect']['width'] * EMU_PER_PX
            tol_x = max(2 * EMU_PER_PX, abs(exp_w) * 0.02)   # 2% 容差（≥2px 地板）
            tol_y = max(2 * EMU_PER_PX, abs(it['rect']['height'] * EMU_PER_PX) * 0.02)
            if geo_checked < 3 and (abs(int(off.get('x')) - exp_x) > tol_x
                                    or abs(int(off.get('y')) - exp_y) > tol_y
                                    or abs(int(ext.get('cx')) - exp_w) > tol_x):
                geo_bad.append('页%d sp off/ext 偏差超 2%%：(%s,%s,%s) vs 期望(%d,%d,%d)'
                               % (i + 1, off.get('x'), off.get('y'), ext.get('cx'),
                                  int(exp_x), int(exp_y), int(exp_w)))
            geo_checked += 1
            # 框宽=渲染宽度（±2%）——全体断言
            if abs(int(ext.get('cx')) - exp_w) > tol_x:
                wrap_bad += 1
            # 字号：首个 run sz == fontSizePx × 50（±1 取整容差）
            rpr = sp.find('.//a:r/a:rPr', NS)
            if rpr is not None and it.get('fontSizePx') and sz_checked < 5:
                exp_sz = int(round(it['fontSizePx'] * 50))
                if abs(int(rpr.get('sz', '0')) - exp_sz) > 1:
                    geo_bad.append('页%d 字号 sz=%s 期望 %d（%spx）'
                                   % (i + 1, rpr.get('sz'), exp_sz, it['fontSizePx']))
                sz_checked += 1
    check('%s③ 几何抽验（off/ext vs 渲染快照 ≤2%%，比对 %d 框）' % (tag, geo_checked), not geo_bad,
          '；'.join(geo_bad[:3]))
    check('%s④ 全部文本框 wrap="square" 且框宽=渲染宽度（违例 %d）' % (tag, wrap_bad), wrap_bad == 0)
    check('%s⑤ 字号 px→pt 映射抽验（%d 组）' % (tag, sz_checked),
          sz_checked > 0 and not [g for g in geo_bad if '字号' in g])

    # ⑥ CJK run 的 ea typeface
    ea_bad = []
    for i, x in enumerate(xmls):
        root = ET.fromstring(x)
        for run in root.findall('.//a:r', NS):
            t = run.find('a:t', NS)
            if t is not None and t.text and CJK_RE.search(t.text):
                rpr = run.find('a:rPr', NS)
                ea = rpr.find('a:ea', NS) if rpr is not None else None
                if ea is None or not ea.get('typeface'):
                    ea_bad.append('页%d run "%s…" 缺 a:ea' % (i + 1, (t.text or '')[:10]))
    check('%s⑥ CJK 文本 run 均含非空 <a:ea typeface>（违例 %d）' % (tag, len(ea_bad)),
          not ea_bad, '；'.join(ea_bad[:3]))

    # ⑨ 覆盖率与报告
    check('%s⑨a native_text_ratio=1.0' % tag, rep.get('native_text_ratio') == 1.0,
          repr(rep.get('native_text_ratio')))
    check('%s⑨b uncovered 清单落盘' % tag,
          all('uncovered' in p for p in rep['pages']))
    return xmls, rep


def chart_parts(pptx_path):
    """读 pptx 内全部 chart part XML。返回 [(part_name, xml_text)]。"""
    import zipfile
    z = zipfile.ZipFile(pptx_path)
    names = sorted(n for n in z.namelist() if re.match(r'ppt/charts/chart\d+\.xml$', n))
    return [(n, z.read(n).decode('utf-8')) for n in names]


def check_charts_deck(tmp, tag):
    """C/ charts-a3：基础五原生映射 + workbook 逐字 + 合成不一致降级。"""
    res = check_deck(tmp, 'charts-a3', 10, tag)
    if not res:
        return
    out = os.path.join(tmp, 'charts-a3', 'export', 'deck-editable.pptx')
    rep_path = os.path.splitext(out)[0] + '.report.json'
    with open(rep_path, encoding='utf-8') as f:
        rep = json.load(f)
    parts = chart_parts(out)
    kinds = sorted(set(re.findall(r'<c:(doughnutChart|lineChart|barChart)>',
                                  ''.join(x for _, x in parts))))
    check('%s⑩a 原生 chart part=5 且类型覆盖 doughnut/line/bar' % tag,
          len(parts) == 5 and kinds == ['barChart', 'doughnutChart', 'lineChart'],
          'parts=%d kinds=%s' % (len(parts), kinds))
    joined = '\n'.join(x for _, x in parts)
    for label, frag in [('亦庄', '10.4'), ('骑行', '38'), ('2025 Q2', '348'),
                        ('1月', None)]:
        ok = ('<c:v>%s</c:v>' % label) in joined and (frag is None or ('<c:v>%s</c:v>' % frag) in joined)
        check('%s⑩b workbook 逐字：%s%s' % (tag, label, ('/%s' % frag) if frag else ''), ok)
    # progress 类目取自标签块（含"94 / 100 天"副行，拼接成完整类目）——子串断言
    check('%s⑩b workbook 逐字：骑行天数…/94' % tag,
          '骑行天数' in joined and '<c:v>94</c:v>' in joined)
    n_chart_pages = sum(1 for p in rep['pages'] if p['charts'])
    check('%s⑩c report 五页各有原生 chart（donut/line/hbar/column/progress）' % tag,
          n_chart_pages == 5, 'chart_pages=%d' % n_chart_pages)

    # 合成不一致：改 district-distance 的数值文本（几何不变）→ 双源校验必 fail
    bad_dir = os.path.join(tmp, 'charts-a3-bad')
    shutil.copytree(os.path.join(ROOT, 'tests/decks', 'charts-a3'), bad_dir,
                    ignore=shutil.ignore_patterns('export', 'prompts'))
    bad_html = os.path.join(bad_dir, 'index.html')
    with open(bad_html, encoding='utf-8') as f:
        src = f.read()
    assert src.count('>10.4</p>') == 1, 'fixture 假设失效'
    with open(bad_html, 'w', encoding='utf-8') as f:
        f.write(src.replace('>10.4</p>', '>99.9</p>'))
    r = subprocess.run([sys.executable, EXPORTER, bad_html], capture_output=True, text=True)
    ok = False
    if r.returncode == 0:
        with open(os.path.join(bad_dir, 'export', 'deck-editable.report.json'),
                  encoding='utf-8') as f:
            rep_bad = json.load(f)
        dist = next((p for p in rep_bad['pages'] if p['slide_id'] == 'district-distance'), None)
        ok = (dist is not None and not dist['charts']
              and any('chart-verify-fail' in x for x in dist['rasterized'])
              and sum(p['counts']['chart'] for p in rep_bad['pages']) == 4)
    check('%s⑩d 合成不一致 → 该图降级烙图且 report 列明（其余 4 图仍原生）' % tag, ok,
          (r.stdout + r.stderr).strip()[-200:])


def check_infographic_deck(tmp, tag):
    """D/ infographic-d1：grpSp 分组 + 嵌套 chart 入组 + ig 覆盖率。"""
    res = check_deck(tmp, 'infographic-d1', 7, tag)
    if not res:
        return
    out = os.path.join(tmp, 'infographic-d1', 'export', 'deck-editable.pptx')
    with open(os.path.splitext(out)[0] + '.report.json', encoding='utf-8') as f:
        rep = json.load(f)
    import zipfile
    z = zipfile.ZipFile(out)
    grp_names = []
    grp_with_chart = 0
    for n in z.namelist():
        if re.match(r'ppt/slides/slide\d+\.xml$', n):
            x = z.read(n).decode('utf-8')
            for m in re.finditer(r'<p:grpSp>.*?</p:grpSp>', x, re.S):
                block = m.group(0)
                nm = re.search(r'<p:cNvPr id="\d+" name="([^"]*)"', block)
                grp_names.append(nm.group(1) if nm else '')
                if '<p:graphicFrame>' in block:
                    grp_with_chart += 1
    families = {'list-grid', 'sequence-steps', 'compare-binary-cols',
                'hierarchy-concentric', 'relation-circle-loop'}
    hit = {f for f in families if any(f in n for n in grp_names)}
    check('%s⑪a grpSp 分组 ≥5 且组名含 data-ig 族名（命中 %d/5 族）' % (tag, len(hit)),
          len(grp_names) >= 5 and len(hit) == 5, 'grp=%r' % grp_names)
    check('%s⑪b 嵌套 chart-progress → 组内 graphicFrame' % tag, grp_with_chart >= 1)
    check('%s⑪c native_infographic_ratio=1.0' % tag,
          rep.get('native_infographic_ratio') == 1.0,
          repr(rep.get('native_infographic_ratio')))
    check('%s⑪d 箭头 svg 烙图（rasterized 含 svg-unmapped）' % tag,
          any(any('svg-unmapped' in r for r in p['rasterized']) for p in rep['pages']))


def check_fx_deck(tmp, tag):
    """E/ motion-v5（轻量）：canvas FX 页烙图。"""
    deck = fresh_deck(tmp, 'motion-v5')
    r = subprocess.run([sys.executable, EXPORTER, deck], capture_output=True, text=True)
    check('%s⑫a 出口 0' % tag, r.returncode == 0, (r.stdout + r.stderr).strip()[-200:])
    if r.returncode != 0:
        return
    out = os.path.join(tmp, 'motion-v5', 'export', 'deck-editable.pptx')
    with open(os.path.splitext(out)[0] + '.report.json', encoding='utf-8') as f:
        rep = json.load(f)
    fx_pages = [p['slide_id'] for p in rep['pages'] if any('canvas-fx' in x for x in p['rasterized'])]
    check('%s⑫b canvas-fx 页烙图且 report 列明（%s）' % (tag, '、'.join(fx_pages)),
          len(fx_pages) >= 2, repr(fx_pages))
    xmls = slide_xmls(out)
    check('%s⑫c 封面满幅烙图 p:pic（ext=12192000×6858000）' % tag,
          '<p:pic>' in xmls[0] and 'cx="12192000"' in xmls[0] and 'cy="6858000"' in xmls[0])


SUBSET_FONTS = os.path.join(ROOT, 'skills/html-pptx/scripts/subset-fonts.py')
ORCHESTRATOR = os.path.join(ROOT, 'skills/html-pptx/scripts/export-pptx.py')
# 字体 fixture 源（本机 TTF；许可闸走真实 fsType——Noto 系 OFL installable）
FONT_SRC = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'


def check_font_embed(tmp, tag):
    """F/ C3 字体内嵌：fsType 许可闸 + fntdata/embeddedFontLst/content-type。"""
    if not os.path.isfile(FONT_SRC):
        check('%s⑬ 字体 fixture 源存在（%s）' % (tag, FONT_SRC), False, '机器无该字体')
        return
    deck = fresh_deck(tmp, 'bake-mix-fonts', 'bake-mix')
    r = subprocess.run([sys.executable, SUBSET_FONTS, deck, '--format', 'ttf',
                        '--font', 'Noto Sans SC=' + FONT_SRC],
                       capture_output=True, text=True)
    check('%s⑬a subset-fonts --format ttf 出口 0' % tag, r.returncode == 0,
          (r.stdout + r.stderr).strip()[-200:])
    ttf = os.path.join(os.path.dirname(deck), 'fonts', 'noto-sans-sc.ttf')
    check('%s⑬b fonts/*.ttf 产出' % tag, os.path.isfile(ttf))

    r = subprocess.run([sys.executable, EXPORTER, deck], capture_output=True, text=True)
    check('%s⑬c 可编辑轨带 fonts/ 导出口 0' % tag, r.returncode == 0,
          (r.stdout + r.stderr).strip()[-200:])
    out = os.path.join(os.path.dirname(deck), 'export', 'deck-editable.pptx')
    import zipfile
    z = zipfile.ZipFile(out)
    names = z.namelist()
    pres = z.read('ppt/presentation.xml').decode('utf-8')
    ct = z.read('[Content_Types].xml').decode('utf-8')
    rels = z.read('ppt/_rels/presentation.xml.rels').decode('utf-8')
    check('%s⑬d fntdata part + content-type + 字体关系注册' % tag,
          any(n.startswith('ppt/fonts/font') and n.endswith('.fntdata') for n in names)
          and 'fntdata' in ct and 'relationships/font' in rels)
    check('%s⑬e presentation.xml 含 embeddedFontLst + 非空 typeface + embedTrueTypeFonts' % tag,
          '<p:embeddedFontLst>' in pres and 'embedTrueTypeFonts="1"' in pres
          and bool(re.search(r'<p:font typeface="[^"]+"', pres)))
    from pptx import Presentation
    check('%s⑬f 内嵌后 python-pptx 重开 4 页' % tag,
          len(list(Presentation(out).slides)) == 4)
    with open(os.path.splitext(out)[0] + '.report.json', encoding='utf-8') as f:
        rep = json.load(f)
    check('%s⑬g 报告 fonts_embedded 非空且 fsType 合规入档' % tag,
          bool(rep.get('fonts_embedded')), repr(rep.get('fonts_embedded')))

    # fsType 受限合成用例：同一字体副本改 fsType=0x0002（restricted）→ 必须跳过
    from fontTools.ttLib import TTFont
    fonts_dir = os.path.join(os.path.dirname(deck), 'fonts')
    os.remove(ttf)   # 只留受限副本，验证"零嵌入而非伪造 embeddedFontLst"
    font = TTFont(FONT_SRC) if not FONT_SRC.endswith('.ttc') else None
    if font is None:
        from fontTools.ttLib import TTCollection
        font = TTCollection(FONT_SRC).fonts[0]
    font['OS/2'].fsType = 0x0002
    font.save(os.path.join(fonts_dir, 'restricted-demo.ttf'))
    font.close()
    r = subprocess.run([sys.executable, EXPORTER, deck, '--out',
                        os.path.join(os.path.dirname(deck), 'export', 'deck-editable.pptx')],
                       capture_output=True, text=True)
    z2 = zipfile.ZipFile(out)
    pres2 = z2.read('ppt/presentation.xml').decode('utf-8')
    with open(os.path.splitext(out)[0] + '.report.json', encoding='utf-8') as f:
        rep2 = json.load(f)
    check('%s⑬h fsType=0x0002 受限 → 跳过且报告列明、不伪造 embeddedFontLst' % tag,
          r.returncode == 0 and '<p:embeddedFontLst>' not in pres2
          and any('restricted' in (s.get('file') or '') for s in (rep2.get('fonts_skipped') or [])),
          repr(rep2.get('fonts_skipped')))


def check_dual_track(tmp, tag):
    """G/ C3 双轨编排：三件套 + tracks schema + 轨语义证据。"""
    deck = fresh_deck(tmp, 'bake-mix-dual', 'bake-mix')
    r = subprocess.run([sys.executable, ORCHESTRATOR, deck], capture_output=True, text=True)
    check('%s⑭a 编排出口 0' % tag, r.returncode == 0, (r.stdout + r.stderr).strip()[-300:])
    if r.returncode != 0:
        return
    exp = os.path.join(os.path.dirname(deck), 'export')
    check('%s⑭b 三件套齐备（deck.pptx / deck-vector.pptx / deck.pdf）' % tag,
          all(os.path.isfile(os.path.join(exp, n))
              for n in ('deck.pptx', 'deck-vector.pptx', 'deck.pdf', 'manifest.json')))
    import zipfile
    z = zipfile.ZipFile(os.path.join(exp, 'deck.pptx'))
    s1 = z.read('ppt/slides/slide1.xml').decode('utf-8')
    check('%s⑭c deck.pptx 是可编辑轨（wrap="square" 文本框）' % tag, 'wrap="square"' in s1)
    z2 = zipfile.ZipFile(os.path.join(exp, 'deck-vector.pptx'))
    s2 = z2.read('ppt/slides/slide1.xml').decode('utf-8')
    check('%s⑭d deck-vector.pptx 是保真轨（svgBlip 双写）' % tag, 'svgBlip' in s2)
    with open(os.path.join(exp, 'deck.pdf'), 'rb') as f:
        pdf = f.read()
    check('%s⑭e deck.pdf 4 页 MediaBox' % tag, pdf.count(b'/MediaBox') == 4)
    with open(os.path.join(exp, 'manifest.json'), encoding='utf-8') as f:
        mf = json.load(f)
    tracks = mf.get('export', {}).get('tracks', {})
    check('%s⑭f tracks schema：双轨 ok + 可编辑轨指标 + 保真轨保真分' % tag,
          tracks.get('editable', {}).get('ok') is True
          and tracks['editable'].get('native_text_ratio') == 1.0
          and tracks.get('vector', {}).get('ok') is True
          and (tracks['vector'].get('fidelity_avg') or 0) > 98)
    check('%s⑭g 顶层字段向后兼容（carriers/fidelity_avg/gate 不动）' % tag,
          bool(mf['export'].get('carriers')) and mf['export'].get('fidelity_avg') is not None
          and bool(mf['export'].get('gate')))


def main():
    tmp = tempfile.mkdtemp(prefix='pptx-editable-check-')
    try:
        res = check_deck(tmp, 'bake-mix', 4, 'A/')
        if res:
            xmls, _ = res
            # ⑦ 烙入页（bake-mix 第 3 页 ch-baked）= 满幅 p:pic
            baked = xmls[2]
            check('A/⑦ 烙入页满幅 p:pic（off 0,0 / ext=12192000×6858000）',
                  '<p:pic>' in baked and 'cx="12192000"' in baked and 'cy="6858000"' in baked
                  and 'x="0"' in baked and 'y="0"' in baked)
        check_deck(tmp, 'smartforge-c1', 8, 'B/')
        check_charts_deck(tmp, 'C/')
        check_infographic_deck(tmp, 'D/')
        check_fx_deck(tmp, 'E/')
        check_font_embed(tmp, 'F/')
        check_dual_track(tmp, 'G/')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print('RESULT:', 'ALL PASS' if not FAILURES else '%d FAILURES: %s' % (len(FAILURES), FAILURES))
    return 0 if not FAILURES else 1


if __name__ == '__main__':
    sys.exit(main())

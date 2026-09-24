#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三形态子技能 C · C1 阶段：可编辑 PPTX 导出（原生元素轨，文本 + 简单形状）。

规格：docs/design/pptx-export-editable.md（§2 路线 / §3 元素映射 L1·L2·L6 / §7 验收）。
与保真轨 export-pptx.py 平行、独立可用；双轨编排与字体内嵌是 C3 的事。

用法：
  python3 scripts/export-pptx-editable.py <deck/index.html> [--out <deck>/export/deck-editable.pptx]

路线（渲染真相 × 契约标记）：Playwright 渲染 deck → freeze 动效 → 渲染后
DOM 快照（真实包围盒 / 真实逐行分行 / 真实计算样式，零估算）→ python-pptx
原生组装：

- 坐标换算【关键】：画布 1920×1080 px → 12192000×6858000 EMU，
  1 画布 px = 6350 EMU（不是 96dpi 的 9525）；字号 1px = 0.5pt；
- 页背景 → 满幅 rect 置底；z-order = DOM 序（先加的在底）；
- L1 文本叶 [data-editable] → p:sp txBox：框=渲染 rect；word_wrap=True
  （wrap=square，用户改字按原宽重排不溢出——ppt-master wrap=none 的超越点）
  + auto_size=None；真实逐行分行 → 逐行 a:p；行内 run 结构（bold/italic/
  underline/strike/字号/颜色逐段）；字体 latin+ea 双 typeface
  （pptx_font_maps.parse_font_family，python-pptx 只写 latin，ea 补丁
  rPr <a:ea typeface>）；字重 ≥600→bold；行距→lnSpc spcPts；
  letter-spacing→rPr spc；opacity×颜色 alpha→srgbClr a:alpha；
- L2 简单几何 → prstGeom（rect/roundRect）：有非透明背景 / 可见边框 /
  borderRadius>0 的块（不含 .baked-source、不含 svg 内部、不含文本叶容器
  之外的元素——含文本叶的容器仍取自身盒置底）；单侧边框 → 细条 rect；
  圆角 → roundRect + adjustment；
- L6：img[data-editable-image] → 定位 p:pic；烙入页
  （data-render-mode="baked"）整页 img 满幅直通，页内不再提取；
- 复杂视觉本期不烙图（C2/L5），在报告 uncovered 诚实列出：
  渐变背景 / 滤镜 / canvas FX / 图表 svg / 信息图 data-ig / 文字特效
  （描边/发光/叠印/流光）/ object-fit:cover 比例不符。

纪律（与保真轨同口径）：单向纪律（deck sha256 前后比对）/ postflight
重开包校验 / 临时目录构建、全过才原子落盘 / 出口报告 JSON（每页 shapes
统计 + uncovered 清单 + native_text_ratio）。

退出码：成功 0，任一失败 1。幂等语义同 extract-manifest：报告除
generated_at 外字节一致。
"""
import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))

# 复用保真轨的工具函数（浏览器 freeze 序列 / sha256 / 常量），不复制代码
_spec = importlib.util.spec_from_file_location('export_pptx', os.path.join(HERE, 'export-pptx.py'))
_epx = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_epx)
sha256_file = _epx.sha256_file
FREEZE_JS = _epx.FREEZE_JS

_spec2 = importlib.util.spec_from_file_location('pptx_font_maps', os.path.join(HERE, 'pptx_font_maps.py'))
_fonts = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(_fonts)
parse_font_family = _fonts.parse_font_family
PPT_SAFE_FONTS = _fonts.PPT_SAFE_FONTS

EMU_PER_PX = 6350            # 12192000 / 1920 = 6858000 / 1080 = 6350 精确
SLIDE_W_EMU = 12192000
SLIDE_H_EMU = 6858000
PX_TO_PT = 0.5               # 1 画布 px = 0.5pt


class ExportError(Exception):
    """管线级失败：打印信息并以退出码 1 终止。"""


def log(msg):
    print('[export-editable] %s' % msg, file=sys.stderr)


# ---------------------------------------------------------------------------
# 渲染快照（渲染后 DOM：真实几何 + 真实逐行分行 + 真实计算样式）
SNAPSHOT_JS = r"""
() => {
  const scale = parseFloat(document.documentElement.style.getPropertyValue('--slide-scale')) || 1;
  const out = {scale, pages: []};

  function inBaked(el){ return !!el.closest('.baked-source'); }
  function visible(el){
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) <= 0.02) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  }
  function norm(s){ return (s || '').replace(/\s+/g, ' ').trim(); }
  /* 画布坐标：相对 .slide 左上角，除以 --slide-scale */
  function toCanvas(slideRect, r){
    return {
      left: (r.left - slideRect.left) / scale, top: (r.top - slideRect.top) / scale,
      width: r.width / scale, height: r.height / scale,
    };
  }
  function transparent(c){
    if (!c || c === 'transparent') return true;
    const m = /^rgba\(([^)]+)\)$/.exec(c.trim());
    return !!m && parseFloat(m[1].split(',')[3]) === 0;
  }

  /* 逐行真实分行：逐字 Range rect 按 top 聚类成行，行内按 (bold/italic/
     underline/strike/字号/颜色) 相邻同款合并成 run */
  function leafLines(el){
    const tw = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    const segs = [];
    let n, order = 0;
    while ((n = tw.nextNode())){
      const txt = n.nodeValue;
      if (!txt) continue;
      const pcs = getComputedStyle(n.parentElement);
      const st = {
        bold: parseInt(pcs.fontWeight, 10) >= 600,
        italic: pcs.fontStyle === 'italic',
        underline: /underline/.test(pcs.textDecorationLine || pcs.textDecoration || ''),
        strike: /line-through/.test(pcs.textDecorationLine || pcs.textDecoration || ''),
        fontSizePx: parseFloat(pcs.fontSize),
        color: pcs.color,
      };
      for (let i = 0; i < txt.length; i++){
        const r = document.createRange();
        r.setStart(n, i); r.setEnd(n, i + 1);
        const rects = r.getClientRects();
        if (!rects.length || rects[0].height === 0) continue;
        const rc = rects[0];
        segs.push({top: rc.top, left: rc.left, height: rc.height, ch: txt[i], st, order: order++});
      }
    }
    segs.sort((a, b) => (a.top - b.top) || (a.left - b.left) || (a.order - b.order));
    const lines = [];
    for (const s of segs){
      let line = null;
      if (lines.length && Math.abs(lines[lines.length - 1].top - s.top) <= 1.5){
        line = lines[lines.length - 1];
      } else {
        line = {top: s.top, left: s.left, height: s.height, runs: []};
        lines.push(line);
      }
      line.height = Math.max(line.height, s.height);
      line.left = Math.min(line.left, s.left);
      const last = line.runs[line.runs.length - 1];
      if (last && last.st === s.st && last.order + 1 === s.order){
        last.text += s.ch; last.order = s.order;
      } else {
        line.runs.push({text: s.ch, st: s.st, order: s.order});
      }
    }
    return lines.map(l => ({
      runs: l.runs.map(r => ({text: r.text, bold: r.st.bold, italic: r.st.italic,
                              underline: r.st.underline, strike: r.st.strike,
                              fontSizePx: r.st.fontSizePx, color: r.st.color})),
    }));
  }

  /* ---------- C2：图表检测（数值文本 × 几何比例双源校验，容差 5%；
     不过校验或结构识别失败 → markRaster 烙图兜底，绝不硬映射） ---------- */
  function numOf(s){
    const m = /(-?\d+(?:\.\d+)?)/.exec((s || '').replace(/,/g, ''));
    return m ? parseFloat(m[1]) : null;
  }
  function unionRect(rs){
    let l = Infinity, t = Infinity, r = -Infinity, b = -Infinity;
    for (const q of rs){ l = Math.min(l, q.left); t = Math.min(t, q.top); r = Math.max(r, q.right); b = Math.max(b, q.bottom); }
    return {left: l, top: t, right: r, bottom: b, width: r - l, height: b - t};
  }
  function median(a){ const s = a.slice().sort((x, y) => x - y); return s[Math.floor(s.length / 2)]; }
  /* 双源不变量：文本值 / 几何长度 比值恒定（±5%）。scale = 隐含轴上限 */
  function ratioCheck(vals){
    const m = median(vals);
    if (!m) return {ok: false, maxDev: 1, scale: 0};
    const dev = Math.max.apply(null, vals.map(v => Math.abs(v - m) / Math.abs(m)));
    return {ok: dev <= 0.05, maxDev: dev, scale: m};
  }

  let rasterSeq = 0;   // 全 deck 烙图序号（python 侧按键取截图文件）
  const slides = Array.from(document.querySelectorAll('section.slide'));
  for (const slide of slides){
    const slideRect = slide.getBoundingClientRect();
    const page = {
      slide_id: slide.getAttribute('data-slide-id') || '',
      render_mode: slide.getAttribute('data-render-mode') || 'html',
      background: getComputedStyle(slide).backgroundColor,
      backgroundImage: getComputedStyle(slide).backgroundImage,
      items: [],
      charts: [],
      uncovered: [],
      igTextTotal: 0,   // data-ig 根内可见文本叶总数（native_infographic_ratio 分母）
    };
    if (page.render_mode === 'baked'){
      const img = slide.querySelector('img[data-editable-image]');
      if (img) page.items.push({kind: 'image', rect: {left: 0, top: 0, width: 1920, height: 1080},
                                src: img.getAttribute('src') || '', full_bleed: true});
      out.pages.push(page);
      continue;
    }
    if (page.backgroundImage && page.backgroundImage !== 'none')
      page.uncovered.push('page-gradient-bg(C3 整页烙图)');

    /* 信息图根（L4 分组用；嵌套 data-ig 取最外层根） */
    const igRoots = Array.from(slide.querySelectorAll('[data-ig]'));
    function igOf(el){
      let root = null, n = el;
      while (n && n !== slide){
        if (n.hasAttribute && n.hasAttribute('data-ig')) root = n;
        n = n.parentElement;
      }
      return root ? {root: igRoots.indexOf(root), family: root.getAttribute('data-ig')} : null;
    }
    function markChart(els){ els.forEach(e => e.setAttribute('data-pptx-chart', '1')); }
    function markRaster(el, reason){
      el.setAttribute('data-pptx-raster', reason);
      el.setAttribute('data-pptx-raster-idx', String(rasterSeq++));
      return rasterSeq - 1;
    }

    /* —— L5 烙图标记：canvas FX 仪式层 —— */
    Array.from(slide.querySelectorAll('canvas[data-fx]')).forEach(c => markRaster(c, 'canvas-fx'));

    /* —— 条形/进度（H-Bar / Progress）：轨道 + [data-anim=line|fill-bar] 横条，
       同容器 ≥2 行成行结构（标签 | 条 | 值）——*/
    const barGroups = new Map();
    Array.from(slide.querySelectorAll('[data-anim="line"],[data-anim="fill-bar"]')).forEach(b => {
      if (inBaked(b)) return;
      const track = b.parentElement;
      if (!track || !visible(track)) return;
      const tr = track.getBoundingClientRect(), br = b.getBoundingClientRect();
      if (!(tr.width > tr.height * 1.5 && tr.height >= 4 && br.width > 0)) return;
      const c = track.parentElement;
      if (!barGroups.has(c)) barGroups.set(c, []);
      barGroups.get(c).push({track, frac: br.width / tr.width,
                             color: getComputedStyle(b).backgroundColor, rect: tr});
    });
    for (const [container, rows] of barGroups){
      if (rows.length < 2) continue;
      let ok = true;
      const data = rows.map(({track, frac, color, rect}) => {
        const prev = track.previousElementSibling, next = track.nextElementSibling;
        const label = prev ? norm(prev.textContent) : '';
        const raw = next ? norm(next.textContent) : '';
        const val = numOf(raw);
        if (!label || val === null) ok = false;
        return {label, raw, value: val, frac, color, rect, track};
      });
      if (!ok) continue;   // 行结构不符 → 非图表，保持 L2 形状语义
      const chk = ratioCheck(data.map(d => d.value / Math.max(d.frac, 1e-6)));
      if (chk.ok){
        markChart(data.map(d => d.track));
        page.charts.push({
          kind: 'bar',
          recipe: data.every(d => /%$/.test(d.raw)) ? 'progress' : 'hbar',
          frame: toCanvas(slideRect, unionRect(data.map(d => d.rect))),
          categories: data.map(d => d.label),
          series: [{name: '', values: data.map(d => d.value), pointColors: data.map(d => d.color)}],
          axisMax: chk.scale, ig: igOf(container),
          verify: {method: 'value/条长 比值恒定', maxDev: Math.round(chk.maxDev * 1000) / 1000},
        });
      } else {
        markRaster(container, 'chart-verify-fail:bar(maxDev=' + (chk.maxDev * 100).toFixed(1) + '%)');
      }
    }
    /* 条形行的第二种包装形态：每行独立包装 div（label/条/值 横排），
       全部单行组且共祖父时按祖父容器合并重试 */
    if (![...barGroups.values()].some(g => g.length >= 2)){
      const singles = [...barGroups.values()].flat();
      if (singles.length >= 2){
        const gps = new Set(singles.map(r => r.track.parentElement.parentElement));
        if (gps.size === 1){
          const gp = [...gps][0];
          const rows2 = singles.map(({track, frac, color, rect}) => {
            const wrap = track.parentElement;
            const texts = Array.from(wrap.querySelectorAll('[data-editable]'));
            const lab = texts.find(e => numOf(norm(e.textContent)) === null);
            const valEl = texts.find(e => numOf(norm(e.textContent)) !== null);
            return {label: lab ? norm(lab.textContent) : '', raw: valEl ? norm(valEl.textContent) : '',
                    value: valEl ? numOf(norm(valEl.textContent)) : null, frac, color, rect, track};
          });
          if (rows2.every(d => d.label && d.value !== null)){
            const chk = ratioCheck(rows2.map(d => d.value / Math.max(d.frac, 1e-6)));
            if (chk.ok){
              markChart(rows2.map(d => d.track));
              page.charts.push({
                kind: 'bar', recipe: rows2.every(d => /%$/.test(d.raw)) ? 'progress' : 'hbar',
                frame: toCanvas(slideRect, unionRect(rows2.map(d => d.rect))),
                categories: rows2.map(d => d.label),
                series: [{name: '', values: rows2.map(d => d.value), pointColors: rows2.map(d => d.color)}],
                axisMax: chk.scale, ig: igOf(gp),
                verify: {method: 'value/条长 比值恒定(包装行)', maxDev: Math.round(chk.maxDev * 1000) / 1000},
              });
            } else {
              markRaster(gp, 'chart-verify-fail:bar(maxDev=' + (chk.maxDev * 100).toFixed(1) + '%)');
            }
          }
        }
      }
    }

    /* —— 柱状（Column）：calc 高度柱 + 上数值下类目 —— */
    const colGroups = new Map();
    Array.from(slide.querySelectorAll('[data-editable-skip]')).forEach(el => {
      if (inBaked(el) || el.closest('[data-pptx-chart]')) return;
      const st = el.getAttribute('style') || '';
      if (!/height\s*:\s*calc\(/.test(st)) return;
      const cs = getComputedStyle(el);
      if (transparent(cs.backgroundColor) || !visible(el)) return;
      const r = el.getBoundingClientRect();
      if (!(r.height > 8)) return;
      /* 柱通常各裹一层包装 div（值/柱/类目竖排），按祖父容器归组 */
      const c = el.parentElement.parentElement || el.parentElement;
      if (!colGroups.has(c)) colGroups.set(c, []);
      colGroups.get(c).push({el, color: cs.backgroundColor, rect: r});
    });
    for (const [container, rows] of colGroups){
      if (rows.length < 2) continue;
      let ok = true;
      const data = rows.map(({el, color, rect}) => {
        const prev = el.previousElementSibling, next = el.nextElementSibling;
        const val = prev ? numOf(norm(prev.textContent)) : null;
        const cat = next ? norm(next.textContent) : '';
        if (val === null || !cat) ok = false;
        return {cat, value: val, len: rect.height, color, el, rect};
      });
      if (!ok) continue;
      const chk = ratioCheck(data.map(d => d.value / Math.max(d.len, 1e-6)));
      if (chk.ok){
        markChart(data.map(d => d.el));
        page.charts.push({
          kind: 'column', frame: toCanvas(slideRect, unionRect(data.map(d => d.rect))),
          categories: data.map(d => d.cat),
          series: [{name: '', values: data.map(d => d.value), pointColors: data.map(d => d.color)}],
          axisMax: chk.scale, ig: igOf(container),
          verify: {method: 'value/柱高 比值恒定', maxDev: Math.round(chk.maxDev * 1000) / 1000},
        });
      } else {
        markRaster(container, 'chart-verify-fail:column(maxDev=' + (chk.maxDev * 100).toFixed(1) + '%)');
      }
    }

    /* —— 环图（Donut）与折线（Line）：svg 内几何 + 页内文本双源 —— */
    const svgs = Array.from(slide.querySelectorAll('svg')).filter(s => !inBaked(s) && visible(s));
    for (const svg of svgs){
      const circles = Array.from(svg.querySelectorAll('circle[stroke-dasharray]'));
      const arcs = circles.map(c => {
        const da = (c.getAttribute('stroke-dasharray') || '').trim().split(/[\s,]+/).map(parseFloat).filter(x => !isNaN(x));
        if (da.length < 2 || da[0] <= 0) return null;
        return {frac: da[0] / (da[0] + da[1]), color: getComputedStyle(c).stroke,
                sw: parseFloat(c.getAttribute('stroke-width')) || 0, r: parseFloat(c.getAttribute('r')) || 0};
      }).filter(a => a && a.frac > 0.005 && a.r > 0);
      if (arcs.length >= 2){
        const pcts = Array.from(slide.querySelectorAll('[data-editable]'))
          .filter(e => /^\d+(?:\.\d+)?%$/.test(norm(e.textContent)));
        const rows = pcts.map(pe => {
          const row = pe.closest('div') || slide;
          const lab = Array.from(row.querySelectorAll('[data-editable]')).find(e =>
            e !== pe && norm(e.textContent) && !/^[\d.]/.test(norm(e.textContent)) && !/%$/.test(norm(e.textContent)));
          return {label: lab ? norm(lab.textContent) : '', pct: parseFloat(norm(pe.textContent))};
        });
        const okRows = rows.length === arcs.length && rows.every(r => r.label);
        const maxDev = okRows ? Math.max.apply(null, arcs.map((a, i) =>
          Math.abs(a.frac * 100 - rows[i].pct) / Math.max(rows[i].pct, 1))) : 1;
        if (okRows && maxDev <= 0.05){
          markChart([svg]);
          const a0 = arcs[0];
          page.charts.push({
            kind: 'donut', frame: toCanvas(slideRect, svg.getBoundingClientRect()),
            categories: rows.map(r => r.label),
            series: [{name: '', values: rows.map(r => r.pct), pointColors: arcs.map(a => a.color)}],
            holeSize: a0.r > 0 ? Math.round((1 - a0.sw / a0.r) * 100) : 60,
            ig: igOf(svg), verify: {method: '弧长比例 vs 图例百分比', maxDev: Math.round(maxDev * 1000) / 1000},
          });
        } else {
          markRaster(svg, okRows
            ? 'chart-verify-fail:donut(maxDev=' + (maxDev * 100).toFixed(1) + '%)'
            : 'chart-deferred:donut(图例行匹配失败)');
        }
        continue;
      }
      const polys = Array.from(svg.querySelectorAll('polyline'))
        .filter(p => (p.getAttribute('points') || '').trim().split(/\s+/).filter(Boolean).length >= 4);
      if (polys.length >= 1){
        const svgRect = svg.getBoundingClientRect();
        const vb = (svg.getAttribute('viewBox') || '').trim().split(/[\s,]+/).map(parseFloat);
        const gridYs = Array.from(svg.querySelectorAll('line')).map(l => parseFloat(l.getAttribute('y1'))).filter(y => !isNaN(y));
        let done = false;
        if (gridYs.length >= 2 && vb.length === 4 && vb[3] > 0){
          const yPxOf = y => svgRect.top + (y - vb[1]) / vb[3] * svgRect.height;
          /* 轴标签：纵范围与 svg 相交的纯数字文本 */
          const labs = Array.from(slide.querySelectorAll('[data-editable]')).map(e => {
            const t = norm(e.textContent);
            if (!/^-?\d+(?:\.\d+)?$/.test(t)) return null;
            const r = e.getBoundingClientRect();
            const cy = r.top + r.height / 2;
            if (cy < svgRect.top - 20 || cy > svgRect.bottom + 20) return null;
            return {v: parseFloat(t), y: cy};
          }).filter(Boolean);
          const gy = gridYs.map(yPxOf).sort((a, b) => a - b);
          const lv = labs.slice().sort((a, b) => b.v - a.v);   // 值降序 ↔ y 升序
          let fit = null;
          if (lv.length >= 2 && gy.length >= 2){
            const top = lv[0], bot = lv[lv.length - 1];
            const b = (bot.v - top.v) / (gy[gy.length - 1] - gy[0]);
            const a = top.v - b * gy[0];
            const nearest = y => gy.reduce((p, c) => Math.abs(c - y) < Math.abs(p - y) ? c : p);
            const maxRes = Math.max.apply(null, lv.map(L => Math.abs(a + b * nearest(L.y) - L.v)));
            const yMis = lv.some(L => Math.abs(nearest(L.y) - L.y) > 15);
            const span = Math.max(Math.abs(top.v - bot.v), 1e-6);
            if (!yMis) fit = {a, b, maxDev: maxRes / span};
          }
          const nPts = polys[0].getAttribute('points').trim().split(/\s+/).filter(Boolean).length;
          let cats = null;
          let scope = svg.closest('div');
          while (scope && scope !== slide && !cats){
            for (const sib of Array.from(scope.parentElement.children)){
              if (sib === scope || sib.contains(svg)) continue;
              const texts = Array.from(sib.querySelectorAll('[data-editable]'))
                .map(e => norm(e.textContent)).filter(t => t && t.length <= 6);
              if (texts.length === nPts){ cats = texts; break; }
            }
            scope = scope.parentElement;
          }
          const series = polys.map(p => {
            const stroke = getComputedStyle(p).stroke || p.getAttribute('stroke');
            let name = '';
            const sw = Array.from(slide.querySelectorAll('[data-editable-skip]')).find(e =>
              getComputedStyle(e).backgroundColor === stroke && e.parentElement && e.parentElement.querySelector('[data-editable]'));
            if (sw) name = norm(sw.parentElement.querySelector('[data-editable]').textContent);
            const ys = p.getAttribute('points').trim().split(/\s+/).filter(Boolean)
              .map(pair => parseFloat(pair.split(',')[1]));
            return {name, stroke, dash: (p.getAttribute('stroke-dasharray') || '').trim(), ys};
          });
          if (fit && fit.maxDev <= 0.05 && cats && series.every(s => s.ys.length === nPts)){
            markChart([svg]);
            page.charts.push({
              kind: 'line', frame: toCanvas(slideRect, svgRect), categories: cats,
              series: series.map(s => ({
                name: s.name, color: s.stroke, dash: s.dash,
                values: s.ys.map(y => Math.round((fit.a + fit.b * yPxOf(y)) * 100) / 100),
              })),
              ig: igOf(svg), verify: {method: '轴标签 vs 网格线线性拟合', maxDev: Math.round(fit.maxDev * 1000) / 1000},
            });
            done = true;
          } else {
            markRaster(svg, 'chart-deferred:line(' + (!fit ? '轴拟合失败' : !cats ? '类目容器匹配失败' : !series.every(s => s.ys.length === nPts) ? '点数与类目不符' : 'fit 超差') + ')');
            done = true;
          }
        }
        if (!done) markRaster(svg, 'chart-deferred:line(网格线或 viewBox 缺失)');
        continue;
      }
      markRaster(svg, 'svg-unmapped(非图表 svg)');
    }

    const els = Array.from(slide.querySelectorAll('*'));
    for (const el of els){
      /* svg 的后代跳过（几何由图表映射或烙图接管）；svg 自身不跳——
         它可能是烙图项（未识别 svg）或已被 chart 标记 */
      if (inBaked(el)) continue;
      const svgAnc = el.closest('svg');
      if (svgAnc && svgAnc !== el) continue;
      /* 烙图：元素自身被标记 → 以 DOM 位次插入 raster 项；其子树的
         非文本后代跳过（data-editable 文字仍走 L1 原生叠加在烙图上） */
      if (el.hasAttribute('data-pptx-raster')){
        if (visible(el)) page.items.push({kind: 'raster', rect: toCanvas(slideRect, el.getBoundingClientRect()),
                                          reason: el.getAttribute('data-pptx-raster'),
                                          rasterIdx: parseInt(el.getAttribute('data-pptx-raster-idx'), 10),
                                          ig: igOf(el)});
        continue;
      }
      if (el.closest('[data-pptx-raster]') && !el.hasAttribute('data-editable')) continue;
      if (el.closest('[data-pptx-chart]') && !el.hasAttribute('data-editable')) continue;
      const tag = el.tagName.toLowerCase();
      if (tag === 'script' || tag === 'style' || tag === 'canvas') continue;

      if (tag === 'img' && el.hasAttribute('data-editable-image')){
        if (!visible(el)) continue;
        const r = toCanvas(slideRect, el.getBoundingClientRect());
        const src = el.getAttribute('src') || '';
        /* SVG 图片 python-pptx 无法直接嵌入（PIL 不识别）→ 走 L5 烙图 */
        if (/\.svg($|\?)/i.test(src)){
          const ridx = markRaster(el, 'image-svg');
          page.items.push({kind: 'raster', rect: r, reason: 'image-svg', rasterIdx: ridx, ig: igOf(el)});
          continue;
        }
        const it = {kind: 'image', rect: r, src,
                    objectFit: getComputedStyle(el).objectFit, ig: igOf(el)};
        // 构图宽高比与图片固有比例不一致时 cover 语义 pptx 无法直接表达（C1 记 uncovered）
        if (it.objectFit === 'cover' && el.naturalWidth && el.naturalHeight){
          const boxAr = r.width / r.height, imgAr = el.naturalWidth / el.naturalHeight;
          if (Math.abs(boxAr - imgAr) / imgAr > 0.05) it.uncovered = 'object-fit-cover-crop';
        }
        page.items.push(it);
        continue;
      }

      if (el.hasAttribute('data-editable')){
        if (!visible(el) || !norm(el.textContent)) continue;
        const cs = getComputedStyle(el);
        const igInfo = igOf(el);
        if (igInfo) page.igTextTotal += 1;
        const r = toCanvas(slideRect, el.getBoundingClientRect());
        const fx = [];
        if (parseFloat(cs.webkitTextStrokeWidth || '0') > 0) fx.push('text-stroke(tt-outline)');
        if (cs.textShadow && cs.textShadow !== 'none') fx.push('text-shadow(tt-glow/tt-shadow)');
        if ((cs.webkitBackgroundClip || cs.backgroundClip) === 'text') fx.push('gradient-flow-text');
        if (fx.length) page.uncovered.push('text-effect:' + fx.join('+') + '(视觉层 C2，文字本体原生可编辑)');
        page.items.push({
          kind: 'text',
          rect: r,
          style: {
            fontFamily: cs.fontFamily,
            fontSizePx: parseFloat(cs.fontSize),
            fontWeight: parseInt(cs.fontWeight, 10),
            fontStyle: cs.fontStyle,
            color: cs.color,
            textAlign: cs.textAlign,
            lineHeightPx: parseFloat(cs.lineHeight) || parseFloat(cs.fontSize) * 1.2,
            letterSpacingPx: cs.letterSpacing === 'normal' ? 0 : parseFloat(cs.letterSpacing) || 0,
            opacity: parseFloat(cs.opacity),
          },
          lines: leafLines(el),
          ig: igInfo,
        });
        continue;
      }

      /* L2 简单几何候选：非透明背景 / 可见边框 / 圆角（装饰与容器底） */
      if (!visible(el)) continue;
      const cs = getComputedStyle(el);
      /* L5 烙图兜底：渐变底 / 滤镜 / 混合模式——原生模型无等价物，
         子树截图嵌入，文字仍走 L1 原生叠加 */
      if ((cs.backgroundImage && cs.backgroundImage !== 'none' && !transparent(cs.backgroundColor))
          || cs.filter !== 'none' || cs.backdropFilter !== 'none' || cs.mixBlendMode !== 'normal'){
        const reason = cs.filter !== 'none' || cs.backdropFilter !== 'none' || cs.mixBlendMode !== 'normal'
          ? 'filter-blend' : 'gradient-bg';
        const ridx = markRaster(el, reason);
        page.items.push({kind: 'raster', rect: toCanvas(slideRect, el.getBoundingClientRect()),
                         reason, rasterIdx: ridx, ig: igOf(el)});
        continue;
      }
      const bg = transparent(cs.backgroundColor) ? null : cs.backgroundColor;
      const sides = [];
      for (const side of ['Top', 'Right', 'Bottom', 'Left']){
        const st = cs['border' + side + 'Style'];
        const w = parseFloat(cs['border' + side + 'Width']);
        const c = cs['border' + side + 'Color'];
        if (st && st !== 'none' && st !== 'hidden' && w > 0 && !transparent(c))
          sides.push({side: side.toLowerCase(), width: w, color: c});
      }
      const radius = parseFloat(cs.borderTopLeftRadius) || 0;
      if (!bg && !sides.length && radius <= 0) continue;
      // 含文本叶的容器仍取自身盒（置底），但跳过无背景无边框的纯结构容器
      page.items.push({kind: 'shape', rect: toCanvas(slideRect, el.getBoundingClientRect()),
                       bg, borders: sides, radius,
                       opacity: parseFloat(cs.opacity), ig: igOf(el)});
    }
    // 形状盒裁剪到画布内（出血装饰记 uncovered 并裁剪）
    for (const it of page.items){
      const r = it.rect;
      if (r.left < -2 || r.top < -2 || r.left + r.width > 1922 || r.top + r.height > 1082){
        const nl = Math.max(0, r.left), nt = Math.max(0, r.top);
        const nr = Math.min(1920, r.left + r.width), nb = Math.min(1080, r.top + r.height);
        it.rect = {left: nl, top: nt, width: Math.max(0, nr - nl), height: Math.max(0, nb - nt)};
        if (it.kind !== 'text') page.uncovered.push('bleed-clipped:' + it.kind + '(出血裁剪)');
      }
    }
    page.items = page.items.filter(it => it.rect.width > 0 && it.rect.height > 0);
    out.pages.push(page);
  }
  return out;
}
"""


def snapshot(deck_html, work):
    """渲染 deck（freeze 后）并提取快照 + L5 烙图截图。
    返回 (snapshot, deck_lang, raster_paths)。"""
    url = 'file://' + os.path.abspath(deck_html)
    raster_paths = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})
        page.goto(url)
        page.wait_for_timeout(1000)
        page.evaluate(FREEZE_JS)
        # 入场终态强制：freeze 回滚后离屏页 .in-view 摘除会把 reveal/data-anim
        # 过渡回 opacity:0（快照要的是渲染终态，与骨架打印 CSS 同口径）
        page.add_style_tag(content=(
            ".js .reveal,.js [data-anim]{opacity:1 !important;transform:none !important;"
            "transition:none !important;filter:none !important;clip-path:none !important}"
            ".js .split-anim .sp-unit{opacity:1 !important;transform:none !important;"
            "transition:none !important}"))
        page.wait_for_timeout(400)
        lang = page.evaluate("document.documentElement.lang || 'zh-CN'")
        snap = page.evaluate(SNAPSHOT_JS)
        # L5 烙图：子树截图。子树内的 data-editable 文字截图前隐藏
        # （文字仍走 L1 原生文本框叠加，避免图内图外双重渲染）
        for el in page.query_selector_all('[data-pptx-raster-idx]'):
            idx = int(el.get_attribute('data-pptx-raster-idx'))
            page.evaluate("(e) => e.querySelectorAll('[data-editable]').forEach("
                          "t => t.style.visibility = 'hidden')", el)
            p = os.path.join(work, 'raster-%d.png' % idx)
            el.screenshot(path=p)
            page.evaluate("(e) => e.querySelectorAll('[data-editable]').forEach("
                          "t => t.style.visibility = '')", el)
            raster_paths[idx] = p
        browser.close()
    return snap, lang, raster_paths


# ---------------------------------------------------------------------------
# 颜色解析（rgb()/rgba() 与 color(srgb …) 两形态，与 j_render_check 同口径）
def parse_color(c):
    """返回 (r, g, b, a) 0-255/0-1，无法解析返回 None。"""
    if not c:
        return None
    c = c.strip()
    m = re.match(r'^rgba?\(([^)]+)\)$', c)
    if m:
        parts = [p.strip() for p in m.group(1).split(',')]
        if len(parts) >= 3:
            r, g, b = (max(0, min(255, float(p))) for p in parts[:3])
            a = float(parts[3]) if len(parts) > 3 else 1.0
            return int(round(r)), int(round(g)), int(round(b)), max(0.0, min(1.0, a))
        return None
    m = re.match(r'^color\(srgb\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)(?:\s*/\s*([\d.]+%?))?\)$', c)
    if m:
        a = 1.0
        if m.group(4) is not None:
            a = float(m.group(4).rstrip('%')) / (100.0 if m.group(4).endswith('%') else 1.0)
        return (int(round(float(m.group(1)) * 255)),
                int(round(float(m.group(2)) * 255)),
                int(round(float(m.group(3)) * 255)),
                max(0.0, min(1.0, a)))
    return None


def _patch_alpha(srgb_clr_el, alpha):
    """srgbClr 元素追加 <a:alpha>（alpha∈[0,1)，val 千分比）。"""
    if alpha >= 0.999:
        return
    from pptx.oxml.ns import qn
    from lxml import etree
    el = etree.SubElement(srgb_clr_el, qn('a:alpha'))
    el.set('val', str(int(round(alpha * 100000))))


def _solid_fill_rgb(fill_owner, rgb, alpha):
    """python-pptx 写完 rgb 后补 alpha 通道。"""
    fill_owner.solid()
    fill_owner.fore_color.rgb = rgb
    from pptx.oxml.ns import qn
    sp_pr = fill_owner._xPr  # FillFormat 的内部 xml（spPr 或 rPr 等）
    srgb = sp_pr.find('.//' + qn('a:srgbClr'))
    if srgb is not None:
        _patch_alpha(srgb, alpha)


# ---------------------------------------------------------------------------
# 组装（python-pptx 原生元素）
def add_native_chart(shapes, ch, RGBColor, Pt):
    """L3 原生 chart：数据/系列名/类目全部来自 DOM 快照（双源校验已过），
    轴与图例删除（标签由 L1 文本框承担，避免双重渲染）；bar 图首类目在顶。"""
    from pptx.chart.data import CategoryChartData
    from pptx.enum.chart import XL_CHART_TYPE
    from pptx.oxml.ns import qn
    from lxml import etree

    r = ch['frame']
    cd = CategoryChartData()
    cd.categories = ch['categories']
    for s in ch['series']:
        cd.add_series(s.get('name') or '', tuple(s['values']))
    ctype = {'bar': XL_CHART_TYPE.BAR_CLUSTERED,
             'column': XL_CHART_TYPE.COLUMN_CLUSTERED,
             'line': XL_CHART_TYPE.LINE_MARKERS,
             'donut': XL_CHART_TYPE.DOUGHNUT}[ch['kind']]
    gf = shapes.add_chart(ctype,
                          int(round(r['left'] * EMU_PER_PX)),
                          int(round(r['top'] * EMU_PER_PX)),
                          int(round(r['width'] * EMU_PER_PX)),
                          int(round(r['height'] * EMU_PER_PX)), cd)
    gf.name = 'chart·' + ch['kind'] + ('·' + ch.get('recipe', '') if ch.get('recipe') else '')
    chart = gf.chart
    chart.has_legend = False
    try:
        chart.category_axis.visible = False    # 标签已由 L1 文本承担
        chart.value_axis.visible = False
        if ch.get('axisMax'):
            chart.value_axis.maximum_scale = float(ch['axisMax'])
    except (AttributeError, ValueError):
        pass                                   # donut 无直角坐标轴
    plot = chart.plots[0]
    if ch['kind'] in ('bar', 'column'):
        try:
            plot.gap_width = 40
        except (AttributeError, ValueError):
            pass
    if ch['kind'] == 'bar':                    # pptx 条形图首类目默认在底，翻转到顶
        orient = chart.category_axis._element.find(qn('c:scaling') + '/' + qn('c:orientation'))
        if orient is not None:
            orient.set('val', 'maxMin')
    for si, ser in enumerate(chart.series):
        sd = ch['series'][si]
        if ch['kind'] == 'line':
            col = parse_color(sd.get('color'))
            if col:
                ser.format.line.color.rgb = RGBColor(*col[:3])
                ser.format.line.width = Pt(1.25)
            try:
                ser.smooth = False
            except (AttributeError, ValueError):
                pass
            if sd.get('dash'):
                try:
                    from pptx.enum.dml import MSO_LINE_DASH_STYLE
                    ser.format.line.dash_style = MSO_LINE_DASH_STYLE.DASH
                except (AttributeError, ValueError):
                    pass
        else:
            pcs = sd.get('pointColors') or []
            for pi, pt in enumerate(ser.points):
                col = parse_color(pcs[pi] if pi < len(pcs) else sd.get('color'))
                if col:
                    pt.format.fill.solid()
                    pt.format.fill.fore_color.rgb = RGBColor(*col[:3])
    if ch['kind'] == 'donut':
        # python-pptx 默认已带 firstSliceAng=0/holeSize=50——改写而非追加
        dch = chart._chartSpace.find('.//' + qn('c:doughnutChart'))
        if dch is not None:
            el = dch.find(qn('c:firstSliceAng'))
            if el is None:
                el = etree.SubElement(dch, qn('c:firstSliceAng'))
            el.set('val', '270')               # 12 点位起始（与 rotate(-90) 一致）
            el = dch.find(qn('c:holeSize'))
            if el is None:
                el = etree.SubElement(dch, qn('c:holeSize'))
            el.set('val', str(int(ch.get('holeSize') or 60)))
    # chartSpace / plotArea 无底无框：页面底色透过来，暗页不出白盒
    cs = chart._chartSpace
    chart_el = cs.find(qn('c:chart'))
    sp = etree.Element(qn('c:spPr'))
    etree.SubElement(sp, qn('a:noFill'))
    ln = etree.SubElement(sp, qn('a:ln'))
    etree.SubElement(ln, qn('a:noFill'))
    if chart_el is not None:
        chart_el.addnext(sp)
    pa = cs.find('.//' + qn('c:plotArea'))
    if pa is not None:
        sp2 = etree.SubElement(pa, qn('c:spPr'))
        etree.SubElement(sp2, qn('a:noFill'))
        ln2 = etree.SubElement(sp2, qn('a:ln'))
        etree.SubElement(ln2, qn('a:noFill'))
    return gf


def add_text_item(shapes, item, deck_lang, RGBColor, Pt, PP_ALIGN):
    from pptx.oxml.ns import qn
    from lxml import etree

    r = item['rect']
    st = item['style']
    tb = shapes.add_textbox(int(round(r['left'] * EMU_PER_PX)),
                                  int(round(r['top'] * EMU_PER_PX)),
                                  int(round(r['width'] * EMU_PER_PX)),
                                  int(round(r['height'] * EMU_PER_PX)))
    tf = tb.text_frame
    tf.word_wrap = True                      # wrap=square：改字按原宽重排不溢出
    from pptx.enum.text import MSO_AUTO_SIZE
    tf.auto_size = MSO_AUTO_SIZE.NONE        # 无 autofit，框即渲染宽
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

    fonts = parse_font_family(st['fontFamily'], deck_lang)
    align = {'left': PP_ALIGN.LEFT, 'start': PP_ALIGN.LEFT,
             'center': PP_ALIGN.CENTER, 'right': PP_ALIGN.RIGHT,
             'end': PP_ALIGN.RIGHT, 'justify': PP_ALIGN.JUSTIFY}.get(st['textAlign'], PP_ALIGN.LEFT)

    lines = item['lines'] or [{'runs': [{'text': '', 'bold': False, 'italic': False,
                                         'underline': False, 'strike': False,
                                         'fontSizePx': st['fontSizePx'], 'color': st['color']}]}]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = Pt(st['lineHeightPx'] * PX_TO_PT)   # lnSpc spcPts 精确行距
        p.space_before = Pt(0)
        p.space_after = Pt(0)
        for seg in line['runs']:
            run = p.add_run()
            run.text = seg['text']
            f = run.font
            f.size = Pt(seg['fontSizePx'] * PX_TO_PT)        # 1px = 0.5pt
            if seg.get('bold'):
                f.bold = True
            if seg.get('italic'):
                f.italic = True
            if seg.get('underline'):
                f.underline = True
            f.name = fonts['latin']                          # 只写 latin
            col = parse_color(seg.get('color') or st['color'])
            alpha = st.get('opacity', 1.0)
            if col:
                f.color.rgb = RGBColor(*col[:3])
                alpha *= col[3]
            rpr = run._r.get_or_add_rPr()
            ea = etree.SubElement(rpr, qn('a:ea'))           # ea 双 typeface 补丁
            ea.set('typeface', fonts['ea'])
            if seg.get('strike'):
                rpr.set('strike', 'sngStrike')
            if st.get('letterSpacingPx'):
                rpr.set('spc', str(int(round(st['letterSpacingPx'] * 50))))  # 1/100pt
            if alpha < 0.999:
                srgb = rpr.find(qn('a:solidFill') + '/' + qn('a:srgbClr'))
                if srgb is not None:
                    _patch_alpha(srgb, alpha)
    return tb


def add_shape_item(shapes, item, RGBColor, Pt):
    from pptx.enum.shapes import MSO_SHAPE

    r = item['rect']
    alpha = item.get('opacity', 1.0)
    borders = item.get('borders') or []
    bg = parse_color(item.get('bg'))

    # 单侧（或多侧）细边框且无填充 → 细条 rect（hairline 高频形态）
    if borders and not bg:
        for b in borders:
            x, y, w, h = r['left'], r['top'], r['width'], r['height']
            bw = b['width']
            if b['side'] == 'top':
                box = (x, y, w, bw)
            elif b['side'] == 'bottom':
                box = (x, y + h - bw, w, bw)
            elif b['side'] == 'left':
                box = (x, y, bw, h)
            else:
                box = (x + w - bw, y, bw, h)
            col = parse_color(b['color'])
            bar = shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                         int(round(box[0] * EMU_PER_PX)),
                                         int(round(box[1] * EMU_PER_PX)),
                                         max(1, int(round(box[2] * EMU_PER_PX))),
                                         max(1, int(round(box[3] * EMU_PER_PX))))
            bar.shadow.inherit = False
            if col:
                _solid_fill_rgb(bar.fill, RGBColor(*col[:3]), col[3] * alpha)
            bar.line.fill.background()
        return

    # 四边等宽边框 + 可选填充 → 原生形状
    rounded = (item.get('radius') or 0) > 0
    shp = shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
        int(round(r['left'] * EMU_PER_PX)), int(round(r['top'] * EMU_PER_PX)),
        int(round(r['width'] * EMU_PER_PX)), int(round(r['height'] * EMU_PER_PX)))
    shp.shadow.inherit = False
    if rounded:
        adj = min(0.5, item['radius'] / max(1.0, min(r['width'], r['height'])))
        try:
            shp.adjustments[0] = adj
        except (IndexError, ValueError):
            pass
    if bg:
        _solid_fill_rgb(shp.fill, RGBColor(*bg[:3]), bg[3] * alpha)
    else:
        shp.fill.background()
    if len(borders) == 4 and len({(b['width'], b['color']) for b in borders}) == 1:
        col = parse_color(borders[0]['color'])
        if col:
            shp.line.color.rgb = RGBColor(*col[:3])
            shp.line.width = Pt(borders[0]['width'] * PX_TO_PT)
    else:
        shp.line.fill.background()


def build_pptx(snap, deck_lang, deck_dir, raster_paths, out_path):
    from pptx import Presentation
    from pptx.util import Emu, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    from pptx.enum.shapes import MSO_SHAPE

    prs = Presentation()
    prs.slide_width = Emu(SLIDE_W_EMU)
    prs.slide_height = Emu(SLIDE_H_EMU)
    blank = prs.slide_layouts[6]
    stats = []
    for page in snap['pages']:
        slide = prs.slides.add_slide(blank)
        counts = {'text': 0, 'shape': 0, 'image': 0, 'bg': 0, 'chart': 0, 'raster': 0}
        rasterized = []
        if page['render_mode'] != 'baked':
            bg = parse_color(page.get('background'))
            if bg:
                rect = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                              0, 0, prs.slide_width, prs.slide_height)
                rect.shadow.inherit = False
                _solid_fill_rgb(rect.fill, RGBColor(*bg[:3]), bg[3])
                rect.line.fill.background()
                counts['bg'] = 1

        # L3 原生 chart：ig 外的直接落 slide（在文本层之下），ig 内的随组发放
        pending_ig_charts = {}
        for ch in page.get('charts', []):
            if ch.get('ig'):
                pending_ig_charts.setdefault(ch['ig']['root'], []).append(ch)
            else:
                add_native_chart(slide.shapes, ch, RGBColor, Pt)
                counts['chart'] += 1

        # L4 信息图分组：ig 根首次出现时建 grpSp（组名 = slide_id·族名），
        # 组内待发放 chart 一并入组；z-order = DOM 序（先加的在底）
        groups = {}

        def group_for(ig):
            key = ig['root']
            if key not in groups:
                g = slide.shapes.add_group_shape()
                g.name = '%s·%s' % (page['slide_id'], ig['family'])
                groups[key] = g
                for ch in pending_ig_charts.pop(key, []):
                    add_native_chart(g.shapes, ch, RGBColor, Pt)
                    counts['chart'] += 1
            return groups[key]

        for item in page['items']:
            shapes = group_for(item['ig']).shapes if item.get('ig') else slide.shapes
            if item['kind'] == 'text':
                add_text_item(shapes, item, deck_lang, RGBColor, Pt, PP_ALIGN)
                counts['text'] += 1
            elif item['kind'] == 'shape':
                add_shape_item(shapes, item, RGBColor, Pt)
                counts['shape'] += 1
            elif item['kind'] == 'image':
                src = os.path.join(deck_dir, item['src'])
                if not os.path.isfile(src):
                    page['uncovered'].append('image-missing:' + item['src'])
                    continue
                shapes.add_picture(src,
                                   int(round(item['rect']['left'] * EMU_PER_PX)),
                                   int(round(item['rect']['top'] * EMU_PER_PX)),
                                   int(round(item['rect']['width'] * EMU_PER_PX)),
                                   int(round(item['rect']['height'] * EMU_PER_PX)))
                counts['image'] += 1
                if item.get('uncovered'):
                    page['uncovered'].append(item['uncovered'] + ':' + item['src'])
            elif item['kind'] == 'raster':
                path = raster_paths.get(item.get('rasterIdx'))
                if not path or not os.path.isfile(path):
                    page['uncovered'].append('raster-missing:' + item.get('reason', '?'))
                    continue
                shapes.add_picture(path,
                                   int(round(item['rect']['left'] * EMU_PER_PX)),
                                   int(round(item['rect']['top'] * EMU_PER_PX)),
                                   int(round(item['rect']['width'] * EMU_PER_PX)),
                                   int(round(item['rect']['height'] * EMU_PER_PX)))
                counts['raster'] += 1
                rasterized.append(item.get('reason', '?'))
        # ig 组内只剩 chart 的兜底（组内无其它成员时也要建组发放）
        for key, charts in pending_ig_charts.items():
            family = charts[0]['ig'].get('family', 'ig')
            g = slide.shapes.add_group_shape()
            g.name = '%s·%s' % (page['slide_id'], family)
            for ch in charts:
                add_native_chart(g.shapes, ch, RGBColor, Pt)
                counts['chart'] += 1
        stats.append({'slide_id': page['slide_id'], 'render_mode': page['render_mode'],
                      'counts': counts,
                      'charts': [{'kind': c['kind'], 'recipe': c.get('recipe'),
                                  'categories': len(c['categories']), 'verify': c.get('verify')}
                                 for c in page.get('charts', [])],
                      'rasterized': sorted(set(rasterized)),
                      'uncovered': sorted(set(page['uncovered']))})
    prs.save(out_path)
    return stats


def postflight(out_path, expect_pages):
    from pptx import Presentation
    prs = Presentation(out_path)
    slides = list(prs.slides)
    if len(slides) != expect_pages:
        raise ExportError('postflight 失败：pptx 重开页数 %d ≠ %d' % (len(slides), expect_pages))
    for i, s in enumerate(slides, 1):
        if len(s.shapes) == 0:
            raise ExportError('postflight 失败：第 %d 页零形状' % i)
    log('postflight 通过：%d 页' % expect_pages)


# ---------------------------------------------------------------------------
# C3 字体内嵌（pptx fntdata；机制参照 ppt-master pptx_package/builder.py 的
# embedded fonts roundtrip——它服务导入侧，我们主动写入；MIT 许可）
FONT_REL_TYPE = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/font'
FONT_CONTENT_TYPE = 'application/x-fontdata'
PML = 'http://schemas.openxmlformats.org/presentationml/2006/main'


def _fsType_embeddable(fs_type):
    """fsType 许可闸【硬规则】：0（installable）/ 0x0004（preview&print）/
    0x0008（editable）才嵌；0x0002（restricted）及其余跳过。"""
    if fs_type == 0:
        return True
    if fs_type & 0x0002:
        return False
    return bool(fs_type & 0x0004 or fs_type & 0x0008)


def embed_fonts(pptx_path, deck_dir):
    """deck/fonts/*.ttf 子集嵌入 pptx。返回 {embedded, skipped} 或 None（无 fonts/）。
    woff2 不支持 fntdata——跳过并提示重跑 subset-fonts --format ttf。"""
    import zipfile
    fonts_dir = os.path.join(deck_dir, 'fonts')
    if not os.path.isdir(fonts_dir):
        return None
    files = sorted(f for f in os.listdir(fonts_dir) if f.lower().endswith(('.ttf', '.woff2')))
    if not files:
        return None
    result = {'embedded': [], 'skipped': []}
    parts = []   # (family, style_slot, payload)
    from fontTools.ttLib import TTFont
    for fn in files:
        fp = os.path.join(fonts_dir, fn)
        if fn.lower().endswith('.woff2'):
            result['skipped'].append({'file': fn, 'reason': 'woff2 不支持 fntdata 内嵌——'
                                      '重跑 subset-fonts.py --format ttf'})
            continue
        try:
            with TTFont(fp) as font:
                fs_type = font['OS/2'].fsType if 'OS/2' in font else None
                if fs_type is None or not _fsType_embeddable(fs_type):
                    result['skipped'].append({'file': fn, 'reason': 'fsType=%s 许可受限，不嵌'
                                              % (fs_type if fs_type is not None else '缺失')})
                    continue
                family = (font['name'].getDebugName(16) or font['name'].getDebugName(1)
                          or os.path.splitext(fn)[0])
                sub = (font['name'].getDebugName(17) or font['name'].getDebugName(2) or '').lower()
                weight = font['OS/2'].usWeightClass if 'OS/2' in font else 400
            slot = 'bold' if (weight >= 600 or 'bold' in sub) else \
                   ('italic' if 'italic' in sub or 'oblique' in sub else 'regular')
            with open(fp, 'rb') as f:
                parts.append({'family': family, 'slot': slot, 'payload': f.read()})
            result['embedded'].append({'file': fn, 'family': family, 'slot': slot})
        except Exception as e:
            result['skipped'].append({'file': fn, 'reason': '解析失败：%s' % e})
    if not parts:
        return result

    import xml.etree.ElementTree as ET
    tmp = pptx_path + '.tmp'
    with zipfile.ZipFile(pptx_path) as zin, \
            zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        names = set(zin.namelist())
        pres_xml = zin.read('ppt/presentation.xml').decode('utf-8')
        pres_rels = zin.read('ppt/_rels/presentation.xml.rels').decode('utf-8')
        ct = zin.read('[Content_Types].xml').decode('utf-8')
        for item in zin.infolist():
            if item.filename in ('ppt/presentation.xml', 'ppt/_rels/presentation.xml.rels',
                                 '[Content_Types].xml'):
                continue
            zout.writestr(item, zin.read(item.filename))
        # 1) fntdata 部件 + 关系
        rid_nums = [int(m.group(1)) for m in re.finditer(r'Id="rId(\d+)"', pres_rels)]
        next_rid = max(rid_nums, default=0) + 1
        rel_add, font_entries = [], []
        for i, part in enumerate(parts, 1):
            fname = 'font%d.fntdata' % i
            zout.writestr('ppt/fonts/' + fname, part['payload'])
            rid = 'rId%d' % next_rid
            next_rid += 1
            rel_add.append('<Relationship Id="%s" Type="%s" Target="fonts/%s"/>'
                           % (rid, FONT_REL_TYPE, fname))
            font_entries.append((part, rid))
        # 2) presentation.xml：embeddedFontLst（schema 位次：notesSz 之后、
        #    defaultTextStyle/extLst 之前）+ embedTrueTypeFonts 属性
        lst = ['<p:embeddedFontLst>']
        fam_slots = {}
        for part, rid in font_entries:
            fam_slots.setdefault(part['family'], {})[part['slot']] = rid
        for family, slots in fam_slots.items():
            lst.append('<p:embeddedFont><p:font typeface="%s"/>' % family)
            for slot in ('regular', 'bold', 'italic'):
                if slot in slots:
                    lst.append('<p:%s r:id="%s"/>' % (slot, slots[slot]))
            lst.append('</p:embeddedFont>')
        lst.append('</p:embeddedFontLst>')
        block = ''.join(lst)
        m = re.search(r'<p:(defaultTextStyle|extLst)[ >]', pres_xml)
        if m:
            pres_xml = pres_xml[:m.start()] + block + pres_xml[m.start():]
        else:
            pres_xml = pres_xml.replace('</p:presentation>', block + '</p:presentation>')
        if 'embedTrueTypeFonts' not in pres_xml:
            pres_xml = pres_xml.replace('<p:presentation ', '<p:presentation embedTrueTypeFonts="1" ', 1)
        # 3) rels + content-type
        pres_rels = pres_rels.replace('</Relationships>', ''.join(rel_add) + '</Relationships>')
        if 'fntdata' not in ct:
            ct = ct.replace('</Types>', '<Default Extension="fntdata" ContentType="%s"/></Types>'
                            % FONT_CONTENT_TYPE)
        zout.writestr('ppt/presentation.xml', pres_xml.encode('utf-8'))
        zout.writestr('ppt/_rels/presentation.xml.rels', pres_rels.encode('utf-8'))
        zout.writestr('[Content_Types].xml', ct.encode('utf-8'))
    os.replace(tmp, pptx_path)
    log('字体内嵌：%d 族入档（%s）' % (len(fam_slots), '、'.join(fam_slots)))
    return result


def run_export(deck_html, out_path):
    """可编辑轨全流程（供 CLI 与 export-pptx.py 双轨编排调用）。
    返回 report dict；失败抛 ExportError。产物：out_path + 同名 .report.json。"""
    deck_html = os.path.abspath(deck_html)
    deck_dir = os.path.dirname(deck_html)
    if not os.path.isfile(deck_html):
        raise ExportError('deck 不存在：%s' % deck_html)
    out_path = os.path.abspath(out_path)
    report_path = os.path.splitext(out_path)[0] + '.report.json'

    hash_before = sha256_file(deck_html)
    t0 = datetime.now(timezone.utc)
    work = tempfile.mkdtemp(prefix='pptx-editable-')
    try:
        snap, deck_lang, raster_paths = snapshot(deck_html, work)
        n_pages = len(snap['pages'])
        log('快照完成：%d 页（lang=%s，烙图 %d 件）' % (n_pages, deck_lang, len(raster_paths)))

        tmp_pptx = os.path.join(work, 'deck.pptx')
        stats = build_pptx(snap, deck_lang, deck_dir, raster_paths, tmp_pptx)
        fonts_report = embed_fonts(tmp_pptx, deck_dir)   # C3：字体内嵌（fsType 闸）
        postflight(tmp_pptx, n_pages)

        if sha256_file(deck_html) != hash_before:
            raise ExportError('单向纪律违反：导出过程中 index.html 发生变化')

        # 覆盖率与字体告警
        n_text = sum(s['counts']['text'] for s in stats)
        n_text_leaves = sum(
            len([it for it in p['items'] if it['kind'] == 'text']) for p in snap['pages'])
        ig_native = sum(len([it for it in p['items'] if it['kind'] == 'text' and it.get('ig')])
                        for p in snap['pages'])
        ig_total = sum(p.get('igTextTotal', 0) for p in snap['pages'])
        unsafe = {}
        for p in snap['pages']:
            for it in p['items']:
                if it['kind'] == 'text':
                    ff = it['style']['fontFamily']
                    for role, family in parse_font_family(ff, deck_lang).items():
                        if family.strip().lower() not in PPT_SAFE_FONTS:
                            unsafe.setdefault(ff, parse_font_family(ff, deck_lang))
        report = {
            'deck': deck_html,
            'generated_at': t0.isoformat(),
            'exporter': 'export-pptx-editable.py (C3)',
            'out': out_path,
            'pages': stats,
            'items': [{'slide_id': p['slide_id'],
                       'items': [{'kind': it['kind'], 'rect': it['rect'],
                                  'fontSizePx': it['style']['fontSizePx'] if it['kind'] == 'text' else None,
                                  'first_text': (it.get('lines') or [{}])[0].get('runs', [{}])[0].get('text', '')[:40]
                                  if it['kind'] == 'text' else ''}
                                 for it in p['items']]}
                      for p in snap['pages']],
            'totals': {
                'text': n_text,
                'shape': sum(s['counts']['shape'] for s in stats),
                'image': sum(s['counts']['image'] for s in stats),
                'chart': sum(s['counts']['chart'] for s in stats),
                'raster': sum(s['counts']['raster'] for s in stats),
            },
            'native_text_ratio': 1.0 if n_text_leaves == 0 else round(n_text / n_text_leaves, 4),
            'native_infographic_ratio': (1.0 if ig_total == 0
                                         else round(ig_native / ig_total, 4)),
            'fonts_embedded': (fonts_report or {}).get('embedded'),
            'fonts_skipped': (fonts_report or {}).get('skipped'),
            'fonts_note': ('fonts/ 不存在——字体未随档，跨机版式可能漂移（防线 B 回退栈）'
                           if fonts_report is None else None),
            'unsafe_fonts': unsafe,
        }
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        shutil.move(tmp_pptx, out_path)
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            f.write('\n')

        dt = (datetime.now(timezone.utc) - t0).total_seconds()
        log('导出完成：%s（%d 页，文本 %d 框 / 形状 %d / 图片 %d / 原生图表 %d / 烙图 %d，耗时 %.1fs）'
            % (out_path, n_pages, report['totals']['text'],
               report['totals']['shape'], report['totals']['image'],
               report['totals']['chart'], report['totals']['raster'], dt))
        report['elapsed_s'] = round(dt, 1)
        return report
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description='可编辑 PPTX 导出（三形态子技能 C）')
    ap.add_argument('deck', help='deck 的 index.html 路径')
    ap.add_argument('--out', help='输出 pptx 路径（缺省 <deck>/export/deck-editable.pptx）')
    args = ap.parse_args()

    deck_html = os.path.abspath(args.deck)
    if not os.path.isfile(deck_html):
        print('deck 不存在：%s' % deck_html, file=sys.stderr)
        return 1
    out_path = os.path.abspath(args.out) if args.out else \
        os.path.join(os.path.dirname(deck_html), 'export', 'deck-editable.pptx')
    try:
        report = run_export(deck_html, out_path)
        print(json.dumps({'ok': True, 'out': out_path,
                          'report': os.path.splitext(out_path)[0] + '.report.json',
                          'pages': len(report['pages']), 'totals': report['totals'],
                          'native_text_ratio': report['native_text_ratio'],
                          'native_infographic_ratio': report['native_infographic_ratio'],
                          'fonts_embedded': report['fonts_embedded'],
                          'elapsed_s': report['elapsed_s']}, ensure_ascii=False, indent=2))
        return 0
    except ExportError as e:
        print(str(e), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())

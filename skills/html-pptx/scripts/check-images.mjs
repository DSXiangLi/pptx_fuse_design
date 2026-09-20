#!/usr/bin/env node
/* check-images.mjs —— 图片槽位契约（editing-contract.md v5）静态校验器
 *
 * 扫描 deck HTML 中全部 <img data-editable-image>，校验：
 *   1. src 必须是指向 assets/ 的相对路径，且落盘文件存在（错误）；
 *   2. 槽位三属性完整性：有 data-image-slot 时，data-image-intent /
 *      data-image-state 必须齐全，state ∈ {placeholder, generated, uploaded}，
 *      slot 格式 <语义名>-<宽>x<高>（错误）；
 *   3. 三方绑定：slot 声明比例 ↔ 可静态判定的构图/素材宽高比，容差 5%
 *      （判定源：img width/height 属性、style 的 aspect-ratio 或 px 宽高对、
 *      素材文件固有尺寸 SVG/PNG/JPEG/GIF/WebP；全部不可判定 → 警告）；
 *   4. 存量兼容：缺 data-image-slot 的老 deck 给警告而非报错；
 *   5. --mode illustration（AI 插画模式产物）：反降级——任何
 *      state="placeholder" 的槽位或缺槽位的 img 均为错误。
 *
 * 用法：node skills/html-pptx/scripts/check-images.mjs <deck.html> [...] [--mode illustration]
 * 幂等（纯读取）。有错误打印清单并以非零退出；仅警告退出码为 0。零依赖，Node ≥ 20。
 */
import { readFileSync, existsSync } from 'node:fs';
import { dirname, join, normalize } from 'node:path';

const STATES = new Set(['placeholder', 'generated', 'uploaded']);
const RATIO_TOLERANCE = 0.05;
const SLOT_RE = /^[a-z0-9][a-z0-9-]*-(\d+)x(\d+)$/;

/* ---------- CLI ---------- */
const args = process.argv.slice(2);
let mode = 'default';
const files = [];
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--mode') {
    mode = args[++i] || '';
    if (!['default', 'illustration'].includes(mode)) {
      console.error('[check-images] ERROR: 未知 --mode ' + JSON.stringify(mode) + '（支持 default / illustration）');
      process.exit(2);
    }
  } else if (args[i].startsWith('--mode=')) {
    mode = args[i].slice('--mode='.length);
    if (!['default', 'illustration'].includes(mode)) {
      console.error('[check-images] ERROR: 未知 --mode ' + JSON.stringify(mode) + '（支持 default / illustration）');
      process.exit(2);
    }
  } else {
    files.push(args[i]);
  }
}
if (!files.length) {
  console.error('用法：node check-images.mjs <deck.html> [...] [--mode illustration]');
  process.exit(2);
}

/* ---------- 素材固有尺寸（零依赖解析） ---------- */
function intrinsicSize(path) {
  let buf;
  try { buf = readFileSync(path); } catch { return null; }
  const ext = (path.split('.').pop() || '').toLowerCase();
  if (ext === 'svg' || buf.subarray(0, 256).toString('latin1').includes('<svg')) {
    const head = buf.subarray(0, Math.min(buf.length, 4096)).toString('utf8');
    const tag = /<svg\b[^>]*>/i.exec(head);
    if (!tag) return null;
    const vb = /viewBox\s*=\s*"([\d.\-\s]+)"/i.exec(tag[0]);
    if (vb) {
      const p = vb[1].trim().split(/\s+/).map(Number);
      if (p.length === 4 && p[2] > 0 && p[3] > 0) return { w: p[2], h: p[3], via: 'svg viewBox' };
    }
    const w = /\bwidth\s*=\s*"([\d.]+)/i.exec(tag[0]);
    const h = /\bheight\s*=\s*"([\d.]+)/i.exec(tag[0]);
    if (w && h && +w[1] > 0 && +h[1] > 0) return { w: +w[1], h: +h[1], via: 'svg width/height' };
    return null;
  }
  /* PNG：8 字节签名 + IHDR，宽高于偏移 16/20（大端） */
  if (buf.length > 24 && buf.readUInt32BE(0) === 0x89504e47) {
    return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20), via: 'png IHDR' };
  }
  /* GIF：宽高于偏移 6/8（小端） */
  if (buf.length > 10 && (buf.toString('latin1', 0, 3) === 'GIF')) {
    return { w: buf.readUInt16LE(6), h: buf.readUInt16LE(8), via: 'gif header' };
  }
  /* JPEG：扫描 SOF0–SOF15（排除 C4/C8/CC）段 */
  if (buf.length > 4 && buf[0] === 0xff && buf[1] === 0xd8) {
    let off = 2;
    while (off + 9 < buf.length) {
      if (buf[off] !== 0xff) { off++; continue; }
      const marker = buf[off + 1];
      if (marker >= 0xc0 && marker <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(marker)) {
        return { w: buf.readUInt16BE(off + 7), h: buf.readUInt16BE(off + 5), via: 'jpeg SOF' };
      }
      if (marker === 0xd8 || marker === 0x01 || (marker >= 0xd0 && marker <= 0xd7)) { off += 2; continue; }
      off += 2 + buf.readUInt16BE(off + 2);
    }
    return null;
  }
  /* WebP：RIFF....WEBP + VP8X / VP8 / VP8L */
  if (buf.length > 30 && buf.toString('latin1', 0, 4) === 'RIFF' && buf.toString('latin1', 8, 12) === 'WEBP') {
    const chunk = buf.toString('latin1', 12, 16);
    if (chunk === 'VP8X') {
      return { w: 1 + buf.readUIntLE(24, 3), h: 1 + buf.readUIntLE(27, 3), via: 'webp VP8X' };
    }
    if (chunk === 'VP8 ') {
      return { w: buf.readUInt16LE(26) & 0x3fff, h: buf.readUInt16LE(28) & 0x3fff, via: 'webp VP8' };
    }
    if (chunk === 'VP8L' && buf[20] === 0x2f) {
      const b0 = buf[21], b1 = buf[22], b2 = buf[23], b3 = buf[24];
      return { w: 1 + (((b1 & 0x3f) << 8) | b0),
               h: 1 + (((b3 & 0x0f) << 10) | (b2 << 2) | ((b1 & 0xc0) >> 6)), via: 'webp VP8L' };
    }
    return null;
  }
  return null;
}

/* ---------- HTML 解析（产物为技能生成的规整 HTML，regex 足够） ---------- */
function parseAttrs(tag) {
  const attrs = {};
  const re = /([\w-]+)(?:\s*=\s*"([^"]*)")?/g;
  let m;
  while ((m = re.exec(tag))) attrs[m[1]] = m[2] === undefined ? '' : m[2];
  return attrs;
}

function styleRatios(style) {
  /* 从 inline style 提取可判定的宽高比来源 */
  const out = [];
  if (!style) return out;
  const ar = /(?:^|;)\s*aspect-ratio\s*:\s*([\d.]+)\s*(?:\/\s*([\d.]+))?/i.exec(style);
  if (ar && +ar[1] > 0) {
    const w = +ar[1], h = ar[2] ? +ar[2] : 1;
    if (h > 0) out.push({ ratio: w / h, via: 'style aspect-ratio' });
  }
  const w = /(?:^|;)\s*width\s*:\s*([\d.]+)px/i.exec(style);
  const h = /(?:^|;)\s*height\s*:\s*([\d.]+)px/i.exec(style);
  if (w && h && +w[1] > 0 && +h[1] > 0) out.push({ ratio: +w[1] / +h[1], via: 'style width/height' });
  return out;
}

/* ---------- 主校验 ---------- */
const errors = [];
const warnings = [];
function err(msg) { errors.push(msg); }
function warn(msg) { warnings.push(msg); }

for (const file of files) {
  const deckDir = dirname(file);
  let html;
  try { html = readFileSync(file, 'utf8'); }
  catch (e) { err(file + ': 读取失败（' + e.message + '）'); continue; }

  const imgRe = /<img\b[^>]*>/g;
  let m, count = 0;
  while ((m = imgRe.exec(html))) {
    const attrs = parseAttrs(m[0]);
    if (!('data-editable-image' in attrs)) continue;
    count++;
    const who = file + ' <img src=' + JSON.stringify(attrs.src || '(无)') + '>';

    /* 1. src 契约与落盘存在性 */
    const src = (attrs.src || '').split('?')[0];
    if (!src || /^(?:[a-z]+:)?\/\//i.test(src) || src.startsWith('/') || src.startsWith('data:')) {
      err(who + ' src 必须是 assets/ 相对路径（不内嵌、不外链），实为 ' + JSON.stringify(attrs.src));
    } else if (!src.startsWith('assets/')) {
      err(who + ' src 必须指向 assets/ 目录，实为 ' + JSON.stringify(src));
    } else if (!existsSync(join(deckDir, normalize(src)))) {
      err(who + ' 引用的落盘文件不存在：' + src);
    }

    /* 2. 槽位三属性 */
    const slot = attrs['data-image-slot'];
    const intent = attrs['data-image-intent'];
    const state = attrs['data-image-state'];
    if (!slot) {
      const msg = who + ' 缺 data-image-slot（存量兼容：编辑器仍可上传替换，建议补齐 v5 三属性）';
      if (mode === 'illustration') err(msg + '——插画模式产物必须带完整槽位契约');
      else warn(msg);
      continue;   /* 无声明比例，比例绑定无从校验 */
    }
    const sm = SLOT_RE.exec(slot);
    if (!sm || +sm[1] <= 0 || +sm[2] <= 0) {
      err(who + ' data-image-slot 格式非法：' + JSON.stringify(slot) + '（期望 <语义名>-<宽>x<高>，如 cover-hero-21x9）');
      continue;
    }
    if (!intent || !intent.trim()) err(who + ' 有 data-image-slot 但缺 data-image-intent（v5 三属性不完整）');
    if (!state) err(who + ' 有 data-image-slot 但缺 data-image-state（v5 三属性不完整）');
    else if (!STATES.has(state)) err(who + ' data-image-state 非法：' + JSON.stringify(state) + '（合法值 placeholder|generated|uploaded）');

    /* 3. 反降级（插画模式） */
    if (mode === 'illustration' && state === 'placeholder') {
      err(who + ' 插画模式产物残留 placeholder 状态槽位（slot=' + slot + '）——生成失败应诚实回退并在交付说明列出，冒充违规');
    }

    /* 4. 三方绑定：声明比例 vs 可判定来源（容差 5%） */
    const declared = +sm[1] / +sm[2];
    const sources = [];
    const aw = +attrs.width, ah = +attrs.height;
    if (aw > 0 && ah > 0) sources.push({ ratio: aw / ah, via: 'img width/height 属性' });
    sources.push(...styleRatios(attrs.style));
    const assetPath = join(deckDir, normalize(src));
    if (src.startsWith('assets/') && existsSync(assetPath)) {
      const dim = intrinsicSize(assetPath);
      if (dim && dim.w > 0 && dim.h > 0) sources.push({ ratio: dim.w / dim.h, via: '素材固有尺寸（' + dim.via + '）' });
    }
    if (!sources.length) {
      warn(who + ' 无法静态判定构图/素材宽高比，slot 声明比例（' + sm[1] + 'x' + sm[2] + '）未经三方绑定校验');
      continue;
    }
    for (const s of sources) {
      const dev = Math.abs(s.ratio - declared) / declared;
      if (dev > RATIO_TOLERANCE) {
        err(who + ' 比例绑定破坏：slot 声明 ' + sm[1] + 'x' + sm[2] + '（' + declared.toFixed(4) + '）与 ' +
            s.via + '（' + s.ratio.toFixed(4) + '）偏差 ' + (dev * 100).toFixed(1) + '%，超出容差 5%');
      }
    }
  }
  if (!count) warn(file + ': 未发现任何 data-editable-image 图位');
}

/* ---------- 汇总 ---------- */
for (const w of warnings) console.warn('[check-images] WARN: ' + w);
if (errors.length) {
  console.error('[check-images] 校验失败（' + errors.length + ' 项错误' +
    (warnings.length ? '，' + warnings.length + ' 项警告' : '') + '，mode=' + mode + '）：');
  for (const e of errors) console.error('  - ' + e);
  process.exit(1);
}
console.log('[check-images] 通过：' + files.length + ' 个文件，mode=' + mode +
  (warnings.length ? '（' + warnings.length + ' 项警告）' : '（无警告）'));

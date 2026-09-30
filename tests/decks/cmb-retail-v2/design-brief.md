# cmb-retail-v2 施工约定（E4 包豪斯 · 设计升级版）

> 任务：以 `tests/decks/cmb-retail/`（B1 瑞士国际主义版）为**内容唯一来源**，做一份内容完全相同（逐字 1:1、同 54 页、同页序、同图片素材）、设计感更强的版本。
> 内容口径沿用 `tests/decks/cmb-retail/page-plan.md`（逐页内容清单/图片槽位/密度自评全部有效，唯"主题=B1"及相关 B1 词汇条款作废）。
> 密度=高密度（阅读主导）不变；场景=银行零售高拜汇报；受众=招商银行。
>
> **主题变更记录**：v2.0 = A1 电子杂志·基底（墨黑米白、衬线、Ghost 巨字）；v2.1 应用户要求（封面重设计 + 配色更亮更多样）改冻结为 **E4 包豪斯·基底原色红**——米白纸 #f4f0e4 + 墨黑 #141412 + 原色红 #D1342B；几何无衬线（Helvetica Neue/PingFang SC）+ 字重倒挂阶梯；母题换为基本形三件套（.mt-bau-circle/.mt-bau-tri/.mt-bau-square）；列表墨点改为内联 5px 墨方块（data-editable-skip）；封面/封底为满版原色红特权页（反白几何构成 + 照片纸托装裱），五个章节页保持暗墨底 + 红圆焦点的明暗节奏。

## 主题冻结（不可协商）

**A1 电子杂志（id: a1）· 基底配色（纯墨黑 + 暖米白）**，四个变体均不采用。

- token 已注入骨架 `:root`（含 G3 墨韵质感与图表推导 token），落码一律 `var(--*)` / `color-mix()`，**禁字面 hex**。
- accent == ink（纯墨黑）：**没有彩色高亮可用**。强调手段 = 字重 / 字号对比 / 留白 / hairline / 暗色反白。这是本主题的设计语言核心——靠排版制造高级感的编辑部杂志。
- G3 质感：`--texture-type:glow`，`--texture-scope:cover`——质感层只铺仪式页（`.cover-page` 自动），正文页一律不加 `texture-on`。

### 禁用的 B1 词汇（串味即失败）
禁 IKB 蓝色块、禁 `.mt-swatch` 色块编号、禁 `.mt-cross` 加号角标、禁 `.mt-grid-dots` 网格点阵、禁"页题前 48×6 accent 题花条"。这些是全 v1 的瑞士系/旧词汇。

### A1 G9 母题词汇（只用这三件，母题件一律 data-editable-skip）
1. **`.mt-ghost` Ghost 残影巨字**——页面背景层，与内容相关的单字/关键词（1–4 字），低透明描边。用法：`<div class="mt-ghost" data-editable-skip aria-hidden="true" style="right:-40px;bottom:-60px;font-size:520px">弘</div>`。纪律：每页至多一个；只作背景不抢焦（z-index:0 已在类里，内容区须 `position:relative;z-index:1`）；**正文页连用不超过两页**（全 deck 约 8–12 页用即可，优先数据英雄页/转折页）；禁与标题同区抢焦。
2. **`.mt-vquote` 竖排题字条**——只许封面/目录/章节页/封底的侧缘，内容用 mono 拉丁或拼音（如 `TIANHONG ASSET MANAGEMENT`、章节拼音）。正文页禁用。
3. **`.mt-dot` 墨点角标**——5px 实心方点，替代列表项圆点/编号前缀：`<span class="mt-dot" data-editable-skip></span>`。

## 字阶（高密度档，画布 px，硬规则）

- 页标题 h2：font-display 衬线 56–64px / **字重 600**（A1 衬线恒重立场，不走倒挂）/ line-height ≥1.3。
- 仪式页巨题：≥77px→600（封面/封底可 700）；章节页章节题 88–100px / 600。
- kicker（小节号如 "1.1 · 整体特色及优势"）：mono 20px / 500 / 低明度；**中文 letter-spacing:0**。
- 正文 ≥18px / 400–500；卡片描述 ≥16px（16–17.9px 文字必须显式 `font-family:var(--font-mono)`，否则 j_render_check 判违规）。
- 标注层：mono 12–16px + `color-mix(in srgb, var(--ink) 45%, transparent)` 级低明度 + ≤20 字符 + 不承载关键结论。暗页上低明度改用 paper 派生（`color-mix(in srgb, var(--paper) 55%, transparent)`）。
- 来源脚注：注记块 note-block（mono 14px 低明度，页底部）。
- 同页字重纪律：小字字重 ≥ 大字字重；14–18px 小字禁 300。
- 中文不设 letter-spacing（或 0）、禁 text-transform:uppercase 用于中文；行高：标题 ≥1.3、正文 ≥1.6。

## 明暗节奏（v2 相对 v1 的核心升级之一）

- **暗色反白页**（`.slide.dark.cover-page`）：封面 p1、五个章节页（p3/p10/p24/p40/p45）、封底 p54。共 7 页暗。
- 目录 p2 与全部正文页 = 亮纸面。章节暗页把 54 页切成五段呼吸，明暗交替天然成立。
- 暗页上的容器明度档用 `var(--ink-tint)` 面；hairline 用 `color-mix(in srgb, var(--paper) 22%, transparent)`；`.mt-ghost` 描边色在暗页改 `-webkit-text-stroke:1px color-mix(in srgb,var(--paper) 20%,transparent)`（inline 覆盖）。

## 刊头家具（正文页统一，仪式页不设）

```html
<header class="masthead">
  <span data-editable style="letter-spacing:0">1.1 · 整体特色及优势</span>
  <span><img data-editable-image data-image-slot="masthead-logo-8x3" data-image-intent="天弘基金品牌横式标识（页眉位）" data-image-state="uploaded" src="assets/s02_02.png" alt="天弘基金标识" width="182" height="68" style="width:182px;height:68px;display:block"></span>
</header>
<footer class="mastfoot">
  <span data-editable style="letter-spacing:0">天弘基金 · 业务情况汇报</span>
  <span data-editable>NN / 54</span>
</footer>
```

- 小节号与章节名对照见旧 page-plan.md「章节结构」与逐页行；页码 NN = 原 deck 页码两位数字。
- masthead 是 absolute 顶 40px；正文内容区从约 y=150px 起排（页题区自行留位）。
- 页题区推荐形态（杂志感来源）：kicker 行（mono 20px 低明度，含小节号）→ 衬线大题（56–64px/600）→ 可配一条 `.rl-fade` 或 hairline 细分。**不要**色块题花。

## 容器与边界（A1 G4 高密度口径，硬规则）

- **无卡片立场**：直角色块、无阴影、无圆角、禁渐变。容器边界 = `var(--paper-tint)` 灰档平涂面（靠空气不靠边界）；锚点容器可降纸档 + 1px hairline（`1px solid color-mix(in srgb, var(--ink) 18%, transparent)`）。同页面灰档面与描边框不混用。
- 高密度页的要点必须装进 K 期 §13 六型容器（kv-rows / ticker / metric-card / versus-cols / stack-rows / note-block），裸排列表即违规；容器内四层字阶（eyebrow mono 低明度 → 题 → 体 → 注 mono 低明度）。
- 列表项前导用 `.mt-dot` 墨点（不用圆点/色块编号）。
- `.rl-*` 装饰线每页 ≤3 款、一律 data-editable-skip；目录/清单对位可用 `.rl-leader`（每页至多一组）。

## 构图与谱系（A1 G8）

- 亲和：巨字宣言、图文证据、轴与节点（时间轴/演进）。**禁连续两页网格矩阵**——杂志节奏靠疏密对比。原 v1 是网格矩阵的页，优先考虑改造为：裂屏对开（左题右证）、轴与节点、巨字+容器群。
- 一页一个视觉重心；连续页构图重心左右互换。
- 数据英雄页：巨数用衬线 display 600 直排（72–120px）+ mono 标注，count-up 只给真 KPI 英雄数字（每页至多 1 处，全 deck 控制在 6 页以内）。

## 动效（A1 G5 editorial，标准-lite 档）

- 节奏：时长偏慢半拍、阶梯 `--d` 步长 ≥0.15s。气质安静，显影感。
- **正文页**：L1 入场——页题/主容器 `class="reveal"`（`style="--d:.2s"` 阶梯）或 `data-anim="wipe-clip"` / `blur-in` / `rise-in`。同页 recipe 不超过 2 种。
- **数据页**：图表描边 `data-anim="draw-line"`（标在 SVG 描边元素上）；KPI 巨数可 `data-anim="count-up"`（直接写终值文本）。
- **仪式页**：大标题 `data-anim="mask-lines"`（`.ml-line>.ml-inner` 分行结构，`.ml-inner` 是 data-editable 叶子）或 `data-anim="chars"`（纯文本，骨架运行时拆字，**产物中禁出现拆字 span**）。
- **禁**：scale-pop / persp-in / scramble / typewriter / data-ptr / data-scroll / amb-* / light-* / data-fx / gradient-flow（A1 无此许可）。mend-bar / data-rotate 不用。

## 图表纪律

- 配方按 `skills/html-pptx/references/charts.md` v2；系列色从 `--chart-series-*` token 取（A1 accent==ink → 自动同色系灰阶，不要自己造彩色）。
- 几何层 SVG 整体 data-editable-skip；轴标签/数值直标文字 data-editable；每个图表页至少一种标注（数值直标/参考线/注释旗标）。数据逐字来自旧页，禁编造。

## 图片槽位（契约 v5，与 v1 同口径）

- 沿用旧页图片文件与槽位三属性：`data-image-slot`（语义名-宽x高）/ `data-image-intent` / `data-image-state="uploaded"`，src 指 `assets/` 同名文件。
- 三方绑定（容差 5%）：slot 比例 = width/height 属性比 = 素材固有比；禁裁剪式 object-fit 改比例（cover 只在同比例下作保险）。素材固有尺寸可用 `file assets/xxx.png` 或 python PIL 查。
- 头像/证件照：显示高度统一 150px，宽=150×固有比，object-fit:cover。
- 章节徽记 s03_01 复用槽位名 `chapter-emblem-1x1`；页眉 logo 复用 `masthead-logo-8x3`；同文件同页多次引用时槽位名加页前缀区分。

## 契约标记（硬规则）

- 每页 `<div class="slide-slot"><section class="slide" data-slide-id="…">…</section></div>`；slide_id 与旧 deck 逐字一致。
- data-editable 只标叶子文本元素（h1/h2/p/li/td/span 等），容器不标；元素内部只含纯文本或 `<b>/<i>/<em>/<strong>/<br>`。
- 装饰件（母题/色块/分隔线/背景层）一律 data-editable-skip。
- 信息图根 `data-ig="<族>-<骨架>"` + `data-ig-skin`，数据单元 `data-ig-item`。
- 表格用 `<table>`，单元格文字 data-editable 标在 `<td>/<th>` 上。

## 导出安全几何（C5c，沿用 v1 教训）

- 通栏带（`background:var(--paper-tint)`）横向 padding ≥44px。
- 单行文本在 PPT 度量下比 Chromium 宽 5–15%，右对齐/贴边单行要预留余量（必要时 max-width 限宽改双行）。
- 装饰元素不要放在 masthead/mastfoot 的 DOM 序之后却位置重叠处（masthead 是 absolute，绘制顺序高于在流元素）。

## 容量与校验（交付前自检）

- 先量容量再动笔：全角记 1、半角记 0.5；超预算就精简容器内排布或调整分区，**禁删文案、禁缩字号突破底线**。
- 正文页内容高度应达画布 60% 以上；溢出画布即失败。
- 产出 = 纯 `<div class="slide-slot">…</div>` 片段序列（不要 `<html>/<style>` 外壳），写入指定 fragment 文件。

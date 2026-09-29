---
name: html-pptx
description: 生成 16:9 竖向滚动的高品质单文件 HTML 幻灯片（网页版 PPT）。当用户需要制作分享、演讲、发布会、汇报风格的网页 PPT，或提到"HTML PPT"、"网页幻灯片"、"把 pptx 转成网页"时使用。产物可被配套的编辑器页面直接打开，就地编辑文字与图片。
---

# HTML PPTX 生成技能

把内容变成一份**可以用浏览器直接演示、可以被编辑器直接修改**的 HTML 幻灯片。

## 产物形态

- 交付物：一个 `index.html` + 一个 `assets/` 图片目录。此外什么都没有。
- 每页是 1920×1080 的固定画布，浏览器里整体缩放适配窗口，**竖向滚动**翻页。
- 文件保持纯净：不含编辑器代码、不含构建产物、不依赖网络（字体用系统栈）。
- 产物必须带有完整的可编辑标记（见下），因为用户接下来会用编辑器页面打开它改字换图。

## 第一性原则

这五条是从"为什么 AI 做的 PPT 会垮"反推出来的。违反任何一条，成品必然垮掉——不是可能，是必然。

### 1. 决策前置

AI 的默认审美会收敛到平庸：居中 hero、紫蓝渐变、卡片墙。这种收敛发生在**决策层**，不在执行层——写得再认真也救不了错误的方向。
→ 主题、密度、叙事弧在写第一行 HTML 之前冻结。候选项来自策展的主题库，让用户**看着选**，不让 AI 即兴配色。约束不是质量的限制，是质量的来源。

### 2. 一致性来自系统，单调来自重复

一份 deck 的视觉统一，靠的是一套 token（色、字、间距、动效变量）贯穿始终，**不是**把同一个版式复制十页。锁死版式换稳定是下策——它压抑内容表达；完全自由是错策——它必然漂移。
→ token 层枚举（主题库只选不改），版式层自由（构图由每页内容决定）。连续两页构图雷同，就是失败。

### 3. 容量先于版式

文字溢出是 HTML 幻灯片的第一大死因，而它的根因是"写完才发现装不下"。
→ 先数清楚这页有多少字、几个条目、几个数字，**再**选构图。装不下就拆页，永远不靠缩字号硬塞。修复溢出的阶梯：微调间距 → 精简文案 → 拆页。缩字号突破底线是禁区。

### 4. 一页一意

一页只传递一个观点。想讲两件事，就拆成两页——页数没有成本，读者的注意力才有成本。如果一页讲完后你自己都说不出"这页的一句话是什么"，这页就不该存在。

### 5. 文件即真相

生成的 HTML 会被编辑器页面直接打开、修改、存回。编辑器和你是两个不相识的进程，**HTML 文件里的标记是你们之间唯一的通信协议**。
→ 所有用户可见的文字和图片都必须带契约标记（`data-editable` 族）。标记不是修饰，是产物的组成部分。省略标记 = 交付一个无法编辑的残次品。

## 规则效力约定

本技能中每条规则都属于三级之一，遵守方式不同：

- **【硬规则】**不可协商。违反了就是 bug，必须修。
- **【默认】**默认遵守，但内容确实需要时可以推翻——推翻时必须在交付说明里写明理由。
- **【参考】**启发与召回用，不是配额，不是检查项。

## 工作流

### Step 0 · 明确输入

两种入口，先确认是哪一种：

- **从 0 到 1**：用户提供主题 / 文案 / 资料。
- **pptx 转换**：用户提供 .pptx 文件。转换是**内容重组，不是逐页复刻**：
  1. 用可用工具（如 python-pptx）提取全部文字与图片；图片原样落盘到 `assets/`（保持原图，不重画、不压缩），并按画面角色补 `data-image-slot` / `data-image-intent`、置 `data-image-state="uploaded"`（契约 v5：用户提供的真图视同上传）；
  2. 通读提取出的全部内容，按叙事弧重新组织——原 pptx 的页序只是参考，合并碎碎念页、拆开过载页；
  3. 之后走与 0-1 完全相同的流程（页计划表 → 冻结主题 → …）。

### Step 0.5 · 需求脑暴

【默认】动笔前先做需求对齐——按 `references/briefing.md` 的八组问题（场景/受众/内容来源与切分/页数预算/视觉风格/字体/动效与明暗/封面与交付 + 自由补充）与用户快速对齐。每组有缺省，用户没答就走缺省不追问；追问至多两轮。若用户在编辑器里填过「需求脑暴页」，其导出的需求简报即本步产物，直接进入下一步。风格明显不合理时（合规报告配糖果风之类）必须回谏一次。

### Step 1 · 页计划表

不动手写代码。先输出一份页计划表，与用户确认：

| 页 | 叙事角色 | 这一页的一句话 | 内容清单（估算字数/条目数） | 明/暗 | 呈现发散（关键页必填） |
|---|---|---|---|---|---|

叙事角色从内容里长出来（开场、问题、论证、数据、转折、收束……），不要套固定目录模板。
明暗节奏：避免连续 3 页以上同为亮色或暗色页；长 deck 每 3–4 页安排一次明暗呼吸。

**呈现发散步**（想象层，H 期）【默认·关键页强制】：封面、数据英雄、对比、流程等关键页，在本列先写 **3 个不同轴上的呈现方案**（每案必须命名差异轴：尺度 / 隐喻 / 维度 / 动静 / 材质）再选定——查询 `references/motifs.md`（内容关系 → 视觉隐喻库）。普通页豁免。发散文案留在计划表，不进产物。反例纪律：对比不要只有左右分栏、增长不要只有上升柱图、数字不要只有 count-up、流程不要只有箭头——收敛到默认解可以，但要能说清为什么其他隐喻不合适。

**密度决策在本步冻结**【硬规则】：与用户确认这份 deck 是**低密度（演讲主导）**还是**高密度（阅读主导）**——只有两档，内容混合时向更近的一档靠拢。密度决定单页信息量、字阶和页数策略，规则见 `references/typography.md` §5。先定密度再排页：低密度宁可加页，高密度用结构化版式承载（文本容器分型见 `components.md` §13——高密度页的要点必须装进容器型，裸排列表即违规）。

**章节结构**（skeleton v7 起）：按叙事弧给章节页标 `data-chapter`（章节页 `.slide` 同时带 `id`，与 `data-slide-id` 同值）；高密度档的封面【默认】必须承载目录——`<a class="nav-link" href="#id">` 章节链接（原生可点可 Tab，骨架另支持数字键 1–9 直跳）。低密度短 deck 可省略。

### Step 2 · 冻结主题

从 `references/themes.md` 中推荐 2–3 套候选让用户选（说明各自气质与 focus——focus 即该主题设计感的来源：配色 / 质感 / 字排 / 形态 / 装饰，能渲染预览就渲染预览）。主题库是**两级架构**（G 期起）：**重主题**（七层表达力栈 L1–L7，Schema 化 G0–G9 字段组——色彩/字排/质感/装饰母题/容器风格/动效签名/构图倾向）+ **配色变体**（每主题 ≥3 套，同一世界的不同光线/材质演绎）——选定主题后**同时冻结变体**（默认基底配色）。G0 的「世界参考」与「unforgettable」是向用户解释主题气质的最好语言。
【硬规则】主题**只选不改**：选定后整套 token（基底 + 变体覆盖合并）复制进骨架的 `SLOT: theme tokens`，主题 G9 的 css 块**逐字**复制进骨架的 `SLOT: theme css`（骨架 v6 起；无母题的主题该槽位留空）。不混搭、不改色值、不自定义 hex；装饰母题只用本主题 G9 词汇，禁跨主题借用。用户坚持自定义时，委婉说明策展预设的意义，仍坚持则在交付说明中记录。

### Step 3 · 复制骨架

【硬规则】把 `assets/skeleton.html` **逐字复制**为产物起点（以仓库当前骨架版本为准，版本见 `<meta name="skeleton-version">`），只填充标有 `SLOT:` 的槽位（主题 token、主题 CSS 块、标题、页面、页码初始文本 `1 / N`）。框架层的 CSS 与 JS **一个字符都不改**——它处理的缩放、滚动、键盘、打印、降级问题，每次重写都会引入新的微妙 bug。

### Step 4 · 逐页生成

每页动手前，重读一遍主题 token 和页计划表中本页那一行。

**先量容量再动笔**【硬规则】：按 `references/typography.md` 的槽位字数预算核对本页内容清单（全角记 1、半角记 0.5），超预算就精简或拆页；标题字号按中文分档表取档，字重按字重阶梯取档。

构图由内容决定。几个【默认】层面的提醒：

- 一页一个视觉重心。大标题、大数字、大图，选一个当主角。
- 卡片网格是 AI 的肌肉记忆，不是设计。同一份 deck 里卡片墙版式最多出现一次。
- 给标签换个颜色不是设计。层级靠字号、字重、留白的对比建立。
- 需要信息图时查 `references/components.md`（v3：构图谱系 × 结构族 × Item 皮肤 × 参数变体）：先定页面构图谱系（§11，连续 3 页同谱系即违规），再按**三步选型**——内容关系 → 结构族 → Item 皮肤；动笔前过**数据形态自证清单**【硬规则】（内容能填入该族数据形态、项数在骨架合法区间、binary 对比恰好两项、族×皮肤组合在白名单内），自证不过就换族或拆页；容器遵守 §12 四档明度与 accent 单焦点纪律；丰富度参照 `gallery/index.html`（每族 × 代表皮肤一页高复杂度实例，可照抄连接件层次/数据墨迹/标注层）。
- 需要图表时查 `references/charts.md`（v2：14 配方——基础五 + 扩展九，均带标注层规格；系列色 8 档推导）：数据真实性与图文一致规则不变，每个图表页至少带一种标注（参考线/区间带/数值直标/注释旗标）。
- 动效用骨架的语义配方：页面 `data-animate` 选节奏、元素按族标记（`data-anim` / `data-ptr` / `data-scroll` / `amb-*`·`light-*` class），recipe 词汇表（8 族）与五层启用矩阵见 `references/motion.md`（v3.1）——拆字类动效（chars/words/shatter）与 typewriter/scramble 只写纯文本 + 标记，拆字由骨架 JS 运行时执行；【硬规则】产物文件中禁止出现拆字 span（文本破坏性动效必须运行时化，契约条款）；动效档（克制/标准/华丽）来自设计意图或用户指定，默认标准。**主题动效签名**（G5）必须遵守：锚点偏好决定 recipe 首选序列、节奏偏移决定时长档与阶梯步长、缓动签名已由主题 CSS 块注入（骨架 var() 消费，无需落码）；注意力预算与禁用清单是硬上限，签名只在预算内定倾向。canvas FX 仪式层（`data-fx`，v5.1）：默认关——只有主题 G5「fx 许可」白名单内的效果可用，只许 `.cover-page` 仪式页、每页至多 1 个，写法唯一（`<canvas data-fx="…" data-editable-skip aria-hidden="true">`），参数全部烧死在骨架不可调（纪律见 motion.md §4 fx 小节）。
- **装饰母题**（G 期，主题 G9）：母题类（`.mt-*`）已在骨架主题 CSS 槽位，产物直接用类名引用即可；只用本主题词汇（加号/网格点阵属瑞士系、Ghost 字/竖排题字条属杂志系、ASCII 框/光标属终端、题花/首字下沉属出版……串味比配色串味更毁差异化，themes.md 禁忌节有完整口径）。母题纯装饰件标 `data-editable-skip`；文本载体类母题（如 `.mt-pub-dropcap` 首字下沉、`.mt-pub-pull` 引文拉页）样式由类承担，文本照常 `data-editable`。关键页执行页计划表的「呈现发散」列（motifs.md）；若计划表未做，现场补做再动笔。
- 中文排版：中文不设 `letter-spacing`（或设为 0）、不用 `text-transform: uppercase`、行高比西文更宽（标题 ≥1.3，正文 ≥1.6）。
- 文本容器（K 期，components.md §13）：高密度页的要点必须装进容器分型（字段行/数据带/指标卡/对照列/堆栈层/注记块），容器内四层字阶纪律是硬规则；容器造型由主题 G4/G9 承担。"问题→解决"类指标用 mend-bar 双态修复条，流水线/轮值状态用 data-rotate 轮转高亮——内容→动效对照表见 `motion.md` §3。
- 装饰元素（色块、分割线、背景图形）标 `data-editable-skip`，让编辑器忽略它们。

### Step 5 · 渲染校验

【硬规则】用无头浏览器（Playwright 或同等工具）真实渲染，逐页测量：

1. 每页内容是否溢出 1920×1080 画布（量 `scrollHeight`/`scrollWidth`，不要目测）；
2. 文字之间是否发生意外重叠；
3. 底部是否留白过多（内容高度不足画布 60% 的页要反思构图）。

发现问题按修正阶梯处理：微调间距 → 精简文案 → 拆页。【硬规则】正文字号不得低于 18px（画布坐标系）。

渲染校验通过后【硬规则】跑容量门禁（第二闸，PPT 度量口径）：

```bash
python3 skills/html-pptx/scripts/check-capacity.py <deck目录>/index.html --json <deck目录>/capacity-report.json
```

该脚本用 PPT 侧的候选字体集度量（`pptx_text_metrics.py`，贪心换行与认证同函数）在 HTML 搭建期预演导出结果，双层检查：**容量视图**（水平/垂直/净距三规则，指名容器）+ **几何预认证**（快照经导出同款布局定型后直跑 certify 的 R1–R4c 全规则实现，指名元素——与导出认证共用同一数学，过闸即导出第一轮认证净）。容量超限或几何相碰必须在 HTML 侧重排——减字、拆卡、降档字号、加宽列、加容器/净距，不要指望导出侧补救（认证修复环只修漂移不救结构性超限）。基线报告 `capacity-report.json` 随产物落盘，供后续翻页/导出迭代对照。

渲染校验与容量门禁均通过后【硬规则】写入全 deck 页级 hash：

```bash
python3 skills/html-pptx/scripts/extract-manifest.py <deck目录>/index.html --write-hashes
```

该命令把每页的 `data-content-hash`（SHA-256 前 12 位，算法见 `docs/design/tri-form-architecture.md` §4.3）写回 `<section class="slide">`，与产物同时交付——它是下游生图/导出 pass 的 stale 检测锚。此后编辑器每次保存会自动重算页级 hash，无需手工重跑；只有绕开编辑器直接改文件时才需要重新执行本命令。

### Step 5.5 · 插画 pass（可选，契约 v5）

入口【硬规则】：Step 5 渲染校验通过、**用户确认内容验收之后**，让用户选择图片模式——插画是内容定稿后的独立 pass，不与内容生成同步（内容改了插画作废，生图成本远高于排版）：

- **a) 纯 HTML 模式**：占位图即终态，直接进 Step 6；
- **b) AI 插画模式**：执行以下四步。

**1. 盘点槽位**：扫描全 deck 的 `data-image-slot`，产出插画清单（槽位 / 所在页 / 比例 / `data-image-intent`）。没有槽位的 deck 先按契约 v5 补齐三属性再进入。

**2. 风格规划**：写一段全 deck 统一的插画风格段（一段文字，所有槽位共享）：

- 主题声明了 G7（插画风格）时：风格段 = G7 风格描述 + 提示词种子，G7 禁忌逐条遵守；
- 主题未声明 G7 时走缺省推导（themes.md 推导规则表）：**主题色抽象图形的精细化版本**——与占位图同族，视觉连续；
- 风格段必须带入主题 token 色系（`--paper` / `--ink` / `--accent` 的具体色值与气质描述），保证全 deck 插画气质一致、与主题协调。

**3. 逐槽生图**：每个槽位的提示词 = 统一风格段 + 该槽位 intent + 比例规格。生图后端用环境中的生图技能（**oai生图**，GPT-Image-2.5），命令契约：

```bash
python <oai生图技能目录>/script.py "<统一风格段 + 槽位 intent>" \
  --aspect-ratio <比例> --resolution 2K --quality medium \
  --output-dir <deck目录>/assets --format png --n 1 --name <槽位语义名>
```

- `<oai生图技能目录>` 从环境中该技能的注册位置解析，**不硬编码机器特定的绝对路径**；
- 比例映射：槽位声明比例（如 `21x9`、`4x5`）映射到 oai生图支持的 `--aspect-ratio`（1:1 / 2:3 / 3:2 / 3:4 / 4:3 / 4:5 / 5:4 / 9:16 / 16:9 / 21:9），找最近值；
- 落盘与占位图**同名**（basename 不变，保持"替换 assets/ 同名文件即换图"的心智模型）；占位图是 SVG 而生成图是 PNG/WebP 时，同步把 img 的 `src` 扩展名改过去；
- 生成成功后把该 img 的 `data-image-state` 改为 `"generated"`。

**4. 回归校验【硬规则】**：

- 重跑 Step 5 渲染校验（图片比例不符会导致布局偏移）；
- 跑静态校验器，必须零错误：`node skills/html-pptx/scripts/check-images.mjs <deck目录>/index.html --mode illustration`；
- 反降级纪律【硬规则】：声明插画模式后，产物中不允许残留 `placeholder` 状态的槽位。**生成失败的槽位诚实回退**——保持 `placeholder` 状态与占位图，并在 Step 6 交付说明中逐条列出（回退不是失败，冒充才是：禁止用 CSS 渐变或占位图冒充插画）。

插画不改布局：尺寸即构图尺寸的纪律不变，生图只填槽位，不重排页面。

### Step 5.6 · 页面烙入 pass（可选，契约 v7 / 三形态 M2）

整页生图——把选定页整体烙成一张图，向上兼容 HTML 的表现力上限。与插画模式的边界【硬规则】：插画 = 页内槽位（文字永远在 HTML 层可编辑）；烙入 = 整页（文字烧死在图里，不可就地编辑）。不存在"背景生图 + 文字叠加"的混合态。完整规格见 `docs/design/page-render-mode.md`。

入口【硬规则】：Step 5 渲染校验通过、**用户确认内容验收之后**，用户**逐页选定**哪些页烙入（典型候选：封面、章节页、收束页等 `.cover-page` 仪式页）。不做"一键全 deck 烙入"的默认推荐——这是用户用编辑性换表现力的显式选择。

**1. 盘点与编译**：对选定页，从 manifest 提取逐字文本与槽位清单，编译生图指令：

```bash
python3 skills/html-pptx/scripts/extract-manifest.py <deck目录>/index.html --out /tmp/manifest.json
python3 skills/html-pptx/scripts/compile-bake-prompts.py /tmp/manifest.json \
  --pages <逗号分隔的 slide_id 清单> \
  --goal "<deck 主题与受众一句话>" --style "<全 deck 统一风格段>" \
  --plan <页计划 JSON> --anchor <风格锚截图文件名> \
  --out-dir <deck目录>/prompts
```

指令按规格 §4 七节模板确定性拼装（Canvas / Deck Goal / Global Style / Style Anchor / Text / Layout / Constraints）——**Text 段 100% 逐字来自 manifest，禁止转述**（防幻觉硬规则，harness 校验精确子串）；Deck Goal / 各页 Layout 来自页计划输入（`--plan` JSON 或 CLI 参数）。**分工口径【硬规则】**：脚本管确定性骨架（Text/Canvas/Constraints 的逐字与拼装），agent 管 Layout 段与风格段的写法——不同构图谱系对生图模型的指令策略不同，写 Layout 与风格段前**必须查询 `references/bake-prompts.md`**（按谱系的指令策略、文字量纪律、失败模式对策）；选页时也用其文字量标准把关（文字密布的页不该烙入）。`prompts/` 是工作区目录，不是交付物。

**2. 风格锚**：风格锚 = **真实 HTML 页的浏览器截图**（默认取封面页，用户可指定）——图片页与 HTML 页的家族相似性由同一渲染产物直接锚定，而非由另一张生图间接近似。

**3. 代表页审批闸门【硬规则】**：先烙一页代表页（默认取烙入清单中的第一页；封面在清单内时强制取封面）→ 用户确认视觉执行质量（文字准确性、材质、构图）→ 才批量。风格方向在 Step 2 主题冻结时已决，此闸门只管执行质量，不重新讨论风格。

**4. 逐页生图**：oai生图 CLI（沿用 Step 5.5 的命令契约），16:9、2K（2560×1440，卡文字清晰度与模型像素上限的平衡点）；落盘 `assets/page-<slide_id>.png`，与槽位同名心智一致。成功后改造页面为烙入结构（契约 v7）：section 加 `data-render-mode="baked"`，整页 img（`data-image-slot="page-baked-16x9"` + intent 写人可读换图指南 + `data-image-state="generated"`，满幅铺放）作为 section 直接子元素，原页面 HTML 完整收进 `<div class="baked-source" hidden>` 源层置于其后。

**5. 回归校验【硬规则】**：

- 重跑 Step 5 渲染校验（烙入页走图片分支：满幅、比例、无位移；源层 hidden 不参与溢出/重叠测量）；
- 跑静态校验器，必须零错误：`node skills/html-pptx/scripts/check-images.mjs <deck目录>/index.html --mode illustration`（v7 起识别页面级槽位 `page-baked-16x9`）；
- 烙入页 hash 重跑：`python3 skills/html-pptx/scripts/extract-manifest.py <deck目录>/index.html --write-hashes`（render_mode 进 canonical string，烙入后 hash 必须更新）；
- 反降级：声明烙入的页不允许残留 `placeholder`。**生成失败的页诚实回退为 HTML 页**（`data-render-mode` 保持 `html`，源层即页面本体——HTML 页本身就是合格交付，不交付残页），失败页在 Step 6 交付说明中逐条列出。

**stale 与重新烙入**：用户在编辑器修改烙入页源层 → hash 翻转 → 编辑器 stale 徽标 → 用户要求时重跑本 pass（仅 stale 页）。生图成本远高于排版，不自动重烙。

### Step 5.7 · 导出 pass（可选，三形态：HTML→PPTX 双轨）

单向交付快照：用户需要 .pptx/.pdf 交付时执行。规格：`docs/design/pptx-export-editable.md`（可编辑轨）+ `docs/design/pptx-export-svg.md`（保真轨）。

```bash
python3 skills/html-pptx/scripts/export-pptx.py <deck目录>/index.html [--force] [--track both|editable|vector]
python3 skills/html-pptx/scripts/export-pptx.py <deck目录>/index.html --check-stale   # 指纹过期检测
```

**双轨产物**（`--track` 缺省 both 两轨全出；任一轨基础设施失败不阻断另一轨，报告逐轨声明）：

| 产物 | 轨道 | 角色 |
|---|---|---|
| `export/deck.pptx` | **可编辑轨（主交付）** | 文本框/形状/原生 chart/信息图分组全部原生可编辑，对方接着改 |
| `export/deck-vector.pptx` | 保真轨 | 整页转曲 SVG（svgBlip+PNG 双写），视觉封存、跨机零漂移 |
| `export/deck.pdf` | 保真轨直出 | printToPDF 落盘，打印/审阅 |
| `export/page-NN.svg/png/diff.png` | 保真轨中间件 | 编辑器对比视图资产 |

**可编辑轨**（export-pptx-editable.py，编排时 import 复用）：渲染后 DOM 快照（真实包围盒/计算样式/逻辑段分行）→ L1 文本框 + L2 简单形状 + L3 原生 chart（数值文本 × 几何比例双源校验，容差 5%，不过烙图兜底绝不硬映射）+ L4 信息图 grpSp 分组 + L5 复杂视觉烙图（canvas FX/渐变/滤镜/未识别 svg，仅限装饰层——**文本永不烙图**）+ 字体内嵌（fonts/*.ttf → fntdata + embeddedFontLst，fsType 许可闸：installable/editable/preview 才嵌，受限跳过并报告列明）。**版式一致性模型（0928 F1–F4′ 数学认证口径，取代 0924 五层）**：① 字体——run typeface 写目标机必有字体（雅黑/宋体映射，WPS 可预测），fntdata 内嵌为 365 增强，fc-match 自动解析子集化（`--no-embed-fonts` 关闭）；② 行模型——单行/标题 wrap=none 永不重排 + 框宽按候选字体集最坏实测（含**混排边界 0.25em/对**，受控实验实测值）×1.08 起；多行用逻辑段 a:p（硬换行分段、软换行交 PPT 贪心重排），lnSpc 写 spcPct 相对口径 = max(作者行高/最坏自然行高, 1.03)（随字体缩放，机制免疫行内叠字），首行基线补偿；③ 松配合——框高 +1 行、顶对齐；④ **出厂门禁 = `certify-pptx.py` 数学认证【硬规则】**——写入后重开产物 XML 纯计算认证（逐行墨水宽/逐块墨水高/行距下限/墨水盒零相碰/骑缝/容器净距 ≥4px，候选字体集逐行取最坏值），违规进修复环（挪位→缩字 normAutofit→装饰烙图），页级修不净降级保真轨 svgBlip 页（manifest tracks.editable.degraded_pages 逐页列明），**终认证全过才落盘**。Step 5 容量门禁（check-capacity 几何预认证层）与本认证共用同一数学——生成侧过闸则导出第一轮认证净。**诚实边界**：不承诺像素级特效等价（glow/混合模式/canvas FX 以烙图兜底，rasterized 与 uncovered 分列）；WPS 不吃内嵌字体，WPS 用户引导保真轨交付。

**保真轨**（既有 M3 管线，参数 spike 实测固化）：防线 C 门禁（渲染校验 + 排版漂移对比，不过不产 PDF——门禁属 deck 级，阻断时两轨都不产出）→ freeze 后 printToPDF（13.333″×7.5″）→ pdftocairo 逐页转曲 SVG → PNG 副本 → svgBlip 双写组装 → postflight 重开包 → 保真分 + 差异热区。

关键口径：

- **烙入页直通**：`data-render-mode="baked"` 页（Step 5.6）跳过 PDF/SVG 转换，`assets/page-<slide_id>.png` 直接满幅嵌入——两个子技能在管线尾部汇合；
- **漂移基线**：防线 C2 需要逐叶排版快照基线，来源按优先级 = 上次 `export/manifest.json` → deck 内 `.manifest-baseline.json`。生成侧在 Step 5 渲染校验通过后【默认】落一份基线：`python3 skills/html-pptx/scripts/extract-manifest.py <deck目录>/index.html --out <deck目录>/.manifest-baseline.json`；无基线时漂移检测诚实降级（报告声明未生效），本次快照自动成为下次基线；
- **降级链**：pdftocairo 不可用或某页转换失败 → 该页 3840×2160 高分辨率截图单独成页（png-fallback），导出报告逐页列明降级原因；截图设施也不可用 → 非零退出，不产半成品；
- **单向纪律**【硬规则】：导出全程对 index.html 只读（前后字节校验），PPTX 永不回读；重导 = 重新翻转（--force），旧 pptx 作废；
- **stale**：编辑器保存会翻转页级 hash——`--check-stale` 检出指纹过期页（导出 hash ≠ 当前 hash），过期即重导；
- **字体防线 A**（可选）：`subset-fonts.py`（`--format auto|woff2|ttf`）按全 deck 实际用字子集化字体 → `fonts/*.woff2`（HTML 侧，可注入骨架 SLOT: fonts @font-face 块）与 `fonts/*.ttf`（pptx fntdata 内嵌的唯一形态，可编辑轨自动嵌入）；未覆盖字形会在 export/manifest.json 的 uncovered_glyphs 中列出。

交付说明口径（追加到 Step 6）：逐轨声明——可编辑轨 native 覆盖率/烙图数/uncovered/字体随档状态；保真轨每页载体（svg / png-fallback / baked）、全 deck 平均保真分、降级页与原因。可编辑轨不承诺像素级特效等价；保真轨 Office 2016+/365 显示矢量 SVG 且可"转换为形状"微调，更老版本及 WPS 走 PNG 位图。

### Step 6 · 交付

交付时说明三件事：

1. 如何演示：浏览器打开 `index.html`，滚动或方向键翻页；
2. 如何编辑：用编辑器页面打开它，文字直接点改，图片点击替换；
3. 如何换图（不用编辑器时）：直接替换 `assets/` 里的同名文件。

若走了 Step 5.5 插画模式，交付说明追加三件事：

1. 哪些槽位已生图（`data-image-state="generated"`）及各自的风格段执行要点；
2. 哪些槽位生成失败、诚实回退为占位图（保持 `placeholder`），附失败原因；
3. 如何替换任一插画：编辑器上传，或直接替换 `assets/` 同名文件（槽位 intent 就是换图指南）。

若走了 Step 5.6 页面烙入模式，交付说明再追加三件事：

1. **诚实声明哪些页已烙入**（`data-render-mode="baked"` 页清单）——这些页的文字烧死在图里，不再可就地编辑，改文字需走"源层编辑 + 重新烙入"流程；
2. 哪些页生图失败、诚实回退为 HTML 页（`data-render-mode` 保持 `html`），附失败原因；
3. 如何替换烙入页的整页图：编辑器上传（整页 img 走既有换图流），或直接替换 `assets/page-<slide_id>.png` 同名文件。

## 可编辑标记契约（摘要）

【硬规则】产物必须携带以下标记，编辑器页面按同一契约实现：

- 每页：`<section class="slide" data-slide-id="cover">`——稳定语义 ID，禁止用页码；
- 可编辑文字：`data-editable`；
- 可替换图片：`data-editable-image`，`src` 必须是指向 `assets/` 的相对路径；图位必须带槽位三属性 `data-image-slot` / `data-image-intent` / `data-image-state`（契约 v5）；
- 纯装饰元素：`data-editable-skip`。

完整约定（含 ID 命名规则、编辑器行为约定、序列化规则）见 `references/editing-contract.md`。生成前必读。

## 图片纪律

- 【硬规则】一律引用 `assets/` 相对路径（如 `assets/hero-team.jpg`），禁止 base64 内嵌、禁止外链图床。
- 【硬规则】每个 `data-editable-image` 图位必须写全槽位三属性（契约 v5）：`data-image-slot`（语义名-宽x高，声明比例与构图宽高比一致，容差 5%）、`data-image-intent`（内容意图一句话）、`data-image-state`（占位图阶段为 `"placeholder"`）。
- 占位图规格：尺寸即构图尺寸（占多大就生成多大）；文件名语义化（`chart-q3-growth.svg`，不是 `img1.png`）；视觉用**主题色的抽象图形**（几何块/网格/线条，从主题 token 取色），不要灰底叉线图；SVG 优先（矢量、可被文本检查）。
- 占位图是交付物的一部分：用户拿到后替换 `assets/` 同名文件即换图，占位图的构图与 intent 就是换图指南。
- pptx 转换入口：提取的原图原样落盘 `assets/`，按画面角色补 `data-image-slot` 与 `data-image-intent`，并置 `data-image-state="uploaded"`（用户提供的真图，视同上传）。
- 内容验收后用户选择"AI 插画模式"时，走 Step 5.5 统一补齐插画（占位 → generated 的批量升级）。

## 质量红线速查（全是硬规则）

- 画布 1920×1080，`transform` 整体缩放，禁止响应式重排；
- 骨架框架层不改一字；
- 可编辑标记不省略；
- 数据真实性：没有真实量化数据就不用量化组件，禁止编造数字；
- 正文 ≥ 18px（画布坐标）；
- 图片走 `assets/`，不内嵌、不外链；
- `prefers-reduced-motion` 下所有动效消失且内容完整可读；
- 打印时每页输出为独立一页。

## 参考文件加载纪律

上下文是稀缺资源。按需加载，禁止批量预读：

- `assets/skeleton.html`——Step 3 时读，逐字复制；
- `references/briefing.md`——Step 0.5 时读（需求脑暴问题组与简报格式）；
- `references/themes.md`——Step 2 时读，选定后只取该主题的 token 块（含所选变体）与 G9 母题 css 块；
- `references/typography.md`——Step 1 定密度、Step 4 定字号字数时读；
- `references/components.md`——Step 4 需要信息图组件时读;
- `references/motifs.md`——Step 1 填呈现发散列、Step 4 关键页落码时读；
- `gallery/index.html`——Step 4 落码信息图页时翻对应族×皮肤的实例页抄丰富度；
- `references/charts.md`——Step 4 需要图表时读；
- `references/motion.md`——Step 4 安排动效时读；
- `references/bake-prompts.md`——Step 5.6 选页把关与写 Layout/风格段前读；
- `references/editing-contract.md`——Step 4 前读一次。

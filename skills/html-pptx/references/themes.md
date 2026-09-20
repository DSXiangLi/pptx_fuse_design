# 主题库（Themes）

策展的主题预设。**只选不改**：选定主题与变体后，整套 token 复制进骨架的 `SLOT: theme tokens`、主题 CSS 块复制进 `SLOT: theme css`，禁止混搭、禁止自定义色值——色彩搭配错了画面瞬间变丑，保护审美比给自由更重要。

字体栈默认走系统字体（离线可用）；用户明确接受联网加载时，可自行替换为 Web 字体。

**两级架构**：本库的单位是**重主题**（七层表达力栈齐备的完整世界），每个重主题带 ≥3 套**配色变体**（同一世界的不同光线/时辰/材质演绎）。变体不是另一个主题——只在 L1 色彩（必要时 L3 质感）上分化，其余五层与基底共享。来源标注：`A` = 归藏电子杂志风，`B` = 归藏瑞士国际主义，`C` = frontend-slides 策展预设，`D` = 主题 Schema 化迭代新增的候选方向。

## Schema：七层表达力栈（L1–L7 ↔ G0–G9）

主题 ≠ 配色方案。主题是一个**七层表达力栈**，每层都要有主权。**两个主题在七层里至少 3 层实质分化，才算两个主题**（入库机器门槛，校验器强制执行两两 diff）。规范全文见 `docs/design/theme-schema.md` 与 `docs/design/theme-expression-stack.md`。

| 层 | 内容 | 字段组 | 必填 |
|---|---|---|---|
| — | 身份：id、名称、气质一句话、适用场景、focus 声明、**世界参考**、**unforgettable**、**分化声明** | G0 identity | ✅ |
| L1 色彩系统 | paper / paper-tint / ink / ink-tint / accent / accent-on + **accent 用量预算**（内容页面积上限 / 满屏特权页 / 首尾色彩闭环） | G1 color | ✅ |
| L2 字体性格 | font-display / font-body / font-mono、字重倾向、**字号对比档**、**字重映射**、标题修饰 | G2 typography | ✅ |
| L3 质感层 | 材质类型 + 实现 token（叠加层规格、强度、范围）——**立场必填**：flat 也要显式写出（"flat 即质感立场"） | G3 texture | ✅（立场） |
| L5 容器风格 | 圆角策略、hairline/分割线风格、阴影策略、**容器造型语言**（直角纯色/圆角弥散/描边窗口/玻璃/撕边……） | G4 shape | 可选 |
| L6 动效签名 | 气质六选 + 强度上限 + 禁用 recipe + **锚点偏好** + **节奏偏移** + **缓动签名** + **fx 许可**（canvas 仪式层白名单，缺省全禁；见 `motion.md` §4/§6） | G5 motion | 可选 |
| L7 构图倾向 | 特别适合 / 禁止的信息图结构族与组件 + **谱系偏好与禁忌**（构图谱系见 `components.md` §11） | G8 component | 可选 |
| L4 装饰母题 | 主题自己的装饰词汇（**不是全都用 + 号和 hairline**：risograph 用套色错位、蓝图用标注引线、终端用 ASCII 框……）+ 主题自带 CSS 块 | G9 motif | 可选 |

**focus 声明**：每主题在 G0 声明 1–2 个字段组为 focus——focus 是该主题设计感的来源。focus 组的字段必须全部显式给出；非 focus 组要么显式给出、要么走缺省推导，两者都合法。

**G0 三个新必填字段**（G 期起）：

- **世界参考**：一句话说清这个主题从哪个世界采样翻译而来（"1950 年代瑞士铁路时刻表"）。主题不是配出来的，是从世界里采样翻译出来的；
- **unforgettable**：这套主题让人记住的那一个东西是什么（"时刻表翻牌"）——答不上来就不立项；
- **分化声明**：与最近邻主题实质分化的层（≥3 层，格式 `与 <id> 分化于 Lx/Ly/Lz：一句话`）——校验器逐层核验声明为真。

**accent 用量预算**（高级感要素 1，归藏实测口径）：双色墨水 + 单一锚点色，accent 是预算制资源——内容页 accent 面积 ≤10%（单页至多一个视觉重心）；满屏 accent 是封面/收束页的特权；首（全亮）尾（半亮或条带）色彩闭环。每主题在 G1 写明自己的预算口径（A 系 accent==ink 时"满屏 accent"体现为暗色反白页）。

**字号对比档与字重映射**（高级感要素 2/3）：每主题在 G2 写明主标题:正文目标比（瑞士系无衬线 ≥8:1，规则见 `typography.md` §5）与字重映射表（照 `typography.md` §3 归藏口径；衬线 display / 极粗标题等例外立场必须在映射表里显式声明）。

**G9 motif 装饰母题**（G 期新增）：母题 = 主题独有的装饰词汇清单 + 一段主题自带 CSS 块（生成侧逐字复制进骨架 `SLOT: theme css`）。CSS 块纪律（校验器强制）：

- 只允许三类规则：① `:root{}` token 重定义（缓动签名等）；② `.mt-*` 前缀的母题类（命名空间防碰撞，**类名全库唯一**，跨主题不得重名）；③ `.mt-*` 的伪元素/后代装饰；
- 颜色只许 `var(--*)` / `color-mix()` 引用 token，禁字面 hex（色彩主权在 G1）；禁外部 `url()`（同 G3 纪律，只许 data: 内联）；禁覆盖框架选择器（`.slide`/`.masthead` 等）；
- 母题件在产物中是装饰，一律带 `data-editable-skip`（契约 v6.2）；每主题母题 CSS ≤40 行，无母题的主题留空合法。

**Variants 配色变体**（G 期新增）：主题条目末尾 `**Variants 配色变体**` 小节，每个变体一个 `####` 子标题。变体字段集定死：**变体名 + 一句话气质 + G1 六色 token（必填）+ 可选 G3 三 token 覆盖 + 可选 accent 预算注记**；变体不得覆盖 G2/G4/G5/G8/G9（字体/形态/动效/构图/母题与基底共享，否则它就是另一个主题）。门槛：**每主题配色套数 = 基底 + 变体 ≥ 3**。

### 缺省推导规则（集中维护，只此一份）

可选字段组缺省时按下表推导，**不允许"留空且无规则"**：

| 缺省组 | 推导规则 |
|---|---|
| G3 texture | flat（平色，无叠加层）——推导仅供草稿阶段；入库主题必须显式写出立场（含 flat），校验器强制执行 |
| G4 shape | 按系列默认：A/B 系 radius=0、无阴影；C/D 系 radius ≤8px |
| G5 motion | 全局默认气质（professional）+ 无禁用 + 节奏/缓动不偏移 + fx 全禁（canvas 仪式层默认关，主题显式声明才可用） |
| G6 chart | 统一 color-mix 推导（见文末"图表 token"节） |
| G7 illustration | 主题色抽象图形（即占位图风格，等价于"纯 HTML 模式"） |
| G8 component | 无特别亲和，全组件可用 |
| G9 motif | 无母题——主题 CSS 块留空（合法；focus 声明 G9 时必填） |

### G3 texture 的落地状态（skeleton v4 起生效）

骨架 v4 实行**背景配给制**（高级感要素 7）：`.slide::before` 质感层默认不渲染，只铺两类页面——

- **仪式页**：封面/章节/封底，由生成侧标 `cover-page` class，自动铺质感层；
- **正文页**：默认纯色。要铺质感必须生成侧**逐页显式加 `texture-on` class**（纪律见 `motion.md` §4 使用规则）。

`--texture-scope` 是主题级的**许可声明**，不再驱动自动行为：`cover` = 只许仪式页（缺省立场）；`all` = 本主题允许正文页铺质感（纸纹/颗粒等材质型主题），但仍需生成侧逐页 `.texture-on` 落码，骨架不自动全铺。主题不给质感（flat）时该层为 `none`，零成本。

手绘类质感（rough 边框、不规则填充）作用于组件层，在 G8 中声明亲和的结构族，由生成侧按配方落码。

---

## A 系 · 电子杂志 × 电子墨水

A 系的灵魂：衬线大标题 + 大留白 + 无阴影无卡片，靠字号与字体对比建立层级。`--accent` 默认等于 `--ink`——强调靠字重和字号，不靠颜色。

### A1 电子杂志（默认）

- **id**：a1
- **气质**：纯墨黑 + 暖米白，杂志感最强
- **适用**：通用分享、商业发布、任何场景的安全选择
- **focus**：G2 + G9
- **世界参考**：归藏"电子杂志 × 电子墨水"——双色墨水、纸面留白、衬线标题的编辑部排版
- **unforgettable**：Ghost 残影巨字——超大低透明描边字作页面背景层，翻页即杂志封面感
- **分化声明**：与 c4 分化于 L2/L4/L6——a1 正文无衬线、母题是 Ghost 巨字与竖排题字条、锚点动效是 mask-lines 逐行显影；c4 全衬线、母题是题花与首字下沉、锚点是 draw-line

**G1 color**

```css
--paper:#f1efea; --paper-tint:#e8e5de;
--ink:#0a0a0b;   --ink-tint:#18181a;
--accent:#0a0a0b; --accent-on:#f1efea;
```

- **accent 预算**：accent 与 ink 同色——"满屏 accent"体现为暗色反白页（`.slide.dark`），是封面/收束的特权；内容页不追求 accent 面积指标，强调靠字重与字号。首尾闭环：暗色封面（全亮墨色）开场 → 收束页暗色反白呼应（可半亮：ink 底 + paper 细条带）。

**G2 typography**

```css
--font-display:"Songti SC","Noto Serif SC","STSong",serif;
--font-body:"PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

- **字重倾向**：标题 600–700、正文 400；强调靠字重与字号，不靠颜色（accent==ink）
- **字号对比**：主标题:正文 ≥8:1（低密度）；高密度 ≥5:1——衬线 display 靠字号差建层级
- **字重映射**：衬线恒重立场（不走倒挂——细衬线大字号发虚）：≥77px→600（封面/收束可 700）；35–76px→600；正文 400；14–16px 小字 500–600
- **标题修饰**：无

**G3 texture**

```css
--texture-type: glow;
--texture-layer: radial-gradient(75% 55% at 80% 10%, color-mix(in srgb, var(--ink) 6%, transparent), transparent 65%);
--texture-scope: cover;
```

- **立场**：墨韵——仪式页一角淡墨晕染，正文页纯纸面

**G4 shape**

- **圆角**：0
- **hairline**：1px solid color-mix(in srgb, var(--ink) 18%, transparent)，只在层级边界出现
- **阴影**：无
- **容器造型**：无卡片立场——靠留白与 hairline 分区；底色块只用 paper-tint 灰档（灰底低对比，靠空气不靠边界），直角纯色，禁渐变、禁阴影、禁描边卡片

**G5 motion**

- **气质**：editorial
- **强度上限**：默认
- **锚点偏好**：封面/章节 mask-lines 逐行显影或 chars；数据页 draw-line；数字以字号对比直排为主，count-up 只给真正的 KPI 英雄页
- **节奏偏移**：时长档 +1（一切比默认慢半拍，显影感）；阶梯步长 ≥90ms
- **缓动签名**：默认三 token，不覆盖
- **禁用**：scale-pop / persp-in（弹跳与透视翻转破坏纸面安静）
- **fx 许可**：仅 ascii-field（字符呼吸场可破格；粒子类禁）

**G8 component**

- **亲和**：巨字宣言、图文证据、轴与节点（时间轴/演进）
- **禁忌**：禁连续两页网格矩阵——杂志节奏靠疏密对比，不靠格子堆叠；不用加号角标与网格点阵（那是瑞士系词汇）

**G9 motif**

- **词汇**：Ghost 残影巨字（页面背景层，与内容相关的单字/关键词，低透明描边，每页至多一个、只作背景不抢焦）/ 竖排题字条（封面与章节页侧缘竖排 mono 拉丁或拼音）/ 墨点角标（5px 实心方点替代图标，标记列表项或编号）

```css
/* A1 电子杂志 · 装饰母题 */
.mt-ghost{position:absolute;z-index:0;pointer-events:none;user-select:none;font-family:var(--font-display);font-weight:600;line-height:1;color:transparent;-webkit-text-stroke:1px color-mix(in srgb,var(--ink) 22%,transparent)}
.mt-vquote{writing-mode:vertical-rl;font-family:var(--font-mono);font-size:13px;letter-spacing:.35em;opacity:.5;pointer-events:none}
.mt-dot{display:inline-block;width:5px;height:5px;background:var(--ink)}
```

- **禁忌**：Ghost 字禁与标题同区抢焦、禁内容页连用超过两页；母题件一律 `data-editable-skip`

**Variants 配色变体**

#### 靛蓝瓷

- **气质**：深靛蓝 + 瓷白，冷静理性，像学术期刊——科技/研究/数据分享、工程师文化

```css
--paper:#f1f3f5; --paper-tint:#e4e8ec;
--ink:#0a1f3d;   --ink-tint:#152a4a;
--accent:#0a1f3d; --accent-on:#f1f3f5;
--texture-layer: radial-gradient(85% 60% at 18% 0%, color-mix(in srgb, var(--ink) 5%, transparent), transparent 62%);
```

#### 森林墨

- **气质**：深森林绿 + 象牙，沉稳有呼吸感——自然/可持续/文化/非虚构内容

```css
--paper:#f5f1e8; --paper-tint:#ece7da;
--ink:#1a2e1f;   --ink-tint:#253d2c;
--accent:#1a2e1f; --accent-on:#f5f1e8;
--texture-type: grain;
--texture-layer: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='240' height='240'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='240' height='240' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E"), radial-gradient(70% 60% at 75% 85%, color-mix(in srgb, var(--ink) 5%, transparent), transparent 65%);
```

#### 沙丘

- **气质**：炭灰 + 沙色，克制高级，像建筑设计图册——艺术/设计/创意/时尚

```css
--paper:#f0e6d2; --paper-tint:#e3d7bf;
--ink:#1f1a14;   --ink-tint:#2d2620;
--accent:#1f1a14; --accent-on:#f0e6d2;
--texture-type: grain;
--texture-layer: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='240' height='240'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='240' height='240' filter='url(%23n)' opacity='0.05'/%3E%3C/svg%3E"), radial-gradient(80% 65% at 70% 90%, color-mix(in srgb, var(--accent) 4%, transparent), transparent 65%);
```

#### 牛皮纸

- **气质**：深棕 + 暖米，像牛皮信封，温暖有年代感——怀旧/人文/阅读/历史/文学分享

```css
--paper:#eedfc7; --paper-tint:#e0d0b6;
--ink:#2a1e13;   --ink-tint:#3a2a1d;
--accent:#2a1e13; --accent-on:#eedfc7;
--texture-type: paper;
--texture-layer: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='240' height='240'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='240' height='240' filter='url(%23n)' opacity='0.06'/%3E%3C/svg%3E"), repeating-linear-gradient(0deg, color-mix(in srgb, var(--ink) 2%, transparent) 0 1px, transparent 1px 5px), radial-gradient(90% 70% at 30% 15%, color-mix(in srgb, var(--ink) 5%, transparent), transparent 60%);
--texture-scope: all;
```

---

## B 系 · 瑞士国际主义

B 系的灵魂：高级灰白底 + **单一**高饱和高亮色 + 1px 极细分割线（hairline）+ 网格。高亮色是手术刀，点到为止——一旦泛滥就掉档。加号角标与网格点阵是 B 系的专属词汇，其他主题禁用。

### B1 瑞士国际主义

- **id**：b1
- **气质**：最经典的瑞士配色，绝不出错
- **适用**：通用场合、商业发布、AI/科技、设计领域
- **focus**：G1 + G9
- **世界参考**：1960 年代瑞士国际主义海报（Müller-Brockmann 网格体系）+ 瑞士铁路 signage 的加号与网格纪律
- **unforgettable**：加号角标 + 网格点阵——页面四角的细十字与版心网格，一眼瑞士
- **分化声明**：与 a1 分化于 L1/L2/L4/L5/L6——accent 是独立高亮色（非 ink）、无衬线倒挂字重、母题是加号/点阵/色块编号而非 Ghost 字、容器是直角色块而非无卡片、动效锐利短促而非慢显影

**G1 color**

```css
--paper:#fafaf8; --paper-tint:#f0f0ee;
--ink:#0a0a0a;   --ink-tint:#1a1a1a;
--accent:#002FA7; --accent-on:#ffffff;
```

- **高亮纪律**：accent 单页至多出现在一个视觉重心上
- **accent 预算**：内容页 accent 面积 ≤10%（与高亮纪律同口径）；满屏 accent 是封面/收束特权（归藏式 IKB 满版蓝 + 反白巨字）。首尾闭环：满版 IKB 封面（全亮）开场 → 收束页半亮呼应（IKB 通栏条带，或蓝底降明度 + 纸白文字）。

**G2 typography**

```css
--font-display:"Helvetica Neue","PingFang SC","Noto Sans SC",sans-serif;
--font-body:"Helvetica Neue","PingFang SC","Noto Sans SC",sans-serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

- **字重倾向**：越大越细（大标题 200–300），越小越粗（正文/标签 500–700）
- **字号对比**：主标题:正文 ≥8:1（瑞士立场，巨字双约束 `min(Xvw, Yvh)` 限高）；高密度 ≥5:1
- **字重映射**：归藏倒挂阶梯：≥154px（≥8vw）→200；77–153px→200–300；35–76px→300–400；17–34px→400–500；14–16px→500–600；同页小字字重 ≥ 大字
- **标题修饰**：无

**G3 texture**

```css
--texture-type: flat;
--texture-layer: none;
--texture-scope: cover;
```

- **立场**：flat 即质感立场——瑞士版面靠纸白、网格与 hairline 建立秩序，任何纹理都是噪声

**G4 shape**

- **圆角**：0
- **hairline**：1px solid color-mix(in srgb, var(--ink) 18%, transparent)，配网格使用
- **阴影**：无
- **容器造型**：直角纯色块（四档明度照 §12）；编号用 accent 实心方块白字（单焦点纪律内）；描边框仅用于图表区，1px hairline

**G5 motion**

- **气质**：professional
- **强度上限**：默认
- **锚点偏好**：wipe-clip 精确揭示（标题/色块）+ count-up（数据页）——瑞士的动效是"对齐到网格的精确位移"，不是显影
- **节奏偏移**：时长档 −1（短促）；阶梯步长 ≤60ms
- **缓动签名**：覆盖 `--ease-out` 为更锐利的 cubic-bezier(.2,.9,.25,1)——快出急停
- **禁用**：blur-in / persp-in / mask-lines（模糊与柔缓不属于网格纪律）
- **fx 许可**：仅 ascii-field（归藏 IKB 封面字符呼吸场的正当先例；粒子类禁）

**G8 component**

- **亲和**：网格矩阵、数据英雄（图表/数字）、裂屏对开（双色对撞）
- **禁忌**：不用 Ghost 残影字（那是杂志系词汇）；轴与节点的时间轴必须严格水平或垂直，禁斜线引导

**G9 motif**

- **词汇**：加号角标（页面四角或内容区角上的细十字，14px，低透明，每页 ≤4 个）/ 网格点阵（封面或收束页背景，24px 点距）/ 色块编号（accent 实心方块 + 反白 mono 编号，替代圆点列表）

```css
/* B1 瑞士国际主义 · 装饰母题 + 缓动签名 */
:root{--ease-out:cubic-bezier(.2,.9,.25,1)}
.mt-cross{position:absolute;width:14px;height:14px;pointer-events:none;opacity:.55}
.mt-cross::before,.mt-cross::after{content:"";position:absolute;background:var(--ink)}
.mt-cross::before{left:50%;top:0;bottom:0;width:1px;margin-left:-.5px}
.mt-cross::after{top:50%;left:0;right:0;height:1px;margin-top:-.5px}
.mt-grid-dots{position:absolute;inset:0;pointer-events:none;background-image:radial-gradient(color-mix(in srgb,var(--ink) 18%,transparent) 1px,transparent 1.5px);background-size:24px 24px}
.mt-swatch{display:inline-flex;align-items:center;justify-content:center;min-width:2.2em;height:2.2em;background:var(--accent);color:var(--accent-on);font-family:var(--font-mono);font-weight:600}
```

- **禁忌**：加号只许四角与内容区角点，禁撒在页面中部；网格点阵只许仪式页；母题件一律 `data-editable-skip`

**Variants 配色变体**

#### 柠檬黄

- **气质**：浅色高亮，活力直接——年轻、运动、零售、消费品

```css
--paper:#fafaf8; --paper-tint:#f0f0ee;
--ink:#0a0a0a;   --ink-tint:#1a1a1a;
--accent:#FFD500; --accent-on:#0a0a0a;
```

#### 柠檬绿

- **气质**：荧光感高亮，适合屏幕与投影——生态、可持续、健康、新兴科技、Z 世代品牌

```css
--paper:#fafaf8; --paper-tint:#f0f0ee;
--ink:#0a0a0a;   --ink-tint:#1a1a1a;
--accent:#C5E803; --accent-on:#0a0a0a;
```

- **accent 预算**：荧光绿满版仅封面，投影场景慎用；其余同基底口径

#### 安全橙

- **气质**：工业感高亮，警告/转折/重点专用——工业、运动、技术发布会的"警告/转折/重点"页

```css
--paper:#fafaf8; --paper-tint:#f0f0ee;
--ink:#0a0a0a;   --ink-tint:#1a1a1a;
--accent:#FF6B35; --accent-on:#ffffff;
```

- **accent 预算**：**不满屏**——满版橙过于刺眼，封面/收束的特权形态是橙色通栏条带（高度 ≤20%）；首尾闭环为同位条带呼应

---

## C 系 · 深色与个性（源自 frontend-slides）

C 系补充暗色与强个性方向。暗色主题中 `.slide.dark` 变体的角色反转：默认页即暗页。

### C1 信号黑

- **id**：c1
- **气质**：纯黑舞台 + 一束信号橙，keynote 发布的压强美学
- **适用**：产品发布、主题演讲、数据宣言、需要冲击力与记忆点的场合
- **focus**：G1 + G5
- **世界参考**：keynote 发布舞台与信号弹美学——黑场、追光、单束高饱和信号色
- **unforgettable**：信号橙色块 + 极粗巨字——黑场上唯一的橙色块就是全场焦点
- **分化声明**：与 c3 分化于 L2/L3/L4/L5/L6——c1 是极粗无衬线 + flat 平色 + 信号条/巨号页码母题 + 直角色块容器 + scale-pop 硬切签名；c3 是全栈等宽 + CRT 扫描线 + ASCII 框/光标母题 + 描边终端窗口 + typewriter/scramble 签名

**G1 color**

```css
--paper:#1a1a1a; --paper-tint:#242424;
--ink:#ffffff;   --ink-tint:#0f0f0f;
--accent:#FF5722; --accent-on:#1a1a1a;
```

- **accent 预算**：内容页 accent 面积 ≤10%（信号橙色块单焦点——单页至多一个橙色块）；满屏 accent 仅封面/收束特权；首尾闭环：封面信号橙色块 + 巨字开场 → 收束页橙色块（半亮或缩小）呼应。

**G2 typography**

```css
--font-display:"Arial Black","PingFang SC","Noto Sans SC",sans-serif;
--font-body:"PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

- **字重倾向**：标题极粗 800–900、正文 400；层级靠色块与字重压强
- **字号对比**：主标题:正文 ≥8:1（低密度）；巨字特档 10:1（封面宣言页）；高密度 ≥5:1
- **字重映射**：反向立场（不走倒挂——极粗无衬线大字即压强）：标题恒重 800–900（≥35px 全档）；正文 400；14–16px 小字 500–600
- **标题修饰**：无

**G3 texture**

```css
--texture-type: flat;
--texture-layer: none;
--texture-scope: cover;
```

- **立场**：flat 即质感立场——高冲击靠色块与字重压强，纹理只会削弱信号

**G4 shape**

- **圆角**：0
- **hairline**：不用——分区靠色块明度差与留白，不靠线
- **阴影**：无
- **容器造型**：大色块直角立场——accent / paper-tint / ink-tint 明度档纯色块承载内容，禁描边卡、禁渐变、禁阴影；accent 色块单页至多一个（与单焦点纪律同口径）

**G5 motion**

- **气质**：dramatic
- **强度上限**：默认
- **锚点偏好**：scale-pop（巨字与色块压入，配缓动签名的过冲回弹）+ wipe-clip 硬切揭示；封面 chars 逐字砸落；count-up 只给真正的 KPI 英雄数字
- **节奏偏移**：时长档 −1（短促有力）；阶梯步长 ≤60ms
- **缓动签名**：覆盖 `--ease-out` 为 cubic-bezier(.2,1.25,.3,1)——带过冲的爆发曲线，色块砸落有回弹
- **禁用**：blur-in / mask-lines / gradient-flow（柔化手段削弱信号冲击）
- **fx 许可**：constellation / starfield / particle-drift（ascii-field 禁——终端字符感与信号黑不搭）

**G8 component**

- **亲和**：巨字宣言、数据英雄（大数字直压）、裂屏对开（黑橙对撞）
- **禁忌**：禁连续两页网格矩阵——碎格子稀释压强；不用加号角标/网格点阵（瑞士系词汇）与 ASCII 字符装饰（终端系词汇）

**G9 motif**

- **词汇**：信号条（accent 粗短条，标题区/页眉的"信号"标记，每页至多一个）/ 巨号页码（超大极粗低透明数字，页面底缘背景层，只作背景不抢焦）/ 信号方块（小实心 accent 方块，替代圆点的列表/编号标记）

```css
/* C1 信号黑 · 装饰母题 + 缓动签名 */
:root{--ease-out:cubic-bezier(.2,1.25,.3,1)}
.mt-sig-bar{display:block;width:64px;height:10px;background:var(--accent)}
.mt-sig-folio{position:absolute;right:2%;bottom:-.16em;z-index:0;pointer-events:none;user-select:none;font-family:var(--font-display);font-weight:900;font-size:30vh;line-height:.8;color:color-mix(in srgb,var(--ink) 7%,transparent)}
.mt-sig-mark{display:inline-block;width:.55em;height:.55em;background:var(--accent)}
```

- **禁忌**：信号条每页至多一个、只许标题区/页眉；巨号页码只作背景层、禁与标题同区抢焦；信号方块只在列表/编号位，禁当装饰撒布；母题件一律 `data-editable-skip`

**Variants 配色变体**

#### 赛博青

- **气质**：冷调电子信号，赛博感——开发者产品、数据平台、AI 基础设施发布

```css
--paper:#1a1a1a; --paper-tint:#242424;
--ink:#ffffff;   --ink-tint:#0f0f0f;
--accent:#00E5FF; --accent-on:#1a1a1a;
```

#### 警报红

- **气质**：警报/故障/转折，紧迫感——风险披露、安全主题、发布会的"问题"章节

```css
--paper:#1a1a1a; --paper-tint:#242424;
--ink:#ffffff;   --ink-tint:#0f0f0f;
--accent:#FF2D40; --accent-on:#ffffff;
```

- **accent 预算**：满版红仅封面（冲击力极强，连用两页即疲劳）；收束页用半亮红色块呼应；其余同基底口径

### C2 暗夜植物园

- **id**：c2
- **气质**：暗夜纸面上浮一层暖金灯光，像翻开一本 19 世纪植物图鉴——沉静、精确、有学术温度
- **适用**：自然/博物/文化/人文类分享，研究型叙事，慢节奏深度内容
- **focus**：G3 + G9
- **世界参考**：19 世纪植物学版画图鉴与标本签——夜观植物园里的标本线描、拉丁学名斜体标注、图鉴编号签条
- **unforgettable**：标本引线标注 + 图鉴编号签——细线引线把标本图与图注缝在一起，mono 小签条像标本柜抽屉上的标签
- **分化声明**：与 d2 分化于 L1/L2/L4/L5/L6——c2 暖金暗哑、d2 琥珀更亮更橙；c2 标题 500–600 恒重、d2 标题 400–500 偏细且带斜体强调；c2 母题是标本引线/编号签/叶脉分叉线、d2 是胶片齿孔/光束角标/显影晕；c2 容器是 1px 细描边直角图鉴卡、d2 无框禁描边只用辉光托底；c2 签名动效是 draw-line 叶脉生长、d2 是 blur-in 显影浮出配更慢缓动（L3 两者同为 glow/cover，不计入分化——拉开靠的是 L4/L5/L6）

**G1 color**

```css
--paper:#0f0f0f; --paper-tint:#1a1816;
--ink:#e8e4df;   --ink-tint:#2a2724;
--accent:#d4a574; --accent-on:#0f0f0f;
```

- **accent 预算**：内容页 accent 面积 ≤5%（暖金只做点睛：引线端点、编号签方块、关键数字）；满屏 accent 不适用——暗夜仪式感靠辉光不靠满色；首尾闭环：封面右上辉光开场 → 收束页同位辉光呼应（可略强）。

**G2 typography**

```css
--font-display:"Songti SC","Noto Serif SC","STSong",serif;
--font-body:"PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

- **字重倾向**：标题 500–600、正文 400——克制不张扬，图鉴的权威感来自排布而非字重
- **字号对比**：主标题:正文 ≥8:1（低密度）；高密度 ≥5:1
- **字重映射**：衬线恒重立场（不走倒挂）：≥77px→500–600；35–76px→500–600；正文 400；14–16px 小字 500
- **标题修饰**：无（斜体只属于拉丁学名标注 `.mt-bot-latin`，不进标题）

**G3 texture**

```css
--texture-type: glow;
--texture-layer: radial-gradient(90% 70% at 78% 8%, color-mix(in srgb, var(--accent) 10%, transparent), transparent 60%);
--texture-scope: cover;
```

- **立场**：glow——仪式页右上角一团暖金辉光，如温室夜灯悬在图鉴上方；正文页纯暗夜纸面

**G4 shape**

- **圆角**：0（标本柜的秩序，图鉴卡一律直角）
- **hairline**：1px solid color-mix(in srgb, var(--ink) 30%, transparent)，承担图鉴卡描边与引线——线在这个主题里是标注工具，不是装饰
- **阴影**：无
- **容器造型**：图鉴卡——直角 1px 细描边 + 左上角钉编号签条（`.mt-bot-plate` + `.mt-bot-tag` 落码），卡内按图鉴版式排（图在上、拉丁名与引线注在下）；禁圆角、禁玻璃、禁弥散投影、禁满版色块

**G5 motion**

- **气质**：calm
- **强度上限**：低
- **锚点偏好**：draw-line 为签名锚点——图鉴引线与叶脉描线的生长感，图注页/数据页优先；标题入场用默认阶梯或 rise-in，克制
- **节奏偏移**：时长档 +1（一切比默认慢，夜观的呼吸）；阶梯步长 ≥90ms
- **缓动签名**：默认三 token，不覆盖
- **禁用**：无（calm 气质本身排除弹跳与硬切）
- **fx 许可**：仅 particle-drift（夜尘/孢子浮动；starfield 太"天文"、constellation 连线太硬，均不属于植物园）

**G8 component**

- **亲和**：图文证据（标本图 + 引线图注，本主题的原生版式）、轴与节点（分类树/谱系——叶脉分叉与分类学同构）
- **禁忌**：禁裂屏对开大色块对撞（图鉴没有满版撞色）；网格矩阵仅用于标本陈列式多图页，连用不超过两页

**G9 motif**

- **词汇**：标本引线标注（`.mt-bot-lead`：accent 空心圆点 + 1px 渐隐细引线 + mono 小注，把图与图注缝在一起，每页 ≤2 条）/ 图鉴编号签（`.mt-bot-tag`：1px 描边 mono 小签条带 accent 方块点，"No.04 / Pl.XII"，钉在图鉴卡左上角或页面角）/ 拉丁学名斜体（`.mt-bot-latin`：衬线 italic 小注，图鉴的学术签名）/ 叶脉分叉细线（`.mt-bot-vein`：羽状分叉 hairline 条带，只许页面侧缘低透明装饰）

```css
/* C2 暗夜植物园 · 装饰母题 */
.mt-bot-tag{display:inline-flex;align-items:center;gap:.7em;padding:.3em .9em;border:1px solid color-mix(in srgb,var(--ink) 32%,transparent);font-family:var(--font-mono);font-size:12px;letter-spacing:.22em;color:color-mix(in srgb,var(--ink) 78%,transparent)}
.mt-bot-tag::before{content:"";width:4px;height:4px;background:var(--accent)}
.mt-bot-plate{position:relative;border:1px solid color-mix(in srgb,var(--ink) 28%,transparent)}
.mt-bot-plate>.mt-bot-tag{position:absolute;top:-1px;left:-1px;background:var(--paper)}
.mt-bot-lead{display:flex;align-items:center;gap:12px;font-family:var(--font-mono);font-size:12px;letter-spacing:.14em;color:color-mix(in srgb,var(--ink) 60%,transparent)}
.mt-bot-lead::before{content:"";flex:none;width:5px;height:5px;border:1px solid var(--accent);border-radius:50%}
.mt-bot-lead::after{content:"";flex:1;height:1px;background:linear-gradient(90deg,color-mix(in srgb,var(--ink) 38%,transparent),transparent)}
.mt-bot-latin{font-family:var(--font-display);font-style:italic;letter-spacing:.04em;color:color-mix(in srgb,var(--ink) 68%,transparent)}
.mt-bot-vein{position:absolute;pointer-events:none;width:90px;height:100%;opacity:.5;background:repeating-linear-gradient(160deg,transparent 0 26px,color-mix(in srgb,var(--ink) 26%,transparent) 26px 27px),linear-gradient(90deg,transparent calc(50% - .5px),color-mix(in srgb,var(--ink) 26%,transparent) calc(50% - .5px) calc(50% + .5px),transparent calc(50% + .5px))}
```

- **禁忌**：引线与签条是标注工具不是装饰，禁无内容空挂；叶脉线禁横穿正文区、禁与引线同页抢焦；母题件一律 `data-editable-skip`

**Variants 配色变体**

#### 月白

- **气质**：暖金灯熄灭后的银灰月色——更冷、更静，像午夜温室的玻璃顶

```css
--paper:#0f0f0f; --paper-tint:#1a1816;
--ink:#e8e4df;   --ink-tint:#2a2724;
--accent:#C9CDC4; --accent-on:#0f0f0f;
```

#### 苔绿

- **气质**：温室深处的苔痕绿——更潮湿、更幽闭的夜，适合蕨类/森林/生态叙事

```css
--paper:#0f0f0f; --paper-tint:#1a1816;
--ink:#e8e4df;   --ink-tint:#2a2724;
--accent:#8FA07A; --accent-on:#0f0f0f;
```

- **accent 预算**：苔绿明度低，暗底上只做线条与小签点，禁大色块；其余同基底口径

### C3 终端绿

- **id**：c3
- **气质**：暗底磷光绿 + 全栈等宽，CRT 终端的物质感与纪律
- **适用**：技术分享、开发者大会、工程文化、安全与基础设施、极客主题
- **focus**：G1 + G9
- **世界参考**：CRT 磷光终端史（VT100 / 早期 Unix）——黑玻璃屏、绿磷光、扫描线、闪烁光标
- **unforgettable**：提示符后的闪烁光标块——那枚 steps() 跳闪的绿色方块，一眼终端
- **分化声明**：与 c1 分化于 L2/L3/L4/L5/L6——c3 是全栈等宽 + CRT 扫描线质感 + ASCII 框/光标/提示符母题 + 描边终端窗口容器 + typewriter/scramble 签名；c1 是极粗无衬线 + flat 平色 + 直角色块 + scale-pop 硬切

**G1 color**

```css
--paper:#0d1117; --paper-tint:#161b22;
--ink:#e6edf3;   --ink-tint:#1c2128;
--accent:#39d353; --accent-on:#0d1117;
```

- **accent 预算**：内容页 accent 面积 ≤10% 且**点状使用**（光标/关键字/单数据点——绿是信号不是油漆）；满屏绿禁止（荧光伤眼），封面暗底 + 绿字而非绿底；首尾闭环：绿字巨标开场 → 收束页绿字/闪烁光标呼应。

**G2 typography**

```css
--font-display:"SF Mono","JetBrains Mono","Menlo",monospace;
--font-body:"SF Mono","JetBrains Mono","Menlo",monospace;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

- **字重倾向**：全栈等宽统一 400–600，层级靠字号与明暗，不靠字重差
- **字号对比**：主标题:正文 ≥8:1（低密度）；高密度 ≥5:1
- **字重映射**：等宽两档立场（不走倒挂——mono 无细体）：标题 600；正文 400；14–16px 小字 600
- **标题修饰**：无（装饰交给母题：提示符前缀与光标）

**G3 texture**

```css
--texture-type: grain;
--texture-layer: repeating-linear-gradient(0deg, color-mix(in srgb, var(--ink) 4%, transparent) 0 1px, transparent 1px 4px);
--texture-scope: all;
```

- **立场**：CRT 扫描线 = 材质本体——全页许可（scope all），强度烧死不得加深

**G4 shape**

- **圆角**：0–2px（直角为主）
- **hairline**：1px solid color-mix(in srgb, var(--accent) 40%, transparent)，终端描边即磷光线
- **阴影**：无
- **容器造型**：1px 描边终端窗口容器——描边 + 标题栏 hairline（栏内嵌 mono 小字会话名/路径）；禁实心色块卡、禁阴影、禁玻璃拟态

**G5 motion**

- **气质**：techy
- **强度上限**：默认
- **锚点偏好**：typewriter / scramble——techy 限定款即本主题签名锚点：命令行段落打字入场、关键词 scramble 定形；光标闪烁作页面句读
- **节奏偏移**：时长档 −1（快）；阶梯步长 ≤45ms（打字机小步快频）
- **缓动签名**：默认三 token，不覆盖（打字感由 recipe 自身的 steps 节奏承担）
- **禁用**：无
- **fx 许可**：constellation / starfield / ascii-field（particle-drift 太柔禁）

**G8 component**

- **亲和**：网格矩阵（终端表格/仪表墙）、数据英雄（mono 大数字 = 终端输出）、轴与节点（日志流/时间线 = commit log 隐喻）
- **禁忌**：禁圆角大卡片与柔和渐变（不属于玻璃磷光屏）；不用加号角标/网格点阵（瑞士系词汇）；裂屏对开慎用——终端是单窗格世界

**G9 motif**

- **词汇**：ASCII 框（1px 磷光描边 + mono 角件 "+"，终端窗口的装饰骨架）/ 闪烁光标块（行尾的绿色方块 caret，复用骨架 tw-caret steps 跳闪）/ "$ " 提示符前缀（命令行段落行首，accent 色）

```css
/* C3 终端绿 · 装饰母题（光标跳闪复用骨架 tw-caret keyframes，主题块不自带 @keyframes） */
.mt-term-box{position:relative;border:1px solid color-mix(in srgb,var(--accent) 45%,transparent)}
.mt-term-box::before{content:"+";position:absolute;top:-.6em;left:-.35em;color:var(--accent);font-family:var(--font-mono);line-height:1}
.mt-term-box::after{content:"+";position:absolute;bottom:-.6em;right:-.35em;color:var(--accent);font-family:var(--font-mono);line-height:1}
.mt-term-caret{display:inline-block;width:.55em;height:1em;margin-left:.08em;background:var(--accent);vertical-align:-.12em;animation:tw-caret 1s steps(1) infinite}
.mt-term-prompt::before{content:"$ ";color:var(--accent);font-weight:600}
```

- **禁忌**：ASCII 框角件只许对角两枚，禁四角全标（过密即噪音）；光标块每页至多两处（句读不是撒布）；提示符前缀只许命令行语义的段落；母题件一律 `data-editable-skip`

**Variants 配色变体**

#### 琥珀磷光

- **气质**：后期 amber 终端（VT220 琥珀屏），暖调怀旧——计算机史、复古计算、硬件文化

```css
--paper:#0d1117; --paper-tint:#161b22;
--ink:#e6edf3;   --ink-tint:#1c2128;
--accent:#FFB000; --accent-on:#0d1117;
```

#### 白磷光

- **气质**：P1 白磷光终端，最冷最素，接近单色打印纸带——极简技术文档、规范与协议主题

```css
--paper:#0d1117; --paper-tint:#161b22;
--ink:#e6edf3;   --ink-tint:#1c2128;
--accent:#F0F6FC; --accent-on:#0d1117;
```

- **accent 预算**：白磷光 accent 与 ink 近色——点状纪律不变，强调靠亮度差与光标位置；其余同基底口径

### C4 纸与墨

- **id**：c4
- **气质**：纸白 + 墨黑 + 一点绯红，传统书籍的安静与仪式感
- **适用**：文化、出版、人文历史、阅读、品牌故事、长篇叙事内容
- **focus**：G2 + G9
- **世界参考**：传统书籍装帧与出版社排版——题花、首字下沉、引文拉页、页码的印刷传统
- **unforgettable**：首字下沉——段首那枚占三行的绯红大字，一眼出版物
- **分化声明**：与 a1 分化于 L1/L2/L4/L6——c4 的 accent 是独立绯红（a1 accent==ink）、全衬线（a1 正文无衬线）、母题是题花/首字下沉/引文拉页（a1 是 Ghost 巨字与竖排题字条）、锚点动效是 draw-line（a1 是 mask-lines）

**G1 color**

```css
--paper:#faf9f7; --paper-tint:#efece7;
--ink:#1a1a1a;   --ink-tint:#2b2b2b;
--accent:#c41e3a; --accent-on:#faf9f7;
```

- **accent 预算**：内容页 accent 面积 ≤5%（绯红出版物式点睛：首字下沉/单引文标记/页码）；满屏 accent 仅封面/收束且宜半版；首尾闭环：封面绯红首字/题花 → 收束页绯红一行题字。

**G2 typography**

```css
--font-display:"Songti SC","Noto Serif SC","STSong",serif;
--font-body:"Songti SC","Noto Serif SC","STSong",serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

- **字重倾向**：全衬线，标题 600–700、正文 400–500
- **字号对比**：主标题:正文 ≥8:1（低密度）；高密度 ≥5:1
- **字重映射**：全衬线恒重立场（不走倒挂——细衬线大字号发虚）：标题 600–700；正文 400–500；14–16px 小字 500–600
- **标题修饰**：首字下沉（封面/章节首段 drop cap）、引文拉页

**G3 texture**

```css
--texture-type: paper;
--texture-layer: radial-gradient(80% 60% at 25% 12%, color-mix(in srgb, var(--ink) 3%, transparent), transparent 65%);
--texture-scope: cover;
```

- **立场**：轻纸纹——仪式页一角纸光，阅读页要绝对干净

**G4 shape**

- **圆角**：0
- **hairline**：1px solid color-mix(in srgb, var(--ink) 18%, transparent)，栏线/页脚线的书籍栏隐喻
- **阴影**：无
- **容器造型**：无卡片立场——靠栏线与留白分区；引文块用 3px 粗左边线 accent（见 .mt-pub-pull）；底色块只用 paper-tint 灰档；禁圆角卡、禁阴影、禁描边装饰框

**G5 motion**

- **气质**：editorial
- **强度上限**：默认
- **锚点偏好**：draw-line（栏线/下划线绘出）+ mask-lines（章节标题逐行显影）；数字以字号对比直排为主，count-up 只给真正的 KPI 英雄页
- **节奏偏移**：时长档 +1（一切比默认慢半拍，翻页感）；阶梯步长 ≥90ms
- **缓动签名**：默认三 token，不覆盖
- **禁用**：scale-pop / persp-in / typewriter / scramble（弹跳、透视与打字机都不属于纸面）
- **fx 许可**：仅 ascii-field

**G8 component**

- **亲和**：图文证据（插图 + 栏线）、巨字宣言（封面题字）、裂屏对开（书籍对开页隐喻）
- **禁忌**：禁连续两页网格矩阵——书页靠栏不靠格；不用加号角标与网格点阵（瑞士系词汇）；图表页须配栏线与衬线标注，不用终端/信号词汇

**G9 motif**

- **词汇**：题花（❧ 字符 + 双侧栏线的居中 ornament，章节末尾/标题下的出版社标记，每页至多一个）/ 首字下沉（::first-letter 绯红大字，占约三行，只许每页首段）/ 引文拉页（3px 绯红粗左边线 + 大号衬线引文）

```css
/* C4 纸与墨 · 装饰母题 */
.mt-pub-orn{display:flex;align-items:center;justify-content:center;gap:16px;color:var(--accent);font-family:var(--font-display);pointer-events:none;user-select:none}
.mt-pub-orn::before,.mt-pub-orn::after{content:"";width:64px;height:1px;background:color-mix(in srgb,var(--ink) 28%,transparent)}
.mt-pub-dropcap::first-letter{font-family:var(--font-display);font-weight:700;font-size:3.2em;line-height:.78;float:left;padding:.06em .14em 0 0;color:var(--accent)}
.mt-pub-pull{border-left:3px solid var(--accent);padding-left:1.2em;font-family:var(--font-display);font-size:1.45em;line-height:1.7}
```

- **禁忌**：题花每页至多一个、只许章节/收束页；首字下沉只许每页首段一段；题花等纯装饰件带 `data-editable-skip`；.mt-pub-dropcap/.mt-pub-pull 加在真实文本上，文本保持可编辑

**Variants 配色变体**

#### 藏青

- **气质**：学术专著与商务出版，沉稳理性——研究、金融、机构报告、严肃长文

```css
--paper:#faf9f7; --paper-tint:#efece7;
--ink:#1a1a1a;   --ink-tint:#2b2b2b;
--accent:#27496D; --accent-on:#faf9f7;
```

#### 黛绿

- **气质**：东方出版社气质，文学与自然——文学、茶文化、博物、人文地理

```css
--paper:#faf9f7; --paper-tint:#efece7;
--ink:#1a1a1a;   --ink-tint:#2b2b2b;
--accent:#2F5D50; --accent-on:#faf9f7;
```

---

## D 系 · 形态与工艺主导

D 系是非颜色主导的方向：质感、形态、字排、母题作为设计感来源的世界采样。

### D1 奶油物语

- **id**：d1
- **气质**：暖奶油底 + 焦糖点缀，圆润轻盈的甜品店感
- **适用**：生活方式、品牌发布、食品餐饮、母婴亲子、活动邀请等轻暖场景
- **focus**：G4 + G9
- **世界参考**：日系生活方式杂志与甜品店品牌物料——圆角贴纸、手写标价签、柔和色块分区的平面语言
- **unforgettable**：微倾焦糖贴纸徽章——像贴在手账页上的 Q 弹小标签，带着回弹缓动蹦出来，一眼甜品店
- **分化声明**：与 d3 分化于 L2/L3/L4/L5/L6——圆润无衬线对楷体手绘字排（L2）；flat 干净立场对纸面晕染（L3）；贴纸徽章/扇贝花边对笔触块/虚线圈注（L4）；规则大圆角 + 弥散阴影对不规则有机圆角 + 零阴影（L5）；Q 弹 scale-pop 对慢速 draw-line 描绘（L6）

**G1 color**

```css
--paper:#fbf6ee; --paper-tint:#f4ecdc;
--ink:#3d3229;   --ink-tint:#544738;
--accent:#c08334; --accent-on:#fffaf0;
```

- **accent 预算**：内容页 ≤10%（焦糖点缀与小色块）；满屏 accent 仅封面/收束；首尾闭环：封面焦糖色块→收束页焦糖一行字或色带

**G2 typography**

```css
--font-display:"Yuanti SC","PingFang SC","Noto Sans SC",sans-serif;
--font-body:"Yuanti SC","PingFang SC","Noto Sans SC",sans-serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

- **字重倾向**：标题 500–600、正文 400，圆润轻盈不用极粗
- **字号对比**：主标题:正文 ≥8:1（低密度）；高密度 ≥5:1
- **字重映射**：圆润立场（不走倒挂——圆体靠圆融不靠细）：标题 500–600；正文 400；14–16px 小字 500–600
- **标题修饰**：无

**G3 texture**

```css
--texture-type: flat;
--texture-layer: none;
--texture-scope: cover;
```

- **立场**：flat 即质感立场——奶油的柔软靠配色、大圆角与弥散阴影表达，纹理破坏干净感

**G4 shape**

- **圆角**：16–24px 大圆角，全套容器统一圆角语言
- **hairline**：不用分割线，用留白与底色块（paper-tint）分区
- **阴影**：柔和弥散 `0 8px 24px color-mix(in srgb, var(--ink) 8%, transparent)`
- **容器造型**：圆角弥散——大圆角色块卡片（paper-tint 底或 accent 单焦点）+ 弥散软阴影；禁直角、禁描边硬卡、禁玻璃拟态

**G5 motion**

- **气质**：calm
- **强度上限**：低（减少动画元素，只动主角）
- **锚点偏好**：scale-pop 是本命（贴纸徽章与圆角卡片 Q 弹出场）；其余元素 rise-in 柔和上浮即可
- **节奏偏移**：不偏移
- **缓动签名**：覆盖 `--ease-out` 为 cubic-bezier(.34,1.56,.64,1)——带回弹的 Q 弹出停
- **禁用**：无禁用
- **fx 许可**：仅 particle-drift（柔和漂浮不破坏奶油感；其余全禁）

**G8 component**

- **亲和**：网格矩阵（圆角卡片阵是它的货架）、巨字宣言（圆润巨字可爱不压人）
- **禁忌**：禁直角硬朗构图与 hairline 密集分割；不用加号角标与网格点阵（那是瑞士系词汇）

**G9 motif**

- **词汇**：贴纸徽章（accent 圆角胶囊小标，微倾 −3°，配 scale-pop 出场，单页 ≤2 个）/ 扇贝花边（paper-tint 圆点连成波浪边条，替代一切直线分隔）/ 奶油圆点（accent 实心圆点作列表符号，替代方点与编号）

```css
/* D1 奶油物语 · 装饰母题 + 缓动签名 */
:root{--ease-out:cubic-bezier(.34,1.56,.64,1)}
.mt-crm-sticker{display:inline-block;padding:.45em 1.1em;border-radius:999px;background:var(--accent);color:var(--accent-on);font-weight:600;letter-spacing:.05em;transform:rotate(-3deg);box-shadow:0 6px 18px color-mix(in srgb,var(--accent) 30%,transparent)}
.mt-crm-scallop{height:16px;background-image:radial-gradient(circle at 8px 0,var(--paper-tint) 8px,transparent 8.5px);background-size:16px 16px;background-repeat:repeat-x}
.mt-crm-dot{display:inline-block;width:.55em;height:.55em;border-radius:50%;background:var(--accent)}
```

- **禁忌**：贴纸徽章禁直角、禁每页超过 2 个（贴满即廉价）；扇贝花边禁进数据图表区（干扰读数）；母题件一律 `data-editable-skip`

**Variants 配色变体**

#### 抹茶

- **气质**：抹茶绿 + 奶油底，清新安静的和菓子感——茶饮、健康、自然系、生活方式品牌

```css
--paper:#fbf6ee; --paper-tint:#f4ecdc;
--ink:#3d3229;   --ink-tint:#544738;
--accent:#7A8B3F; --accent-on:#fffaf0;
```

#### 莓果

- **气质**：莓果粉 + 奶油底，甜美柔软的法式橱窗感——美妆、母婴、节庆、礼物场景

```css
--paper:#fbf6ee; --paper-tint:#f4ecdc;
--ink:#3d3229;   --ink-tint:#544738;
--accent:#C45B6E; --accent-on:#fffaf0;
```

### D2 柔光暗房

- **id**：d2
- **气质**：暗房安全灯下的琥珀光——影像正在显影液里浮现，安静、有胶片的颗粒时间感
- **适用**：摄影/影像/艺术/品牌故事，氛围叙事，情绪主导的发布
- **focus**：G3 + G9
- **世界参考**：摄影暗房与胶片工艺——安全灯红光、显影液里慢慢显影的相纸、胶片齿孔、放大机投下的光束
- **unforgettable**：显影——一切从黑暗中柔光浮现（blur-in 显影式入场 + accent 辉光托底），胶片齿孔条压住页缘
- **分化声明**：与 c2 分化于 L1/L2/L4/L5/L6——d2 琥珀更亮更橙、c2 暖金暗哑；d2 标题 400–500 偏细 + 斜体强调、c2 标题 500–600 恒重；d2 母题是胶片齿孔/光束角标/显影晕、c2 是标本引线/编号签/叶脉分叉线；d2 容器无框禁描边只许辉光托底、c2 是 1px 细描边直角图鉴卡；d2 签名动效是 blur-in 显影 + 覆盖缓动为更慢的浮出曲线、c2 是 draw-line 叶脉生长（L3 两者同为 glow/cover，不计入分化——拉开靠的是 L4/L5/L6）

**G1 color**

```css
--paper:#14110e; --paper-tint:#211b16;
--ink:#f0e6d8;   --ink-tint:#2c241d;
--accent:#e8a34c; --accent-on:#14110e;
```

- **accent 预算**：内容页 accent 面积 ≤5%（暖金是暗房里的灯，只点一两处：辉光托底、光束角标、关键数字）；满屏 accent 禁止——暗房没有开大灯的时刻；首尾闭环：封面辉光开场 → 收束页同位辉光呼应（可略强）。

**G2 typography**

```css
--font-display:"Songti SC","Noto Serif SC","STSong",serif;
--font-body:"PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

- **字重倾向**：标题 400–500 偏细、正文 400——氛围靠辉光而非字重，暗场衬线偏细更空
- **字号对比**：主标题:正文 ≥8:1（低密度）；高密度 ≥5:1
- **字重映射**：衬线偏细立场：≥77px→400–500；35–76px→400–500；正文 400；14–16px 小字 500
- **标题修饰**：斜体强调（西文/引文用 italic 点睛，中文不全句斜体）

**G3 texture**

```css
--texture-type: glow;
--texture-layer: radial-gradient(120% 90% at 70% 10%, color-mix(in srgb, var(--accent) 14%, transparent), transparent 60%);
--texture-scope: cover;
```

- **立场**：glow——仪式页上方一团琥珀辉光，是放大机投下的光束也是安全灯；正文页纯暗，内容靠自己"显"出来

**G4 shape**

- **圆角**：0–4px（胶片是工业切片，几乎不用圆角）
- **hairline**：少用——暗房里边界靠光不靠线；必要时 1px solid color-mix(in srgb, var(--ink) 22%, transparent)
- **阴影**：无硬阴影；唯一允许的"影"是 accent 低透明辉光托底（`.mt-drk-halo`）
- **容器造型**：无框 + 辉光底——容器不描边、不出卡片、不落厚色块，用显影晕柔光把内容从暗底中"显"出来；禁描边卡、禁硬投影、禁满版色块（与 c2 图鉴卡立场相反，这是两主题 L5 的分界）

**G5 motion**

- **气质**：calm（ambience 型归入沉静：慢速、低强度、只动主角）
- **强度上限**：低
- **锚点偏好**：blur-in 显影式入场为签名——标题与图像如相纸在显影液中浮现；数据页 draw-line 可用但不做主角，count-up 只给真正的 KPI 英雄页
- **节奏偏移**：时长档 +1（显影是慢过程，急不得）
- **缓动签名**：覆盖 `--ease-out` 为 cubic-bezier(.1,.7,.2,1)——更慢更柔的浮出曲线，像影像从药水里长出来
- **禁用**：无（calm 气质本身排除硬切/弹跳/字符噪点类）
- **fx 许可**：starfield、particle-drift（暗场星点与药液浮尘；constellation 连线感太硬，禁）

**G8 component**

- **亲和**：巨字宣言（暗场巨字 + 辉光托底，暗房最正当的仪式感）、裂屏对开（明/暗对撞 = 负片/正片、曝光/遮光）
- **禁忌**：禁密集网格矩阵（暗场堆格子像档案柜，不属于暗房）；数据英雄页保持大留白，图表以 accent 单系列描线为主

**G9 motif**

- **词汇**：胶片齿孔条（`.mt-drk-film`：12px 方孔 repeating 边带，只许页面上缘或下缘横贯一条）/ 光束角标（`.mt-drk-beam`：细长三角光楔从页角射入，accent 低透明，每页至多 1 个、只许仪式页）/ 显影晕（`.mt-drk-halo`：accent 低透明 radial 柔光托底，是无框容器唯一的"边界"）

```css
/* D2 柔光暗房 · 装饰母题 + 缓动签名 */
:root{--ease-out:cubic-bezier(.1,.7,.2,1)}
.mt-drk-film{height:26px;pointer-events:none;background-image:linear-gradient(90deg,color-mix(in srgb,var(--ink) 55%,transparent) 0 12px,transparent 12px 24px);background-size:24px 12px;background-repeat:repeat-x;background-position:0 50%;opacity:.6}
.mt-drk-beam{position:absolute;pointer-events:none;width:200px;height:200px;background:linear-gradient(135deg,color-mix(in srgb,var(--accent) 20%,transparent),transparent 65%);clip-path:polygon(0 0,100% 0,0 100%)}
.mt-drk-halo{position:relative}
.mt-drk-halo::before{content:"";position:absolute;inset:-12%;pointer-events:none;background:radial-gradient(65% 65% at 50% 60%,color-mix(in srgb,var(--accent) 13%,transparent),transparent 70%)}
```

- **禁忌**：齿孔条禁竖放、禁多于一组边带；光束角标禁压正文文字；显影晕禁叠在任何描边卡上（无框立场）；母题件一律 `data-editable-skip`

**Variants 配色变体**

#### 银盐

- **气质**：黑白银盐相纸的冷调——暖灯关掉，只剩月光白的显影盘，适合建筑/纪实/极简影像

```css
--paper:#14110e; --paper-tint:#211b16;
--ink:#f0e6d8;   --ink-tint:#2c241d;
--accent:#C0C8D0; --accent-on:#14110e;
```

#### 安全灯红

- **气质**：暗房安全灯的忠实采样——红是暗房里唯一被允许的光，氛围最强、使用最克制

```css
--paper:#14110e; --paper-tint:#211b16;
--ink:#f0e6d8;   --ink-tint:#2c241d;
--accent:#C0392B; --accent-on:#f0e6d8;
```

- **accent 预算**：红光下辉光即安全灯本灯，正合世界；但红 accent 面积预算从严——≤5% 不变且永不满屏，正文文字一律保持 ink 不落红

### D3 手绘油彩

- **id**：d3
- **气质**：画纸暖灰 + 赭石一笔，手绘油彩的呼吸感与留白
- **适用**：艺术、文化、展览、人文叙事、创作者作品集、慢内容分享
- **focus**：G2 + G9
- **世界参考**：画室速写本与手工画册——可见笔触的油画小品、铅笔虚线圈注、细双描边的画框装裱
- **unforgettable**：笔触块——不规则有机边缘的色块像一笔抹上去的油彩，垫在标题后面，每页都有"被画出来"的痕迹
- **分化声明**：与 a1 分化于 L2/L3/L4/L5/L6——a1 是编辑部衬线、墨韵 glow、Ghost 残影字、无卡片立场、mask-lines 显影；d3 是楷体手绘字排、纸面晕染全页许可、笔触块与虚线圈注、不规则有机圆角容器、draw-line 慢描绘

**G1 color**

```css
--paper:#e9e5da; --paper-tint:#dcd6c6;
--ink:#33413a;   --ink-tint:#46564d;
--accent:#a05f3c; --accent-on:#f5f1e6;
```

- **accent 预算**：内容页 ≤10%（赭石点缀：笔触块/单强调字）；满屏 accent 仅封面/收束；首尾闭环：封面赭石墨色块→收束页赭石一笔

**G2 typography**

```css
--font-display:"Kaiti SC","STKaiti","Songti SC","Noto Serif SC",serif;
--font-body:"Kaiti SC","STKaiti","Songti SC","Noto Serif SC",serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

- **字重倾向**：400–600，靠字体手绘感不靠字重对比
- **字号对比**：主标题:正文 ≥8:1（低密度）；高密度 ≥5:1
- **字重映射**：手绘立场——楷体无多档字重，层级靠字号差：标题 400–600；正文 400；14–16px 小字 500–600
- **标题修饰**：手绘衬线字体本身即修饰，不另加

**G3 texture**

```css
--texture-type: paper;
--texture-layer: radial-gradient(80% 60% at 30% 20%, color-mix(in srgb, var(--accent) 5%, transparent), transparent 70%), radial-gradient(70% 80% at 75% 85%, color-mix(in srgb, var(--ink) 4%, transparent), transparent 70%);
--texture-scope: all;
```

- **立场**：画纸晕染 = 材质本体——纸与颜料晕染是这个世界的一部分，正文页也允许铺（scope all），但仍需生成侧逐页 `texture-on` 落码

**G4 shape**

- **圆角**：不规则圆角——微妙非对称 radius（如 `14px 18px 12px 20px`），禁全等圆角的工业感
- **hairline**：不用直线分割，用留白分区；标注职能交给虚线圈注（G9）
- **阴影**：无——纸面世界不吃投影，层次靠色块叠压与晕染
- **容器造型**：不规则圆角 + 极淡纸色底（paper-tint）；禁直角硬卡、禁玻璃拟态、禁描边窗口

**G5 motion**

- **气质**：calm
- **强度上限**：低
- **锚点偏好**：draw-line（笔触描绘感——线条像被画出来，是它的签名）；文字入场 rise-in 轻上浮
- **节奏偏移**：时长档 +1（慢半拍，描绘需要的时间）
- **缓动签名**：默认三 token，不覆盖
- **禁用**：无禁用
- **fx 许可**：全禁（手绘材质与数字粒子/字符场冲突）

**G7 illustration**

- **风格**：手绘油画质感插画——可见笔触、低饱和、灰绿/赭石/雾蓝三色体系、大量留白
- **提示词种子**：hand-painted oil illustration, muted sage green / ochre / misty blue palette, visible brushstrokes, generous negative space
- **禁忌**：不用照片级写实、不用高饱和霓虹色、不用矢量扁平风

**G8 component**

- **亲和**：图文证据（画作 + 图注是它的原生形态）、巨字宣言（手绘巨字有画册封面感）
- **禁忌**：禁网格矩阵密集排布（画室的墙不是货架）；数据英雄页慎用，图表须以笔触块或画框装裱收编

**G9 motif**

- **词汇**：笔触块（不规则有机边缘的 accent 淡色块，垫在标题或关键词后，像一笔抹上去的油彩）/ 手绘虚线圈注（dashed 不规则圆角框，像铅笔随手圈出的批注）/ 画框双描边（细双线装裱图片与画作，纸色勾边隔开两道墨线）

```css
/* D3 手绘油彩 · 装饰母题 */
.mt-art-brush{position:relative;isolation:isolate}
.mt-art-brush::before{content:"";position:absolute;inset:-.15em -.35em;z-index:-1;background:color-mix(in srgb,var(--accent) 22%,transparent);border-radius:62% 38% 55% 45%/48% 55% 42% 52%}
.mt-art-circle{border:2px dashed color-mix(in srgb,var(--accent) 65%,transparent);border-radius:58% 42% 50% 50%/52% 48% 55% 45%;padding:.4em .9em}
.mt-art-frame{border:1px solid color-mix(in srgb,var(--ink) 55%,transparent);box-shadow:inset 0 0 0 5px var(--paper),inset 0 0 0 6px color-mix(in srgb,var(--ink) 35%,transparent)}
```

- **禁忌**：笔触块每页 ≤2 处且只垫重点（处处笔触即脏）；虚线圈注禁圈长段落（只圈词/短语）；母题件一律 `data-editable-skip`

**Variants 配色变体**

#### 雾蓝

- **气质**：油画三色体系的重心移向雾蓝——烟雨山水感，冷静诗意，适合东方美学、节气、慢旅行

```css
--paper:#e9e5da; --paper-tint:#dcd6c6;
--ink:#33413a;   --ink-tint:#46564d;
--accent:#5B7A8C; --accent-on:#f5f1e6;
```

#### 灰绿

- **气质**：油画三色体系的重心移向灰绿——苔色入画，植物标本册感，适合自然、植物、生态、茶文化

```css
--paper:#e9e5da; --paper-tint:#dcd6c6;
--ink:#33413a;   --ink-tint:#46564d;
--accent:#6B7F5E; --accent-on:#f5f1e6;
```

---

## 选择建议

| 场景 | 推荐 |
|---|---|
| 不知道选什么 | A1 电子杂志 |
| AI / 技术 / 产品发布 | A1 靛蓝瓷变体 或 B1 瑞士（IKB） |
| 文化 / 行业观察 / 深度内容 | A1 森林墨变体 或 C4 纸与墨 |
| 人文 / 书评 / 怀旧 | A1 牛皮纸变体 或 C4 纸与墨 |
| 生活方式 / 消费品牌 / 轻暖场景 | D1 奶油物语 |
| 自然 / 博物 / 研究型叙事 | C2 暗夜植物园 |
| 设计 / 艺术 / 展览 / 匠心 | D3 手绘油彩 或 A1 沙丘变体 |
| 年轻 / 活力 / 零售 | B1 柠檬黄 / 柠檬绿变体 |
| 工业 / 警告 / 转折重点 | B1 安全橙变体 |
| 开发者 / 工程文化 | C3 终端绿 |
| 高冲击 keynote | C1 信号黑 |
| 沉浸暗场 / 影像 / 晚间发布 | D2 柔光暗房 |
| 出版 / 长篇叙事 / 品牌故事 | C4 纸与墨 |

## 图表 token（全主题统一推导）

图表颜色不写死、不逐主题枚举，按以下规则从基础 token 推导（规则见 references/charts.md）：

```css
--chart-grid:   color-mix(in srgb, var(--ink) 12%, transparent);  /* 网格线 */
--chart-label:  color-mix(in srgb, var(--ink) 60%, transparent);  /* 轴/图例标签 */
--chart-series-1: var(--accent);     /* 主系列 */
--chart-series-2: color-mix(in srgb, var(--accent) 55%, var(--paper));
--chart-series-3: color-mix(in srgb, var(--accent) 32%, var(--paper));
--chart-series-4: color-mix(in srgb, var(--ink) 18%, var(--paper));
/* 5–8 档（F3 扩，多系列图表用）：accent 浅阶与 ink 阶梯明暗交错续排，
   保证任意相邻两档明度可区分；1–4 档定义冻结不变（向后兼容）。 */
--chart-series-5: color-mix(in srgb, var(--ink) 62%, var(--paper));
--chart-series-6: color-mix(in srgb, var(--accent) 16%, var(--paper));
--chart-series-7: color-mix(in srgb, var(--ink) 40%, var(--paper));
--chart-series-8: color-mix(in srgb, var(--ink) 24%, var(--paper));
--chart-bar-radius: 0;               /* A/B 系 0；C/D 系可用 ≤8px */
--chart-stroke: 2.5px;               /* 折线宽 */
```

推导即约定：系列色全部从 accent/ink/paper 用 color-mix 派生——A 系 accent==ink 时自动得到同色系灰阶，多系列不会撞色。生成图表时把这段加进主题的 `:root` 块即可，不允许逐图表自定义系列色。暗色页上若系列色与底色拉不开，对 paper 做镜像派生（`color-mix(in srgb, var(--accent) X%, var(--ink))`，5–8 档同样镜像：ink 阶梯换成 accent 向 ink 的阶梯）。

**系列色使用纪律（F3）**：8 档是硬上限——系列数 >4 时先自问能否合并（尾部并"其他"、维度下钻拆页）；超过 8 系列说明图表选型错了（改热力表格/斜率图/拆页）。堆叠图同一柱内相邻段的明度差由交错阶梯天然保证，禁止相邻段取相邻奇偶档以外的组合自行调配。

## 禁忌

- 禁止混搭：不取 A 系的底色配 B 系的高亮色；
- 禁止自定义 hex：用户坚持时展示本库请其重选；
- 禁止一份 deck 中途换主题（变体切换同样禁止——变体在选定时一次冻结）；
- B 系的高亮色单页最多出现在一个视觉重心上；
- accent 是预算制资源：内容页 accent 面积 ≤10%（各主题 G1 的预算口径为准），满屏 accent 只给封面/收束；
- **装饰母题只用本主题 G9 词汇，禁跨主题借用**：加号角标/网格点阵属瑞士系（b1），Ghost 残影字/竖排题字条属杂志系（a1），ASCII 框/光标属终端（c3），题花/首字下沉属出版（c4）……母题串味比配色串味更毁差异化；
- 母题件一律 `data-editable-skip`（契约 v6.2）；文本载体类母题（如 `.mt-pub-dropcap`/`.mt-pub-pull`）除外——样式由类承担，文本保持可编辑。

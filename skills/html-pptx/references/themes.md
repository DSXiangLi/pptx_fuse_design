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
| L2 字体性格 | font-display / font-body / font-mono、字重倾向、**字号对比档**、**字重映射**、标题修饰（可引用 `typography.md` §7 文字效果词汇 `.tt-*`）；可选「display 联网备选」（性格字体 + fallback + 仅用户接受联网时加载，离线回落无感） | G2 typography | ✅ |
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
- **标题修饰**：填充 + 描边混排（`.tt-outline`）亲和——信号黑标题里描边词充当背景层、填充词（或 accent 词）做焦点；删除线对照（`.tt-strike`）亲和反差数据带的 from 值；禁用 gradient-flow（柔化渐变削弱信号，G5 同口径）
- **display 联网备选**：Bebas Neue 类窄体大写（fallback：'Arial Narrow','Helvetica Neue Condensed',sans-serif）——仅用户接受联网时加载，离线回落系统极粗无衬线无感

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

## E 系 · 世界采样（I 期新增）

E 系是"世界采样法"的第一批成果（构思流程见 handover §5.3）：每个主题从一个真实世界翻译而来——印刷工艺、设计史、东方版画、行业票据、自然系统。

### E1 孔版印刷

- **id**：e1
- **气质**：大豆油墨 + 荧光专色 + 套色错位，独立出版 zine 的手工印刷感与不完美的生命力
- **适用**：创意/设计/艺术分享、青年文化与亚文化主题、工作坊与社区活动、独立出版、任何"反精致"立场的表达
- **focus**：G3 + G9
- **世界参考**：Riso 孔版印刷与独立出版 zine 文化——大豆油墨专色滚筒、手工装订小志、套色不准的"印刷事故美"、网目调与颗粒噪点
- **unforgettable**：套色错位——同一形状两层油墨错开 2–3px 叠印出的重影色边，一眼 riso；没有错位就是骗子主题
- **分化声明**：与 d3 分化于 L2/L4/L5/L6——d3 是楷体手绘字排、笔触块/虚线圈注/画框双描边母题、不规则有机圆角容器、calm 气质的 draw-line 慢描绘；e1 是粗黑无衬线海报字排、套色错位叠印块/裁剪虚线/网目调母题、微旋转拼贴卡容器、playful 气质的 scale-pop 蹦贴节奏

**G1 color**

```css
--paper:#f7f2e6; --paper-tint:#ece5d3;
--ink:#221d16;   --ink-tint:#332c22;
--accent:#FF48B0; --accent-on:#fdfaf3;
```

- **accent 预算**：内容页 accent 面积 ≤10%（荧光专色给错位叠印块/网目调块/单强调词——专色油墨是滚筒上一整支，但版面里只准点染）；满屏荧光 accent 是封面/收束特权（riso 海报的整版荧光单色是它的原生形态）；首尾闭环：封面荧光专色满版 + 错位巨标开场 → 收束页同色错位叠印条带呼应（半亮：accent 淡档色块）。

**G2 typography**

```css
--font-display:"Helvetica Neue","Arial Black","PingFang SC","Noto Sans SC",sans-serif;
--font-body:"Helvetica Neue","PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;
--font-mono:"Courier New","SF Mono","JetBrains Mono",monospace;
```

- **字重倾向**：标题 700–900（海报粗黑，拉丁落 Arial Black 档）、正文 400–500——zine 的对比是油墨与纸，不是字重阶梯
- **字号对比**：主标题:正文 ≥8:1（低密度）；高密度 ≥5:1
- **字重映射**：粗黑恒重立场（不走倒挂——zine 标题越大越要黑，细大标题在厚纸上发飘）：≥77px→800–900；35–76px→700–800；正文 400；14–16px 小字 500–600
- **标题修饰**：标题/关键词后垫套色错位叠印块（G9 `.mt-ris-misreg`），字体本身不加修饰

**G3 texture**

```css
--texture-type: grain;
--texture-layer: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='240' height='240'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='240' height='240' filter='url(%23n)' opacity='0.05'/%3E%3C/svg%3E"), radial-gradient(70% 60% at 75% 85%, color-mix(in srgb, var(--accent) 4%, transparent), transparent 65%);
--texture-scope: all;
```

- **立场**：颗粒 = 材质本体——riso 大豆油墨的颗粒感与滚筒上墨不均是这个世界的一部分，全页许可（scope all），正文页也铺，但仍需生成侧逐页 `texture-on` 落码

**G4 shape**

- **圆角**：0–2px（剪纸拼贴以直角为主，zine 没有工业圆角）
- **hairline**：1px dashed color-mix(in srgb, var(--ink) 38%, transparent)——裁剪虚线隐喻（剪刀沿线的 zine 手工感），实线 hairline 只给图表轴
- **阴影**：无投影——"厚度"由套色错位块的双层叠印承担（G9），纸面世界不吃弥散阴影
- **容器造型**：微旋转拼贴卡——直角纯色块（paper-tint 或 accent 淡档）整体 `transform: rotate(±1.5°)`，像 zine 页面上随手贴上去的纸片；禁精密直角网格对齐的强迫症排布、禁玻璃拟态、禁描边窗口

**G5 motion**

- **气质**：playful
- **强度上限**：默认
- **锚点偏好**：scale-pop 为签名锚点——拼贴卡/叠印块蹦贴上墙的弹感；封面标题 chars 错落阶梯入场（逐字如逐色滚筒套印）；数据页 rise-in 轻上浮，禁数据端过度编排
- **节奏偏移**：时长档默认；阶梯步长 60–90ms（拼贴逐件上墙的节奏）
- **缓动签名**：覆盖 `--ease-out` 为 cubic-bezier(.3,1.4,.4,1)——轻微过冲回弹，纸片落位的物理感
- **禁用**：typewriter / scramble（打字机是终端词汇）/ blur-in（模糊不属于油墨与纸）
- **fx 许可**：全禁（颗粒与拼贴是材质不是像素仪式，canvas 粒子不属于印刷世界）

**G8 component**

- **亲和**：图文证据（拼贴画页是它的原生形态）、巨字宣言（海报式粗黑巨字 + 错位叠印）、裂屏对开（zine 跨页对撞）
- **禁忌**：禁连续两页网格矩阵——zine 是拼贴不是货架；禁绝对对齐洁癖：相邻拼贴件允许 ±1.5° 微旋转与轻微破格出血；图表须收编进拼贴卡（纸贴图表），禁裸图表直角网格页

**G9 motif**

- **词汇**：套色错位叠印块（`.mt-ris-misreg`：同一形状两层 accent 不同明度错 2–3px 叠印 + multiply 混色，垫在标题/关键词后，每页 ≤2 处）/ 裁剪虚线（`.mt-ris-cut`：dashed 分隔线，剪刀沿线的手工暗示）/ 网目调点块（`.mt-ris-halftone`：accent 半调点阵，只许页面角落或色块边缘低透明，模拟 riso 挂网）

```css
/* E1 孔版印刷 · 装饰母题 + 缓动签名 */
:root{--ease-out:cubic-bezier(.3,1.4,.4,1)}
.mt-ris-misreg{position:relative;isolation:isolate}
.mt-ris-misreg::before,.mt-ris-misreg::after{content:"";position:absolute;inset:-.12em -.3em;z-index:-1;mix-blend-mode:multiply}
.mt-ris-misreg::before{background:color-mix(in srgb,var(--accent) 80%,transparent);transform:translate(-2.5px,2px)}
.mt-ris-misreg::after{background:color-mix(in srgb,var(--accent) 40%,var(--paper));transform:translate(2.5px,-2px)}
.mt-ris-cut{border:none;border-top:1px dashed color-mix(in srgb,var(--ink) 38%,transparent)}
.mt-ris-halftone{position:absolute;pointer-events:none;background-image:radial-gradient(color-mix(in srgb,var(--accent) 55%,transparent) 1.2px,transparent 1.7px);background-size:9px 9px;opacity:.5}
```

- **禁忌**：错位量 2–3px 烧死——超过即成故障而非工艺；错位块每页 ≤2 处且只垫重点（处处错位即脏污）；网目调禁铺满版心；`.mt-ris-misreg` 是文本载体类母题（加在真实文本上，文本保持可编辑），其余母题件一律 `data-editable-skip`

**Variants 配色变体**

#### Riso 蓝

- **气质**：只换墨辊——荧光粉滚筒换成 Riso 蓝，同一台机器同一批纸，冷静清爽——技术社区、独立杂志、音乐与现场文化

```css
--paper:#f7f2e6; --paper-tint:#ece5d3;
--ink:#221d16;   --ink-tint:#332c22;
--accent:#0078BF; --accent-on:#f2f8fc;
```

#### 向日葵黄

- **气质**：只换墨辊——向日葵黄专色，最"印刷车间"的一档，明度高、噪点下最出颗粒——青年文化、市集/展览、轻品牌

```css
--paper:#f7f2e6; --paper-tint:#ece5d3;
--ink:#221d16;   --ink-tint:#332c22;
--accent:#FFB511; --accent-on:#221d16;
```

- **accent 预算**：荧光黄明度饱和双高——错位块/半调块面积再收一半（内容页 ≤5%），满屏黄仅封面；黄底上的文字一律 ink 不用 accent-on；其余同基底口径

### E2 蓝图

- **id**：e2
- **气质**：硫酸纸深蓝底 + 白线 + 尺寸标注，工程制图的精确、复写感与"可施工"的权威
- **适用**：工程/建筑/制造、技术方案与架构汇报、基础设施、产品规格书、流程严谨的交付文档
- **focus**：G3 + G9
- **世界参考**：建筑工程蓝图（cyanotype 氰版晒图）——硫酸纸蓝底白线、双向箭头尺寸标注、右下角图框标题栏、绘图网格纸
- **unforgettable**：尺寸标注线——双向箭头 dimension line 加两端延伸线，把图与尺寸缝在一起，一眼工程制图
- **分化声明**：与 b1 分化于 L1/L3/L4/L5——b1 是纸白底高亮色的 flat 平色世界，母题是加号角标/网格点阵/色块编号，容器是直角纯色块；e2 是深蓝底白线世界，制图网格纸质感全页铺底（paper/all vs flat/cover），母题是尺寸标注线/双线图框/图框标题栏，容器是 1px 双线图框

**G1 color**

```css
--paper:#14304a; --paper-tint:#1b3d5c;
--ink:#f2f6f9;   --ink-tint:#0f2438;
--accent:#35C8E8; --accent-on:#0e2a3f;
```

- **accent 预算**：内容页 accent 面积 ≤5%（亮青是蓝图上最亮的那支笔——只给尺寸线箭头、图签、关键数字标注）；满屏 accent 禁止——蓝图的世界里满版只有蓝底，没有满版青色；首尾闭环：封面白线巨标 + 亮青图签开场 → 收束页同位亮青标注/图签呼应。

**G2 typography**

```css
--font-display:"Helvetica Neue","PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;
--font-body:"Helvetica Neue","PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

- **字重倾向**：标题 500–600 恒重 + 拉丁大写字距拉开（工程字一手写体制图字体），正文 400；图注/图号/尺寸一律 mono
- **字号对比**：主标题:正文 ≥8:1（低密度）；高密度 ≥5:1
- **字重映射**：工程字恒重立场（不走倒挂——蓝图上一套字管到底，层级靠字号与线宽不靠字重）：标题 600；副标/区块标 500–600；正文 400；标注/图号 mono 400–500；14–16px 小字 500
- **标题修饰**：拉丁标题全大写 + letter-spacing 拉开；图签编号 mono 前缀（"DWG-A1 / SCALE 1:50" 式，见 G9 `.mt-bp-tag`）

**G3 texture**

```css
--texture-type: paper;
--texture-layer: repeating-linear-gradient(0deg, color-mix(in srgb, var(--ink) 5%, transparent) 0 1px, transparent 1px 7px), repeating-linear-gradient(90deg, color-mix(in srgb, var(--ink) 5%, transparent) 0 1px, transparent 1px 7px), repeating-linear-gradient(0deg, color-mix(in srgb, var(--ink) 12%, transparent) 0 1px, transparent 1px 35px), repeating-linear-gradient(90deg, color-mix(in srgb, var(--ink) 12%, transparent) 0 1px, transparent 1px 35px);
--texture-scope: all;
```

- **立场**：制图网格纸 = 材质本体——蓝图全部画在网格纸上（7px 细格 + 35px 主格双向细白线），全页许可（scope all），正文页也铺，但仍需生成侧逐页 `texture-on` 落码

**G4 shape**

- **圆角**：0（图框一律直角，制图没有圆角）
- **hairline**：1px solid color-mix(in srgb, var(--ink) 45%, transparent)——白线即墨线；线在这个主题里是制图工具：尺寸线、延伸线、图框线、剖面线
- **阴影**：无
- **容器造型**：1px 双线图框容器——外框 + 内缩 5px 第二道细线（`.mt-bp-frame` 落码），右下角钉图框标题栏（`.mt-bp-tag`：图号/比例/日期 mono 小字）；禁圆角卡、禁阴影、禁玻璃拟态、禁满版色块卡

**G5 motion**

- **气质**：professional
- **强度上限**：默认
- **锚点偏好**：draw-line 为签名锚点——尺寸线/图框/折线图像被绘图笔逐段画出；标题入场 wipe-clip 精确揭示（制图的对齐感）；数字以 mono 直排 + 标注线呈现，count-up 只给真正的规格英雄页
- **节奏偏移**：时长档默认（制图是精确不是迟缓，也不是抢）；阶梯步长 ≤60ms
- **缓动签名**：默认三 token，不覆盖（精确感由 draw-line 的描绘节奏承担）
- **禁用**：scale-pop / persp-in（弹跳与透视翻转不属于图板）
- **fx 许可**：全禁（蓝图是纸面世界，无像素仪式）

**G8 component**

- **亲和**：轴与节点（流程图/系统图 = 工程图的原生形态，节点即构件）、数据英雄（规格大数字 + 标注线）、网格矩阵（器件明细表/参数表）
- **禁忌**：禁手绘/有机形态（撕边、笔触、晕染都不是制图）；裂屏对开慎用——图框是完整单页，禁把图框劈开；不用加号角标/网格点阵（瑞士系词汇）——本主题的角部词汇是延伸线与图框角

**G9 motif**

- **词汇**：尺寸标注线（`.mt-bp-dim`：双向箭头 hairline + 居中 mono 尺寸注记，两端可带延伸线——工程制图词汇，与 c2 的标本引线 `.mt-bot-lead` 不同源：那是渐隐装饰引线，这是双向箭头的度量工具）/ 双线图框（`.mt-bp-frame`：外 1px + 内缩 5px 细线，图纸边框）/ 图框标题栏（`.mt-bp-tag`：钉在图框右下角的 mono 分格小签——图号/比例/日期，每页至多一个）

```css
/* E2 蓝图 · 装饰母题 */
.mt-bp-frame{position:relative;border:1px solid color-mix(in srgb,var(--ink) 55%,transparent)}
.mt-bp-frame::before{content:"";position:absolute;inset:5px;border:1px solid color-mix(in srgb,var(--ink) 32%,transparent);pointer-events:none}
.mt-bp-tag{position:absolute;right:-1px;bottom:-1px;display:flex;font-family:var(--font-mono);font-size:11px;letter-spacing:.14em;color:color-mix(in srgb,var(--ink) 82%,transparent);border:1px solid color-mix(in srgb,var(--ink) 55%,transparent);background:var(--paper)}
.mt-bp-tag>span{padding:.35em .9em;border-left:1px solid color-mix(in srgb,var(--ink) 32%,transparent)}
.mt-bp-tag>span:first-child{border-left:none}
.mt-bp-dim{display:flex;align-items:center;gap:.8em;font-family:var(--font-mono);font-size:12px;letter-spacing:.12em;color:color-mix(in srgb,var(--ink) 75%,transparent)}
.mt-bp-dim i{flex:1;position:relative;height:1px;font-style:normal;background:color-mix(in srgb,var(--ink) 55%,transparent)}
.mt-bp-dim i::before,.mt-bp-dim i::after{content:"";position:absolute;top:-3px;width:0;height:0;border:3.5px solid transparent}
.mt-bp-dim i::before{left:0;border-right:6px solid color-mix(in srgb,var(--ink) 55%,transparent)}
.mt-bp-dim i::after{right:0;border-left:6px solid color-mix(in srgb,var(--ink) 55%,transparent)}
```

- **禁忌**：尺寸线只标真实结构（容器/图/关键间距），禁无对象空挂——标注是度量不是装饰；标题栏只许右下角、每页至多一个；双线图框禁嵌套（图框套图框即图纸事故）；母题件一律 `data-editable-skip`

**Variants 配色变体**

#### 反相蓝图

- **气质**：蓝线白底的晒图反相——从硫酸纸回到绘图板，更亮更文档化，适合打印交付与正式评审

```css
--paper:#f4f7f9; --paper-tint:#e5ecf1;
--ink:#14304a;   --ink-tint:#27455e;
--accent:#0E7D99; --accent-on:#f4f7f9;
```

#### 黑板粉笔

- **气质**：深灰黑板 + 白粉笔线 + 粉笔黄标注——制图前的推演现场，适合方案推演、教学、头脑风暴复盘

```css
--paper:#232a30; --paper-tint:#2d353c;
--ink:#e9edf0;   --ink-tint:#161b1f;
--accent:#E3C85C; --accent-on:#232a30;
--texture-type: grain;
--texture-layer: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='240' height='240'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='240' height='240' filter='url(%23n)' opacity='0.06'/%3E%3C/svg%3E"), repeating-linear-gradient(0deg, color-mix(in srgb, var(--ink) 6%, transparent) 0 1px, transparent 1px 7px), repeating-linear-gradient(90deg, color-mix(in srgb, var(--ink) 6%, transparent) 0 1px, transparent 1px 7px);
```

- **accent 预算**：粉笔黄是黑板上唯一的彩色粉笔——标注纪律不变（≤5%），粉笔尘颗粒感强于基底网格；其余同基底口径

### E3 装饰艺术 Art Deco

- **id**：e3
- **气质**：墨黑底 + 金线扇形放射，爵士时代的对称奢华与隆重
- **适用**：品牌发布、晚宴/庆典/颁奖典礼、奢侈品、金融、历史文化、需要仪式感与华丽记忆的场合
- **focus**：G9 + G1
- **世界参考**：1920s Art Deco——《了不起的盖茨比》的爵士时代、克莱斯勒大厦的扇形放射与阶梯几何、剧院海报的对称金框
- **unforgettable**：金线扇形放射（sunburst）+ 对称双线金框——页顶一扇金线放射、标题上下菱形分隔，一眼盖茨比
- **分化声明**：与 c1 分化于 L1/L2/L4/L5/L6——e3 墨黑暖底 + 金属金 accent、c1 纯黑舞台 + 信号橙；e3 是高对比衬线 display + 大写宽字距拉丁 kicker、c1 是极粗无衬线；e3 母题是扇形放射/双线金框/菱形分隔、c1 是信号条/巨号页码/信号方块；e3 容器是双线金描边直角框、c1 是大色块直角禁描边；e3 动效 dramatic 慢速隆重（时长 +1、mask-lines 亲和、禁 scale-pop）、c1 dramatic 短促爆发（时长 −1、scale-pop 过冲亲和、禁 mask-lines）

**G1 color**

```css
--paper:#111110; --paper-tint:#1b1b18;
--ink:#f0e9d6;   --ink-tint:#0a0a09;
--accent:#c9a227; --accent-on:#111110;
```

- **accent 预算**：金是线不是面——内容页 accent 面积 ≤8%（金线、扇形放射、菱形分隔、双线框，禁大面积金块）；满屏特权：封面/收束可用满幅双线金框 + 扇形放射仪式背景 + 金底反白特权页；首尾闭环：封面金线 sunburst（全亮）开场 → 收束页同构 sunburst（半亮或缩小）呼应。

**G2 typography**

```css
--font-display:"Songti SC","Noto Serif SC","STSong",serif;
--font-body:"PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

- **字重倾向**：标题 600–700（Didone 感高对比衬线，粗档表达）、正文 400；层级靠对称构图与字重，不靠色彩泛滥
- **字号对比**：主标题:正文 ≥8:1（低密度）；高密度 ≥5:1
- **字重映射**：衬线恒重立场（不走倒挂——细衬线大字号发虚）：≥77px→600–700；35–76px→600；正文 400；14–16px 小字 500–600
- **标题修饰**：kicker 行 = 大写拉丁 + 宽字距（letter-spacing ≥.3em），上下配菱形分隔符居中对称——Deco 的原生语言

**G3 texture**

```css
--texture-type: flat;
--texture-layer: none;
--texture-scope: cover;
```

- **立场**：flat 即质感立场——金线本身即质感，任何叠加纹理只会把金属感糊掉

**G4 shape**

- **圆角**：0（Deco 的几何是直角与扇形，圆角不属这个世界）
- **hairline**：1px solid color-mix(in srgb, var(--accent) 55%, transparent)——分隔线即金线
- **阴影**：无
- **容器造型**：双线金框直角容器——border + outline 两条 1px 金线、间距 5–6px，直角、中空、无填充；底色块只用 ink-tint/paper-tint 明度档；禁圆角、禁阴影、禁描边以外的装饰性容器

**G5 motion**

- **气质**：dramatic
- **强度上限**：默认
- **锚点偏好**：mask-lines 逐行揭示（标题逐行揭幕，剧院开场感）+ draw-line（双线金框与分隔线生长）；封面 chars 逐字登场（慢阶梯）；count-up 只给真正的 KPI 英雄数字
- **节奏偏移**：时长档 +1（一切隆重慢半拍）；阶梯步长 ≥90ms
- **缓动签名**：默认三 token，不覆盖
- **禁用**：scale-pop / persp-in / scramble（弹跳、透视翻转与字符扰乱不庄重）
- **fx 许可**：全禁（金线放射已是仪式，canvas 仪式层会让它变廉价）

**G7 illustration**

- **种子**：装饰艺术风格插画——暗底金线勾边、扇形/阶梯摩天楼剪影、几何化孔雀与棕榈纹、对称构图；线稿感、禁照片写实、禁柔焦渐变

**G8 component**

- **亲和**：巨字宣言（中轴对称构图）、裂屏对开（中轴对称裂屏 + 金线分界）、轴与节点（对称装饰的时间轴）
- **禁忌**：禁斜线/对角构图——Deco 是中轴对称的艺术；网格矩阵仅许严格对称档且禁连页；不用加号角标/网格点阵（瑞士系词汇）与 ASCII 字符装饰（终端系词汇）

**G9 motif**

- **词汇**：扇形放射 sunburst（repeating-conic-gradient 半扇金线，页顶中央或标题区背景，低透明，每页至多一个）/ 双线金框（border + outline 双线直角框，容器或整页内框）/ 菱形分隔符（旋转 45° 的小金菱，两侧金线翼卫，标题上下居中对称）

```css
/* E3 装饰艺术 · 装饰母题 */
.mt-deco-sun{width:min(56vw,480px);height:calc(min(56vw,480px)/2);border-radius:999px 999px 0 0;overflow:hidden;pointer-events:none;background:repeating-conic-gradient(from -90deg at 50% 100%,color-mix(in srgb,var(--accent) 60%,transparent) 0deg 1.5deg,transparent 1.5deg 9deg)}
.mt-deco-frame{border:1px solid color-mix(in srgb,var(--accent) 70%,transparent);outline:1px solid color-mix(in srgb,var(--accent) 70%,transparent);outline-offset:5px}
.mt-deco-divider{display:flex;align-items:center;justify-content:center;gap:14px;pointer-events:none}
.mt-deco-divider::before,.mt-deco-divider::after{content:"";width:72px;height:1px;background:color-mix(in srgb,var(--accent) 65%,transparent)}
.mt-deco-rhombus{display:inline-block;width:8px;height:8px;background:var(--accent);transform:rotate(45deg)}
```

- **禁忌**：sunburst 每页至多一个、只许页顶/标题区/仪式页背景层，禁与标题同区抢焦；双线金框只许直角、禁配阴影；菱形分隔只许中轴对称位；母题件一律 `data-editable-skip`

**Variants 配色变体**

#### 墨绿金

- **气质**：深墨绿 + 金，老钱俱乐部与丝绒帷幕——金融、家族传承、威士忌、私享晚宴

```css
--paper:#0e1a14; --paper-tint:#16241c;
--ink:#f0e9d6;   --ink-tint:#080f0b;
--accent:#c9a227; --accent-on:#0e1a14;
```

#### 珍珠白银

- **气质**：珍珠浅底 + 深墨 + 银灰金，日间舞会与珠宝图册——时尚、美妆、婚礼、轻奢华品牌

```css
--paper:#ece9e2; --paper-tint:#e0dcd2;
--ink:#17181c;   --ink-tint:#26272c;
--accent:#8c7a4f; --accent-on:#ece9e2;
```

- **accent 预算**：浅底下银灰金明度差弱于暗底金——金线加倍克制（面积 ≤6%），满屏特权改为深墨反白页 + 银灰金双线框；其余同基底口径

### E4 包豪斯 Bauhaus

- **id**：e4
- **气质**：米白纸 + 墨黑 + 原色，圆/三角/方基本形的构成游戏，理性而有玩心
- **适用**：设计、教育、文化、产品方法论、品牌故事，任何"形式追随功能"立场的场合
- **focus**：G9 + G4
- **世界参考**：包豪斯 1919–1933（魏玛/德绍）——Kandinsky 与 Klee 的基本形练习、三原色构成、不对称平衡、形式追随功能
- **unforgettable**：三原色基本几何形的构成游戏——一个正圆、一个三角、一个方块在页面上达成不对称平衡，一眼包豪斯
- **分化声明**：与 b1 分化于 L1/L4/L6/L7——e4 米白暖纸底 + 原色 accent（三原色以变体轮换）、b1 灰白冷纸底 + 单一高亮蓝；e4 母题是基本形三件套（正圆/三角/方块）大尺度构成、b1 是加号角标/网格点阵/色块编号；e4 动效默认缓动且不禁 mask-lines（逐行揭示服务构成节奏）、b1 锐利快出急停缓动且禁 mask-lines；e4 构图是不对称平衡（网格必须被基本形打破）、b1 是网格矩阵纪律亲和

**G1 color**

```css
--paper:#f4f0e4; --paper-tint:#e9e3d3;
--ink:#141412;   --ink-tint:#26241f;
--accent:#D1342B; --accent-on:#f4f0e4;
```

- **accent 预算**：内容页 accent 面积 ≤10%——原色是构成的焦点件，单页至多一个 accent 实色基本形；满屏原色是封面/收束特权（满版原色 + 反白几何构成）；首尾闭环：满版原色封面（全亮）开场 → 收束页原色基本形（缩小或半亮）呼应。
- **多色注记**：主题只有一个 accent——包豪斯的三原色用**变体轮换**表达（基底=红，变体=黄/蓝，同一世界的三种光）；母题里的基本形用 `var(--accent)` + `var(--ink)` + `color-mix()` 派生，单页单 accent 纪律不破。

**G2 typography**

```css
--font-display:"Helvetica Neue","PingFang SC","Noto Sans SC",sans-serif;
--font-body:"Helvetica Neue","PingFang SC","Noto Sans SC",sans-serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

- **字重倾向**：几何无衬线，字重倒挂立场（大标题 200–300 细而稳，小字 500–700）——包豪斯的粗细是功能不是装饰
- **字号对比**：主标题:正文 ≥8:1（低密度）；高密度 ≥5:1
- **字重映射**：归藏倒挂阶梯：≥154px→200；77–153px→200–300；35–76px→300–400；17–34px→400–500；14–16px→500–600；同页小字字重 ≥ 大字
- **标题修饰**：无（大写拉丁小标题可配基本形标记，修饰归母题不归字体）

**G3 texture**

```css
--texture-type: flat;
--texture-layer: none;
--texture-scope: cover;
```

- **立场**：flat 即质感立场——包豪斯不要纹理，纸面、原色、几何三样就够

**G4 shape**

- **圆角**：0——圆只属于基本形正圆，不作为容器圆角策略
- **hairline**：2px solid var(--ink)——网格线是粗结构线、横贯版面的功能分隔，不是装饰细线
- **阴影**：无
- **容器造型**：直角纯色基本形块——容器即放大的基本形（正方块、正圆块承载内容，accent / ink / paper-tint 三档纯色）；基本形块是不对称构图的平衡件，accent 块单页至多一个（与单焦点纪律同口径）；禁圆角卡、禁描边卡、禁渐变、禁阴影

**G5 motion**

- **气质**：professional
- **强度上限**：默认
- **锚点偏好**：wipe-clip 精确揭示（基本形块与标题沿网格方向滑入）+ mask-lines（标题逐行揭示，服务构成节奏）；count-up 给数据英雄页
- **节奏偏移**：时长档 −1（短促）；阶梯步长 ≤60ms
- **缓动签名**：默认三 token，不覆盖
- **禁用**：scale-pop / persp-in / blur-in（过冲弹跳与柔焦不是包豪斯的理性）
- **fx 许可**：全禁

**G8 component**

- **亲和**：裂屏对开（原色对撞）、巨字宣言（配基本形平衡件）、图文证据（图与文的不对称并置）
- **禁忌**：禁严格对称的静态网格矩阵连页——包豪斯的平衡是不对称的，网格可用但必须被基本形打破；轴与节点可用但轴线必须粗结构线化；不用加号角标/网格点阵（那是瑞士系词汇）

**G9 motif**

- **词汇**：基本形三件套（`.mt-bau-circle` 正圆 / `.mt-bau-tri` 三角 / `.mt-bau-square` 方块——大尺度低透明做背景构成，或 accent 实色做焦点，每页 1–3 件成组出现、达成不对称平衡）/ 粗网格线（2px ink 结构线，横贯版面的功能分隔）/ 三原色轮换（基本形颜色派生自 `var(--accent)` 与 `var(--ink)`，换变体即换世界的光）

```css
/* E4 包豪斯 · 装饰母题 */
.mt-bau-circle,.mt-bau-tri,.mt-bau-square{position:absolute;pointer-events:none;user-select:none}
.mt-bau-circle{border-radius:50%}
.mt-bau-tri{clip-path:polygon(50% 0,100% 100%,0 100%)}
.mt-bau-fill-accent{background:var(--accent)}
.mt-bau-fill-ink{background:var(--ink)}
.mt-bau-tint{background:color-mix(in srgb,var(--ink) 10%,transparent)}
.mt-bau-line{display:block;height:2px;background:var(--ink)}
```

- **禁忌**：基本形必须正圆/正三角/正方——禁椭圆、禁圆角矩形、禁任意多边形，形不真即背叛；每页 1–3 件成组构成不对称平衡，禁对称撒布当墙纸；accent 实色基本形单页至多一个（单焦点纪律）；母题件一律 `data-editable-skip`

**Variants 配色变体**

#### 原色黄

- **气质**：原色黄 + 墨黑，乐观明亮，教室里的构成练习——教育、儿童、科普、生活方式品牌

```css
--paper:#f4f0e4; --paper-tint:#e9e3d3;
--ink:#141412;   --ink-tint:#26241f;
--accent:#F2A600; --accent-on:#141412;
```

- **accent 预算**：黄底配深字（accent-on 用 ink）；满版黄封面投影场景注意亮度，正文页黄面积仍 ≤10%；其余同基底口径

#### 原色蓝

- **气质**：原色蓝 + 墨黑，冷静理性，最贴近瑞士邻居的一种光——科技、建筑、机构发布

```css
--paper:#f4f0e4; --paper-tint:#e9e3d3;
--ink:#141412;   --ink-tint:#26241f;
--accent:#0057A8; --accent-on:#f4f0e4;
```

### E5 构成主义 Constructivism

- **id**：e5
- **气质**：米纸 + 墨黑 + 革命红，对角线劈开版面的宣传画压强
- **适用**：宣言式发布、动员/号召、变革叙事、观点鲜明的演讲、需要鼓动性的场合
- **focus**：G9 + G5
- **世界参考**：苏联构成主义海报 1920s（Rodchenko、Lissitzky）——红黑石印两色、激进对角线、宣传口号式排版
- **unforgettable**：对角线切割——页面被一条粗对角色带劈开，文字沿对角排布，一眼宣传画
- **分化声明**：与 c1 分化于 L1/L4/L6/L7——e5 米纸底 + 革命红石印两色、c1 纯黑舞台 + 信号橙；e5 母题是对角切割带/粗黑横杠/阶梯错排、c1 是信号条/巨号页码/信号方块；e5 动效是 wipe-clip 硬切直进直出零过冲、c1 是 scale-pop 过冲回弹爆发曲线；e5 构图对角线亲和且禁水平垂直网格矩阵、c1 巨字宣言居中压场

**G1 color**

```css
--paper:#eadfc4; --paper-tint:#ddd0b0;
--ink:#171310;   --ink-tint:#2b241a;
--accent:#9E1B1E; --accent-on:#eadfc4;
```

- **accent 预算**：内容页 accent 面积 ≤15%（对角色带本身即面积——预算是给结构件的，比瑞士系宽，但单页至多一条红带/一个红色焦点）；满屏红仅封面宣言页特权（满版红 + 反白口号）；首尾闭环：封面满版红（全亮）开场 → 收束页红色对角带（半亮）呼应。

**G2 typography**

```css
--font-display:"Arial Black","PingFang SC","Noto Sans SC",sans-serif;
--font-body:"PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

- **字重倾向**：标题极粗 800–900、正文 400；口号即压强
- **字号对比**：主标题:正文 ≥8:1（低密度）；巨字特档 10:1（宣言页）；高密度 ≥5:1
- **字重映射**：反向立场（不走倒挂——极粗大写即宣传画）：标题恒重 800–900（≥35px 全档）；正文 400；14–16px 小字 500–600
- **标题修饰**：拉丁标题全大写；中文标题配粗黑横杠（`.mt-con-bar`）引导——口号式排版的原生语言

**G3 texture**

```css
--texture-type: grain;
--texture-layer: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='240' height='240'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='240' height='240' filter='url(%23n)' opacity='0.05'/%3E%3C/svg%3E");
--texture-scope: cover;
```

- **立场**：石印颗粒——仪式页铺轻颗粒，像油墨滚过石版；正文页纯纸面

**G4 shape**

- **圆角**：0
- **hairline**：不用——分区靠色带与对角切割，细线太文气
- **阴影**：无
- **容器造型**：无容器立场——色带与对角线即结构；内容直接落纸面或 ink/accent 纯色带内（反白字），禁描边卡、禁圆角、禁阴影、禁玻璃

**G5 motion**

- **气质**：dramatic
- **强度上限**：默认
- **锚点偏好**：wipe-clip 硬切（标题与色带沿对角方向切出）+ chars 逐字砸落（封面口号）；rise-in 硬位移（阶梯错排块逐级入场）；count-up 只给真正的 KPI 英雄数字
- **节奏偏移**：时长档 −1（急促）；阶梯步长 ≤50ms
- **缓动签名**：覆盖 `--ease-out` 为 cubic-bezier(.8,0,.2,1)——硬切急停，零过冲零回弹
- **禁用**：scale-pop / blur-in / mask-lines / gradient-flow（过冲回弹与一切柔化手段都与硬切立场冲突）
- **fx 许可**：全禁

**G8 component**

- **亲和**：裂屏对开（对角变体——裂屏线必须是斜的）、巨字宣言（口号式）、数据英雄（数字配粗横杠）
- **禁忌**：禁水平垂直网格矩阵连页——构成主义就是反网格的；轴与节点的时间轴/流程必须走对角或阶梯错排，禁水平直线轴；不用加号角标/网格点阵（瑞士系词汇）与 Ghost 残影字（杂志系词汇）

**G9 motif**

- **词汇**：对角切割带（`.mt-con-diag`——transform rotate 的宽色带横贯页面，accent 或 ink 实色，页面结构件而非点缀，每页至多一条）/ 粗黑横杠（`.mt-con-bar`——极粗短杠，标题强调与列表编号标记）/ 阶梯错排（文字块沿对角逐级错位——生成侧用 margin 阶梯落码，无类）

```css
/* E5 构成主义 · 装饰母题 + 缓动签名 */
:root{--ease-out:cubic-bezier(.8,0,.2,1)}
.mt-con-diag{position:absolute;left:-15%;width:130%;height:14vh;pointer-events:none;transform:rotate(-12deg);background:var(--accent)}
.mt-con-diag--ink{background:var(--ink)}
.mt-con-bar{display:inline-block;width:1.6em;height:.28em;background:var(--ink)}
.mt-con-bar--accent{background:var(--accent)}
```

- **禁忌**：对角带每页至多一条、角度全场统一（−12° 签名角）；对角带是结构件，禁缩小当装饰撒布；横杠只在标题/列表位；母题件一律 `data-editable-skip`

**Variants 配色变体**

#### 工业蓝

- **气质**：米纸 + 墨黑 + 工业蓝，五年计划与建设题材——工业、基建、工程、组织变革叙事

```css
--paper:#eadfc4; --paper-tint:#ddd0b0;
--ink:#171310;   --ink-tint:#2b241a;
--accent:#1E4E8C; --accent-on:#eadfc4;
```

#### 全墨

- **气质**：单色石印——米纸 + 墨黑两色印刷，最朴素也最锋利——档案、历史、极简宣言

```css
--paper:#eadfc4; --paper-tint:#ddd0b0;
--ink:#171310;   --ink-tint:#2b241a;
--accent:#171310; --accent-on:#eadfc4;
```

- **accent 预算**：accent 与 ink 同色——强调靠字重与对角结构，"满屏 accent"体现为满版墨底反白宣言页（封面/收束特权）；其余同基底口径

### E6 Memphis 孟菲斯

- **id**：e6
- **气质**：纯白底 + 墨黑粗描边 + 糖果色几何碎形，1980s Memphis 的戏谑与高能量
- **适用**：年轻消费品牌、活动发布、创意行业、教育科普、潮流零售、节庆营销
- **focus**：G9 + G5
- **世界参考**：1980s 孟菲斯设计小组（Ettore Sottsass 与米兰激进设计运动）——糖果色几何碎形、之字波浪线、彩纸屑撒布、黑白网格底的反叛平面语言
- **unforgettable**：彩纸屑撒布——圆点/三角/之字线几何碎形像庆祝彩纸撒在页面上，一眼 Memphis
- **分化声明**：与 d1 分化于 L2/L4/L5/L6——e6 是几何无衬线强字重对比（极粗标题对常规正文），d1 是圆体 500–600 的圆润轻盈（L2）；e6 母题是彩纸屑碎形/之字波浪线/粗描边，d1 是贴纸徽章/扇贝花边/奶油圆点（L4）；e6 容器是 2–3px 墨黑粗描边圆角卡 + accent 硬偏移投影，d1 是无描边大圆角 + 弥散软阴影（L5）；同为回弹缓动但参数错开（e6 cubic-bezier(.5,1.7,.4,1) 对 d1 (.34,1.56,.64,1)），且 e6 锚点是彩纸屑/卡片的 scale-pop 齐蹦 + magnetic 指针吸附，d1 是贴纸徽章单主角 Q 弹（L6）

**G1 color**

```css
--paper:#FFF8EE; --paper-tint:#FFE9C7;
--ink:#1A1A2E;   --ink-tint:#3A3A55;
--accent:#FF3DA5; --accent-on:#FFF8EE;
```

- **accent 预算**：内容页 accent 面积 ≤10%，且**彩纸屑碎形计入用量**（3–5 件/页即花掉大半预算，其余留给单强调）；满屏 accent 仅封面/收束的特权；首尾闭环：封面彩纸屑 + accent 色块开场 → 收束页同构图彩纸屑呼应。
- **多彩纪律**：单 accent 世界——多彩感用 accent + color-mix 明度阶梯（accent 55%/30% 对 paper 派生）+ ink 派生凑出"糖果罐"，禁引入第二种高饱和色；换糖果罐 = 换变体，不混罐。

**G2 typography**

```css
--font-display:"Futura","Century Gothic","PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;
--font-body:"PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

- **字重倾向**：几何无衬线强对比——标题 700–900 极粗，正文 400–500，字重差本身是装饰
- **字号对比**：主标题:正文 ≥8:1（低密度）；高密度 ≥5:1
- **字重映射**：极粗标题立场：≥77px→800；35–76px→700；正文 400；14–16px 小字 500–600
- **标题修饰**：无（装饰交给彩纸屑与之字线）

**G3 texture**

```css
--texture-type: flat;
--texture-layer: none;
--texture-scope: cover;
```

- **立场**：flat 即质感立场——孟菲斯是丝网印刷式的平涂世界，纸纹与颗粒都破坏糖果色的纯度

**G4 shape**

- **圆角**：8–16px 圆角，全套容器统一圆角语言
- **hairline**：不用细分割线——区隔靠 2–3px 墨黑粗描边或之字波浪线（G9），细线在粗描边世界里发虚
- **阴影**：禁弥散软阴影；唯一允许的"影"是 accent 硬偏移投影（`8px 8px 0` 平涂色块影，丝印套色错位的隐喻）
- **容器造型**：粗描边圆角卡——2–3px ink 描边 + 圆角 + 可选 accent 硬偏移投影；禁无描边色块卡、禁弥散阴影、禁玻璃拟态

**G5 motion**

- **气质**：playful
- **强度上限**：默认
- **锚点偏好**：scale-pop 是本命（彩纸屑碎形与粗描边卡弹跳入场）；magnetic 指针吸附亲和（徽章/按钮被光标吸住，±16px 上限不动）；其余元素 rise-in
- **节奏偏移**：时长档 −1（快，节庆的急切感）；阶梯步长 ≤60ms
- **缓动签名**：覆盖 `--ease-out` 为 cubic-bezier(.5,1.7,.4,1)——比 d1 的回弹更弹更闹，参数错开防撞
- **禁用**：typewriter / scramble（打字机是 techy 限定款，不属于糖果世界）
- **fx 许可**：全禁（彩纸屑撒布已是仪式层，canvas 粒子与之打架）

**G8 component**

- **亲和**：网格矩阵（粗描边圆角卡片阵是它的货架）、巨字宣言（极粗巨字 + 彩纸屑撒布，节庆感拉满）
- **禁忌**：禁 hairline 密集分割与直角硬朗构图；不用加号角标/网格点阵（瑞士系词汇）、不用 Ghost 残影/竖排题字条（杂志系词汇）；图表页保持粗描边 + 圆角 + 硬偏移投影，柱条可用 ≤8px 圆角

**G9 motif**

- **词汇**：彩纸屑碎形（`.mt-mem-confetti` 一组小几何形 absolute 撒布——圆点 + 三角 + 空心环，颜色在 accent / accent 明度阶梯 / ink 间轮换，**3–5 件/页克制撒布**）/ 之字波浪线（`.mt-mem-zig`：linear-gradient 折出的锯齿横带，替代一切直线分隔）/ 粗描边圆角卡（`.mt-mem-card`：3px ink 描边 + accent 硬偏移投影的签名容器）

```css
/* E6 Memphis 孟菲斯 · 装饰母题 + 缓动签名 */
:root{--ease-out:cubic-bezier(.5,1.7,.4,1)}
.mt-mem-confetti{position:absolute;inset:0;pointer-events:none;user-select:none;overflow:hidden}
.mt-mem-confetti i{position:absolute;display:block}
.mt-mem-dot{width:14px;height:14px;border-radius:50%;background:var(--accent)}
.mt-mem-tri{width:0;height:0;border-left:9px solid transparent;border-right:9px solid transparent;border-bottom:15px solid color-mix(in srgb,var(--accent) 55%,var(--paper))}
.mt-mem-ring{width:16px;height:16px;border:3px solid var(--ink);border-radius:50%}
.mt-mem-zig{height:12px;pointer-events:none;background-image:linear-gradient(135deg,var(--ink) 25%,transparent 25%),linear-gradient(225deg,var(--ink) 25%,transparent 25%);background-size:16px 12px;background-repeat:repeat-x}
.mt-mem-card{border:3px solid var(--ink);border-radius:14px;background:var(--paper);box-shadow:8px 8px 0 color-mix(in srgb,var(--accent) 85%,var(--ink))}
```

- **禁忌**：彩纸屑每页 3–5 件为上限，撒满即廉价；之字线每页至多一条、禁进数据图表区（干扰读数）；硬偏移投影只许 accent 色，禁 ink 色投影（与描边糊成一团）；母题件一律 `data-editable-skip`

**Variants 配色变体**

#### 电光蓝

- **气质**：糖果罐换成电光蓝——更冷更锐的孟菲斯，科技馆与极客活动感——科技产品、赛事、潮流数码

```css
--paper:#FFF8EE; --paper-tint:#FFE9C7;
--ink:#1A1A2E;   --ink-tint:#3A3A55;
--accent:#00B8D9; --accent-on:#1A1A2E;
```

- **accent 预算**：电光蓝明度高，accent-on 反深字（墨黑）才读得清；其余同基底口径

#### 柠檬黄

- **气质**：柠檬黄糖果罐——最闹最节庆的一罐，黑白网格底的经典孟菲斯海报感——节庆营销、儿童教育、活动邀请

```css
--paper:#FFF8EE; --paper-tint:#FFE9C7;
--ink:#1A1A2E;   --ink-tint:#3A3A55;
--accent:#FFD93D; --accent-on:#1A1A2E;
```

- **accent 预算**：柠檬黄明度最高——accent-on 必须反深字；硬偏移投影由 `.mt-mem-card` 的 color-mix(accent 85%, ink) 自动压暗，无需另处理；其余同基底口径

### E7 浮世绘

- **id**：e7
- **气质**：宣纸米底 + 墨线平涂 + 印泥红落款，浮世绘版画的平面秩序与东方余白
- **适用**：文化艺术、东方美学、展览与博物馆、品牌故事、茶/器物/旅行、人文叙事
- **focus**：G3 + G9
- **世界参考**：江户浮世绘版画（葛饰北斋《富岳三十六景》、歌川广重《东海道五十三次》）——平涂色面、细轮廓墨线、浪花云霞纹样、落款姓名印
- **unforgettable**：姓名印 + 浪花带——右下角一方印泥红底白字印章如画作的落款，页缘一条扇形浪纹压住版面
- **分化声明**：与 d3 分化于 L2/L4/L5/L6——e7 是宋体系衬线恒重字排，d3 是楷体手绘字排（L2）；e7 母题是姓名印/浪花带/云霞横带/竖排题跋的版画纹样，d3 是笔触块/虚线圈注/画框双描边的油画工艺——版画平涂与油画笔触是两个工艺世界（L4）；e7 容器是无框平涂色面 + 细墨线轮廓 + 直角，d3 是不规则有机圆角 + 零描边（L5）；同为 calm + draw-line，但 e7 节奏更仪式化（阶梯步长 ≥120ms 的套印节奏：一层色面落定再上下一层），d3 只慢半拍无步长纪律（L6）（L3 两者同为 paper+all，按规则不计入）

**G1 color**

```css
--paper:#F5EFE2; --paper-tint:#E9DFC9;
--ink:#23201B;   --ink-tint:#3D3A33;
--accent:#B03A2E; --accent-on:#F5EFE2;
```

- **accent 预算**：内容页 accent 面积 ≤5%——印泥红在浮世绘里是落款与点缀不是主色（姓名印一方 + 至多一处单强调）；**满屏 accent 禁止**——浮世绘的大色面是墨与纸的派生平涂（ink-tint / paper-tint 色面），红永远只是落款；首尾闭环：封面题字旁一方姓名印开场 → 收束页同位置印章呼应。

**G2 typography**

```css
--font-display:"Songti SC","Noto Serif SC","STSong",serif;
--font-body:"Songti SC","Noto Serif SC","STSong",serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

- **字重倾向**：全衬线恒重——标题 600–700、正文 400–500，层级靠字号差与墨的浓淡
- **字号对比**：主标题:正文 ≥8:1（低密度）；高密度 ≥5:1
- **字重映射**：全衬线恒重立场（不走倒挂——细衬线大字号发虚）：标题 600–700；正文 400–500；14–16px 小字 500–600
- **标题修饰**：竖排题跋条（见 G9 `.mt-uki-inscription`）——标题右侧一列竖排小字题跋是原生修饰，不另加

**G3 texture**

```css
--texture-type: paper;
--texture-layer: radial-gradient(90% 70% at 20% 15%, color-mix(in srgb, var(--ink) 3%, transparent), transparent 60%), radial-gradient(80% 70% at 80% 90%, color-mix(in srgb, var(--ink) 2%, transparent), transparent 65%);
--texture-scope: all;
```

- **立场**：宣纸纹理 = 材质本体——版画印在纸上，纸是这个世界的一部分，正文页也允许铺（scope all），但仍需生成侧逐页 `texture-on` 落码；强度烧死不得加深

**G4 shape**

- **圆角**：0——版画是方的世界，禁圆角卡
- **hairline**：1px solid color-mix(in srgb, var(--ink) 45%, transparent)，细墨线轮廓即版画骨法
- **阴影**：无——纸面世界不吃投影，层次靠平涂色面叠压与墨线勾勒
- **容器造型**：无框平涂色面 + 细墨线轮廓——分区靠 paper-tint/ink-tint 平涂色面与 1px 墨线描边；禁圆角、禁阴影、禁玻璃拟态、禁弥散

**G5 motion**

- **气质**：calm
- **强度上限**：低
- **锚点偏好**：draw-line 是签名锚点——墨线轮廓像被毛笔一笔勾出；文字入场 rise-in 轻上浮
- **节奏偏移**：时长档 +1，阶梯步长 ≥120ms——套印节奏：一层色面落定再上下一层，版画等得起
- **缓动签名**：默认三 token，不覆盖
- **禁用**：scale-pop / persp-in / typewriter / scramble（弹跳、透视与打字机都不属于版画）
- **fx 许可**：全禁（手工版画与数字粒子/字符场冲突）

**G7 illustration**

- **风格**：浮世绘平涂版画——平涂色面、粗墨轮廓线、浪/云/山纹样、限色套印、宣纸底
- **提示词种子**：ukiyo-e woodblock print, flat color planes, bold black outlines, wave and cloud patterns, limited palette, washi paper texture
- **禁忌**：不用照片级写实、不用渐变柔光、不用 3D 渲染与高饱和数码色

**G8 component**

- **亲和**：图文证据（画 + 题跋 = 浮世绘的原生版式）、巨字宣言（封面题字 + 印章落款，画册封面的仪式感）
- **禁忌**：禁网格矩阵密集排布（版画的秩序是中轴与余白不是货架网格）；裂屏对开慎用——版画画幅是完整一张；图表须以墨线轮廓与平涂色面收编，禁终端/信号词汇

**G9 motif**

- **词汇**：姓名印（`.mt-uki-seal`：accent 实色小方块 + 反白篆意字，右下角落款位，每页至多一方）/ 浪花带（`.mt-uki-wave`：repeating radial-gradient 半圆鳞片浪纹条，只许页缘一条横贯）/ 云霞横带（`.mt-uki-cloud`：两条错位的断续横带，区段分隔的霞光）/ 竖排题跋条（`.mt-uki-inscription`：标题右侧竖排小字，文本载体类母题）

```css
/* E7 浮世绘 · 装饰母题 */
.mt-uki-seal{display:inline-flex;align-items:center;justify-content:center;width:2.4em;height:2.4em;background:var(--accent);color:var(--accent-on);font-family:var(--font-display);font-weight:700;font-size:.5em;line-height:1.15;text-align:center;writing-mode:vertical-rl;letter-spacing:.08em;box-shadow:inset 0 0 0 1.5px color-mix(in srgb,var(--accent-on) 40%,transparent)}
.mt-uki-wave{height:26px;pointer-events:none;user-select:none;background-image:radial-gradient(circle at 13px 26px,transparent 9px,color-mix(in srgb,var(--ink) 55%,transparent) 9px 10.5px,transparent 10.5px),radial-gradient(circle at 13px 26px,transparent 4px,color-mix(in srgb,var(--ink) 55%,transparent) 4px 5.5px,transparent 5.5px);background-size:26px 26px;background-repeat:repeat-x}
.mt-uki-cloud{height:10px;pointer-events:none;user-select:none;background-image:repeating-linear-gradient(90deg,color-mix(in srgb,var(--accent) 70%,var(--paper)) 0 60px,transparent 60px 88px),repeating-linear-gradient(90deg,color-mix(in srgb,var(--ink) 25%,transparent) 0 34px,transparent 34px 88px);background-position:0 0,14px 5px;background-size:88px 4px,88px 4px;background-repeat:repeat-x}
.mt-uki-inscription{writing-mode:vertical-rl;font-family:var(--font-display);font-size:.5em;letter-spacing:.35em;color:color-mix(in srgb,var(--ink) 70%,transparent);border-left:1px solid color-mix(in srgb,var(--ink) 40%,transparent);padding-left:.6em}
```

- **禁忌**：姓名印每页至多一方、只许右下角/题跋末尾的落款位（多方印即画蛇添足）；浪花带只许页面上缘或下缘一条横贯，禁进图表区；云霞横带只许区段分隔，禁与浪花带同页（浪与霞不同页）；`.mt-uki-inscription` 是文本载体类母题——样式由类承担，文本保持可编辑；其余母题件一律 `data-editable-skip`

**Variants 配色变体**

#### 北斋蓝

- **气质**：普鲁士蓝（ベロ藍）入画——《神奈川冲浪里》的蓝浪世界，冷静、深邃、构图感最强——海洋、旅行、设计史、沉静叙事

```css
--paper:#F5EFE2; --paper-tint:#E9DFC9;
--ink:#23201B;   --ink-tint:#3D3A33;
--accent:#2B4B6F; --accent-on:#F5EFE2;
```

- **accent 预算**：蓝变体的 accent 是主役色而非落款色——内容页面积放宽至 ≤10%（浪花带/色面可用 accent 派生），姓名印保持 accent 实色不变；满屏仍禁止

#### 藤紫

- **气质**：藤紫落款——平安贵族色的余韵，比红更幽更文——文学、香道花道、雅集、女性向文化品牌

```css
--paper:#F5EFE2; --paper-tint:#E9DFC9;
--ink:#23201B;   --ink-tint:#3D3A33;
--accent:#7A5C8E; --accent-on:#F5EFE2;
```

### E8 号外报纸

- **id**：e8
- **气质**：纸白 + 油墨黑 + 号外红，超粗黑标题压顶、通栏粗细双线、多栏小字的新闻冲击力
- **适用**：新闻/资讯/时事评论、数据简报与行业观察、战报式项目汇报、危机通报、复古 editorial 叙事
- **focus**：G2 + G9
- **世界参考**：黑白小报与"号外"传单——报头徽标、通栏粗细分栏线、三栏小字正文、满版超粗黑标题的新闻纸
- **unforgettable**：号外版式——满版超粗黑标题压顶 + 通栏粗细双线 + 多栏小字正文，一张纸撑起的街头新闻冲击
- **分化声明**：与 c4 分化于 L2/L4/L7——c4 是全衬线恒重的书籍排版（宋体标题 + 宋体正文）、母题是题花/首字下沉/引文拉页、禁忌网格矩阵（书页靠栏不靠格）；e8 是 display 极粗无衬线黑体（Arial Black 系）+ body 报宋衬线的报馆字排、母题是通栏粗细双线/报头条/三栏容器、网格矩阵（多栏即网格）是原生亲和

**G1 color**

```css
--paper:#f4f1ea; --paper-tint:#e8e4da;
--ink:#111111;   --ink-tint:#232323;
--accent:#C8102E; --accent-on:#fdf9f4;
```

- **accent 预算**：内容页 accent 面积 ≤5%（号外红只给：报头日期线、单条通栏规则、关键数据角标——报纸一天只有一个头条）；满屏 accent 仅封面"号外"页且宜半版（上半红底反白巨标 + 下半纸白多栏）；首尾闭环：号外红报头开场 → 收束页红色通栏粗细线呼应。

**G2 typography**

```css
--font-display:"Arial Black","Impact","SimHei","PingFang SC","Noto Sans SC",sans-serif;
--font-body:"Georgia","Times New Roman","Songti SC","SimSun",serif;
--font-mono:"Consolas","Courier New","SF Mono",monospace;
```

- **字重倾向**：display 极粗恒重（800–900 黑到底），body 400 衬线小字——冲击力来自字重两极与栏密度，不是中间档
- **字号对比**：主标题:正文 ≥8:1（低密度；号外头条 ≥10:1，封面可冲 12:1）；高密度 ≥5:1
- **字重映射**：极粗黑体立场（不走倒挂——报头越黑越有冲击）：≥77px→800–900；35–76px→800；正文 400；14–16px 栏内小字 400–500；图注/署名 mono 400
- **标题修饰**：拉丁头条全大写；标题下通栏粗细双线（G9 `.mt-news-rule`）

**G3 texture**

```css
--texture-type: paper;
--texture-layer: radial-gradient(85% 60% at 15% 8%, color-mix(in srgb, var(--ink) 4%, transparent), transparent 60%);
--texture-scope: cover;
```

- **立场**：轻新闻纸纹——仪式页纸色微沉一角，阅读页保持干净（报纸的质感在纸色本身与栏密度，不靠叠加层）

**G4 shape**

- **圆角**：0
- **hairline**：通栏粗细双线（3px 粗 + 1px 细）做报头下与栏间分隔，是版面骨架；栏内次级分隔用 1px solid color-mix(in srgb, var(--ink) 25%, transparent)
- **阴影**：无
- **容器造型**：无卡片立场——多栏即容器：CSS columns 分栏文本 + column-rule 细栏线分区；图证用 1px 黑框 + 图注栏线；禁圆角卡、禁阴影、禁弥散渐变、禁描边装饰框

**G5 motion**

- **气质**：professional
- **强度上限**：默认
- **锚点偏好**：wipe-clip 硬切揭示为签名锚点（标题/通栏线——报纸的动效是"付印"般的利落）；章节页 mask-lines 头条逐行显影；数字以超大字重直排为主，count-up 只给数据简报英雄页
- **节奏偏移**：时长档 −1（快，付印节奏）；阶梯步长 ≤60ms
- **缓动签名**：默认三 token，不覆盖
- **禁用**：scale-pop / blur-in / typewriter / scramble（弹跳、柔焦、打字机都不属于报纸）
- **fx 许可**：全禁（新闻纸无像素仪式）

**G8 component**

- **亲和**：网格矩阵（多栏即网格——栏是它的原生单位，与 c4 的书页立场正好对立）、巨字宣言（号外头条）、数据英雄（头版大数字 + 栏线收编）
- **禁忌**：禁圆角柔和组件与渐变卡片；裂屏对开仅限"号外"封面（上红下纸半版对开）；图表收编为"新闻图表"——1px 黑框 + mono 图注，禁彩色圆角图表卡；不用题花/首字下沉（那是书籍词汇，c4 专属）

**G9 motif**

- **词汇**：通栏粗细双线（`.mt-news-rule`：3px 粗 + 1px 细的 thick-thin rule，报头下与栏间的"印刷规则"，每页 ≤2 条）/ 报头徽标条（`.mt-news-mast`：mono 大写报名 + 日期/期号分列左右，上下细线夹住，只许封面/收束）/ 三栏文本容器（`.mt-news-cols`：CSS columns + column-rule 细栏线，栏数 2–4 烧死）/ 斜切引文块（`.mt-news-pull`：衬线斜体通栏大引文，上粗线 + 下细线夹住）

```css
/* E8 号外报纸 · 装饰母题 */
.mt-news-rule{height:5px;border:none;border-top:3px solid var(--ink);border-bottom:1px solid var(--ink)}
.mt-news-mast{display:flex;align-items:baseline;justify-content:space-between;gap:1.2em;padding:.55em 0;border-top:1px solid var(--ink);border-bottom:1px solid var(--ink);font-family:var(--font-mono);font-size:12px;letter-spacing:.26em;text-transform:uppercase}
.mt-news-cols{columns:3;column-gap:2.2em;column-rule:1px solid color-mix(in srgb,var(--ink) 22%,transparent);text-align:justify}
.mt-news-pull{border-top:3px solid var(--ink);border-bottom:1px solid var(--ink);padding:.7em 0;font-family:var(--font-body);font-style:italic;font-size:1.45em;line-height:1.6}
```

- **禁忌**：粗细双线每页 ≤2 条（通栏规则是版面骨架不是撒布）；三栏容器只装真实正文，禁栏内塞卡片；`.mt-news-cols`/`.mt-news-pull` 为文本载体类母题（样式由类承担，文本保持可编辑），其余母题件一律 `data-editable-skip`

**Variants 配色变体**

#### 财经蓝

- **气质**：号外红换藏蓝——从街头号外走进金融版，权威、克制、数据感——财报、行业研报、机构简报

```css
--paper:#f4f1ea; --paper-tint:#e8e4da;
--ink:#111111;   --ink-tint:#232323;
--accent:#1E3A6E; --accent-on:#f4f1ea;
```

#### 泛黄旧报

- **气质**：旧报纸泛黄 + 墨褐标题——档案馆里的合订本，年代感与史料感——历史回顾、编年叙事、纪念专题

```css
--paper:#ece2c6; --paper-tint:#ded2b2;
--ink:#241d14;   --ink-tint:#352a1c;
--accent:#6B4A2F; --accent-on:#f0e8d2;
--texture-layer: radial-gradient(60% 50% at 20% 15%, color-mix(in srgb, var(--accent) 8%, transparent), transparent 60%), radial-gradient(70% 60% at 80% 90%, color-mix(in srgb, var(--ink) 6%, transparent), transparent 65%);
```

- **accent 预算**：墨褐饱和度低，礼仪性使用口径不变（≤5%）；"号外"封面的满版特权改为半版旧化晕染；其余同基底口径

### E9 地质地层

- **id**：e9
- **气质**：白昼大地剖面——纸米底上铺开赭石层理与等高线，像摊开一张地质调查图：精确、沉稳、有岩石的时间厚度
- **适用**：地质/考古/历史纵深、组织架构与层级、演进与成因类内容，研究型叙事，自然与人文地理
- **focus**：G3 + G9
- **世界参考**：地质调查剖面图与岩芯样本档案——层理条纹、地质年代色标、等高线圈、钻孔取出的岩芯圆柱
- **unforgettable**：层理色带——页面底缘（或侧缘）横贯一条大地色水平层理带，层厚可对应数据比例，是层级/组成内容的天然隐喻（与 references/motifs.md「地层剖面」隐喻同构）
- **分化声明**：与 a1 分化于 L2/L4/L5/L7——e9 是 sans display + mono 标注的科学绘图字排、a1 是衬线杂志字排；e9 母题是层理色带/岩芯样本条/等高线圈、a1 是 Ghost 巨字/竖排题字条；e9 容器是直角薄色层剖面切片、a1 是无卡片立场；e9 构图亲和轴与节点与地层剖面隐喻、a1 亲和巨字宣言（L1 与 a1 沙丘变体同为大地调，但本声明对 a1 基底核验——基底是墨黑双色，四层全真）

**G1 color**

```css
--paper:#f0e9d8; --paper-tint:#e3d9c3;
--ink:#2c251d;   --ink-tint:#413729;
--accent:#a85a2a; --accent-on:#f0e9d8;
```

- **accent 预算**：内容页 accent 面积 ≤10%（赭石只给测绘关键标注：地层界线、岩芯主层段、年代标尺当前段、关键数字；层理色带的大面积色层用 accent/ink 向 paper 的 color-mix 淡阶，不计入预算）；满屏 accent 禁止——大地没有荧光时刻，封面/收束的特权形态是层理色带加高至页底 30%；首尾闭环：封面底部厚层理色带开场 → 收束页同层序薄色带呼应。

**G2 typography**

```css
--font-display:"Avenir Next","Helvetica Neue","PingFang SC","Noto Sans SC",sans-serif;
--font-body:"PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;
--font-mono:"JetBrains Mono","SF Mono","Menlo",monospace;
```

- **字重倾向**：标题 600–700、正文 400——科学绘图的权威来自标注体系的清晰，不靠细字的优雅
- **字号对比**：主标题:正文 ≥8:1（低密度）；高密度 ≥5:1
- **字重映射**：sans 恒重立场（不走倒挂——图签标题要立得住）：≥77px→600–700；35–76px→600；正文 400；14–16px 小字 500–600
- **标题修饰**：无（修饰交给 mono 年代标注与等高线，不进标题）

**G3 texture**

```css
--texture-type: grain;
--texture-layer: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='240' height='240'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='240' height='240' filter='url(%23n)' opacity='0.05'/%3E%3C/svg%3E");
--texture-scope: all;
```

- **立场**：岩石颗粒 = 材质本体——切片、岩芯、断口全是颗粒，全页许可（scope all）；正文页仍需生成侧逐页 `.texture-on` 落码，强度烧死不得加深（颗粒是岩石，不是沙暴）

**G4 shape**

- **圆角**：0（岩层是切出来的，一刀切齐）
- **hairline**：1px solid color-mix(in srgb, var(--ink) 28%, transparent)，承担地层界线与图廓线——线在这个主题里是测绘工具，不是装饰
- **阴影**：无
- **容器造型**：剖面切片——直角薄色层容器（paper-tint 或 accent color-mix 淡阶的纯色薄层，像从剖面上切下的一片地层），顶缘可压 2px accent 界线作"地表线"；禁圆角、禁阴影、禁玻璃拟态、禁描边装饰框

**G5 motion**

- **气质**：calm
- **强度上限**：低
- **锚点偏好**：draw-line 为签名锚点——等高线与地层界线的测绘描绘感，剖面图页/年代轴页优先；标题入场用默认阶梯或 rise-in，克制
- **节奏偏移**：时长档 +1（地质时间的尺度，急不得）；阶梯步长 ≥90ms
- **缓动签名**：默认三 token，不覆盖
- **禁用**：无（calm 气质本身排除弹跳与硬切）
- **fx 许可**：全禁（canvas 仪式层是夜空与终端的词汇，白昼大地剖面不点灯）

**G8 component**

- **亲和**：轴与节点（地质年代轴/演进——年代标尺是它的原生形态）、层级与组成内容（层理色带 = 地层剖面隐喻，与 motifs.md 同构）、图文证据（标本/剖面图 + 测绘标注）
- **禁忌**：禁圆角卡片阵与弥散阴影（那是奶油系词汇）；巨字宣言慎用——图鉴版面靠测绘精度建立权威，不靠巨字压场

**G9 motif**

- **词汇**：层理色带（`.mt-geo-strata`：页底或侧缘横贯的大地色水平层理带，色层从 accent/ink/paper-tint 用 color-mix 派生大地阶梯，层厚比例由生成侧按数据调整 gradient 断点）/ 岩芯样本条（`.mt-geo-core`：竖向圆柱感色条 = 年代标尺，分段色对应地质年代，段界比例由生成侧调整）/ 等高线圈（`.mt-geo-contour`：细线同心闭合曲线，低透明背景装饰，只许页角与留白区）/ 年代标注签（`.mt-geo-tag`：mono 小字 + accent 短横引线，标注年代/层位/海拔）

```css
/* E9 地质地层 · 装饰母题 */
.mt-geo-strata{position:absolute;left:0;right:0;bottom:0;height:10%;pointer-events:none;border-top:1px solid color-mix(in srgb,var(--ink) 34%,transparent);background:linear-gradient(180deg,color-mix(in srgb,var(--accent) 28%,var(--paper)) 0 24%,color-mix(in srgb,var(--ink) 14%,var(--paper)) 24% 42%,color-mix(in srgb,var(--accent) 48%,var(--paper)) 42% 55%,var(--paper-tint) 55% 78%,color-mix(in srgb,var(--ink) 30%,var(--paper)) 78%)}
.mt-geo-core{width:20px;border-radius:10px;border:1px solid color-mix(in srgb,var(--ink) 32%,transparent);background:linear-gradient(180deg,color-mix(in srgb,var(--accent) 62%,var(--paper)),color-mix(in srgb,var(--accent) 26%,var(--paper)) 38%,color-mix(in srgb,var(--ink) 18%,var(--paper)) 62%,color-mix(in srgb,var(--ink) 40%,var(--paper)))}
.mt-geo-contour{position:absolute;pointer-events:none;width:340px;height:340px;border-radius:50%;opacity:.5;background:repeating-radial-gradient(circle at 50% 50%,transparent 0 27px,color-mix(in srgb,var(--ink) 20%,transparent) 27px 28px)}
.mt-geo-tag{display:inline-flex;align-items:center;gap:.6em;font-family:var(--font-mono);font-size:12px;letter-spacing:.2em;color:color-mix(in srgb,var(--ink) 66%,transparent)}
.mt-geo-tag::before{content:"";width:14px;height:1px;background:var(--accent)}
```

- **禁忌**：层理色带每页至多一条（页底或侧缘二选一，横放），禁压正文；等高线圈禁横穿正文区、禁与岩芯条同页抢焦；岩芯条只许年代/层级语义处，禁当纯装饰撒布；母题件一律 `data-editable-skip`

**Variants 配色变体**

#### 岩灰蓝

- **气质**：灰蓝色调的石灰岩与页岩层——更冷、更克制，像阴天野外的测绘现场，适合工程/基建/数据基础设施叙事

```css
--paper:#eeebdf; --paper-tint:#e1dcc9;
--ink:#2c2b26;   --ink-tint:#403e35;
--accent:#5f7482; --accent-on:#eeebdf;
```

#### 红土

- **气质**：红土高原与氧化铁层——更暖、更荒原，适合考古/文明/迁徙/远征类叙事

```css
--paper:#f2e6d2; --paper-tint:#e5d6ba;
--ink:#2e211a;   --ink-tint:#453024;
--accent:#a63f2a; --accent-on:#f2e6d2;
```

- **accent 预算**：红土红与层理色带同属暖域，色带淡阶与 accent 标注的明度差要拉大（淡阶混色 ≤35%），其余同基底口径

### E10 星图

- **id**：e10
- **气质**：深夜蓝天球上，银白星点以金色虚线缝成星座——浩瀚、精确，有观星手册的浪漫
- **适用**：愿景/战略/路线图、关系图谱与生态位叙事、科技与人文交叉主题，晚间发布与沉浸暗场
- **focus**：G9 + G5
- **世界参考**：古典星图与观星手册（Uranometria 以降的天球测绘传统）——深蓝夜空、实星点+虚线连线的星座、黄道坐标网格、星等符号与坐标注记
- **unforgettable**：星座连线——几颗亮星以 1px 虚线缝成星座，旁缀斜体星名与 mono 星等注记；"把内容要点连成星座"是天然的关系隐喻
- **分化声明**：与 d2 分化于 L3/L4/L5/L6/L7——e10 质感是极轻 grain 夜空底噪、d2 是 glow 显影辉光；e10 母题是星座连线/黄道坐标网格/星等注记、d2 是胶片齿孔/光束角标/显影晕；e10 容器是无框 + 虚线连线结构（禁辉光托底）、d2 无框只靠辉光托底；e10 签名动效是 draw-line 连线成星座 + fx 仪式层本命、d2 是 blur-in 显影浮出；e10 构图亲和轴与节点（星座=节点连线）、d2 亲和裂屏对开（L2 同为暗场衬线偏细，拉开靠后五层，全真）

**G1 color**

```css
--paper:#0b1426; --paper-tint:#152138;
--ink:#dfe7f2;   --ink-tint:#1d2c47;
--accent:#e8b64c; --accent-on:#0b1426;
```

- **accent 预算**：内容页 accent 面积 ≤5%（金黄是星光——只给亮星、星座连线、星等注记与关键数字，禁大块铺色）；满屏 accent 禁止（夜空永不天亮，封面仪式感靠星座与 fx 星场而非满色）；首尾闭环：封面主星座开场 → 收束页同一星座再现（或黄道金光带呼应）。

**G2 typography**

```css
--font-display:"Songti SC","Noto Serif SC","STSong",serif;
--font-body:"PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

- **字重倾向**：标题 400–500 偏细、正文 400——深空衬线偏细更透，层级靠字距与排布，不靠字重压强
- **字号对比**：主标题:正文 ≥8:1（低密度；夜空巨字特档 10:1 仅封面宣言页）；高密度 ≥5:1
- **字重映射**：衬线偏细立场：≥77px→400；35–76px→400–500；正文 400；14–16px 小字 500
- **标题修饰**：加宽字距（letter-spacing ≥.08em，星图题铭传统）；标题旁可缀 mono 坐标注记（`.mt-star-mag`）；斜体只属于星名（`.mt-star-name`），不进标题本体

**G3 texture**

```css
--texture-type: grain;
--texture-layer: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='240' height='240'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='240' height='240' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
--texture-scope: cover;
```

- **立场**：极轻颗粒 = 夜空底噪——仪式页深空铺一层微弱颗粒；正文页保持纯净星场（星点交给母题与 fx 仪式层）；与 d2 划界：星图没有显影灯，glow 禁入

**G4 shape**

- **圆角**：0（天球仪的经纬是测绘线，容器不磨圆）
- **hairline**：不用实线分割——分组与引导用 1px dashed color-mix(in srgb, var(--ink) 30%, transparent) 虚线（坐标引线与星座连线同一种语言）
- **阴影**：无；唯一允许的光是星点自身辉光（`.mt-star-dot`），禁对容器施辉光
- **容器造型**：无框 + 虚线连线结构——内容悬浮于星空，分区靠坐标网格与虚线连线；禁实色卡、禁描边实框、禁辉光托底（辉光托底是 d2 暗房词汇，这是两主题 L5 的分界）

**G5 motion**

- **气质**：calm
- **强度上限**：默认（calm 档内——深空不疾不徐）
- **锚点偏好**：draw-line 为签名锚点——虚线描绘即连线成星座，关系图谱页/路线图页优先；标题入场 rise-in 或默认阶梯；count-up 只给真正的 KPI 英雄数字
- **节奏偏移**：时长档 +1（观星是慢的仪式）；阶梯步长 ≥90ms
- **缓动签名**：默认三 token，不覆盖
- **禁用**：scale-pop / scramble（弹跳与字符噪点破坏夜空）
- **fx 许可**：constellation / starfield / particle-drift 全开——本库第一个 fx 本命主题：星座与星空本来就是这个世界（ascii-field 禁——字符场是终端词汇）；fx 仍只许封面/收束仪式页，每页至多 1 个

**G8 component**

- **亲和**：轴与节点（星座 = 节点连线，关系/演进内容的原生形态）、巨字宣言（夜空巨字 + 星场，本主题的封面仪式感）、图文证据（星图 + 星名注记）
- **禁忌**：禁密集网格矩阵（星空不是表格——网格语言只许黄道坐标网格一种）；数据英雄页保持大留白，图表以 accent 单系列描线为主；裂屏对开慎用（天球是整一的）

**G9 motif**

- **词汇**：星座件（`.mt-star-dot` 星点：小圆点 + 十字星芒，自带微弱辉光；`.mt-star-link` 连线：1px dashed 线段，宽度与 rotate 由生成侧按星点间距定位——两个类组合使用，把内容要点缝成星座）/ 黄道坐标网格（`.mt-star-grid`：细经纬直线网格，低透明背景层，只许仪式页与图版区）/ 斜体星名（`.mt-star-name`：衬线 italic 小注，古典星图的签名）/ 星等注记（`.mt-star-mag`：mono 小字标注星等/坐标/编号）

```css
/* E10 星图 · 装饰母题 */
.mt-star-dot{position:absolute;width:5px;height:5px;border-radius:50%;background:var(--ink);box-shadow:0 0 6px color-mix(in srgb,var(--accent) 60%,transparent)}
.mt-star-dot::before,.mt-star-dot::after{content:"";position:absolute;left:50%;top:50%;background:color-mix(in srgb,var(--ink) 80%,transparent)}
.mt-star-dot::before{width:13px;height:1px;transform:translate(-50%,-50%)}
.mt-star-dot::after{width:1px;height:13px;transform:translate(-50%,-50%)}
.mt-star-link{position:absolute;height:0;border-top:1px dashed color-mix(in srgb,var(--accent) 55%,transparent);transform-origin:left center;pointer-events:none}
.mt-star-grid{position:absolute;inset:0;pointer-events:none;opacity:.5;background:repeating-linear-gradient(0deg,transparent 0 47px,color-mix(in srgb,var(--ink) 10%,transparent) 47px 48px),repeating-linear-gradient(90deg,transparent 0 47px,color-mix(in srgb,var(--ink) 10%,transparent) 47px 48px)}
.mt-star-name{font-family:var(--font-display);font-style:italic;letter-spacing:.06em;color:color-mix(in srgb,var(--ink) 75%,transparent)}
.mt-star-mag{font-family:var(--font-mono);font-size:11px;letter-spacing:.22em;color:color-mix(in srgb,var(--ink) 52%,transparent)}
```

- **禁忌**：星座件是关系图式不是撒星——每页星座 ≤1 组（3–7 颗星），星点禁无连线空挂（孤星不是星座）；坐标网格禁进正文阅读区；母题件一律 `data-editable-skip`（`.mt-star-name`/`.mt-star-mag` 承载真实星名/坐标文本时除外——样式由类承担，文本保持可编辑）

**Variants 配色变体**

#### 星云紫

- **气质**：银河深处的星云紫调——更神秘、更内省，适合 AI/深科技/哲学与宇宙学叙事

```css
--paper:#100c22; --paper-tint:#1a1433;
--ink:#e2dcf2;   --ink-tint:#261d47;
--accent:#9b7fd4; --accent-on:#100c22;
```

#### 极夜蓝白

- **气质**：极夜下的蓝白星光——最冷、最素，接近天文台观测记录纸，适合科研/数据/天文与极地叙事

```css
--paper:#0a111c; --paper-tint:#131e2d;
--ink:#e8eef5;   --ink-tint:#1b2939;
--accent:#cfe0f0; --accent-on:#0a111c;
```

- **accent 预算**：蓝白 accent 与 ink 近色——点状纪律不变，强调靠明度差与连线结构而非色相；其余同基底口径

### E11 票据

- **id**：e11
- **气质**：纸白票纸 + 墨黑字段 + 航司蓝 accent，登机牌与票根的工业浪漫与出发感
- **适用**：旅行与出行、活动票务、产品发布（"启程/上线"叙事）、物流交通行业、流程与清单型内容
- **focus**：G9 + G2
- **世界参考**：航空登机牌与演出票根（IATA 登机牌 / 热敏纸演出票）——撕线齿孔、条码、mono 大写字段、副券存根
- **unforgettable**：撕线副券——一条齿孔虚线把页面撕出主券/副券，条码压底，一眼登机牌
- **分化声明**：与 c3 分化于 L1/L2/L3/L4/L6——e11 是纸白浅底的票纸世界，c3 是暗底磷光屏（L1）；e11 的 mono 只用于字段标签与票据数据（正文用黑体），c3 是全栈等宽（L2）；e11 是 flat 干净票纸，c3 是 CRT 扫描线 grain/all（L3）；e11 母题是齿孔撕线/条码/副券字段行，c3 是 ASCII 框/闪烁光标/提示符（L4）；e11 签名动效是 wipe-clip 撕开式揭示，c3 是 typewriter/scramble 打字机（L6）

**G1 color**

```css
--paper:#FDFCF9; --paper-tint:#F2F0E8;
--ink:#1D2129;   --ink-tint:#3A3F4A;
--accent:#0F4C81; --accent-on:#FDFCF9;
```

- **accent 预算**：内容页 accent 面积 ≤8%——蓝只给：头带横条、关键字段值（班次/座位号/日期）、条码上方一行字；封面/收束允许 accent 头带横贯版面上缘（≤30%，登机牌头带是它的原生形态），不满屏；首尾闭环：封面头带 + 条码开场 → 收束页同位头带 + 条码呼应。

**G2 typography**

```css
--font-display:"Arial Black","Avenir Next Heavy","PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;
--font-body:"PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

- **字重倾向**：display 700–900 极粗无衬线、正文 400–500 黑体；mono 字段 500–700 + 大写 + 加宽字距——票据的层级是"字段纪律"而非字体重量游戏
- **字号对比**：主标题:正文 ≥8:1（低密度）；高密度 ≥5:1
- **字重映射**：极粗标题立场：≥77px→800；35–76px→700；正文 400；14–16px 小字 500–600
- **标题修饰**：mono 小号大写字段行压题（LABEL / VALUE 对，见 G9 `.mt-tix-field`）——标题上方一行 "FLIGHT / PPTX-0926" 式字段是原生修饰

**G3 texture**

```css
--texture-type: flat;
--texture-layer: none;
--texture-scope: cover;
```

- **立场**：flat 即质感立场——登机牌是热敏打印的工业纸面，纹理交给齿孔与条码的几何节奏，纸纹多余

**G4 shape**

- **圆角**：0–4px（票据是工业切片，几乎不用圆角）
- **hairline**：1px solid color-mix(in srgb, var(--ink) 30%, transparent)，字段分隔线即票面框线
- **阴影**：无——票纸是平的，禁弥散投影
- **容器造型**：票据容器——1px 描边 + 齿孔分隔（`.mt-tix-perf`）+ 副券区（`.mt-tix-stub` 淡 accent 底）；禁圆角大卡、禁弥散阴影、禁玻璃拟态

**G5 motion**

- **气质**：professional
- **强度上限**：默认
- **锚点偏好**：wipe-clip 是签名锚点——撕开的揭示感，副券与字段像被撕出来；数据页 fill-bar 亲和（登机进度条隐喻）；其余元素 rise-in
- **节奏偏移**：不偏移；阶梯步长 ≤60ms（值机柜台的高效节奏）
- **缓动签名**：默认三 token，不覆盖
- **禁用**：scale-pop / magnetic / typewriter / scramble（弹跳吸附与打字机都不属于票纸——mono 字段直接落位，不打字）
- **fx 许可**：全禁（票面是印刷品，无仪式层）

**G8 component**

- **亲和**：轴与节点（航线/时刻 = 行程时间线的原生隐喻）、网格矩阵（值机柜台式字段阵列）、数据英雄（航班号/座位号式 mono 大数字）
- **禁忌**：不用竖排题字条/Ghost 残影（杂志系词汇）、不用圆角弥散卡（奶油系词汇）；裂屏对开慎用——票据是单张连续票面，对开请用主券/副券撕线代替

**G9 motif**

- **词汇**：齿孔撕线（`.mt-tix-perf`：dashed 虚线 + 两端半圆缺口，把票面撕出主券/副券，每页至多一条）/ 条码（`.mt-tix-barcode`：repeating-linear-gradient 粗细交替竖条，只许页底一条横贯）/ 票根字段行（`.mt-tix-field`：mono 大写小字 LABEL/VALUE 对，文本载体类母题）/ 副券区（`.mt-tix-stub`：淡 accent 底 + 左描边的存根区）

```css
/* E11 票据 · 装饰母题 */
.mt-tix-perf{position:relative;border-top:2px dashed color-mix(in srgb,var(--ink) 50%,transparent)}
.mt-tix-perf::before,.mt-tix-perf::after{content:"";position:absolute;top:-10px;width:20px;height:20px;border-radius:50%;background:var(--paper)}
.mt-tix-perf::before{left:-10px}
.mt-tix-perf::after{right:-10px}
.mt-tix-barcode{height:44px;pointer-events:none;user-select:none;background-image:repeating-linear-gradient(90deg,var(--ink) 0 2px,transparent 2px 5px,var(--ink) 5px 6px,transparent 6px 11px,var(--ink) 11px 14px,transparent 14px 17px,var(--ink) 17px 18px,transparent 18px 23px)}
.mt-tix-field{font-family:var(--font-mono);text-transform:uppercase;letter-spacing:.08em;line-height:1.4}
.mt-tix-field small{display:block;font-size:.55em;font-weight:500;color:color-mix(in srgb,var(--ink) 55%,transparent);letter-spacing:.18em}
.mt-tix-field b{font-weight:700;color:var(--ink)}
.mt-tix-stub{background:color-mix(in srgb,var(--accent) 8%,var(--paper));border-left:1px solid color-mix(in srgb,var(--ink) 35%,transparent);padding:1em 1.2em}
```

- **禁忌**：齿孔撕线每页至多一条（横竖皆可，只一条——撕两次票就废了）；条码只许页底一条横贯，禁进图表区、禁竖放；字段行 LABEL 永远大写 mono，禁中文进 LABEL 位（中文进 VALUE）；`.mt-tix-field` 是文本载体类母题——样式由类承担，文本保持可编辑；`.mt-tix-perf`/`.mt-tix-barcode` 一律 `data-editable-skip`

**Variants 配色变体**

#### 铁路绿

- **气质**：绿皮车与 JR 线路色——铁道票的怀旧工业感，比航司蓝更慢更有人情——铁路/公路旅行、城市漫游、复古交通主题

```css
--paper:#FDFCF9; --paper-tint:#F2F0E8;
--ink:#1D2129;   --ink-tint:#3A3F4A;
--accent:#2F6B4F; --accent-on:#FDFCF9;
```

#### 演出粉

- **气质**：livehouse 与音乐节热敏票根——高饱和演出粉，票务的躁动与收藏欲——演出、赛事、潮流活动、青年文化

```css
--paper:#FDFCF9; --paper-tint:#F2F0E8;
--ink:#1D2129;   --ink-tint:#3A3F4A;
--accent:#D6336C; --accent-on:#FDFCF9;
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
| 独立出版 / zine / 创意印刷 | E1 孔版印刷 |
| 工程 / 制造 / 技术方案 | E2 蓝图 |
| 奢华 / 庆典 / 品牌盛典 | E3 装饰艺术 |
| 设计教育 / 构成 / 现代主义 | E4 包豪斯 |
| 宣言 / 动员 / 激进主张 | E5 构成主义 |
| 年轻 / 玩趣 / 活动庆典 | E6 孟菲斯 |
| 东方美学 / 文化典藏 / 节物 | E7 浮世绘 |
| 新闻 / 快讯 / 资讯简报 | E8 号外报纸 |
| 地质 / 考古 / 长期演进叙事 | E9 地质地层 |
| 天文 / 科幻 / 探索主题 | E10 星图 |
| 行程 / 票务 / 物流 / 活动 | E11 票据 |

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

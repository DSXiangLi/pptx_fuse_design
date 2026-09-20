# AGENTS.md — HTML PPTX 设计系统

## 项目定位（基调）

本项目要构建一个 **HTML PPTX 设计系统**：AI 生成"网页版 PPT"（HTML 幻灯片），并配套一个可交互的 UI 页面，用于设计决策、预览与直接编辑。

- 产出物的形态是 **HTML 版 PPTX**（幻灯片以网页形式呈现与交付）。
- UI 页面在生产环境中需要以 **iframe 嵌入** 方式接入宿主系统，设计时必须考虑嵌入场景（尺寸自适应、跨窗口通信、无侵入样式隔离等）。
- 本项目追求高级感、可交付的设计质量，拒绝平庸的 AI 默认审美。

## 输入模式（两种入口）

1. **从 0 到 1 构建**：用户提供主题 / 文案 / 资料，AI 直接生成 HTML 版 PPT。
2. **转换修改**：用户上传现成的 `.pptx` 文件，先转换为 HTML，再进入同一套编辑与修改流程。

## UI 页面必须承载的核心功能

### 1. Design System 面板（设计决策）

- 将整体设计语言、配色、字体、动效等**所有设计相关选项**，通过 brainstorming 的方式给出候选，让用户逐项做选择，而不是让 AI 单方面拍板。
- 配色等选项必须是**可视化面板**（色板、字体预览、动效预览），所见即所得，不能只给文字描述。

### 2. 渲染与直接编辑（核心诉求）

- AI 生成的 HTML 版 PPT 必须在页面中**直接渲染预览**。
- **页面直接可编辑**：所有 HTML PPT 中的文字，用户可以在页面上直接选中、删除、修改，**无需切换编辑模式**，并且修改结果能够**直接保存**。
- 这是本项目的第一优先级诉求：编辑体验必须流畅、即时、可靠。

## 已确认的技术决策

- **技术栈**：纯静态 HTML / JS / CSS，无框架、无构建步骤，保证 iframe 嵌入与交付的轻便性。
- **持久化**：编辑结果保存回 **HTML 文件本身**（序列化 DOM 后写回 / 导出为文件），交付形态就是单个 HTML 文件。
- **编辑范围**：
  - 第一期：页面上**直接编辑文字**（就地 contenteditable，无需切换模式，直接保存）。
  - 后续：提供一个**下拉面板**，让用户选择配色、边框类型等视觉效果；这些非文字类修改**通过 AI coding 整体修改 HTML**，而非在页面内做完整属性编辑器。
- **导出**：不需要从 HTML 反向导出为 `.pptx`，交付物即 HTML 网页版 PPT。
- **转换链路**：`.pptx → HTML` 由 **AI coding agent** 完成（读取 pptx 内容后生成 HTML），页面不负责解析 pptx，只接收转换成果。
- **AI 位置**：AI 在**开发侧**（coding agent），**页面内不含 AI 调用**。因此 design-system 面板的候选来自**预置主题库**（人工策划的配色/字体/动效组合），而非运行时动态生成。
- **保存机制**：使用 **File System Access API**（`showSaveFilePicker` / 文件句柄直写），目标浏览器为 Chrome / Edge；不支持的浏览器降级为下载导出。
- **幻灯片形态**：**16:9 竖向滚动**——每页为 16:9 画幅，页面间上下滚动浏览，适合网页阅读与 iframe 嵌入文档流。
- **产品架构**：**独立编辑器页面**（如 `editor.html`）——编辑器打开任意幻灯片 HTML 进行编辑，再通过 FSAA 写回原文件；幻灯片文件本身保持纯净，可独立演示，编辑器代码只需维护一份。
- **主题应用**：design-system 面板**只收集用户意图**（生成结构化的修改清单 / 给 AI 的指令），实际的样式代码修改由 **AI coding agent 落码**完成；面板不直接改 HTML。
- **宿主集成**：第一期先保证页面**独立可用**。嵌入协议已实现最小闭环：入 `{type:"pptx-html:load", html, name?, assetsUrl?}`，出 `pptx-html:save` / `pptx-html:dirty`（嵌入态保存一律走 postMessage，FSAA 在嵌入语境不可用）；宿主侧更多集成（鉴权、双向协议扩展）预留设计，暂不实现。端到端验收 harness 见 `tests/harness/`（`python3 tests/harness/run_e2e.py`）。
- **第一期编辑辅助**：除文字就地编辑外，支持**图片替换**（用户可替换幻灯片中的图片）。
- **本期范围收敛**：第一期只做 **HTML 页面化编辑**（编辑器 + 文字/图片编辑 + 保存），保持干净，不做多余功能。
- **可编辑标记**：编辑器与幻灯片之间通过**统一标签约定**识别可编辑区域（具体标记规范在设计文档中定义，AI 生成侧与编辑器共用同一约定）。
- **图片资产管理**：幻灯片中的图片一律**引用外部文件**，统一放在 `assets/` 目录；AI 生成时使用占位图片文件，用户下载后可随时直接替换 `assets/` 中的同名文件完成换图。
- **意图清单 Schema**：design-system 面板收集的用户意图需要**结构化 Schema**（参考 AskUserQuestion 工具的 schema 形态：问题/选项/多选/自由输入），输出给 AI coding agent 落码。
- **预置主题来源**：主题库基于 `source/guizang-ppt-skill/` 与 `source/frontend-slides/` 两者策划。

## 项目组成

1. **HTML PPTX 生成技能**：`skills/html-pptx/`（v1.7）——中文技能，面向 AI coding agent，负责从 0-1 生成或将 pptx 转换为高质量 HTML 幻灯片。原则性指导优先、枚举式罗列谨慎。组成：`SKILL.md`（五条第一性原则 + 工作流 + 密度双档决策 + K 期章节结构（data-chapter/nav-link/高密度封面目录默认必载）+ Step 1/4 呈现发散步（H 期想象层：关键页先写 3 个不同轴呈现方案再选定，查询 references/motifs.md）+ 两级主题冻结（重主题 + 配色变体，Step 2）+ Step 5.5 插画 pass——内容验收后用户声明"AI 插画模式"才进入：盘点槽位 → 风格规划（主题 G7 或缺省推导 + token 色系）→ 逐槽生图（oai生图 CLI，同名覆盖占位图、state 翻 generated）→ 回归校验（渲染重跑 + check-images --mode illustration），反降级硬规则：禁 placeholder 残留、失败诚实回退）、`assets/skeleton.html`（v7.1：16:9 竖向滚动固定骨架 + **文字效果词汇 .tt-***（outline 描边字/strike 删除线/mark 荧光标记/uline 粗下划线——纯 CSS 静态类、文字保持可编辑、描边字编辑态还原本色，契约 v6.4） + **G 期 SLOT: theme css 主题 CSS 槽位**（框架层之后、`</style>` 之前：:root{} token 重定义即动效缓动签名 + .mt-* 全库唯一母题类；白名单三类规则、禁字面 hex、禁外部 url()、禁覆盖框架选择器）+ **K 期章节跳转**（data-chapter 章节声明 + nav-link 锚点平滑滚动 + 数字键 1–9 直跳/0/Home 回封面/End 到末页，老 deck 无章节不动作）与 **mend-bar 双态修复条**（纯 CSS 两阶段 --from 警示渐变→--val accent 纯态）+ **data-rotate 轮转高亮**（loop 型，in-view 启动离屏停、2.4s 烧死、freeze 摘除清空 .active）+ 运行时文本引擎（chars/words/shatter 拆字 + typewriter/scramble 主题限定款，文件纯文本、入场执行、完成还原）+ count-up/draw-line/fill-bar recipe + F4 动效词汇库 8 族扩展——enter 补全（blur-in/scale-pop/wipe-clip/rise-in/persp-in）、text 补全（mask-lines 逐行遮罩：生成侧显式分行 .ml-line>.ml-inner 纯 CSS；gradient-flow 流光字）、data 补全（fill-bar-y 竖柱/ring 环形进度纯 CSS——pathLength="100" + --val）、link 补全（dash-flow 流动虚线/flow-dot 沿线粒子 offset-path）、amb 补全（noise/gradient-blob/kenburns/marquee）、light 族（sweep/border-beam/god-rays/light-leak/spotlight）、ptr 族（pointer tracker：rAF 节流 pointermove 只写 --mx/--my/--mxr/--myr CSS 变量不碰 DOM；tilt ±6°/magnetic ±16px/parallax ±28px 上限烧死；reduced-motion 与非 fine 指针不启动；passive 监听不劫持嵌入宿主；__pptxMotion.freeze() 供编辑器冻结）、scroll 族（read-progress 纯 CSS scroll-timeline（放 .deck 内最后）；parallax/scrub/scrub-draw 由骨架 JS 滚动驱动 .slide 的 --sp 进度变量、CSS calc 消费——CSS view() 在 overflow:hidden 画布下绑错滚动容器致进度冻结（Chromium 145 实测），偏离说明见 0919_iter_f4.md；cover/stack 页间 sticky 纯 CSS）+ **F5 fx 仪式层（v5.1）**：canvas 2D 仪式效果 4 款（constellation/starfield/particle-drift/ascii-field），`data-fx` 选类、参数烧死无参数通道，只许 .cover-page 仪式页、主题 G5「fx 许可」白名单默认关，rAF 绑 in-view 离屏停帧，reduced-motion 不初始化，freeze 停帧+摘除 width/height）+ 刊头家具槽位（.masthead 页眉/.mastfoot 页脚 hairline 行，样式在框架层、内容是可选 SLOT）+ 背景配给制（质感层默认只铺仪式页 .cover-page，正文页须逐页显式 .texture-on；--texture-scope 降级为许可声明 cover/all）+ G3 质感槽位（--texture-layer）+ 背景 ambience 类 + 缓动三 token + .js 降级门槛 + skeleton-version meta，逐字复制）、`references/themes.md`（**G 期重构为两级架构 + I 期建库 20 套**：20 个七层重主题（表达力栈 L1–L7 ↔ G0–G9：色彩/字排/质感/装饰母题 G9/容器风格 G4 扩/动效签名 G5 扩/构图倾向 G8 扩）+ 每主题 ≥3 套配色变体（同世界的光线/材质演绎，只许覆盖 G1 六色与可选 G3）——A/B 系为原 16 套纯配色主题的诚实合并（A1–A5→电子杂志 5 变体、B1–B4→瑞士 4 变体），E 系 11 套为 I 期世界采样新主题（孔版/蓝图/装饰艺术/包豪斯/构成主义/孟菲斯/浮世绘/号外报纸/地质地层/星图/票据）；G0 新增世界参考/unforgettable/分化声明三必填；两两七层 diff ≥3 层为入库机器门槛；Schema 化字段组 + focus 声明（G9 装饰主导入分组）+ 集中缺省推导规则 + 图表 token 统一推导 + F1 高级感要素落位：G1 accent 用量预算（内容页 ≤10%/满屏特权页/首尾闭环）、G2 字号对比档与字重映射表、G3 立场必填——A 系纸纹/墨韵、B 系 flat 立场、C2/D2 glow、A4/C4/D3 paper、A3/A5/C3 grain；G5 动效签名（气质六选 + 强度上限 + 禁用 recipe + 锚点偏好/节奏偏移/缓动签名，typewriter/scramble 为 techy 主题限定款；F5 起新增「fx 许可」白名单——canvas 仪式层效果逐主题声明，缺省全禁：editorial 系仅 ascii-field、B1 破格 ascii-field（归藏 IKB 先例）、C1 粒子三款、C3 粒子+字符场、calm 系仅柔和款、D3 全禁））、`references/motifs.md`（H 期新建：内容关系→视觉隐喻库，八类关系——对比/增长/流程/数字/层级/组成/因果/时间各 3+ 发散隐喻，绑视觉语言落法与亲和气质；SKILL.md 呈现发散步的查询库；语义化 canvas FX 四款仅登记未落码）、`references/typography.md`（标题分档/字重映射表（归藏倒挂口径量化：≥154px→200…14–16px→500–600，含衬线/极粗例外立场条款）/字号对比档硬规则（低密度 ≥8:1、高密度 ≥5:1）/槽位预算/密度规则）、`references/components.md`（v3：构图谱系六谱系（§11：巨字宣言/数据英雄/网格矩阵/轴与节点/图文证据/裂屏对开 + 张力来源 + 节奏纪律——禁连续 3 页同谱系）× 结构族六族 × Item 皮肤六款 × 参数变体，三步选型 + 数据形态自证清单 + 族×皮肤适配矩阵 + 容器规格（§12：四档明度/accent 单焦点/灰底低对比；G 期起容器造型语言委托主题 G4/G9，§12 只管明度档与焦点纪律）+ **K 期 §13 文本容器层**（六型：字段行 kv-rows/数据带 ticker/指标卡 metric-card/对照列 versus-cols/堆栈层 stack-rows/注记块 note-block + 容器内四层字阶硬规则——高密度页要点必须装进容器型，裸排列表即违规）+ 组合嵌套规则 + stylize 接口；Callout/Ghost/Highlight 归页面修饰件）、`gallery/`（F2+F3 实例层：index.html = skeleton v4 画廊 deck 50 页，6 族 × 6 皮肤 × 高复杂度参照实例 + 嵌套组合 + 修饰件示范 + 9 类图表配方页（p16–24，各带完整标注层）+ G/I 期 20 页主题样张（p25–44：同一封面内容 × 20 重主题，section 级 token + G9 母题 css 注入，渲染验收物）+ K 期 §13 六型文本容器实例页（p45–50：kv-rows/ticker/metric-card/versus-cols/stack-rows/note-block，B1 主主题高密度实例，含 mend-bar 演示）；多主题 sampler 形态——:root 主主题 + 单页 section 级 token 覆盖，此豁免仅属画廊；经 `tests/decks/components-gallery` 符号链接进 harness 回归，T18 校验零溢出零重叠/镜像表/谱系节奏/图表根覆盖/瀑布·雷达·斜率几何抽验）、`references/charts.md`（v2：14 配方——基础五（H-Bar/Column/Line/Donut/Progress）+ 扩展九（堆叠/分组柱、面积、瀑布、散点·气泡、雷达、斜率、定量漏斗、热力表格），每配方带标注层规格（参考线/区间带/数值直标/注释旗标，标注文字 data-editable、引线与几何 skip、配色从 chart token 推导）+ 系列色 8 档 color-mix 推导（1–4 档冻结、5–8 档明暗交错续排）+ 可编辑分层）、`references/motion.md`（v3.1：三原理六原则 + 反目录覆盖纪律 + 触发器三维模型（inview/loop/scroll/pointer + v5.1 新增 canvas in-view 生命周期，族前缀自文档化）+ 8 族 41 recipe 词汇表（每 recipe 带职能/触发器/适用内容/时长档/主题亲和与禁用；K 期新增 mend-bar 双态修复条/data-rotate 轮转高亮 + §3 内容→动效对照表——与 motifs.md 互引：motifs 管静态呈现隐喻、对照表管动态过程隐喻）+ **fx 仪式层小节**（v3.1/F5：canvas 2D 4 款枚举 + 五条启用纪律硬规则——默认关/只许仪式页每页至多 1 个/写法唯一/fx 即该页唯一 L4 环境层/降级零痕迹）+ 五层启用矩阵（L1 入场/L2 文字/L3 数据/L4 环境/L5 交互：克制=仅 L1、标准=L1–L4 各一、华丽=全开；注意力预算三档共享——加层不加同层数量；华丽档相邻页锚点 recipe 不重复）+ 气质对照表 + 主题 G5 接口（G 期扩为动效签名：锚点偏好/节奏偏移/缓动签名，注意力预算仍是硬上限）+ 背景配给纪律（F1）+ 降级链，文本破坏性动效必须运行时化）、`references/editing-contract.md`（可编辑标记契约 v6.4，含信息图组件分层与 data-ig 辅助标记 + 图片槽位契约——`data-image-slot`/`data-image-intent`/`data-image-state` 三属性、三方绑定（槽位比例↔构图尺寸↔生图比例，容差 5%）、存量兼容警告、插画模式反降级 + v6 动效扩展——typewriter/scramble 纳入运行时化条款、mask-lines 分行结构（.ml-line/.ml-inner）归属产物、gradient-flow 透明填充效果编辑态强制还原本色、pointer/scroll 族运行时 CSS 变量（--mx 系/--rx 系/--sp）净化清单、__pptxMotion.freeze() 编辑态冻结交互层约定 + v6.1 canvas FX 净化条款——canvas[data-fx] 产物中为空元素，运行时 width/height 由 freeze 摘除、序列化兜底，编辑器页面共用 + v6.2 主题 CSS 块条款——SLOT: theme css 原样保留、.mt-* 母题件 skip、文本载体类母题文本保持可编辑、主题块 :root token 重定义禁净化）、`scripts/sync-themes.mjs`（主题数据 + 面板动效组（五层启用矩阵选项，__MOTION_JSON__ 标记区间）单源同步 + Schema 校验器——F1 起校验 G1 accent 预算/G2 对比档·字重映射/G3 立场三 token（枚举 type/scope、flat⇔none、禁外部 url()）；G 期起校验 G0 三必填/变体字段集（≥2 变体、只许六色+可选 G3 覆盖）/G9 css 白名单与 .mt-* 全库唯一/两两七层 diff ≥3 分化门槛/分化声明逐层核验，校验失败非零退出）、`scripts/check-images.mjs`（图片槽位契约静态校验器：三属性完整性 / state 合法值 / 比例三方绑定（解析 SVG/PNG/JPEG/GIF/WebP 固有尺寸）/ assets 落盘存在性 / `--mode illustration` 反降级，幂等、失败非零退出）。验收脚本（tests/harness/）：`j_render_check.py`（零溢出/零重叠/字号档，标注层豁免口径）、`k_nav_check.py`（章节跳转三通道）、`density_measure.py`（DOM 密度量化：文本叶/标注层/字阶档）。设计依据见 `docs/research/source-survey.md`（调研索引；各项目细节文档在 `docs/research/projects/`，最优方案综合判断见 `docs/research/optimal-solution.md`，SOTA 视觉枚举规范见 `docs/research/sota-visual-languages.md`），迭代规划见 `docs/skill-roadmap.md`（视觉纵深 F1–F6 见 `docs/progress/0919_visual_depth_plan.md`，F1/F2/F3/F4/F5 已完成）。
2. **编辑器页面（已实现）**：`editor.html`（v2.4）——单文件、纯静态、无框架、无构建、无外部依赖。**K 期适配 skeleton v7**：编辑态拦截 `.nav-link` 目录锚点点击跳转（契约 v6.3）、序列化净化新增 data-rotate 的 .active 运行时 class 移除。承载 design-system 意图收集（右侧抽屉，主题数据由 `skills/html-pptx/scripts/sync-themes.mjs` 从 `references/themes.md` 单源生成，含 theme/rhythm/motion/density 四组 + 自由补充；主题卡按 focus 分组展示——配色/质感/装饰/字排/形态主导，卡片带 focus 标签与气质一句话；**G 期起主题卡带配色变体色点行**（点击切换变体、再点回基底，导出时变体 token 合并进 answers.theme.tokens 并携带 theme_css——主题 G9 母题 CSS 块，导出文案为双 SLOT 口径：SLOT: theme tokens + SLOT: theme css）；**F4 起 motion 组为五层启用矩阵**——克制=仅 L1 入场 / 标准=L1–L4 各一（默认）/ 华丽=L1–L5 全开，选项数据由 sync-themes.mjs 写入 __MOTION_JSON__ 标记区间，语义源 motion.md v3 §5）、iframe srcdoc 渲染预览、文字就地编辑（两段手势 + contenteditable plaintext-only）、**文字样式编辑**（选中文字元素后顶栏出现字体/字号/字色/对齐控件组，只写白名单四属性 inline style，随保存序列化保留）、**PPT 式目录侧栏**（Shadow DOM 克隆缩略图 + IntersectionObserver 懒渲染 + 点击导航 + 当前页高亮 + 编辑后失效重克隆）、图片替换（FSAA 写入 assets/，同名覆盖优先；上传成功置 `data-image-state="uploaded"` 并保留 slot/intent——契约 v5）、批注（顶栏分段切换批注模式 → iframe 内框选 → 父页面弹窗 → 三层引用 slide/path/excerpt → 导出指令，嵌入态额外 postMessage `pptx-html:annotations`；批注不置脏、不进保存产物）、序列化净化保存（§5.4 五条 + 运行时动效归位：拆字 span 还原 textContent、draw-line 描边 style、html 运行时 class、**v2.1 起含 pointer/scroll 族运行时 CSS 变量（--mx/--my/--mxr/--myr/--rx/--ry/--mgx/--mgy/--sp）与 tw-live class，空 style 属性一并移除；v2.2 起含 canvas[data-fx] 的运行时 width/height（契约 v6.1，freeze 主责、净化兜底）**；编辑拆字/count-up/typewriter/scramble 元素前先经骨架 `__pptxMotion` 接口强制还原；**v2.1 编辑态冻结交互动效层**：加载后调用 `__pptxMotion.freeze()` 摘除 pointer tracker 与 scroll 驱动，注入样式把 [data-scroll]/[data-ptr]/.spotlight/.read-progress 压回静态终态，编辑 gradient-flow 类透明填充文字时强制还原本色——契约 v6；mask-lines 的 .ml-line/.ml-inner 分行结构是产物内容原样保留，行叶子 .ml-inner 可直接编辑；v2.0 确认兼容 skeleton v4——刊头家具 .masthead/.mastfoot 为产物 SLOT 内容原样保留，v4 背景配给纯 CSS 无运行时残留）。**git 版本**：探测 `tools/edit.py` 伴随服务（`/api/health`），有后端时保存走 `/api/save`（每次保存一个版本），顶栏"历史"面板列版本、回滚（服务端 pre-rollback 保护提交）；无后端维持 FSAA/下载现状。与技能共用 `skills/html-pptx/references/editing-contract.md` 契约（v6.3，含"样式覆盖"节、"文本破坏性动效必须运行时化"条款、"信息图组件的分层"节、"图片槽位契约"节、v6 动效扩展、v6.1 canvas FX 净化条款、v6.2 主题 CSS 块条款、v6.3 章节跳转/v7 动效条款与 v6.4 文字效果词汇条款；信息图辅助标记 data-ig/data-ig-skin/data-ig-item 编辑器不消费、保存原样保留）。设计文档：`docs/design-editor.md`（v0.3，已通过审核修订）+ `docs/design/editor-v2.md`（v2 迭代）+ `docs/design/theme-expression-stack.md`（G/H 期）+ `docs/design/high-density-containers.md`（K 期）。
3. **本地伴随服务（已实现）**：`tools/edit.py`——python3 标准库零依赖。静态托管工作目录（editor.html 不在工作目录时回落项目根副本）+ 最小 API：`GET /api/health`（含 gitReady）、`POST /api/save`（原子写 + git add 仅该 deck 与同级 assets/ + commit；非仓库需调用方 init:true 确认）、`GET /api/versions`、`POST /api/rollback`（先 pre-rollback 保护提交再还原）。所有 API 拒绝路径穿越。用法：`python3 tools/edit.py [工作目录] [--port 8926] [--no-browser]`。

## 参考资源

`source/` 目录下为收集的参考实现，仅供借鉴思路，不是本项目的代码：

- `source/codex-ppt-skill-main/`、`source/dashi-ppt-skill/`、`source/guizang-ppt-skill/`、`source/ppt-master/`：各类 PPT 生成 skill
- `source/frontend-slides/`、`source/open-design/`：前端幻灯片 / 开放设计相关参考

`docs/` 目录用于存放设计文档与调研资料：`docs/research/`（调研体系，索引为 `source-survey.md`；含 `motion_gudie.md` 动效指南）、`docs/design/`（设计文档，索引为 `README.md`，重大决策先在此评审后实施）、`docs/progress/`、`docs/test_acceptance/`。

## 协作约定

- 重大设计决策先写入 `docs/` 下的设计文档，评审通过后再实施。
- 修改代码后保持本文档与实际架构同步。
- **范例是矿不是图**：外部优秀示例（`source/`、用户提供的参考 pptx/html）的价值是**抽象、压缩、提炼范式回灌技能**——不是复刻。拿到好示例的固定动作：量化解剖（实测数据回答"它好在哪里"，如 `docs/research/demo1-density-analysis.md`）→ 范式条款（落进 `references/` 的硬规则）→ 验收资产（按新范式重做的测试 deck）。把"重现示例"当目标是项目层面的失败。

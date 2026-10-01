# 设计文档（docs/design/）

> 本目录承载**已通过调研、等待评审实施**的设计决策。调研依据在 `../research/`（索引：`../research/source-survey.md`），迭代分期在 `../skill-roadmap.md`。
> 本批文档源于 2026-09-18 对调研结论的五条修订意见 + 两条新增方向，状态：**待评审**。

## 文档地图

| 文档 | 解决的问题 | 对应修订意见 |
|---|---|---|
| `editor-v2.md` | 编辑器 v2 迭代：文字样式编辑（白名单四属性 inline style）、PPT 式目录侧栏、本地 git 版本回滚（tools/edit.py 伴随服务） | 2026-09-18 用户意见（本轮已实施） |
| `iteration-plan.md` | v2 迭代排期：A 编辑器 v2 → B 主题 Schema → C 动效 v2 → D 信息图 v2 → E 插画管线 → F/G 上下兼容 | 2026-09-18 开工计划 |
| `theme-schema.md` | 主题库从无 schema 的惯例对齐，升级为显式 Schema：必填核心 + 可选字段组 + focus 机制（重点/辅助项）+ 缺省推导规则 | 意见 1（迭代 B 已实施） |
| `motion-system.md` | 拆字类动效与就地编辑的共存方案（运行时拆分）；motion_gudie 三原理六原则入库为动效规范 v2 | 意见 2 + `../research/motion_gudie.md`（迭代 C 已实施） |
| `infographic-system.md` | 信息图从 12 个平铺组件升级为"结构族 × Item 皮肤 × 主题"的正交组合衍生模型（借鉴 antv-infographic 架构，不引入库） | 意见 3（迭代 D 已实施） |
| `illustration-pipeline.md` | AI 生图插画模式：内容验收后的统一插画补齐 pass + 图片槽位契约 + 反降级校验 | 意见 6（迭代 E 已实施） |
| `compat-roadmap.md` | 未来规划：向上兼容（页面级全图化：HTML 截图 / AI 重绘）与向下兼容（html2pptx）的形态、契约与排序 | 意见 7 |
| `visual-depth.md` | 视觉纵深：归藏高级感 8 要素落位、信息图/图表组件库（画廊+配方双形态）、动效词汇库 8 族与五层启用矩阵 | 2026-09-19 v2 效果诊断 + 两轮深潜调研（F1–F6 已实施完毕） |
| `handover-theme-differentiation.md` | **session 交接文档**：进度快照 + 用户验收 comment + baoyu-design 补充调研 + 主题差异化/想象层的独立思考（七层表达力栈、隐喻库、世界采样构思法、G–J 期路线） | 2026-09-19 用户验收 comment |
| `theme-expression-stack.md` | G+H 期设计：主题 = 七层表达力栈（L1–L7 ↔ G0–G9）；骨架 v6 主题 CSS 槽位；两级主题架构（9 重主题 + 配色变体，16 纯调色板主题诚实合并）；两两七层 diff ≥3 的机器门槛；隐喻库 + 呈现发散步 | handover §5 路线（G/H/I/J 全部实施完毕） |
| `theme-e12-neobrutalism.md` | E12 商务粗野入库：cmb-retail-v3 deck 级定制主题的回灌蒸馏——策展五色（变体即五色）+ 粗墨描边 + 硬偏移投影 + 直角平面卡；与 E6 孟菲斯的 ≥4 层分化；章节级 data-hue 色相轮转记为 deck 级玩法（不进 G9 css 白名单） | 2026-09-30 用户验收 v3 后批准入库（已实施，sync-themes 校验 + T18 全绿） |
| `high-density-containers.md` | K 期：高密度表达三件套——文本容器层（components.md §13 六型 + 四层字阶纪律）、章节跳转导航（skeleton v7：data-chapter/nav-link/数字键）、动效编排纪律吸收（mend-bar 双态修复条 + data-rotate 轮转高亮 + 内容→动效对照表） | 2026-09-20 用户验收意见（高密度测试缺口 + demo1 动效复盘） |
| `tri-form-architecture.md` | 三形态架构总览：HTML（唯一真相）/ 整页生图（视觉上限）/ PPTX（单向交付快照）；翻转统一动词；**转换即技能**红线；manifest + content-hash 公共地基；防幻觉三硬规则 | 2026-09-21 上下兼容两轮设计讨论（M1 已实现，T23） |
| `page-render-mode.md` | 子技能 A：整页生图烙入模式——与插画模式的边界（页内槽位 vs 整页）、源层保留结构（契约 v7）、HTML 样张锚 + 确定性指令编译、代表页审批闸门、stale 重烙 | 同上（M2 已实现，T24） |
| `pptx-export-svg.md` | 子技能 B：HTML→PDF→SVG→PPTX 矢量管线（浏览器即编译器、文字转曲、svgBlip+PNG 双写）；字体/布局稳定性四道防线（字体随档子集化/度量兼容回退/导出渲染门禁/容器余量） | 同上（M3 已实现 T25；C3 起为保真轨 deck-vector.pptx + deck.pdf 直出） |
| `editor-tri-view.md` | 编辑器 v3：三态工作台（编辑/对比/导出）、翻面交互（手势/过场 + 背面三态含黑面空态）+ 并排（默认落定）/滑动分割/差异热区（质检层）、stale 闭环、保真分排序 | 同上（M4 已实现，editor.html v3.0 + T26） |
| `handover-tri-form.md` | **session 交接文档**：三形态翻转设计的进度快照 + 阅读顺序 + 已定决策快照 + M1–M4 任务规划 + 遗留待澄清点——下个 session 从这里读起 | 2026-09-21 设计闭环交接 |
| `pptx-export-editable.md` | 子技能 C：可编辑 PPTX 导出（原生元素轨）——渲染真相 × 契约标记路线（真实分行文本框 wrap=square / 原生 chart XML / 信息图 grpSp 分组 / 复杂视觉烙图兜底 / 字体内嵌 embeddedFontLst）；双轨导出（deck.pptx 可编辑轨主交付 + deck-vector.pptx/deck.pdf 保真轨）；ppt-master 资产借用清单 | 2026-09-22 用户意见（SVG 轨不可编辑≈PDF）+ ppt-master v6.6.0 调研（**C1–C3 已实现**，T25/T27 全绿） |

## 决策速览

1. **主题 Schema**：色与字是必填核心，质感/形态/动效亲和/插画风格等是可选字段组；每个主题声明 1–2 个 focus 字段组作为设计感来源，其余走集中维护的缺省推导——"不覆盖全字段也完整"。
2. **拆字不禁令**：产物文件中的文字永远是纯文本节点，拆字由骨架 JS 在运行时执行；编辑器看到的永远是纯文本，编辑契约零改动，无 JS/reduced-motion 天然降级。
3. **信息图组合衍生**：结构族（有限枚举）× Item 皮肤（有限枚举）× 参数变体（密度/方向/项数）= 大组合空间；数据字段与结构族硬约定防止 AI 乱填；新族/新皮肤入库走 `../research/sota-visual-languages.md` 七件规范。
4. **插画管线**：占位图 →（内容验收）→ AI 统一补齐插画 →（用户随时）上传替换，三级供给链共享同一条 `assets/` 资产契约；声明插画模式必须真实落盘（可静态校验的反降级）。
5. **上下兼容**：HTML 永远是唯一事实源与起点；全图化和 pptx 导出都是**导出态分支**，以独立工具承载，不污染产物纯净性。（2026-09-21 起升级为实施级设计：见 `tri-form-architecture.md` 系列四文档；原 `compat-roadmap.md` 保留为历史记录。）
6. **三形态与翻转**：HTML = 唯一真相源，整页生图与 PPTX 导出是两种"翻转"（单向、逐字引用、hash 失效检测）；**转换是技能不是后端**——编辑器只消费 `export/` 产物；PPTX 保真走浏览器渲染→PDF→SVG 转录路线，字体随 deck 子集化内嵌根治跨机版式漂移。

## 共同纪律

- 所有枚举型资产（主题、信息图结构族、Item 皮肤、动效 recipe）入库必须满足 `../research/sota-visual-languages.md` 的七件结构与三级验收。
- 凡涉及编辑器与生成器之间的约定，先改 `skills/html-pptx/references/editing-contract.md` 再改生成侧，契约不后补。

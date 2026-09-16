# 参考项目调研与第一性原理分析

> 调研对象：`source/` 下六个参考项目。目的：为新技能 `skills/html-pptx/` 的设计提供依据。
> 调研日期：2026-09-16。

## 一、各项目一句话定位

| 项目 | 产物形态 | 核心策略 | 对本项目的价值 |
|---|---|---|---|
| guizang-ppt-skill | 单 HTML，横滑翻页，vw/vh 流体 | 种子模板 + 锁死主题/版式 + 脚本校验 | 主题策展、校验闭环、"案底式"规则写法 |
| frontend-slides | 单 HTML，1920×1080 固定舞台 + transform 缩放 | 无模板现写 + 渐进披露模板库 + 反 AI slop 原则 | 画布缩放方案、"Show don't tell" 风格发现、密度模式 |
| codex-ppt-skill | 整页 AI 生图拼 pptx | 门禁式工作流（大纲→风格→样张→批量） | 叙事方法论、样张门禁、"风格是系统不是模板" |
| dashi-ppt-skill | React SSR 静态 HTML + 内置编辑器 | JSON 契约 + 锁模板填文案 + 受约束定制 | 可编辑标记约定、容量驱动选版、稳定 ID 教训 |
| ppt-master | SVG → 原生可编辑 PPTX | 规则效力分级 + spec/lock 双文件 + 条件加载 | 元设计（Hard/Default/Reference 分级）、防上下文漂移 |
| open-design | 单 HTML deck + 桌面编辑器 | 固定骨架 SLOT 逐字复制 + 提示词即代码 | 骨架防漂移模式、编辑桥架构与实测教训 |

## 二、关键发现（按主题归并）

### 画布与适配
- frontend-slides / dashi / open-design 三家独立收敛到同一方案：**固定 1920×1080 设计画布 + 单个 transform 整体缩放**，禁止响应式重排。open-design 还记录了缩放实现的踩坑（transform-origin 必须 top left、shell 不能是 grid/flex 包装）。
- 六家的翻页交互（横滑/切页）与我们确定的"16:9 竖向滚动"形态都不兼容，**交互代码不可复用，缩放与 chrome 外置的思路可迁移**。

### 质量保障
- guizang 的闭环最完整：Pre-flight 类名预检 → 生成 → 静态校验 + Playwright 渲染测量（输出溢出 px 数）→ 按"修正阶梯"修复（微调间距→压文案→换版式，不许缩字号）。
- open-design 的"固定骨架 + SLOT 注释逐字复制"直接回应了"AI 每轮重写基础设施必然引入微妙 bug"的漂移问题。
- ppt-master 的 spec/lock 双文件 + "每页生成前重读 lock"回应长上下文漂移。

### 一致性与审美
- codex："风格是系统，不是重复构图"——一份 deck 一个视觉身份，但版式必须由内容驱动。
- dashi v4 的反模式清单精准打击 AI 默认审美："不要把所有页面都画成标题+卡片墙""卡片网格最多占三分之一""给标签换色不是设计"。
- guizang / open-design 的主题纪律："只选不改"——策展预设替代自由度，禁止混搭、禁止自定义 hex。
- frontend-slides 直接对 AI 行为诊断（"你会收敛到 Space Grotesk 和紫渐变白底"），并记录 CSS 静默失败类坑（`-clamp()` 必须写成 `calc(-1 * clamp())`）。

### 可编辑性（我们核心诉求的先行者们）
- dashi：`data-editable-path` 显式标记 + `data-editable-skip` 排除装饰 + 无标记时的启发式兜底（叶子元素 + 行内元素白名单）。**稳定 ID 教训**：不用遍历序号（reflow 会漂移），用"slide key + child-index 路径"。
- open-design 的实测经验：`contenteditable=plaintext-only` 为默认、首击选中二击才编辑（避免截断文本框突然撑高）、源码文件是唯一事实源、补丁原地应用永不重载页面。
- frontend-slides 的血泪规则：不要用 CSS `~` 兄弟选择器做编辑按钮 hover（pointer-events 断链），用 JS + 延迟。

### 共同的反面教材
- SKILL.md 过载：guizang 632 行 + 8000 行 references、dashi 263 行塞数十条硬规则、ppt-master 单文件 700+ 行防御性散文。**agent 遵循成本与规则数量成正比**——这印证了"原则突出、枚举谨慎"的设计要求。
- 编辑器与产物耦合（dashi 把 10277 行播放器+编辑器塞进每个产物）、产物是图片完全不可编辑（codex），都是我们要避开的。

## 三、第一性原理分析

### 问题 1：AI 生成的幻灯片为什么平庸？
AI 的默认输出收敛到训练分布的均值：居中 hero、紫蓝渐变、卡片墙、Inter 字体。**靠"写提示词让它更努力"无效**，因为收敛发生在决策层而非执行层。
→ 推论：**决策必须前置且外置**。主题、密度、叙事弧在写代码前冻结，且候选项来自人工策展的库（用户可视化选择），AI 只在冻结的约束内发挥。约束不是限制质量，是质量的来源。

### 问题 2：一致性从哪来？
两种路线：锁死版式（guizang 22 版式、dashi 锁模板）换稳定，但压抑内容表达；完全自由则必然漂移。
→ 推论：**一致性应该由 token 系统承载（色/字/间距/动效的少量变量），不由版式复制承载**。版式交给"构图原则 + 内容容量"动态决定。这就是"原则突出、枚举谨慎"的技术含义：枚举只保留在 token/主题层（这里枚举是保护），版式层用原则（这里枚举是枷锁）。

### 问题 3：文字溢出为什么根除不了？
因为 AI 在"写完再发现溢出"。人眼检查不可靠，AI 目测更不可靠。
→ 推论：**容量规划先于版式选择**（先数字数/条目数再选构图），**渲染测量代替目测**（脚本量出溢出 px 数），**修复有阶梯**（间距→文案→拆页，缩字号是最后的禁区）。溢出是规划问题，不是排版问题。

### 问题 4：编辑器怎么认识生成的文件？
编辑器与生成器是两个不相识的进程，唯一的通信介质是 HTML 文件本身。
→ 推论：**data 属性即契约**。生成侧必须给每个可编辑元素打稳定语义标记（`data-editable` / `data-slide-id`），这不是可选的修饰，是产物的组成部分。文件是唯一事实源，编辑器的一切操作最终序列化回文件。

## 四、结论：新技能站在谁的肩膀上拿什么

| 设计决策 | 来源 | 理由 |
|---|---|---|
| 1920×1080 固定画布 + transform 缩放 + 竖向滚动 | frontend-slides / open-design（缩放部分） | 三家收敛验证过的保真方案；竖滚是我们自己的形态决策 |
| 固定骨架 skeleton.html 逐字复制 + SLOT 填充 | open-design deck-framework | 消灭基础设施漂移 |
| 主题库"只选不改"，token 即换肤契约 | guizang / open-design directions | 策展保护审美；`var()` 全覆盖使换主题零风险 |
| 规则效力分级（Hard / Default / Reference） | ppt-master | 让原则与清单各就其位 |
| 叙事弧 + 页计划表前置确认 | codex / guizang | 防止边写边想 |
| 容量驱动选版 + 渲染测量校验 + 修正阶梯 | dashi / guizang | 根治溢出 |
| 可编辑标记契约（data-editable 族 + 稳定语义 ID） | dashi / open-design | 我们与编辑器的通信协议 |
| 反模式清单（AI slop 负面清单） | frontend-slides / dashi v4 | 原则性对抗审美收敛 |

**明确不拿的**：横滑翻页交互、演讲者模式（激光笔/观众屏）、编辑器内置进产物、SVG/PPTX 工具链、门禁式多轮人工确认、22 个锁死版式的枚举教法。

---

## 五、主流框架补充调研（2026-09-16 第二轮）

对象：reveal.js / Slidev / impress.js / Spectacle / Shower / WebSlides / scrollytelling 模式（scrollama、Pudding 方法论）/ contenteditable 与 FSAA 浏览器现状。

### 结论摘要

1. **我们的形态决策被主流验证**：reveal.js 5.0 Scroll View 的 `compact` 布局（宽=视口宽、高按长宽比推出）与我们 `.slide-slot` 模型完全同构；Shower 的"文档/放映双模"是同一路线的老前辈。WebSlides 证明滚动形态可以不缩放，但代价是放弃版式确定性——我们不走那条路。
2. **缩放方案是行业共识**：reveal（`clamp(min(w/W,h/H))` + min/max 护栏）、Slidev（CSS `scale` 属性 + `transform-origin: top left`）、impress.js（默认画布同为 1920×1080）全部收敛到"固定画布 + 整体缩放"。
3. **骨架采纳的改进**（已实施）：`transform-origin: top center`（修复窄窗口裁剪 bug）、`ResizeObserver` 观察 deck（iframe/侧栏场景）、打印 `print-color-adjust: exact`、reduced-motion 时键盘瞬时翻页、`.slide-slot` 加 `content-visibility: auto`、fit() 阈值去抖。
4. **滚动动效纪律**：scroll-to-trigger，绝不 scrolljack；IntersectionObserver 原生够用，不引库；连续滚动动画可用纯 CSS `animation-timeline: view()` 做渐进增强。
5. **编辑器关键事实**：Firefox 136+ 才支持 `plaintext-only`（降级 + 粘贴拦截是必需品）；transform 缩放容器内的 contenteditable 光标偏移是高危组合，必须多缩放档实测；FSAA 在跨域 iframe 直接 SecurityError（降级路径是必需品）；FSAA 需安全上下文 + 瞬时用户激活；`::before/::after` 内容不进 outerHTML（chrome 类装饰天然"保存即消失"）。
6. **不反向导出 pptx 的决策被佐证**：Slidev 的 `pptx-editable` 实践证明 HTML→可编辑 PPTX 保真天花板很低。

来源明细见调研原始记录（revealjs.com、slidev 仓库文档、caniuse、MDN 等）。

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

1. **HTML PPTX 生成技能**：`skills/html-pptx/`——中文技能，面向 AI coding agent，负责从 0-1 生成或将 pptx 转换为高质量 HTML 幻灯片。原则性指导优先、枚举式罗列谨慎。组成：`SKILL.md`（五条第一性原则 + 工作流）、`assets/skeleton.html`（16:9 竖向滚动固定骨架，逐字复制）、`references/themes.md`（策展主题库，源自 guizang + frontend-slides）、`references/editing-contract.md`（可编辑标记契约，编辑器页面共用）。设计依据见 `docs/research/source-survey.md`。
2. **编辑器页面（已实现）**：`editor.html`（v1.2）——单文件、纯静态、无框架、无构建、无外部依赖。承载 design-system 意图收集（右侧抽屉，主题数据内置自 `references/themes.md`）、iframe srcdoc 渲染预览、文字就地编辑（两段手势 + contenteditable plaintext-only）、图片替换（FSAA 写入 assets/，同名覆盖优先）、批注（顶栏分段切换批注模式 → iframe 内框选 → 父页面弹窗 → 三层引用 slide/path/excerpt → 导出指令，嵌入态额外 postMessage `pptx-html:annotations`；批注不置脏、不进保存产物）、序列化净化保存（§5.4 五条）。与技能共用 `skills/html-pptx/references/editing-contract.md` 契约。设计文档：`docs/design-editor.md`（v0.3，已通过审核修订）。

## 参考资源

`source/` 目录下为收集的参考实现，仅供借鉴思路，不是本项目的代码：

- `source/codex-ppt-skill-main/`、`source/dashi-ppt-skill/`、`source/guizang-ppt-skill/`、`source/ppt-master/`：各类 PPT 生成 skill
- `source/frontend-slides/`、`source/open-design/`：前端幻灯片 / 开放设计相关参考

`docs/` 目录用于存放设计文档与调研资料（如 `docs/research/motion_gudie.md` 动效指南，待补充）。

## 协作约定

- 重大设计决策先写入 `docs/` 下的设计文档，评审通过后再实施。
- 修改代码后保持本文档与实际架构同步。

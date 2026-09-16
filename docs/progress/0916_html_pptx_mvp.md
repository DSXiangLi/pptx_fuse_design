# 0916 · 项目从零到 MVP

## 背景

项目目标：HTML PPTX 设计系统——AI 生成网页版 PPT（单 HTML + assets/），配套独立编辑器页面就地编辑。本日完成从零到可用的完整闭环。

## 决策记录（按时间）

1. **形态**：16:9 竖向滚动；纯静态无框架；FSAA 直写保存；不反向导出 pptx（Slidev 的 pptx-editable 实践证明保真天花板低）。
2. **架构**：独立编辑器页面 + 纯净产物；AI 在开发侧，页面不含 AI；pptx→HTML 由 AI agent 转换。
3. **两轮调研**：6 个 `source/` 参考项目 + 主流框架（reveal/Slidev/impress/scrollytelling），结论沉淀 `docs/research/source-survey.md`。
4. **技能设计**：原则优先、枚举谨慎；固定骨架 SLOT 制；主题库 13 套策展（guizang + frontend-slides 血统）；可编辑标记契约。
5. **编辑器**：iframe srcdoc 隔离渲染；两段手势文字编辑；批注模式（框选 → 弹窗 → 三层引用回传 AI）。
6. **验收驱动**：4 个子 agent 生成不同主题测试 deck → harness 自动化验收。

## 产出

| 产出 | 位置 | 状态 |
|---|---|---|
| 生成技能 | `skills/html-pptx/` | v1，骨架经框架调研修订（transform-origin bug 等 6 项） |
| 编辑器 | `editor.html` | v1.2（文字编辑 + 图片替换 + 批注） |
| 设计文档 | `docs/design-editor.md` | v0.3，两轮审核修订 |
| 测试 deck ×4 | `tests/decks/` | 全部通过渲染校验 |
| E2E harness | `tests/harness/` | 13/13 PASS |

## 关键踩坑（供后来者）

- Chromium `plaintext-only` 的 Enter 产生 `\n` 而非 `<br>`——提交时必须归一化，否则序列化丢换行；
- iframe 内 FSAA 函数存在但调用被静默吞掉——嵌入态保存必须一律走 postMessage；
- srcdoc 的 base URL 继承编辑器目录——嵌入加载必须注入 `<base>`（assetsUrl）否则图片全 404；
- `transform-origin: top left` 在窄窗口裁切内容——画布缩放必须 `top center`；
- mousedown preventDefault 会抑制焦点转移，Esc 监听要挂双层。

## 遗留

- 图片替换（FSAA 交互）与 Firefox 降级路径未经真实浏览器人工验收；
- 独立模式跨目录打开时编辑器内图片预览坏（产物正确，预览层待 blob URL 方案）；
- 意图清单导出指令未经人工走查。

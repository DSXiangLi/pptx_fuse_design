# 编辑器验收文档（test_acceptance）

> 对应模块：`editor.html` · 设计文档 `docs/design-editor.md` §11 · 自动化 harness `tests/harness/run_e2e.py`
> 最近全量执行：2026-09-16，13/13 PASS（Chromium 145 headless）

## P0（核心路径，失败即功能不可用）

| # | 验收项 | 方式 | 状态 |
|---|---|---|---|
| P0-1 | 往返幂等：未修改 deck 打开→保存，首趟仅白名单 diff、第二趟逐字节相等，四 deck 全过 | harness T1 | ✅ |
| P0-2 | 文字编辑端到端：两段手势、单行+多行（`<br>` 持久化）、窄文本框、失焦/Esc 语义 | harness T2/T3 | ✅ |
| P0-3 | 保存产物零编辑器痕迹（contenteditable/注入节点/运行时状态/?v= 全部净化） | harness T2 | ✅ |
| P0-4 | 渲染一致性：编辑器内与直开布局逐页一致（像素差 <0.2%，裸 iframe 对照） | harness T4 | ✅ |
| P0-5 | 批注端到端：框选多元素 → 弹窗剔除 → 导出 JSON 的 slide/path/excerpt 在原文件回解成功 | harness T7 | ✅ |
| P0-6 | 批注不置脏、不进保存产物 | harness T7/T8 | ✅ |

## P1（重要回归路径）

| # | 验收项 | 方式 | 状态 |
|---|---|---|---|
| P1-1 | 嵌入模式：保存/批注一律走 postMessage（save/dirty/annotations） | harness T6/T7 | ✅ |
| P1-2 | assetsUrl `<base>` 注入正确且不进产物 | harness T5 | ✅ |
| P1-3 | 批注边界：零命中静默、空批注置灰、Esc 取消无残留、模式切换手势门控 | harness T8 | ✅ |
| P1-4 | 图片替换（FSAA 写 assets/、同名覆盖、换扩展名） | 人工（headless 不可交互） | ⏳ 待人工 |
| P1-5 | Firefox 降级（编辑可用、保存降级下载、plaintext-only fallback） | 人工 | ⏳ 待人工 |
| P1-6 | 意图清单导出指令人工走查（粘贴给 coding agent 可执行） | 人工 | ⏳ 待人工 |

## 已知限制（非缺陷）

- 独立模式跨目录打开 deck 时编辑器内图片预览坏（产物正确）；待 blob URL 预览方案。
- 首趟保存的白名单 diff（布尔属性 `=""` 化等）为 HTML 解析规范化，稳定且一次性。

# 编辑器验收文档（test_acceptance）

> 对应模块：`editor.html` · 设计文档 `docs/design-editor.md` §11 · 自动化 harness `tests/harness/run_e2e.py`
> 最近全量执行：2026-09-20（I/J 期），43/43 PASS（Chromium 145 headless；T9 断言 20 主题卡、T18 覆盖 44 页画廊、T1 新增 3 个 J 期终验 deck）

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
| P1-7 | 密度双档：同一内容源低档页数 > 高档；可编辑元素无一超槽位预算 | 脚本（已内联核验） | ✅ 2026-09-16 |
| P1-8 | density-low / density-high 加入 harness 回归（往返幂等） | harness T1 ×2 | ✅ |
| P1-9 | 信息图组件 deck（infographic-b2）：11 类组件标记合规、零溢出 | harness T1 + Playwright | ✅ 2026-09-16 |
| P1-10 | 图表 deck（charts-a3）：五图表几何与数值比例一致、契约分层 | harness T1 + Playwright 抽查 | ✅ 2026-09-16 |
| P1-11 | 骨架 v2 动效：data-anim 阶梯、.js 门槛、reduced-motion 静态可读 | harness T1-charts-a3 + 生成侧自验 | ✅ 2026-09-16 |
| P1-12 | 主题数据单源：sync-themes.mjs 幂等 + 13 主题自检 + 面板导出 | node 脚本 + harness T9 | ✅ 2026-09-16 |
| P1-13 | 骨架 v5 动效 8 族全生命周期：enter/text/data/link 终态与精确还原、scroll 族滚动驱动（read-progress/scrub-draw/parallax/sticky）、ptr 族程序化指针写入与 freeze、reduced-motion 全静态 | harness T19（motion-v5 deck） | ✅ 2026-09-19 |
| P1-14 | v5 deck 编辑侧：交互层冻结、mask-lines 行叶子编辑、gradient-flow 编辑态还原本色、pointer/scroll 运行时变量净化、产物内容（--val/--pin-i 等）保留、重载幂等 | harness T20 | ✅ 2026-09-19 |
| P1-15 | G 期主题库：9 重主题 × ≥3 配色变体 Schema 校验（G0 三必填/变体字段集/G9 css 白名单/.mt-* 全库唯一/两两七层 diff ≥3/分化声明逐层核验） | sync-themes.mjs（含否定测试） | ✅ 2026-09-19 |
| P1-16 | G 期面板：主题卡变体色点切换、装饰主导分组、导出意图含变体合并 tokens + theme_css + 双 SLOT 文案 | harness T9 | ✅ 2026-09-19 |
| P1-17 | G 期画廊主题样张：9 页同内容不同主题渲染，零溢出零重叠、编辑器往返幂等 | harness T18 + T1-components-gallery | ✅ 2026-09-19 |
| P1-18 | G 期样张肉眼验收：9 主题同一封面内容一眼可辨（装饰/容器/质感/字体分化） | 人工 | ⏳ 待人工 |
| P1-19 | I 期主题库：20 重主题两两 190 对七层 diff ≥3 全过；变体/G9 css/类名唯一性校验 | sync-themes.mjs | ✅ 2026-09-20 |
| P1-20 | I 期撞脸矩阵：gallery 20 页同内容样张零溢出零重叠、往返幂等 | harness T18 + T1 | ✅ 2026-09-20 |
| P1-21 | J 期同题终验：本地优先软件 × a1/e2/e6 三 deck，呈现发散三案留档（各 NOTES.md），自检全过并加入 T1 回归 | harness T1 ×3 + j_render_check.py | ✅ 2026-09-20 |
| P1-22 | 撞脸矩阵与 J 三 deck 肉眼验收：20 主题同内容一眼可辨、三 deck 同内容一眼不同 | 人工 | ⏳ 待人工 |
| P1-23 | K 期章节跳转：数字键/nav-link/End 三通道、编辑态拦截不跳转、老 deck 无章节无副作用 | harness T22 | ✅ 2026-09-20 |
| P1-24 | K 期 v7 动效：mend-bar 双态修复条（--from/--val 产物内容）、data-rotate 轮转 in-view 生命周期 + freeze 清空 + 净化无残留 | harness T22 | ✅ 2026-09-20 |
| P1-25 | K 期高密度验收 deck（smartforge-c1）：8 页高密度、六型容器全用、四层字阶、零溢出零重叠 | harness T1/T18 + k_nav_check.py | ✅ 2026-09-20 |
| P1-26 | K 期高密度肉眼验收：smartforge-c1 层次感与跳转体验 | 人工 | ⏳ 待人工 |

## 已知限制（非缺陷）

- 独立模式跨目录打开 deck 时编辑器内图片预览坏（产物正确）；待 blob URL 预览方案。
- 首趟保存的白名单 diff（布尔属性 `=""` 化等）为 HTML 解析规范化，稳定且一次性。

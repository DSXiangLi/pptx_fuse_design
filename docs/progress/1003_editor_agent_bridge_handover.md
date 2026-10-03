# 编辑器↔Agent Bridge v2：完整交接文档

> 日期：2026-10-03
>
> 交接状态：P0–P3 Linux 自动实现已完成；P4 已完成故障组、单页协议性能基线和完整历史回归。25 个标准 deck 已可信恢复并核验，`run_e2e.py` 55/55 与 `o_tri_view` 通过；真正 Bridge 真实大 deck/10倍素材、完整性能样本、真实 MCP 宿主及人工交付验收仍待完成。
>
> 下一会话唯一入口：先阅读本文，再按“第 10 节：下一步执行计划”继续。
>
> Git 状态：本轮未执行 `git add`、`git commit` 或 `git push`；暂存区为空。

## 1. 本次工作的原始目标

本次工作的目标不是简单地给编辑器增加几个 MCP 按钮，而是将现有纯静态 `editor.html` 与开发侧 AI coding agent 连接成一个可恢复、可审计、不会静默覆盖用户内容的协作闭环：

```text
用户明确提交意图
→ Bridge 持久接收
→ Agent 可靠认领
→ Agent 只修改独立 attempt 工作副本
→ 执行真实技能验收
→ 带 revision CAS 和 validation 证据发布
→ 编辑器在保护用户草稿的前提下刷新
→ 用户继续修改或提交下一轮意图
```

必须同时支持两个入口：

1. **从零创作**：没有 HTML 文件时打开脑暴页，用户冻结需求简报并明确发送，Agent 生成首版 HTML，原会话首次加载作品。
2. **已有作品优化**：打开已有 HTML，用户保存文字/图片修改，或提交主题、批注、插画、整页烙入、导出等请求，Agent 完成后页面安全刷新。

本次还要求：

- 从第一性原理审核原 MCP 化设计，而不是直接照旧方案编码。
- 形成完整优化后的总体设计、公共协议、一致性/恢复设计、执行计划和测试验收计划。
- 文档审核通过后再进入开发。
- 转换能力继续属于 `skills/html-pptx/`，不得迁入 daemon。
- 保持编辑器纯静态、无框架、无构建步骤；无 Bridge 时继续支持 FSAA、下载和宿主 `postMessage`。
- 自动化测试只操作临时工作区，不改写真实 deck，不污染用户 Git HEAD 或暂存区。

## 2. 第一性原理结论与冻结边界

### 2.1 请求、事实和草稿必须分离

- 保存 HTML、替换资产和回滚是已经发生的 **A 类事实**，走 revision CAS 和持久 receipt，不唤醒模型。
- 需求简报、设计修改、批注、插画、烙入和导出是需要 Agent 执行的 **B 类请求**，走 UUID、服务 seq、attempt、lease、validation 和显式 complete/fail。
- 浏览器 DOM、未发送批注、脑暴表单和设计表单是用户草稿，不能因为远端发布成功就自动清空。

### 2.2 持久接收不等于执行完成

系统分别回答三个问题：

1. 请求是否已经可靠接收。
2. 哪个 consumer 正在处理哪个 attempt。
3. 候选结果是否仍基于当前正式 revision，能否安全发布。

不能再用一个页面游标或 `after_seq` 隐式表达三种确认。

### 2.3 Agent 不能直接改正式文件

Agent 只能修改：

```text
.pptx-html/jobs/<intent_id>/attempt-<N>/work/<relative-deck>
```

正式目标只允许由 Bridge 在验证通过后发布。retry 创建新的 attempt 路径；旧副本保留，不复用、不自动删除。

### 2.4 SQLite 是状态真相

- session、consumer、client、intent、attempt、retry receipt、write receipt、event、draft、snapshot、publication 都以 SQLite/WAL 为状态真相。
- 文件系统 journal、snapshot、bundle manifest 和 Git 专用 ref 用于保护发布和恢复。
- 浏览器 IndexedDB 只保护本地草稿，不能替代服务端状态。

### 2.5 不承诺无法保证的 exactly-once

Bridge 可以保证自身持久状态、发布和 receipt 的幂等重放，但不能保证外部模型调用或付费生图 API 恰好执行一次。processing lease 过期后转为 interrupted；只有用户明确 retry 才创建下一 attempt，并提示可能重复外部费用。

### 2.6 转换仍是技能

Bridge 的 `--convert` 和 `/api/convert` 只是在 attempt 工作副本内触发：

```bash
python3 skills/html-pptx/scripts/export-pptx.py <work_path> --force --track both
```

导出算法、字体处理、渲染门禁、PPTX 组装和交付规则仍全部位于 `skills/html-pptx/`。`formats` 只影响用户下载选择，不能减少完整双轨重建和验收范围。

## 3. 已完成的设计文档

以下文档已经完成并经过两轮独立交叉审核：

| 文档 | 作用 | 状态 |
|---|---|---|
| `docs/design/editor-agent-bridge.md` | 总体问题、第一性原理、用户流程、总体架构和取舍 | 已完成 |
| `docs/design/editor-agent-bridge-protocol.md` | 五个 MCP 工具、HTTP 路由、SSE、身份、状态机、错误和重试公共契约 | 已完成 |
| `docs/design/editor-agent-bridge-consistency.md` | revision、bundle、Git、CAS、journal、草稿、鉴权、路径与恢复算法 | 已完成 |
| `docs/progress/1002_editor_agent_bridge_plan.md` | P0–P4 实施计划、文件分工、出口条件和实际执行记录 | 已完成并记录当前结果 |
| `docs/test_acceptance/editor-agent-bridge.md` | 四层证据、测试矩阵、故障、性能、人工验收和实际结果 | 已完成并记录当前结果 |
| `docs/howto/editor-agent-bridge.md` | 安装、手动模式、MCP 模式、五工具循环、错误处理和安全说明 | 已完成 |
| `docs/design/README.md` | 设计文档索引 | 已同步 |
| `docs/progress/README.md` | 进度文档索引 | 已同步 |
| `AGENTS.md` | 当前专项状态、架构和测试边界 | 已同步 |

设计审核期间解决的关键问题：

1. 无 deck 脑暴到首次生成和首次加载的完整状态流。
2. consumer 首次注册、await acquire、close 后必须重新 open。
3. UUID、服务 seq、attempt 和 retry receipt，移除隐式确认。
4. attempt 独立副本路径和 retry 不复用旧副本。
5. validation 的精确 schema 和必需 checks。
6. bundle revision、CAS、journal、snapshot 和 Git 专用 ref。
7. 手动 `--deck` / `--new` bootstrap 和非 Git 首存确认。
8. Bridge 导出固定完整 `--track both`。
9. 持久 intent query，不依赖 SSE 永久保存。
10. 路由级 payload 限额。
11. `resource_path` 明确作为同源静态 URL 的相对路径。
12. MCP 可选 `export_source_revision` 缺省时不发送非法 `null`。
13. 正常 stop 先回收活动 HTTP/SSE 线程，再关闭 SQLite。

## 4. 已完成的生产实现

### 4.1 `tools/bridge_core.py`

已实现标准库 Bridge 核心，主要能力包括：

- SQLite schema、WAL、迁移和未来 schema 拒绝。
- 每个规范 workdir 单 daemon 和 `flock` 互斥。
- `serve.json` 发现文件、instance 身份、management/browser/bootstrap 凭证。
- session、consumer、client、intent、attempt、retry/write receipt、event、draft、snapshot、publication。
- source revision、export revision 和完整 bundle revision。
- intent 接收、认领、lease、重投递、取消、retry 和持久 query。
- attempt 工作副本创建与隔离。
- A 类 save、asset、rollback 的 CAS 和 receipt。
- Git 专用 `refs/pptx-html/...` 与隔离 `GIT_INDEX_FILE`，不移动用户 HEAD，不修改真实暂存区。
- publication journal、故障注入、旧状态恢复、DB committed 后修复、第三种字节冻结。
- `dir_fd`、`O_NOFOLLOW`、路径规范化、符号链接和危险硬链接拒绝。
- SVG 主动内容检查和未知受管扩展拒绝。
- convert claim 时清除继承的旧 export，防止旧轨混入新结果。
- 23 个公开协议路由、内部 stop 路由和 7 类 SSE 事件。
- Host、Origin、Bearer、body 大小和静态资源隔离。
- `revision <work_path>` 内部只读 CLI。
- 正常 shutdown 的活动 socket 断开、请求线程回收和数据库关闭顺序。

### 4.2 `tools/bridge_mcp.py`

已使用官方 MCP SDK 1.28.x 实现 stdio 薄代理，恰好暴露五个工具：

1. `open_editor`
2. `await_intent`
3. `push_update`
4. `get_status`
5. `close_session`

代理负责：

- 启动或附着 daemon。
- 保存 management token，不向浏览器暴露。
- consumer heartbeat。
- 将协议错误映射为 MCP 工具错误。
- 大 payload 返回摘要和绝对 `intent_file`。
- validation 精确序列化。

官方依赖限定为：

```text
mcp>=1.28,<2
```

daemon 和手动编辑模式仍只依赖 Python 标准库。

### 4.3 `tools/edit.py` 与 `tools/start-webui.sh`

`tools/edit.py` 已重构为 Bridge v2 统一入口：

```text
--deck REL
--new [REL]
--mcp
--stop
--convert
--no-browser
--port
```

`tools/start-webui.sh` 已透传手动目标参数并显式附加 `--convert`。转换逻辑仍不在服务内。

### 4.4 `editor.html` v3.2

已完成：

- Bridge 状态条和任务 UI。
- URL fragment token 读取后立即清理。
- sessionStorage、client_id 和 browser heartbeat。
- 鉴权 fetch、fetch-SSE 解析、断线重连和 7 类事件消费。
- 持久 intent query、retry 和 cancel。
- 无 deck 脑暴、明确发送和首次生成加载。
- 需求、设计、批注、插画、烙入、导出六类 intent。
- IndexedDB 本地草稿和服务 draft。
- load、manifest、save generation/epoch，防迟到响应覆盖新内容。
- dirty、active edit、表单和 pending 风险保护。
- save、asset、rollback receipt 和 revision CAS。
- export/assets 强制缓存刷新。
- 使用后端 `resource_path` 构造同源静态 URL，不从绝对路径猜 basename。
- 无 Bridge 时保留 FSAA、下载、复制和嵌入 `postMessage`。

### 4.5 `skills/html-pptx/SKILL.md`

已加入可选 Bridge 协作工作流：

```text
open_editor
→ await_intent
→ 读取 intent_file
→ 只修改 work_path
→ 执行原技能验收
→ push_update complete/fail
→ 用户继续时重新 await
→ 明确结束时 close_session
```

已写明六类 intent 映射、validation、完整双轨导出、冲突、恢复和 close 纪律。

## 5. 已完成的测试实现

### 5.1 `tests/harness/test_bridge_core.py`

当前有 21 个 unittest，覆盖：

- schema/WAL 和迁移。
- source revision 黄金值。
- open/register/acquire/close/reopen。
- intent UUID 幂等、claim 重投递和 attempt 路径。
- retry receipt 和独立 attempt。
- complete validation、发布和 receipt 重放。
- complete 响应丢失和重启恢复。
- intent/claim/open/close/retry 响应丢失。
- A 类 save/asset/rollback 响应丢失。
- save CAS、Git index 隔离。
- 外部副作用不自动重演。
- 双 consumer 和双 daemon 排他。
- publication 各故障点恢复。
- DB committed 后旧目标修复。
- 第三方字节冻结。
- 符号链接/硬链接拒绝。
- SVG 主动内容和未知扩展拒绝。
- convert 清除旧 export。

### 5.2 `tests/harness/r_bridge_check.py`

已实现组：

```text
transport
sdk
http
security
ui
integration
fault
performance
```

无参数默认运行：

```text
transport,sdk,http,ui,fault,integration
```

`security` 与 `http` 共用真实 daemon 入口；`performance` 必须显式选择。

### 5.3 `tests/harness/run_e2e.py`

已接入 `T29-bridge`。T12 已从旧 v1.6 companion 流程迁移为真实手动 daemon + bootstrap/browser bearer 流程，覆盖鉴权、CAS、receipt、draft、snapshot 历史与 Git 专用 ref 隔离；修复历史 UI 消费 `snapshot_id` 后，完整入口 T1–T29 共 55 项全部通过。

## 6. 已执行验证与真实结果

### 6.1 定向回归

| 命令 | 结果 | 耗时 |
|---|---|---:|
| `python3 -m unittest tests.harness.test_bridge_core -v` | 21/21 PASS | 5.894s |
| `python3 tests/harness/r_bridge_check.py` | 默认六组 PASS，退出码0 | 20.846s |
| `python3 tests/harness/k_brief_check.py` | ALL PASS | 2.483s |
| `python3 tests/harness/o_tri_view_check.py` | ALL PASS | 107.329s |

`r_bridge_check.py` 默认六组为 transport、sdk、http/security、ui、integration、fault，不包含 performance。以上自动结果不替代真实 Kimi/Codex 宿主。

静态检查：

```bash
python3 -m py_compile \
  tools/edit.py \
  tools/bridge_core.py \
  tools/bridge_mcp.py \
  tests/harness/r_bridge_check.py \
  tests/harness/test_bridge_core.py \
  tests/harness/run_e2e.py
bash -n tools/start-webui.sh
git diff --check -- editor.html tools skills/html-pptx tests/harness docs AGENTS.md
```

结果：全部通过。

### 6.2 单页协议性能基线

已有忽略目录内报告：

- `tests/harness/results/bridge/metrics.json`
- `tests/harness/results/bridge/report.json`

环境：Linux arm64、Python 3.13.11、MCP SDK 1.28.0、Git 2.20.1、8 CPU。fixture 只有 1 页、456B，因此只能作为协议基线。

| 指标 | 样本 | P50 | P95 | Max | 判定 |
|---|---:|---:|---:|---:|---|
| status | 100 | 1.115ms | 2.624ms | 3.860ms | PASS |
| browser heartbeat | 100 | 2.674ms | 4.396ms | 8.257ms | PASS |
| 小 intent | 200 | 3.811ms | 7.267ms | 11.794ms | PASS |
| 近 1MiB intent | 20 | 20.624ms | 45.130ms | 46.413ms | PASS |
| 25s await | 1 | 25002.970ms | 25002.970ms | 25002.970ms | 有界阈值 PASS，样本不足 |
| 120s await | 1 | 120009.915ms | 120009.915ms | 120009.915ms | 有界阈值 PASS，样本不足 |

资源快照：

```text
RSS 24.867 MiB → 32.949 MiB，增长 8.082 MiB
FD 9 → 9
```

这不是 54 页大 deck、30 分钟稳定性或完整冷启动分布认证。

### 6.3 fixture 恢复与零污染证据

- 完整枚举 25 个标准 deck；恢复前原有 7 个可用，其中 `cmb-retail` 实际存在但被 `.gitignore` 隐藏。
- 18 个缺失目录从可信 Git 删除前统一快照 `dd5d87940f9463a3b60972f0c9b288195a2264d5` 原字节恢复，共 47 个文件；Git blob 核验 missing=0、mismatch=0。
- `cmb-retail` 对删除前 `5fdd8c723e26594e7334080ba2c06cdf5e5733c1` 的 100 个历史受控文件核验 missing=0、mismatch=0。
- 恢复后的全 fixtures 基线为 806 entries / 789020265 bytes；所有测试后复核 added=0、removed=0、changed=0。

### 6.4 完整历史回归与 T12 修复

首次运行完整 `python3 tests/harness/run_e2e.py`，真实失败于 T12：旧 v1.6 测试无鉴权 POST `/api/save`，与 Bridge v2 的 bootstrap/browser bearer、session/base_revision、专用 ref、snapshot 和 receipt 协议冲突。

T12 迁移后继续检出真实生产消费者 bug：`editor.html` 历史 UI 把可空 Git commit `v.hash` 当稳定身份并调用 `slice()`。现已改为 `snapshot_id || hash`，commit hash 仅作可选显示，rollback 传稳定版本 id，同时保留旧 versions schema 只有 `hash` 时的 fallback。生产鉴权与 revision CAS 未放松。

修复后结果：

```text
python3 tests/harness/run_e2e.py
==== 汇总：55 项，55 PASS，0 FAIL ====
```

耗时约 860 秒，T1–T29 全部通过。该结果证明完整历史 harness 与其现有子测试通过；不得把其中 `cmb-retail` 的 T1/导出子测试冒称 PERF-03、CNS-08 或完整54页 Bridge convert/P4-C。

## 7. 本轮最后修复的关闭竞态

最终回归曾暴露：活动 SSE 请求线程在 daemon shutdown 后仍可能访问已经关闭的 SQLite，随后尝试向已断连接写错误响应，产生：

```text
sqlite3.ProgrammingError: Cannot operate on a closed database
BrokenPipeError
```

最终修复：

1. `BridgeCore.begin_shutdown()` 先设置 `ready=false` 和 stop event，并唤醒 session conditions。
2. `BridgeHTTPServer` 跟踪活动 request sockets。
3. shutdown 主动断开活动 SSE/keep-alive sockets。
4. `server_close()` 等待所有 request threads 退出。
5. 之后才调用 `core.close()` 关闭 SQLite、workdir lock 和安全目录句柄。
6. SSE 循环显式检查 stop event。

修复后重新运行默认 `r_bridge_check.py`，六组全部 PASS，关闭阶段无 traceback。

## 8. 当前准确状态

| 阶段 | 状态 | 可以声称的结论 | 不能声称的结论 |
|---|---|---|---|
| P0 transport | 完成，Linux 自动 | 官方 SDK stdio、initialize/list/call、并发、取消和有界等待通过 | 真实 Kimi/Codex 宿主通过 |
| P1 core/protocol | 完成，Linux 自动 | 五工具、SQLite、CAS、receipt、journal、Git 隔离、安全和恢复通过 | 硬件断电全耐久认证 |
| P2 editor | 完成，Linux 自动 | Playwright 无 deck、保存世代、dirty 保护、SSE、fragment 清理及手动 bootstrap 历史 UI/CAS 回滚通过 | 真实宿主中的全部交互通过 |
| P3 skill integration | 完成，确定性自动范围 | SKILL 契约、真实 MCP/HTTP driver、work_path、validation 和发布闭环通过 | 真实大模型创作、付费生图和真正 Bridge 54页 convert 通过 |
| P4 full acceptance | 部分完成 | fault、单页协议性能、25 deck 的 `run_e2e` 55/55、独立 `o_tri_view` 与 fixture 零变化核验通过 | PERF-03/CNS-08、完整性能样本、真实宿主、Office/WPS、生图和硬件掉电通过 |

本轮总体结论必须保持：

> P0–P3 Linux 自动闭环已完成，P4 部分通过；完整历史回归已经通过，但真正 Bridge 真实大 deck/10倍素材、完整性能样本、真实宿主和人工验收仍未完成，不得宣称 P4 全量完成。

## 9. 当前工作区与版本控制状态

### 9.1 本轮核心 modified/untracked 文件

```text
M  AGENTS.md
M  docs/design/README.md
M  docs/progress/README.md
M  editor.html
M  skills/html-pptx/SKILL.md
M  tests/harness/run_e2e.py
M  tools/edit.py
M  tools/start-webui.sh
?? docs/design/editor-agent-bridge.md
?? docs/design/editor-agent-bridge-protocol.md
?? docs/design/editor-agent-bridge-consistency.md
?? docs/howto/editor-agent-bridge.md
?? docs/progress/1002_editor_agent_bridge_plan.md
?? docs/progress/1003_editor_agent_bridge_handover.md
?? docs/test_acceptance/editor-agent-bridge.md
?? tests/harness/r_bridge_check.py
?? tests/harness/test_bridge_core.py
?? tools/bridge_core.py
?? tools/bridge_mcp.py
```

### 9.2 前期研究文件

以下文件来自本次前期调研或用户已有工作，必须保留，不要在下一会话擅自删除：

```text
M  docs/research/source-survey.md
?? docs/research/agent-webui-bridge.md
?? docs/research/projects/cowart.md
?? docs/research/projects/deepseek-harness.md
```

### 9.3 仓库边界注意事项

当前 Git 顶层可能位于项目目录之上，直接运行不带 pathspec 的 `git status --short` 会列出大量与本项目无关的用户目录变化。下一会话必须使用：

```bash
git status --short -- .
git diff --cached --name-only -- .
git diff --check -- editor.html tools skills/html-pptx tests/harness docs AGENTS.md
```

禁止清理、还原或提交项目目录外的变化。

### 9.4 当前运行态

- 没有已知残留 `tools/edit.py` 或 `bridge_mcp.py` 进程。
- `tools/__pycache__` 和 `tests/harness/__pycache__` 已清理。
- 测试性能报告位于 `.gitignore` 忽略目录，不进入提交。
- 暂存区为空。
- 未执行 commit/push。

## 10. 下一步执行计划

可信 fixture 恢复与完整历史回归已经完成。下一会话第一优先级转为尚无证据的真正 Bridge 大 deck/10倍素材和完整性能样本；每一步仍必须使用临时副本并保留源 fixture 零变化证明。

### 10.1 P4-A：fixture 恢复（已完成）

25 个标准 deck 已完整枚举。恢复前原有 7 个可用，其中 `cmb-retail` 实际存在但被 `.gitignore` 隐藏；18 个缺失目录从可信 Git 删除前统一快照 `dd5d87940f9463a3b60972f0c9b288195a2264d5` 原字节恢复，共 47 个文件，Git blob 核验 missing=0、mismatch=0。`cmb-retail` 对删除前 `5fdd8c723e26594e7334080ba2c06cdf5e5733c1` 的 100 个历史受控文件核验 missing=0、mismatch=0。

恢复后的全 fixtures 基线为 806 entries / 789020265 bytes；所有测试后复核 added=0、removed=0、changed=0。未合成弱化 fixture，未通过删测试或改路径制造绿灯。

### 10.2 P4-B：完整标准回归（已完成）

已完成核心 unittest、默认 r_bridge、`k_brief_check.py`、独立 `o_tri_view_check.py` 和完整 `run_e2e.py`。完整入口最终为 55项、55 PASS、0 FAIL，T1–T29 全通过；修复过程中的 T12 真实失败和消费者修复见 §6.4。

此结论只覆盖既有标准 harness。它不自动完成下一节 PERF-03/CNS-08 的真正 Bridge 真实大 deck/10倍素材场景，也不替代真实宿主和人工交付验收。

### 10.3 P4-C：真实 deck 集成与规模测试

#### 目标

在已恢复且通过历史 harness 的 `bake-mix` 和 54 页 `cmb-retail` 上，补齐真正 Bridge 事件→attempt→技能门禁→发布→可编辑 UI 的端到端与规模证据；现有 T1/导出子测试不能替代本节。

#### 必测场景

1. `bake-mix`：
   - 已有 deck open。
   - 源层编辑。
   - 批注或设计 intent。
   - bake/convert 请求。
   - work_path 中执行真实技能门禁。
   - complete 后 editor 正面、背面、对比和下载产物刷新。
2. `cmb-retail` 54 页：
   - open/manifest/status 延迟。
   - 文字保存和 CAS。
   - 同名资产刷新。
   - 54 页导出和 validation。
   - publication 和 editor 可编辑时间。
   - 原 fixture 字节不变。
3. 10 倍素材副本：
   - 在 2GiB/20,000 文件上限内构建临时副本。
   - 记录 hash、复制、seal、发布、保存、恢复耗时。
   - 记录峰值 RSS、FD 和 SQLite 锁等待。
   - 超限样本必须预先拒绝，不得部分复制后失败。

#### 验收标准

- PERF-03 与 CNS-08 有真实报告。
- 所有修改只发生在临时副本和 attempt work_path。
- complete 后正式副本与 editor 显示一致。
- 双轨导出完整：`deck.pptx`、`deck-vector.pptx`、`deck.pdf`、native 页图和 manifest。
- 任一轨失败时不发布假 fresh。

### 10.4 P4-D：补齐性能样本和稳定性

#### 目标

完成验收计划中尚不足的统计样本，而不是只保留单次 long poll。

#### 待完成项目

- PERF-04：25 秒 await ×20；120 秒 await ×3。
- PERF-05：独立冷启动 ×20。
- PERF-06：30 分钟空闲稳定性；完整 100 次连接/断开。
- 活动 SSE、keep-alive 和 long poll 状态下反复正常 stop。
- 记录 RSS、FD、线程、子进程、端口和 SQLite 文件状态。

#### 验收标准

- 报告保留所有原始样本，不只给平均值。
- 给出 P50、P95、Max 和环境负载。
- 最终 FD/线程/子进程回到基线容差。
- 不通过关闭 fsync、跳过 validation 或减少数据规模改善数字。

### 10.5 P4-E：真实 Kimi 与 Codex MCP 宿主验收

#### 目标

证明官方 SDK conformance 可以在真实宿主中完成用户工作流，而不是只在测试 ClientSession 中成立。

#### 每个宿主分别记录

- 宿主名称和版本。
- MCP 配置方式，配置中只出现绝对 workdir 和启动命令，不记录 token。
- initialize/list_tools 结果恰好五工具。
- 无 deck open → brief intent → await → work_path → complete → editor 首次加载。
- 已有 deck open → design/anno intent → complete → 页面刷新。
- 25 秒和 120 秒 await 行为。
- cancellation 和重新 attach。
- close 后必须重新 open。
- 10 分钟真实模型会话的调用次数、时间和成本。
- stdout 无协议外日志，stderr 脱敏。

#### 验收标准

- Kimi 和 Codex 分别有独立记录，不能互相替代。
- 不把 SDK 测试结果复制为宿主结果。
- 配置示例不包含 management/browser/bootstrap token。
- 模型退出不关闭用户页面；页面关闭不丢已接收 intent。

### 10.6 P4-F：Office/WPS 与真实付费生图人工验收

#### Office/WPS 目标

对真实双轨交付件进行人工目检：

- PowerPoint 365 打开、播放、编辑和保存。
- WPS 打开、播放、编辑和保存。
- 字体、行距、CJK/拉丁混排、图表、信息图、烙入页和图片无明显错位。
- 可编辑轨文本仍可编辑。
- 保真轨视觉稳定。
- 不以 LibreOffice 参考渲染替代 Office/WPS 结论。

#### 付费生图目标

只在用户明确授权费用后执行：

- illustration intent 必须已有插画模式授权。
- bake intent 必须明确页码和代表页审批。
- 记录外部调用次数、费用和失败。
- 失败不伪造 `generated`，不自动重复付费调用。
- retry 明确提示可能重复费用。

### 10.7 P4-G：最终文档回扫与交付判定

所有验证完成后：

1. 更新 `docs/progress/1002_editor_agent_bridge_plan.md` 的阶段状态和执行记录。
2. 更新 `docs/test_acceptance/editor-agent-bridge.md` §16，逐项从 BLOCKED/NOT_RUN 转为 PASS 或保留真实阻断。
3. 更新本文的当前状态和剩余任务。
4. 更新 `AGENTS.md` 当前专项。
5. 更新 `docs/howto/editor-agent-bridge.md` 中任何因真实宿主产生的配置差异。
6. 执行提交前文档回扫和修复代码验收。
7. 运行最终静态检查和标准测试。
8. 只有用户明确要求时才执行 `git add`、`git commit` 或 `git push`。

最终“全量完成”的必要条件：

- 定向 Bridge 测试通过。
- 标准 `run_e2e.py` 全通过。
- 真实 fixtures 完整且未被测试污染。
- 真实大 deck 与规模性能通过。
- Kimi/Codex 分别验收。
- Office/WPS 人工验收。
- 付费生图若属于本次交付范围，必须有用户授权和真实记录；若不执行，最终报告必须保留 NOT_RUN。

## 11. 下一会话开始时的必读顺序

下一会话不要从代码猜协议，按以下顺序阅读：

1. `AGENTS.md`
2. `docs/progress/1003_editor_agent_bridge_handover.md`
3. `docs/design/editor-agent-bridge.md`
4. `docs/design/editor-agent-bridge-protocol.md`
5. `docs/design/editor-agent-bridge-consistency.md`
6. `docs/progress/1002_editor_agent_bridge_plan.md`，重点 §11
7. `docs/test_acceptance/editor-agent-bridge.md`，重点 §16
8. `docs/howto/editor-agent-bridge.md`
9. `skills/html-pptx/SKILL.md` 中 Bridge 协作章节

如果开始恢复 fixtures，还应读取：

- `tests/harness/run_e2e.py`
- `tests/harness/o_tri_view_check.py`
- `tests/harness/m_bake_check.py`
- `tests/harness/n_fidelity_check.py`
- `tests/harness/p_editable_check.py`
- `tests/harness/q_capacity_check.py`

## 12. 关键代码入口

| 入口 | 位置 | 说明 |
|---|---|---|
| BridgeCore | `tools/bridge_core.py` | 状态、文件、发布、安全和 HTTP 核心 |
| shutdown 生命周期 | `tools/bridge_core.py` 的 `begin_shutdown`、`BridgeHTTPServer` | 活动请求先退出，SQLite 后关闭 |
| MCP 五工具 | `tools/bridge_mcp.py` | 官方 SDK stdio 薄代理 |
| CLI | `tools/edit.py` | 手动、MCP、daemon、stop、convert 分流 |
| 浏览器 Bridge 运行时 | `editor.html` 的 Bridge v2 区段 | token、heartbeat、SSE、draft、intent、刷新 |
| 技能协作 | `skills/html-pptx/SKILL.md` | Agent 对 intent/work_path/validation 的执行纪律 |
| 核心测试 | `tests/harness/test_bridge_core.py` | 21 个状态、安全和恢复测试 |
| 综合测试 | `tests/harness/r_bridge_check.py` | transport 到 performance 的分组 harness |
| 全量入口 | `tests/harness/run_e2e.py` | T1–T29 项目标准回归 |

## 13. 不得回退的协议与安全红线

下一会话修改代码时不得破坏以下约束：

1. MCP 工具保持恰好五个，不新增任意 shell 或文件发布工具。
2. Agent 只修改 `work_path`，不直接写正式 deck。
3. complete 必须带真实 validation，不允许仅凭“完成了”发布。
4. source/export revision 分离；旧 export 不得伪装 fresh。
5. Bridge convert 永远完整 `--track both`。
6. page、daemon、consumer 生命周期独立。
7. close 后同 consumer 必须重新 open，heartbeat 不能复活。
8. retry 必须显式确认并创建新 attempt。
9. 用户草稿不能因远端更新被静默清除。
10. management token 不进入浏览器、HTML、日志或示例配置。
11. browser token 只经 fragment 接收、转 sessionStorage、立即清 fragment。
12. SSE 使用 Authorization fetch，不把 token 放 query。
13. 不修改用户 HEAD、真实 Git index 或现有 Git 配置。
14. 路径安全必须继续拒绝穿越、符号链接和危险硬链接。
15. publication 遇第三种字节必须冻结，不覆盖外部修改。
16. stop 必须先回收活动请求线程，再关闭 SQLite。
17. 测试只操作临时工作区和 fixture 副本。
18. 缺 fixture 时诚实 BLOCKED，不伪造绿灯。
19. 转换算法只进技能，不进入 `tools/edit.py` 或 Bridge 核心。
20. 未真实执行 Kimi/Codex、Office/WPS、付费生图时继续标记 NOT_RUN。

## 14. 建议的新会话启动提示

重启后可直接向新会话发送：

```text
请先阅读 AGENTS.md 和 docs/progress/1003_editor_agent_bridge_handover.md，严格按交接文档继续 editor-agent Bridge v2 的 P4 验收。可信 fixtures 与完整历史回归已经完成；下一步只补真正 Bridge 真实大 deck/10倍素材、完整 PERF-04/05/06 样本、真实 Kimi/Codex 宿主及人工环境证据，不得用 run_e2e 的 cmb T1/导出子测试代替 P4-C。不要执行 git commit/push，除非我明确授权。
```

## 15. 最终交接结论

当前代码和文档已经形成可工作的 Linux 自动 Bridge 闭环：页面明确提交、Agent 可靠认领、attempt 副本修改、真实 validation、CAS 发布、receipt 重放、草稿保护和页面刷新均已落地。核心 unittest 21/21、默认 r_bridge 六组、脑暴回归、独立 `o_tri_view` 和完整 `run_e2e` 55/55 均通过；25 个标准 deck 已从可信来源恢复并完成测试前后零变化核验。T12 已迁移到真实手动 daemon + bootstrap/browser bearer/CAS 流程，历史 UI 已统一使用 `snapshot_id` 稳定回滚并兼容旧 `hash` schema。

剩余工作集中在 P4 未有证据的范围，而不是继续扩展协议：PERF-03 真正 Bridge 真实大 deck 事件→可编辑 UI、CNS-08 54页×10倍素材、PERF-04/05/06 完整样本、真实 Kimi/Codex、Office/WPS、经授权付费生图和硬件掉电仍为 BLOCKED/NOT_RUN。在这些证据完成前，状态必须保持“P0–P3 完成，P4 部分完成”。

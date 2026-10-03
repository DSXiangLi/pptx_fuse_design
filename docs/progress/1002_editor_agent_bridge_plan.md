# 编辑器↔Agent 桥 v2：分阶段执行计划

> 2026-10-03 · 状态：P0–P3 Linux 自动实现已落地；P4 已完成故障组、单页协议性能和完整历史回归。25 个标准 deck 已恢复并完成原字节核验，`run_e2e.py` 55/55 与 `o_tri_view` 通过；真实 Bridge 大 deck/10倍素材性能、完整性能样本和人工环境仍未完成。本文保留原计划并在 §8.2、§11 登记真实结果；未列为 PASS 的项目不得推定通过。未提交 Git。
> 规范：[协议与状态机](../design/editor-agent-bridge-protocol.md)（下文简称“协议”）；配套：[一致性与安全](../design/editor-agent-bridge-consistency.md)、[测试验收计划](../test_acceptance/editor-agent-bridge.md)、[外部使用指南](../howto/editor-agent-bridge.md)。协议优先；旧总览的页面 seq / after_seq 隐式确认语义不得沿用。

## 1. 目标、现状与不做什么

`editor.html` v3.2、`tools/edit.py` v2、`tools/bridge_core.py` 与 `tools/bridge_mcp.py` 已形成“页面明确提交 → Agent 可靠认领 → attempt 工作副本验收 → 显式确认发布 → 页面保稿刷新”的 Linux 自动闭环。技能仍负责生成、插画、烙入和转换；bridge 只负责接收、状态、隔离、验收证据核验和发布。

已落地目标：

1. 无 deck 时先脑暴；同一 session 在首次生成发布后加载真实 HTML，不创建伪空文件。
2. 已有 deck 的请求使用 UUID 去重、服务 seq 排序和 attempt 防迟到确认；A 类保存/资产/回滚使用 receipt/CAS。
3. SQLite 是状态真相；副本、journal、快照、Git 专用 ref 与 revision CAS 保护磁盘；浏览器 IndexedDB/服务草稿独立保护输入。
4. 官方 SDK stdio 代理暴露五个 MCP 工具；daemon 保持标准库，手动模式不依赖 `mcp` 包。
5. 自动结果与真实宿主/模型/Office/WPS/付费生图结果分开登记。

不做：页面内模型调用；自写 JSON-RPC/MCP 传输；无限 long poll；任意 shell / 任意发布源工具；daemon 实现转换；多 deck 共用同一受管目录；全局文件系统事务或外部生图恰好一次保证；自动修改用户宿主配置。测试仍只操作临时工作区，不在真实 deck 上做破坏性写入。

## 2. 事实、前置闸门与文件分工

### 2.1 2026-10-03 当前事实与未测项

- 生产实现已存在：`tools/bridge_core.py`、`tools/bridge_mcp.py`、`tools/edit.py` v2、`editor.html` v3.2；`skills/html-pptx/SKILL.md` 已写入五工具循环和 validation 纪律。
- 本机自动环境：Linux arm64、Python 3.13.11、官方 `mcp` SDK 1.28.0、Git 2.20.1；Playwright UI 组实跑通过。SDK通过不代表真实 Kimi/Codex 宿主通过。
- 核心命令 `python3 -m unittest tests.harness.test_bridge_core -v` 于 2026-10-03 实跑 **21/21 PASS，5.894s**。
- `python3 tests/harness/r_bridge_check.py` 默认组实跑 **transport、sdk、http/security、ui、integration、fault 全部 PASS，20.846s**；默认组不包含 performance。
- `python3 tests/harness/k_brief_check.py` 实跑 **ALL PASS，2.483s**；`python3 tests/harness/o_tri_view_check.py` 实跑 **ALL PASS，107.329s**。
- 完整枚举得到 25 个标准 deck：原有 7 个可用，其中 `cmb-retail` 实际存在但被 `.gitignore` 隐藏；其余 18 个缺失目录从可信 Git 删除前统一快照 `dd5d87940f9463a3b60972f0c9b288195a2264d5` 按原字节恢复，共 47 个文件，Git blob 核验 missing=0、mismatch=0。`cmb-retail` 对删除前 `5fdd8c723e26594e7334080ba2c06cdf5e5733c1` 的 100 个历史受控文件核验 missing=0、mismatch=0。
- 恢复后 fixtures 基线为 **806 entries / 789020265 bytes**；所有测试后复核 added=0、removed=0、changed=0。
- 首次完整 `run_e2e.py` 真实失败于 T12 的旧 v1.6 匿名 `/api/save` 预期；迁移到手动 daemon + bootstrap/browser bearer 后又检出历史 UI 把可空 `v.hash` 当稳定身份。现已改为 `snapshot_id || hash`，Git commit hash 只作可选显示，rollback 传稳定 id，并保留旧 schema fallback。修复后完整回归 **55项、55 PASS、0 FAIL，约860s**，T1–T29 全通过。
- `r_bridge_check.py --group performance` 的已有报告仍只是单页临时 deck 协议测量。PERF-03 真正 Bridge 真实大 deck 事件→可编辑 UI、54 页×10倍素材与 PERF-04/05/06 完整样本仍 BLOCKED；不得把 `run_e2e` 中 `cmb-retail` T1 或导出子测试冒称 P4-C 完成。
- 尚未执行：真实 Kimi、Codex MCP 宿主；Office/WPS；真实付费生图；硬件掉电耐久性。
- 已修正实现回归点：open/status 返回 `resource_path`，前端优先使用该相对路径；MCP `ValidationEvidence.export_source_revision` 为可省略/`null` 时不会向 daemon 发送非法 null 字段；历史 UI 按 Bridge v2 `snapshot_id` 回滚并兼容旧 `hash` schema。

### 2.2 本轮定稿的公共约束

实现者先完整读取[总览](../design/editor-agent-bridge.md)、协议及一致性文档，不在代码/测试里自创字段。本轮已消除接口前置待决项：

1. 工作副本为 `.pptx-html/jobs/<intent_id>/attempt-<N>/work/<relative-deck>`，首次 attempt=1；旧副本永久保留。retry 必须带 retry_id UUID、expected_attempt、mode='rebuild'、当前 base_revision、confirmed:true；同 retry_id 同报文重放原 attempt，异报文拒绝。旧进程未停不再阻断独立路径重建，但用户须确认可能重复付费。
2. validation=`{candidate_revision,checks,export_source_revision?}`；checks 为非空 `{name,argv:string[],exit_code:int,report_path:string|null}` 列表，仅允许真实 exit_code=0。brief/design/anno/bake/illustrate 必有 render/capacity/images/manifest；convert 必有 export。候选源 revision 使用 `python3 tools/bridge_core.py revision <work_path>` 取得；这是内部只读辅助，不新增 MCP 工具。只有显式 export check 且 export_source_revision 与候选源一致才新设 fresh。
3. heartbeat 的 role 分支、client 首次绑定、A 类 receipt、GET/HEAD 无 Origin 只读例外全部按协议 §7；旧 owner 只能重放同 intent+attempt+consumer 已持久成功 receipt，不能续租或新写。
4. 控制/intent JSON body 2MiB、intent payload 1MiB；save/draft JSON body 64MiB；asset JSON body 48MiB 且原始图片≤32MiB；保留既有大 HTML 保存能力，限额统一定义且逐路由边界测试。
5. P0只验证SDK transport，不依赖P1；P1完成后跑五工具conformance，真实宿主另测。
6. consumer由管理open登记/刷新且不抢owner，返回consumer_state；await原子acquire registered/paused/expired中仍具登记资格者→waiting，已有他有效owner则SESSION_BUSY。close设置requires_open，同consumer必须重复open同session，不可heartbeat复活。
7. 无MCP手动入口固定为CLI `--deck REL` / `--new [REL]`互斥，默认已有index则打开，否则briefing target=index.html；一次性本机bootstrap兑换browser session。手动非Git打开不失败、git_ready=false；首存用户确认init:true，先init及保护后写。MCP open仍自动init。
8. 桥转换永远`--track both`，formats仅选下载件，不减少重建/验收范围；完整三文件、native页图与manifest双轨成功后才全局fresh，禁单轨发布。
9. 浏览器通过POST /api/intents/query按seq分页或指定intent_id查询持久摘要；status新增recoverable_count但不替代query。SSE resync与新origin恢复必须重查，不能只依赖被清理的旧事件。

### 2.3 实际落点

| 文件/目录 | 已实现责任与边界 |
|---|---|
| `tools/edit.py` | v2 CLI 分流：`--mcp`、`--deck/--new`、`--daemon`、`--stop`、`--convert`；复用 bridge core，不承载转换算法 |
| `tools/bridge_core.py` | SQLite 状态机、目录单 deck、认领/lease、revision、attempt 副本、publication journal、恢复、Git 专用 ref、23 个公开协议路由及内部 stop 路由 |
| `tools/bridge_mcp.py` | 官方 MCP SDK stdio 薄代理，恰好五工具；代理持有 management token 并独立心跳 |
| `tools/start-webui.sh` | 透传手动目标参数并附加 `--convert`，仍只触发技能转换 |
| `editor.html` | v3.2 bridge token 绑定、鉴权 fetch、SSE、请求列表/retry/cancel、IndexedDB/服务草稿、CAS 保存/资产/回滚、加载代次和强制产物刷新；历史 UI 以 `snapshot_id` 为稳定回滚标识，旧 schema 回退 `hash` |
| `skills/html-pptx/SKILL.md` | 五工具协作循环、六 intent 映射、work_path 单向写入、真实 validation、恢复与结束纪律 |
| `tests/harness/test_bridge_core.py` | 21 个标准库 unittest，覆盖状态机、安全、幂等、Git 隔离与 publication 恢复 |
| `tests/harness/r_bridge_check.py` | transport/sdk/http/ui/fault/security/integration/performance 选择器；默认组不含 performance |
| `tests/harness/run_e2e.py` | `T29-bridge` 子进程与 T1–T28 全部保留；T12 已迁移为真实手动 daemon + bootstrap/browser bearer/CAS/receipt/snapshot 历史回滚；完整入口 55/55 PASS |
| `docs/howto/editor-agent-bridge.md` | 外部安装、配置、手动启动、五工具循环、安全、恢复和错误指南 |

实现保持单 daemon、单 SQLite 真相、无 Web 框架、无第二套状态存储。转换所有权仍在技能。

## 3. 统一执行纪律

- **先安全基座，后UI开通**：本轮审查通过→P0独立transport→P1核心及五工具conformance→P2；P3文案按已定稿协议准备，端到端验收等P2；P4汇总全链路与人工结果。
- **先失败证据，再通过证据**：每个子阶段先写能抓出相应错误的测试；不能只证明 import、compile 或 schema 输出存在。
- **只改工作副本**：Agent 读取返回的绝对 `intent_file` / `work_path`，生成和导出均指向副本；目标路径只供识别，不作直接写入。
- **不把刷新当确认**：SQL commit 和持久 events 先于 completion receipt；客户端成功应用或记录待处理后才推进游标。
- **不可用要可见**：Git 失败、缺依赖、草稿备份失败、过大载荷、磁盘满、恢复失败均不返回成功外观；用户输入保持可恢复。
- **不自动重演外部副作用**：processing 租约过期转 interrupted；用户明确 retry 才增加 attempt；不以新消费者出现为自动重试依据。
- **保守重试**：只有已定义幂等键的写操作才自动重发；save/asset/rollback 遇响应丢失先查状态/revision，不虚构其拥有 intent UUID 的幂等保证。
- **集中常量**：lease、heartbeat、payload、SSE 留存/退避采用协议值，在核心集中定义并由测试对照；性能阈值另列为验收目标，不能偷改协议以让测试通过。
- **不污染源仓库**：测试在临时工作区和隔离工程副本中运行；真实 fixture 前后做字节摘要对比。测试内 Git 操作仅限自建临时仓库。

## 4. P0：独立 transport 探针，不依赖 P1

P0 只证明官方 SDK 的真实 stdio、取消、并发和有界等待可用；不要求已经存在 daemon、SQLite、认领、发布或五工具实现。探针仅放测试侧，使用独立名称，不让生产 `--mcp` 以临时工具冒充完成。

### P0.1 最小 SDK 探针

1. 在 `r_bridge_check.py --group transport` 的隔离子进程内使用官方 `mcp>=1.28,<2`，注册 `probe_wait(timeout_sec)` 与 `probe_status()`；两者只维护测试内存计数，不读写 deck、不启动业务 daemon。
2. 官方 ClientSession 经真实 stdio initialize → list → call，断言探针这两个工具的 schema、结构化内容、兼容文本和错误封装；**此阶段不要求恰好五个业务工具**。
3. stdout 无协议外日志；非法类型、未知探针工具、EOF、坏输入分别记录，diagnostic 只写 stderr。probe_wait 的 1/25/120 秒实等与 0/121/非整数拒绝在探针层验证。

### P0.2 取消、并发和资源

1. wait 阻塞时并行 status，验证 SDK 调度不串行冻结；可加受控标准库 HTTP 测试服务模拟阻塞 I/O，仅用于测 offload/取消，不依赖真实业务接口。
2. 发送真实 MCP cancellation，确认等待被取消且连接/任务回收；100 次取消、100 次 1 秒 timeout 后测资源基线。只取消线程 future 而底层连接泄漏不算通过。
3. 断 stdin/stdout、关闭 client、SIGTERM/SIGKILL、测试 HTTP 对端断开，必须有界退出。独立周期计数可验证 await 不阻塞定时任务，但不把它叫真实 consumer 续租或 interrupted 验收。
4. claim/cancel 竞争、lease/heartbeat、重复 receipt、无 SDK 的生产 `--mcp` 懒加载等业务验证明确移到 P1.5，不让 P0 依赖未建成的 P1。

### P0.3 宿主与证据边界

探针的 Linux SDK 结果单独记录版本与日志。可用真实宿主运行探针测 25/120 秒和取消，但完整 Kimi/Codex 五工具、重挂、10 分钟模型成本及结束行为留给 P4 人工组；SDK 通过不替代宿主通过，未测成本仍为未知。若宿主实际更短超时，按证据使用 1–120 秒范围内调用，不增加无限后台模型轮询。

**P0 出口**：transport 自动组通过，有真实取消/并发/等待及资源证据；即可进入 P1。没有五工具和业务状态不算 P0 缺项，也不能因此宣称业务 conformance 已通过。

## 5. P1：标准库持久、安全与发布核心

### P1.1 daemon 身份与权限

1. 规范化 workdir；竞争每 workdir 启动锁，取锁者负责初始化/恢复并终生持锁。已有锁持有者时走有界等待与 attach，验证 serve.json、instance_id、协议、管理 health workdir；attach 不要求再次取得 daemon 独占锁，也不得删锁抢占。陈旧端口、其他服务占端口、双启动均不能误 attach。
2. `.pptx-html` 私有目录与 0600 发现文件；management token 只进入代理内存和管理 Authorization。浏览器仅 session scoped token，经 fragment 引导到 sessionStorage 并清除地址片段。
3. 静态请求路径在统一入口拒绝 `.pptx-html`、`.git`、凭证和越界/符号链接穿透；受管资产读取按一致性文档实现，不能因 iframe 无 Authorization 而整体开放管理文件。
4. 校验 Host、同源 Origin、权限矩阵和所有路径；公开 health 只返协议规定四字段。跨 session 的 token、ID、draft_id、version path、资产路径不得互通。
5. 无MCP实现`--deck REL`与`--new [REL]`互斥；无参时index存在则打开，否则briefing target=index.html；非index显式--deck slides.html。CLI/脚本首次及再次打开都签发新的单次bootstrap，已存活daemon通过仅管理权限的POST /api/bridge/bootstrap签发，不创建consumer。
6. 按§7.6实现landing→fragment清除→按token摘要ticket独立命名的短期Path=/bootstrap cookie→GET /bootstrap?ticket=非秘密摘要→302 editor片段。raw boot不进query/日志/普通API；校验Host/同源/一次使用/300秒expiry/重启，两个启动tab不得互串。手动非Gitgit_ready=false仍可开，首存init:true先保护后写；MCP open自动init；匿名旧写401。

### P1.2 SQLite 状态机与有界接收

1. 实现 sessions/intents/events/clients 最少实体、外键/WAL/busy_timeout、必要唯一约束及 session+status+seq 查询索引；数据库版本升级失败拒绝写入，不重建丢历史。
2. 按 session/intent UUID/规范 payload digest 去重；单调 seq/event_id 由服务分配。JSON 字段顺序不改变 digest，未知 type/顶层字段拒绝。
3. 接收事务落盘后返回 accepted；派生 intent JSON 失败时认领返回明确错误，不给不存在指针，也不能删除已接收 SQL 记录。
4. 新增consumers登记状态：open事务注册/刷新本consumer，无人owner时registered，不抢他有效owner；await原子acquire有资格的registered/paused/expired→waiting，同owner重入，他有效owner SESSION_BUSY。close设requires_open，再次open同session才解除；heartbeat不能登记/acquire。processing过期先interrupted，取得owner也须用户处理恢复后才能继续。
5. 实现 cancel/retry/close/lease 迁移；每条迁移和通知在同一状态真相下记录，拒绝 succeeded retry、过期 attempt 和越权 complete。
6. 按路由先选预算再读体：控制/intent 2MiB、save/draft 64MiB、asset 48MiB JSON且raw≤32MiB；intent规范UTF-8 payload≤1MiB，MCP >16KiB返回摘要+绝对intent_file+payload_bytes。集中常量按协议§7.5实现；真实多MiB HTML/草稿/典型大图必须成功回归，不能把控制限额套到文档。磁盘满拒绝新增，不删除未确认请求或旧attempt副本。
7. A 类 save/asset/rollback 只发 facts/events 更新 revision；不能塞进 B 类队列。await 附最新 facts 摘要而非完整历史。

### P1.3 工作副本、CAS 与日志化发布

1. open 登记受管目标：无 deck 的 target_path 已知而 deck_path/revision=null；同目录重复目标复用，第二个受管 deck 拒绝；不重叠目录允许独立任务。
2. Git基线只覆盖受管集合，不改父仓库配置/index。MCP open自动init及保护，失败停止；手动bootstrap非Git打开成功但git_ready=false，首次save确认init:true后先init/保护再写，失败仅阻断发布。atomic_write只有单文件原子性，不能描述为跨文件事务。
3. 认领时创建对应工作副本与基线，保留相对 assets/fonts/export 关系；检查副本及目标符号链接，生成/转换实际写到 `work_path`。
4. complete先鉴权并查同intent+attempt+原consumer的持久成功结果，命中只读重放；未命中才按新写顺序校验有效owner/lease/attempt → 路径/产物/精确validation → seal及目标revision CAS → 快照/journal → 受控发布 → 文件/Git/SQLite终态与events → receipt。旧owner无成功结果不得进入写流程；阶段细节按一致性journal表。
5. 外部编辑或页面保存抢先改变 revision 时 conflict，不覆盖；保留副本。export-only 发布也检查基线，不把旧内容产物伪标 fresh。
6. publish 失败或 daemon 重启，先恢复未完 journal 再 ready；恢复后只能是可验证的旧状态、新状态或明确阻断，不能放行混合状态。无法恢复返回 RECOVERY_FAILED 并保留证据。
7. complete 重试只返原 receipt；崩溃发生在文件替换后、SQL 终态前或响应前均需覆盖。不能声称外部 Agent shell 和生图费用也恰好一次。
8. save/rollback/asset/显式本地 convert 共用互斥和 revision 通路；转换实现仍调用技能。冲突返回明确错误而不是队列外悄悄写文件。

### P1.4 SSE 与客户端状态

1. events 持久化、鉴权 fetch 流、每业务事件 id、15 秒注释 ping；心跳分消费者与浏览器，不能以 HTTP/SSE 连接存在证明页面 online。
2. 浏览器 15 秒 heartbeat，45 秒未见 offline，离线 dirty=null；聚合 any_dirty 和 clients，不把一个 clean tab 代替所有 tab。
3. after 游标重放、去重、保留最近 7 天与每 session 最近 1000 条的并集；过期返回 resync-required；intent/receipt/快照不随事件清理删除。
4. SSE/await不长期占写锁，连接有界并可回收。新增浏览器POST /api/intents/query：严格session/statuses/cursor/limit/intent_id，seq升序分页、limit默认50最大100、单条模式禁止混入过滤字段，结果无payload；status返回recoverable_count但不代替详情。索引支持session+seq/status，单页limit+1判断has_more。
5. 首载/新origin/SSE resync先status记事件E，再query从cursor=0分页恢复，最后订阅after=E补齐变化；失败保留本地草稿，不通过跳最新游标丢恢复入口。

### P1.5 五工具 conformance（P1核心完成后）

1. 生产 `tools/edit.py /abs/workdir --mcp` 经官方SDK真实initialize/list/call，恰好五工具、精确schema、结构化结果、错误封装和stdout隔离；执行验收SDK-01–07，与P0的两个探针工具严格分开。
2. 真实daemon/SQLite覆盖open登记registered/不抢owner→await acquire→同owner重入；close后直接await/heartbeat拒绝，重新open同session才可acquire，自然expired单独测试。再测claim/cancel竞争、redelivered、retry_id丢响应、旧attempt新写拒绝/成功receipt只读、15/90秒lease与浏览器15/45秒心跳。
3. 测long poll期间status/heartbeat/close并行，真实HTTP关闭/取消能回收；生产无SDK时--mcp非零且提示安装，手动模式不导入SDK。
4. 实现并验收内部只读CLI `python3 tools/bridge_core.py revision <work_path>`；候选源与seal内部完整摘要分离，checks结构、必需names、报告路径和fresh绑定全部负例通过。

**P1 出口**：核心unittest、真实HTTP/安全/恢复组和P1.5五工具conformance通过；CAS、丢响应、独立attempt、双启动/消费者及每个journal断点均有证据。尚未有UI不可宣称用户场景闭环。

## 6. P2：editor 全链路接入

### P2.1 能力探测与显式发送

1. 梳理现有 `saveDeck`、`serializeClean`、`buildBriefExport`、`briefLast`、`refreshExport`、`loadVersions`、转换按钮三通道和嵌入 postMessage 分支。
2. 连接态集中认证fetch与错误展示；先按协议精确heartbeat绑定client，再从POST /api/bridge/status读取capabilities.local_convert/git_ready初始化按钮。公共health仍不含旧gitReady/convert详情；401不等于无后端，不匿名重试或请求管理open。
3. 无 deck 的 open 直接呈现脑暴；预览/复制不发送。发送时重新 `buildBriefExport()` 固化同源 text/json，不复用过期 briefLast。
4. 主题/批注/convert/bake/illustrate 六类请求共用提交包装器：先处理 dirty，再本地保存 UUID+payload+base_revision 快照，POST accepted 后记 seq。双击/响应丢失重发同 ID；修改后新发送才新建 ID。
5. 浏览器持久队列不存管理 token；持久化失败阻止“已可靠提交”假提示，保留界面输入并给导出恢复入口。body/payload 超限保持草稿并提供 JSON 下载。
6. 增加pending/working/succeeded/failed/conflict/interrupted和retry/cancel控件；v1明确只有rebuild，用户确认当前base及可能重复费用后持久化retry_id/expected_attempt/mode/base_revision/confirmed，再发送。网络重发使用原retry_id，不把确认解释成继续写旧副本或自动rebase。

### P2.2 草稿保护与安全加载

1. heartbeat 上报独立 client_id、dirty、active_edit、draft_pending、当前 revision/已应用游标；页面开关与 consumer 生命周期互不绑定。
2. 刷新前检查当前 tab 三种编辑风险，不只看 dirty。先备份 `serializeClean()` 结果与 annotations/base_revision，经鉴权草稿 API 成功后再允许用户选择重载；失败不丢原 DOM。
3. 草稿恢复不得把旧 HTML 直接覆盖新 revision：展示备份/当前版本，用户明确处理，恢复后按正常 CAS 保存；session 草稿不经静态 URL 暴露。
4. `deck-changed` 先验 session，再判断加载代次和草稿。首个发布使同一 session 首次加载；旧 fetch 延迟完成不能覆盖更新版本或切换后的任务。
5. `export-refreshed` 强制清除缓存 manifest 并重取；`assets-changed` 同时更新画布与目录缩略图并标 stale。资源缓存键不污染序列化后的真实 src。
6. SSE UTF-8 分块、CRLF、多行 data、重复/断线/过期游标均有统一处理；只有成功处理或记录待处理后更新游标。receipt.events 不是已应用证明。
7. 关闭tab已接收任务继续；首载、重新认证或resync后调用query恢复列表，不仅依赖status计数/SSE旧记录。close_session只暂停本consumer并设requires_open，浏览器仍可用；同consumer再协作必须重复open同session后await，不以heartbeat复活。

### P2.3 旧链路边界

- 桥会话：保存、版本、回滚、资产经受限凭证和 CAS；图片替换沿用外部 assets 文件及 data-image-state 语义。
- 无 MCP 手动服务：相同安全 API 可编辑，不要求安装 mcp；显式 `--convert` 才能本地转换，与 Agent 发布互斥。
- 普通 http.server / file://：FSAA 或下载降级，不伪造服务器保存、协作在线或 conversion 成功。
- 嵌入：原 `pptx-html:load/save/dirty/brief/annotations/export-intent` 协议保持；桥不夺取宿主保存。不得因新 auth 拦截嵌入正常消息。
- HTML 交付：canonical/hash、编辑契约和源层约定不变；token、SSE 脚本、任务 ID、草稿标记、cache-busting 临时 URL 不写入产物。

**P2 出口**：Linux Playwright 完成无 deck 与已有 deck 闭环；双 tab 草稿保护、首次加载、缓存失效、静态/嵌入/手动模式回归通过。单独 HTTP 200 不算 UI 验收。

## 7. P3：技能整合与真实产物

1. 在 `skills/html-pptx/SKILL.md` 接入已冻结五工具：open → await → Read intent_file（必要时）→ 只改 work_path → 原技能验收 → push_update complete/fail → 用户继续才重挂，明确结束 close。
2. 六类请求分流到既有脑暴、主题双 SLOT、批注、Step 5.5 插画、Step 5.6 烙入、Step 5.7 导出；不抄第二套转换代码，不越过代表页审批或用户插画授权。
3. validation记录真实argv/退出码/报告；桥所有转换固定调用export-pptx.py <work_path> --force --track both，formats仅控制用户下载选择。必须重建并验收export/deck.pptx、deck-vector.pptx、deck.pdf、native逐页图及manifest的editable/vector两轨成功；任一缺失/失败不发布，不拿继承旧轨凑齐。fresh为完整集合全局binding，convert必须填同候选源export_source_revision。单轨能力仅留技能非桥手工调用。
4. Linux 自动化用确定性 Agent driver 执行真实五工具、磁盘编辑与技能脚本；明确它不是大模型创作能力或生图质量证明。付费生图仅在后续获准人工测试中执行，费用与不可回滚边界单列。
5. 小 fixture 验证烙入源层及导出：复制 `bake-mix`；真实密度验收复制 54 页 `cmb-retail`。所有脚本指向副本，真实 fixture 前后字节一致。
6. 从已有 deck 批注修改、样式修改、资产替换、回滚到导出逐步跑通；工作副本中抽取 hash/渲染/容量/导出报告，complete 后从正式目标及 editor 重新验证，不只检查副本。
7. 交付配置示例只用绝对 workdir，不含发现文件 token，不改用户现有 Kimi/Codex 配置；真实宿主加载由用户明确操作并记录版本。

**P3 出口**：确定性自动 driver + 真实技能产物 + editor 可见结果全部通过；原始 deck 不变。未执行付费生图及真实模型时，相关能力标“未测”，不伪写 generated 或已完成宿主验收。

## 8. P4：全回归、测量与交付判定

1. `r_bridge_check.py` 已纳入 `run_e2e.py` 的 `T29-bridge`，沿用子进程退出码判定；核心 unittest 可独立运行。
2. 新 HTTP harness 已覆盖受限鉴权、匿名 401、Host/Origin、静态隔离、bootstrap、intent 幂等/query、草稿、资产和回滚主路径。
3. fault 组已覆盖 publication 注入矩阵、响应丢失、双消费者/daemon、SSE 过期游标和 schema 迁移；进程崩溃模拟不等于硬件掉电认证。
4. 25 个标准 deck 已完整恢复并核验，标准 `run_e2e.py` 55/55 与独立 `o_tri_view` 均通过；fixtures 测试前后 806 entries / 789020265 bytes，added=0、removed=0、changed=0。
5. performance 已完成单页协议基线；PERF-03 真正 Bridge 真实大 deck 事件→可编辑 UI、54页×10倍素材、PERF-04/05/06 完整样本仍待测。`run_e2e` 中的 `cmb-retail` T1/导出子测试不等于这些规模验收。
6. Kimi/Codex 人工、Office/WPS、真实生图和硬件掉电仍未执行，因此总体验收保持“部分完成”。任何 git commit/push 仍需用户另行授权。

### 8.1 命令与本次结果

```bash
# 2026-10-03：退出码 0，Ran 21 tests，OK；5.894s
python3 -m unittest tests.harness.test_bridge_core -v

# 2026-10-03：退出码 0；默认组选中 fault,http,integration,sdk,transport,ui；20.846s
python3 tests/harness/r_bridge_check.py

# 2026-10-03：ALL PASS；2.483s
python3 tests/harness/k_brief_check.py

# 2026-10-03：ALL PASS；107.329s
python3 tests/harness/o_tri_view_check.py

# 2026-10-03：55项、55 PASS、0 FAIL；约860s
python3 tests/harness/run_e2e.py
```

`r_bridge_check.py` 已实现 `--group transport|sdk|http|ui|fault|security|integration|performance`。无参数默认运行 `transport,sdk,http,ui,fault,integration`；`security` 与 `http` 共用实现入口，`performance` 必须显式选择。技能命令由 harness 以 subprocess 和副本绝对路径调用。完整回归首次运行在 T12 暴露旧 v1.6 匿名保存测试与 Bridge v2 冲突；迁移 T12 后继续发现并修复历史 UI 的 `snapshot_id` 消费错误，最终全量通过。

### 8.2 阶段状态登记

| 阶段 | 2026-10-03 状态 | 已有证据与边界 |
|---|---|---|
| P0 | **完成（Linux 自动）** | 官方 SDK initialize/list/call、schema、有界等待、并发和 100 次取消通过；未替代真实宿主 |
| P1 | **完成（Linux 自动）** | 核心 unittest 21/21；五工具 stdio、HTTP/安全、CAS/receipt、journal/fault、revision CLI 通过 |
| P2 | **完成（Linux 自动）** | Playwright 无 deck、保存世代、dirty 草稿保护、SSE、fragment 清理及手动 bootstrap 历史 UI/CAS 回滚通过 |
| P3 | **完成（确定性自动范围）** | SKILL 桥契约检查 + 真实 MCP/HTTP 无 deck claim、独立 work_path、validation、complete/receipt 重放通过；不代表真正 Bridge 54页 convert 场景完成 |
| P4 | **部分完成** | fault、单页 performance、25 deck 完整 `run_e2e` 55/55、独立 `o_tri_view` 与 fixture 零变化核验通过；真实 Bridge 大 deck/10倍素材、完整性能样本和人工组未完成 |
| Kimi/Codex 真实宿主与模型成本 | **未测** | 不以 SDK client 结果替代；成本未知，不估成零 |

## 9. 方案风险提示（自审）

| 维度 | 风险 | 控制措施 |
|---|---|---|
| 外溢影响 | 高 | health/API 鉴权改变 editor、脚本和旧测试；P2/P4 联动，嵌入及静态路径独立回归 |
| 性能影响 | 中 | SQLite 写锁不可跨 long poll；有界请求/事件留存、资源回收与 P95 实测，54 页真实规模覆盖 |
| 维护成本 | 中 | SDK transport、标准库核心、静态 UI 各一处职责；契约映射与集中常量阻止多套语义 |
| 根因解决度 | 中 | SQL 确认与 journal 解决隐式确认和覆盖，但外部付费副作用仍只能显式恢复，不承诺全局 exactly-once |
| 向后兼容性 | 高 | 匿名写主动不兼容且明确 401；公开 health 不再给旧详情，所有自带消费者一起升级 |
| 简洁性 | 低 | 五工具、单目录单 deck、SQLite 标准库；不增常驻任务系统/框架/通用 shell 工具 |
| 边界覆盖 | 高 | retry 重建意图、validation、revision/journal 细节先冻结；响应丢失、断电模拟、双消费者、草稿失败均为硬闸 |

自审改进已纳入：将“进程在 = Agent 在线”改为 lease 证据；将“完成通知 = 页面刷新”改为 applied cursor；将“保存后整目录原子替换”改为分阶段恢复；将仅小 deck 冒烟提升为 54 页与真实产物回归；将标准 harness 对 fixture 的潜在写入隔离到镜像。本轮四项独立审核修订已同步至P1/P2/P3：open登记与await acquire、手动单次bootstrap和首存Git确认、固定完整both导出、持久请求query及跨事件清理恢复。设计审核结论须由整套设计交叉审核给出，本文不自行批准开发。

## 10. 一致性文档交叉复读后的执行细化

本节是 P1/P2/P4 的必做子步骤，不是未来可选加固；与验收计划 §15 一一对应，不增加 MCP 工具或私改主协议。

### 10.1 P1 补充：bundle、Git 与提交点

1. 按一致性文档 §2–3 落 `bundle_files` 分类清单；source/export/derived 分别绑定，摘要前缀和紧凑 JSON 编码逐字遵循算法。CSS/同名图/字体字节变化使 source revision 变化；纯导出不改 source，旧产物未知 binding 则 stale。页级 canonical 不参与替代 CAS。
2. Git 采用 `refs/pptx-html/<workspace-key>/<session-id>` 专用 ref 与 `GIT_INDEX_FILE` 隔离 index；API/workdir/bundle/Git树四种路径显式转换。只新增保护对象和专用 ref，不移动用户 HEAD、不写真实 index、不跑用户 hooks/filter，不把旧“每次保存提交当前分支”当兼容要求。
3. A 类保存/资产/回滚调用同一 publication；稳定 write key 与 receipt 按一致性 §5.1 实现。客户端可重发同一不可变快照：目标未前进则原 receipt，已前进则明确 conflict，不自动重写旧内容。
4. complete按协议validation校验candidate_revision（候选源），服务内部另算完整seal清单摘要；复制期间任一受管文件变化即失败。PREPARED/APPLYING且DB未COMMITTED统一回old；DB COMMITTED保new补journal；Git ref已是old不动、等于new才CAS回old，第三值冻结。第三种文件字节/损坏快照同样不ready，不猜“看起来完成”。
5. 静态GET/HEAD遵守bundle读锁；多次GET跨发布后重核revision，不接受HTML/资产混合装载。关键写入复算真实字节，后台观察只作便利。
6. attempt-<N>/work路径永久隔离，旧副本不复用不删除。retry事务按retry_id去重、expected_attempt CAS、mode=rebuild与confirmed=true校验，当前base正确才新建attempt；旧生产者仍活着也不污染新路径，但未知外部费用须显式确认。
7. 空间默认值按一致性文档集中：内部10GiB、文件系统至少512MiB保留、bundle≤2GiB/20,000文件、同workdir最多2个准备并发。峰值预检包含 old/new/seal/temp/job/Git/SQLite；任何阶段仍处理 ENOSPC，绝不清掉未确认记录换空间。

### 10.2 P2 补充：保存中继续输入与多维草稿

1. 保存快照绑定 session/epoch/editGeneration/hash map；异步 serializeClean 结果不借共享 lastSaveHashes。receipt 后 generation 已变化时仍 dirty，不把旧 hash 写到新 DOM；同tab保存串行，后次基于前次真实 revision。
2. 防自动重载不仅三项 heartbeat 状态，还包括未提交批注/设计或脑暴表单、待确认 intent、saveInFlight、pendingAssetWrites。IndexedDB 保存这些状态和未上传 Blob；服务 draft 正文仅用已有 html/annotations/base_revision，表单留本地，不扩 body。
3. 图片是两次明确写入：资产成功到R1后才标上传已确认，HTML的src/state以R1另存到R2；第二步失败保留草稿，不能显示整个换图保存成功。浏览器大图超过body限额不走匿名或FSAA旁路。
4. 缓存刷新覆盖 CSS/font 与图片，保留用户原有 URL query，只清桥注入参数；export-only刷新不重载HTML/清批注。恢复原slide_id/章节/view/侧栏状态，目标页消失有明确落点。
5. token绑定client后，复制tab不能沿用旧凭证伪装新client，重新合法open领独立凭证。同session新tab可以读服务草稿，但恢复为自己的新草稿，不覆盖他tab原记录。
6. daemon重启旧实例token失效；手动重开CLI/脚本取得新单次bootstrap，同端口/新端口均重新认证。新origin不能读旧IndexedDB；新页首绑后status记E→query完整恢复请求→after=E补流，即使旧事件已清理也能恢复旧失败项。服务草稿可重取，未上传稿仍从旧页下载，不混称透明跨端口恢复。

### 10.3 P4 补充：威胁与极端负载

1. GET/HEAD路径隔离、硬链接、目录fd/O_NOFOLLOW竞态、匿名已登记交付资源的准确边界均测试。作品公开静态读取不等于匿名API可写；恶意同源deck、同UID进程不在沙箱保证内，入口声明仅可信deck。
2. 在基础性能组之外增加10倍素材体积的合成副本测量：不减少54页数据，仍受2GiB/20,000文件上限；超上限必须先拒绝而不是改预算让测试进入。记录峰值RSS、hash/复制/锁等待和保存/发布耗时，不提前声称毫秒级大bundle保存。
3. 针对一致性文档 §13 失败矩阵逐行挂接测试ID；已自动覆盖的故障点见下节，保存中继续输入由 UI 组覆盖。图片R1/HTML失败、字体变更页hash不变、新端口草稿恢复、真实大 bundle 等未在现有自动报告中完整证明，继续保留为待验项。

## 11. 2026-10-03 实际执行记录

### 11.1 已执行命令

| 命令 | 结果 | 说明 |
|---|---|---|
| `python3 -m unittest tests.harness.test_bridge_core -v` | PASS，21/21，5.894s | 状态机、revision、幂等、Git 隔离、publication 恢复、安全/迁移 |
| `python3 tests/harness/r_bridge_check.py` | PASS，退出码0，20.846s | 默认组 transport、sdk、http、ui、fault、integration；`security` 复用 http 入口；不含 performance |
| `python3 tests/harness/k_brief_check.py` | ALL PASS，2.483s | 需求脑暴 UI 回归 |
| `python3 tests/harness/o_tri_view_check.py` | ALL PASS，107.329s | 真实 `bake-mix` 副本上的三态工作台与导出链 |
| `python3 tests/harness/run_e2e.py` | PASS，55/55，退出码0，约860s | T1–T29 全通过；含恢复后的 25 个标准 deck、T12 Bridge v2 手动 daemon 历史回滚及 T29 bridge 默认组 |

### 11.2 fixture 恢复与零污染证据

- 完整枚举 25 个标准 deck；恢复前原有 7 个可用，其中 `cmb-retail` 实际存在但被 `.gitignore` 隐藏。
- 18 个缺失目录从可信 Git 删除前统一快照 `dd5d87940f9463a3b60972f0c9b288195a2264d5` 原字节恢复，共 47 个文件；Git blob 核验 missing=0、mismatch=0。
- `cmb-retail` 对删除前 `5fdd8c723e26594e7334080ba2c06cdf5e5733c1` 的 100 个历史受控文件核验 missing=0、mismatch=0。
- 恢复后的全 fixtures 基线为 806 entries / 789020265 bytes；所有测试后复核 added=0、removed=0、changed=0。

### 11.3 T12 真实回归与修复

首次完整回归在 `tests/harness/run_e2e.py` T12 暴露旧 v1.6 测试仍发送无鉴权 `/api/save`，与 Bridge v2 的 bootstrap/browser bearer、session/base_revision、专用 ref、snapshot 和 receipt 协议冲突。T12 已迁移为真实手动 daemon + bootstrap 浏览器流程，并保留或强化无后端降级、匿名写拒绝、鉴权后路径穿越拒绝、非 Git 显式 init、两次 UI 保存 receipt/版本、HEAD/index 零污染、未保存 draft、revision CAS 回滚及 pre-rollback 快照断言。

迁移后继续检出 `editor.html` 历史 UI 将可空 Git commit `v.hash` 当稳定身份并调用 `slice()`。现改为优先 `snapshot_id`、旧 schema 缺字段时回退 `hash`；commit hash 仅作可选显示，rollback 传稳定版本 id。定向 T12 与最终完整回归均通过，生产鉴权和 CAS 未放松。

### 11.4 单页性能实测

环境：Linux 5.4.96 arm64、Python 3.13.11、MCP SDK 1.28.0、Git 2.20.1、8 CPU；采样时系统 load average 约 15.98/15.87/15.32。原始样本在忽略目录 `tests/harness/results/bridge/metrics.json`。

| 指标 | 样本 | P50 | P95 | Max | 阈值结论 |
|---|---:|---:|---:|---:|---|
| status | 100 | 1.115ms | 2.624ms | 3.860ms | ≤250ms，PASS |
| browser heartbeat | 100 | 2.674ms | 4.396ms | 8.257ms | ≤250ms，PASS |
| 小 intent accepted | 200 | 3.811ms | 7.267ms | 11.794ms | ≤500ms，PASS |
| 近 1MiB intent | 20 | 20.624ms | 45.130ms | 46.413ms | ≤2s，PASS |
| 25s await | 1 | 25002.970ms | 25002.970ms | 25002.970ms | timeout+5s 内，PASS；样本不足以形成计划分布 |
| 120s await | 1 | 120009.915ms | 120009.915ms | 120009.915ms | timeout+5s 内，PASS；样本不足以形成计划分布 |

资源快照：RSS 24.867→32.949MiB（+8.082MiB），FD 9→9。该有界运行未覆盖 30 分钟空闲和 100 轮完整连接/断开，不能据此宣称 PERF-06 完成。

### 11.5 已知阻断与未测

- **BLOCKED**：PERF-03 真正 Bridge 真实大 deck 事件→可编辑 UI；CNS-08 的 54 页×10倍素材。完整 `run_e2e.py` 与独立 `o_tri_view` 已通过，不再列为阻断。
- **部分样本**：PERF-04 计划的 25s×20、120s×3 未满足；PERF-05 冷启动20次、PERF-06 30分钟稳定性与完整100轮连接/断开未跑。
- **NOT_RUN**：真实 Kimi、Codex MCP 宿主；真实模型调用与10分钟成本；Office/WPS；真实付费生图；硬件掉电。
- **结论边界**：P0–P3 的 Linux 自动实现范围完成；P4 的 fault、单页 performance 和完整历史回归通过，但真正 Bridge 大 deck/10倍素材、完整性能样本及人工环境未完成，仍只能判定部分完成。不得把 `run_e2e` 中 `cmb-retail` T1/导出子测试冒称完整54页 Bridge convert/P4-C。

# 编辑器↔Agent 桥 v2：协议与状态机

> 状态：公共接口定稿并于 2026-10-03 完成 P0–P3 Linux 自动实现；P4 仅 fault 与单页协议性能已有结果，真实 fixtures 全回归和人工宿主仍未完成。本文取代旧设计以页面 seq 和 after_seq 隐式确认执行的做法。
> 总览：[editor-agent-bridge.md](editor-agent-bridge.md)。一致性与安全：[editor-agent-bridge-consistency.md](editor-agent-bridge-consistency.md)。本文是生产者、代理、daemon、编辑器和测试共用的规范；实际执行证据见[验收记录](../test_acceptance/editor-agent-bridge.md#16-2026-10-03-实际执行记录)。

## 1. 版本、身份与命名

- `protocol_version: 2` 是应用协议版本，不是 MCP 协议版本。MCP 初始化和取消由官方 Python SDK 处理。
- MCP server 名 `pptx-html-bridge`，五工具 `open_editor`、`await_intent`、`push_update`、`get_status`、`close_session`。
- 一个代理固定绑定一个规范化绝对 workdir：`python3 tools/edit.py /abs/workdir --mcp`。配置明确传入 workdir，不依赖宿主 cwd；跨 workdir 启动另一代理。
- daemon 每 workdir 一个，发现文件 `.pptx-html/serve.json`。规范化 workdir、随机 instance_id、协议版本与健康响应必须匹配；不能仅凭端口可连判断 attach 成功。
- `session_id` 为服务端生成的随机 ID，代表创作任务，不代表一个 stdio 连接。任务可先有目标路径、后有真实 deck。
- `client_id` 为浏览器连接 ID；每个 tab 独立生成，禁止作为排序依据。
- `consumer_id` 为 MCP 代理启动时生成的随机 ID，不由模型提供；代理自动附在管理端 HTTP 请求中。
- `intent_id` 为浏览器一次明确提交生成的 UUID；同一次请求的网络重发必须使用相同 ID。JSON 对象字段顺序不影响语义摘要。
- `attempt` 首次为1，只有成功的明确 retry 事务递增；`retry_id` 是一次恢复决定的UUID，网络重发不得换ID。attempt隔离路径与retry receipt见§6.1。
- `seq` 为 SQLite 分配的单调整数，按 session 查询排序；不要求连续，不接收客户端自定 seq。
- `event_id` 为事件表的单调整数，与 intent seq 不共用。
- 时间统一 UTC RFC3339，带 `Z`。所有返回的文件指针为绝对路径；HTTP 资源路径用 URL 编码后的工作区相对路径。ID 均不可替代权限检查。

## 2. 真相与落盘布局

```text
.pptx-html/
  serve.json
  daemon.lock
  daemon.log
  bridge.sqlite3
  intents/<intent_id>.json
  jobs/<intent_id>/attempt-<N>/work/<relative-deck>
  snapshots/<snapshot_id>/
  drafts/<draft_id>.json
  transactions/<transaction_id>.json
```

SQLite（标准库 sqlite3）是 session、请求状态、seq、结果和 SSE 事件的唯一权威来源；JSON intent 是供 Agent 阅读的派生副本，重建不改变消费状态。SQLite 启用外键、WAL、busy_timeout，接收/认领/确认在事务中进行。服务启动先恢复未完发布事务，再对外宣告 ready。

最少数据实体：

| 实体 | 必需字段 |
|---|---|
| sessions | id、target_path、deck_path（可空）、phase、created_at、updated_at、revision、export_revision、agent_state、owner_consumer_id（可空） |
| consumers | session_id、consumer_id、state、registered_at、requires_open、lease_until；session+consumer唯一，owner acquire在事务内 |
| bootstrap_tokens | token_digest、instance_id、mode、target_path、expires_at、used_at；单次token摘要唯一，不存明文 |
| intents | id、session_id、seq、type、payload_json、payload_digest、base_revision、status、consumer_id、lease_until、attempt（首次1）、result_json、created_at、updated_at |
| attempts | session_id、intent_id、attempt、base_revision、work_path、consumer_id、status、result_json、created_at；intent+attempt唯一，旧行/旧副本永久保留 |
| retry_receipts | session_id、retry_id、intent_id、request_digest、expected_attempt、mode、base_revision、confirmed、result_json、created_at；session+retry_id唯一 |
| write_receipts | session_id、write_key、action、receipt_id、snapshot_id、result_json、created_at；session+write_key唯一 |
| events | id、session_id、type、data_json、created_at |
| clients | id、session_id、token_digest绑定、last_seen、dirty、active_edit、draft_pending、revision、last_event_id |

凭证不进入 intent JSON、状态响应、事件和用户可复制的技能指令。内部目录不可通过静态服务读取。

## 3. 创作任务、消费者、页面的独立生命周期

### 3.1 创作任务

`briefing → generating → editing`；生成失败回到 briefing 并保留失败请求。已有 deck 打开直接 editing。`paused` 是消费者状态，不撤销作品；`close_session` 不删除 session、请求、草稿和文件。

无 deck 时 `target_path` 已知（默认 `index.html`），`deck_path=null`，`revision=null`。提交简报不需要伪造空 HTML。生成完成且发布成功后设置 deck_path，向原 session 推 `deck-changed`；浏览器首次加载。

v1 同一目录只登记一个受管 deck，避免共享 assets/fonts/export 归属冲突。不同目录、互不重叠的受管文件集合可有独立任务；重复 open 相同目标复用 session。目录内其他未登记文件不进入发布与回滚集合。

### 3.2 Agent 消费者

会话聚合 agent_state 为 `offline/waiting/working/paused/recovering`；调用者独立 consumer_state 为 `registered/waiting/working/paused/expired`。daemon 存活或 consumer 已登记不等于 Agent 正在等待；只有 await 取得有效 owner lease 才显示 waiting/working。管理 open 与 await 的职责分离：

1. `open_editor` 的管理 open 事务登记/刷新本 consumer，记录 `(session_id,consumer_id,state,registered_at,requires_open,lease_until)`。无人有效 owner 时本 consumer 为 registered、无 owner lease；若已有别人有效 owner，仅把本 consumer 登记为 registered，不抢占、不终止对方。若本 consumer 已是有效 owner，刷新登记和lease但保持其waiting/working状态。
2. `await_intent` 在事务内 acquire：先核验本 consumer 已 open 登记且 requires_open=false；对 registered/paused/expired 且不存在 processing/未完publication、无人有效owner的情况取得owner并waiting，建立90秒lease。同一有效owner重入；他有效owner一律SESSION_BUSY。已过期processing先转interrupted，不自动重做；取得owner后仍按恢复闸门返回RECOVERY_REQUIRED，直到用户明确处理请求。
3. close 将本consumer置paused、requires_open=true并释放owner；同consumer必须再次open_editor重复同目标/session，事务清除requires_open并回registered，随后才能await。paused不绕过这个显式close闸门；heartbeat、get_status和成功receipt重放均不能恢复登记资格或取得owner。
4. 代理每15秒只给已acquire的有效owner续租，与模型是否再次调用工具无关；registered状态不伪发心跳证明在线。仅lease自然过期且没有显式close闸门的已登记consumer，可由await重新acquire；新consumer必须先open。

- `await_intent` 默认等待 25 秒，范围 1–120 秒。该值是保守初始值，不保证适合所有宿主；P0 按目标宿主测试结果调整配置。
- waiting 超时返回 timeout，不产生假请求，不推进执行状态。
- 用户选择继续优化时 Agent 重挂；用户明确结束时 close_session。脑暴提交后可关 tab，已接收的请求仍执行。
- 页面关闭不取消任务；取消请求是独立、明确操作，未执行请求允许 cancel，已执行中只能请求停止、不能承诺回滚外部生图费用。
- 代理 lease 默认 90 秒、每 15 秒续约。过期的 processing 请求置 `interrupted`，不自动重跑；新代理显示恢复选项，用户明确重试后创建新 attempt。防止生图/发布被无声重复执行。
- 尚未认领的 pending 请求在新消费者 attach 后可以正常执行；已成功请求只返回记录，不再次认领。

### 3.3 浏览器

每 15 秒发送 client heartbeat，45 秒未见为 offline。get_status 对离线页面返回 `dirty:null`，而不是假 clean。多 tab 返回 clients 数组与 `any_dirty`；只要有活跃编辑或草稿待处理，自动重载必须保护该 tab 的状态。页面关闭、暂停协作和停止 daemon 是三个不同操作。

## 4. 请求生命周期与“不重不漏”的准确边界

```text
pending → processing → succeeded
                    → failed
                    → conflict
                    → interrupted
pending → cancelled
failed/conflict/interrupted → 用户明确 retry → pending（attempt 增加）
```

1. 页面先将提交快照写入本地待确认队列，再 POST。服务事务插入 intent 后才返回 accepted。
2. 相同 session/intent_id/payload_digest 重试返回原 seq/status；同 ID 不同内容返回 `IDEMPOTENCY_CONFLICT`，不覆盖旧请求。
3. await 在事务内认领最早 pending，请求和 consumer 绑定。一个 session 最多一个 processing 请求、一个有效 owner。
4. 同一 owner 重试 await 若已有 processing，则重放同一认领结果，并带 `redelivered:true`；没有完成确认不会取走下一条。
5. push_update 完成动作绑定 intent_id、attempt、consumer_id；结果落盘后返回 receipt。重复完成请求只返回原 receipt，不重复发布。
6. publish 中断由事务日志恢复；结果响应丢失可查询状态。不依赖模型记忆 after_seq 来断言任务已执行。
7. 不宣称外部副作用“恰好一次”：生图付费 API、Agent 任意 shell 等不由桥控制。保证的是已确认接收的请求可恢复、发布操作可核验、重复请求不重复发布、未知执行结果必须显式处理。

A 类事实（保存/换图/回滚）记录为 events/session revision，不入需要模型认领的 B 类工作队列。下一条 B 类结果返回最新 facts 摘要。连续保存不会强迫模型每次醒来。

## 5. MCP 工具契约

官方 SDK 自动生成 inputSchema；参数使用精确类型、Literal 枚举和约束，工具描述包含边界、返回值、错误、是否会写盘。不把业务字典直接当 JSON-RPC 顶层结果；SDK 返回 structuredContent 与兼容文本。协议错误和业务失败分开，业务失败使用 `isError` 或明确 `ok:false` 的工具错误封装，禁止返回成功外观的错误。

### 5.1 open_editor

输入：

| 参数 | 类型/缺省 | 含义 |
|---|---|---|
| deck_path | string 或 null，null | 已有工作区内 HTML 的绝对路径；null 为先脑暴 |
| output_path | string，`index.html` | 无 deck 时的工作区相对目标 HTML 路径；已有 deck 时忽略 |
| view | `edit/brief/annotate/export`，edit | 页面初始视图，物理翻面不是单独视图 |
| open_browser | boolean，true | 是否尝试 OS 打开 URL；headless 用 false |

副作用：按需启动/复用daemon、登记任务、在管理open事务注册/刷新本consumer（§3.2），不抢别人的有效owner。MCP open自动在用户指定workdir初始化所需Git仓库并建保护基线，失败返回明确错误；不改父仓库配置/无关index。手动CLI入口不调用这个MCP自动init流程，见§7.6。

返回：`{ok,protocol_version,session_id,deck_path,target_path,resource_path,revision,phase,url,page_online,agent_state,consumer_state,git_initialized,capabilities}`。`target_path` 是供 Agent 识别的绝对路径；`resource_path` 是已校验的 workdir 相对 POSIX 路径，浏览器只用它构造同源静态 URL，禁止从绝对路径猜 basename。consumer_state是本调用者状态，不是会话owner的状态；无owner新登记返回registered。page_online由heartbeat证明；活tab不重复开窗，离线且open_browser=true可重开，false永不启动浏览器。重复目标复用session，显式close后的本consumer重新open后恢复registered资格；URL只带browser凭证。

### 5.2 await_intent

输入：`session_id:string`、`timeout_sec:int=25`（1–120）。不接受after_seq作为消费确认。代理自动附consumer身份，先核验open登记及requires_open资格，再按§3.2原子acquire；只有取得有效owner后才维护lease，不能以先续租作为首次acquire前置条件。

认领结果：

```json
{
  "ok": true,
  "kind": "intent",
  "session_id": "s_example",
  "intent_id": "i_example",
  "seq": 18,
  "attempt": 1,
  "type": "anno.submitted",
  "base_revision": "sha256:example",
  "payload": {"version": 1, "kind": "annotations", "deck": "index.html", "annotations": []},
  "intent_file": "/work/.pptx-html/intents/i_example.json",
  "work_path": "/work/.pptx-html/jobs/i_example/attempt-1/work/index.html",
  "target_path": "/work/index.html",
  "redelivered": false,
  "facts": [],
  "page_online": true
}
```

示例中的摘要字符串不是合法 hash 的格式范本；实际 revision 为 `sha256:` 加 64 个小写十六进制字符。所有可变输出均按真实任务生成。

超时结果：`{ok:true,kind:'timeout',session_id,page_online,agent_state,pending_count,interrupted_count}`。他人占有返回 `SESSION_BUSY`；待恢复请求返回 `RECOVERY_REQUIRED` 及 intent_id/status，不自动绕过。

取消工具等待仅停止本次 long poll，释放等待连接，不删除 pending 或成功记录。认领与取消竞争时 processing 保留，重试按同 owner 重放。

### 5.3 push_update

输入：

| 参数 | 类型/缺省 | 含义 |
|---|---|---|
| session_id | string，必填 | 任务 |
| intent_id | string，必填 | 当前认领请求 |
| attempt | integer ≥1，必填 | 防迟到确认 |
| action | `progress/complete/fail`，必填 | 通知/完成/失败 |
| message | string，空串 | 最多 2000 字符的人类可读状态，不传凭证 |
| validation | object 或 null，缺省 null | 新 complete 必须提供下述精确结构；progress/fail 只允许省略或 null |

代理自动带 consumer_id。progress 只续租和发 notice，不发布、不推进终态。fail 记录失败原因并保留工作副本。complete 只发布服务分配的 attempt 工作副本，**不接受任意源目录、任意 shell 或原始 HTML 参数**。服务检查所有权、attempt、路径/符号链接、validation、目标 revision，再执行日志化发布。生成类必须存在目标HTML；转换类必须完整重建并验收both集合（含native与manifest双轨），formats仅决定下载选择；daemon不代跑验收和转换。

validation 仅有以下字段，未知字段拒绝：

| 字段 | 类型与规则 |
|---|---|
| candidate_revision | 必填 string，`sha256:`+64 小写 hex；按一致性 §3 算出的**工作副本源 revision**，不是 base_revision、页 hash 或完整 bundle 摘要；complete 时源 HTML 必须存在 |
| checks | 必填非空数组；每项精确为 `{name,argv,exit_code,report_path}` |
| checks[].name | `render/capacity/images/manifest/export` 之一，同名不得重复；最低必需集合见下表 |
| checks[].argv | 非空 string[]，每项非空，无 NUL；真实执行的程序及参数，不是供 daemon 执行的命令，不接受单个 shell 字符串 |
| checks[].exit_code | 严格 integer，只接受 0；布尔值不算 integer |
| checks[].report_path | 必填 string 或 null；无独立报告时为 null；有值为相对本 attempt `work/` 根的路径，须存在、为普通文件、禁止绝对路径/穿越/链接逃逸 |
| export_source_revision | convert或主动更新导出时必填；只修改源时可省略。提供时须为合法源revision、等于candidate_revision且checks含成功export；null/错误值拒绝，fresh还必须通过完整both集合核验 |

| intent type | 必需 check names |
|---|---|
| brief.submitted / design.submitted / anno.submitted / bake.requested / illustrate.requested | render、capacity、images、manifest 全部存在 |
| convert.requested | export；candidate_revision 还必须等于该 attempt 的 base_revision |

Agent 实际运行当前技能要求的命令后提交结果，代理不得补造 checks、伪填 exit_code=0 或替模型声明验收成功。渲染/容量/图片/manifest 脚本输出和实际 report_path 对应；manifest 写 hash 等会改变 HTML 的步骤完成后，须在最终候选上完成必要回归，再计算 candidate_revision。源在检查后继续变化必须重新验收。check 名不是任意脚本的安全认证；Agent 是受信任生产者，daemon 验证结构、报告归属、实际源摘要和产物完整性，不宣称证明恶意 Agent 的命令确曾执行。

内部只读辅助命令为 `python3 tools/bridge_core.py revision <work_path>`：work_path 是本次认领返回的目标 HTML 绝对路径，命令按该 attempt 登记及合法新增源清单流式计算摘要，stdout 只输出一行源 revision；异常写 stderr、非零退出，缺 HTML 不输出假摘要，不改文件/DB，不需要管理 token，也不新增 MCP 工具。Agent 用该输出填 candidate_revision，daemon 在 seal 时独立复算。

**桥v1导出一律完整both**：convert.requested的formats仅选择用户下载件，执行固定为`python3 <技能目录>/scripts/export-pptx.py <work_path> --force --track both`，本地--convert同样执行。每次重建并验收`export/deck.pptx`、`export/deck-vector.pptx`、`export/deck.pdf`、`export/native/`内与页数对应的参考页图，以及`export/manifest.json`中export.tracks的editable/vector均成功；同时校验manifest引用的其他导出文件。禁止单轨发布或用继承旧轨/旧native凑完整集合；技能的--track editable/vector仅留给非桥手工使用。

fresh是上述完整集合的全局binding，不按formats子集标fresh。convert complete必须提交成功export check且export_source_revision等于candidate_revision，并通过完整集合核验；缺binding为VALIDATION_REQUIRED。非convert源修改允许省略binding并保留旧导出stale，但若主动更新导出件同样必须完整both及同源检查，不接受部分导出发布。原生参考渲染依赖不可用导致缺native时明确失败，不沿用非桥技能的可选native降级冒充完整。

结构非法INVALID_ARGUMENT；缺必需检查/非零/摘要或binding不符VALIDATION_REQUIRED；报告越界PATH_DENIED；报告/交付件/原生页图缺失或tracks不完整INVALID_ARTIFACT。任何一轨失败都不发布新集合，保留旧目标和失败副本。

返回：`{ok,intent_id,status,receipt_id,revision,export_revision,events:[event_id],page_online}`。冲突不覆盖磁盘，状态 conflict，返回当前 revision 与工作副本路径。

**成功 receipt 重放与失效 owner 新写分开**：鉴权后先查 `(session_id,intent_id,attempt,原consumer_id)` 的已持久成功结果。只在 action=complete 且精确命中时允许旧 owner 读取原 receipt，即使该 lease 已过期或 daemon 已重启；不续租、不改文件、不重复 events、不重新消费 validation。无该成功记录时，任何失效 owner 的 progress/fail/complete 均拒绝，不能因曾参与任务而获得新写权限；其他 consumer 不得通过冒用旧 attempt 完成新发布。重放返回原持久结果，客户端另读 get_status 获得当前状态，不将旧 receipt 当最新磁盘。

`events` 表示服务已记录通知，**不是页面已应用**；应用状态由 heartbeat 的 last_event_id/revision 表示。

### 5.4 get_status

输入：session_id 必填。

返回：`{ok,session_id,phase,deck_path,target_path,revision,export_revision,export_stale,agent_state,page_online,any_dirty,clients,pending_count,processing,interrupted,recoverable_count,latest_event_id,capabilities}`。recoverable_count为当前failed/conflict/interrupted请求总数；不是恢复列表，详情及分页必须调用浏览器POST /api/intents/query。processing/interrupted仍只含id/type/attempt/status摘要，不返回完整HTML或历史payload。clients含online、dirty（离线null）、active_edit、draft_pending、revision、last_seen。未知session返回SESSION_NOT_FOUND。

open_editor与get_status的capabilities统一为 `{local_convert:boolean,git_ready:boolean}`：前者仅表示daemon是否显式启用--convert，后者表示本任务Git保护基线/仓库当前可用，不证明未保存DOM已备份。浏览器完成首次heartbeat绑定后，通过已有鉴权POST /api/bridge/status读取能力；不调用管理open获取、不把这些字段泄露进公共health。真正执行时仍检查互斥/权限/保护状态，capabilities不是绕过门禁的许可。

### 5.5 close_session

输入：session_id 必填；reason:string 缺省 `user-ended`。

只释放本consumer角色，consumer_state=paused、requires_open=true，不停daemon/浏览器、不删pending。自己的未完请求转interrupted并保留原因；不结束别人的processing/owner。返回`{ok,session_id,consumer_state:'paused',agent_state,pending_count}`；agent_state按全session实际owner/恢复情况计算，有其他owner时不能假称会话paused。重复关闭幂等。再次协作必须同consumer重复open_editor同目标/session→registered，再await acquire；直接heartbeat或await均不能越过显式close闸门。

## 6. B 类意图 Schema

公共请求：`{protocol_version:2,intent_id,session_id,type,base_revision,payload,client_ts}`。session_id 与凭证绑定，deck_path 由服务任务登记推导，不信任页面另传路径。服务拒绝未知 type 与未知顶层字段。

| type | payload | 提交前条件 | Agent 工作副本动作 |
|---|---|---|---|
| brief.submitted | 现有 `{text,json}`；json.kind=design-brief | 无 deck 合法；已有 deck 先处理草稿 | 冻结简报，生成/改版，验收后 complete |
| design.submitted | `{version,kind,deck,answers}`；theme 含 tokens/theme_css | 基于已保存版本 | 双 SLOT 改版，保留内容，验收后 complete |
| anno.submitted | 现有 `{version,kind,deck,annotations}`；每项 id/targets/note/created_at | 目标对应 base_revision | 按分组批注定位，changed/missing 不盲改；验收后 complete |
| convert.requested | `{formats:[pptx,vector,pdf],scope:'all'}`，非空去重下载选择 | 文件已保存 | 永远--force --track both；完整三文件/native/manifest双轨成功，formats不减执行范围，禁单轨发布 |
| bake.requested | `{slide_ids:[string]}`，非空且去重 | 明确用户选择重新生图；内容已验收 | Step 5.6，代表页审批纪律保留；后续是否导出由明确请求决定 |
| illustrate.requested | `{slots:[string]}`，空数组表示全部待生成槽位 | 用户明确选择插画模式 | Step 5.5，失败不伪造 generated |

脑暴“预览”和“复制”都不是发送。点击发送才固化一个 intent_id。修改表单后发送重新生成同源 text/json；不能重用过期 briefLast。首次 intent 的 attempt=1。重试不改原 payload，按下面显式 rebuild 协议创建新 attempt；取消按既有状态机执行。

### 6.1 retry 的确认、幂等与独立路径

`POST /api/intent/retry` 精确 body（所有字段必填，未知字段拒绝）：

| 字段 | 规则 |
|---|---|
| session_id / intent_id | 当前浏览器凭证所属任务及原请求 |
| retry_id | UUID；一次明确重试先持久化此 ID，所有网络重发用同 ID |
| expected_attempt | 严格 integer≥1；页面确认时看到的原 attempt，不接收客户端指定新 attempt |
| mode | Literal `rebuild`；v1 不支持 resume/reuse，不静默复用旧副本 |
| base_revision | 当前磁盘源 revision；仅当前仍无 deck 时允许 null |
| confirmed | Literal true；点击确认“从当前版本重建，旧副本保留，未知外部操作可能重复费用”后才能发送 |

返回 `{ok:true,session_id,intent_id,retry_id,attempt,status:'pending',base_revision}`，为不可变 retry receipt。处理顺序：鉴权 → 按 `(session_id,retry_id)` 查记录 → 同报文重放原 receipt / 异报文 IDEMPOTENCY_CONFLICT → 首次请求检查 expected_attempt 与当前 attempt 相等、状态为 failed/conflict/interrupted、无未完 publication、base 与实际磁盘一致 → 同一 SQLite 事务中 attempt+1、状态 pending、新 base、retry receipt 和事件落盘。一个不同 retry_id 若竞争同 expected_attempt，只有一个成功；落后的请求返回 RECOVERY_REQUIRED，不能多增。base 过期返回 REVISION_CONFLICT；非法 mode/confirmed/类型返回 INVALID_ARGUMENT；非可重试状态或未完 publication 返回 RECOVERY_REQUIRED。这些失败都不建新 attempt。

同 retry_id 同报文的已成功重试，在后续认领或更晚 attempt 已发生后仍返回原 retry receipt，而非再次增号；页面用 get_status 获取当前进度。原始 intent 接收摘要不随 retry 改写，另存 attempts 与 retry_receipts 的基线/状态/结果历史。新 attempt 在 claim 时建立 `.pptx-html/jobs/<intent_id>/attempt-<N>/work/<relative-deck>`；relative-deck 相对 daemon workdir，N 为服务分配整数。旧副本永久保留、不重命名、不删除、不链接为新副本；旧生产者继续写旧路径不会污染新路径，但独立路径不撤销外部费用，也不构成任意 shell 沙箱。

### 6.2 有界请求与内联结果

intent POST 的完整 JSON body≤2MiB；payload 按递归对象键排序、数组顺序保留、ensure_ascii=false、紧凑 JSON 的 UTF-8 字节数计量，≤1MiB；禁止非有限数。payload digest 使用同一规范编码，原 payload 数据完整存储。MCP 内联阈值也用此 payload_bytes：≤16KiB 返回完整 payload，超过则返回摘要/intent_file/payload_bytes，由 Agent 读完整文件。派生 JSON 失败不交付不存在指针。超限返回 PAYLOAD_TOO_LARGE、保留输入，不截断、不伪分页。save/draft/asset 不受此控制请求小限额约束，按 §7.5 独立限额执行。

## 7. HTTP API

### 7.1 认证与通道

- `/api/health` 不带凭证只返回 `{ok,protocol_version,bridge_available,instance_id}`，不含路径、session、token、版本历史；带管理凭证可返回 workdir 身份供代理验证。
- 管理请求 `Authorization: Bearer <management-token>`。凭证从本机 0600 发现文件读入代理内存，不交给模型。
- 浏览器使用作用域为 session 的凭证，仅能提交、读状态、保存当前目标、换受管图片、操作自己的草稿、订阅当前任务事件，不能 complete/publish。
- URL fragment `#brt=<browser-token>&session=<id>` 在初始化时读入 sessionStorage 后 history.replaceState 移除。fragment 不进入 HTTP 请求/Referer；不能写 localStorage 明文长期共享管理 token。
- SSE 使用 fetch 流 + Authorization，避免将 bearer 放在 query。解析 UTF-8 分块、多行 data、CRLF、重连游标；不把浏览器 SSE 当 MCP SSE 传输。
- Host 必须为准确 loopback 服务主机和端口。浏览器写请求必须有严格同源 Origin；所有请求只要携带 Origin 就必须匹配，拒绝 null/跨源/前缀匹配。非浏览器管理 Bearer 客户端可无 Origin。
- 浏览器同源 GET/HEAD 可不发送 Origin：鉴权 API 仍须有效 session Bearer 且 Sec-Fetch-Site=same-origin；这不是匿名写豁免。公开 health/已登记静态交付资源按一致性 §9.4 执行 Host、白名单、Fetch Metadata 和链接检查；静态资源不携带管理 token。无 body GET/HEAD 不要求 JSON Content-Type，不支持的方法仍返回405。

### 7.2 路由表

| 方法与路径 | 权限 | 入参/结果 |
|---|---|---|
| GET /api/health | 公共/管理增强 | 上述健康结构 |
| POST /api/bridge/open | 管理 | 对应 open_editor，附 consumer_id |
| POST /api/bridge/await | 管理 | session_id/consumer_id/timeout_sec → await 结果 |
| POST /api/bridge/update | 管理 | 对应 push_update |
| POST /api/bridge/status | 管理或当前任务浏览器 | session_id → get_status |
| POST /api/bridge/close | 管理 | session_id/consumer_id/reason |
| POST /api/bridge/heartbeat | 管理或浏览器 | §7.3 role 分支精确 body；续租或更新本 client 快照 |
| POST /api/intent | 浏览器 | 公共请求 → `{ok,accepted,intent_id,seq,status}` |
| POST /api/intent/retry | 浏览器 | §6.1 session_id/intent_id/retry_id/expected_attempt/mode/base_revision/confirmed → 不可变 retry receipt |
| POST /api/intent/cancel | 浏览器 | session_id/intent_id → cancelled 或 CANNOT_CANCEL_RUNNING |
| GET /api/events?session_id=...&after=... | 浏览器 | text/event-stream，after 为非负 event id |
| POST /api/bridge/draft | 浏览器 | session_id/client_id/html/annotations/base_revision → `{ok,draft_id}`；创建 client 必须匹配绑定 |
| GET /api/bridge/drafts?session_id=... | 浏览器 | 当前 session 最近50条草稿元数据，含创建 client；不返完整正文 |
| GET /api/bridge/draft?id=... | 浏览器 | 当前 session 草稿内容；恢复创建新草稿，不覆盖另一 client 原记录 |
| POST /api/save | 浏览器/管理 | path/html/init 加 session_id/base_revision → §7.4 A类 receipt |
| GET /api/versions?path=... | 浏览器/管理 | 受管范围内版本，不列其他项目 |
| POST /api/rollback | 浏览器/管理 | path/hash 加 session_id/base_revision → §7.4 A类 receipt |
| POST /api/bridge/asset | 浏览器 | session_id/base_revision/path/data_base64 → §7.4 A类 receipt；仅 assets 允许格式 |
| POST /api/convert | 浏览器/管理 | 仅显式 --convert，本地执行与 Agent 任务互斥 |
| GET /api/convert-status | 浏览器/管理 | 当前受管转换状态 |
| POST /api/bridge/bootstrap | 仅本机管理 | §7.6 mode/path固定目标签发单次boot URL；不创建consumer、不自动init |
| GET /bootstrap | landing公共/兑换仅单次boot | §7.6片段引导、限定cookie、一次使用后302 editor；HEAD拒绝 |
| POST /api/intents/query | 当前任务浏览器 | §7.7 statuses/cursor/limit或intent_id；持久摘要分页，无payload |

对无 MCP 的手动启动，daemon 发放本地编辑会话浏览器凭证，网页功能不要求安装 mcp 包。普通 http.server/file:// 不支持这些 API，维持现有降级；不把无后端静态场景误判为保存成功。旧匿名写 API 明确401，提供的 editor/启动脚本/测试一起升级；嵌入 postMessage 保持不变，桥不接管宿主保存。

### 7.3 heartbeat 精确结构与浏览器绑定

`POST /api/bridge/heartbeat` 由 role 判别两个严格 body，字段全部必填、未知字段拒绝，不能混入另一分支字段：

- 管理：`{protocol_version:2,role:'consumer',session_id,consumer_id}`。只给本 session 已登记且有效的当前 owner 续租，不认领请求、不让过期/paused owner 复活；状态由 await/processing 推导，不接受客户端自报 working。返回 `{ok:true,role:'consumer',session_id,server_time,lease_until,agent_state}`。
- 浏览器：`{protocol_version:2,role:'browser',session_id,client_id,dirty,active_edit,draft_pending,revision,last_event_id}`。client_id 为每 tab 生成的 UUID；三个状态字段为严格 boolean；revision 是该 tab 已加载源 revision 或 null，不能改服务 revision；last_event_id 为严格非负整数，表示已成功应用或持久记录待处理的游标，不可超出本 session 最新事件。返回 `{ok:true,role:'browser',session_id,client_id,server_time,last_seen,online_until,revision,last_event_id}`，其中 revision/游标回显本次接受的 client 快照，非服务当前版本。

首次合法 browser heartbeat 在 SQLite 事务中把该受限 token 摘要绑定 `(session_id,client_id)`；未绑定 token 除这次握手外不可调用业务 API。之后同 token 换 client_id 或跨 session 返回403；浏览器 token 不能使用 role=consumer。绑定后 draft 写入只能署名自身 client，当前 session 草稿仍允许列出/读取并明确恢复成新草稿，不能跨 session。复制 tab 产生新 client 时须通过合法 open 取得独立 token；同一 tab 刷新保留自己的 sessionStorage client_id。管理端不能通过 browser body 假装页面在线。

浏览器每15秒心跳、45秒未见离线，代理每15秒续90秒 lease；各 tab 至多一个 heartbeat 在途，避免旧快照晚到倒写。页面的 draft_pending 应涵盖未发批注/表单、待确认请求、保存/资产在途等保护状态。last_seen/server_time/lease 时间均由服务产生 UTC RFC3339；离线状态由服务计算，get_status 中 dirty=null。关闭/过期 owner 续租返回 RECOVERY_REQUIRED，不能利用成功 receipt 重放例外重新取得新写权限。

### 7.4 A 类保存、换图、回滚 receipt

三个写端点成功返回精确核心 `{ok:true,session_id,path,receipt_id,revision,export_revision,snapshot_id,events}`；path 为工作区相对合法路径，revision 为保存后源摘要，export_revision 为摘要或 null，events 为持久 event id 数组，snapshot_id 指本次保护版本。可附兼容字段 committed:boolean、hash:string|null、gitReady:boolean，Git 版本是专用 ref 保护提交而非用户当前分支提交。只有 publication COMMITTED 才返回成功。

幂等 write key 为 session+动作+base_revision+规范正文摘要；HTML 按原字符串、图片按解码字节、回滚按解析后完整 hash，路径规范化后参与摘要。相同 key 命中成功且实际 bundle 仍等于原发布结果→原 receipt，无新写/事件/版本；目标已前进→REVISION_CONFLICT，details 含原 receipt_id 与当前 revision；存在未完 publication→RECOVERY_REQUIRED。客户端串行保存并重发同一不可变快照，不依赖不存在的 A类 intent UUID。完整规则和磁盘验证见一致性 §5.1。

### 7.5 分路由传输限额

1MiB=1,048,576字节。先按路由选择预算，再读取 body；Content-Length 与实际接收字节都检查，拒绝歧义长度/未知长度传输，不接收超过限额的尾部。JSON 路由要求 UTF-8/application/json，不以字符数量当字节预算。

| 路由/对象 | 集中常量 | 上限 |
|---|---|---|
| 一般控制请求及 POST /api/intent（含retry、heartbeat、update） | CONTROL_BODY_MAX | 完整 JSON body 2MiB |
| intent.payload | INTENT_PAYLOAD_MAX | §6.2 规范 JSON UTF-8 1MiB |
| MCP 内联 payload | INTENT_INLINE_MAX | 同一计量≤16KiB |
| POST /api/save、POST /api/bridge/draft | DOCUMENT_BODY_MAX | 完整 JSON body 64MiB |
| POST /api/bridge/asset | ASSET_BODY_MAX | 完整 JSON body 48MiB |
| asset 解码后图片 | ASSET_RAW_MAX | 原始文件32MiB，另受格式/尺寸校验 |

所有数值在 bridge_core 集中定义；代理/editor 可按公开能力或协议常量执行前置提示，服务端最终裁决。不得用一般控制预算把原64MiB HTML保存收窄；多MiB HTML/草稿与典型大图是正常支持场景。图片 raw≤32MiB仍需完整JSON≤48MiB；超任一预算413 PAYLOAD_TOO_LARGE，保留输入、零部分发布。请求预算不替代磁盘总量预算，不扩大静态/管理权限。

### 7.6 无MCP手动CLI与一次性bootstrap

手动CLI新增互斥参数 `--deck REL` 与 `--new [REL]`：--deck必须指向workdir内已有HTML；--new不传REL时为index.html，目标必须不存在。两者都省略时，仅当index.html存在才打开它，否则创建briefing会话的target=index.html，不扫描猜测其他HTML；非index必须明确`--deck slides.html`。路径/目录单deck/链接约束与MCP相同，参数非法非零退出，无覆盖。脚本透传这些参数；--no-browser不启动OS浏览器，但向本机终端提供单次启动URL。--mcp不接受这两个手动选择参数，目标仍由open_editor给出。

本机CLI每次打开/重开都生成新的bootstrap授权；初次启动由daemon本机调用签发，同daemon已存活时，CLI用发现文件管理凭证调用 **POST /api/bridge/bootstrap**。该管理路由严格body为 `{mode:'deck'|'new',path:REL}`，CLI先按上述缺省确定mode/path；返回`{ok:true,url,expires_at}`，URL固定为本实例`/bootstrap#boot=<token>`。这是启动凭证签发，不创建consumer、不开MCP，也不提前初始化Git；浏览器和boot token不能调用签发路由。bootstrap随机强度至少256bit，数据库只存摘要、instance_id、固定mode/target、expires_at、used_at；有效期300秒（BOOTSTRAP_TTL_SEC），单次使用，重启失效。再次签发不撤销已有browser token。

**fragment不进入HTTP，兑换链路固定为两次GET，而不是假定服务能直接读取fragment：**

1. 本机打开`/bootstrap#boot=...`；无ticket查询参数的GET只返回固定landing HTML，不创建session/凭证。页面无第三方资源、不读取deck，读取boot后立刻replaceState清除；缺片段提示重新运行本机入口。
2. landing以SHA-256(token UTF-8)的64位小写hex作为非秘密ticket选择器，设置短期cookie `pptx_bootstrap_<ticket>=<token>`（token使用URL安全随机编码；仅Path=/bootstrap、SameSite=Strict、Max-Age=300、无Domain），再导航`/bootstrap?ticket=<ticket>`。不同token不同cookie名，避免两个启动tab抢同cookie而打开错误目标。ticket只是完整token摘要，不是认证凭证；query不含raw token。此cookie只用于GET /bootstrap兑换，不作API认证，不使用无法读取302 Location的fetch manual模式。
3. **GET /bootstrap?ticket=...** 从对应命名cookie取token，先核对token摘要等于ticket，再校验loopback地址、精确Host/端口、Origin若有必须同源、Sec-Fetch-Site=same-origin、本实例/未过期/未使用/绑定目标合法。事务消耗token、创建/复用固定session并发browser token，302 Location=`/editor.html#brt=<browser-token>&session=<id>`，只清本ticket的cookie。所有响应no-store/no-referrer。首次OS landing允许Sec-Fetch-Site=none，兑换只许同源landing；带ticket缺cookie401，不回落landing；非法/未知query400；HEAD405不兑换；无效/过期/重放401、来源403、目标冲突409。
4. editor按既有brt流程清fragment→sessionStorage→首次heartbeat绑定→鉴权status/query。兑换响应丢失不允许重放原browser token，用户重新运行CLI/脚本拿新的单次URL；旧已登记session复用，不能用匿名重定向恢复凭证。

boot token不得进入query、Referer、日志、技能指令、payload、HTML产物或其他API；落入其他API一律401。landing只执行固定受信脚本，CSP限制default-src为none并仅许可该脚本，frame-ancestors为none，不开放CORS。仅本机终端展示/OS打开的启动URL允许含短期boot片段，管理token永不显示。该GET是单次本机启动授权兑换例外，不放宽普通GET/HEAD与写API安全规则。

手动打开不要求已有Git：登记/预览成功，capabilities.git_ready=false，不自动init，也不冒称已保护。首个发布写入前用户明确确认，`POST /api/save`携init:true，先init（若已有父仓库则复用）并保护基线，再写HTML；未确认409 GIT_INIT_REQUIRED，init/保护失败503 STORAGE_UNAVAILABLE且目标不动。无Git工具也允许手动打开/保SQLite草稿，禁止未保护发布。其他发布操作先引导首存确认。MCP open仍按§5.1自动init，不混用此手动规则。

### 7.7 浏览器持久请求查询

**POST /api/intents/query** 仅允许已绑定的当前session浏览器凭证，body精确为 `{session_id,statuses?,cursor?,limit?,intent_id?}`，未知字段拒绝，body使用控制路由2MiB预算：

- session_id必填；statuses可省略，若给出为非空且无重复枚举数组，成员仅pending/processing/succeeded/failed/conflict/interrupted/cancelled；省略为全部状态。
- cursor可省略默认0，严格integer≥0；limit可省略默认50，严格integer 1..100，布尔值不算integer。
- intent_id可省略；给出时必须UUID，且statuses/cursor/limit即使是缺省值也禁止出现，进入单条模式。

返回 `{ok:true,items:[{id,seq,type,status,attempt,base_revision,created_at,updated_at,error,result_summary}],next_cursor,has_more}`。error为`{code,message,retryable}`或null，描述当前attempt失败/冲突/中断原因，message至多2000字符并脱敏。result_summary在succeeded时为`{receipt_id,revision,export_revision,message}`，message≤2000字符；无持久成功结果为null。绝不内联payload、HTML、checks、凭证或内部路径。单条模式找到时items长度1、next_cursor=null、has_more=false；不存在或属于他session的ID统一404 INTENT_NOT_FOUND，不泄露归属。

列表以session固定、statuses过滤、seq>cursor、seq升序，读取limit+1判断has_more；有更多时next_cursor=本页最后seq，否则null（空页同样null/false）。查询只读、不claim/续租/改attempt。每页是当前SQLite读快照，不承诺跨页状态冻结；状态过滤变化可使旧seq出现，因此完整恢复从cursor=0重建，不只追末尾。status的recoverable_count精确定义为当前failed/conflict/interrupted条数，不能代替详情查询。

首次载入、新origin重新认证和SSE resync时，先取status及其latest_event_id=E，再从query cursor=0分页重建请求列表，保存/呈现或记录待处理后订阅after=E的SSE补齐查询期间变化；若E又过期则重做。分页返回按id/attempt合并，不能用旧页覆盖更新的SSE状态。已接收请求及result不随SSE事件清理，故旧事件消失仍能恢复retry/cancel/查看结果。失败状态的error.retryable表示允许用户进入明确恢复操作，不代表自动重跑付费动作。

## 8. SSE 事件

| event | data 必需字段 | 页面动作 |
|---|---|---|
| deck-changed | session_id/revision/path/source/receipt_id | 检查当前任务、草稿和加载代次，重读已发布文件 |
| export-refreshed | session_id/revision/export_revision | 强制失效 manifest 并重新获取，不能只调用使用缓存的 refreshExport |
| assets-changed | session_id/revision/files | 刷新主画布和缩略图，标记相关导出 stale |
| intent-status | session_id/intent_id/status/attempt | 入队/处理中/冲突/完成/失败显示 |
| notice | session_id/intent_id/level/message | 真状态，不伪造百分比 |
| resync-required | session_id/latest_event_id/revision | §7.7先status记E，再query全分页恢复请求，必要文件另读并after=E补流；不能以计数/跳游标替代 |
| server-stop | instance_id | 显式停止提示并停止当前流；可手动重连 |

每条业务事件包含 `id:`，`data` 为单个 JSON 对象。ping 是注释保活，15 秒一次，无业务 id。重连退避 1、2、4、8、16、30 秒；同 id 不重复应用，但客户端只在成功处理或记录待处理状态后推进应用游标。通知持久化先于 HTTP completion receipt。

事件保留至少最近 7 天和每 session 最近 1000 条（二者取覆盖更广者）；低于 oldest_event_id 的游标触发 resync-required。intent/receipt/恢复快照不随 SSE 清理。容量超过保护上限时拒绝新提交并说明空间问题，不删除未确认请求。

## 9. 错误契约

业务错误统一 `{ok:false,error:{code,message,retryable,details}}`；details 只含允许公开的 session/intent/revision/字段名，不含 token、堆栈、任意磁盘路径。HTTP 状态与 code 对齐。

| HTTP | code | 后续动作 |
|---|---|---|
| 400 | INVALID_ARGUMENT / UNSUPPORTED_PROTOCOL | 修正字段，不重试原报文 |
| 401/403 | UNAUTHORIZED / ORIGIN_DENIED / PATH_DENIED | 重新通过合法启动入口连接；禁止自动转匿名写 |
| 404 | SESSION_NOT_FOUND / INTENT_NOT_FOUND | 重新 open 或显示记录不存在 |
| 409 | REVISION_CONFLICT / SESSION_BUSY / IDEMPOTENCY_CONFLICT | 展示差异/排队/修正 ID，禁止覆盖 |
| 409 | RECOVERY_REQUIRED / CANNOT_CANCEL_RUNNING | 未登记或close后先重新open；待恢复请求由用户决定，禁止自动重复副作用 |
| 409 | GIT_INIT_REQUIRED | 手动首存须用户确认init:true，先初始化及保护基线，不得先覆盖目标 |
| 413 | PAYLOAD_TOO_LARGE | 保留输入，下载或缩减后重新明确提交 |
| 422 | INVALID_ARTIFACT / VALIDATION_REQUIRED | 修正工作副本与验收证据 |
| 503 | RECOVERY_FAILED / STORAGE_UNAVAILABLE | 保留快照和请求，停止发布，不返回成功 |

## 10. 兼容性和验收索引

- 保持原 HTML 编辑标记与 canonical 不变；应用协议独立升级。
- 官方 MCP 协议版本由 SDK 协商，不伪造某个宿主必然接受 120 秒。
- 常驻 HTTP 服务仍只用标准库，`mcp>=1.28,<2` 仅 --mcp 路径依赖；缺包时打印安装指引到 stderr 并非零退出，不影响手动编辑器。
- 逐工具、页面、故障和安全验收见 [../test_acceptance/editor-agent-bridge.md](../test_acceptance/editor-agent-bridge.md)。所有声称幂等的动作必须测试“执行完成但响应丢失”的重试，而不是只重复正常请求。

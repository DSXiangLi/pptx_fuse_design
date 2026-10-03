# 编辑器↔Agent 桥 v2：文件一致性、恢复与安全

> 状态：一致性规范已用于 2026-10-03 的 P0–P3 Linux 自动实现；publication fault 与单页协议性能已测，真实大 deck、全回归和人工环境仍未完成。
> 上位规范：[协议与状态机](editor-agent-bridge-protocol.md)。本文细化文件、恢复和安全约束，不增加MCP工具，不改变intent状态机，不以旧版语义覆盖[新总览](editor-agent-bridge.md)。
> [执行计划](../progress/1002_editor_agent_bridge_plan.md)与[测试验收计划](../test_acceptance/editor-agent-bridge.md#16-2026-10-03-实际执行记录)分别承载实施顺序和真实验收状态；本文失败矩阵仍是后续全量验收的必需输入。

## 1. 目标、现状与基本约束

桥的职责不是让 Agent 可以写更多文件，而是让“谁基于哪一版修改、哪一组文件已经发布、页面有没有保住自己的输入”成为可核验的事实。

旧 v1 的单文件先写后保护、用户 index/分支污染、迟到保存清 dirty、`openHtml` 清草稿和缓存 manifest 不重取等路径已由 bridge v2 受管模式替换：`tools/bridge_core.py` 提供 bundle publication/CAS/journal/Git 专用 ref，`editor.html` v3.2 使用保存世代、草稿风险、加载 epoch 与强制产物重取。纯静态/嵌入降级仍保留，不冒充受管保证。

当前实现继续受以下硬约束：

1. SQLite 是请求、所有权、结果、revision 和事件的唯一状态真相；文件 journal 是它的可验证恢复材料，不是另一套任务状态机。
2. Agent 只收到服务分配的工作副本路径；正常发布只能走 `push_update(action=complete)`。浏览器保存、换图、回滚、本地 opt-in 转换复用同一个发布器。
3. 发布前做 revision 比较并交换（CAS）；过期副本不能覆盖当前文件。浏览器未保存的 DOM 不等于磁盘版本，必须另行保护。
4. HTML、图片、字体、导出件和派生 manifest 按受管文件集合处理；不能只保护 HTML。
5. 多文件替换只有可恢复提交，不是操作系统级全局原子事务。桥内读写隔离与崩溃恢复必须落地，不能用“原子保存”掩盖窗口。
6. 不拦截任意外部 shell，不承诺外部生图恰好一次，不把本机 bearer 或工作区路径当沙箱。

本文的 v1 表示桥首次交付范围；线上应用协议仍为 `protocol_version:2`。

## 2. 受管 bundle 与归属

### 2.1 登记模型

以规范化 workdir 为 daemon 边界，以目标 HTML 所在目录为 bundle 根。一个目录只登记一个受管 deck。SQLite 中除协议规定的实体外，持久化 `bundle_files`、`snapshots`、`publications`、`write_receipts` 与凭证摘要；它们都归属 session，不能由静态目录扫描结果直接替代。

`bundle_files` 至少记录 `session_id / path / class / sha256 / size / present / snapshot_id`。path 是相对于 bundle 根的 POSIX 路径，case-sensitive；登记前拒绝名称碰撞、控制字符和无法无损编码的路径。登记根与文件必须位于 workdir 内，受管集合不得与已有任务重叠。只比较 HTML 路径而不比较 assets/fonts/export 集合是不充分的。

首次登记明确受管范围：目标HTML、已有assets/fonts合法普通文件、导出集合和派生文件；目录内其他HTML、原始pptx、资料、脚本不自动纳入。MCP open立即准备Git保护基线；手动bootstrap可先登记文件清单供预览，非Git时标未保护，延至用户首存init:true后建立基线，不能因缺Git拒绝打开。发现符号链接/硬链接/危险扩展仍拒绝登记并指出相对路径，不能沿链接纳入另一项目。

后续的新增文件只来自受控工作副本差异或受限资产 API；必须在合法子树和格式白名单内，且目标不存在未登记的同名文件。未登记文件即使位于 `assets/`，也不能被静默覆盖或删除。初次登记前存在的合法资产以明确的基线清单固定归属，之后不能每次递归复制目录冒充清单。

### 2.2 文件分类

| 类别 | 范围 | 是否影响源 revision | 发布与回滚规则 |
|---|---|---|---|
| 源 HTML | 登记的唯一目标 `.html` | 是 | 完整字节保存；已有编辑契约不变 |
| 源图片 | `assets/` 中登记图片，包括上传图、插画与页面烙入图 | 是 | 字节、路径、新增与删除均计入 |
| 源字体 | `fonts/` 中登记的 woff2/woff/ttf/otf | 是 | 字体替换必须使旧导出 stale |
| 导出件 | `export/` 下登记的 pptx/pdf/svg/png、原生参考页图及报告 | 否 | 独立 export revision，属于同一保护快照 |
| 导出 manifest | `export/manifest.json` | 否 | 与该次导出件一起发布；不能先发“已刷新”再落文件 |
| 派生分析 | 根 `manifest.json`、`.manifest-baseline.json`、`capacity-report.json`，及登记的技能报告 | 否 | 绑定生成时的源 revision；不因存在就认为有效 |
| 内部状态 | `.pptx-html/`、SQLite/WAL/SHM、job、snapshot、draft、journal、token | 否 | 绝不进入用户 bundle、Git 用户分支或静态托管 |
| 其余文件 | 未登记资料、其他 deck、目录外引用 | 否 | 不复制、不提交、不回滚；本桥不保证其一致性 |

报告允许登记为派生文件，不等于开放任意脚本文件发布。字体子集化若写入 fonts 或修改 HTML，则是源变更；仅生成 PPTX 内嵌字体 part 则仍是导出变更。`assets/page-<id>.png` 虽然由生图得到，因 HTML 直接引用，属于源而非导出。

对 HTML 引用的工作区内本地文件做依赖检查：引用必须落在登记范围，或明确判定为不可受管外部依赖。受管交付验收不得把后者假称可回滚。远程字体、远程图片随外网变化不受 revision 保证，验收报告必须列明；本桥不自动下载或修改 URL。

### 2.3 删除、增量与旧导出

工作副本是完整受管快照，缺失的受管文件表示删除候选，必须在 seal 差异清单列出；不得以整个目录 `rmtree` 实现删除。发布删除只能针对旧清单文件，未登记同级文件原样保留。

源变更后可以保留旧导出供对比，但旧导出绑定的 `export_source_revision` 不变，`export_stale=true`。不能因保留了 `export/manifest.json` 就给它盖上当前源版本。纯导出刷新不制造源变更，不让同源的排队请求无故过期；内容未改变的重新导出也不能阻止实际产物缓存刷新。

## 3. revision：内容指纹、导出指纹与页级 hash 分离

### 3.1 确定性算法

源 revision 为 `sha256:` 加 64 个小写十六进制字符。没有目标 HTML 的 briefing 会话值为 `null`，不构造空 HTML 的假版本。

计算步骤：

1. 从受管清单取当前存在的源 HTML、assets、fonts；逐文件流式计算原始字节的 SHA-256 和字节数。不解析或规范化 HTML，不去除换行、BOM、CSS 和字体内容。
2. 路径统一为 bundle 根相对 `/` 路径，禁止 `.`、`..`、反斜杠、绝对路径、NUL。不悄悄大小写折叠或 Unicode 改名；以 UTF-8 字节序排序。
3. 构造记录数组 `[path, byte_length, content_sha256]`；以紧凑 JSON（UTF-8、ensure_ascii=false、无空格、无末尾换行、数组顺序固定）编码。
4. 对 `b"pptx-html-source-v1\n" + encoded_records` 求 SHA-256，添加前缀。空目录不计入；文件新增、删除、改名和同名换字节均改变摘要。

记录域前缀是算法版本，不随协议版本变化。后续改变算法必须迁移基线，不能在同一数据库里把两种算法的摘要当同义值。

导出 revision 使用同一记录编码，对当前登记的 export 文件与导出 manifest 求摘要，域前缀为 `pptx-html-export-v1\n`；没有任何导出件时为 `null`。派生分析文件有单独的逐文件 hash 和 source binding，不参加上述两种摘要。发布整个 bundle 时另计算完整清单摘要，包含分类与缺失标记，用于 journal 校验而不是作为页面编辑版本。

### 3.2 绑定与 stale

SQLite 的发布记录同时保存：`source_revision`、`export_revision`、`export_source_revision`、派生报告各自的 `derived_source_revision`、完整 bundle 清单、receipt。导出 freshness 的必要条件是：

- 当前源 revision 等于 export_source_revision；
- 登记的导出文件存在且 hash 与最近已确认清单一致；
- 桥执行固定`--force --track both`；完整`export/deck.pptx`、`deck-vector.pptx`、`deck.pdf`、`export/native/`逐页参考图与`export/manifest.json`均由本次重建，manifest的export.tracks同时记录editable/vector成功且引用文件齐全；formats只选择下载，不减少执行范围。fresh为完整集合全局binding，禁单轨发布，不能以旧轨或旧native补齐新集合。

现有导出 manifest 没有桥字段时不伪造 freshness：首次登记可保护其字节，但其来源绑定为未知，状态 stale/未核验。新的成功导出由工作副本验收和源前后校验建立绑定，SQLite 持有绑定，不要求篡改旧 manifest schema。只有当本次 complete 明确验收了新导出，才更新绑定；继承来的旧产物不能因一起复制而“变新”。

协议 `export-refreshed` 中的 revision 是当前源 revision，export_revision 是产物内容摘要。两者相等的事件仍可能是新的确认；事件 id 和 receipt 用来驱动一次真正刷新，不能仅以 hash 去重事件。

`editor.html:3738` 附近的页级 `data-content-hash` 仍遵循既有 canonical，与 extractor 双端一致，不扩展成 bundle 算法。它不包含 CSS、同名图片字节、字体，也不足以作为 CAS。桥模式以 bundle stale 为总兜底：bundle stale 时不能只因每页旧 hash 相等就显示全部新鲜。资产影响无法逐页精确归因时，整份导出保守 stale，不虚构精确页级结论。

### 3.3 外部改动与 ABA

服务在登记、认领复制前、保存/发布 CAS 前、回滚前和重启恢复时重新核对实际文件，不能只信 SQLite 中缓存的 revision。GET/status 可以使用最近观察值，但必须经过有界的后台观察或关键动作检查；观察到外部改动时，在 bundle 锁内建立新的保护快照、更新 revision 并记录事实事件，然后对旧 base 返回 conflict。保护失败则冻结写入，不以旧 revision 继续。

外部删除导出或修改派生 manifest 不改变源 revision，但会使产物完整性检查失败，必须失效相关视图。后台观察是便利功能，不是 CAS 的前提。

revision 是内容地址，不是递增序号：A→B→A 可以回到同一个摘要。只有相同文件字节才算相同源，不保证“从未发生过其他操作”；需要顺序时使用 event_id、seq、attempt 和 publication id。防迟到完成依赖所有权与 attempt，不依赖 revision 独自承担 fencing。

## 4. Git 基线与恢复快照

### 4.1 父仓库路径与 index 隔离

必须通过 `git -C <workdir> rev-parse --show-toplevel` 找仓库根。Git 对象中的 path 一律为相对该仓库根的路径，而 API path 相对 workdir，bundle 清单 path 相对 bundle 根，三者显式转换，禁止混用。

例如仓库根 `/repo`、workdir `/repo/tests/decks/demo`、目标 `/repo/tests/decks/demo/index.html`，Git 读取键是 `tests/decks/demo/index.html`，不是 `index.html`。命令以参数数组调用，路径参数置 `--` 后；对象读取使用已解析的完整 commit id 与已校验树路径，不把用户字符串拼为 shell。

桥选择“专用 Git ref + 隔离 index”的版本存储，不自动提交用户当前分支：

1. 基线和后续保护版本写入仓库中的 `refs/pptx-html/<workspace-key>/<session-id>`；workspace-key 来自规范化工作区身份摘要，session-id 由服务生成。
2. 用 `.pptx-html/` 内临时 `GIT_INDEX_FILE` 构造仅含受管文件的树；树路径仍以仓库根为基准。通过 `hash-object`、`update-index --cacheinfo`、`write-tree`、`commit-tree` 创建保护对象，不运行用户工作树的 `git add`。
3. 用 `update-ref <ref> <new> <expected-old>` CAS 更新专用 ref；该旧/新值进入 publication journal。提交身份通过每次命令 `-c` 指定，不修改本地或全局 Git 配置。
4. 用户 HEAD、分支、真实 index 及已暂存内容字节完全不动；不 stash、不 checkout、不 reset、不清理其他文件、不执行用户 hooks/filter。Git 对象来自已 seal 的原始字节，不能由 checkout filter 改写。

因此“保存并记录版本”是可从编辑器历史回滚的保护版本，不等同于替用户向当前开发分支提交。验收必须检查真实 index 文件 hash、HEAD 和无关工作树文件字节前后一致。Git 对象库新增对象与专用 ref 是明确允许的副作用。

没有仓库时，只在用户指定workdir初始化；已有父仓库复用其对象库及专用ref，不在子目录嵌套init。MCP open_editor按既定授权自动init并建保护基线，失败则open报错。手动bootstrap打开则先登记/预览，非Git或Git不可用时仍可打开，capabilities.git_ready=false，绝不声称已保护。

手动首次保存由用户确认后带init:true：锁内复核base→init仓库→保护当前受管基线→正常发布；未确认返回409 GIT_INIT_REQUIRED，初始化/保护失败返回503且目标字节不动。若有现成仓库则直接建立保护基线，不要求重复init。资产/回滚/本地转换等发布操作同样要求基线就绪，UI先引导完成首存确认；草稿与请求的SQLite持久化不伪装为Git保护，也不因尚无Git禁止保稿。

### 4.2 快照内容

快照目录 `.pptx-html/snapshots/<snapshot_id>/` 存储不可变清单与恢复字节；至少包含旧版和候选新版的所有受管内容、创建/删除清单、源/导出摘要、Git commit/ref、来源动作和时间。使用拷贝，不使用可被后续写入污染的硬链接。可按 hash 复用不可变 blob，但首次实现不要求去重存储。

快照与 Git 有不同职责：快照为事务恢复提供明确的新旧字节，Git 为用户历史提供可核验版本。不能仅凭 Git 存在便删除未完成 journal 依赖的恢复字节。快照不存 bearer、浏览器凭证、管理发现文件、任意工作目录外资料。

`/api/versions?session_id=...&path=...` 只列该 session 登记的快照/保护 commit，不遍历父仓库的其他项目历史。每项的 `snapshot_id` 是稳定回滚标识，`hash` 只是可空的 Git commit 展示值；回滚请求的 `hash` 字段可承载该 session 版本表内的 `snapshot_id`，并兼容旧 Git hash，但不能使用任意可解析 Git commit 来读取未受管文件。迁移旧版本时仅显式导入该目标受管路径；旧 commit 不包含的字体/导出不能伪造存在，标注历史范围不足，不默认作为完整 bundle 回滚点。

### 4.3 回滚是新发布，不是 Git reset

回滚请求携带 base_revision，在锁内再次核对实际文件；当前受管改动先快照保护，然后从选定历史清单构造候选 bundle，走同一个 journal 发布器。新增/删除/换图/字体一起恢复；未登记文件原样保留。

回滚产生新的 receipt、事实事件和保护版本。源 revision 可能等于历史值，发布 id 仍是新的。若历史导出完整且有可信 source binding，可同时恢复 freshness；否则恢复字节但继续 stale。回滚前用户未保存 DOM 不在磁盘快照里，由 §8 的浏览器草稿保存，不能向用户宣称 Git 已经保护了它。

## 5. 浏览器保存、资产写入与 A 类 receipt

### 5.1 服务端保存流程

浏览器/管理 `/api/save` 必须指向 session 登记的目标；既有 `path` 与服务推导路径不一致即拒绝。处理顺序为：鉴权与限额 → 校验 UTF-8 HTML → 保留请求候选字节 → bundle 锁 → 验证当前 revision → 旧 bundle 快照/Git 保护 → seal 新 bundle → journal 发布 → SQLite receipt/events → 返回。

只改变 HTML 的保存继承当前受管资产；先前读到的另一 tab 图片不能被陈旧 HTML 保存误回滚。若 base_revision 过期，即使 HTML 字节看起来相同也不能忽略资产差异。受管模式保存失败不自动降级成 FSAA 写原文件；允许用户明确下载副本，但文案为“副本已下载，未发布到工作区”，不清除桥的未确认状态。

A 类写入不进入 Agent 工作队列。为处理“已落盘但响应丢失”，服务在 SQLite 中记录 write receipt，并从现有报文生成稳定写入键，不增加 MCP 参数：

- key 域包含 session、动作类型、base_revision，以及规范化请求正文摘要；HTML 按原始字符串字节、资产按解码字节、回滚按解析后的完整目标 hash 计算。
- 同键重试且当前目标仍等于该 receipt 的发布结果，返回原 receipt，不再发事件、再做 Git 版本或再写文件。
- 若同键已有成功记录但目标已经前进，返回 `REVISION_CONFLICT`，附允许公开的原 receipt_id 与当前 revision，不能重放旧内容，也不能让客户端误以为旧 receipt 代表最新磁盘。
- 原处理仍处于未完成 publication 时，返回 `RECOVERY_REQUIRED` 或等待短暂锁释放后重查；不得再次建立另一条发布事务。

保存 receipt 必须包含 `ok/session_id/path/receipt_id/revision/export_revision/snapshot_id/events`，可保留旧 `committed/hash/gitReady` 展示字段；其含义按 §4 的保护版本解释。资产与回滚 receipt 使用相同确认核心。receipt 与事件同一 SQLite 提交；网络响应不是持久化边界。

### 5.2 资产写入

`/api/bridge/asset` 只接受当前任务 `assets/` 下已登记图片的替换或明确新图片路径。路径禁止 `.pptx-html`、fonts、export、HTML、可执行文件和设备文件。图片类型按扩展与文件签名双校验；浏览器上传支持 PNG/JPEG/WebP/GIF，不把 SVG 当任意 XML 上传入口。既有或 Agent 生成 SVG 可纳入受管资产，但发布时必须检查禁止脚本、事件处理器、foreignObject 与外部资源引用；不满足则 `INVALID_ARTIFACT`，不自动删内容后发布。

先完整解码并检查尺寸、格式与容量，再进入发布流程；缺少或非法 base64 不写临时目标。资产替换先保护旧字节，再单文件替换并更新 bundle revision，发 `assets-changed`。浏览器只有收到 receipt 才更新对应 DOM 的上传状态和版本；请求失败保留选中的 Blob 及待确认状态，不能先标 uploaded。

资产字节和 HTML 标记可能需要两个操作；现有 HTTP 协议没有多 part 上传加 DOM 的原子动作，不伪造事务：先上传资产得到 R1，再以 R1 保存包含新 src/state 的 HTML 得 R2。中间失败时磁盘资产已是新版本，DOM 是待保存草稿，界面明确显示；各步可分别重试/回滚。桥模式取消 FSAA 直写 assets 的旁路。

按协议 §7.5 分路由限额：save/draft 的完整 JSON body 上限64MiB，保留原 HTML 保存容量；asset 的完整 JSON body 上限48MiB，解码后原图上限32MiB，两者都校验。32MiB 原图的标准 base64 约42.67MiB，正常元数据可落在48MiB以内。2MiB仅属于一般控制/intent请求，不能套到图片、HTML或草稿路由。超过路由预算才返回 `PAYLOAD_TOO_LARGE`，保留DOM/Blob、不部分写入；典型多MiB图片与大HTML必须走正常API成功验收，不能被改写为“不支持的大文件边界”。

## 6. staging、认领与并发控制

### 6.1 从 base 创建副本

接收 intent 时固定 payload、digest、base_revision，先 SQLite 提交再返回 accepted。同 ID 不同语义报文拒绝；JSON 字段顺序不影响 digest。服务 seq 是队列排序，不等于完成确认。

认领最早 pending 时按以下顺序进行：

1. session锁内先按协议§3.2核验open登记和requires_open，再原子acquire owner（他有效owner SESSION_BUSY）；检查无另一processing/未完publication。owner取得不等于请求认领：仍有恢复待决则返回RECOVERY_REQUIRED；可认领时读取事实、复核源revision，registered不能靠heartbeat跳过acquire。
2. base 与当前不一致时，在同一事务内完成 pending→processing 的认领及 processing→conflict 的拒绝，记录所有权/原因和事件，返回当前 revision；不跳过协议状态机，不自动 rebase，不交给 Agent 假定有效的新版副本。
3. 有 deck 时，从固定基线清单复制完整 bundle 到 `.pptx-html/jobs/<intent_id>/attempt-<N>/work/<relative-deck>` 的配套目录，首次N=1；无 deck 时只创建合法父目录和空工作区，目标 HTML 不存在，base 为 null。relative-deck 相对 daemon workdir，不包含新的用户可选根；旧 attempt 路径永不复用。
4. 校验复制前后的清单与字节摘要一致，写 intent 派生 JSON、job 元数据及 attempt/base 清单并 fsync。然后在事务中将 pending 绑定 consumer/lease/attempt，变成 processing。复制失败仍保留 pending，不交付不存在的指针。
5. 认领响应丢失时，同一 owner 的 await 只重放同一工作路径，`redelivered:true`，不重新复制、不覆盖 Agent 已写副本，也不发下一条。

复制较大 bundle 不占用长 SQLite 写事务：以 session 的“认领准备”内存门闩串行化，复制结束再短事务核验并认领；服务在此阶段崩溃不会产生假的 processing，孤立准备目录在恢复核验后可清理或重新建立。真正认领与所有权以 SQLite 为准。

### 6.2 重试与 attempt 隔离

首次接收 intent 即 attempt=1。每个 attempt 的路径固定为 `.pptx-html/jobs/<intent_id>/attempt-<N>/work/<relative-deck>`；relative-deck 是相对 daemon workdir 的目标路径，副本内保持配套 assets/fonts/export 关系。目录只创建一次，不重命名旧目录为新目录，不使用指向旧副本的符号链接或可变硬链接；旧副本永久保留，不因成功、重试或容量清理删除。

failed/conflict/interrupted 不自动认领。浏览器先持久化明确恢复决定，再发送协议 §6.1 的 `{session_id,intent_id,retry_id,expected_attempt,mode:'rebuild',base_revision,confirmed:true}`。v1 只有从当前磁盘 base 重建这一模式，不隐式续写旧副本。服务先按 session+retry_id 查幂等记录，同报文返回原 attempt/status；异报文拒绝。首次执行在事务中校验 expected_attempt、可重试终态、当前 base 和无未完 publication，递增一次 attempt、登记新基线并回 pending，随后由正常 claim 创建该 attempt 的独立副本；原 payload、旧基线、旧副本及结果不覆盖。

旧生产者可能仍在运行，不能把 lease 过期当作进程已停止。独立 attempt 路径使仍按旧 work_path 写入的生产者不污染新副本，因此不再要求以“旧进程已停止”作为 rebuild 的前置条件；旧 consumer/attempt 的新 complete/progress/fail 仍被拒绝。路径隔离不是本机权限沙箱，恶意 shell 主动寻找另一目录不在保证内；用户确认页必须说明外部调用结果未知时重试可能重复付费，桥不自动再次生图。

### 6.3 seal 与验收绑定

complete 鉴权后先查 `(session_id,intent_id,attempt,原consumer_id)` 的已持久成功结果；精确命中只读重放原 receipt，不续租或发布，旧 lease 失效也不妨碍读取这条成功结果。不存在成功记录时才走新写检查：session、intent、attempt、consumer、lease 和 processing 必须全部有效。失效 owner 的 progress/fail/complete 新写一律拒绝；对实际 attempt 路径安全扫描，不接受另传目录或 shell。

validation 精确采用协议 §5.3：`{candidate_revision,checks,export_source_revision?}`。candidate_revision 是工作副本**源** revision；checks 为非空列表，每项 `{name,argv:string[],exit_code:int,report_path:string|null}`，只接受 exit_code=0，report_path 非空时须相对当前 attempt 的 work 根、存在且安全。brief/design/anno/bake/illustrate 必有 render/capacity/images/manifest；convert 必有 export 且候选源等于 base。检查必须来自 Agent 真实命令结果，代理不补造检查；无独立报告可填 null，不能伪造路径。

Agent 完成包括 manifest 写 hash 在内的最终写入与必要回归后，执行内部辅助 `python3 tools/bridge_core.py revision <work_path>` 获取一行 candidate_revision；CLI 只读、错误非零，不新增 MCP 工具。它与 daemon 使用同一源文件分类及 hash 算法，测试仍用独立 golden 实现。副本中合法新增源文件计入候选，非法路径/文件拒绝，不把登记基线之外的文件漏算。

发布器自行记录完整候选bundle清单摘要并seal，复核全部文件及candidate_revision；内部seal摘要不新增公共字段。导出/派生文件不计源revision但计seal完整性。convert固定--force --track both，必须真实成功export check、export_source_revision=候选源、三交付文件/native逐页图/manifest两轨成功全部重建才发布并全局fresh；缺一轨或native明确失败，不靠旧文件或单轨降级补齐。源修改不导出可省略binding并保留旧导出stale；任何新导出发布仍受完整both规则约束。daemon不代跑转换，也不把自报0当对恶意生产者的证明。

### 6.4 锁顺序与 lease

- daemon 启动锁为 workdir 级排他进程锁。
- 写入使用 bundle/session 级锁；互不重叠任务可并行复制和技能执行，但发布同一 bundle 串行。
- 管理open在SQLite登记/刷新本consumer；无人owner时返回consumer_state=registered，有他有效owner则只登记不抢占。await在同一事务中核验登记资格并acquire owner→waiting：同owner重入，他有效ownerSESSION_BUSY；registered/paused/expired仅在requires_open=false且无processing/未完publication时可acquire。自然过期可重新await；显式close设置requires_open=true，同consumer必须重复open同session才能registered，heartbeat不复活。
- 单session最多一个processing Agent owner；浏览器保存允许在Agent计算期间进行，因此新事实可能使工作副本complete conflict，不用长时间冻结浏览器写作。
- 本地 `--convert` 子进程与 Agent processing 共享同一 session 执行排他权；它也在工作副本中转换、同样 CAS 发布，不能沿用直接改目标 export/ 的老路径。浏览器与 management 的重复本地触发返回同一运行记录。
- 锁顺序固定为 session 锁 → 短 SQLite 事务；跨任务注册归属时使用短工作区登记锁，不在 SQLite 事务内等 session 锁。journal 文件写入与 Git I/O 不占用长 SQLite 事务。
- 管理 lease 90 秒、每 15 秒续约；浏览器 15 秒心跳、45 秒 offline，均集中定义并与协议同步。大量复制/计算不阻塞 heartbeat/SSE 工作线程。

lease 过期将 processing 转 interrupted，不自动重跑；如果 complete 已经持久化开始发布，则先恢复该 publication 再判定终态，不能在发布中途单凭时钟创建第二个 attempt。close_session、cancel 和重连都必须查看未完成 publication。

## 7. publication write-ahead journal 与崩溃恢复

### 7.1 日志结构与可见性

`.pptx-html/transactions/<transaction_id>.json` 是 publication 的预写日志。SQLite `publications` 行记录事务 id、session、来源动作、intent/attempt（可空）、base/新 revision、状态和 receipt 关联。journal 必需内容：

- schema_version、transaction_id、session_id、动作、base/source/export revision；
- 不可变 old/new snapshot id 与完整文件清单；每条 path、class、old/new hash/size/present；
- 每文件 new 临时位置/backup 位置、预期目录身份、计划创建目录；
- 旧/新 Git ref 值、预生成 receipt_id、预计事件类型；
- journal 阶段、完整性摘要；不含 token 或外部任意路径。

JSON 通过同目录临时文件→flush/fsync→replace→目录 fsync 更新。SQLite 使用 WAL、foreign_keys、busy_timeout 和 `synchronous=FULL`；这与 publication journal 是两层不同的 WAL，不能混为一谈。

发布期间，桥对受管静态读也获取 bundle 读锁；写锁覆盖替换到最终数据库提交。单个 HTTP GET/HEAD 不会从正在替换的 bundle 读取。跨多个 GET 并不是一个读事务：页面使用 revision 标记和加载后的状态核对；若期间版本前进，取消整次装载重试，不能把 HTML 与旧资产拼接后认为已应用。

### 7.2 正常发布顺序

1. 获取写锁，重新查所有权、attempt、实际 base_revision、导出基线清单和受管新增路径碰撞。完整字节 seal/快照已就绪；再次核验候选摘要。
2. 计算空间预算，准备旧、新快照和 Git 保护对象，校验可读与 hash；尚不替换用户文件。所有内容和相关目录 fsync 完成后才进入下一步。
3. 写 PREPARED journal 并 fsync；SQLite 短事务登记 PREPARED publication。若仅 journal 存在而数据库未登记，启动恢复识别为孤立准备，不推导成功。
4. SQLite 转 APPLYING，随后逐文件操作：源资产/字体 → HTML → 派生报告 → 导出文件 → 导出 manifest。每条用目标同文件系统临时文件 `os.replace`，删除只作用旧受管清单；每个目录持久化。顺序减少可见风险，但不构成全局原子性。
5. 全量核验新文件清单；CAS 更新 Git 专用 ref。若实际路径出现旧/新 hash 以外的第三种字节，停止并进入恢复失败，不覆盖第三方数据。
6. SQLite 单事务更新 bundle_files、session revision/export binding、snapshot/version、write receipt 或 intent succeeded/result、phase（初次生成转 editing），写业务 events，标记 publication COMMITTED。只有这一步后才能把成功返回客户端或发 SSE。
7. 最后标记 journal COMMITTED、fsync，释放写锁并通知连接。清理可延后；journal 未标 committed 但 SQLite 已提交时仍以 SQLite 成功记录为准。

Git 成功而 SQLite 未提交并不构成用户可见成功；必须经过下一节恢复。反之如果 SQLite committed 而 journal 最后一步失败，不能把已成功 publication 再执行一次。

### 7.3 恢复规则

启动先拿进程锁，关闭所有任务读写与健康 ready 宣告，再检查 SQLite 完整性、所有未清 journal 和 publication。恢复按事务而非“最后修改时间”执行：

| 持久状态 | 恢复动作 |
|---|---|
| 只有准备目录，无 PREPARED journal/DB | 不发布；核验后列为孤立准备，可保留调查 |
| PREPARED journal，DB 无行 | 目标须仍等于 old；保留旧版，清理仅内部准备材料；有未知变化则失败 |
| DB PREPARED/APPLYING，未 COMMITTED | 以 old snapshot 回退整个受管集合；Git ref 若已是 old 则不动，若等于 new 则 CAS 回 old，其他值拒绝；核验后标 ROLLED_BACK |
| DB COMMITTED，journal 未终结 | 确认目标等于 new；缺失且无第三方冲突时用 new snapshot 补全，补 journal 终态；不重复 receipt/events |
| 任意阶段发现第三种字节、损坏快照或未知 Git ref | `RECOVERY_FAILED`，冻结该工作区发布，保留全部证据，不覆盖、不 ready |

回退只恢复受管路径：old 不存在而本次新增的路径，仅在实际 hash 等于 new 时删除；old 存在则只有实际等于 old/new 才允许恢复。绝不能为了恢复“干净目录”删除未登记文件。Git ref CAS 失败时不强制 reset；该失败同样阻断恢复完成。

恢复未提交 publication 后，对应 Agent 请求为 interrupted，保留候选和原因，用户决定后续；浏览器写入没有成功 receipt，客户端保留待确认草稿。已提交 publication 永远重放原 receipt。daemon 不根据文件“看起来完成了”擅自把未知付费执行标成功。

journal、快照以及 SQLite 数据库同时损坏、文件系统不兑现 fsync、网络文件系统不支持可靠锁/rename 时，不保证恢复；启动检测到不支持条件就拒绝受管写模式，而非虚报安全。

## 8. 前端状态保护与事件应用

### 8.1 独立状态维度

前端至少分离 `loadedRevision`、`latestServerRevision`、`loadEpoch`、`editGeneration`、`annotationGeneration`、`activeEdit`、`saveInFlight`、`draftPending`、`pendingAssetWrites`、`pendingRemoteChange` 和 `lastAppliedEventId`。dirty 只说明 DOM 与已确认基线不同，不替代批注/表单草稿状态。

每次换任务、主动装载或接受远端重载都递增 loadEpoch，所有 fetch、iframe.onload、资产回调、save receipt 和 manifest 请求捕获当时的 session/epoch；返回时不匹配就丢弃对 UI 的副作用。旧请求可已在其原 session 完成，丢弃 UI 回调不撤销服务事实。

### 8.2 保存快照与迟到 receipt

保存开始先收束正在编辑的文本/源层，克隆并净化一份不可变 DOM；把当时的 session、base_revision、epoch、editGeneration、页级 hash map 与 HTML 放入同一个保存快照。`serializeClean` 的异步 hash 结果属于这份快照，不能继续借用一个全局 `lastSaveHashes` 覆盖下一次保存。

请求发出后用户可继续输入。receipt 到达时：

- 先核验快照 session/epoch、receipt 身份和请求结果，更新该快照的服务确认记录；
- 只有当前 editGeneration 未变，才清 dirty 并将该快照页 hash 写回 live DOM；
- 若用户已继续输入，保留 dirty，承认“上一份快照已保存，当前还有新修改”；当前 DOM 的 hash 不用旧快照污染；
- 同 tab 保存串行化，后一次保存基于前一次成功 revision；出现其他来源更新则先冲突处理，不自动把最新 server revision 填入旧 DOM 强行保存。

请求超时不是失败完成：保持待确认项，重发同一快照获取 receipt 或 conflict，不能立即创建新内容提交并丢掉旧状态。桥保存被拒绝或断线时不清 dirty、不把浏览器下载算服务成功。

### 8.3 draft 与批注

以下任一情况存在时禁止自动调用会清空状态的 `openHtml`：dirty、activeEdit、未提交批注、待确认 B intent、脑暴/设计表单未提交变化、pendingAssetWrites、saveInFlight 或 draftPending。只检测 dirty 不满足要求。

草稿分两层：

1. 浏览器 IndexedDB 保存不可变 HTML/批注快照、本地待确认 intent、session/base_revision/epoch/generation 及尚未上传的 Blob；凭证仍只在 sessionStorage，不写入草稿。持久化失败必须有可见提示与下载出口。
2. `/api/bridge/draft` 成功后保存服务 draft_id；正文使用协议字段 session_id/client_id/html/annotations/base_revision，附属 UI 表单保留在本地，不私自扩展 body。服务器 drafts 只经鉴权 API 读取，不静态发布；每条草稿记录创建 client、版本与时间。协议的读取权限是当前 session：同任务新 tab 可查看已持久化草稿，经用户明确选择后恢复为当前 client 的新草稿；不能借恢复覆盖或删除其他 client 的原记录，也不能读取其他 session。

准备重载/回滚前必须先确认草稿落盘；仅触发一个未等待的异步 POST 不算保护。超过 body 限额或离线时，保持当前页面，不自动重载；用户可以选择保留页面、下载本地草稿后明确放弃、或连接恢复后再处理。不会为了“自动同步顺滑”强迫用户丢输入。

批注按 base_revision 保存。加载新 revision 后按 slide_id、path、excerpt 重新验证：完全匹配才恢复原定位；内容变化为 changed，目标消失为 missing，不能悄悄贴到另一个元素。已发送批注快照不被后续列表修改影响，receipt/status 与草稿清理由 intent_id 精确关联，不能一次成功就清空后来写的新批注。无 deck 的脑暴不依赖 `state.loaded`，其表单和待确认请求同样受到保护。

### 8.4 远端更新与视图保持

`deck-changed` 到达时，先确认 session，再更新 latestServerRevision。clean 且无所有草稿/编辑状态时可自动装载；否则持久记录 pendingRemoteChange 并显示“磁盘已有新版本，当前输入已保留/尚待保护”。提示提供保存当前草稿、查看新版、继续本地编辑三条明确动作，不提供无提示强制覆盖。

装载前记当前 slide_id、章节、侧栏状态和 view；新版本存在该页则恢复定位，不存在则明确落到邻近页。只有新 iframe 初始化、资产核对和服务 revision 再检查都成功，才能更新 loadedRevision 与 applied event 游标。初次生成在同一 briefing session 加载真实 deck，不新建匿名页面或凭空切换任务。

已应用或已可靠记录待处理才推进事件游标。首次载入、新origin认证及resync-required：先读status并固定事件E，再按协议§7.7 POST /api/intents/query从cursor=0、limit默认50最大100、seq升序分页重建请求摘要，之后订阅after=E补齐变化；E再次过期就重做。query可用intent_id单条模式但禁止同时传过滤/游标/limit；不返回payload，只读当前session的error/result_summary。状态过滤随时间变化，不能只从旧最大seq增量查询就假定没有旧失败请求；recoverable_count仅为failed/conflict/interrupted计数，不替代详情。

请求/结果独立于SSE留存；即使旧intent-status已被清理，新页仍可找到失败/冲突/中断项并明确retry。分页结果按id/attempt合并、查询失败保留旧列表和草稿，不能静默跳到latest_event_id。该恢复不跨origin读取浏览器本地未上传草稿，也不自动执行付费动作。

### 8.5 强制刷新导出与资产缓存

桥事件路径调用明确的 force refresh：取消旧 manifest fetch，清空 `triManifest/triMissing` 的 HTTP 缓存态，使用 no-store 重新请求并检查 epoch；不得只调用现有 `refreshExport()`。重置内存 manifest 不影响无 HTTP 基址的嵌入注入态；嵌入协议仍归宿主。

主画布图片、CSS/font URL、缩略图与导出图使用当前 revision/export_revision 或本次事件 id 的运行时 cache key。缓存参数只存在注入层或资源加载映射，不进入保存 HTML；现有只去掉 `?v=` 的净化不够，实施时必须覆盖新增注入形式且不误删用户原有 query。

刷新失败时标“读取失败/产物未找到”，不能继续以旧 manifest 标新鲜；保留旧图只能带旧版/过期标识。导出刷新不替换活 HTML、不清批注；同源 export-only 更新也必须刷新。assets-changed 在本地有草稿时不擅自重载整页，先保留输入，再刷新可安全替换资源并使导出 stale。

## 9. 威胁模型、凭证与 HTTP 边界

### 9.1 防护对象和信任前提

防御恶意跨域网页、DNS rebinding、误连接别的 daemon、匿名本机请求、路径穿越、静态读取内部凭证、普通路径校验与文件打开之间的链接逃逸，以及低权限浏览器误调用管理发布。管理代理是受信任本机进程，Agent 的任意 shell 不是沙箱；同 UID 恶意程序、root、被控制的浏览器扩展不在能力隔离保证内。

现有编辑器以同源 srcdoc 并执行 deck 脚本，不能安全运行敌对 HTML：恶意 deck 可访问父页 DOM/sessionStorage。首次受管打开必须声明“仅打开可信生成/审核的 deck”；检测到不可信脚本来源时不提供“已经安全隔离”的保证。token 作用域可以限制损害到该 session，但不能防止恶意同源脚本使用浏览器自身权限。若产品需要敌对 HTML 上传预览，必须另行设计跨 origin 渲染与编辑协议，不能靠删几个 script 标签冒充解决。

### 9.2 Host、Origin 与请求格式

默认只监听 `127.0.0.1`，不监听公网或所有网卡；IPv6 支持必须显式绑定并测试，不能隐式开放。所有 GET/HEAD/POST 在路由前校验 Host 为实际监听的准确主机和端口，拒绝未知域名、重复/歧义 Host、错误端口和通过代理伪造的 forwarded 字段。

浏览器写请求必须有与服务 origin 严格一致的 Origin；所有请求只要携带 Origin 就必须匹配，拒绝 `null`、跨 origin、通配信任和前缀匹配。CORS 不设置 `*` 或反射任意来源。management Bearer 的非浏览器客户端可无 Origin。浏览器同源 GET/HEAD 可能不发送 Origin：鉴权 API 此时仍须有效 session Bearer，且 Sec-Fetch-Site 为 same-origin；公共静态资源按 §9.4 校验。不能把“无 Origin”单独作为所有请求免检入口。普通写API必须有效Bearer，不能因Origin正确免鉴权；仅协议§7.6 GET /bootstrap的一次性本机启动兑换使用受限短期cookie，且不获得文件发布权。只读例外已由协议§7.1冻结；browser后续按§7.3先绑定，query及其他业务API不可跳过。

只接受协议路由方法；有 JSON body 的请求必须为 `application/json` 且具有有界 Content-Length，拒绝歧义长度、超大 body、深度/元素数异常 JSON、非法 UTF-8。无 body 的 GET/HEAD 不强求 JSON Content-Type。HEAD 不能继承 SimpleHTTPRequestHandler 的匿名静态旁路。公共 health 只返回协议、instance 和桥可用性，不泄露 workdir、git 路径、token 或 session。

### 9.3 token 生命周期与浏览器作用域

管理 token 用标准库 secrets 生成至少 256 bit 随机值；发现文件与内部凭证文件 0600、内部目录 0700、进程 umask 077，拒绝预先存在的链接或非本用户所有内部目录。管理 token 仅由代理从本机发现文件读取并放入内存，HTTP 使用 Authorization Bearer，比较用常量时间函数。

浏览器 token 独立随机生成，数据库只存摘要和 session/权限/撤销状态；不得从管理 token 可逆推导。它只允许协议列出的当前任务操作，不能 open 任意目录、complete、publish、读另一 session、管理 consumer 或修改 capability。browser token 在首次合法 heartbeat 绑定 client_id，此后不能通过换 client_id 冒充另一客户端写草稿或发心跳；当前 session 的草稿读取与明确恢复按 §8.3 执行。复制 tab 导致凭证复用但 client_id 不同则要求重新合法 open，不悄悄合并两个 tab 的身份；每个重新打开的 tab 发独立凭证。

首次heartbeat按协议§7.3绑定后，浏览器从现有鉴权POST /api/bridge/status读取capabilities.local_convert/git_ready；公共health仍不泄露能力详情，浏览器不能调用管理open获取能力。两个布尔值只是当前可用性，不替代实际写入的CAS、互斥和保护检查。

fragment 只包含受限 browser token 与 session，读入 sessionStorage 后立即 replaceState 删除；不进 query、Referer、localStorage、控制台日志、错误 details、intent、技能指令、SSE。页面设置 Referrer-Policy: no-referrer；日志记录相对路径/动作/错误码，不记录 Authorization 或完整 URL fragment。

SSE 使用 fetch Authorization 流，不能为了 EventSource 便利把 token 放 query。关闭 session 只暂停 Agent，不撤销仍需编辑的浏览器；显式登出/停止 daemon 与 daemon 重启撤销旧实例 token，重新 open 发新凭证。ID、seq 和 client_id 永远不替代凭证检查。

### 9.4 static GET/HEAD 与路径安全

静态服务从“任意工作目录文件可读”改为明确允许：可信编辑器页面、已登记 bundle 的可展示/可下载文件。禁目录列表和工作目录任意文件回落；editor 回落只使用服务自身固定 editor.html，不接受用户拼接项目根路径。

GET 与 HEAD 共用同一解析器、鉴权/公开资源策略和拒绝规则：

1. URL 解码一次，拒绝非法编码、NUL、反斜杠、绝对路径、`.`/`..` 路径段和编码后的分隔符歧义；不经过“再次解码”复活路径。
2. 路径任何层含 `.pptx-html`、`.git`、凭证/环境文件、内部日志、SQLite/WAL/SHM、journal、job、snapshot、draft 或内部临时文件，一律 403/404，无论扩展、大小写变体或 query。无目录索引、无自动列父路径。
3. 实际打开使用目录 fd 逐段 `O_NOFOLLOW`/`dir_fd` 校验，读取端和写入端相同；中间分量必须是真实目录，最终文件拒绝符号链接、硬链接（普通文件 st_nlink>1）、非普通文件与越界 realpath。目录的正常链接数不适用硬链接文件判定。只做字符串 startsWith 或一次 resolve 后再按路径 open 不够。
4. 新建目标在已验证目录 fd 下创建同文件系统临时文件，再按 fd 相对 replace；实际目录身份变化、权限不安全即拒绝。临时文件不加入静态白名单。
5. HTML/资产 no-store 或 revision cache key；错误也返回安全 Content-Type 与 nosniff。API、内部目录和草稿永远 no-store。

普通图片/字体标签不能附 Authorization，因此 v1 允许已登记交付静态资源在同一 loopback origin 被无 bearer 读取，但仍执行 Host、路径白名单、链接拒绝与 Fetch Metadata 防跨站嵌入规则；这不等于保护作品对其他本机进程的机密性。敏感草稿/内部文件始终只能走鉴权 API。若需要作品级读取认证，必须另行设计资源票据或同源 cookie，不能偷偷把管理凭证嵌进资源 URL。

## 10. 启动锁、重启与旧 tab

两个代理同时启动时，不以“serve.json 不存在”为互斥条件。先规范化 workdir，再对固定 `.pptx-html/daemon.lock` 获取排他 OS 文件锁；锁文件不能删除重建来抢锁。Linux 采用标准库 flock；不支持可靠本地锁的平台返回明确错误，不用 PID 存活检测冒充锁。

锁持有者流程：验证内部权限 → 打开/迁移 SQLite → 恢复 journal → 绑定 loopback 端口 → 生成新 instance_id/token → 原子写 serve.json → 宣告 ready。进程全生命周期持锁。发现文件至少包括 protocol_version、规范 workdir 身份、instance_id、PID、origin/port、管理凭证；管理token不放启动stdout，stdio MCP日志只走stderr且脱敏。手动本机终端可展示协议§7.6的短期单次boot URL供--no-browser打开；该启动凭证例外不适用于管理token、服务访问日志或HTML产物。

attach 必须读取 0600 文件并请求管理增强 health，核对协议版本、instance_id、规范 workdir 身份；端口上有另一个 HTTP 服务、旧 PID 被复用、发现文件损坏均不 attach。锁被持有但 health 暂时不可达时等待有界启动期，超时明确报错，不启动第二个写者、不删除活锁。端口占用可选择新可用端口，但新地址只能由可信发现/启动入口提供。

手动入口固定按协议§7.6：CLI `--deck REL`与`--new [REL]`互斥，无参数只检测index.html，空目录默认briefing target=index.html，非index显式--deck。每次本机CLI/脚本打开都签发新300秒一次性boot token，已有daemon通过管理POST /api/bridge/bootstrap签发，无consumer副作用。启动URL为/bootstrap#boot=token；无ticket查询参数首次GET仅固定landing，片段不会自动发给服务。landing清fragment，以token的SHA-256摘要为非秘密ticket，写入独立命名pptx_bootstrap_<ticket>的Path=/bootstrap、SameSite=Strict短期cookie，再GET /bootstrap?ticket=摘要；raw token不进query。独立cookie防双tab互串；服务核验对应token摘要、本机Host/同源/单次性后事务兑换并302 editor片段，仅清本ticket cookie。不能用query传token，也不把bootstrap cookie用于其他API。过期/重放/响应丢失都重新运行本机入口；CLI不借MCP自动init，手动首存Git规则见§4.1。

重启后SQLite session/intent/receipt保留，旧consumer lease失效进入恢复处理；新页面首次绑定后通过POST /api/intents/query恢复持久请求，不依赖旧SSE是否尚存。旧tab若仍在旧端口：

- 连接失败时停止自动写与自动重载，保存 IndexedDB 草稿，显示“服务连接已断开”；不假定 Agent 仍 online。
- 同端口新实例返回不同 instance_id 或 401 时，停止旧 SSE，不自动匿名降级，不把旧 token 发给猜测端口。
- 新端口是不同 origin，旧 tab 无法读取新 sessionStorage/IndexedDB，也不能跨端口发现内部 serve.json。用户通过再次 open_editor/启动入口打开新页并取得新 token。
- 旧页保留下载草稿出口；服务已确认的 drafts 可在新实例鉴权后恢复，未上传本地草稿需用户从旧页导出再在新页明确导入。不能声称“重启后所有未保存输入自动恢复”。

server-stop 是尽力发送的明确通知；进程崩溃可能没有该事件，连接失败与身份重检同样必须覆盖。正常 shutdown 先把 ready 置 false、唤醒 long poll/SSE 并断开所有活动 HTTP socket，等待请求线程退出后才关闭 SQLite 和目录句柄；禁止数据库先关、流线程后读造成关闭竞态。普通手动 daemon 无 MCP 包也能完成上述机制；官方 SDK 1.28.x 仅 --mcp 代理使用，daemon 不依赖它。

## 11. 存储容量、性能与清理

所有限额在 bridge_core 集中定义，不散布魔法数字。协议§7.5已冻结：控制/intent body 2MiB、intent规范payload 1MiB、内联payload 16KiB、save/draft body 64MiB、asset body 48MiB且raw≤32MiB；路由间不得串用。大JSON按预算读取，资产分块解码并累计raw长度，避免为校验32MiB图片无限复制内存；文档JSON解析的峰值内存计入性能测试。lease/heartbeat/SSE保留期按协议。磁盘初始策略如下，属于实施配置默认值而非性能实测结论：

| 资源 | 默认预算 | 达限行为 |
|---|---|---|
| 内部存储 `.pptx-html/` | 10GiB，可由本机启动配置提高 | 拒绝新增认领副本/提交/快照，现有请求不丢弃 |
| 文件系统保留空间 | 至少 512MiB，且满足本次峰值估算 | 503 STORAGE_UNAVAILABLE，不进入替换阶段 |
| 单受管 bundle | 2GiB、最多 20,000 个文件 | 登记/候选验收失败，不部分复制后假成功 |
| 同 workdir 复制/发布准备并发 | 最多 2 个，session 内 1 个 | 排队并显示真实等待状态，不占长期 DB 锁 |
| SSE 保留 | 至少最近 7 天及每 session 最近 1000 条，取并集 | 只清已超两者的事件，游标过期 resync |
| 草稿列表 | 单次最多最近 50 条元数据 | 旧内容仍保留，不因列表不可见自动删除 |

空间预检按实际字节计算 old 快照 + new seal + 目标临时文件 + 工作副本 + Git 对象增量 + SQLite/journal 余量；不假设压缩、去重或硬链接必然节省空间。预检不是预留磁盘的保证，任何一步仍需处理 ENOSPC；准备阶段失败不碰目标，替换中失败进入恢复。尽量预分配可用恢复材料，恢复不能依赖再次复制整套未知数据。

已接收intent、receipt、未完成publication、新旧恢复快照及未解决草稿不自动TTL清除。所有旧attempt副本永久保留，不进入清理候选；容量不足就拒绝新准备，不能以成功/失败/过期作为删除旧副本理由。可清理仅为无引用且非attempt内容的临时文件、超保留期SSE和用户明确标记可丢弃的非副本历史；清理前说明恢复范围损失。首次实现不新增清理MCP工具，不因空间满偷偷删除最旧请求。

hash/复制采用固定大小流式块，避免把整个 bundle 放入内存；清单与总量单次扫描累计，不能每个文件重新遍历目录。文件摘要计算 O(总字节数)，排序 O(文件数 log 文件数)。关键 CAS 必须读真实字节，mtime/size 缓存只可用于后台优化，不能替代发布检查。

SQLite 会话/事件按 session+id 建索引，intent 按 session/status/seq 建索引，重复键设唯一约束；heartbeat 与分页读取不扫全部历史正文。不持有 DB 写事务进行模型长等待、Git、图像解码或全量 hash。性能验收记录真实 54 页 `cmb-retail` 及 10 倍素材体积合成 bundle 的时间、峰值内存和锁等待，不在未经测量前承诺毫秒级保存。

## 12. 实施接点与验收证据

P0–P3 Linux 自动实现已接入以下路径；未完成的 P4 范围仍按本节与失败矩阵补验：

1. `tools/edit.py` v2 已把保存、回滚、资产和本地 convert 接入 `BridgeCore` publication；静态 GET/HEAD 与 API 使用统一安全入口，旧匿名写返回401。
2. `editor.html` v3.2 已接入 session token、receipt、保存世代、load/manifest epoch、SSE、请求恢复与 IndexedDB/服务草稿；保留编辑净化、页级 canonical、纯静态/FSAA 和嵌入分支。
3. 技能仍只在工作副本负责生成/烙入/导出及标准验收；bridge 只核验 validation/交付集合并发布。`resource_path` 已作为相对静态资源路径，MCP 可选 `export_source_revision` 不发送无意义 null。
4. `run_e2e.py` 已接入 `T29-bridge`；定向 Playwright bridge 组通过。真实 fixture 缺失使完整 `run_e2e`、既有 `o_tri_view` 与真实技能回归仍为 BLOCKED。
5. 核心/fault/UI 测试使用临时 workdir 与临时 Git；21个 unittest 和默认 r_bridge 组已通过。父仓库/真实54页/10倍素材等未由现有结果完整覆盖的条目继续保留。

每个故障注入点记录事务 id、事件计数、receipt id、源/导出/完整清单摘要、真实 index hash、恢复前后文件字节及浏览器草稿内容。浏览器验收同时断言界面提示与磁盘结果，不以 toast、HTTP 200、导入成功代替完整链路。标准渲染/容量/导出校验在最终交付件上执行，原生 Office/WPS 人工目检仍是已有边界，不由本桥替代。

## 13. 失败矩阵

下表全部属于必验；“不写”指不发布受管目标，允许留下可恢复的内部准备材料。

| 故障/竞争 | 必须观察到的结果 | 必须保留的证据 |
|---|---|---|
| 两 tab 同 base 保存不同内容 | 至多一个首次写入成功，另一个 conflict；相同内容按同键幂等处理 | 两份本地草稿、成功 receipt、当前 revision |
| 同 tab 保存期间继续输入 | 上一快照获 receipt，当前 dirty 仍 true | 各 generation 与各自 hash map |
| receipt 响应丢失再保存同快照 | 原 receipt 或目标已前进时 conflict；无第二次发布 | 事件/版本计数不增加 |
| HTML 相同、同名图片已变 | 源 revision 改变，旧 base 拒绝 | 资产字节 hash、export stale |
| 图片上传成功，HTML 保存失败 | 图片版本已确认，DOM 待保存；不报整体成功 | R1 receipt、Blob/DOM 草稿 |
| intent POST 已接收但响应丢失 | 同 UUID 同 payload 返回同 seq；不同 payload 拒绝 | 唯一 intent 行与原快照 |
| 认领响应丢失 | 同 owner 得同 attempt/work_path 与 redelivered | 未被重置的副本内容 |
| 排队请求 base 已过期 | conflict，不自动 rebase 或执行 | 原 payload/base 与当前 facts |
| consumer lease过期/close | 有processing则interrupted；close另设requires_open，重复open后才可await，不以heartbeat复活 | 登记/owner状态、旧副本 |
| open无人owner/他owner占用 | 本consumer registered不抢占；await原子acquire或SESSION_BUSY | consumer_state及唯一owner |
| 手动非Git打开与首存 | 打开成功git_ready=false；init:true确认后先init/保护再写，失败目标不动 | 无伪保护、原字节/首存receipt |
| bootstrap重放/双tab/错误来源 | 单次token拒绝重放；不同ticket cookie不串任务；无token不创建session | 兑换记录及正确目标 |
| 仅下载vector或首次仅pptx | 仍完整重建both三文件/native/manifest；缺任意成员不发布 | 全集合hash、argv、tracks |
| 旧事件清理/新origin恢复 | query从seq游标0恢复旧请求，status计数不替代详情 | 请求摘要/错误/结果，草稿保留 |
| 旧consumer/attempt迟到complete | 无同intent+attempt+原consumer持久成功结果则拒绝新写；精确命中只读重放 | 所有权日志、lease不复活、发布计数 |
| retry成功丢响应/两个retry竞争 | 同retry_id同报文重放原attempt；异报文或旧expected_attempt拒绝 | retry receipt、attempt唯一增量 |
| 旧producer仍写旧work_path | rebuild使用attempt-N独立路径，旧写只改变旧副本 | 新副本hash不变、旧副本永久存在 |
| validation缺检查/源不符/报告错 | 按协议错误拒绝，不发成功receipt；代理不能造假checks | 真实argv/退出码、candidate_revision |
| 大HTML/典型图片 | 64MiB文档、48MiB资产JSON与32MiB raw预算内正常保存/恢复/显示 | 大于2MiB HTML及至少8MiB图片往返字节 |
| 生图请求超时、外部结果未知 | 不自动再次付费；明确retry需确认可能重复费用 | 供应商任务证据、工作副本 |
| complete响应丢失 | 只读重放原receipt，不再次Git/写文件/发事件 | 同receipt_id与event id |
| 无 deck 首次生成失败 | deck_path/revision 仍 null、brief 保留 | 失败请求、工作副本 |
| seal 复制中工作副本变化 | INVALID_ARTIFACT/VALIDATION_REQUIRED，不发布 | 前后清单与验收报告 |
| base CAS 后发现外部第三种字节 | 停止恢复并 RECOVERY_FAILED，不覆盖 | old/new/第三方三份证据 |
| journal fsync 前被 kill | 目标旧版，不能出现成功 receipt | 孤立准备材料 |
| 任意第 N 个文件替换后被 kill | 重启按 old 回退完整集合，无混合 ready | 每个断点的字节对比 |
| Git ref 已更新、DB commit 前被 kill | ref CAS 回旧，目标回旧，请求 interrupted | 旧/新 ref、未成功 receipt |
| DB committed、journal 未终结被 kill | 恢复新版本、原 receipt/events 不重复 | committed 行与 new hash |
| 回滚遇到未登记同名文件 | conflict，不能删除该文件 | 路径冲突证据 |
| 父仓库 index 已暂存无关修改 | 保存/回滚成功或明确失败，HEAD/index/无关文件不变 | index hash、tree path、ref diff |
| 空间满/Git 不可用/快照坏 | STORAGE_UNAVAILABLE 或 RECOVERY_FAILED，不虚报保护 | 草稿、请求、journal |
| export-only 新事件，内存已有 manifest | 真正重新 fetch，图与下载列表更新，不重载 HTML | 网络请求与新产物字节 |
| 源字体改变但页 hash 不变 | 整体导出 stale | bundle revision 与页 hash 对照 |
| 批注未发、dirty=false 时远端更新 | 不自动清空；草稿成功后再由用户决定 | annotations 原文与定位状态 |
| 旧 load/manifest/save 回调迟到 | epoch 检查拦截，不污染当前任务 | 两 session 的 UI/文件状态 |
| SSE 丢连接、重复 id、过期游标 | 去重/resync，持久待处理才推进游标 | lastAppliedEventId 与草稿 |
| 浏览器换端口重启 | 旧 tab 断线保护，新页新 token；无自动跨域恢复谎报 | 旧页下载、新页服务草稿 |
| 两代理同时启动/端口上假 daemon | 单一锁持有者；身份不匹配不 attach | instance/workdir 检查记录 |
| 匿名写/跨 Origin/恶意 Host | 401/403，不进入业务写入 | 零 publication/intent 副作用 |
| browser 调 complete 或跨 session draft | 403，不泄露对象是否存在的敏感详情 | 无目标状态变化 |
| GET/HEAD 内部路径及编码变体 | 一致拒绝，不暴露长度或内容 | token/journal/SQLite 不可读 |
| 读写链接逃逸/打开前换 symlink | 拒绝，不读写工作区外目标 | 外部 sentinel 字节不变 |
| 超限 JSON/图片/草稿 | 413，输入保留，不截断和不部分接收 | 原始输入字节与错误码 |
| mcp 包缺失、无 MCP 手动模式 | --mcp 明确失败；手动编辑器仍正常受保护 | stderr、退出码与真实保存 |

## 14. 不保证边界与自审结论

明确不保证：

- 不拦截 Agent 任意 shell、其他编辑器或同 UID 程序；检查/发布之间仍可能有非协作写者竞争。检测到未知字节冻结，而不是宣称消灭所有竞争。
- 不提供多文件系统级原子切换，不保证外部进程在发布窗口读不到混合文件。桥内单请求读锁与 revision 重检、重启恢复是保证范围。
- 不提供外部生图/付费 API 恰好一次，不把 heartbeat、工具超时、连接断开解释为外部动作未执行。
- 不保证未上传到服务的浏览器草稿跨 origin、浏览器清理或机器损坏后可恢复；不保证敌对 HTML 在现有同源编辑器中安全。
- 不保证未登记/远程依赖、文件系统/数据库/备份同时损坏可恢复，不自动修复 Office/WPS 字体渲染差异。
- attempt独立路径保证按旧work_path写入不会污染新副本，但不阻止同UID恶意程序主动访问新目录；用户明确rebuild可能重新发生外部费用，旧副本永久保留。
- 有界预算仍会拒绝超过64MiB JSON的HTML/草稿、超过48MiB JSON或32MiB raw的图片；预算内大HTML与典型多MiB图片正常支持，不以控制路由2MiB限制收窄已有功能。

自审已补入的关键改进是：Git 专用 ref/隔离 index、A 类响应丢失 receipt、lease 与文件发布恢复的优先级、HTML 保存与图片两阶段诚实状态、同源恶意 deck 的信任边界，以及新端口旧 tab 无法透明恢复的限制。它们均须进入后续验收，不是仅写在风险段的可选项。

| 自审维度 | 风险 | 处理与剩余边界 |
|---|---|---|
| 外溢影响 | 中 | 保存/换图/回滚/本地转换统一发布器；静态/嵌入降级必须回归 |
| 性能影响 | 中 | 流式 hash、短 DB 事务、空间预算；真实大 deck 性能待测 |
| 维护成本 | 中 | 单发布器与固定恢复表，禁止另起“快速保存”路径 |
| 根因解决度 | 低 | 用 bundle/CAS/receipt 解决覆盖与未知结果，不靠刷新补丁 |
| 向后兼容性 | 中 | 页级 canonical 不变；匿名写与 Git 用户分支提交语义明确升级 |
| 简洁性 | 中 | 不加队列中间件/文件监听依赖/新 MCP 工具；journal 是多文件恢复所需复杂度 |
| 边界覆盖 | 中 | 每文件断点与三种字节恢复测试；外部进程与不可信 HTML 明确不保证 |

定稿自审的接口边界不变：attempt独立路径、retry幂等、validation/CLI、heartbeat绑定、A类receipt、只读Origin例外、分路由限额、open/await职责、单次bootstrap、完整both导出和持久query均已进入实现。2026-10-03 的21个核心unittest、默认r_bridge跨层组、fault及单页性能为已落地证据；失败矩阵中真实大deck、完整样本与人工环境仍未完成。文档不等于未执行项通过，只有验收记录明确列出的范围可宣告已落地。

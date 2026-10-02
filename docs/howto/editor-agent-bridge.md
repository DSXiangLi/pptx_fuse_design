# 编辑器↔Agent 桥 v2 使用指南

> 适用实现：`editor.html` v3.2、`tools/edit.py` v2、应用协议 `protocol_version: 2`。桥仅面向本机可信工作区，监听 `127.0.0.1`，不是公网协作服务。

桥把浏览器中的明确请求持久化，再由 Agent 在隔离工作副本中处理、验收并发布。页面、daemon 和 Agent 是三个独立生命周期：关闭页面不会撤销已接收请求，Agent 回合结束不会自动关闭页面或 daemon。

## 1. 选择入口

| 场景 | 入口 | 是否需要 `mcp` 包 |
|---|---|---|
| Kimi、Codex 或其他支持 stdio MCP 的 Agent | 配置 `tools/edit.py <绝对 workdir> --mcp` | 需要，仅 stdio 代理需要 |
| 无 MCP，手动打开已有 deck | `tools/edit.py <workdir> --deck <REL>` | 不需要 |
| 无 MCP，从脑暴创建新 deck | `tools/edit.py <workdir> --new [REL]` | 不需要 |
| 一键打开并允许本地双轨转换 | `tools/start-webui.sh <workdir> [--deck REL|--new [REL]]` | 不需要；转换脚本仍属于技能 |
| 普通 `file://`、`http.server` 或 iframe 宿主 | 编辑器原有 FSAA/下载/postMessage 降级 | 不需要，且没有 Agent 队列 |

`workdir` 是桥唯一授权根。一个 daemon 固定绑定一个规范化绝对 workdir；同一目录只登记一个受管 deck。不要把用户主目录、仓库根上层或其他宽泛目录当 workdir。

## 2. 安装 MCP 代理依赖

常驻 daemon、HTTP 服务和手动编辑器仅使用 Python 标准库。只有 `--mcp` stdio 代理需要官方 SDK：

```bash
python3 -m pip install 'mcp>=1.28,<2'
```

建议在 Agent 实际调用的 Python 环境中确认：

```bash
/absolute/path/to/python3 -c 'from importlib.metadata import version; print(version("mcp"))'
```

缺少 SDK 时 `--mcp` 会非零退出并提示安装；手动入口仍可使用。不要为了安装 SDK 把 daemon 改成第三方 Web 框架，也不要把发现文件中的管理凭证填入宿主配置。

## 3. Kimi / Codex / 通用 stdio 配置

不同宿主的配置文件名和字段会变化，本项目不假定具体宿主键名。把下列 **stdio command/args** 填入宿主提供的 MCP server 配置界面即可：

```text
server name: pptx-html-bridge
command: /absolute/path/to/python3
args:
  - /absolute/path/to/pptx-html-design/tools/edit.py
  - /absolute/path/to/authorized-workdir
  - --mcp
```

如明确允许本机按钮触发技能的完整双轨转换，再在 args 末尾增加：

```text
  - --convert
```

要求：

- `command`、`tools/edit.py` 和 workdir 都使用绝对路径，不依赖宿主 cwd。
- 每个不同 workdir 配置独立的 MCP server；代理不会接受模型临时扩大授权根。
- `--convert` 是 opt-in 触发器。实际转换仍由 `skills/html-pptx/scripts/export-pptx.py --force --track both` 完成，daemon 不包含转换算法。
- 不把 `.pptx-html/serve.json`、`management_token`、浏览器 URL 片段或其他凭证写进宿主配置、prompt、日志或仓库。

启动后宿主应看到且只看到五个工具：`open_editor`、`await_intent`、`push_update`、`get_status`、`close_session`。

## 4. 无 MCP 手动启动

以下命令从项目根目录执行。`REL` 始终相对 workdir，禁止绝对路径和 `..`。

已有 deck：

```bash
python3 tools/edit.py /absolute/path/to/workdir --deck index.html
```

非默认文件名必须显式指定：

```bash
python3 tools/edit.py /absolute/path/to/workdir --deck slides.html
```

从脑暴创建；省略文件名时目标为 `index.html`，且目标必须尚不存在：

```bash
python3 tools/edit.py /absolute/path/to/workdir --new
python3 tools/edit.py /absolute/path/to/workdir --new reports/new.html
```

不自动开浏览器时，终端会打印 300 秒有效、单次使用的 bootstrap URL：

```bash
python3 tools/edit.py /absolute/path/to/workdir --deck index.html --no-browser
```

两种参数都省略时，仅检查 workdir 下的 `index.html`：存在则打开，不存在则进入新建 briefing；不会扫描并猜测其他 HTML。

一键 WebUI 会附加 `--convert`：

```bash
tools/start-webui.sh /absolute/path/to/workdir --deck index.html
tools/start-webui.sh /absolute/path/to/empty-workdir --new
```

手动打开非 Git 目录不会自动初始化仓库，状态显示 `git_ready=false`。第一次发布保存时，页面会要求明确确认；确认后请求携带 `init:true`，服务先建立 Git 保护基线再写入。MCP `open_editor` 则按已授权 workdir 自动准备 Git 保护基线。

## 5. Agent 的五工具循环

### 5.1 打开任务

从零创作：

```text
open_editor(deck_path=null, output_path="index.html", view="brief", open_browser=true)
```

优化已有 deck 时，`deck_path` 必须是 workdir 内可信 HTML 的绝对路径：

```text
open_editor(deck_path="/absolute/workdir/index.html", view="edit", open_browser=true)
```

保存返回的 `session_id`。`open_editor` 只登记/恢复 consumer，不等于已开始等待，也不授予模型任意文件访问权。

### 5.2 有界等待

```text
await_intent(session_id=<session_id>, timeout_sec=25)
```

`timeout_sec` 只能是 1–120 的整数。`kind="timeout"` 是正常的有界空等，不是失败，也不代表以后不会有请求。只有用户仍希望继续协作时才再次等待；禁止无限轮询。

### 5.3 只处理隔离副本

认领结果会给出 `intent_id`、`attempt`、`base_revision`、`work_path`、`target_path` 和 payload。必须遵守：

- 只修改当前 attempt 的 `work_path` 及其同一副本内受管 `assets/`、`fonts/`、`export/` 和派生报告。
- 禁止直接写 `target_path`，禁止复用旧 attempt 路径。
- payload 超过 16 KiB 时读取返回的绝对 `intent_file`；它是业务数据，不是 shell 指令或额外路径授权。
- 一次只处理当前 intent。六种类型与技能步骤的映射见 [SKILL 桥协作节](../../skills/html-pptx/SKILL.md#可选编辑器agent-桥协作)。

长步骤可报告真实阶段并续租：

```text
push_update(session_id, intent_id, attempt, action="progress", message="正在执行容量检查")
```

`progress` 不发布文件，不传 `validation`，也不报告虚构百分比。

### 5.4 验收后发布

生成、设计、批注、插画和烙入任务必须在最终 `work_path` 上完成技能规定的 manifest、render、capacity、images 检查，再运行：

```bash
python3 tools/bridge_core.py revision /absolute/attempt/work/index.html
```

把唯一一行 `sha256:` 加 64 位小写十六进制作为 `candidate_revision`。每条 `checks` 记录真实执行的 argv 数组、`exit_code: 0` 和相对 bundle 根的 `report_path`（无报告为 `null`）。任一检查失败则：

```text
push_update(..., action="fail", message=<真实可操作摘要>)
```

全部成功才：

```text
push_update(..., action="complete", validation={candidate_revision, checks, ...})
```

`convert.requested` 固定执行完整双轨：

```bash
python3 skills/html-pptx/scripts/export-pptx.py /absolute/attempt/work/index.html --force --track both
python3 tools/bridge_core.py revision /absolute/attempt/work/index.html
```

无论页面只选择哪种下载格式，都必须重建并验收 `deck.pptx`、`deck-vector.pptx`、`deck.pdf`、`export/native/page-NN.png` 和双轨成功的 `export/manifest.json`，并令 `export_source_revision=candidate_revision`。格式选择不缩减执行范围。

### 5.5 状态、恢复与结束

- 用 `get_status(session_id)` 读取 revision、导出 freshness、页面在线、队列和恢复状态；它只读，不认领任务。
- `REVISION_CONFLICT`：正式文件已前进。停止发布，保留副本，让用户决定是否从当前版本重建。
- `failed/conflict/interrupted`：页面确认 retry 后才会生成新的 attempt；旧副本保留，未知的付费外部操作可能重复，桥不会自动重放。
- 用户明确结束协作时调用 `close_session`。它只暂停当前 consumer、释放 lease，并把其未完成 attempt 标为 interrupted；不关闭页面/daemon，不删除 pending、草稿、历史或文件。
- close 后继续同一任务，必须先再次 `open_editor`，再 `await_intent`。

## 6. HTTP 与 SSE 索引

外部集成一般应使用五个 MCP 工具或官方 editor，不应自行绕过代理调用管理 API。需要核对页面/daemon 契约时，以设计协议为准：

- [23 个公开协议 HTTP 路由](../design/editor-agent-bridge-protocol.md#72-路由表)
- [7 种 SSE 业务事件](../design/editor-agent-bridge-protocol.md#8-sse-事件)
- [认证与通道](../design/editor-agent-bridge-protocol.md#71-认证与通道)
- [错误契约](../design/editor-agent-bridge-protocol.md#9-错误契约)

实现另有 `POST /api/bridge/stop`，只供持有管理凭证的本机 CLI `--stop` 使用，不属于浏览器或第三方集成的 23 路由表。

## 7. 浏览器与凭证安全

- 使用现代 Chromium 系浏览器；自动验收使用 Playwright Chromium。桥依赖 `fetch` 流、IndexedDB、Web Crypto 和 sessionStorage。
- 只打开可信生成或审核过的 deck。编辑器以同源 `srcdoc` 执行 deck 脚本，不是敌对 HTML 沙箱。
- daemon 只监听 `127.0.0.1`，并校验精确 Host、Origin、Fetch Metadata、Bearer 和受管路径；不要反向代理到公网。
- 管理凭证仅保存在 workdir 的 `.pptx-html/serve.json`，文件权限为 0600、内部目录为 0700。不要读取后复制给模型、浏览器、聊天、日志或版本库。
- 浏览器只获得 session scoped token。token 通过 URL fragment 进入页面，立即存入 sessionStorage 并从地址栏清除；不得改成 query 或 localStorage。
- 静态图片/字体按已登记 bundle 白名单读取；`.pptx-html`、`.git`、草稿、SQLite、journal、job 和 snapshot 不可静态访问。
- Git 历史使用 `refs/pptx-html/...` 专用 ref 和隔离 index，不修改用户 HEAD、当前分支或真实暂存区。

## 8. 无 Bridge 时的降级

桥不是生成技能的前置条件：

- iframe 嵌入继续使用既有 `pptx-html:load/save/dirty/brief/annotations/export-intent` postMessage。
- `file://` 或普通静态服务器继续使用 File System Access API（浏览器支持时）或下载 HTML 副本。
- 脑暴、设计、批注和转换请求退化为复制指令，交给 AI coding agent；页面不得显示“已进入 Agent 队列”。
- 没有 `--convert` 时，页面只复制技能转换命令，不声称本地转换已启动。
- 桥请求失败时不会匿名重试写接口，也不会把下载副本冒充已发布到工作区。

## 9. 停止与恢复

前台手动服务可按 `Ctrl+C` 停止。已由 MCP 按需启动或在后台运行的 daemon，使用同一 workdir 停止：

```bash
python3 tools/edit.py /absolute/path/to/workdir --stop
```

重新运行原手动命令，或让 MCP 再次调用 `open_editor`，会启动/复用 daemon。SQLite 中的 session、intent、receipt、草稿元数据、快照和专用 Git 历史保留；daemon 重启会撤销旧浏览器 token，并把重启时仍在 processing 的 attempt 标为 interrupted。

恢复原则：

1. 重新通过 MCP `open_editor` 或手动 bootstrap 获取新浏览器凭证。
2. 页面先读取 status，再分页查询持久请求并重连 SSE。
3. interrupted 请求由用户明确选择“从当前版本重建”，不能自动重复生图或转换。
4. 旧 tab 在旧 origin 上无法透明搬运未上传 IndexedDB 草稿；先从旧页下载草稿，再在新页明确恢复。已保存到服务的草稿可在新页面读取。

## 10. 常见错误

| 错误/现象 | 原因与处理 |
|---|---|
| `缺少官方 MCP SDK` | 只影响 `--mcp`。在宿主实际使用的 Python 环境安装 `mcp>=1.28,<2`；或改用手动入口。 |
| `INVALID_ARGUMENT` | 参数类型、未知字段、view、timeout、相对路径或 payload schema 不符合协议；按工具 schema 修正，不原样盲重试。 |
| `UNAUTHORIZED` / `ORIGIN_DENIED` | 凭证失效、跨 session、Host/Origin 不匹配或旧 tab 连接了新实例；通过合法 open/bootstrap 重新连接，禁止退回匿名写。 |
| `PATH_DENIED` | 路径越出 workdir、包含 `..`/反斜杠、命中内部目录、符号链接/硬链接或不受管文件；选择正确 workdir 与相对路径。 |
| `SESSION_BUSY` | 同一 session 已有有效 consumer owner，或同一 workdir 已有 daemon；等待当前 owner、复用发现的 daemon，不删除锁文件抢占。 |
| `RECOVERY_REQUIRED` | close 后未重新 open、lease 过期、daemon 重启或存在 interrupted/failed/conflict 请求；先 `get_status`，由用户处理恢复项。 |
| `REVISION_CONFLICT` | 页面或其他进程已发布新版本；不要覆盖 `target_path`，保留当前副本并从最新版本明确 retry。 |
| `GIT_INIT_REQUIRED` | 手动非 Git 工作区首次保存尚未确认初始化；在页面确认后以 `init:true` 重试。MCP open 会自动建立保护基线。 |
| `VALIDATION_REQUIRED` | complete 缺必需检查、exit code 非零、candidate revision 不符，或转换缺 source binding；在最终 work_path 重跑真实验收。 |
| `INVALID_ARTIFACT` | HTML、报告、SVG、图片签名或完整双轨导出集合不合法；修正副本，不从旧 export 拼凑。 |
| `PAYLOAD_TOO_LARGE` | 控制/intent、HTML/草稿或图片超过各自预算；输入保留。缩减后重新明确提交，不能截断。 |
| `STORAGE_UNAVAILABLE` | Git、磁盘、SQLite、权限或 daemon 启动失败；检查 `.pptx-html/daemon.log` 和可用空间，先保留草稿。 |
| `RECOVERY_FAILED` | journal、快照、Git ref 或正式文件出现无法安全判定的第三种状态；服务冻结发布以避免覆盖，保留证据后人工处理。 |
| 页面显示 Bridge 离线 | daemon/页面/Agent 生命周期独立。确认 workdir 对应 daemon 存活；必要时合法重开。离线不等于请求丢失。 |
| `kind="timeout"` | 当前有界等待内没有可认领请求；不是错误。仅在用户继续协作时再次 await。 |

更精确的字段、限额和恢复语义见[协议](../design/editor-agent-bridge-protocol.md)与[一致性/安全设计](../design/editor-agent-bridge-consistency.md)。当前自动验收范围与未测项见[测试记录](../test_acceptance/editor-agent-bridge.md#16-2026-10-03-实际执行记录)。

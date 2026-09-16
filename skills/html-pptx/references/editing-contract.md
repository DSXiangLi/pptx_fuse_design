# 可编辑标记契约（Editing Contract）

本文件是**生成技能**（生产者）与**编辑器页面**（消费者）之间的唯一协议。双方各自实现，以 HTML 文件中的标记为通信介质。文件是唯一事实源。

## 标记一览

| 标记 | 位置 | 含义 |
|---|---|---|
| `data-slide-id` | 每个 `<section class="slide">` | 页面的稳定语义 ID |
| `data-editable` | 叶子文本元素 | 用户可在编辑器中就地修改的文字 |
| `data-editable-image` | `<img>` | 用户可替换的图片 |
| `data-editable-skip` | 任意元素 | 纯装饰，编辑器必须忽略 |

## 规则（生成侧义务）

1. **稳定语义 ID**：`data-slide-id` 用描述性 kebab-case slug（如 `cover`、`q3-growth`、`closing`）。【禁止】用页码或遍历序号（`slide-1`、`slide-2`）——增删页面后序号漂移，编辑器的定位会套到错误元素上。
2. **标记在最小语义容器上**：`data-editable` 标在直接承载文字的元素（`h1`/`p`/`li`/`blockquote`/`td` 等），【禁止】标在 `section`、`div` 容器上——那会让编辑器把整个版式变成一个大文本框。
3. **内容保持简单**：`data-editable` 元素内部只含纯文本或简单行内标签（`<b>` `<i>` `<em>` `<strong>` `<br>`）。不含块级嵌套、不含 `<img>`、不含 SVG。
4. **图片**：`data-editable-image` 的 `src` 必须是指向 `assets/` 的相对路径。`alt` 写有意义的描述（编辑器会展示它）。
5. **装饰标记**：色块、分割线、背景图形、页眉页脚装饰文字，标 `data-editable-skip`。
6. **框架层不可编辑**：骨架中标注"框架层 · 禁止修改"的 CSS/JS/chrome 不在标记范围内，编辑器不得触碰。

## 规则（编辑器侧约定）

1. **两段手势**：首次点击只选中（显示选中框），再次点击（或双击）才进入编辑——否则给截断文本框加 contenteditable 会释放截断、元素突然撑高。
2. **纯文本优先**：进入编辑时设 `contenteditable="plaintext-only"`（不支持的浏览器降级 `"true"` 并拦截粘贴格式）。不提供富文本工具栏。
3. **就地补丁**：编辑结果直接写回 DOM，序列化整个文档保存。**永不重载页面**。
4. **序列化净化**：保存前移除一切编辑态残留（`contenteditable` 属性、选中态 class、编辑器注入的节点），保证存回的文件与"纯净产物"同构。
5. **保存**：File System Access API 直写原文件；不可用（非 Chrome/Edge、跨域 iframe 受限）时降级为下载导出。
6. **图片替换**：用户选择本地图片后，写入 `assets/` 目录并更新 `src`；同名覆盖优先（保持"替换 assets/ 同名文件即可换图"的心智模型）。
7. **兜底定位**：编辑器内部记录修改位置时，用 `data-slide-id` + 祖先 child-index 路径——页与路径之间用 `:`，路径层级之间用 `>`，如 `cover:h1.0`、`metrics:div.2>span.1`。不用全局遍历序号。

## 生成侧自检

交付前执行：

```bash
# 每页都有稳定 ID
grep -c 'data-slide-id="' index.html   # 应等于页数
# 没有可编辑元素里嵌套块级结构（人工抽查）
# 图片全部指向 assets/
grep -o 'src="[^"]*"' index.html | grep -v 'src="assets/'   # 应为空
```

## 版本

契约 v1（2026-09）。任何一侧修改标记语义前，必须同步修改本文件并告知另一侧。

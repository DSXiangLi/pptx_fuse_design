# 主题库（Themes）

策展的主题预设。**只选不改**：选定后整套 token 复制进骨架的 `SLOT: theme tokens`，禁止混搭、禁止自定义色值——色彩搭配错了画面瞬间变丑，保护审美比给自由更重要。

每套主题包含：调色板（语义 token）+ 字体栈 + 使用要点。字体栈默认走系统字体（离线可用）；用户明确接受联网加载时，可自行替换为 Web 字体。

来源标注：`A` = 归藏电子杂志风（双色墨水系统），`B` = 归藏瑞士国际主义（灰白底 + 单一高亮色），`C` = frontend-slides 策展预设。

---

## A 系 · 电子杂志 × 电子墨水

A 系的灵魂：衬线大标题 + 大留白 + 无阴影无卡片，靠字号与字体对比建立层级。`--accent` 默认等于 `--ink`——强调靠字重和字号，不靠颜色。

### A1 墨水经典（默认）

适合：通用分享、商业发布、任何场景的安全选择。调性：纯墨黑 + 暖米白，杂志感最强。

```css
--paper:#f1efea; --paper-tint:#e8e5de;
--ink:#0a0a0b;   --ink-tint:#18181a;
--accent:#0a0a0b; --accent-on:#f1efea;
--font-display:"Songti SC","Noto Serif SC","STSong",serif;
--font-body:"PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

### A2 靛蓝瓷

适合：科技/研究/数据分享、工程师文化、技术发布会。调性：深靛蓝 + 瓷白，冷静理性，像学术期刊。

```css
--paper:#f1f3f5; --paper-tint:#e4e8ec;
--ink:#0a1f3d;   --ink-tint:#152a4a;
--accent:#0a1f3d; --accent-on:#f1f3f5;
--font-display:"Songti SC","Noto Serif SC","STSong",serif;
--font-body:"PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

### A3 森林墨

适合：自然/可持续/文化/非虚构内容。调性：深森林绿 + 象牙，沉稳有呼吸感。

```css
--paper:#f5f1e8; --paper-tint:#ece7da;
--ink:#1a2e1f;   --ink-tint:#253d2c;
--accent:#1a2e1f; --accent-on:#f5f1e8;
--font-display:"Songti SC","Noto Serif SC","STSong",serif;
--font-body:"PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

### A4 牛皮纸

适合：怀旧/人文/阅读/历史/文学分享。调性：深棕 + 暖米，像牛皮信封，温暖有年代感。

```css
--paper:#eedfc7; --paper-tint:#e0d0b6;
--ink:#2a1e13;   --ink-tint:#3a2a1d;
--accent:#2a1e13; --accent-on:#eedfc7;
--font-display:"Songti SC","Noto Serif SC","STSong",serif;
--font-body:"PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

### A5 沙丘

适合：艺术/设计/创意/时尚、审美优先的场合。调性：炭灰 + 沙色，克制高级，像建筑设计图册。

```css
--paper:#f0e6d2; --paper-tint:#e3d7bf;
--ink:#1f1a14;   --ink-tint:#2d2620;
--accent:#1f1a14; --accent-on:#f0e6d2;
--font-display:"Songti SC","Noto Serif SC","STSong",serif;
--font-body:"PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

---

## B 系 · 瑞士国际主义

B 系的灵魂：高级灰白底 + **单一**高饱和高亮色 + 1px 极细分割线（hairline）+ 网格。字重阶梯：越大越细（大标题 weight 200–300），越小越粗。高亮色是手术刀，点到为止——一旦泛滥就掉档。

### B1 克莱因蓝（IKB）

适合：通用场合、商业发布、AI/科技、设计领域。最经典的瑞士配色，绝不出错。

```css
--paper:#fafaf8; --paper-tint:#f0f0ee;
--ink:#0a0a0a;   --ink-tint:#1a1a1a;
--accent:#002FA7; --accent-on:#ffffff;
--font-display:"Helvetica Neue","PingFang SC","Noto Sans SC",sans-serif;
--font-body:"Helvetica Neue","PingFang SC","Noto Sans SC",sans-serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

### B2 柠檬黄

适合：年轻、运动、零售、消费品、活力主题。浅色高亮，`.accent-on` 必须用深色文字。

```css
--paper:#fafaf8; --paper-tint:#f0f0ee;
--ink:#0a0a0a;   --ink-tint:#1a1a1a;
--accent:#FFD500; --accent-on:#0a0a0a;
--font-display:"Helvetica Neue","PingFang SC","Noto Sans SC",sans-serif;
--font-body:"Helvetica Neue","PingFang SC","Noto Sans SC",sans-serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

### B3 柠檬绿

适合：生态、可持续、健康、新兴科技、Z 世代品牌。荧光感适合屏幕与投影。

```css
--paper:#fafaf8; --paper-tint:#f0f0ee;
--ink:#0a0a0a;   --ink-tint:#1a1a1a;
--accent:#C5E803; --accent-on:#0a0a0a;
--font-display:"Helvetica Neue","PingFang SC","Noto Sans SC",sans-serif;
--font-body:"Helvetica Neue","PingFang SC","Noto Sans SC",sans-serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

### B4 安全橙

适合：工业、运动、技术发布会的"警告/转折/重点"页。只做局部高亮，满屏橙色过于刺眼。

```css
--paper:#fafaf8; --paper-tint:#f0f0ee;
--ink:#0a0a0a;   --ink-tint:#1a1a1a;
--accent:#FF6B35; --accent-on:#ffffff;
--font-display:"Helvetica Neue","PingFang SC","Noto Sans SC",sans-serif;
--font-body:"Helvetica Neue","PingFang SC","Noto Sans SC",sans-serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

---

## C 系 · 深色与个性（源自 frontend-slides）

C 系补充暗色与强个性方向。暗色主题中 `.slide.dark` 变体的角色反转：默认页即暗页。

### C1 信号黑（Bold Signal）

适合：高冲击发布、 keynote 开场、自信的品牌叙事。调性：深灰底 + 信号橙色块焦点。

```css
--paper:#1a1a1a; --paper-tint:#242424;
--ink:#ffffff;   --ink-tint:#0f0f0f;
--accent:#FF5722; --accent-on:#1a1a1a;
--font-display:"Arial Black","PingFang SC","Noto Sans SC",sans-serif;
--font-body:"PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

### C2 暗夜植物园（Dark Botanical）

适合：艺术、品牌、高端私享。调性：墨黑底 + 暖金/雾粉点缀，优雅克制。点缀色控制在每页一处。

```css
--paper:#0f0f0f; --paper-tint:#1a1816;
--ink:#e8e4df;   --ink-tint:#2a2724;
--accent:#d4a574; --accent-on:#0f0f0f;
--font-display:"Songti SC","Noto Serif SC","STSong",serif;
--font-body:"PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

### C3 终端绿（Terminal Green）

适合：开发者、技术布道、黑客美学。全页等宽字体，正文也可用 mono。

```css
--paper:#0d1117; --paper-tint:#161b22;
--ink:#e6edf3;   --ink-tint:#1c2128;
--accent:#39d353; --accent-on:#0d1117;
--font-display:"SF Mono","JetBrains Mono","Menlo",monospace;
--font-body:"SF Mono","JetBrains Mono","Menlo",monospace;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

### C4 纸与墨（Paper & Ink）

适合：文学、出版、深度长文分享。调性：暖米 + 炭黑 + 绯红 accent，配首字下沉、引文拉页更出彩。

```css
--paper:#faf9f7; --paper-tint:#efece7;
--ink:#1a1a1a;   --ink-tint:#2b2b2b;
--accent:#c41e3a; --accent-on:#faf9f7;
--font-display:"Songti SC","Noto Serif SC","STSong",serif;
--font-body:"Songti SC","Noto Serif SC","STSong",serif;
--font-mono:"SF Mono","JetBrains Mono","Menlo",monospace;
```

---

## 选择建议

| 场景 | 推荐 |
|---|---|
| 不知道选什么 | A1 墨水经典 |
| AI / 技术 / 产品发布 | A2 靛蓝瓷 或 B1 克莱因蓝 |
| 文化 / 行业观察 / 深度内容 | A3 森林墨 或 C4 纸与墨 |
| 人文 / 书评 / 生活方式 | A4 牛皮纸 |
| 设计 / 艺术 / 品牌 | A5 沙丘 或 C2 暗夜植物园 |
| 年轻 / 消费 / 活力 | B2 柠檬黄 或 B3 柠檬绿 |
| 开发者 / 工程文化 | C3 终端绿 |
| 高冲击 keynote | C1 信号黑 |

## 禁忌

- 禁止混搭：不取 A 系的底色配 B 系的高亮色；
- 禁止自定义 hex：用户坚持时展示本库请其重选；
- 禁止一份 deck 中途换主题；
- B 系的高亮色单页最多出现在一个视觉重心上。

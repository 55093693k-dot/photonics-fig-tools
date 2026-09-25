# fig_channel —— 给图件打"渠道标签"

**用途**：一张图的**证据等级取决于它是谁画的**。求解器（Lumerical）自己导出的结构视图 /
场分布 / 数据曲线，和用 matplotlib 重画出来的曲线，**不能当作等价的证据**。
这个模块把这条要求从"口头约定"变成**可审计的字段**：

- 在图上画一行 footer（人看得见）；
- 同时把同一句话写进 PNG 的 `tEXt` 元数据（机器读得到）；
- 于是整目录的图可以在几秒内自动核完，不需要 OCR（配合 `fig_index`）。

## 依赖

- 生成端：`matplotlib`（用于 `save()`）
- 读取端：**无第三方依赖** —— `read_text()` 是一个 20 行的 PNG chunk 解析器，
  即使没装 PIL 也能核验。

## 渠道约定

| 渠道 | 含义 |
|---|---|
| `official-monitor` | 求解器官方导出：`addindex()`（材料 / 折射率监视器）+ `image()` + `exportfigure()` |
| `official-view` | 求解器官方导出：`exportview()` |
| `external` | matplotlib / 任何非求解器渲染 —— **需要标签** |

规则：**官方渠道优先**；matplotlib **禁止**使用，除非 (a) 官方功能做不出这张图
且 (b) 事先获得批准。获批的外部图必须**在图旁**（footer）与**在报告里**都写明
"外部绘图，非官方导出"。

## 最小用法

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import fig_channel as FC          # 与本文件同目录

fig, ax = plt.subplots()
ax.plot([1, 2, 3], [1, 4, 9])
FC.save(fig, "out.png", "external",
        "model top view, source sim/MODEL_OBJECTS.json")
plt.close(fig)
```

`FC.save()` = `fig.savefig()` **加上** footer 标签 **加上** `tEXt` chunk。
要迁移已有的出图脚本，**只需把 `fig.savefig(...)` 一行换成 `FC.save(fig, ...)`**，
`dpi=` / `bbox_inches=` 等参数照常传（会原样透传给 `savefig`；
若自己传 `metadata=dict(...)`，会与渠道 chunk **合并**，不会被覆盖）。

## 核验一张图

```python
import fig_channel as FC
print(FC.read_text("out.png"))     # {'External-Plot': 'EXTERNAL PLOT (matplotlib) ...'}
```

要核一整个目录，用 `fig_index`。

## 设计上的两个小决定（都来自实际问题）

- **footer 用短句，完整声明放元数据。** footer 比画布宽时，`bbox_inches="tight"`
  会把图**横向撑宽**（实测出现过 1351 px 的图变成 1561 px）。所以图上只放短句，
  完整声明写进元数据 —— 而 `fig_index` 审计的正是元数据。
- **中文字体走字体文件，不走字体名。** matplotlib 按**字体名**查找 CJK 字体在
  某些机器上不可靠；这里按路径依次尝试 `msyh.ttc` / `simhei.ttf` / `simsun.ttc`，
  找不到就退回纯 ASCII footer（不报错）。

## 公开常量

| 名称 | 含义 |
|---|---|
| `CHUNK` | PNG `tEXt` 的键（默认 `"External-Plot"`） |
| `MARK` | `fig_index` 要求的 ASCII 标记（外部图必须包含它） |
| `TEXT` | 每个渠道的完整 ASCII 声明 |
| `save(fig, path, channel, provenance, **kw)` | 出图 + 打标签 |
| `read_text(path)` | 读出 PNG 的 `tEXt`/`iTXt` 字典 |

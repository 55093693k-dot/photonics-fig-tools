# fig_index —— 审计一整个图目录

**用途**：把"图件渠道规则"变成一条命令。扫描一个目录，逐张图：

1. 用命名规则判**渠道**（`--rule CHANNEL=REGEX`，先匹配者胜；没匹配上 = `external`）；
2. 渠道为 `external` 的图**必须**带渠道标签（PNG `tEXt` chunk + ASCII 标记）
   —— 缺 chunk / 缺标记 = **VIOLATION（退出码 1）**；
3. 记录每张图的**字节 / 像素 / md5**，并可对照 `--prov` 传入的来源 JSON
   （JSON 里带 `"path"` 键的记录），让"引擎 / 命令 / 字节"这组证据**跟着文件名走**；
4. 输出 `--index`（机器可读 JSON）+ 可选 `--md`（Markdown 表）。

**为什么这么做**：规则禁止把外部（matplotlib）图当成官方求解器导出来引用。
与其相信报告里写了一句说明，不如**让标签住在文件里**，再由工具读回来
—— "**文件本身就是证据**"。

## 依赖

- **无第三方运行时依赖**（纯标准库）。
- 需要 `fig_channel` 模块在同一 `sys.path` 上（默认标记与 chunk 键都取自它）。

## 最小用法

```powershell
python fig_index.py `
    --figs ..\figs `
    --index out\FIGS_INDEX.json `
    --md out\figs_README.md `
    --rule official-monitor=_idx_ --rule official-view=_exportview_ `
    --prov out\MATERIAL_FIGS.json
```

命令行参数

| 参数 | 说明 |
|---|---|
| `--figs` | **必填**：要扫的图目录 |
| `--index` | 写出 JSON 索引到这里 |
| `--md` | 写出 Markdown 表到这里 |
| `--rule` | `CHANNEL=REGEX`，可重复；不给则用默认两条 |
| `--prov` | 来源 JSON（可重复）；用于把来源记录挂到图记录上 |
| `--label-key` | 期望的 `tEXt` 键（默认 = `fig_channel.CHUNK`） |
| `--mark` | 期望出现在 chunk 里的 ASCII 标记（默认 = `fig_channel.MARK`） |

退出码：`0` = 无违规；`1` = 至少一条违规（**可直接用在 CI / 发布前自检里**）。

## 输出长什么样

JSON 索引里每张图一条记录：

```json
{"name": "fig01_field.png", "bytes": 48114, "kind": "PNG", "px": [1200, 800],
 "md5": "3f1c9a0b2d4e", "channel": "official-view", "label_ok": true, "label": ""}
```

`--md` 输出是一张表（图 / 渠道 / 字节 / 像素 / md5 / 标签 / 来源），
**可以直接当图目录的 README 用**。

## 三个实现细节

- **文件类型按字节嗅探，不看扩展名**（PNG 魔数、JPEG 走到 SOF 标记）。
  扩展名骗人的情况在导出图里并不少见。
- **非 PNG 的外部图会被标记为"标签无法审计"**（`note` 字段）——
  JPEG 没有 `tEXt` 通道，只能靠文件名规则区分，工具不会假装它通过了。
- **stdout 只用 ASCII**，避免在非 UTF-8 控制台上崩掉；结构化结果全部走 `--index` / `--md`。

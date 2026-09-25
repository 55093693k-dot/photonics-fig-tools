# rasterize_pdf —— 把 PDF 指定页光栅化成 PNG

**用途**：有些设计参数**只能从图上读出来**（渐变段的几何、层序、尺寸标注）。
凭印象抄下来的数没法辩护 —— 只有当你能**指定页码 + 指定 dpi 重现同一张光栅图**时，
那个数才站得住。这个工具把这件事变成一条命令，并顺带支持"先下载再光栅化"。

**为什么需要"先下载"这一步**：论文 PDF 常常不在本地，而手工下载再找路径会打断流程。
`--url` 让它在文件不存在时先取一份，存在就跳过（幂等）。

## 依赖

```powershell
pip install pymupdf        # import 名是 fitz
```

## 最小用法

```powershell
# 光栅化本地 PDF 的第 1、6 页，200 dpi
python rasterize_pdf.py --pdf refs\paper.pdf --pages 1,6 --dpi 200 --outdir refs\_pages

# 全部页
python rasterize_pdf.py --pdf refs\paper.pdf --pages all --dpi 300

# 先下载（仅当文件不存在时）再光栅化
python rasterize_pdf.py --url https://example.org/paper.pdf --pdf refs\paper.pdf --pages 6
```

## 参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `--pdf` | **必填** | PDF 路径（也是 `--url` 的落盘位置） |
| `--url` | 无 | 若 `--pdf` 不存在则先下载到这里 |
| `--pages` | `1` | `1` 起始、逗号分隔，或 `all` |
| `--dpi` | `200` | 光栅化分辨率 |
| `--outdir` | `<pdf 目录>/_pages` | 输出目录（自动创建） |

输出文件名：`<pdf 基名>_p<两位页号>_<dpi>dpi.png`（例如 `paper_p06_200dpi.png`）
—— **页码与 dpi 都编进文件名**，这样"我是按这张图读的数"是可指认的。

## 注意

- 第 N 页的**页码从 1 开始**（命令行里是 `6`，内部会转成 index 5）。
- `--dpi` 每页都会打印实际输出像素尺寸，用来确认没有意外缩放。
- 这个工具**只负责出图**，不做 OCR、不解读图上的数 —— 读数由人来做，
  工具只保证这一步可重放。
- 请确认你有权下载与使用该 PDF；不要把付费内容的光栅图随代码一起发布。

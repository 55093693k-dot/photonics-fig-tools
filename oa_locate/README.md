# oa_locate —— 由 DOI 查开放获取副本

**用途**：出版商站点（IEEE / Optica 等）对**脚本请求**会返回 418 / 403，
于是"我没法再看一眼那张图"就变成了一个设计决策的阻塞项。
OpenAlex 的 API 不做机器人拦截，并且列出每个开放获取出处
（出版商、仓库、arXiv …）及其**直链 pdf_url**。

这个工具就是一条查询：给 DOI，拿回所有 OA 出处 + 最佳 PDF 链接。

## 依赖

**无**（纯标准库：`urllib` + `json`）。

## 最小用法

```powershell
python oa_locate.py --doi 10.1364/OE.23.016289 --out refs\_oa2.json
```

## 参数

| 参数 | 说明 |
|---|---|
| `--doi` | **必填**：DOI（不带 `https://doi.org/` 前缀） |
| `--out` | **必填**：结果 JSON 的落盘路径（UTF-8） |

## 输出结构

```json
{
  "doi": "10.1364/OE.23.016289",
  "title": "...",
  "year": 2015,
  "oa": { "...": "OpenAlex 的 open_access 块" },
  "best_pdf": "https://.../paper.pdf",
  "locations": [
    {"pdf_url": "...", "landing": "...", "host": "...", "name": "...",
     "oa": true, "version": "publishedVersion"}
  ]
}
```

拿到 `best_pdf` 之后，配合 `rasterize_pdf` 就可以直接
"下载 + 光栅化到某页"：

```powershell
python rasterize_pdf.py --url <best_pdf> --pdf refs\paper.pdf --pages 6 --dpi 200
```

## 使用前请改一处

`oa_locate.py` 里的

```python
API = "https://api.openalex.org/works/doi:%s?mailto=your-email@example.com"
```

**请把 `your-email@example.com` 换成你自己的联系方式** —— OpenAlex 用 `mailto`
做"礼貌池"识别，写真实邮箱你的请求会被更稳定地服务。

## 边界

- 它查的是**公开的开放获取**条目，**不绕过任何付费墙**。
  查不到 OA 副本时，正确做法是走机构订阅或联系作者，而不是换工具。
- OpenAlex 的元数据可能滞后或有错；`best_pdf` 建议先试再信。
- 请遵守目标站点的服务条款与当地法律。

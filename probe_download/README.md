# probe_download —— 批量试 URL，把结果写进日志

**用途**：当你有一串候选链接（镜像、arXiv、机构仓库、出版商直链），
想知道**哪个真的能下、下到的是什么**。逐条手工点开很慢，而且控制台输出容易被截断
或受编码影响看不全。

这个工具一次试完所有 URL，把**状态码 / Content-Type / 字节数 / 前 8 字节魔数**
（以及短响应的正文）写进一份 UTF-8 日志 —— 于是"我确认过这个链接"是有记录的。

## 依赖

**无**（纯标准库）。

## 最小用法

```powershell
python probe_download.py --log out\probe.txt --save refs\paper.pdf `
    --urls https://a.example/p.pdf https://b.example/p.pdf https://arxiv.org/pdf/xxxx.xxxxx
```

## 参数

| 参数 | 说明 |
|---|---|
| `--urls` | **必填**：一个或多个待试 URL |
| `--log` | **必填**：UTF-8 日志输出路径 |
| `--save` | 可选：把成功的响应体保存到这里 |
| `--save-if` | 可选：仅当响应体以该字符串开头时才保存（用于"这其实是个 HTML 错误页"的情况） |

## 日志长什么样

```
OK   200  https://.../p.pdf  ct=application/pdf  bytes=2481327  magic=b'%PDF-1.7'
FAIL https://.../q.pdf  HTTPError: HTTP Error 403: Forbidden
OK   200  https://.../r.pdf  ct=text/html  bytes=1204  magic=b'<!DOCTYP'
     body> <!DOCTYPE html><html>...请登录...
```

最后一行是典型陷阱：**状态码 200、Content-Type 是 text/html** ——
看着像成功了，其实拿到的是一张登录页。`magic=` 与 `--save-if` 就是为这个设计的。

## 设计上的两个刻意选择

- **一切写进文件，不依赖终端。** 控制台编码和输出截断都不可靠；
  这份日志可以逐行 grep，也可以作为"当时确实是这个链接"的证据存档。
- **发送浏览器 UA 与 `Referer`。** 不少站点按 UA / Referer 做区分；
  设成和浏览器一致能显著降低误报的 403。

## 注意

- 请只探测你**有权访问**的资源；不要用它做批量抓取或绕过访问控制。
- 日志里可能含带查询串的 URL（部分站点用签名参数）—— 分享日志前先看一眼。

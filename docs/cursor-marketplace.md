# Cursor Marketplace 适配说明

这是仓库内的插件适配准备，不是 Cursor Marketplace 上架。本次没有提交发布申请，没有接受 [Cursor Marketplace Publisher Terms](https://cursor.com/marketplace-publisher-terms)，也没有改查册服务。本文不是法律意见，也不声明这套插件已经符合发布者条款。

按 2026-11-20 核对的条款文本，这套适配 **does not meet Marketplace listing approval conditions**。原因写在下面的收费边界里。在 Cursor 书面澄清第 3.1 条之前，不应把它当作可以上架的版本。

## 核对过的规范

- [Plugins](https://cursor.com/docs/plugins)
- [Plugins reference](https://cursor.com/docs/reference/plugins)
- 官方 manifest schema：[`https://cursor.com/schemas/cursor-plugin/plugin.json`](https://cursor.com/schemas/cursor-plugin/plugin.json)
- schema 原文快照：[`cursor/plugins` `schemas/plugin.schema.json`](https://github.com/cursor/plugins/blob/main/schemas/plugin.schema.json)，Git blob `02903d117b6a0e3bf6acd35aab3d48d91cd54a5e`
- 多插件索引 schema 只作排除依据：[`marketplace.schema.json`](https://github.com/cursor/plugins/blob/main/schemas/marketplace.schema.json)
- Agent Plugins 根 manifest schema：[`plugin.schema.json` 1.0.0](https://agent-plugins.org/schemas/1.0.0/plugin.schema.json)

本仓库在这次修改之前没有根目录 `plugin.json`，没有 `.cursor-plugin/plugin.json`，也没有 `mcp.json`。这是直接查看当前树得到的，不是沿用旧笔记。

## 选用的布局

Cursor 同时接受两种插件：

| 格式 | Manifest | 与本仓库的关系 |
| --- | --- | --- |
| Agent Plugin | 仓库根 `plugin.json` | 公开 schema 要求 `$schema`，并且拒绝未声明字段。该 schema 没有 Cursor 的 `variables`。 |
| Cursor Plugin | `.cursor-plugin/plugin.json` | 官方 schema 接受 `variables`。插件文档要求密钥只写成 `${VAR}`，由用户在 Plugins → Configure 填写。 |

这里使用 Cursor Plugin，插件根就是仓库根：

```text
.cursor-plugin/plugin.json
mcp.json
docs/cursor-marketplace.md
```

`plugin.json` 的 `mcpServers` 是相对路径 `./mcp.json`。这和 `cursor/plugins` 里已公开的 Hunter 插件相同：`type` 为 `http`，地址放在 `url`，密钥放在 `headers` 的 `${VAR}`。Hunter 的说明把这种 HTTP 端点称作 Streamable HTTP；本仓库 README 里给通用 MCP 客户端的示例则写成 `streamable-http`。插件包按 Cursor 市场上的 `http` 字段书写，不另造一种传输。

故意没有加的文件：

- 仓库根 `plugin.json`。它和 `.cursor-plugin/plugin.json` 是两套 manifest。Agent schema 不能表达这里需要的变量注入。
- `.cursor-plugin/marketplace.json`。它的 schema 要求 `plugins[]` 和每个插件的 `source`，用于一个仓库收录多个插件。本仓库只有一个插件。官方单插件提交看的是 plugin manifest，不是这条多插件索引。

`mcp.json` 启动 `scripts/cursor_mcp_stdio_bridge.js`，再把 JSON-RPC 转到已经公开的端点：

`https://www.86hc.com/wp-json/hkquery/v1/mcp/rpc`

直接把这个 URL 写进插件时，Cursor 3.31.11 会用协议版本 `2025-11-25` 做 `initialize`。2026-11-20 实测该端点对这个版本回复 `2026-07-28`。Cursor 自带的 MCP SDK 只接受 `2025-11-25`、`2025-06-18`、`2025-03-26`、`2024-11-05` 和 `2024-10-07`，于是连接失败，工具列表出不来。同一端点会原样回显 `2025-06-18`。桥接只在握手请求里把 Cursor 不兼容的版本改成 `2025-06-18`，其余消息原样转发，不另写查册服务。空的 `HK_COMPANY_API_KEY`，以及未替换的 `${HK_COMPANY_API_KEY}` 字面量，都不会被放进请求头。

## Cursor 3.31.11 图形界面验收

2026-11-20 在这台带 XFCE 显示的 Linux 上，用官方 `.deb` 安装了 Cursor `3.31.11`（`52fdf018932f1335bc6dd36acc5e33d307591920`）。测试使用单独的 `HOME` 和 `--user-data-dir`，没有登录，没有使用个人账号。

直接把远程 URL 写进插件时，Cursor 会加载 `86hc-hongkong-company`，但 stdio/HTTP 连接失败，日志是 `Server's protocol version is not supported: 2026-07-28`。改用上面的桥接后，同一未登录窗口里的日志变为 `Successfully connected to stdio server`，随后快照是 `status=connected`、`toolCount=9`。这是 Cursor 自己写出的工具描述文件，不是另一次手工握手。没有发送 `tools/call`。

子进程环境里的 `HK_COMPANY_API_KEY` 不是 manifest 里的默认空字符串，而是 21 字节的未替换字面量 `${HK_COMPANY_API_KEY}`。桥接把这种字面量当成未配置。因此这次能挂载，不能解读成 Cursor 已经套用了 `default: ""`。

命令面板可以执行 Open Plugins，窗口标题会变成 `Customize - workspace - Cursor`。未登录时画面仍停在 Log In / Sign Up，插件 logo 没有画出来。没有点击登录或注册。

没有新的查册进程，没有改 `server.py`、`index.js`、`package.json`、`pyproject.toml`、`Dockerfile` 或 GitHub Actions。可选密钥使用插件变量 `HK_COMPANY_API_KEY`，配置里的值只有 `${HK_COMPANY_API_KEY}`。不使用用户级 `mcp.json` 的 `${env:NAME}`，那是另一套插值。变量不放进 `required`，默认是空字符串，以保留现有的客人额度路径。

发布者身份只写仓库和官网已经公开的资料：HC BUSINESS LIMITED、`https://www.86hc.com`、`support@86hc.com`。官网首页标题为「香港公司注册处查册｜董事股东查询｜BR商业登记证 - 恒诚」。没有把其他品牌写进插件元数据。

## 收费边界

[Publisher Terms 3.1](https://cursor.com/marketplace-publisher-terms)（页面所载 Last updated May 6, 2026）的意思是：Marketplace 对发布者免费提供上架；插件一旦发布，用户不付费即可获得；发布者不得因为用户通过 Marketplace 访问或使用插件而直接或间接收费。

现有服务没有被改写成免费版，付费能力也没有从工具列表里拿掉。2026-11-20 的只读 `tools/list` 返回与仓库一致的 9 个工具。收费边界以下列当时能公开打开的页面为准，没有登录用户中心，也没有下单：

- 接入指南第 3 节工具表和第 5 节三档额度：简体 [sec-mcp-5](https://www.86hc.com/insights/hong-kong-company-search-mcp-api-claude-cursor-integration-guide#sec-mcp-5)、繁体 [sec-mcp-5](https://www.86hc.com/tc/insights/hong-kong-company-search-mcp-api-claude-cursor-integration-guide#sec-mcp-5)、英文 [sec-mcp-5](https://www.86hc.com/en/insights/hong-kong-company-search-mcp-api-claude-cursor-integration-guide#sec-mcp-5)。
- 统一价格表：[简体](https://www.86hc.com/pricing)、[繁体](https://www.86hc.com/tc/pricing)、[英文](https://www.86hc.com/en/pricing)。
- 用户中心入口公开返回标题「个人中心与法定查册控制台」：[领 Key](https://www.86hc.com/user?tab=mcp#mcp)、[积分充值收银台参数](https://www.86hc.com/user?tab=mcp&mcp_topup=1#mcp)。本次没有登录，没有查看余额，没有进入收银台。

2026-11-20 简体指南第 5 节写的三档是：

| 档 | 公开标价 | 公开包含的额度 |
| --- | --- | --- |
| 免 Key | HK$ 0 | 每日 15 次搜索、3 家全息详情；存档目录与银行开户预审写为无限次免费 |
| 免费 API Key | HK$ 0 | 每日 50 次搜索 + 20 家全息详情，00:00 重置；每笔付费调档赠 +10 永久积分 |
| 永久积分包 | HK$ 100 / 100 积分 | 公开折合每家全息查册 HK$ 1.00；写明先扣每日 20 点免费额度，永久积分不过期 |

同一页第 3 节工具表把带 Key 的 `search_companies` 写成 20 次/日，第 5 节和第 5 节英文页则写成 50 次/日。价格表里的积分包又写「叠加每日免费 50 次搜索 + 20 家详情」。这三处公开数字不一致，这里并列保留，不替页面裁决哪一个才算数。

和费用直接相关、本次没有调用的能力是：

- `create_filing_order`：`readOnlyHint` 为 false。指南写明它调取 NAR1、NNC1、BRC 或 360° 报告，并返回付款链接或扣减积分，须经用户确认。价格表把注册处存档写成「法定规费 + 统一服务费 HK$ 10/份」。2026-11-20 公开合计包括 NAR1 / NNC1 HK$ 28、ND2A HK$ 20、A&A HK$ 33。商业登记证电子复本合计 HK$ 40，商业登记册电子摘录合计 HK$ 47。360° 全景尽调报告标价 HK$ 499。价格表还有更多尽调方案，这里不逐项改写成插件功能。
- `manage_account_credits`：`readOnlyHint` 为 false。指南和价格表都写明 HK$ 100 购买 100 个永久查询积分。查余额被写成免费只读；充值须经用户确认。
- `batch_get_company_details`：只读。免 Key 每日 3 家；带 Key 每日 20 家。英文工具表写明每家 1 个积分。每日免费额度用完后，公开规则是扣永久积分。
- `search_companies`：公开页把它写成每日次数上限，没有写成按次港币单价。免 Key 是 15 次/日。带 Key 的次数在上面两处公开文字里分别是 20 和 50，超额后如何处理，本次没有调用。
- `get_company_filings`、`assess_bank_account_eligibility`、`check_filing_order_status`、`check_bank_application_status`：指南写成 100% 免费、只读。状态查询仍可能按单号返回下载链接或申请资料。本次没有调用。
- `submit_bank_account_application`：指南写成 100% 免费，并要求申请人确认。它仍会收集联络资料。本次没有调用。

`create_filing_order` 在现有说明里不配置 API key 也会生成付款链接。客人额度因此不能解释成「插件的使用不收费」。付费工具仍然处在同一条 MCP 连接上。

本次没有为了绕过 3.1 删除这些工具，也没有做一套隐藏的受限免费版。那样会改变产品，同时隐瞒付费服务。

结论保持为：条款未被澄清前，这套适配不具备上架批准条件。

官网这些页面本次只确认可以公开打开，没有改写，也没有代替发布者条款：

- https://www.86hc.com/terms-of-service
- https://www.86hc.com/privacy-policy
- https://www.86hc.com/disclaimer

## 验证范围

可重复的本地检查：

```bash
python3 -m pip install -r scripts/requirements-cursor-plugin-check.txt
python3 scripts/validate_cursor_plugin.py --check-upstream
python3 -m unittest tests/test_cursor_plugin_manifest.py
python3 -m py_compile server.py
node --check index.js
python3 scripts/mcp_readonly_handshake.py
```

握手只发送 `initialize` 和 `tools/list`。它不读取环境里的 API key，不发送 `tools/call`。无 header、空 `X-API-Key`、字面量 `${HK_COMPANY_API_KEY}` 三种列工具结果需要一致。这只说明现有网关在列工具时接受这三种 header。

Cursor 3.31.11 的图形界面验收写在上面。那次没有登录，插件进程收到的是未替换字面量，不是空字符串。Customize 标题可以打开，logo 仍被登录页挡住。

也没有完成这些验收：

- 没有用真实 key 连接，没有查询公司、下单、购买文件或读取客户资料
- 没有登录 Cursor 或 86hc 账号。`https://cursor.com/marketplace/publish` 的公开页本次没有给出可提交表单，因此表单上的实时字段名未被看到
- 没有接受发布者条款，没有发邮件，没有创建上架

仓库是公开的：`https://github.com/86hc-compliance/hongkong-company-mcp`。公开本身不等于已经获准上架。

## 以后若要人工提交，再准备的字段

下面这些本次都没有填进 Marketplace 表单：

| 字段 | 当前仓库里的值或缺口 |
| --- | --- |
| 仓库地址 | `https://github.com/86hc-compliance/hongkong-company-mcp` |
| 插件名 | `86hc-hongkong-company` |
| 显示名 | `86HC Hong Kong Company` |
| 版本 | `1.3.2`，与当前 MCP server 相同，不是新的服务版本 |
| 简介 | manifest 里的英文描述，包含 payment links |
| 作者 / 发布者 | `HC BUSINESS LIMITED`，`support@86hc.com` |
| 主页 | `https://www.86hc.com` |
| 许可证 | `MIT` |
| 分类 | `integrations`，只沿用官方插件仓库里见过的分类名 |
| 关键词 | `86hc`、`hong-kong`、`company-registry`、`mcp` |
| Logo | `assets/logo.png`，manifest 用相对路径引用。原图 94×84、不透明白底，图案未居中。官方文档没有规定像素尺寸，所以没有裁切、放大或改成透明背景。Marketplace 里的实际显示还没有图形界面可看 |
| 最低客户端版本 | 未写。官方 Hunter 示例写了 Cursor `3.13.0`，本仓库没有验证这个下限 |
| MCP 地址 | 插件启动本地桥接，转发到上面的现有 RPC 地址。直接 HTTP 在 Cursor 3.31.11 上因协议版本 `2026-07-28` 被拒绝 |
| 变量 | `HK_COMPANY_API_KEY`，可选，默认空 |
| 额度与单价披露 | 接入指南 `#sec-mcp-5`、`https://www.86hc.com/pricing` 及其繁体、英文页。本次没有填进 Marketplace 表单 |
| 服务条款 | `https://www.86hc.com/terms-of-service` |
| 隐私政策 | `https://www.86hc.com/privacy-policy` |
| 免责声明 | `https://www.86hc.com/disclaimer` |
| 发布者条款 | 未接受 |
| 身份和营业审查材料 | 未准备 |

合并到 `main` 还会触发 `.github/workflows/docker-publish.yml`。该流程会构建 Docker Hub 镜像，并用本仓库 `README.md` 更新镜像说明。本次不推 `main`，也不合并。

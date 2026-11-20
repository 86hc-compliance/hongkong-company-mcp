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

`mcp.json` 只指向已经公开的端点：

`https://www.86hc.com/wp-json/hkquery/v1/mcp/rpc`

没有新的查册进程，没有改 `server.py`、`index.js`、`package.json`、`pyproject.toml`、`Dockerfile` 或 GitHub Actions。可选密钥使用插件变量 `HK_COMPANY_API_KEY`，配置里的值只有 `${HK_COMPANY_API_KEY}`。不使用用户级 `mcp.json` 的 `${env:NAME}`，那是另一套插值。变量不放进 `required`，默认是空字符串，以保留现有的客人额度路径。

发布者身份只写仓库和官网已经公开的资料：HC BUSINESS LIMITED、`https://www.86hc.com`、`support@86hc.com`。官网首页标题为「香港公司注册处查册｜董事股东查询｜BR商业登记证 - 恒诚」。没有把其他品牌写进插件元数据。

## 收费边界

[Publisher Terms 3.1](https://cursor.com/marketplace-publisher-terms)（页面所载 Last updated May 6, 2026）的意思是：Marketplace 对发布者免费提供上架；插件一旦发布，用户不付费即可获得；发布者不得因为用户通过 Marketplace 访问或使用插件而直接或间接收费。

现有服务没有被改写成免费版，付费能力也没有从工具列表里拿掉。2026-11-20 的只读 `tools/list` 返回与仓库一致的 9 个工具。和费用直接相关、本次没有调用的能力是：

- `create_filing_order`：`readOnlyHint` 为 false。仓库描述写明它为 NAR1、NNC1、CI、A&A、ND2A、BRC、EBRE 生成支付宝、AlipayHK 或 Stripe 付款链接。线上工具描述里能看到 stripe、alipay、payment、checkout、credit 和 HK$。
- `manage_account_credits`：`readOnlyHint` 为 false。仓库描述写明 `buy_100_credits` 以 HK$ 100 购买 100 个查询额度，并生成付款链接。
- `batch_get_company_details`：只读，但仓库写明每家公司消耗 1 个额度。客人每日额度用完之后，继续查询依赖付费额度。
- `search_companies`：仓库写明不消耗详情额度，客人每日 15 次。超额之后是拒绝还是另收费，本次没有调用，不能下结论。
- `submit_bank_account_application`：`readOnlyHint` 为 false，会提交申请并收集联络资料，仓库要求个人 API key。仓库没有写这个工具本身的价格，所以这里不把它说成免费，也不另编一个价格。
- `check_filing_order_status` 和 `check_bank_application_status` 按单号查询状态，可能返回下载链接或申请资料。本次没有调用。

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

握手只发送 `initialize` 和 `tools/list`。它不读取环境里的 API key，不发送 `tools/call`。无 header、空 `X-API-Key`、字面量 `${HK_COMPANY_API_KEY}` 三种列工具结果需要一致。这只说明现有网关在列工具时接受这三种 header，不说明 Cursor 客户端会在变量为空时成功挂载插件。

Agent SDK 的扩展文档写明，未解析的插件占位符会使校验失败，而不是挂上半截服务器。IDE 是否把 `default: ""` 当成已解析，本次没有 Cursor 图形界面可以确认。

也没有完成这些验收：

- 没有把插件放进 `~/.cursor/plugins/local` 后执行 Reload Window
- 没有在 Customize 里看到 `plugin-86hc-hongkong-company-hongkong-company`
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
| Logo | 仓库没有 logo 文件，manifest 不引用 |
| 最低客户端版本 | 未写。官方 Hunter 示例写了 Cursor `3.13.0`，本仓库没有验证这个下限 |
| MCP 地址 | 上面的现有 RPC 地址，`type` 为 `http` |
| 变量 | `HK_COMPANY_API_KEY`，可选，默认空 |
| 服务条款 | `https://www.86hc.com/terms-of-service` |
| 隐私政策 | `https://www.86hc.com/privacy-policy` |
| 免责声明 | `https://www.86hc.com/disclaimer` |
| 发布者条款 | 未接受 |
| 身份和营业审查材料 | 未准备 |

合并到 `main` 还会触发 `.github/workflows/docker-publish.yml`。该流程会构建 Docker Hub 镜像，并用本仓库 `README.md` 更新镜像说明。本次不推 `main`，也不合并。

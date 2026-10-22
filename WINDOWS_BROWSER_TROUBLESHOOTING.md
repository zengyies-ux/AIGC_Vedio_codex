# 浏览器会话异常与Windows特定故障排查

本页供Codex按实际故障查阅；组员正常使用只需[三步SOP](QUICK_START.md)。不要把修复命令变成每次安装必做步骤。

## 正常准备

新安装先保持Codex应用及用户配置的默认位置；工作流和素材可以放在`D:\短剧项目`等用户选择的目录，不需要挪到系统盘。已有自定义配置先识别，不自动重置或移动。默认路径是减少变量的部署建议，不是所有浏览器故障的已证实原因。

默认使用Codex内置浏览器；不可用先报告具体工具限制，不静默转外部浏览器。Windows按`Ctrl+T`打开浏览器标签页（该宿主已提供内置浏览器且支持该快捷键时，入口以当前界面为准），在同一会话登录制作网站；需要读取飞书在线材料时再登录飞书。外部Edge／Chrome已登录不代表内置浏览器也已登录。用户明确指定其他浏览器时按要求执行；已有连接只在选定浏览器内复用。

先实际读取目标页面，确认工具连接和站点权限。文件上传能力另按当前宿主工具文档核实；仅可读网页不等于可上传。权限拒绝、连接缺失、登录失效分别报告，不更换通道绕过拒绝。Windows操作体验属于当前测试反馈，不保证所有版本比Mac更快。

<a id="session-recovery"></a>
## 当前聊天连不上：先区分异常（Mac／Windows通用）

已有一次现场记录：旧聊天持续报`Local browser use is disabled in Work settings`，用户确认已登录并明确选择内置浏览器；用户授权新开同项目聊天后，新聊天正常读取及下载。只能确认两会话表现不同，原因未定位，不能据此保证新开必好，也不能只凭错误文字断言用户关了设置。

- **找不到标签页／标签列表为空：**不等于浏览器被禁用。工具仍可用时，在当前聊天的内置浏览器打开用户给的完整URL；创建调用报错也先重新列实际标签，若页面已经存在就绑定，不反复新建。不猜旧聊天标签ID，不假定其他聊天的页签自动共享。
- **当前聊天的工具连接不可用：**保存现有记录，向用户说明原始错误。用户确认浏览器可用但本聊天仍失败时，建议用户在同一项目新开聊天、重新选择内置浏览器，先做一次普通读取诊断；只有用户明确要求时，AI才代建新聊天。新聊天仍失败则停止重复尝试，核实际设置／连接或日志；不连续创建多个窗口碰运气。
- **制作网站登录失效：**有本次正常恢复授权、飞书已登录且账号／应用／既有权限相符时，按[飞书正常恢复](extensions/seedance-jumeng-operator/references/generation-execution.md#login-recovery)勾选协议、使用飞书登录、授权，再重访原完整目标URL；只有扫码、验证码、凭据、账号冲突或新权限等无法内部完成的情况才交用户。恢复后先核原队列／历史，不重提交未知点击。
- **生成提示词审核拒绝：**这与浏览器或账号权限拒绝不同。按[合规表达](memories/seedance_workflow/field_lessons.md#moderation-recovery)核具体回执与内容，完成实质合规改稿后在原授权范围内处理，不用换账号／聊天试同样内容。
- **网站访问明确拒绝、管理员限制或宿主安全审查拒绝：**停受影响操作，交用户按正常权限流程处理；不得以新聊天、换账号或控制通道规避拒绝。新聊天只诊断会话连接，不扩大权限。

切换前旧聊天停止网页写入。把当前材料目录、目标集／URL、已完成文件、采用稿／资产来源记录、回执日志及待办留在现有状态；给用户一段简短续做话，不另建一套交接表。新聊天先读同一记录，核实际页面再补差异：已下载文件直接复用，已有卡不重建，已提交或回执未知的生成任务先查，不因换聊天重提。延续的授权仍限原任务；原来只准备不能变成付费生成。

## 浏览器入口消失且内置插件清单缺失

**匹配条件：** `@Chrome`／`@Browser`入口缺失，日志明确报`bundled-marketplaces\openai-bundled\.agents\plugins\marketplace.json`不存在；当前官方安装包内原始清单实际存在。只有扩展未授权、网站未登录或上传不可用时，不套用本修复。

用户报告在Microsoft Store／MSIX版`26.1013.4894.0`中复制838个文件后恢复。社区Issue记录了加密／Application Protected文件导致部分复制方式失败、`xcopy /G`成功的类似情形。这是特定故障的已报告绕过办法，不是官方通用修复，也不是本项目在Windows独立复现的结论；文件数量会随版本变化。

1. 保存任务，**完全退出Codex**，在独立PowerShell中执行。不要让Codex在自己运行时覆盖插件缓存。
2. 先核安装包、原清单与日志实际目标。下面脚本仅适用默认用户目录；若设置了`CODEX_HOME`、存在多个安装包，或报错路径不同，先查实际位置，不直接照抄。

```powershell
$ErrorActionPreference = 'Stop'
if ($env:CODEX_HOME) { throw '存在自定义CODEX_HOME，请先核实际缓存位置，不自动重置。' }
$packages = @(Get-AppxPackage -Name OpenAI.Codex)
if ($packages.Count -ne 1) { throw '未找到唯一安装包，请核当前Codex安装来源。' }
$source = Join-Path $packages[0].InstallLocation 'app\resources\plugins\openai-bundled'
$dest = Join-Path $env:USERPROFILE '.codex\.tmp\bundled-marketplaces\openai-bundled'
$manifest = Join-Path $source '.agents\plugins\marketplace.json'
if (!(Test-Path -LiteralPath $manifest -PathType Leaf)) { throw '安装包原清单不存在，不适用此修复。' }
Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json | Out-Null
Write-Host "来源：$source"
Write-Host "目标：$dest"
```

3. 确认目标与错误日志一致后，复制官方安装包内的完整目录。若目标已有部分内容，先在同一父目录留备份；备份失败就停止，不删除旧目录继续。

```powershell
if (Test-Path -LiteralPath $dest) {
    $backup = "$dest.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss-fff')"
    Copy-Item -LiteralPath $dest -Destination $backup -Recurse -ErrorAction Stop
}
New-Item -ItemType Directory -Path $dest -Force | Out-Null
xcopy "$source\*" "$dest\" /E /I /Y /G /H
if ($LASTEXITCODE -ne 0) { throw "xcopy未成功完成，退出码：$LASTEXITCODE" }
$targetManifest = Join-Path $dest '.agents\plugins\marketplace.json'
if (!(Test-Path -LiteralPath $targetManifest -PathType Leaf)) { throw '目标清单仍缺失。' }
Get-Content -LiteralPath $targetManifest -Raw | ConvertFrom-Json | Out-Null
if ((Get-FileHash -LiteralPath $manifest).Hash -ne (Get-FileHash -LiteralPath $targetManifest).Hash) {
    throw '来源与目标清单哈希不一致。'
}
Write-Host '清单复制核对通过；请重启Codex验证实际浏览器。'
```

`/E`包含空子目录，`/I`按目录处理目标，`/Y`覆盖同名文件，`/G`允许复制加密源到不支持加密的目标，`/H`包含隐藏／系统文件。操作只针对官方内置插件缓存，不触碰工作流项目、模型、作品或账号文件。

4. 重开Codex、新建聊天，检查`@`入口并实际打开网页、读取内容及点击普通链接。清单存在不等于浏览器已可用。仍失败时保留错误与启动日志，继续检查插件初始化／注册状态；不盲目重复复制。

不要删除整个`.codex`、伪造空清单、修改WindowsApps所有权／ACL，或照抄第三方的保留插件市场注册配置。日志对外提供前隐去账号、令牌和个人路径。本页不自动修复正在运行的应用。

## 能填图，但项目素材库为空

按[素材与正文节点](extensions/seedance-jumeng-operator/references/fill-and-verify.md#素材与正文节点)核项目库、卡片参考、正文节点。先查分类与搜索条件，再补库；这不是已证实的Windows限制。用户本次反馈明确说明代理经提醒可上传，故按流程遗漏修订。无需重生成视频来验证入库。

## 来源

- [OpenAI快捷键说明](https://learn.chatgpt.com/docs/reference/commands)：内置浏览器可用时的Windows Ctrl+T。
- [OpenAI Codex社区Issue #41164](https://github.com/openai/codex/issues/41164)：缺失内置插件市场与复制失败的社区报告；不等同官方修复承诺。
- [Microsoft xcopy文档](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/xcopy)：参数与退出码。

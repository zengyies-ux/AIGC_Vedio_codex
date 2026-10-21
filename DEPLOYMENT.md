# 交给Codex部署到本机

本页供执行部署的Codex使用。组员只需提供仓库地址；环境、依赖、路径和校验由Codex处理，不让用户手动配置。正常登录／系统弹窗和确实缺失的材料由用户处理。日常上手见[上手SOP](QUICK_START.md)。

## 先辨版本与目录

本工作树为Core1.9.3本地候选，用户明确测试时核实际本地提交及candidate.json；不要到GitHub寻找未发布的1.9.3包，也不要把正式包冒称已包含本地修订。默认正式部署如下。

当前正式推荐V3.9／Core1.9.2，发行标签core-v1.9.2，专用核心包Seedance_Codex_Workflow_Core_v1.9.2_2026-10-20_release.zip。旧候选与1.8.8正式包保留，核包名、清单和release_status=release。新导演策略与快速检查的实片效果边界见验证说明。

仓库：https://github.com/zengyies-ux/AIGC_Vedio_codex 。从[Core1.9.2正式Release](https://github.com/zengyies-ux/AIGC_Vedio_codex/releases/tag/core-v1.9.2)获取附件。Core1.8.8基线已在Mac验证同聊天连续三集及另一单集，共11条原生+2次延长，视觉复查与临时副本清理完成；含用户补充声线，声音未审，不宣称无人介入或全片无误。Windows x64 CPU提供部署适配，用户确认Core1.7.2实操可用；本版在线资产、快速检查和审片清理等增量仍待Windows真机增量验证。发布状态不等于所有平台或所有画面已验收。

- 从固定标签`core-v1.9.2`读取`packaging/package_config.json`、`releases/latest.json`及本说明，下载上述正式ZIP与同名SHA文件，核内容版本、清单、实际tag提交和哈希。不把旧候选或未核的latest当正式版。
- `main`首页只作正式发布导航；源码开发目录与干净Core制作目录分开，不clone历史main后直接运行旧规则，不使用GitHub自动生成的Source code ZIP替代专用核心包。候选版须用户明确选择并核其实际状态。
- 用户没给安装目录时，在本机文档目录选清楚命名的新目录；已有项目不得覆盖。Windows路径使用本机实际盘符与反斜杠，含空格路径正确引用，不要求用户改成Unix路径或手工设置PATH。

## 获取、校验与安装

1. 核系统／架构、可用Python、目标目录及是否已有制作项目。新安装优先使用用户指定的空目录；若没给，选本机文档目录下清楚命名的新目录，遇同名非空目录先辨用途，不能覆盖。
2. 获取上节选定的**核心ZIP和同版本SHA文件**到临时目录；对ZIP计算SHA-256与附件值一致，校验ZIP CRC，再解到临时目录。检查包名／版本目录、`PACKAGE_INFO.md`的版本和`release_status`，逐项核`MANIFEST.sha256`，文件集合须等于清单加MANIFEST本身；拒绝绝对路径、上级逃逸和非预期文件。发布附件还可对照GitHub返回的digest；没有SHA或清单不完整不能标部署通过。
3. 新安装只将校验后的核心根目录放到制作目录；空项目索引用于首次登记。启动入口为`AGENTS.md`，通用制作词见[唯一启动词](NEW_PROJECT_CONVERSATION_PROMPT.md)。用户选择旧公开包时，以该包实际能力为准，不把当前分支的文档当旧包已安装能力。
4. **升级先保护用户资料。** 对旧／新MANIFEST中的发行文件做差异，临时备份需替换文件；只替换清单中的发行文件，明确跳过`memories/seedance_workflow/projects/INDEX.md`，保留所有用户项目、状态、采用稿、偏好、素材、`.codex_tmp/`缓存和已有环境。检查本机改过的发行文件并保留其副本／差异，不能静默覆盖未辨归属的个人修改；不整包覆盖或清空目录。升级后按新发行清单核除受保护索引外的安装文件，索引差异单列，不能假称与空索引逐字一致。

这些步骤由Codex执行、记录结果；不把下载、建venv、挑版本或手改路径的工作转给新人。

## 自动准备与自检范围

先读[音频工具说明](tools/local_audio/README.md)。Core1.8.5沿用已验Mac arm64英文MLX，提供Windows x64英文CPU预览适配（faster-whisper1.2.1／CTranslate2 4.8.3／int8）。两平台用各自Python3.12锁文件，模型／转写缓存分后端，用户项目与原音轨不动。用户确认Windows1.7.2实操可用；未提供的硬件、性能及异常恢复细节仍以本机实际自检记录，不称全平台稳定。

Codex先定位Python3.12；Windows优先用`py -3.12`，Mac优先已有项目环境或`python3.12`。缺少时由Codex通过本机可用的官方／常规渠道准备独立运行时，例如Windows可用winget的`Python.Python.3.12`用户安装；安装后重新定位实际解释器，用户只处理必要正常系统弹窗。不改系统Python或要求用户手配环境。

由Codex以找到的Python绝对路径执行（PowerShell路径含空格用调用运算符`&`，Unix路径正常引号）：

```text
<实际Python3.12> -X utf8 tools/local_audio/bootstrap.py --install --prepare-model
```

`bootstrap.py`按系统选择锁文件，健康venv复用，缺依赖补齐，损坏环境旁建后再采用；报告实际`active_python`及恢复阶段。后续用报告的解释器运行工具，不假设它一定在旧默认路径。下载失败保留可恢复缺项，不写成功；Windows文件占用先结束相应占用后重跑，不删除用户原文件／缓存。模型固定repo／revision及manifest，首次下载与缓存复用分开记录。CPU不用CUDA；如导入报Visual C++ Runtime缺失，由Codex走[微软官方运行库](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)正常安装（可用winget的`Microsoft.VCRedist.2015+.x64`），必要系统授权由用户处理，不让用户手配DLL或PATH。

自检包含依赖版本、运行时导入、内置decoder和临时WAV；`--prepare-model`核固定模型。用户已有本集音轨时，再由Codex加`--audio <真实MP3/WAV绝对路径>`核真实转写、缓存、耗时及词表；不要为部署强行处理历史项目，不把导入／模拟当真实音频通过。正文、JSON及日志使用UTF-8，实际中文用户名／空格路径和Windows占用恢复仍须真机验证。CPU性能按真机记录，不承诺硬件无关速度。

Windows可以原生PowerShell使用Codex，也可选WSL2，见[官方Windows说明](https://learn.chatgpt.com/docs/windows/windows-app)；本版Windows预览优先原生x64 CPU。用户已有Windows1.7.2实际制作成功反馈；新电脑的安装、模型下载恢复、CPU资源与文件占用等具体条件仍按本机验证，不能用旧版、Mac或模拟结果冒充本版在线入口、清理及画面质量通过。

新安装保持Codex应用／用户配置默认位置，已有自定义配置先识别，不自动重置；本工作流和材料仍可使用用户指定的D盘目录。网页默认使用Codex内置浏览器，在线取图与制作保持同一浏览器会话；Windows当前版本支持时可用Ctrl+T打开标签页（以当前界面为准），提前在同一会话登录制作网站，使用飞书在线材料时才登录飞书。用户明确指定其他浏览器时才改变；内置浏览器工具不可用先报告，不因外部浏览器已登录自动换用。当前聊天连接失败先按[会话异常处理](WINDOWS_BROWSER_TROUBLESHOOTING.md#session-recovery)区分缺标签、工具错误与明确拒绝；同项目新聊天读取诊断有成功案例，但不保证修复。只有浏览器入口缺失且日志指向内置插件清单时，才用Windows条件式修复，不默认执行复制。

网页需另核当前宿主提供的真实浏览器连接、正常登录及目标集可读状态。读到`extensions/seedance-jumeng-operator/SKILL.md`只说明技能文本存在；连接未提供或站点拒绝时据实报告，保留恢复点，不绕过。部署自检只读网页，不代用户生成／付费或改项目卡。

## 部署完成的交付

报告制作目录、实际来源tag／提交、版本／候选状态、ZIP与MANIFEST校验结果，并分别列：

| 项目 | 应报事实 |
|---|---|
| 核心 | 文件就绪、入口正确；新安装空项目，升级用户资料保护结果 |
| 音频 | 系统／架构／Python、依赖／decoder／Metal／模型是否就绪，实际做过的转写或待适配项 |
| 浏览器 | 工具是否连接、登录／页面是否可读，未提供URL则未核；不把技能安装当连接成功 |

给出[完整制作启动词](NEW_PROJECT_CONVERSATION_PROMPT.md)；仅收集资产时使用[独立资产收集词](ASSET_DOWNLOAD_PROMPT.txt)。请组员随后只放材料、指定集数和个人想法。记录真实耗时与必要人工介入；未验证项明确留待实际任务，不称完整新机／新一集链路已验收。

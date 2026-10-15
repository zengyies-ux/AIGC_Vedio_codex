# 交给Codex部署到本机

这是唯一部署执行说明，面向执行部署的Codex。组员给仓库地址、目标目录和版本选择即可；依赖选择、环境准备与自检由Codex完成。正常账号登录、系统交互或确实无法内部解决的缺项才交用户。创作想法用自然语言记录到项目既有偏好，不要求组员修改核心或配置文件。

## 先辨版本与目录

仓库：<https://github.com/zengyies-ux/AIGC_Vedio_codex>。2026-10-15核对：默认`main`仍是历史备份；已发布Core入口为[core-v1.5.1](https://github.com/zengyies-ux/AIGC_Vedio_codex/releases/tag/core-v1.5.1)，提交`631bb6a4b7c49116ed66d62948711fa0d314d3d3`，也是prerelease，不称稳定版。当前[V3.6工作分支](https://github.com/zengyies-ux/AIGC_Vedio_codex/tree/codex/director-v3-6)的Core1.6.1为分支候选，未创建对应tag／Release，新一集完整链路待验。

- 未指定试候选时，先实时核上述明确tag和Release附件；若状态变化，报告差异并按用户版本意图取包，不能用GitHub“latest”隐式跳过prerelease。当前默认取1.5.1专用核心ZIP及同名SHA文件，**它不包含V3.6延长准备与本次修订**。
- 用户明确试V3.6候选时，解析`codex/director-v3-6`真实提交，按该提交读取`packaging/package_config.json`、`releases/latest.json`及其中指定的1.6.1核心ZIP／SHA，记录提交、候选状态和文件哈希。候选附件在工作分支`releases/`，不是不存在的core-v1.6.1 Release。
- 团队制作目录使用已校验的干净核心包；源码开发目录供修改／打包，不能默认clone旧main或将GitHub自动生成的Source code ZIP整包当制作环境。只取核心ZIP，不导入仓库历史项目。

## 获取、校验与安装

1. 核系统／架构、可用Python、目标目录及是否已有制作项目。新安装优先使用用户指定的空目录；若没给，选本机文档目录下清楚命名的新目录，遇同名非空目录先辨用途，不能覆盖。
2. 获取上节选定的**核心ZIP和同版本SHA文件**到临时目录；对ZIP计算SHA-256与附件值一致，校验ZIP CRC，再解到临时目录。检查包名／版本目录、`PACKAGE_INFO.md`的版本和`release_status`，逐项核`MANIFEST.sha256`，文件集合须等于清单加MANIFEST本身；拒绝绝对路径、上级逃逸和非预期文件。发布附件还可对照GitHub返回的digest；没有SHA或清单不完整不能标部署通过。
3. 新安装只将校验后的核心根目录放到制作目录；空项目索引用于首次登记。启动入口为`AGENTS.md`，通用制作词见[唯一启动词](NEW_PROJECT_CONVERSATION_PROMPT.md)。用户选择旧公开包时，以该包实际能力为准，不把当前分支的文档当旧包已安装能力。
4. **升级先保护用户资料。** 对旧／新MANIFEST中的发行文件做差异，临时备份需替换文件；只替换清单中的发行文件，明确跳过`memories/seedance_workflow/projects/INDEX.md`，保留所有用户项目、状态、采用稿、偏好、素材、`.codex_tmp/`缓存和已有环境。检查本机改过的发行文件并保留其副本／差异，不能静默覆盖未辨归属的个人修改；不整包覆盖或清空目录。升级后按新发行清单核除受保护索引外的安装文件，索引差异单列，不能假称与空索引逐字一致。

这些步骤由Codex执行、记录结果；不把下载、建venv、挑版本或手改路径的工作转给新人。

## 自动准备与自检范围

先读[音频工具说明](tools/local_audio/README.md)，复用未变且自检通过的环境／同音轨缓存。当前已验证**Apple Silicon Mac、Python3.12、英文MLX Whisper**；其他系统和语言不能沿用该已验结论。

Mac arm64由Codex定位已有Python3.12；缺少时在本机允许的常规安装渠道准备独立运行时，正常系统安装授权由用户处理，不修改系统Python。以下从制作根目录执行，已有正确venv不重复创建／安装：

```sh
python3.12 -m venv .codex_tmp/audio_v3/venv
.codex_tmp/audio_v3/venv/bin/python -m pip install --cache-dir .codex_tmp/audio_v3/pip-cache -r tools/local_audio/requirements-lock-macos-arm64-py312.txt
.codex_tmp/audio_v3/venv/bin/python -m pip check
.codex_tmp/audio_v3/venv/bin/python tools/local_audio/localize.py --help
.codex_tmp/audio_v3/venv/bin/python tools/prompt_review/check_prompt.py --help
```

继而由Codex检查锁定依赖版本、MLX的Metal可用性、`imageio_ffmpeg.get_ffmpeg_exe()`返回decoder的正常启动；不需要用户手改PATH／先装Homebrew。依现有`localize.py`的`model_directory(Path('.codex_tmp/audio_v3'))`准备或校验固定repo／revision及权重manifest，首次约481MB公开模型下载与已有缓存复用分别记录。音频留本机，初次准备不强行转写某个历史项目。解码可用临时短音频自检；模块导入／decoder／权重通过仍不等于真实转写已测，当前新机转写需实际跑过才报通过。

**Windows可以使用Codex**：官方已支持原生PowerShell，也可选WSL2，见[官方Windows说明](https://learn.chatgpt.com/docs/windows/windows-app)。本项目锁定的MLX音频后端目前尚未适配／验收Windows，不在Windows直接执行Mac锁文件，也不把切WSL当MLX已兼容。可自动获取核心、做哈希／文件校验和纯Python入口检查；音频标为“未就绪／本项目待适配”，本机可读资料与无关工作继续。未经真实验证不得报Windows整集全链部署成功；本轮不另造第二套音频后端或完整安装器。

网页需另核当前宿主提供的真实浏览器连接、正常登录及目标集可读状态。读到`extensions/seedance-jumeng-operator/SKILL.md`只说明技能文本存在；连接未提供或站点拒绝时据实报告，保留恢复点，不绕过。部署自检只读网页，不代用户生成／付费或改项目卡。

## 部署完成的交付

报告制作目录、实际来源tag／提交、版本／候选状态、ZIP与MANIFEST校验结果，并分别列：

| 项目 | 应报事实 |
|---|---|
| 核心 | 文件就绪、入口正确；新安装空项目，升级用户资料保护结果 |
| 音频 | 系统／架构／Python、依赖／decoder／Metal／模型是否就绪，实际做过的转写或待适配项 |
| 浏览器 | 工具是否连接、登录／页面是否可读，未提供URL则未核；不把技能安装当连接成功 |

给出[通用制作启动词及源就绪短续做词](NEW_PROJECT_CONVERSATION_PROMPT.md)，请组员随后只放材料、指定集数和个人想法。记录真实耗时与必要人工介入；未验证项明确留待实际任务，不称完整新机／新一集链路已验收。

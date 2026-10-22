# Seedance Codex Workflow

**把剧本、配音和真实素材交给 Codex，完成导演设计、视频提示词与授权范围内的网页制作。**

你只需准备材料、填写启动词。环境配置、音频定位、素材核对和内部记录由 Codex 完成。

```mermaid
flowchart LR
    A[你准备材料] --> B[Codex解读并设计]
    B --> C[填写网页并按授权生成]
    C --> D[你查看成片与反馈]
```

| 现在要做什么 | 从这里开始 |
|---|---|
| 第一次使用 | 按下方 **① 安装 → ② 放材料 → ③ 开始制作** 操作 |
| 已安装，开始一集或连续2—3集 | [正式版完整制作启动词](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.9.2/NEW_PROJECT_CONVERSATION_PROMPT.md) |
| 只收集图片，暂不制作视频 | [正式版独立资产收集词](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.9.2/ASSET_DOWNLOAD_PROMPT.txt)；无需音频 |
| 中断了，想继续 | 告诉 Codex：“先核已有任务和结果，沿原记录继续，不重复提交。” |

> **正式推荐：Core 1.9.2 · V3.9**
>
> 当前本地工作树为1.9.5候选，新增正常登录恢复、审核修订整稿重填与情绪跨切设计，保留既有制作规则；尚未推送。本地验证用仓库内启动词，下面公开部署仍指正式1.9.2。
>
> 本版修订多人设计、原台词核查、快速视觉检查及上手流程。既有生产链有实测记录；新增创作规则不等于已经证明每集更好看，具体效果以实际成片反馈为准。

## ① 安装：把这段话发给 Codex

只在首次使用或需要升级时操作。复制整段，无需自己下载依赖：

```text
请从 https://github.com/zengyies-ux/AIGC_Vedio_codex 部署推荐版本 Core 1.9.2。
先读取 core-v1.9.2 标签下的 DEPLOYMENT.md，获取并校验正式核心包，准备本机环境并自检。
保留我已有的项目、素材、偏好和缓存；完成后报告核心、音频和浏览器状态，并告诉我应在Codex中打开哪个含AGENTS.md的制作目录。
```

按提示完成账号登录或系统弹窗。等 Codex 报告自检结果后继续；出现问题，直接把报错交给它处理。

## ② 放材料：建一个剧目文件夹

例如 Windows 的 `D:\短剧项目\剧名`，或 Mac 的 `~/Documents/短剧项目/剧名`。Mac实际路径可从Finder复制。放好以下材料：

| 材料 | 你需要准备什么 |
|---|---|
| 剧本 | 完整剧本；启动时说明要做哪一集 |
| 配音 | 每集一个完整 MP3，已剪掉多余气口和长空白，保留全部旁白、对白、顺序及必要停顿；已有有效 WAV 也可 |
| 图片 | 已有角色、场景和必要道具图；没有本地图时提供只读在线资产文档链接 |
| 想法（可选） | 直接写想强调的剧情、情绪或画面；不写即交给 AI 导演 |

**不用做时间码、单集 Word、逐镜表或下载目录配置。** Codex 先核本地，缺少或不确定才查所给在线来源；新下载图片归入这份材料目录。

## ③ 开始制作：复制启动词，填写顶部

先在制作网站打开目标剧目中的本集生成页面，复制地址栏完整URL；每集使用自己的页面链接，网页字段不要填网站首页。

打开[正式版完整制作启动词](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.9.2/NEW_PROJECT_CONVERSATION_PROMPT.md)，复制其中完整代码块到工作流项目的新聊天。只改顶部的剧名／集数、材料目录、可选资产链接、制作网页、想法和执行范围。

- **先准备，自己点生成**：选择“只准备，由我点击生成”。
- **让 Codex 完成生成**：使用启动词提供的生成授权选项，明确允许付费提交、等待、视觉复查和有界修正。
- **连续2—3集**：明确写集数范围，并逐集给出网页，例如“EP19：URL；EP20：URL”。

保持电脑与当前任务运行。缺少登录、权限或必要图片时，按 Codex 汇总的具体问题补充即可。完成后说“这版采用”，或指出要修改的片段。

需要更详细的一步一步说明，查看[正式版使用指南](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.9.2/QUICK_START.md)。

<details>
<summary><strong>只想收集资产？</strong></summary>

打开[正式版独立资产收集词](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.9.2/ASSET_DOWNLOAD_PROMPT.txt)，整份复制到新聊天，只填写剧名、负责集数、材料目录和在线资产文档。Codex 会读负责范围剧本，核本地，补下载适配原图，整理来源与真实缺项。

不需要音频，不进入视频制作。角色优先三视／阶段造型，不收独立面部高清图；不生成或重绘图片。资产是否齐全按剧本需要与实际核图判断，不能只看下载数量。

本版提供[两名子代理协作收集词](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.9.2/ASSET_DOWNLOAD_PROMPT.txt)：分别核剧本需求和资产缺项，主控独占浏览器与下载归档。

</details>

<details>
<summary><strong>已验证到哪里，有哪些边界？</strong></summary>

| 环境 | 现有证据与边界 |
|---|---|
| Apple Silicon Mac | Core1.8.8基线已完成一聊天三集及另一单集，共11条原生、2次延长；视觉复查与13份临时视频清理有记录。生成声音按用户要求未审，不宣称画面全部无误。 |
| Windows x64 | Core1.7.2实操已获用户确认；提供CPU音频后端、依赖准备与自检。本版新增量仍待Windows真机验证。 |
| 其他架构／语言 | 未声明完整支持，以本机自检为准。 |

资产样本已核42张唯一原图（角色23、场景16、道具3），文件与来源指纹一致。样本不是新剧资产齐全的保证。1.9.2的规则与工具检查不代替新成片验证。详细记录见[正式版验证说明](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.9.2/validation/director_v38.md)。

默认只准备；生成和付费需明确授权。关键问题最多三次修正须在任务授权内，不自动充值或无限返抽。当前支持活动任务内等待，关闭应用后不会自动持续执行。本流程不生成资产图。

</details>

<details>
<summary><strong>下载、升级与维护入口</strong></summary>

| 用途 | 正式1.9.2入口 |
|---|---|
| 下载 | [正式Release](https://github.com/zengyies-ux/AIGC_Vedio_codex/releases/tag/core-v1.9.2) |
| 部署／升级／自检 | [DEPLOYMENT.md](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.9.2/DEPLOYMENT.md) |
| 制作规则 | [AGENTS.md](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.9.2/AGENTS.md) |
| 网页操作 | [执行技能](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.9.2/extensions/seedance-jumeng-operator/SKILL.md) |
| 变化与计划 | [CHANGELOG](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.9.2/CHANGELOG.md) · [ROADMAP](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.9.2/ROADMAP.md) |
| 核心包维护 | [packaging/README](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.9.2/packaging/README.md) |

使用Release专用核心包 `Seedance_Codex_Workflow_Core_v1.9.2_2026-10-20_release.zip` 及同名校验文件；GitHub自动生成的Source code ZIP不作为团队制作包。核心包不含真实项目、素材、媒体或账号，升级保留个人资料。

维护者查看[部署说明](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.9.2/DEPLOYMENT.md)和[版本变化](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.9.2/CHANGELOG.md)。旧版见[历史Release](https://github.com/zengyies-ux/AIGC_Vedio_codex/releases)。

</details>

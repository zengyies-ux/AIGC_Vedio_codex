# Seedance Codex Workflow

面向短剧制作团队的 Codex 工作流：读取剧本、音频和真实资产，完成导演设计与提示词，并按授权执行网页生成、等待结果和视频延长。

**当前正式推荐：Core 1.8.8 · V3.8**

Core1.8.8已获用户验证认可：一聊天连续三集与另一单集正常制作完成。运行与画面审查已可用，人物表现、部分构图和具体成片仍需要用户判断。

[使用SOP](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.8.8/QUICK_START.md) · [完整制作启动词](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.8.8/NEW_PROJECT_CONVERSATION_PROMPT.md) · [独立资产收集词](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.8.8/ASSET_DOWNLOAD_PROMPT.txt) · [下载正式版](https://github.com/zengyies-ux/AIGC_Vedio_codex/releases/tag/core-v1.8.8)

## 开始使用

把下面这段话交给 Codex：

```text
请从 https://github.com/zengyies-ux/AIGC_Vedio_codex 部署推荐版本 Core 1.8.8。
先读取 core-v1.8.8 标签下的 DEPLOYMENT.md，获取并校验正式核心包，准备本机环境并自检。
保留我已有的项目、素材、偏好和缓存；完成后报告核心、音频和浏览器状态，并给出制作入口。
```

准备完整剧本、目标集已剪好气口的完整 MP3、已有资产或只读在线资产链接，以及可选想法。把材料目录原样交给 Codex，例如 `D:\短剧项目\剧名`；无需填写时间码、下载目录或内部记录。

## 制作范围

- 从原材料开始，或沿用已采用的解读、分段、正式稿，只补剩余工作。
- 先读本集剧本、核本地资产；不足时从已提供来源主动下载原图，归入材料目录。角色优先适配三视／阶段造型，不收独立面部高清图。
- 结合连续声音含义设计行动和回应，核人物状态、空间关系及可剪余量；简单动作使用自然短句。
- 将真实图片补入项目素材库，加入卡片参考并建立正文引用；明确授权后执行本集原生生成、活动任务内等待及必要的一次延长。

支持一聊天一集，或明确指定连续2—3集并提供各集网页。默认只准备；生成和付费需明确授权，关键问题最多三次修正须在任务授权内，不自动充值或无限返抽。本流程不生成资产图，线上仍缺的必要素材集中说明。自动等待需要当前任务持续运行，关闭应用后的持久后台执行尚未提供。

## 验证范围

| 环境 | 已有证据与边界 |
|---|---|
| Apple Silicon Mac | 本版一聊天三集及另一单集共11条原生、2次延长完成，视觉复查与13份临时视频清理已有证据。三集任务含一次声线补充；生成声音按用户要求未审，不宣称画面全部无误。 |
| Windows x64 | 提供CPU音频后端、依赖准备与自检；用户已确认 Core 1.7.2 实操可用。保留该基线，1.8.8在线资产、审片清理等增量仍需真机验证。 |
| 其他架构／语言 | 未声明完整支持，由 Codex 报告本机实际能力。 |

资产收集样本已核42张唯一原图（角色23、场景16、道具3）；文件与来源指纹一致。已有原生生成、等待及一次延长成功记录；具体版本、人工介入、效果反馈和待验项见[验证说明](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.8.8/validation/director_v38.md)。首次部署仍须本机自检。

## 项目入口

| 使用者 | 入口 |
|---|---|
| 制作组员 | [简明SOP](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.8.8/QUICK_START.md)、[完整启动词](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.8.8/NEW_PROJECT_CONVERSATION_PROMPT.md)、[独立资产收集词](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.8.8/ASSET_DOWNLOAD_PROMPT.txt) |
| 执行部署的Codex | [部署、升级与自检](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.8.8/DEPLOYMENT.md) |
| 执行制作的Codex | [唯一规则入口](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.8.8/AGENTS.md)、[网页操作技能](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.8.8/extensions/seedance-jumeng-operator/SKILL.md) |
| 维护者 | [版本变化](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.8.8/CHANGELOG.md)、[路线图](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.8.8/ROADMAP.md)、[核心包维护](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.8.8/packaging/README.md) |

使用 Release 专用核心包 `Seedance_Codex_Workflow_Core_v1.8.8_2026-10-20_release.zip` 及同名校验文件；GitHub自动生成的Source code ZIP不作为团队制作包。核心包不含真实项目、素材、媒体或账号，升级保留个人资料。

默认分支首页固定导航到正式标签；开发与旧版见[分支](https://github.com/zengyies-ux/AIGC_Vedio_codex/branches)和[历史Release](https://github.com/zengyies-ux/AIGC_Vedio_codex/releases)。下一版1.9.0将针对人物性格、关系互动与镜头设计做本地试验，不混入本版运行验证。

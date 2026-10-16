# Seedance Codex Workflow

面向短剧制作团队的 Codex 工作流：读取剧本、音频和真实资产，结合用户想法完成提示词，并按授权执行网页原生生成、等待结果和视频延长。

**当前发布：Core 1.7.2 · V3.7 团队上手版**

[使用SOP](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.7.2/QUICK_START.md) · [完整制作启动词](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.7.2/NEW_PROJECT_CONVERSATION_PROMPT.md) · [下载与版本说明](https://github.com/zengyies-ux/AIGC_Vedio_codex/releases/tag/core-v1.7.2)

## 开始使用

把本仓库地址交给 Codex：

```text
请从 https://github.com/zengyies-ux/AIGC_Vedio_codex 部署推荐版本 Core 1.7.2。
先读取 core-v1.7.2 标签下的 DEPLOYMENT.md，获取并校验干净核心包，自动准备本机环境并自检。
保留我已有的项目、素材、偏好和缓存；完成后告诉我核心、音频、浏览器是否就绪，并给出制作入口。
```

部署完成后，准备完整剧本、目标集已剪好气口的完整 MP3、已有资产图，以及可选想法。Windows 示例路径为 `D:\短剧项目\剧名`；把实际路径原样交给 Codex 即可。按[三步SOP](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.7.2/QUICK_START.md)开始制作，用户无需手填时间码或管理内部文件。

## 可以完成什么

- 从原材料开始，或沿用已经采用的解读、分段、正式稿，只补剩余工作。
- 核对音频、角色与素材阶段，保持原句、声音映射和本集可剪余量。
- 填写网页、上传必要真实素材、建立图片／视频引用，提交前设置本段参数。
- 明确授权后，完成本集原生生成、活动任务内等待、必要局部核源及一次延长；中断后按记录恢复。

默认只准备；生成和付费需要本次明确授权。必要素材由用户补充，本流程不生成资产图。不自动充值、失败重提或修改其他集。不同集默认独立原生，同集按需接续。

## 平台与验证状态

| 环境 | 当前范围 |
|---|---|
| Windows x64 | 已提供CPU音频后端、依赖准备与自动自检；**真机完整制作待验证**。首次部署可测试，不标为全链已验。 |
| Apple Silicon Mac | 英文音频工具及网页完整制作已有真实单集验证，画面与连续性获用户认可。 |
| 其他架构／语言 | 未声明完整支持；由Codex说明实际能力及缺项。 |

真实案例完成两条原生和一次延长，各提交一次，无人工网页接管；用户补充必要场景素材一次。程序／受控测试与实片效果分别记录，见[验证说明](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.7.2/validation/director_v37.md)。一个成功案例不代表所有场景、异常恢复或Windows均已通过。

自动等待需要当前任务继续运行；关闭应用后的持久后台执行尚未提供。浏览器连接、网站登录及账户积分由使用者本人持有。

## 项目入口

| 使用者 | 入口 |
|---|---|
| 制作组员 | [简明SOP](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.7.2/QUICK_START.md)、[完整启动词](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.7.2/NEW_PROJECT_CONVERSATION_PROMPT.md) |
| 执行部署的Codex | [部署、升级与自检](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.7.2/DEPLOYMENT.md) |
| 执行制作的Codex | [唯一规则入口](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.7.2/AGENTS.md)、[网页操作技能](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.7.2/extensions/seedance-jumeng-operator/SKILL.md) |
| 维护者 | [版本变化](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.7.2/CHANGELOG.md)、[路线图](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.7.2/ROADMAP.md)、[核心包维护](https://github.com/zengyies-ux/AIGC_Vedio_codex/blob/core-v1.7.2/packaging/README.md) |

请使用Release中的专用核心ZIP及校验文件，不把GitHub自动生成的Source code ZIP当作团队制作包。核心包不含真实项目、素材、音频、成片或账号信息，升级保留个人资料。

本仓库为公开仓库。默认分支保留历史代码，本首页导航指向已清理旧SOP目录的当前发布标签；开发工作与版本记录可从[分支](https://github.com/zengyies-ux/AIGC_Vedio_codex/branches)和[历史Release](https://github.com/zengyies-ux/AIGC_Vedio_codex/releases)追溯。

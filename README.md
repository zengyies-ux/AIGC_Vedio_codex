# Seedance 视频提示词工作流

把剧本、想法和真实素材转成有情绪、动作因果与连续声音的视频提示词，并按授权填入网页、准备视频延长。团队使用干净Core制作；源码工作树用于开发。

## 交给Codex部署

本页在V3.7工作分支。要试本次候选，可直接把下面这段交给Codex：

```text
请将 https://github.com/zengyies-ux/AIGC_Vedio_codex/tree/codex/director-v3-7 的Core1.7.0候选部署到本机[目标目录，可留空由你选新空目录]。
先读该分支DEPLOYMENT.md，核真实提交与候选状态，获取干净核心ZIP并校验SHA和MANIFEST；辨系统／架构，自动准备支持范围的环境与工具并自检。
升级保留我的项目、索引、偏好、素材和缓存。分别报告核心、音频与浏览器是否就绪，提供制作入口；正常登录／系统弹窗或真实缺项才请我处理。
```

[唯一部署说明](DEPLOYMENT.md)负责全部执行步骤。当前默认main仍是历史备份，已发布点[Core1.5.1](https://github.com/zengyies-ux/AIGC_Vedio_codex/releases/tag/core-v1.5.1)是prerelease；它不含V3.7延长准备和本次修订。Core1.7.0在本工作分支供试用，未创建该版本tag／Release，也未通过完整自动执行链与Windows真机验收。仅给仓库根地址时应辨明这些版本，不以clone成功代替当前核心部署。

当前Mac继续已验英文MLX Whisper；新增Windows x64 CPU音频候选与自动环境／自检入口，真机安装、音频和网页仍待验证。支持范围和自检按部署说明，不让组员自行选Python／修改核心配置。技能文本存在与浏览器实际连接分开报告。

## 制作与规则入口

- 唯一AI规则入口：[AGENTS.md](AGENTS.md)。按任务加载，不读整库／历史项目。
- [通用制作基线与源就绪短续做词](NEW_PROJECT_CONVERSATION_PROMPT.md)：材料目录、目标集及可选网页／想法；明确本任务自主授权，普通默认验证模式保留。
- [规则导航](memories/seedance_workflow/README.md)、[项目状态索引](memories/seedance_workflow/projects/INDEX.md)、[新项目模板](memories/seedance_workflow/projects/PROJECT_TEMPLATE.md)。团队核心ZIP内索引为空，升级不能覆盖个人索引。
- [版本记录](CHANGELOG.md)、[能力与待验](ROADMAP.md)、[匿名V3.7证据](validation/director_v36.md)。

V3.7支持从原始材料、已采用解读／分段、已有正式稿三个自然入口继续，只补当前执行所需事实，不强制重导演／三代理／转写。保原句、声音跨镜、摄影、七栏与本集额外6—10秒可剪素材；人物选择、对方下一步与相关第三人影响由主控落实到镜头。身份与阶段适配继续核实际资产，用户只给真实资料与想法，本流程不出图。

跨集默认按角色／阶段／场景独立原生，不等待前集末态；同集必要接续仍可一次延长，区域累计只沿本集链。[唯一网页技能](extensions/seedance-jumeng-operator/SKILL.md)默认只准备；正确模式不再点、填后不切回，必要节点身份等待保留，不为已知秒数回退反复设置或重访。收到本任务生成指令后才在目标卡设置参数、最后设整数秒并同页核准。

用户可明确授权本集原生及所需一次延长的完整生成链，沿[唯一执行规程](extensions/seedance-jumeng-operator/references/generation-execution.md)提交一次、活动任务内短周期等待可见结果、局部核合格源再继续。轻量回执日志保护中断／接管恢复，点击后回执未知先查队列，不盲重试；不自动加购／失败返抽，也不宣称应用关闭后持续运行。开发本版不代表获得生产生成授权。

已有历史待源恢复、左柄缩参考、同源节点／区间和单次提交回执证据；后续用户报告画面约70分可用及互动不足。现行模式／秒数流程按反馈修正，历史切卡和切模式试验不再是生产必做。V3.7完整自动链只做受控模拟，本轮不改已完成作品；Windows真机、完整自动链现场表现及新集互动效果仍待验证，见[本版说明](validation/director_v37.md)。

## 目录与历史恢复

| 位置 | 用途 |
|---|---|
| memories/seedance_workflow/ | 导演、执行、接续、既有模板与按需案例 |
| memories/seedance_workflow/projects/ | 本地制作状态、素材、采用索引及历史；不加入新Core公开包 |
| tools/、extensions/ | 本机音频／提示检查与唯一网页技能 |
| packaging/、releases/ | 显式白名单、核心候选／发行记录与校验 |
| Skill/、团队专项SOP/ | 保留的社区资料与团队文档，不作默认规则入口 |

早期完整备份及恢复标签见[历史版本记录](CHANGELOG.md)与[发行记录](releases/README.md)。它们保留当时范围，不能当新人干净Core。需要恢复时先在新目录核对，保住当前制作；当前公开提交只限核心白名单，私有项目、网址／ID、截图与媒体留本机。仅在用户明确要求的里程碑提交／推送，不自动同步；本轮推工作分支候选，不改main、旧标签或旧发行物。

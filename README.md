# Seedance 视频提示词工作流

把剧本、想法和真实素材转成有情绪、动作因果与连续声音的视频提示词，并按授权填入网页、准备视频延长。团队使用干净Core制作；源码工作树用于开发。

## 交给Codex部署

本页在V3.6工作分支。要试本次候选，可直接把下面这段交给Codex：

```text
请将 https://github.com/zengyies-ux/AIGC_Vedio_codex/tree/codex/director-v3-6 的Core1.6.1候选部署到本机[目标目录，可留空由你选新空目录]。
先读该分支DEPLOYMENT.md，核真实提交与候选状态，获取干净核心ZIP并校验SHA和MANIFEST；辨系统／架构，自动准备支持范围的环境与工具并自检。
升级保留我的项目、索引、偏好、素材和缓存。分别报告核心、音频与浏览器是否就绪，提供制作入口；正常登录／系统弹窗或真实缺项才请我处理。
```

[唯一部署说明](DEPLOYMENT.md)负责全部执行步骤。当前默认main仍是历史备份，已发布点[Core1.5.1](https://github.com/zengyies-ux/AIGC_Vedio_codex/releases/tag/core-v1.5.1)是prerelease；它不含V3.6延长准备和本次修订。Core1.6.1在本工作分支供试用，未创建该版本tag／Release，也未通过新一集完整链路验收。仅给仓库根地址时应辨明这些版本，不以clone成功代替当前核心部署。

当前本机音频已测Apple Silicon Mac英文MLX Whisper；Windows可使用Codex，但本项目Windows音频尚待适配。支持范围和自检按部署说明，不让组员自行选Python／修改核心配置。技能文本存在与浏览器实际连接分开报告。

## 制作与规则入口

- 唯一AI规则入口：[AGENTS.md](AGENTS.md)。按任务加载，不读整库／历史项目。
- [通用制作基线与源就绪短续做词](NEW_PROJECT_CONVERSATION_PROMPT.md)：材料目录、目标集及可选网页／想法；明确本任务自主授权，普通默认验证模式保留。
- [规则导航](memories/seedance_workflow/README.md)、[项目状态索引](memories/seedance_workflow/projects/INDEX.md)、[新项目模板](memories/seedance_workflow/projects/PROJECT_TEMPLATE.md)。团队核心ZIP内索引为空，升级不能覆盖个人索引。
- [版本记录](CHANGELOG.md)、[能力与待验](ROADMAP.md)、[匿名V3.6证据](validation/director_v36.md)。

V3.6保已有强情绪／肢体交锋、连续声音跨镜、原句、七栏、摄影与整集额外6—10秒可剪素材。A交人物职责及阶段变化，C据此核实际资产身份和身体／造型／空间，主控核冲突处理落实到成稿；身份正确不等于整张图适用。

[唯一网页技能](extensions/seedance-jumeng-operator/SKILL.md)保原生独立任务一卡，延长先核真实平台结构及合格原生源，当前已验同源卡延长草稿、片段区间、视频槽／正文真实视频同源及必要图片。一次明确本集原生及所需延长准备授权覆盖该范围；缺源只相关段待源，通知就绪后局部核源再续做，不重复建卡或重转音轨。模型2.5Pro／480P／整数新增秒在任务身份、模式与引用就绪后最后核。不点击生成、批量生成或付费。

两条延长准备已有实际证据，正文／节点／模式／源槽／区间重访保持，新增秒数重访回5，恢复后只当前同页正确；原生也曾回4秒或单独回退模型／分辨率。用户后续报告整集生成，局部体态偏差已促成本次规则纠正，不把准备成功写成实片合格。新一集全链路、手调区间、多候选选源、完整声音／同步等仍待实际验证。

## 目录与历史恢复

| 位置 | 用途 |
|---|---|
| memories/seedance_workflow/ | 导演、执行、接续、既有模板与按需案例 |
| memories/seedance_workflow/projects/ | 本地制作状态、素材、采用索引及历史；不加入新Core公开包 |
| tools/、extensions/ | 本机音频／提示检查与唯一网页技能 |
| packaging/、releases/ | 显式白名单、核心候选／发行记录与校验 |
| Skill/、团队专项SOP/ | 保留的社区资料与团队文档，不作默认规则入口 |

早期完整备份及恢复标签见[历史版本记录](CHANGELOG.md)与[发行记录](releases/README.md)。它们保留当时范围，不能当新人干净Core。需要恢复时先在新目录核对，保住当前制作；当前公开提交只限核心白名单，私有项目、网址／ID、截图与媒体留本机。仅在用户明确要求的里程碑提交／推送，不自动同步；本轮推工作分支候选，不改main、旧标签或旧发行物。

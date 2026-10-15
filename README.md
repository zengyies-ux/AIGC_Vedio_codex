# Seedance 视频提示词工作流

将当前剧本、用户想法与参考素材转成可执行的视频提示词，并根据真实成片反馈局部修正。项目保留导演规则、提示词模板、各剧制作记录、已有素材与历史版本。

## 从哪里开始

- AI协作入口：[AGENTS.md](AGENTS.md)。按当前任务加载规则，不自动读取全部历史项目。
- 新项目启动：[NEW_PROJECT_CONVERSATION_PROMPT.md](NEW_PROJECT_CONVERSATION_PROMPT.md)。
- 规则导航：[工作流说明](memories/seedance_workflow/README.md)。
- 当前及已完成项目：[项目索引](memories/seedance_workflow/projects/INDEX.md)。
- 版本记录：[CHANGELOG.md](CHANGELOG.md)。

## 目录

| 位置 | 内容 |
|---|---|
| `memories/seedance_workflow/` | 分工明确的导演流程、执行与接续规则、既有模板及按需案例 |
| `memories/seedance_workflow/projects/` | 当前状态入口、稳定设定、真实资产、采用索引及可追溯历史 |
| `packaging/`、`releases/` | 供团队使用的核心学习包及发布记录 |
| `Skill/`、`团队专项SOP/` | 保留的社区资料与团队文档，非默认AI规则入口 |

## GitHub备份方式

2026-10-10核对本仓库为公开仓库。日常小修改在本地进行；仅在用户要求的大重构或里程碑备份时手动提交、推送，不设置自动同步。

- `pre-refactor-2026-10-03`：重构前原样基线，包含原README和原规则。
- `backup-v1.0.0`：基线加简短README、版本说明及临时文件忽略配置；尚未重构。
- 完整原目录快照与SHA-256校验文件保存在对应GitHub Release中；快照在初始化Git及修改说明文件之前生成。

此前完整备份版本保留当时的规则、历史项目、正式素材、旧提示词和发行包；此为历史范围，现行V3公开提交仅限下文的核心白名单，不追加私有项目。临时渲染与缓存只在历史完整快照，目录外素材、其他聊天和账号配置不在该备份范围。

本地重构在 `codex/seedance-workflow-refactor` 分支分阶段提交，原标签保留；验收记录见 [CHANGELOG.md](CHANGELOG.md)。需要恢复时，从相应标签或Release下载到新目录核对，保留现有工作目录。核心学习包的版本独立于本仓库备份版本。

V2前的恢复点为 `pre-refactor-v2-2026-10-03`，保留V1三次重构提交。V2按六步制作流程完善交接、导演权限、声音替换与时间对应；本轮备份使用工作分支及 `workflow-refactor-v2-2026-10-03`里程碑，不为备份合并主分支。临时验收样稿仅本机保存，核心结论进入CHANGELOG。


## 当前V3.6本地候选入口

日常目录`AIGC_Vedio_codex_V3`、开发分支`codex/director-v3-6`，基于已发布`core-v1.5.1`／提交631bb6a，以[AGENTS.md](AGENTS.md)为唯一入口。当前方案、音频及实际操作各查项目状态／索引，不覆盖原稿、V2或旧发布。

导演与声音规则沿用V3.5.1：完整输入、A／B／C协作、任务自主授权、强情绪与身体交锋、原句／声窗、整集额外6—10秒可剪素材、七栏、摄影和无BGM保留。既有稿开发网页操作不重拆集或重转音轨。[短启动词](NEW_PROJECT_CONVERSATION_PROMPT.md)可选择只交稿、原生填稿或指定延长准备。

[唯一网页技能](extensions/seedance-jumeng-operator/SKILL.md)现支持明确授权范围内的视频延长准备：核源卡／真实原生结果／目标位置，切延长模式、选视频片段区间、核视频槽与正文视频同源、保必要人物和关联场景图，设置2.5Pro／480P／新增秒数，正常保存与恢复。不点击生成、批量生成或付费提交，准备不等于自动生成。

实际两条延长分别接29.056和22.08秒原生源完整至末尾，各新增23秒；在源卡内独立延长草稿准备，无新卡／上传，原生全文与节点切回后逐字保持。全文、1视频＋5图片、模式／槽／区间重访保留，新增时长重访回5秒，恢复23后只认证当前同页正确；独立画幅控件、手工区间调整、生成回执、延长实片和同步仍未验。

V3.6候选包Core1.6.0只在本机准备，尚未远端发布或创建标签。本轮未包含新的GitHub发布授权；之前公开点[Core1.5.1](https://github.com/zengyies-ux/AIGC_Vedio_codex/releases/tag/core-v1.5.1)及旧main保持。匿名证据与待验见[本版说明](validation/director_v36.md)，真实网址／资源／正文／截图留私有项目。

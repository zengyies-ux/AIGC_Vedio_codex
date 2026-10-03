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

本仓库为私有备份仓库。日常小修改在本地进行；仅在用户要求的大重构或里程碑备份时手动提交、推送，不设置自动同步。

- `pre-refactor-2026-10-03`：重构前原样基线，包含原README和原规则。
- `backup-v1.0.0`：基线加简短README、版本说明及临时文件忽略配置；尚未重构。
- 完整原目录快照与SHA-256校验文件保存在对应GitHub Release中；快照在初始化Git及修改说明文件之前生成。

Git版本保留目录内的规则、历史项目、正式素材、旧版提示词和既有发行包；临时渲染目录与系统缓存不进入Git，但保存在完整快照中。项目目录外的素材引用、其他聊天记录与账号配置不在本备份范围内。

本地重构在 `codex/seedance-workflow-refactor` 分支分阶段提交，原标签保留；验收记录见 [CHANGELOG.md](CHANGELOG.md)。需要恢复时，从相应标签或Release下载到新目录核对，保留现有工作目录。核心学习包的版本独立于本仓库备份版本。

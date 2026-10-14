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

Git版本保留目录内的规则、历史项目、正式素材、旧版提示词和既有发行包；临时渲染目录与系统缓存不进入Git，但保存在完整快照中。项目目录外的素材引用、其他聊天记录与账号配置不在本备份范围内。

本地重构在 `codex/seedance-workflow-refactor` 分支分阶段提交，原标签保留；验收记录见 [CHANGELOG.md](CHANGELOG.md)。需要恢复时，从相应标签或Release下载到新目录核对，保留现有工作目录。核心学习包的版本独立于本仓库备份版本。

V2前的恢复点为 `pre-refactor-v2-2026-10-03`，保留V1三次重构提交。V2按六步制作流程完善交接、导演权限、声音替换与时间对应；本轮备份使用工作分支及 `workflow-refactor-v2-2026-10-03`里程碑，不为备份合并主分支。临时验收样稿仅本机保存，核心结论进入CHANGELOG。


## 当前V3.2试制入口

日常使用固定本机目录`AIGC_Vedio_codex_V3`、分支`codex/director-v3-2`，从这里开Local聊天。先读`AGENTS.md`，再按当前任务读项目状态及原始输入；原`AIGC_Vedio_codex`保留旧分支与已有修改，不双向同步。新聊天读取已落盘资料，不自动继承未保存对话。

默认完整剧本、目标集完整音轨、已有资产和可选想法；GPT连续提取、定位、核看、导演设计与分段。验证模式集中审核一次，确认后交七栏／逐镜正式提示词；已实现常规内部采用路径，启用仍等用户认可正常流程和实际效果并落盘。子智能体仅在用户授权后可选，单智能体也能完成。

预算和素材必需性分别由[声音与时间](memories/seedance_workflow/execution_rules.md#sound-and-time)、[参考规则](memories/seedance_workflow/execution_rules.md#references)唯一维护。完整剧情、原句、人物目的、行动与回应、强情绪、摄影、接续及精准返修保留。新窗口独立重测按[恢复范围](memories/seedance_workflow/continuity_and_review.md#task-recovery)从原始输入重新设计，旧未采用时轴与补图结论不带入。

公开下载：[Core 1.2.0 / V3.2试制版](https://github.com/zengyies-ux/AIGC_Vedio_codex/releases/tag/core-v1.2.0)或[发行目录](releases/README.md)。当前[匿名验收](validation/director_v32.md)只证明规则、工具及入口静态/模拟检查；独立新窗口和实际成片、对白同步、返修／后期负担仍待用户验证，不宣称质量提升。网页独立技能已提炼，未合入、未完整实测，本轮不接入或操作网页。

本次只公开核心、必要工具、通用启动词、匿名验收及发行物；私有项目、音视频、模型、词表、缓存、会话、含本机路径的计划和启动词留本地。旧版本和标签保留，main仍是旧备份点，不作为V3.2入口。

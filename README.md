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


## 导演V3与可选工具

V3以现行核心基线 `a32c0a6fc82be123a455e7757c1c14c8b31987c8` 建立独立分支 `codex/director-v3`，原目录与其他窗口不切换。导演采用“定观看重点→排自然场面→落镜头与声音”，继承已审阶段，镜数／镜长用于诊断，指定画面与局部返修范围继续保留。实际文字验收与限制见[本轮验证说明](validation/director_v3.md)。

- **导演核心：**现有六阶段、七栏、强情绪、接续及精准返修继续使用；未生成新成片，不宣称质量提升已证实。
- **本机音频定位：**[可选工具](tools/local_audio/README.md)单独安装和运行。按用户最新确认的[时间采用标准](memories/seedance_workflow/execution_rules.md#sound-and-time)，完整对应且与用户参考时码各点相差不超过2秒可通过使用；无参考时由Codex整理候选位置，用户一次整体确认或指出局部问题；对应不完整只处理受影响项。实际听检状态另记。模型、音频、词表、短段与缓存只留本机。
- **网页扩展：**由另一个工作树／分支维护，复用同一核心提交，当前核心包不含网页自动填稿扩展；不要建立第二套导演规则。

日常制作使用独立本机目录 `AIGC_Vedio_codex_V3`，从这个目录开Local聊天，先读本目录的 `AGENTS.md` 和当前项目状态。原 `AIGC_Vedio_codex` 保留为原有工作区及修改基线；新聊天不会自动继承本聊天未落盘的内容。新项目继续使用[启动词](NEW_PROJECT_CONVERSATION_PROMPT.md)，只有一套现行核心入口。

收尾发布为 `1.1.1`；`core-v1.1.1` 所指的完整提交同时是未来自动化复用的兼容提交。已发布 `core-v1.1.0` 及其ZIP保留，默认 `main` 不作为V3入口。本轮不接入网页操作。

公开下载使用 `core-v1.1.1` 核心标签或[干净核心包](releases/README.md)，默认 `main` 仍为原备份点。本轮仅新增核心、脚本及匿名验证说明，本次项目剧本／制作资料未加入公开提交；已有仓库历史保持不变。

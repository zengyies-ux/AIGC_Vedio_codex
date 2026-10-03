# 仓库备份版本记录

本文件记录整个工作仓库的备份里程碑；核心学习包的版本继续由 `packaging/CHANGELOG.md` 管理。

## 2026-10-03 — 工作流重构与本地验收

按用户提供的重构指导完成三阶段本地修改。执行前工作区干净；完整读取磁盘现行核心文件，校验原备份后建立 `codex/seedance-workflow-refactor`。没有追溯旧聊天。

### 修改范围

- 收紧 `AGENTS.md`，改为按任务定位；新项目开场只保留目标、入口和本次输入。导演判断、执行细则、接续／审片、模板及模型证据分别归位，以稳定锚点互相引用。
- 保留七栏正文、制作设置、角色映射、逐镜粒度、声音原文、无BGM、摄影基线及动物表演方法。镜数集中到执行规则，生成约束集中到接续规则，方法库保留具体例子与适用条件。
- 整理《10美元》《网恋亿万富翁》《黑帮继承人》三个活动项目：状态只留当前任务，概览留固定设定，索引区分文字版本与实际采用，旧过程追加到已有历史／复盘。六个归档项目未改写；旧提示词、剧本、素材与已有证据保持原样。
- 修清原旁白、生成局部与最终剪辑三时轴：原起点17秒、前段生成19秒，原24.5秒对白先算局部7.5秒；最终剪辑位置由实际保留长度决定。
- 独立审查发现并补回两处迁移遗漏：依赖同一动作／遮挡的特殊转场优先同任务生成；普通镜头时码用于节奏分配，不作毫秒机械控制，明确锁定节点仍遵守。
- 同步README和核心包白名单，使新导航包含的动物规则、学习说明能够随核心包进入；仅验证临时目录，没有生成新发行包、改版本或上传GitHub。

### 固定入口读取量

| 对照范围 | 重构前UTF-8字节 | 重构后UTF-8字节 | 减少 |
|---|---:|---:|---:|
| AGENTS入口 | 42,153 | 10,029 | 76.2% |
| 正式落稿入口：AGENTS＋模板 | 63,320 | 19,665 | 68.9% |
| 《10美元》恢复入口：AGENTS＋项目索引＋状态＋提示词索引 | 68,815 | 22,224 | 67.7% |

这些数字只比较相同入口文件，不包含剧本、资产、采用正文或按需专项，也不是实际总上下文、token数或耗时测量。AGENTS低于本次10 KiB预算。

### 核心能力的维护位置

| 能力 | 当前位置 |
|---|---|
| 剧本解读与分段判断 | [director_os.md](memories/seedance_workflow/director_os.md#script-design) |
| 主动导演、强情绪与动物表演 | [execution_rules.md](memories/seedance_workflow/execution_rules.md#performance)、[director_patterns.md](memories/seedance_workflow/director_patterns.md#selection)、[animal_city_motion.md](memories/seedance_workflow/animal_city_motion.md) |
| Seedance执行与证据边界 | [execution_rules.md](memories/seedance_workflow/execution_rules.md#references)、[model_behavior.md](memories/seedance_workflow/model_behavior.md#evidence-boundaries) |
| 分段接续、实际源片与制作约束 | [continuity_and_review.md](memories/seedance_workflow/continuity_and_review.md#generation-choice) |
| 正式提示词骨架与一次检查 | [prompt_template.md](memories/seedance_workflow/prompt_template.md) |
| 精准返修与审片证据 | [continuity_and_review.md](memories/seedance_workflow/continuity_and_review.md#review-and-repair)、[field_lessons.md](memories/seedance_workflow/field_lessons.md) |

### 实际验收

三条独立上下文分别执行规则审查、EP10全链文字回放及其他三个案例；实施方复核结果与样稿。

| 案例 | 实际文字结果 |
|---|---|
| 《10美元》EP10 | 保留原文后追加导演补充，核对57秒三段并交完整20／20／17秒、13／12／10镜样稿；保留空舞伴→崩溃→等待→完整抱起→上楼和三处记忆点。历史约90分未赋予新样稿。 |
| 黑豹EP13片段02 | 找回V1动作基础；程序核对前8镜相同，保留0—15秒，只写镜09—15替换样稿；识别实际前25秒为止损可用，未把最新失败版当基线。 |
| 飞龙EP23 | 采用稿对白局部7.5—11秒，与原时轴一致；按记录的实际坐稳、右爪及药瓶末态接戏，识别原生源一次延长，未用计划末态或截图替代。 |
| 《10美元》新窗口恢复 | 仅靠磁盘找到EP09／12／13三处补镜、10／6／15秒和实际EP12原生源；正确识别三个补镜均仅文字完成、未生成未验收。 |

备份ZIP的705文件逐个匹配SHA-256清单；核心／入口及活动项目入口399个本地链接与锚点有效，七栏字段顺序和原编号章节保留，Git空白检查通过，受保护内容零改动。临时核心包目录18份Markdown验证通过。独立规则审查的两项发现均已修复，未解决发现0。

测试稿、逐文件读取记录和JSON留在被忽略的 `.codex_tmp/refactor_acceptance/`，只作本次验收，不是新生产稿或日常入口。未生成视频、未听检、未重新审片；声画同步、真实受力／反射／接缝、新稿质量与最终剪辑均未验证。平台规格仍保留原核验日期，未冒充本次重新核验。

### 本地提交与恢复

- `e4ec644`：入口与核心归并。
- `958b27f`：活动项目当前依据与历史分离。
- 两项审查修正与本记录在后续验收提交中保存，可用 `git log`定位。
- `backup-v1.0.0`所指提交仍为 `01036d8a88638ece7ac53a69dfa55318bb8f5d71`；原样标签 `pre-refactor-2026-10-03`仍指向 `17977b0792b2345b46c6d9136e19955ca40f0f23`。原ZIP及校验清单保留；外部媒体依旧只保留路径引用。

## backup-v1.0.0 — 2026-10-03

用途：大重构前保存可恢复基线。本版尚未实施工作流重构。

- 原样基线标签：`pre-refactor-2026-10-03`。
- 原样提交：`17977b0792b2345b46c6d9136e19955ca40f0f23`。
- 保留九个项目目录、规则、模板、源文件、正式素材、全部历史提示词、复盘、社区资料及团队SOP。
- 简化根README，增加本版本说明；忽略临时渲染目录，并明确保留已有发行压缩包。
- 未修改 `AGENTS.md`、工作流规则、各项目制作内容与提示词。
- 日常修改留在本地；大重构或里程碑备份按用户要求手动上传，无自动同步。

完整原目录快照：`AIGC_Vedio_codex_pre-refactor_2026-10-03.zip`，共705个文件，压缩前203,307,279字节。逐文件SHA-256清单及压缩包校验文件随Release保存，已逐文件读取压缩包验证。

压缩包SHA-256：

```text
65dd41ccc65deb97d42686712aba6d137a96281d31ad12746661e9074d9fefc2
```

备份范围为本项目目录实际文件；外部路径仅保留引用，不包含目录外素材或聊天历史。

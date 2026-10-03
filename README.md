# Seedance 视频提示词工作流

这是一套给 Codex 使用的 Seedance 短剧创作知识包。核心规则不是提示词词典，也不携带某一部剧的剧情上下文；各项目目录单独保存制作事实与历史，只有用户明确继续对应项目时才读取。它帮助 Codex 把当前剧本片段、用户想法和参考素材转译成可执行的视频生成提示词。

## 最短工作方式

```text
用户给当前片段、想法和素材
→ Codex读懂事件、台词对象、人物所知与观众感受
→ 把剧情压成一个清楚的可拍事件
→ 选择能承载它的功能场景，核对空间主轴、锚点与实际状态
→ 把人物目的或环境运动变成有来路的行动、对方回应和最终落点
→ 选择情绪高点的记忆画面与拍法，组织快节奏镜头链
→ 用语义职责绑定 @图片
→ 输出本次自包含提示词
→ 根据成片反馈修正
```

## 七条核心认识

1. **每次生成没有上下文。** Seedance只知道本次提示词和本次素材。
2. **场景图是有功能的空间，不是背景。** 先确定这处空间要承载哪项叙事或视觉任务，再选择入口、动作锚点、路线、人物主轴与光源清楚的拍摄区；大地点可按剧情拆成多个简单拍摄区，确有必要时再分别准备场景资产。
3. **镜头编号就是切点。** 连续动作被错误拆开，会重置姿势、方向和惯性。
4. **说话、听话和无台词都在表演。** 对白需要对象、目的和台词内的情绪变化；直接听者与重要关系人需要在触发后给出可见回应，不能等轮到台词才“活过来”。
5. **更多描述不等于更强控制。** 剧情动作、空间关系、声音时序和参考职责永远高于修饰词。
6. **旁白短剧有真实切镜密度。** 海外9:16旁白短剧每个编号镜头原则上不超过3秒；只有真实剪辑切点才计为新镜头，推拉摇移、变焦和移焦仍属于当前单镜。默认硬切，可在少量切点设计清楚的遮挡或甩镜转场。一个事件跨过多个意义节拍时，还要更新信息、关系、行动、空间或环境结果；只换角度重复同一表面动作不算推进。
7. **分段是在给抽卡风险分仓。** 每段有一个主情绪命题和一个主要复杂执行核心；以动作闭环、稳定边界和失败后的返抽范围比较候选段数，不把段数少直接等同省积分。

## 文件职责

| 职责 | 文件 |
|---|---|
| 入口与协作边界 | `AGENTS.md` |
| 从剧本到画面的判断流程 | `memories/seedance_workflow/director_os.md` |
| Seedance理解方式、Fast与2.5边界 | `memories/seedance_workflow/model_behavior.md` |
| 素材、动作、声音、光线和执行规则 | `memories/seedance_workflow/execution_rules.md` |
| 已验证的可复制提示词骨架 | `memories/seedance_workflow/prompt_template.md` |
| 空间、动态站位与成片复盘 | `memories/seedance_workflow/continuity_and_review.md` |
| 构图、转场、冲突与对白表演接力、拆段及情绪特效案例 | `memories/seedance_workflow/director_patterns.md` |
| 真人大量对白剧入口（待建设） | `memories/seedance_workflow/live_action_dialogue_drama.md` |
| 匿名失败案例与验证结论 | `memories/seedance_workflow/field_lessons.md` |
| 新项目结构 | `memories/seedance_workflow/projects/PROJECT_TEMPLATE.md` |
| 当前2.5技术摘要与官方来源 | `memories/seedance_workflow/seedance_2_5_technical_notes.md` |

具体任务的读取顺序统一见 `AGENTS.md` 第4节，来源冲突顺序见其第3节。本页说明文件职责，不增加另一套必读清单。先理解剧情并形成连续画面，再选择切点、机位与记忆画面，最后检查镜数、时码、素材和文本执行；这些检查不能代替情绪与观看效果判断。

## 目录

```text
AIGC_Vedio_codex/
├── AGENTS.md
├── README.md
├── PROJECT_HISTORY.md
├── Skill/seedance2-skill-main/       # 2.0社区历史资料，原样保留，不默认读取
└── memories/seedance_workflow/
    ├── director_os.md
    ├── model_behavior.md
    ├── seedance_2_5_technical_notes.md
    ├── execution_rules.md
    ├── prompt_template.md
    ├── continuity_and_review.md
    ├── director_patterns.md
    ├── live_action_dialogue_drama.md
    ├── field_lessons.md
    └── projects/
        ├── INDEX.md
        └── PROJECT_TEMPLATE.md
```

## 使用边界

- 先遵守用户当次要求和实际平台能力，再参考本仓库规则。
- 当前默认Seedance 2.5，主要使用公司平台的全能参考与视频延长。当前不上传首尾帧或成片截图作为生成参考，只保留内部审片用途。新镜头方法直接融入正式设计，不默认增加白模资产或技巧试拍版本。
- 官方资料中的数量、时长和产品限制可能变化；任务涉及未确认限制时核对当次平台，已确认的制作基线可沿用，不为普通构思反复打开上传页。
- 历史经验用于降低风险，不用于把每条提示词写成同一种格式或同一组镜头。
- 旁白节奏由Codex内部对齐；给Seedance的正文只写需要生成的画面与声音，不附旁白原文及校准说明。
- 剧情手机消息与文件短句可直接指定内容并由Seedance生成，不默认安排后期贴图。字幕、倒放等按本次需求决定；当前禁止生成或主动添加任何BGM，短促非旋律音效与对白、环境声、动作声按设计使用。

## 当前项目依据

- `AGENTS.md`是唯一协作入口；`execution_rules.md`维护通用执行细则，`prompt_template.md`负责输出骨架。导演流程、模式与复盘提供判断依据，不另建一套相互竞争的规则。
- 项目概览保存固定设定；`production_state.md`唯一维护当前进度、审核与待修项；素材清单保存已提供、已备好、待补及停用状态。
- `prompts/INDEX.md`指向各段当前文本并注明实际采用情况；最新文件名不等于最新成片，制作完成也不等于审定。
- 历史制作记录、早期地图与旧提示词按需追溯，不作为默认执行依据。最新用户确认优先；遇到未确认事实不自行补成已完成。

## 打包给其他 Codex

若目的是让另一位 Codex 学习通用工作流，制作“干净核心学习包”：保留根目录的 `AGENTS.md`、专用核心包`README.md`与`ROADMAP.md`，以及 `memories/seedance_workflow/` 下的核心规则、技术摘要和 `projects/PROJECT_TEMPLATE.md`；另生成一个空白`projects/INDEX.md`，供新项目登记。历史项目目录、`PROJECT_HISTORY.md`、历史审片、素材和提示词全部排除。`Skill/seedance2-skill-main/`是旧2.0社区资料，`团队专项SOP/`是尚待单独修订的人类组员材料，二者也不进入Codex核心学习包。

核心学习包由`packaging/build_core_package.py`按白名单生成，只在用户明确要求更新时手动运行，不设自动同步。若目的是完整迁移制作记录，则另行保留整个 `projects/`、素材清单、源文件说明、提示词和复盘。无论哪种包，都排除 `tmp/`、`.DS_Store`、`__MACOSX/`、缓存、渲染预览和已经生成的压缩包。项目历史正文中残留的旧电脑绝对路径只作过程证据，不能据此认定文件可用；活动入口与索引必须改成包内相对链接或只记录外部文件名。打包后从解压目录运行链接、绝对路径与文件清单检查。

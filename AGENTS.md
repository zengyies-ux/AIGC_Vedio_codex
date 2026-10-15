# Seedance 视频提示词协作工作流

> 本仓库唯一规则入口。以本轮输入建立依据，按任务读取；不默认读历史项目、旧聊天或整库。

## 1. 目标与工作顺序

把剧本、可选想法和真实素材转成自然、可执行的视频提示词：忠实事件，人物、空间、动作、道具与声音连续，情绪与记忆点可读。

输入：完整剧本、目标集数、该集完整MP3/WAV、已有资产图、可选想法；不要求用户制作单集Word、绿标、人工时码或逐镜画面。连续前置：全剧通读/目标集提取 → GPT定说听人、本机定位/核看资产 → 完整原轨覆盖＋可剪余量下解读、设计/分段 → 内部核查 → 提示词 → 返修。见[导演流程](memories/seedance_workflow/director_os.md#workflow-stages)。

默认验证模式：解读、分段/候选位置一次整体审核后出正式稿，不追加审批。用户明确授权当集自主制作时，在该范围内部核查后直接出稿并落盘授权，不因升级失效，也不据此启用全局常规模式。用户认可流程/效果并落盘启用常规模式后，内部核查采用出稿；沉默、文档验收或发布不切模式。资产缺失、输入冲突或无法内解问题才问，少确认不省设计。

当前V3.5试制版。先据剧本设计场面与力度，再转译镜头／声音，最后核技术。有明确人物冲突时，主动设计有力度的肢体对抗，并拍清对手、在场者及环境的因果反应；细则唯一见[冲突场面](memories/seedance_workflow/director_os.md#conflict-staging)。声音连续，按行动与回应切镜；长台词跨镜，见[声音跨镜](memories/seedance_workflow/execution_rules.md#audio-shot-independence)。

同类完整单集默认A剧本／冲突、B声音／时间、C资产／空间三名GPT-6.1-sol high协作，主控统一设计与采用；小修或用户指定单智能体不凑代理，容量不可用不无限重试，见[协作职责](memories/seedance_workflow/director_os.md#collaboration)。

## 2. 用户决定与协作边界

依据优先级：

1. 用户本轮最新明确要求与纠正。
2. 用户当前采用的剧本、拆解、时码、素材与真实成片反馈。
3. 对应项目当前状态、固定设定、资产清单及提示词采用索引。
4. 本仓库核心流程、执行规则与模板。
5. 匿名案例、历史项目、旧提示词及旧版模型资料。

用户的剧情、动作、镜头感与审美优先。新要求替换失效决定并同步状态；当前文件不能解答具体缺失/冲突时才短问，旧聊天只追溯该决定。

用户见解优先；未写见解即委托Codex主动解读和导演。可补局部动作、场景角度、辅助场景与道具，随整体方案评估，不逐件审批。完整权限见[导演边界](memories/seedance_workflow/director_os.md#creative-boundaries)。

保留事件、关系、动机、知情顺序、台词与结果；改变因果或新增秘密/关系、后续事件须确认。缺素材不取消好方案，可继续解读规划；先核看现有素材，按[必需性](memories/seedance_workflow/execution_rules.md#references)判断，只为必要身份、场所或关键识别依据请求最小补图；普通物件可描述。用户补齐后核看，不默认生成图或写图提示词；只阻断受影响绑定，不伪造编号，无关工作继续。

“简化”只去重复、未采用推理和过细描述，保留人物、路人、事件、镜数、对白、节奏与强度；用户点名删除的画面任务才移除。

## 3. 新窗口与压缩后的恢复

按“最新输入→项目状态→采用文件/素材→所需规则”恢复。

- 继续指定项目：从[项目索引](memories/seedance_workflow/projects/INDEX.md)定位，读 `production_state.md` 中工作模式、当前输入与采用来源；按链接读当前文本、`prompts/INDEX.md`及必要资产。固定设定按需读 `project_overview.md`。
- 新项目：从[项目模板](memories/seedance_workflow/projects/PROJECT_TEMPLATE.md)建立独立目录；不带入旧角色、剧情和图片编号。
- 继续继承采用稿，返修保有效部分；独立重测从原始输入设计，不继承旧未采用时轴、预算或补图。新结果独立保存，采用后切入口，见[恢复规则](memories/seedance_workflow/continuity_and_review.md#task-recovery)。接续查实际合格源，不用计划终态代填。
- 只处理指定范围，已读未变规则不重载。

## 4. 按阶段读取

按阶段读取，README仅作地图。

| 当前任务 | 本次读取路径 |
|---|---|
| 新集前置设计／补写初解 | 完整剧本与目标集、音频、实际资产 → [剧本解读](memories/seedance_workflow/director_os.md#script-design)。GPT核定原句和归属、实际定位并核看，连续完成解读与分段。旧Word/批注/绿标有则兼容保留，不要求补做；不默认渲染或全片听检。 |
| 整集拆段／重拆 | 解读、定位与[预算](memories/seedance_workflow/execution_rules.md#sound-and-time) → [分段](memories/seedance_workflow/director_os.md#segmentation)和[生成方式](memories/seedance_workflow/continuity_and_review.md#generation-choice)。先预算后段数，按事件、情绪、切点与依赖设计；验证模式随整体方案一次审核。 |
| 新设计／重排镜头 | [功能场景](memories/seedance_workflow/director_os.md#functional-scenes)、[情绪节奏](memories/seedance_workflow/director_os.md#emotion-and-rhythm)、[镜头选择](memories/seedance_workflow/director_os.md#shot-language)；需要拍法才检索[方法库](memories/seedance_workflow/director_patterns.md)。 |
| 正式提示词 | 当前模式下采用的解读／分段、音频定位与实际资产 → [既有模板](memories/seedance_workflow/prompt_template.md)。接续读对应接续章节；执行疑难只查相应章节，不重新通读导演流程。 |
| 多人对白／高情绪 | [表演与动作](memories/seedance_workflow/execution_rules.md#performance)、[空间关系](memories/seedance_workflow/execution_rules.md#space)；按刺激、说者、听者和最相关关系人接力，不为避险删表演。 |
| 跨段／复杂同场接续 | [生成方式](memories/seedance_workflow/continuity_and_review.md#generation-choice)、[实际源片与末态](memories/seedance_workflow/continuity_and_review.md#source-state)。必要源合格后接续，无依赖任务可并发。 |
| 局部返修 | 反馈、可用基线与接缝 → [审片与精准返修](memories/seedance_workflow/continuity_and_review.md#review-and-repair)。文字足够就直接修，改镜头才查拍法，不默认全片审看。 |
| 表现力不足／画面重复 | [情绪节奏](memories/seedance_workflow/director_os.md#emotion-and-rhythm)与方法库对应任务；先找变化和直接回应，再选拍法。 |

| 执行疑难／专项 | 精确入口 |
|---|---|
| 素材与参考绑定 | [参考与素材](memories/seedance_workflow/execution_rules.md#references) |
| 镜数、真实切点、构图与运镜 | [镜头执行](memories/seedance_workflow/execution_rules.md#shots) |
| 声音定位、现场对白替换、预算与三时轴 | [声音与时间](memories/seedance_workflow/execution_rules.md#sound-and-time) |
| 光线、设备基线、成像与运动可读性 | [摄影执行](memories/seedance_workflow/execution_rules.md#cinematography) |
| 拟人动物 | [动物表演](memories/seedance_workflow/animal_city_motion.md)，真人不加载 |
| 真人大量对白剧 | [专项入口](memories/seedance_workflow/live_action_dialogue_drama.md)，不机械套用旁白短剧切镜密度 |
| 首次建立模型边界／重复失败 | [证据与版本边界](memories/seedance_workflow/model_behavior.md#evidence-boundaries)；失败现象按需检索[field_lessons.md](memories/seedance_workflow/field_lessons.md) |
| 当次平台规格未确认 | [2.5技术摘要](memories/seedance_workflow/seedance_2_5_technical_notes.md)，不足时核对当前平台，普通构思不反复查规格 |

## 5. 生成与交付底线

每次Seedance只读本次正文和上传素材，正文自包含、可见可听可执行。未来计划、分析、旁白对齐与制作接力留项目文件。人物轻绑定、场景强锚定、关键道具按需控制，参考区和正文用同一固定简名。

当前用公司平台Seedance 2.5全能参考和延长；不默认Fast、白模、绿幕或试拍。一次延长、约55秒预留转换、固定区域≤60秒、截图仅内审维护于[接续规则](memories/seedance_workflow/continuity_and_review.md#generation-choice)，是当前制作约束。用户俯视站位图按[空间规则](memories/seedance_workflow/execution_rules.md#space)使用，不自行增制图。

按[模板](memories/seedance_workflow/prompt_template.md)保留制作设置、角色映射、七栏/可选栏、逐镜、摄影、现场对白、目标语言和无BGM。按已设计场面分别写连续声音和真实切镜，再交叉核对；不将逐句音频区间复制成逐镜区间。原轨含旁白与台词：现场对白替换原台词，旁白后期编排，不重复加算对白。完整覆盖实际原轨，整集生成素材额外保留6—10秒可剪余量（至少6秒，取整计入，不是每段加）；当集最新额度与锁定节点仍有效，计算与分配只按[唯一时间政策](memories/seedance_workflow/execution_rules.md#sound-and-time)处理。时间对应留分段／制作设置，正文不放后期调度。

写入项目`prompts/`并更新索引；当前正式稿、真实素材、方式、整数时长、可执行条件及实际回执沿用[交付与续做](memories/seedance_workflow/continuity_and_review.md#execution-handoff)分工，供用户及网页填稿层消费。用户指定网页填写时才读[剧梦填稿技能](extensions/seedance-jumeng-operator/SKILL.md)：V3.5只填稿、真实图片／已就绪视频绑定及参数回读，不点击生成、不付费提交、不实操完整延长选源／区间；后者留V3.6。聊天默认给链接、变化、缺项与必要风险，用户要全文或未建项目才内联。审核先修画面，台词本身被拒才交用户决定，不自行改词。

## 6. 状态与知识维护

`production_state.md`只维护任务与工作模式、输入版本、音频采用来源、方案认可、采用链接、必要实拍末态及未决事项；`project_overview.md`保存稳定设定；`assets/README.md`保存真实资产；`prompts/INDEX.md`保存当前文本与实际采用关系。旧过程进已有复盘并链接，不叠“最新”或每轮建快照/交接。满意、止损可用、仅文字完成、生成成功与未知须区分。

原剧本、素材、旧稿与失败证据不覆盖。反馈先修本项目，偏好留项目；有依据才更新唯一核心位置，用户新决定立即按范围执行。完整维护见[接续与反馈](memories/seedance_workflow/continuity_and_review.md#feedback-maintenance)。项目结束标明无活动任务，索引链接状态页。

`Skill/seedance2-skill-main/`、`团队专项SOP/`及历史项目不默认读；方法、官方能力、平台约束与反馈分别标来源。

# Seedance 视频提示词协作工作流

> 本仓库唯一规则入口。先以本轮用户输入建立当前依据，再按任务定位下列文件；不自动读取历史项目、旧聊天或整套方法库。

## 1. 目标与工作顺序

把当前剧本、用户想法和真实素材转成自然、好看、能被 Seedance 执行的视频提示词，同时做到：忠实事件；人物、空间、动作、道具和声音不穿帮；情绪变化与视觉记忆点清楚可读。

六步主线：通读 → 单集Word、批注、绿标时码与实际资产 → 解读审核 → 分段确认 → 提示词 → 返修。交接见[导演流程](memories/seedance_workflow/director_os.md#workflow-stages)；已确认阶段直接继续。

不穿帮与表现力在同一次设计中完成。解读先形成事实、所知、目的、因果和情绪，再落行为、回应、镜头与声音。已确认解读和分段后仍需具体导演设计与成稿核对，不机械复制、不重开整轮解读、不增导演卡。

## 2. 用户决定与协作边界

依据优先级：

1. 用户本轮最新明确要求与纠正。
2. 用户当前采用的剧本、拆解、时码、素材与真实成片反馈。
3. 对应项目当前状态、固定设定、资产清单及提示词采用索引。
4. 本仓库核心流程、执行规则与模板。
5. 匿名案例、历史项目、旧提示词及旧版模型资料。

用户的剧情理解、动作顺序、镜头感与审美优先。新要求替换失效决定并同步状态，不混写冲突版本。具体决定缺失或实质冲突且当前文件不能解答时，才问一个短问题；旧聊天只追溯该缺失决定。

用户见解优先；未写见解即委托Codex主动解读和导演。可补充局部动作、场景角度、辅助场景与道具，在解读方案中随单集审核统一评估，不逐件审批。压迫要有可见恶意与承受反应，强情绪不能只写标签。完整权限见[导演边界](memories/seedance_workflow/director_os.md#creative-boundaries)。

保留关键事件、关系、动机、知情顺序、台词与结果；实质改变因果、制造新秘密／关系或后续须承认的事件时，指出变化并确认。缺素材不取消好方案，可继续解读规划；简述所需素材、用途和结构／状态，由用户补齐，不默认生成图或写图片提示词。受影响正式稿须等真实素材补齐核看再绑定，不伪造编号；无关工作继续。

“简化”只去重复、未采用推理和过细描述，保留人物、路人、事件、镜数、对白、节奏与强度；用户点名删除的画面任务才移除。

## 3. 新窗口与压缩后的恢复

按“用户最新输入 → 对应项目当前状态 → 本次采用文件与素材 → 所需规则”恢复，不只凭会话摘要或旧时轴开写。

- 继续指定项目：从[项目索引](memories/seedance_workflow/projects/INDEX.md)定位，先读该项目 `production_state.md`；按其中链接读当前采用的拆解／分段／提示词、`prompts/INDEX.md`及必要资产。固定设定按需读 `project_overview.md`。
- 新项目：从[项目模板](memories/seedance_workflow/projects/PROJECT_TEMPLATE.md)建立独立目录；不带入旧角色、剧情和图片编号。
- 缺项先查本项目；接续核对实际合格源片，不用计划终态代填未知实拍。
- 只处理指定范围。已读且未变规则不重复全文加载；事件、所知、对象、空间、情绪、时码和素材明确即可工作。

## 4. 按阶段读取

按阶段定位下列章节，README仅作地图。

| 当前任务 | 本次读取路径 |
|---|---|
| 代拆剧本／补写用户初解 | Word、批注、绿标时码及核看资产 → [剧本解读](memories/seedance_workflow/director_os.md#script-design)。保留原文与批注、追加导演补充，交Markdown审核稿及简短素材缺项；默认不制Word、渲染或全音轨听检，不提前拆段。 |
| 整集拆段／重拆 | 已审解读 → [分段判断与交接表](memories/seedance_workflow/director_os.md#segmentation)；接续查[生成方式](memories/seedance_workflow/continuity_and_review.md#generation-choice)。按完整事件、情绪兑现、声音、落稳切点与依赖选择，交用户确认。 |
| 新设计／重排镜头 | [功能场景](memories/seedance_workflow/director_os.md#functional-scenes)、[情绪节奏](memories/seedance_workflow/director_os.md#emotion-and-rhythm)、[镜头选择](memories/seedance_workflow/director_os.md#shot-language)；需要拍法才检索[方法库](memories/seedance_workflow/director_patterns.md)。 |
| 正式提示词 | 采用拆解／分段与资产 → [既有模板](memories/seedance_workflow/prompt_template.md)。接续读对应接续章节；执行疑难只查相应章节，不重新通读导演流程。 |
| 多人对白／高情绪动作 | [表演与动作](memories/seedance_workflow/execution_rules.md#performance)、[空间关系](memories/seedance_workflow/execution_rules.md#space)；按刺激、说话者、直接听者及最相关关系人安排接力，不能为避险先删表演。 |
| 跨段／复杂同场接续 | [生成方式](memories/seedance_workflow/continuity_and_review.md#generation-choice)、[实际源片与末态](memories/seedance_workflow/continuity_and_review.md#source-state)。等待必要源片合格；无依赖任务可以并发。 |
| 局部返修 | 用户反馈、已知可用基线及受影响接缝 → [审片与精准返修](memories/seedance_workflow/continuity_and_review.md#review-and-repair)。文字足以定位时直接修，不默认打开全部视频；改镜头才查对应拍法。 |
| 表现力不足／画面重复 | [情绪节奏](memories/seedance_workflow/director_os.md#emotion-and-rhythm)与方法库对应任务；先找人物变化和直接回应是否入镜，再选择有效拍法。 |

| 执行疑难／专项 | 精确入口 |
|---|---|
| 素材与参考绑定 | [参考与素材](memories/seedance_workflow/execution_rules.md#references) |
| 镜数、真实切点、构图与运镜 | [镜头执行](memories/seedance_workflow/execution_rules.md#shots) |
| 原音轨、绿标对白替换、主动加时与三时轴 | [声音与时间](memories/seedance_workflow/execution_rules.md#sound-and-time) |
| 光线、设备基线、成像与运动可读性 | [摄影执行](memories/seedance_workflow/execution_rules.md#cinematography) |
| 拟人动物 | [动物表演](memories/seedance_workflow/animal_city_motion.md)，真人不加载 |
| 真人大量对白剧 | [专项入口](memories/seedance_workflow/live_action_dialogue_drama.md)，不机械套用旁白短剧切镜密度 |
| 首次建立模型边界／重复失败 | [证据与版本边界](memories/seedance_workflow/model_behavior.md#evidence-boundaries)；失败现象按需检索[field_lessons.md](memories/seedance_workflow/field_lessons.md) |
| 当次平台规格未确认 | [2.5技术摘要](memories/seedance_workflow/seedance_2_5_technical_notes.md)，不足时核对当前平台，普通构思不反复查规格 |

## 5. 生成与交付底线

每次 Seedance 生成只读取本次提示词和上传素材，正文必须自包含，只写当前可见、可听、可执行的内容。未来计划、导演分析、旁白对齐说明与制作接力留在项目文件。人物轻绑定、场景强锚定、关键道具按需控制；参考区用简短固定语义名称，正文直呼相同名称。

当前主要使用公司平台 Seedance 2.5全能参考与视频延长，不默认加Fast测试、白模、绿幕或额外试拍。一次延长限制、约55秒预留区域转换／固定区域不超过60秒、截图只内审等是当前制作约束，完整维护于[接续规则](memories/seedance_workflow/continuity_and_review.md#generation-choice)，不冒充模型物理上限。用户专门制作的俯视站位图按[空间规则](memories/seedance_workflow/execution_rules.md#space)使用，Codex不自行增加制图步骤。

正式提示词按[模板](memories/seedance_workflow/prompt_template.md)保留制作设置、角色映射、七栏与可选栏、逐镜粒度、摄影、现场对白、目标语言和无BGM。先写声音时序与镜头，再补参考及最短跨镜状态。原音轨含旁白与台词：绿标对白由生成现场声接替，旁白后期编排；完整表演／自然对白／情绪可主动加时，仅明确锁定节点为硬约束。时间对应写在分段／制作设置，正文不放后期调度，详见[执行声音](memories/seedance_workflow/execution_rules.md#sound-and-time)。

提示词写入项目 `prompts/`并更新索引；对话默认给文件链接、变化、素材缺口和必要风险。用户要求聊天全文或尚未建立项目时才内联。审核返修先调整画面；台词本身被明确拒绝才交由用户决定，不自行改词。

## 6. 状态与知识维护

`production_state.md`只维护当前任务、确认决定、采用链接、必要实拍末态与未决事项；`project_overview.md`保存稳定设定；`assets/README.md`保存真实资产；`prompts/INDEX.md`保存当前文本与实际采用关系。旧过程进入已有历史／复盘并链接，不在顶部叠加“最新”，不每轮另建快照或交接文件。满意、止损可用、仅文字完成、生成成功与未知须区分。

原剧本、素材、旧提示词和失败证据不覆盖。反馈先修本项目；项目偏好留本项目，有推广依据才更新唯一核心位置并替换旧说明，明确用户新决定立即按范围执行。完整维护见[接续与反馈](memories/seedance_workflow/continuity_and_review.md#feedback-maintenance)。项目结束标明无活动任务，索引链接状态页。

`Skill/seedance2-skill-main/`、`团队专项SOP/`和历史项目不属于默认规则入口；它们存在也不自动读取。核心方法、官方公开能力、平台用户约束和真实反馈分别标清来源。

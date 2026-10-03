# Seedance 视频提示词协作工作流

> 本仓库唯一规则入口。先以本轮用户输入建立当前依据，再按任务定位下列文件；不自动读取历史项目、旧聊天或整套方法库。

## 1. 目标与工作顺序

把当前剧本、用户想法和真实素材转成自然、好看、能被 Seedance 执行的视频提示词，同时做到：忠实事件；人物、空间、动作、道具和声音不穿帮；情绪变化与视觉记忆点清楚可读。

工作顺序：剧本事实与人物所知 → 目的、因果和主情绪 → 可拍事件与功能场景 → 行动、直接回应和新状态 → 镜头、节奏与声音 → 分段及生成依赖 → 按既有模板落稿 → 根据真实反馈精准返修。

不穿帮与表现力在同一次设计中完成，不能先让人物稳定站位，再靠质感词补表演。拆解可以做深；已确认拆解和分段之后，做一次精简转译与成稿核对，直接继续，不重开导演发散、不增加多层导演卡。

## 2. 用户决定与协作边界

依据优先级：

1. 用户本轮最新明确要求与纠正。
2. 用户当前采用的剧本、拆解、时码、素材与真实成片反馈。
3. 对应项目当前状态、固定设定、资产清单及提示词采用索引。
4. 本仓库核心流程、执行规则与模板。
5. 匿名案例、历史项目、旧提示词及旧版模型资料。

用户的剧情理解、动作顺序、镜头感和审美边界优先。新要求直接替换失效决定，并同步项目状态；不能把两个冲突版本一起塞进提示词。只有具体决定缺失、或两条用户要求仍实质冲突，且当前文件不能解答时，才问一个短而具体的问题；旧聊天只用于追溯该缺失决定。

Codex须在已确立剧情与素材范围内主动设计行为、直接反应、关系变化、构图、运镜、转场和现场声音。用户未逐处标注也要完成导演工作；压迫与施害须有可见恶意、承受者反应和后续反转铺垫，强情绪不能只写标签或微表情。既有情境中的局部表演，以及剧本已经确立、素材齐全且不增加事实的短暂回忆，可直接设计。

新增场景、人物、剧情性道具、未确立往事或小插曲，或改变关键事件、动机、人物关系、知情顺序与后续状态时，先提出具体用途、拍法和素材需求，用户确认且必要素材齐全后才进入可执行提示词。不擅改台词原文、顺序、对象与结果，不伪造素材编号。

用户要求“简化”时，删除重复解释、未采用推理和过细描述，保留已确认人物、路人、事件、镜数、对白、节奏与情绪强度；只有用户点名删除的画面任务才移除。

## 3. 新窗口与压缩后的恢复

按“用户最新输入 → 对应项目当前状态 → 本次采用文件与素材 → 所需规则”恢复，不只凭会话摘要或旧时轴开写。

- 继续指定项目：从[项目索引](memories/seedance_workflow/projects/INDEX.md)定位，先读该项目 `production_state.md`；按其中链接读当前采用的拆解／分段／提示词、`prompts/INDEX.md`及必要资产。固定设定按需读 `project_overview.md`。
- 新项目：从[项目模板](memories/seedance_workflow/projects/PROJECT_TEMPLATE.md)建立独立目录；不带入旧角色、剧情和图片编号。
- 缺项先查本项目；接续核对实际合格源片，不用计划终态代填未知实拍。
- 已确认阶段从下一步继续，只做用户指定范围。已读且未变化的规则不重复全文加载；读到事件、所知、对象、空间、情绪、时码和素材已明确即可工作。

## 4. 按阶段读取

按阶段定位下列章节，README仅作地图。

| 当前任务 | 本次读取路径 |
|---|---|
| 代拆剧本／补写用户初解 | 剧本、批注与素材 → [剧本解读](memories/seedance_workflow/director_os.md#script-design)。默认保留原文、英文台词、时码及批注，追加中文导演补充，先交Markdown审核稿；用户未要求时不制作Word、不渲染、不听检原音轨，也不提前拆生成片段。 |
| 整集拆段／重拆 | 已确认拆解 → [分段判断](memories/seedance_workflow/director_os.md#segmentation)；接续查[生成方式](memories/seedance_workflow/continuity_and_review.md#generation-choice)。按完整因果、情绪兑现、对白窗口、可重建切点及返抽范围选段数。 |
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
| 原旁白时间、生成局部时间、剪辑时间及对白 | [声音与三时轴](memories/seedance_workflow/execution_rules.md#sound-and-time) |
| 光线、设备基线、成像与运动可读性 | [摄影执行](memories/seedance_workflow/execution_rules.md#cinematography) |
| 拟人动物 | [动物表演](memories/seedance_workflow/animal_city_motion.md)，真人不加载 |
| 真人大量对白剧 | [专项入口](memories/seedance_workflow/live_action_dialogue_drama.md)，不机械套用旁白短剧切镜密度 |
| 首次建立模型边界／重复失败 | [证据与版本边界](memories/seedance_workflow/model_behavior.md#evidence-boundaries)；失败现象按需检索[field_lessons.md](memories/seedance_workflow/field_lessons.md) |
| 当次平台规格未确认 | [2.5技术摘要](memories/seedance_workflow/seedance_2_5_technical_notes.md)，不足时核对当前平台，普通构思不反复查规格 |

## 5. 生成与交付底线

每次 Seedance 生成只读取本次提示词和上传素材，正文必须自包含，只写当前可见、可听、可执行的内容。未来计划、导演分析、旁白对齐说明与制作接力留在项目文件。人物轻绑定、场景强锚定、关键道具按需控制；参考区用简短固定语义名称，正文直呼相同名称。

当前主要使用公司平台 Seedance 2.5全能参考与视频延长，不默认加Fast测试、白模、绿幕或额外试拍。一次延长限制、约55秒预留区域转换／固定区域不超过60秒、截图只内审等是当前制作约束，完整维护于[接续规则](memories/seedance_workflow/continuity_and_review.md#generation-choice)，不冒充模型物理上限。用户专门制作的俯视站位图按[空间规则](memories/seedance_workflow/execution_rules.md#space)使用，Codex不自行增加制图步骤。

正式提示词保留既有制作设置、角色映射、正文栏目顺序与逐镜粒度，按[模板](memories/seedance_workflow/prompt_template.md)输出；完整摄影基线、现场对白、目标语言、必要画面文字与全段无BGM等按执行规则保留。实际落稿先写声音时序和镜头，再补参考及最短跨镜状态。局部修错使用正向目标替换错误句并去重，保留有效动作链、情绪骨架、声音和摄影要求。

提示词写入项目 `prompts/`并更新索引；对话默认给文件链接、变化、素材缺口和必要风险。用户要求聊天全文或尚未建立项目时才内联。审核返修先调整画面；台词本身被明确拒绝才交由用户决定，不自行改词。

## 6. 状态与知识维护

`production_state.md`只维护当前任务、确认决定、采用链接、必要实拍末态与未决事项；`project_overview.md`保存稳定设定；`assets/README.md`保存真实资产；`prompts/INDEX.md`保存当前文本与实际采用关系。旧过程进入已有历史／复盘并链接，不在顶部叠加“最新”，不每轮另建快照或交接文件。满意、止损可用、仅文字完成、生成成功与未知须区分。

原剧本、素材、旧提示词和失败证据不覆盖。新反馈先入项目复盘；明确新决定立即按范围执行。可推广且有验证依据的经验只更新其唯一维护位置，替换旧说明并保留证据；单次观察不能写成官方机制。项目结束明确当前无活动任务，索引链接状态页，不重复维护全部进度。

`Skill/seedance2-skill-main/`、`团队专项SOP/`和历史项目不属于默认规则入口；它们存在也不自动读取。核心方法、官方公开能力、平台用户约束和真实反馈分别标清来源。

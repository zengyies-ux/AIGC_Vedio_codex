# Seedance 核心知识库地图

唯一规则入口是根目录[AGENTS.md](../../AGENTS.md)。本页用于定位文件，日常按阶段和具体问题读取，不默认通读方法库或项目历史。

| 文件 | 唯一维护职责与入口 |
|---|---|
| [director_os.md](director_os.md#script-design) | 决定场面与力度、集中采用、权限、功能场景与分段；明确冲突见[唯一细则](director_os.md#conflict-staging) |
| [execution_rules.md](execution_rules.md#sound-and-time) | 执行已选动作：素材、空间、受力、表演、声音定位／采用、预算与三时轴、切点和摄影 |
| [continuity_and_review.md](continuity_and_review.md) | 恢复、原生／延长、真实依赖、当前约束、审片返修及[交付与续做](continuity_and_review.md#execution-handoff) |
| [prompt_template.md](prompt_template.md) | 现有制作设置、角色映射、正文骨架与信息归属、一次成稿检查；具体方法链接到对应规则 |
| [model_behavior.md](model_behavior.md) | 模型理解及有证据范围的观察、版本边界；不把用户选择解释成模型机制 |
| [seedance_2_5_technical_notes.md](seedance_2_5_technical_notes.md) | 官方资料摘要、核对日期与当次平台适用边界；当前制作规则链接到维护处 |
| [director_patterns.md](director_patterns.md) | 按当前叙事与镜头任务检索方法、有效例子及适用条件 |
| [field_lessons.md](field_lessons.md) | 按失败现象检索匿名案例、原因假设、修法及验证状态 |
| [animal_city_motion.md](animal_city_motion.md) | 拟人动物耳、尾、毛发、爪与身体重心的主动表演；真人不加载 |
| [visual_language_learning_notes.md](visual_language_learning_notes.md) | 外部方法来源、采用／弃用项及待验证边界 |
| [live_action_dialogue_drama.md](live_action_dialogue_drama.md) | 待真实项目建设的对白剧入口，避免误套旁白短剧节奏 |
| [projects/INDEX.md](projects/INDEX.md) | 项目定位；当前事实进状态页，固定设定进概览，素材与采用关系各进对应索引 |

默认完整剧本＋目标集完整音频＋已有资产＋可选想法，GPT连续完成提取、定位、核看、导演设计与分段。本轮验证模式只集中审核一次，确认同时记录音频位置采用；用户实际认可流程与效果后才按落盘的常规模式内部核查采用、直接交正式提示词。旧Word／高亮／人工时码可兼容，不是新项目必填。

解读／分段读导演流程，正式提示词读采用设计、素材与模板，局部返修读用户反馈、可用基线及受影响接缝；遇到具体疑难才加读执行或方法章节。同一要求只在上表职责文件完整维护，其他文件保留短提示与链接。

反馈先修本项目，项目偏好留项目；可推广经验才更新唯一核心位置，用户明确新决定立即按范围执行，详见[反馈维护](continuity_and_review.md#feedback-maintenance)。单次观察、外部方法、官方宣称与平台／用户约束分别标明。旧2.0社区资料、团队SOP与项目历史不自动参与新任务。

[本机音频定位工具](../../tools/local_audio/README.md)服务目标集的实际定位与同音频缓存复用；归属由剧本语境核定。候选、内部核查、采用来源和实际听检分开；未实际播放不声称听检或精度通过，旧人工参考路径仍可兼容。当前能力与待实片验证边界见[路线图](../../ROADMAP.md)。

V3.4先据剧本设计[冲突场面](director_os.md#conflict-staging)，再按[声音跨镜](execution_rules.md#audio-shot-independence)转译镜头与连续声轨。可计算检查见[提示词检查工具](../../tools/prompt_review/README.md)，不接管拍法或认证画面质量；匿名验收及未验证边界见[本版说明](../../validation/director_v34.md)。

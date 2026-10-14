# Seedance Codex Workflow Core

供GPT执行Seedance短剧导演与提示词工作流的干净核心包，不含项目剧本、素材、制作记录或成片。1.4.0为V3.4试制版：先设计有力度的冲突交锋及因果反应，再转译镜头与声音；画外开口合法，排版工具不代选摄影。继承完整输入、音频定位与缓存、一次集中审核、原轨预算、三时轴、七栏、完整摄影与接续。制作设置、状态及提示索引直接承接未来网页执行，不新增中间导演系统。
## 使用方式

1. 新会话先读`AGENTS.md`。
2. 用户本轮最新要求、当前剧本、时码、素材和真实成片反馈始终优先。
3. 按任务读取`memories/seedance_workflow/`中的相关章节，不一次加载全部文件。
4. 新项目使用`memories/seedance_workflow/projects/PROJECT_TEMPLATE.md`建立目录，并登记到空白项目索引。
5. 完整提示词写入项目`prompts/`文件；聊天默认返回文件链接和必要说明。

## 包含内容

```text
AGENTS.md
README.md
ROADMAP.md
CHANGELOG.md
PACKAGE_INFO.md
memories/seedance_workflow/
├── README.md
├── director_os.md
├── model_behavior.md
├── seedance_2_5_technical_notes.md
├── execution_rules.md
├── prompt_template.md
├── continuity_and_review.md
├── director_patterns.md
├── animal_city_motion.md
├── visual_language_learning_notes.md
├── live_action_dialogue_drama.md
├── field_lessons.md
└── projects/
    ├── INDEX.md
    └── PROJECT_TEMPLATE.md
```

本机音频工具位于`tools/local_audio/`，当前已验证范围为Apple silicon Mac／英文MLX Whisper。模型、词表和短段留本机；默认调用已有工具定位，依赖/环境首次准备一次，后续复用同音轨缓存。模式、预算与采用依据查[执行规则](memories/seedance_workflow/execution_rules.md#sound-and-time)，必要资产查[参考规则](memories/seedance_workflow/execution_rules.md#references)，不重复写一套政策。

当前默认验证模式：解读、分段和音频候选一次整体审核后出正式提示词。已实现并测试常规内部采用路径，默认启用仍须用户认可正常流程与效果并落盘；沉默、工具估计或版本发布不启用。旧Word／绿标／人工参考可兼容，不成为正常输入前提。实际音频定位采用、用户方案认可、听检与成片评价分别记录。

日常以`AGENTS.md`为唯一入口，项目状态指向当前采用稿。V3.4试制发布点`core-v1.4.0`，规则及匿名文本验收见[本版说明](validation/director_v34.md)；独立新窗口、实片表现／对白同步和后期负担仍待用户正常制作。网页技能未合入，本轮未操作网页；实际表现力认可后再实测普通生成、一次真实延长、绑定回执与中断续做。历史V3.2发布及V3.3本地候选保留，历史说明不作为现行命令。
## 明确排除

- 所有历史与活动项目正文。
- `PROJECT_HISTORY.md`及项目纪念信息。
- 角色、场景、道具、音频、视频、截图与审片证据。
- 旧Seedance 2.0社区Skill。
- 面向人类组员且尚待修订的团队SOP。
- 临时文件、缓存、渲染预览和旧压缩包。

## 更新原则

本包只在用户明确要求时手动发布新版本。普通项目反馈不会自动进入核心规则；只有用户明确要求的大更新或已经跨项目验证的经验才纳入。已实现、试制待验证与后续网页计划分别见`ROADMAP.md`，不增加制作步骤。

# Seedance Codex Workflow Core

供GPT执行Seedance短剧导演与提示词工作流的干净核心包，不含项目剧本、素材、制作记录或成片。1.2.0为V3.2试制版：完整剧本、目标集完整音轨、资产和可选想法构成默认输入，GPT连续完成定位、核看、解读与分段；用户无需制作绿标、人工时码或单集拆解Word。

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

日常从保存本包和当前项目资料的本机目录开Local聊天，以`AGENTS.md`为入口。发布点`core-v1.2.0`为试制版，规则／工具验收及入口静态/模拟检查见[匿名说明](validation/director_v32.md)；独立新窗口、实片表现／对白同步和后期负担待用户正常制作。网页独立技能未合入、未完整实测，本轮不接入。

## 明确排除

- 所有历史与活动项目正文。
- `PROJECT_HISTORY.md`及项目纪念信息。
- 角色、场景、道具、音频、视频、截图与审片证据。
- 旧Seedance 2.0社区Skill。
- 面向人类组员且尚待修订的团队SOP。
- 临时文件、缓存、渲染预览和旧压缩包。

## 更新原则

本包只在用户明确要求时手动发布新版本。普通项目反馈不会自动进入核心规则；只有用户明确要求的大更新或已经跨项目验证的经验才纳入。已实现、试制待验证与后续网页计划分别见`ROADMAP.md`，不增加制作步骤。

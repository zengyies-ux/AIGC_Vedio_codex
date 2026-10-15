# Seedance Codex Workflow Core

供GPT执行Seedance短剧导演与提示词工作流的干净核心包，不含项目剧本、资产、制作记录或成片。1.5.0为V3.5试制版：整集生成素材额外6—10秒可剪余量、固定配角身份与姿态／空间、上游改变后的下游核对、延长必需视频引用及执行状态分层；保情绪与声音对接、七栏、摄影、无BGM和真实镜长。默认A／B／C三代理协作，主控采用，任务级自主授权继续有效。
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

日常以`AGENTS.md`为唯一入口，项目状态指向当前采用稿。V3.5发布点`core-v1.5.0`，匿名结果见[本版说明](validation/director_v35.md)。本包新增[网页填稿扩展](extensions/seedance-jumeng-operator/SKILL.md)，只在用户指定网页填写时读取；当前只填不生成，完整延长操作留V3.6。

实际空卡测试完成正式全文／6图片节点／19秒同页核对；重访正文和节点保留，模型／时长回退后恢复，参数持久性未通过。未新增上传、视频节点插入或生成，不宣称网页全流程、延长或新实片通过。旧发布与匿名历史说明保留，工作区原项目不为新规则强制返工。
## 明确排除

- 所有历史与活动项目正文。
- `PROJECT_HISTORY.md`及项目纪念信息。
- 角色、场景、道具、音频、视频、截图与审片证据。
- 旧Seedance 2.0社区Skill。
- 面向人类组员且尚待修订的团队SOP。
- 临时文件、缓存、渲染预览和旧压缩包。

## 更新原则

本包只在用户明确要求时手动发布新版本。普通项目反馈不会自动进入核心规则；只有用户明确要求的大更新或已经跨项目验证的经验才纳入。已实现、试制待验证与后续网页计划分别见`ROADMAP.md`，不增加制作步骤。

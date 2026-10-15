# Seedance Codex Workflow Core

供GPT执行Seedance短剧导演及网页准备工作流的干净核心包，不含项目剧本、资产、操作记录或成片。1.6.0为V3.6本地候选：沿用有效导演／声音、6—10秒可剪素材、协作、七栏、摄影与原生填稿，按明确任务范围准备真实源、视频延长模式、片段区间、视频槽／正文视频、人物场景和新增秒数；不提交生成／付费。
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

日常以`AGENTS.md`为唯一入口，项目状态指向当前采用稿；普通提示词制作不加载网页规程。只原生填写读[填稿](extensions/seedance-jumeng-operator/references/fill-and-verify.md)，明确延长准备读[唯一路由](extensions/seedance-jumeng-operator/references/video-extension.md)，不从准备授权推导生成或发布。

两条实际延长准备完成，源卡内编辑续段；模式、完整源区间、槽与正文视频同源、1视频5图及全文重访保持，原生草稿／历史不变。新增时长回5秒，恢复23后仅当前同页正确；未生成、延长实片／回执／声画接缝未验。详见[匿名说明](validation/director_v36.md)。

此候选只本机保存，尚未GitHub发布；旧`core-v1.5.1`和历史包保留。新版本和标签仅在用户明确授权发布后执行，不能把本地ZIP当远端成功。
## 明确排除

- 所有历史与活动项目正文。
- `PROJECT_HISTORY.md`及项目纪念信息。
- 角色、场景、道具、音频、视频、截图与审片证据。
- 旧Seedance 2.0社区Skill。
- 面向人类组员且尚待修订的团队SOP。
- 临时文件、缓存、渲染预览和旧压缩包。

## 更新原则

本包只在用户明确要求时手动发布新版本。普通项目反馈不会自动进入核心规则；只有用户明确要求的大更新或已经跨项目验证的经验才纳入。已实现、试制待验证与后续网页计划分别见`ROADMAP.md`，不增加制作步骤。

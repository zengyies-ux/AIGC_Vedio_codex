# Seedance Codex Workflow Core

这是一份供Codex学习和执行Seedance海外短剧提示词工作流的干净核心包，不包含任何历史项目、剧本、角色资产、成片、审片记录或旧提示词。1.1.2含V3.1稳定化修补：保住解读中的有效互动，统一声音短格式及镜头开口，并在一次简短顺读中核对对白和项目节奏。现有2秒原配音采用与无时码一次确认继续保留。

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

可选工具位于`tools/local_audio/`，状态与实测限制见`validation/director_v3.md`。无需运行音频工具即可使用导演核心；音频采用按`memories/seedance_workflow/execution_rules.md`现行时间标准，实际听检状态独立记录，受影响未通过项继续人工定位。完整MP3／WAV可与剧本、资产一起提供，个人想法可选。没有参考时码时，Codex主动整理候选表，用户一次整体采用或指出少数问题，不重填整套时码；真实确认绑定同音轨与完整候选表，不能用候选反证自身满足2秒误差。分阶段审核继续保留。

日常从安装本包且保存当前项目资料的本机目录开Local聊天，以该目录`AGENTS.md`为入口；本机项目与缓存不会因发布核心包自动上传。发布标签`core-v1.1.2`对应V3.1实现与文本检查结果；实际生成改善待下一次正常制作验证，用户认可后再用该提交作为网页扩展的稳定基础。网页扩展仍另分支维护，本轮不实施。

## 明确排除

- 所有历史与活动项目正文。
- `PROJECT_HISTORY.md`及项目纪念信息。
- 角色、场景、道具、音频、视频、截图与审片证据。
- 旧Seedance 2.0社区Skill。
- 面向人类组员且尚待修订的团队SOP。
- 临时文件、缓存、渲染预览和旧压缩包。

## 更新原则

本包只在用户明确要求时手动发布新版本。普通项目反馈不会自动进入核心规则；只有用户明确要求的大更新或已经跨项目验证的经验才纳入。未来自动拆解剧本、分段并生成提示词的方向见`ROADMAP.md`，它不是当前强制流程。

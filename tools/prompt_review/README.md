# 正式稿轻量检查

此工具只读现有Markdown，不建立第二套提示词格式，不改文件。检查唯一可复制text正文中的编号、声明镜数、连续覆盖、正时长、实际单镜上限、明确开口时点是否在所属镜头、正文后期调度及声音范围。

在工作区运行：

```sh
python3 tools/prompt_review/check_prompt.py /absolute/path/to/prompt.md --max-shot-seconds 3
python3 -m unittest discover -s tools/prompt_review -p 'test_*.py' -v
```

当前用户快节奏旁白任务使用3秒上限，其他题材传入实际明确上限。没有0.8秒下限。时间窗口是设计预算，不保证平台逐帧执行。

一条1—5秒声音跨0—2、2—3.4、3.4—5.6秒三个镜头合法，不要求对白窗口等于镜头窗口。完整原句仍只列一次，依据[声音跨镜](../../memories/seedance_workflow/execution_rules.md#audio-shot-independence)核本镜发言者画内外与受击回应。

隐藏切镜、同时出现静默用语和对白、没有明确特写会给待人工复核提示，不用字符串匹配擅自判定人物语义。听者安静与说话者画外持续可以合法；连续运镜改变构图不等于硬切。不要为了清除警告删表演或塞“特写”关键词。

structural_pass只代表已实现的结构项无错；visual_quality和source_continuity始终为not_assessed。它不能证明情绪有效、表演自然、原文全部对应、空间连贯、源片合格或实片效果。未解析到唯一正文／逐镜格式时不报通过。最终仍按[模板](../../memories/seedance_workflow/prompt_template.md#final-check)顺读。

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

整集预算使用显式的一次性内部算术输入，不从项目目录、通配符或历史版本推测采用稿。JSON仅含实际原轨长度A、唯一当前各段路径、方式和整数提交／新增秒数，例如：

```json
{
  "audio_seconds": 70.1649375,
  "segments": [
    {"path": "01.md", "mode": "native", "seconds": 30},
    {"path": "02.md", "mode": "extension", "seconds": 20},
    {"path": "03.md", "mode": "native", "seconds": 28}
  ]
}
```

```sh
python3 tools/prompt_review/check_prompt.py --episode-budget /absolute/path/to/budget.json
python3 tools/prompt_review/check_prompt.py /absolute/path/to/extension.md --mode extension
```

`path`相对该JSON所在目录解析，也可用绝对路径。调用方负责列全且只列当前各段；工具拒绝归一化后的重复路径、通配符、未知方式、非正整数秒数和额外字段。`native`的seconds是原生提交秒数，`extension`是本次新增秒数；不填重复包含的源长，也不填失败返抽。若同时给位置文件参数，须与JSON当前各段路径及顺序完全一致。CLI还核正文声明的生成秒数与显式秒数相等。

上例G＝30＋20＋28＝78，R＝7.8350625，通过6—10秒算术区间；不会将延长源再计30秒得到108。整数总长范围为`ceil(A+6)..floor(A+10)`，此例77—80。取整已计入R。唯一政策见[声音与时间](../../memories/seedance_workflow/execution_rules.md#sound-and-time)。`budget_pass`只证明显式数值满足区间，仍需人工核可裁位置、完整声音及实际区域预算。

未给整集信息时，单稿结果的`episode_budget`返回`status: not_assessed`和`detail: budget not assessed`。提供JSON时，CLI输出`{prompts: [...], episode_budget: {...}}`，顶层给整集核算；单稿自身仍不推断整集预算。不提供JSON时保留原数组输出。结构或预算失败退出1，输入无效／文件不可读退出2。Python API为`assess_episode_budget(episode=None, base_dir=None)`；无输入不检查，显式无效输入抛`ValueError`。

延长检查须显式给`--mode extension`，或在整集JSON将该段设为extension；API为`inspect(text, max_shot_seconds=3.0, generation_mode=None)`。仅检查可复制正文的`【人物与场景参考】`是否有唯一固定源简名及`@视频N`，并在`【空间与道具状态】`以相同源简名给出状态。缺少或歧义均不报结构通过。

`source_reference.status: text_reference_present`只表示文字引用及同名状态存在，`source_binding`始终`not_assessed`。预设`@视频1`与平台实际`@视频2`不能只比字符串：网页操作者须用真实节点、同一源片身份及模式／就绪证据核实。本工具不检查页面，不认证真实绑定或可提交，也不根据身份、站位、力度关键词认证视觉质量。

# 正式稿轻量检查

此工具只读现有Markdown，不建立第二套提示词格式，不改文件。检查唯一可复制text正文中的编号、声明镜数、连续覆盖、正时长、实际单镜上限、明确开口时点是否在所属镜头、正文后期调度及声音范围。

在工作区运行：

```sh
python3 tools/prompt_review/check_prompt.py /absolute/path/to/prompt.md --max-shot-seconds 2.5
python3 -m unittest discover -s tools/prompt_review -p 'test_*.py' -v
```

默认使用当前同类快节奏旁白短剧的2.5秒真实单镜上限，常态约1—1.5秒的选择仍由实际观看任务决定；其他题材通过`--max-shot-seconds`传入实际明确上限，可使用小数。2.5秒通过，2.501秒超限；不设机械最短镜长，0.6秒有清楚任务时可以合法。时间窗口是设计预算，不保证平台逐帧执行。

一条1—5秒声音跨0—2、2—3.4、3.4—5.6秒三个镜头合法，不要求对白窗口等于镜头窗口。完整原句仍只列一次，依据[声音跨镜](../../memories/seedance_workflow/execution_rules.md#audio-shot-independence)核本镜发言者画内外与受击回应。

隐藏切镜、同时出现静默用语和对白、没有明确特写会给待人工复核提示，不用字符串匹配擅自判定人物语义。听者安静与说话者画外持续可以合法；连续运镜改变构图不等于硬切。不要为了清除警告删表演或塞“特写”关键词。

structural_pass只代表已实现的结构项无错；visual_quality和source_continuity始终为not_assessed。它不能证明情绪有效、表演自然、每镜有新信息/动作进度/关系/情绪、原文全部对应、空间连贯、源片合格或实片效果。全局站位、实际动作阶段和画外人物须沿同一场面人工顺读，不因2.5秒结构通过而免检，不另增审核表。未解析到唯一正文／逐镜格式时不报通过。最终仍按[模板](../../memories/seedance_workflow/prompt_template.md#final-check)顺读。

整集预算使用显式的一次性内部算术输入，不从项目目录、通配符或历史版本推测采用稿。JSON仅含实际原轨长度A、唯一当前各段路径、方式和整数提交／新增秒数，例如：

```json
{
  "audio_seconds": 70.1649375,
  "segments": [
    {"path": "01.md", "mode": "native", "seconds": 30},
    {"path": "02.md", "mode": "extension", "seconds": 27},
    {"path": "03.md", "mode": "native", "seconds": 30}
  ]
}
```

```sh
python3 tools/prompt_review/check_prompt.py --episode-budget /absolute/path/to/budget.json
python3 tools/prompt_review/check_prompt.py /absolute/path/to/extension.md --mode extension
```

`path`相对该JSON所在目录解析，也可用绝对路径。调用方负责列全且只列当前各段；工具拒绝归一化后的重复路径、通配符、未知方式、非正整数秒数和额外字段。`native`的seconds是原生提交秒数，`extension`是本次新增秒数；不填重复包含的源长，也不填失败返抽。若同时给位置文件参数，须与JSON当前各段路径及顺序完全一致。CLI还核正文声明的生成秒数与显式秒数相等。

最低素材量按实际原轨A计算：`Rmin = 8 + 7A/60`，`Gmin = ceil(A + Rmin) = ceil((67A + 480)/60)`。此处Rmin是整集最低额外素材量，取整后的实际余量为`G-A`；不是每段加，也不重复加现场对白。60秒原轨最低75秒，90秒最低109秒，120秒最低142秒，106.576秒最低128秒（取整前127.009866…秒），70秒最低87秒。JSON小数按Decimal读取，向上取整使用精确分数运算，不先舍入循环小数，也不受Decimal上下文精度影响；API传入float时以其已有十进制表示为准，需保留精确边界可传Decimal。

上例G＝30＋27＋30＝87，R＝16.8350625，Rmin＝16.185909375，Gmin＝87；不会将延长源再计30秒得到117。默认按Gmin这个精确整数目标分配各段；必要超出时，由主控说明具体原因并沿现有授权处理。工具不分配各段，也不新设超额授权流程。唯一政策见[声音与时间](../../memories/seedance_workflow/execution_rules.md#sound-and-time)。

预算报告保留`generated_seconds`、`reserve_seconds`与`integer_generated_range`；新增`minimum_reserve_seconds`、`minimum_generated_seconds`、默认等于Gmin的`target_generated_seconds`、`excess_seconds = max(0, G-Gmin)`、`excess_review_required`。兼容范围字段改为`[Gmin, null]`，null表示本工具没有统一上限，不能当作无穷费用授权。低于Gmin时`budget_pass: false`；等于或超出时为true，同时固定`budget_scope: minimum_only`，超出时另标`excess_review_required: true`。通过只证明显式合计达到最低量，不能证明费用、可剪性、声音覆盖、语义、实际区域预算或提交已获批准，也不表示生成越多越好。

未给整集信息时，单稿结果的`episode_budget`返回`status: not_assessed`和`detail: budget not assessed`。提供JSON时，CLI输出`{prompts: [...], episode_budget: {...}}`，顶层给整集核算；单稿自身仍不推断整集预算。不提供JSON时保留原数组输出。结构或预算失败退出1，输入无效／文件不可读退出2。Python API为`assess_episode_budget(episode=None, base_dir=None)`；无输入不检查，显式无效输入抛`ValueError`。

延长检查须显式给`--mode extension`，或在整集JSON将该段设为extension；API为`inspect(text, max_shot_seconds=2.5, generation_mode=None)`。仅检查可复制正文的`【人物与场景参考】`是否有唯一固定源简名及`@视频N`，并在`【空间与道具状态】`以相同源简名给出状态。缺少或歧义均不报结构通过。

`source_reference.status: text_reference_present`只表示文字引用及同名状态存在，`source_binding`始终`not_assessed`。预设`@视频1`与平台实际`@视频2`不能只比字符串：网页操作者须用真实节点、同一源片身份及模式／就绪证据核实。本工具不检查页面，不认证真实绑定或可提交，也不根据身份、站位、力度关键词认证视觉质量。

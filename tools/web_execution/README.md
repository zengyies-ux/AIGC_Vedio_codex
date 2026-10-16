# 轻量网页回执日志（V3.7候选）

`journal.py`是宿主LLM的提交前后记录工具，使用Python标准库。它不连接浏览器、不点击、不等待、不下载、不调用私有API，也不支付。完整操作规程见[授权生成—等待—核源—续做](../../extensions/seedance-jumeng-operator/references/generation-execution.md)。

默认`prepare`不能取得提交许可。明确本集`generate`授权后，AI使用现有目标／卡／采用稿／素材事实创建一份私有记录，逐卡同页核对，先写`intent`；原子保存并回读成功后才返回一次`one_use_click_permission`。宿主在当前已核页面正常点击一次。重新读记录、重复`intent`、失败、未知回执和中断都不会补发许可。记录中意图token仅是本地意图，绝不是平台任务ID或支付回执。

JSON事件和目录由AI内部整理，用户不需要填写表格、卡号或JSON。只准备可以沿已有运行记录，不强制产生新文件。完整链把记录放在项目已有的私有执行／review位置；不发布真实URL、卡号、授权原文、素材或截图，也不新建三套交接目录。

## 调用与恢复

由宿主已核Python运行，路径均使用实际绝对路径；Windows沿部署工具取得的Python，不要求用户配置系统PATH。

```text
<已核Python> <仓库绝对路径>/tools/web_execution/journal.py --record <私有记录绝对路径>
<已核Python> <仓库绝对路径>/tools/web_execution/journal.py --record <私有记录绝对路径> --event <AI内部事件绝对路径>
```

不带`--event`只读并给下一步建议，永远不返回点击许可。带事件时，成功退出且输出含本次`one_use_click_permission`才有一次许可；报错、输出丢失或调用中断均不能点击。许可不能跨回合保存后再用。`actions`里的`lookup_or_wait`描述意图之后的恢复路径，首次返回许可时先消费这一次点击，再只读回执。

所有事件形如`{"op": "intent", "data": {...}}`。可用事件仅有：

| 事件 | AI提供的实际事实 | 行为 |
|---|---|---|
| `init` | `scope`、`authorization`、`tasks`、`simulation` | 仅创建不存在的记录；已有记录拒绝重置 |
| `authorize` | 新的明确`authorization`、读当前页面后的`current=snapshot(record)`与`evidence` | 将只准备提升到当前范围生成；不是每段重批 |
| `intent` | `task_id`、当前同页`visible`，真实执行`live=true`／受控模拟`live=false` | 核门禁、持久化、回读后仅此调用返回一次许可 |
| `observe` | `task_id`、`status`、`evidence`、`identity`，必要`result`／可见`receipt` | 记录可见处理中／结果／失败／未知，不触发操作 |
| `source_check` | `task_id`、`result_key`、布尔`qualified`、原源`interval`、局部`evidence`、`unextended=true` | 仅检查已经完成的确切原生源，不以计划末态代填 |
| `pause` | 用户接管／改变要求的`reason` | 停止后续提交许可 |
| `resume` | 当前实际目标、采用版本／卡已复核的`current=snapshot(record)`与`evidence` | 仅解除暂停；未决意图仍只能查询 |

`snapshot`是日志函数返回的不可变目标事实；宿主必须先对照实际页面、正文版本、卡映射及队列读回，不能仅复制旧快照冒充核对。记录只接收已经定位并复核的真实卡；新建／上传由宿主按规程先查现有结果，成功即记录映射。恢复建议没有“新建卡／重新上传”动作；创建／上传的未知结果同样先查既有页面，不重做。

## 最小内部事实

`scope`必须恰含非空`project`、`episode`及可信完整`target_url`。每条任务包括：

- `id`内部段标识、`card`实际卡定位、`prompt_version`及正文语义规范化后的`prompt_sha256`。正文规范化须还原真实节点到项目固定简名，保留空格／换行和台词，不按删除全部空白的字符串做比对。
- `mode=native|extend`、采用的整数`seconds`、`model`、`resolution`；有独立可核画幅控件时记录`aspect_ratio`，否则在既有记录注明未核，不伪造控件证据。默认模型／分辨率为2.5 Pro／480P，仍由同页读回核准。
- 延长的`source_task`必须指本记录本集原生任务；原生不能隐含依赖前集，延长不能再延长。允许保存实际`assets`等语义映射用于恢复。
- 已存在且影响接缝的下游结果定位放`downstream_result_keys`；未生成下游不新增等待。

`authorization`默认`mode=prepare`。`generate`必需用户的`quote`和出处`source`，只接收直接来自人类的明确授权；不拿代理推断、测试授权或旧他集授权代替。`max_submissions`只在用户实际给出时录正整数；可比较的真实预算可存`max_cost`和`currency`，不可数值化的原文范围由宿主保留并核。没有数值不要发明限额，也不逐段重问。

`intent.visible`必须包含当前`scope`全部字段，及`card`／`prompt_version`／`prompt_sha256`／`mode`／`model`／`resolution`／整数`seconds`（任务含画幅时还含`aspect_ratio`）。另需布尔`nodes_verified`、`queue_checked`、`downstream_inventory_checked`、`region_plan_checked`均为真，非空`region_plan_evidence`指向已采用的本集区域累计及A/G/R依据，以及`downstream_checks={真实下游定位: {qualified: true, evidence: 局部事实}}`。这不是用户要填的审核表，是宿主实际同页核对所得；发现新的已有下游也须放入检查。

延长还需`source_input={key, resource, interval, native_unextended: true, selection_evidence}`，以及完全对应的`video_slot={resource, interval}`和`video_node={resource, interval}`。`interval`均为原源坐标的起止列表，允许原URL带区间，也允许可见选择链证实的新裁后资源；新资源从0计时另记，不混到这里。任何终点改变须重核局部末态。日志允许UI对实际资源时长最多0.01秒的显示舍入差，不用这个容差绕过实际入口上限；入口30秒限制仍按现场区间读数处理。

如果用户给可比较预算，提交前还需当前可见`cost_quote={amount, currency, evidence}`。日志保守累计全部已尝试的报价（未知／失败也不释放），超过上限或旧报价未知就不发许可；报价预留不表示实际扣费。更换限额只接受新的明确授权，不自动加购或归因共享账户余额变化。

## 回执、源与结果

`observe.status`仅支持`processing`、`result`、`failed`或`unknown`。`identity`包含该任务目标／集／卡／版本／SHA／模式，需实际可见证据关联，不能只靠最后一个封面。正常`processing`不因时间经过自动完成；`unknown`连续三次转`user_decision`，不会继续无限查询或重提。后续唯一明确结果仍可无新尝试地回填。

结果`result`除同一身份字段外，必须有`key`、`key_kind=platform|visible_composite`、`resource`、`identity_evidence`及实际`actual_seconds`。`visible_composite`表示可靠可定位的历史／正文／时长／播放器资源组合，不是假平台ID。`output_shape`按实际媒体填`new_only`、`includes_source`或`unknown`，不预设延长是否含源。已有结果只有明确`adopted_preexisting=true`才能无新意图采用；普通准备不能伪装成生成回执。

成为延长源还必须有从实际历史确认的整数`extension_count=0`，缺省／未知／已有延长都拒绝。`source_check`记录原源选用区间与GPT必要局部身体／空间／接触证据，`qualified=false`会阻断该段，不能转成`bool("false")`。意图还会重核当前源尚未延长。同一源结果／资源已有一次意图（包括未知／失败）或已有被采用延长结果，均不能取得第二次许可。参考裁剪不会重置原生实际长度、本集区域累计或A/G/R。区域及完整音轨预算由宿主从唯一已采用分段核对并提供证据；同一源加延长可包含有依据的区域转换，不能把文件总长直接当单区时长。本工具不推算第二套分段或改稿。

当前没有自动改稿、换源、追加范围或失败重提接口；这些变化先回主控取得具体决定、保留既有尝试和旧记录后处理，不能删除或新建记录清零。本工具不会重新标记旧结果为新版本。

## 持久化与能力边界

写入使用同目录临时文件、UTF-8、文件fsync、关闭后原子替换和回读；POSIX另同步目录。原文件占用／权限／空间错误不返回点击许可。OS拥有的进程锁在进程退出后释放，保留的小`.lock`文件不是活动任务证据，不手工删锁绕开其他写入。正常记录重开不会重建卡、上传或提交。Windows锁分支已实现但须真机验收。

等待由宿主在活动任务内每30—60秒执行，日志建议30秒但自己不sleep；应用关闭后不会后台唤醒。日志只能阻止自己的第二次许可，不能拦截用户或其他会话直接点击，不能验证宿主提供的“可见证据”真实性，也不能保证平台只受理一次。真实浏览器仍由宿主按其工具文档操作；不要声称本目录包含浏览器自动执行器。

## 验证

```bash
python3 -m unittest discover -s tools/web_execution -p 'test_*.py' -v
```

2026-10-15在Mac当前Python标准库运行**25项受控模拟行为测试通过**：原生→处理中→真实结果记录→局部合格源→一次延长→结果；只准备阻断；整集授权提升；未知不重提与三次异常返回；暂停／重开复用卡及素材映射；目标／版本／参数变化拒绝；已存在下游首态前移；失败不重提；原URL区间／新裁后资源；同源一次延长；裁剪不重置区域／预算依据、合法区域转换不被文件总长误杀；次数／报价上限；模拟不混真实；原子写失败与回读异常；中文／空格路径CLI及另一进程写锁。

这些是模拟日志行为，**没有真实网页、真实提交、付费、真实媒体或Windows运行**。历史UI操作证据见[证据边界](../../extensions/seedance-jumeng-operator/references/evidence.md)；Windows普通账户／中文路径／占用恢复、浏览器连接／文件选择／真实节点／参数、一次真实授权完整链仍待现场验收。

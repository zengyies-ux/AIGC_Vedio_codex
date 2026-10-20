# 轻量网页回执与审修日志（Core 1.9.1 本地候选）

`journal.py`是宿主LLM的提交前后记录工具，使用Python标准库。它不连接浏览器、不点击、不等待、不下载、不调用私有API，也不支付。完整操作规程见[授权生成—等待—核源—续做](../../extensions/seedance-jumeng-operator/references/generation-execution.md)。

默认`prepare`不能取得提交许可。明确本集`generate`授权后，AI使用现有目标／卡／采用稿／素材事实创建一份私有记录，逐卡同页核对，先写`intent`；原子保存并回读成功后才返回一次`one_use_click_permission`。宿主在当前已核页面正常点击一次。重新读记录、重复`intent`、失败、未知回执和中断都不会补发许可。记录中意图token仅是本地意图，绝不是平台任务ID或支付回执。

JSON事件和目录由AI内部整理，用户不需要填写表格、卡号或JSON。只准备可以沿已有运行记录，不强制产生新文件。本集固定沿同一份canonical记录：初次先收齐真实卡映射再init，修正版本用repair追加，未定稿后段不造假任务。独立原生收到可见processing回执后可依次提交下一张原生，页面点击仍串行，生成可同时等待；任何submit_intent／unknown会阻止新提交，延长保持顺序核源。次数与报价在该记录合计，不为等待中的卡另开文件规避限制。旧分卡日志保留，先核其已有提交和结果，不能删改或把已尝试任务重建为prepared；跨旧记录的累计由主控核对原任务范围，工具不声称提供跨文件全局限额。完整链把记录放在项目已有的私有执行／review位置；不发布真实URL、卡号、授权原文、素材或截图，也不新建三套交接目录。

## 调用与恢复

由宿主已核Python运行，路径均使用实际绝对路径；Windows沿部署工具取得的Python，不要求用户配置系统PATH。

```text
<已核Python> <仓库绝对路径>/tools/web_execution/journal.py --record <私有记录绝对路径>
<已核Python> <仓库绝对路径>/tools/web_execution/journal.py --record <私有记录绝对路径> --event <AI内部事件绝对路径>
```

不带`--event`只读并给下一步建议，永远不返回点击许可。带事件时，成功退出且输出含本次`one_use_click_permission`才有一次许可；报错、输出丢失或调用中断均不能点击。许可不能跨回合保存后再用。`actions`里的`lookup_or_wait`描述意图之后的恢复路径，首次返回许可时先消费这一次点击，再只读回执。

所有事件形如`{"op": "intent", "data": {...}}`。可用事件：

| 事件 | AI提供的实际事实 | 行为 |
|---|---|---|
| `init` | `scope`、`authorization`、`tasks`、`simulation` | 仅创建不存在的记录；已有记录拒绝重置 |
| `authorize` | 新的明确`authorization`、读当前页面后的`current=snapshot(record)`与`evidence` | 将只准备提升到当前范围生成；不是每段重批 |
| `intent` | `task_id`、当前同页`visible`，真实执行`live=true`／受控模拟`live=false` | 核门禁、持久化、回读后仅此调用返回一次许可 |
| `observe` | `task_id`、`status`、`evidence`、`identity`，必要`result`／可见`receipt` | 记录可见处理中／结果／失败／未知，不触发操作 |
| `source_check` | `task_id`、`result_key`、布尔`qualified`、原源`interval`、局部`evidence`、`unextended=true` | 仅检查已经完成的确切原生源，不以计划末态代填 |
| `review` | `task_id`、`outcome`（usable/minor/critical/unknown）、真实`evidence`及结果的`result_key`；关键问题另有`issue`、`cause`、`plan` | 记录实际审片，不把生成完成当合格；不提交 |
| `repair_decision` | 当前失败修正任务`task_id`、用户实际追加的正整数`additional_attempts`、直接用户`quote/source/evidence` | 只增加明确新批准额度，不清零已用次数；重放同一用户消息不重复加额 |
| `user_accept` | 已完成结果的`task_id/result_key`、直接用户原话`quote`、消息出处`source`和对应结果`evidence` | 独立记录用户观看采用；保留AI审片、覆盖缺项和偏差，不提交 |
| `repair` | `task_id`为待修旧任务、`replacement`为新任务规格、修正`evidence`、`dialogue_unchanged=true` | 保留旧尝试，追加同段修正版本；仍须独立同页核准与`intent` |
| `rebind_source` | 未提交延长的`task_id`、同谱系已审原生`source_task`、`current=snapshot(record)`、`evidence` | 切到修正后的合格原生，清空旧核源；不提交 |
| `history_reconcile` | `task_id`、外部旧日志中未纳入本日志的`prior_repair_attempts`、核对`evidence` | 旧日志迁移前核清已尝试修正；计数只增不减 |
| `pause` | 用户接管／改变要求的`reason` | 停止后续提交许可 |
| `resume` | 当前实际目标、采用版本／卡已复核的`current=snapshot(record)`与`evidence` | 仅解除暂停；未决意图仍只能查询 |

`snapshot`是日志函数返回的不可变目标事实；宿主必须先对照实际页面、正文版本、卡映射及队列读回，不能仅复制旧快照冒充核对。记录只接收已经定位并复核的真实卡；新建／上传由宿主按规程先查现有结果，成功即记录映射。恢复建议没有“新建卡／重新上传”动作；创建／上传的未知结果同样先查既有页面，不重做。

## 最小内部事实

`scope`必须恰含非空`project`、`episode`及可信完整`target_url`。每条任务包括：

- `id`内部段标识、`card`实际卡定位、`prompt_version`及正文语义规范化后的`prompt_sha256`。正文规范化须还原真实节点到项目固定简名，保留空格／换行和台词，不按删除全部空白的字符串做比对。
- `mode=native|extend`、采用的整数`seconds`、`model`、`resolution`；有独立可核画幅控件时记录`aspect_ratio`，否则在既有记录注明未核，不伪造控件证据。默认模型／分辨率为2.5 Pro／480P，仍由同页读回核准。
- 延长的`source_task`必须指本记录本集原生任务；原生不能隐含依赖前集，延长不能再延长。允许保存实际`assets`等语义映射用于恢复。
- 已存在且影响接缝的下游结果定位放`downstream_result_keys`；未生成下游不新增等待。

`authorization`默认`mode=prepare`。`review_required=true`要求每条实际结果审片，`auto_repair=true`额外启用有界修正（须同时开启review_required）；二者只有当前用户授权包含主动审修才录入，旧授权不因升级自动扩大。`generate`必需用户的`quote`和出处`source`，只接收直接来自人类的明确授权；不拿代理推断、测试授权或旧他集授权代替。`max_submissions`只在用户实际给出时录正整数；可比较的真实预算可存`max_cost`和`currency`，不可数值化的原文范围由宿主保留并核。没有数值不要发明限额，也不逐段重问。

`intent.visible`必须包含当前`scope`全部字段，及`card`／`prompt_version`／`prompt_sha256`／`mode`／`model`／`resolution`／整数`seconds`（任务含画幅时还含`aspect_ratio`）。另需布尔`nodes_verified`、`queue_checked`、`downstream_inventory_checked`、`region_plan_checked`均为真，非空`region_plan_evidence`指向已采用的本集区域累计及A/G/R依据，以及`downstream_checks={真实下游定位: {qualified: true, evidence: 局部事实}}`。这不是用户要填的审核表，是宿主实际同页核对所得；发现新的已有下游也须放入检查。

延长还需`source_input={key, resource, interval, native_unextended: true, selection_evidence}`，以及完全对应的`video_slot={resource, interval}`和`video_node={resource, interval}`。`interval`均为原源坐标的起止列表，允许原URL带区间，也允许可见选择链证实的新裁后资源；新资源从0计时另记，不混到这里。任何终点改变须重核局部末态。日志允许UI对实际资源时长最多0.01秒的显示舍入差，不用这个容差绕过实际入口上限；入口30秒限制仍按现场区间读数处理。

如果用户给可比较预算，提交前还需当前可见`cost_quote={amount, currency, evidence}`。日志保守累计全部已尝试的报价（未知／失败也不释放），超过上限或旧报价未知就不发许可；报价预留不表示实际扣费。更换限额只接受新的明确授权，不自动加购或归因共享账户余额变化。

## 回执、源与结果

`observe.status`仅支持`processing`、`result`、`failed`或`unknown`。`identity`包含该任务目标／集／卡／版本／SHA／模式，需实际可见证据关联，不能只靠最后一个封面。正常`processing`不因时间经过自动完成；`unknown`连续三次转`user_decision`，不会继续无限查询或重提。后续唯一明确结果仍可无新尝试地回填。

结果`result`除同一身份字段外，必须有`key`、`key_kind=platform|visible_composite`、`resource`、`identity_evidence`及实际`actual_seconds`。`visible_composite`表示可靠可定位的历史／正文／时长／播放器资源组合，不是假平台ID。`output_shape`按实际媒体填`new_only`、`includes_source`或`unknown`，不预设延长是否含源。已有结果只有明确`adopted_preexisting=true`才能无新意图采用；普通准备不能伪装成生成回执。

普通首次延长源必须有从实际历史确认的整数`extension_count=0`，缺省／未知拒绝。修正替代候选可以复用已有候选的原生源，必须仍是`mode=native`，不能使用任何延长结果。`source_check`记录原源选用区间与GPT必要局部身体／空间／接触证据，`qualified=false`会阻断该段，不能转成`bool("false")`。意图还会重核当前源尚未延长。普通非修正任务对同一源结果／资源已有一次意图（包括未知／失败）或已有被采用延长结果时，不能取得第二次许可；唯一例外是下面明确授权、已归因、受3次谱系上限约束的替代延长候选。参考裁剪不会重置原生实际长度、本集区域累计或A/G/R。区域及完整音轨预算由宿主从唯一已采用分段核对并提供证据；同一源加延长可包含有依据的区域转换，不能把文件总长直接当单区时长。本工具不推算第二套分段或改稿。

## 主动审片与有界修正

完整生成授权包含主动审修时，宿主实际复查画面并调用review。从Core1.8.7起默认review_audio=false，本版保持（省略也为false），只以视觉覆盖与视觉关键未决判断采用／核源；不提取或转写成片声音，不要求用户试听。coverage.audio可省略或为空，audio_status=not_requested，complete.audio仍如实记false而非伪造通过。原始输入配音的定位和提示词原句核对保留。

只有用户明确专项检查生成声音才录review_audio=true，并使用下述可选音频方法及门禁。旧记录不清零：按当前用户决定更新音频政策、复用视觉证据追加review，可解除仅因声音的旧unknown，不伪造user_accept。真实提交unknown、视觉问题、修正次数和原授权保持。

支持明确声明`visual_method=overview|continuous|shot_sequence`、`audio_method=listening|transcript_and_spotcheck`和`blocking_unknowns=[]`。`limitations`保留“未逐帧”“没有全轨连续听检”等方法限制；真正影响事件、台词、说者、动作、身份或接缝的未决判断写入blocking_unknowns，不能挪到limitations后宣称可用。明确方法下，当前要求通道的方法覆盖且无关键未决即可usable/minor，不因合法方法限制逼用户逐条代审。

- overview为1.9.1默认：记录实际快速浏览的窗口和非空visual_evidence（看了哪些范围、有无明显站位／肢体逻辑错误），不能仅拿到首帧缩略图就声称完成浏览，无关键blocking_unknowns即可采用或记轻微可剪；不需镜头清单、全区间或密集帧。assessment_scope=obvious_visual_errors，assessment_complete只表示该快速检查完成；complete.visual仍按实际窗口记录，不能伪称全片逐镜覆盖。源接缝未合格仍不能延长，review=unknown不授权返抽。
以下详细方法仅在专项审查确需时采用，不是默认步骤。

- continuous要求visual窗口完整覆盖；listening仅在review_audio=true时要求audio覆盖。未请求声音时不用audio_method或transcript_coverage；blocking_unknowns只列本轮实际检查范围内的关键未决项，不放声音未核。
- shot_sequence另记`shot_coverage=[{interval:[实际镜头起止],frame_points:[实际核看时点],evidence:"本镜证据"},...]`及`visual_evidence`。镜头区间须覆盖完整结果，每个实际镜头有帧点且落在该镜和真实visual窗口；visual_evidence说明全段扫描、实际切点、逐镜覆盖及关键动作／接缝加密，可引用存有具体时点的证据文件。首中尾少帧不代表全片，不能伪造镜头表来凑完整覆盖。
- transcript_and_spotcheck另记`transcript_coverage`完整生成音轨转写与授权台词对照范围，以及`audio_evidence`说明该对照和实际疑点核对；audio仅为实际局部听检窗口且不能为空，不声称全片已听。转写不能确认的说者、台词、音效／动作时序等关键疑点须补核或列blocking_unknowns。

日志的`complete`仅表示实际visual/audio窗口是否覆盖全域；`assessment_complete`表示所声明方法的覆盖。工具只验证结构、区间、帧点及非空证据声明，不能认证真实镜头数、图像／转写质量或代替宿主审片。所声明方法尚未完成或存在关键疑点时保持unknown并补核；overview的局部观察不因complete.visual=false自动阻断；已确证关键错误可记critical后精准修正，不冒称旧片全审，新结果按当前实际要求的检查级别复查。

`usable`为可用；`minor`为轻微、后期可剪且不伤事件／对白／关键接缝，记录可裁依据，不追求无瑕疵重抽；`critical`记录具体错误、因果和修正方案；`unknown`只补证据，不能重生成。任何未经原剧本／用户授权的新台词都不允许；台词以原剧本／用户明确授权原句为基准，不以错误提示词为准。删除擅自新增的“Help him!”属于恢复获授权台词，不算改原台词；`dialogue_unchanged=true`是宿主已核事实，不是工具自动识别语言。

用户明确说已观看并采用某一真实结果时，用`user_accept(task_id,result_key,quote,source,evidence)`保存直接用户原话及消息出处。子代理意见、主控推断或沉默不能替用户提供quote。采用只针对该确切已完成结果：可接受AI记为critical的偏差，或AI仅局部核看而记为unknown的覆盖缺项，不把它们改成usable、不补造AI全片审听。已知问题、实际coverage和既有source_check全部保留；后续不再自动修该结果。必要时由用户采用依据解除审片质量门禁，但延长仍须真实原生源、身份／资源／区间匹配及必要局部接缝核查，qualified=false须重新核查后才能续做。也允许明确采用带superseded_by的旧结果：独立保存该谱系当前用户采用选择，原尝试、计数和新版历史不删；尚未提交的新版不再自动生成，已处理中新版继续读回执而不自动取消。若已有提交下游使用了另一结果，返回review_existing_downstream交主控核必要接缝，不隐式重做或改其源。用户接受不覆盖submit_intent/processing/unknown提交状态、错误结果身份、延长结果冒充原生、权限拒绝或实际余额不足，也不新增生成授权。

`cause=prompt|model|platform_transient`且有具体`plan`可进入有界修正；素材不足、权限、余额不足、原因不明分别用`asset|access|balance|unknown`，返回实际阻塞，不能随机改稿反复付费。平台明确失败须先归因；处理中、点击不明、回执unknown及审片unknown都不获得修正许可。

每段首次任务形成稳定`repair_root`；`repair`追加新的不可变任务，沿`repair_of`链接旧版本，旧任务保留结果且标`superseded_by`。同谱系所有问题、版本、卡号共享最多**3次主动修正提交**，初次生成不计；次数由已持久化修正`intent`加已核旧日志外部修正次数计算。只有提交意图计数，纯改稿、创建修正候选不计；未知／失败不退次数。默认达到3次后该谱系返回用户决定。用户随后明确批准再修具体次数时，用repair_decision保存原话、可唯一定位的直接用户消息出处及实际追加整数；累计上限=默认3+已批准追加次数，已用次数、旧错误和回执保留。重复处理同一quote/source不再次增加额度；子代理意见不授权追加。新指令可重新开启该谱系的修正并保留此前用户采用历史，但不覆盖unknown、暂停、诊断、素材、源或成本门禁；没有新的明确追加决定仍拒绝第4次。不能改issue名称、换稿／卡／任务名、换源或新日志清零。此保守的段谱系总上限避免不同错误轮换造成无限生成。

修正仅保留同段原模式、整数时长、模型、分辨率及画幅，不能扩大剧情、授权集数或预算。原生修正后，依赖它且尚未提交的延长可用`rebind_source`转到同谱系已审可用或用户明确观看采用的原生，随后重新核选用区间、实际末态、正文和真实节点。已提交或已完成下游不能被隐式重做。

延长修正生成的是同一原生源的**替代候选**，不连续延长旧延长结果。新任务`source_task`必须保持原生源，提交前`source_input`须有`native_origin=true`及`replaces_task=被替换延长任务ID`，并再次核原源区间、槽和正文节点；`source_check.unextended=true`在这个分支表示选用媒体本身是原生，而非声称它从未产生过候选。普通延长仍执行原一次提交门禁。所有候选尝试、报价保留；有效成片只计最终采用原生及一条采用延长，被替换候选不重复计时。

Schema 2兼容读取schema 1，旧文件只读时不写回。旧记录开启自动修正前须`history_reconcile`：主控查项目状态和采用索引指向的全部旧日志及同目标并行记录；任何旧／并行submit_intent或unknown先查清，不得把历史标为已核可修，也不得换scope、集号写法或文件跳过未决意图。按同段版本关系核对，按意图token／真实结果去重，累计本日志之外的修正提交并写依据；不把`adopted_preexisting`复制结果再次算提交，不把未提交草稿算次数。当前工具不能证明宿主已发现全部历史文件，也不能阻止绕过日志的人工／其他会话点击。新生产每集固定沿一份canonical日志追加版本，不能以新空文件代替历史。EP20/21历史证据不自动迁移、不重开已停止任务。

同一聊天连续做2–3集时，由主控从用户材料和自然语言目标建立顺序，每集独立日志／采用稿／URL和卡映射，切集前重核身份。跨集默认独立原生，不等待前集成片；同集必要实际源依赖保留。无需用户填配置表，本工具不增加多集调度器。

积分正常消耗不构成停止理由，未给数值不编预算；真实余额不足或用户明确次数／预算上限仍是约束。不充值。日志保守报价预留不声称实际扣费，修正次数和成本分别核，限额不因追加新版本重置。本工具不会重新标记旧结果为新版本。

## 持久化与能力边界

写入使用同目录临时文件、UTF-8、文件fsync、关闭后原子替换和回读；POSIX另同步目录。原文件占用／权限／空间错误不返回点击许可。OS拥有的进程锁在进程退出后释放，保留的小`.lock`文件不是活动任务证据，不手工删锁绕开其他写入。正常记录重开不会重建卡、上传或提交。Windows锁分支已实现但须真机验收。

等待由宿主在活动任务内每30—60秒执行，日志建议30秒但自己不sleep；应用关闭后不会后台唤醒。日志只能阻止自己的第二次许可，不能拦截用户或其他会话直接点击，不能验证宿主提供的“可见证据”真实性，也不能保证平台只受理一次。真实浏览器仍由宿主按其工具文档操作；不要声称本目录包含浏览器自动执行器。

## 验证

```bash
python3 -m unittest discover -s tools/web_execution -p 'test_*.py' -v
```

2026-10-15在Mac当前Python标准库运行**27项受控模拟行为测试通过**：原生→处理中→真实结果记录→局部合格源→一次延长→结果；只准备阻断；整集授权提升；未知不重提与三次异常返回；暂停／重开复用卡及素材映射；目标／版本／参数变化拒绝；已存在下游首态前移；失败不重提；原URL区间／新裁后资源；同源一次延长；裁剪不重置区域／预算依据、合法区域转换不被文件总长误杀；次数／报价上限；模拟不混真实；原子写失败与回读异常；中文／空格路径CLI及另一进程写锁。

这些是模拟日志行为，**没有真实网页、真实提交、付费、真实媒体或Windows运行**。后续Mac真实整集已补现场证据，范围见[本版说明](../../validation/director_v37.md)；历史UI操作证据见[证据边界](../../extensions/seedance-jumeng-operator/references/evidence.md)；Windows普通账户／中文路径／占用恢复、浏览器连接／文件选择／真实节点／参数、Windows真实完整链及其他异常恢复仍待现场验收。

1.8.6本地候选新增审片／3次谱系修正／延长替代候选／修正源重新绑定／旧日志计数迁移的受控模拟；测试结果按实际运行报告，不代表真实媒体审片质量或浏览器实测。




本次1.8.6本地实际运行63项标准库受控模拟测试通过（33项原有行为、30项审修与用户采用行为），未作真实网页提交、真实媒体识别或Windows运行。用户接受偏差不代表AI完成全片审片。

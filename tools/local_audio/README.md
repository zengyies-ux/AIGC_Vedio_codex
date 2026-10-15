# 本机英文音频定位与采用

V3.2 的正常入口是完整剧本、目标集完整 MP3/WAV 和实际资产。GPT通读后提取目标集，核定旁白／对白、说话者、直接听者和顺序，再调用现有本机工具；不要求用户做绿标、人工时码、单集拆解Word或填写JSON。语言和平台范围仍是已测 Apple silicon Mac 英文 MLX Whisper，不泛称全部语言或设备已验证。

工具给出候选及匹配证据，GPT内部核对内容、归属和边界。默认**验证模式**随导演解读、画面设计和分段集中审核一次，用户明确整体回复同时记录音频采用；不会再追加音频审批。用户已明确本任务自主制作时，真实授权与范围落盘后允许该范围内部核查采用；用户以后认可流程与实片效果、明确启用并落盘**长期常规模式**后，后续按其范围采用。版本发布、沉默、单独工具检查都不启用常规模式。采用、用户方案认可、实际听检和生成效果分别记录。

## 环境

需 Python 3.12、macOS arm64。独立 venv、模型、完整词表和音频短段均放 `.codex_tmp/audio_v3/`，不入 Git。MLX Whisper 官方依赖包含 PyTorch 等包，正常安装依赖；运行转写只使用这一套 MLX 后端。`imageio-ffmpeg` 的 arm64 wheel 内带 decoder，不要求改系统 PATH 或安装 Homebrew。

```sh
python3.12 -m venv .codex_tmp/audio_v3/venv
.codex_tmp/audio_v3/venv/bin/python -m pip install --cache-dir .codex_tmp/audio_v3/pip-cache -r tools/local_audio/requirements-lock-macos-arm64-py312.txt
```

主选模型为 `mlx-community/whisper-small.en-mlx`（英文 small，约 481 MB），固定 revision `52a88bf6e98b114a210c21bb83e22d6e1505cb73`；固定 MLX `0.32.3`、MLX Whisper `0.4.3`、imageio-ffmpeg `0.6.0`。完整已测依赖记录在 lock 文件。首次下载从公开模型仓库读取权重；音频始终在本机解码和转写，不发往外部转写服务。模型文件不进入 Git。

## 默认输入与运行

GPT以剧本语境确定归属，写入既有JSON接口；引号仅辅助句段划分，不推断说话者，ASR不通过声纹代替人物关系判断。

```json
{"units": [
  {"id": "p1", "text": "She stopped at the door.", "kind": "narration", "speaker": "narrator"},
  {"id": "p2", "text": "Will you stay?", "kind": "dialogue", "speaker": "actor_A", "listener": "actor_B"},
  {"id": "p3", "text": "He looked away.", "kind": "narration", "speaker": "narrator"}
]}
```

旁白／对白全部保留逐句候选。对白可用 `listener` 或非空 `listeners`；未知说话者／听者不能进入V3.2采用。可选 `dialogue_group` 指定当前分组，未指定则按连续对白分组，旁白或显式分组变化处分开；没有绿标仍完整定位。原句和原始ASR保持原样；不能借工具改台词或金额。

```sh
.codex_tmp/audio_v3/venv/bin/python tools/local_audio/localize.py \
  --audio '/absolute/path/episode.mp3' \
  --script '/absolute/path/target_episode_units.json' \
  --cache .codex_tmp/audio_v3 \
  --out .codex_tmp/audio_v3/current_candidates
```

纯文本仍接受 `Episode 20`／`[P1258]`，用 `--episode 20` 提取，但不能由引号可靠核定角色。GPT在正式采用前核定JSON角色；不是要求用户重新填表。

可选 `--anchors-json` 只指定当前设计派生的句段单位，不提供强制时间窗口：

```json
[{"id": "anchor_A", "unit_id": "p1"}]
```

`historical_seconds` 兼容原样保存作比较，不能强制匹配或沿用旧分段。旁白段首、对白组、生成局部和剪辑时间分开；工具不替GPT决定段数。

## 核查、一次整体确认与授权内部采用

首次输出 `result.json`、`review.md`、关键短段和两个未完成模板：`internal_review_request.json` 的 `checked:false` 与 `candidate_confirmation_request.json` 的 `confirmed:false`。GPT先处理低置信、短句、重复和边界问题，能内部查清的不交用户作业；确实不能判断且影响执行才指出局部疑点。

GPT核查后在结果目录外保存 `--internal-review-json` 记录：

```json
{
  "basis": "gpt_internal_review", "checked": true, "project_scope": "current_project",
  "audio_file_sha256": "<当前完整文件SHA256>",
  "audio_content_identity_sha256": "<当前音频内容身份SHA256>",
  "derived_anchors_sha256": "<当前派生段首SHA256>",
  "checks": {"content_complete": true, "roles_verified": true, "boundaries_verified": true},
  "reviewed_unit_ids": ["p1", "p2", "p3"], "unresolved_blockers": [],
  "review_source": "<本次实际核查的剧本、候选及相关证据>",
  "review_note": "<实际核查结果；未解决问题不能写成已解决>"
}
```

真实核查记录要覆盖全部句段，内容／角色／边界检查均完成、源版本和当前派生段首相符，并无未决阻断。检查标志不能掩盖程序发现的漏句、错配、角色未知、重复归属、零／不完整时码或正文ASR差异。记录不等于听检，工具始终保留 `playback_verified:false` 和实测误差 `null`。

验证模式仍将解读、画面、分段和候选合成一份方案。用户一次真实回复整体采用或指出局部问题后，GPT复制确认模板到结果目录外，保存 `basis:user_explicit`、`confirmed:true` 和非空真实回复摘要。`--candidate-confirmation-json` 与核查文件一起运行到新输出目录；没有明确回复、空模板或只完成GPT核查，均不采用。用户无需填写JSON或整套时码。

确认绑定音频文件及 `audio_content_identity_sha256`，不把候选时码抄成独立参考。通过来源是 `user_overall_confirmation`，`user_confirmation_recorded` 保存真实事实，`scheme_approval` 只描述该次原始整体回复的范围。候选未确认与核查未完成分别显示，不合并为实片通过。

内部采用通过 `--production-mode-json` 读取已落盘授权，至少包含：

```json
{
  "mode": "routine", "basis": "user_explicit", "authorized": true,
  "project_scope": "current_project",
  "authorization_source": "<用户本任务自主或长期常规授权的实际来源>",
  "authorization_note": "<真实授权原话与范围；当集自主不记成长期认可>"
}
```

接口`mode:routine`可承载明确的当集自主授权或长期常规：用project_scope限定当前任务，authorization_source/note记录真实范围和原话，并在项目状态明确是否启用长期；不能用机器字段推断用户满意或长期授权。范围须与内部核查相同。没有模式记录默认为验证；内部核查文件本身不改变模式。已授权常规模式通过后来源是 `gpt_internal_review`、状态 `internally_adopted_candidates`，不写 `user_explicit` 音频确认、不伪造回复，也不记当前导演方案已获用户认可。模式授权持久保存在现有项目状态关联记录中，后续同范围新窗口读取它，不逐集重问；长期常规默认启用仍等待用户实际认可；本任务自主分支只依据该任务明确授权。

测试记录的 `basis:test_simulation` 只用于受控演练；任一采用环节是模拟都保持 `automatic_pass:false`、真实用户确认和方案认可为false，只有 `simulated_adoption_pass:true`。不能将单测fixture或模拟回复写进真实项目采用页。

### 内容身份与派生段首

新候选schema为2，转写缓存 `VERSION=2` 保留。`audio_content_identity_sha256` 包含完整输入文件／PCM、实际原句、旁白／对白及说听角色、逐句完整估计边界、匹配疑点和对白组；不含路径、耗时或派生段首。`derived_anchors_sha256` 单独绑定当前段首。

音频、原句、说听归属或匹配证据变更，使旧确认和核查失效。合法改分段只重新匹配已缓存词表、核验当前派生段首，更新内部核查，不重转整轨，也不重复询问未变音频采用。旧整体回复保留历史范围；新段首变化后 `scheme_approval.approved:false`、`covers_current_derived_anchors:false`，不能声称新导演方案已被认可。新增段首映射缺失或失效仍阻断。

旧只带 `candidate_content_sha256` 的确认严格核对完整候选（包括段首），不会静默升级为新宽范围确认。新请求模板使用分开的内容身份与段首字段；候选完整快照SHA仍保留用于追溯。

## 旧输入与2秒参考兼容

`--dialogue-docx` 可读取正文直接段落的明确 run-level `highlight=green` 或 `shd fill=00ff00/92d050`，不渲染。表格绿标、继承样式及其他绿色值不支持。旧绿标秒数不参与配句，普通新项目不要求此文件。

已有独立用户参考时码可单独用 `--reference-times-json`，绑定完整音频文件SHA、`basis:user_supplied`、`tolerance_seconds:2`，覆盖所有对白组首尾和请求段首。恰好2秒可通过，超出或内容阻断均拒绝；参考只在匹配完成后比较，不强制时间窗。此兼容路径保持旧speaker-only接口，不猜填听者；V3.2新候选采用须含剧本直接听者。参考参数与候选采用／内部核查／模式参数互斥。

```json
{
  "basis": "user_supplied", "audio_file_sha256": "<完整文件SHA256>", "tolerance_seconds": 2,
  "dialogue_groups": {"dialogue_01": {"start": 44, "end": 46}},
  "anchors": {"anchor_A": {"start": 25}}
}
```

兼容通过来源为 `user_reference_times`、状态 `user_reference_passed`；参考一致性不代表方案整体认可或听检精度。没有独立人工参考不再要求或声称满足≤2秒。

## 输出、缓存与保护

- `result.json`：全部 `sentence_candidates`、原句及角色、估计首尾、遗漏／差异、对白组及派生段首；候选证据、GPT核查、采用来源、原始整体回复范围、听检和生成／成片状态各自明确。
- `review.md` 与关键 `review_clips/*.wav`：候选原句、角色、区间及原点映射，便于内部处理相关疑点和集中审核。完整词表只留本地。
- ASR缓存由解码内容SHA、既有cache VERSION、工具版本、固定模型及参数决定。相同音频复用词表，改镜头／段首不重转；`--force-transcribe` 仅为明确重转或性能请求。

只允许经本轮确认的 `cancelled/canceled` 书写等价；匹配记录原剧本词、原ASR词、规范词及 `user_confirmed_cancelled_canceled_spelling` 来源。原文、ASR词表和原时码不改。`exact_tokens` 兼容字段表示受限规范化后的匹配覆盖，`equivalent_tokens` 与逐句 `spelling_equivalences` 单列；金额、人名、否定词、真实漏词／漏句均不模糊归一。

完整MP3/WAV本机解码到16kHz单声道PCM，原点为0；不去掉开头静音、不平移输入版本。模型manifest固定repo/revision及配置／权重SHA，缓存payload、schema和有限单调时码核验；破坏明确拒绝。输入与所有输出检查resolved path／hardlink碰撞并核对前后SHA，原始输入与原ASR不覆盖。音频和模型始终本机，不上传到转写服务或Git。

首次安装、模型下载、冷启动、转写、匹配与缓存耗时分列；缓存速度不冒充第一次处理速度。超过120秒应核对实际阶段。没有可访问Metal GPU的环境只进行已有词表匹配／缓存回归，不能报告转写成功。

## 依据与验收

[MLX Whisper 官方用法](https://github.com/ml-explore/mlx-examples/tree/main/whisper)支持 `word_timestamps=True`；[官方 transcribe 实现](https://github.com/ml-explore/mlx-examples/blob/main/whisper/mlx_whisper/transcribe.py)通过 cross-attention 与 DTW 估计词时间，而非人工真值。[固定模型来源](https://huggingface.co/mlx-community/whisper-small.en-mlx/commit/52a88bf6e98b114a210c21bb83e22d6e1505cb73)和 [decoder 发行包](https://pypi.org/project/imageio-ffmpeg/0.6.0/)可核对。

```sh
python3 -m unittest discover -s tools/local_audio -p 'test_*.py' -v
```

有意义的验收覆盖既有失败保护，以及无绿标完整候选、一次真实集中确认、默认验证不会自行采用、受控常规授权与真实核查、模拟与真实采用隔离、原句／角色／音频变更失效、派生段首重校、受限书写等价：重复句不能复用同一词、少一次同文重复不能判定唯一归属、删除对白不能借后句、截断首尾不可冒充完整边界、短句零时长提示、改剧本复用词表、离线模型与篡改拒绝、原音频碰撞保护及缓存词时码校验；用户参考恰好 2 秒通过、超过／缺项／错指纹／错配拒绝；候选沉默不采用、显式事实保存、内容变更使确认失效、模拟确认不冒充真实用户采用，并始终区分采用通过和听检真值。真实样本的匿名性能与验证限制见[验收报告](validation_report.md)。

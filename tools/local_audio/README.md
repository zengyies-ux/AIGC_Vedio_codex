# 可选本机英文音频定位

只在 Apple silicon Mac 上用 MLX Whisper 准备原音轨的估计时间对应。它不参加每轮导演判断，也不替代剧本、三时轴或原有人工定位。提供完整用户参考时码后，全部边界差不超过 2 秒即可采用通过；新集没有参考时码时，先整理候选，由用户一次明确整体确认或指出少数问题。采用依据与实际听检分别记录，不能据此宣称实测精度。

## 环境

需 Python 3.12、macOS arm64。独立 venv、模型、完整词表和音频短段均放 `.codex_tmp/audio_v3/`，不入 Git。MLX Whisper 官方依赖包含 PyTorch 等包，正常安装依赖；运行转写只使用这一套 MLX 后端。`imageio-ffmpeg` 的 arm64 wheel 内带 decoder，不要求改系统 PATH 或安装 Homebrew。

```sh
python3.12 -m venv .codex_tmp/audio_v3/venv
.codex_tmp/audio_v3/venv/bin/python -m pip install --cache-dir .codex_tmp/audio_v3/pip-cache -r tools/local_audio/requirements-lock-macos-arm64-py312.txt
```

主选模型为 `mlx-community/whisper-small.en-mlx`（英文 small，约 481 MB），固定 revision `52a88bf6e98b114a210c21bb83e22d6e1505cb73`；固定 MLX `0.32.3`、MLX Whisper `0.4.3`、imageio-ffmpeg `0.6.0`。完整已测依赖记录在 lock 文件。首次下载从公开模型仓库读取权重；音频始终在本机解码和转写，不发往外部转写服务。模型文件不进入 Git。

## 输入与运行

英文剧本可用带 `Episode 20`／`[P1258]` 的纯文本；用 `--episode 20` 选择本集。也可用 JSON 精确保留剧本段落、旁白／对白归属及说话者，避免工具推测角色：

```json
{"units": [
  {"id": "p1", "text": "She stopped at the door.", "kind": "narration", "speaker": null},
  {"id": "p2", "text": "\"Will you stay?\"", "kind": "dialogue", "speaker": "speaker_from_script", "dialogue_group": "group_1"}
]}
```

纯文本的引号只用于初分旁白／对白，不能可靠确定说话者。正式使用须以剧本语境核定归属，或在 JSON 提供 `speaker`；转写结果不覆盖原台词。

可选 `--dialogue-docx` 只读取 zip/XML 内**正文直接段落**的明确 run-level `highlight=green`，或 `shd fill=00ff00/92d050`，按连续绿标段落建立对白组，不渲染 Word。当前不支持表格内绿标、继承样式或其他绿色值；不能泛称所有 Word 绿标均可识别。绿标旧秒数不参与音频匹配。没有受支持绿标时，可在 JSON 明确 `dialogue_group`、`kind` 与剧本说话者完成分组；两者均未提供则提示分组缺失，保留人工归属入口。

可选段首 JSON 仅指定剧本单位，不提供强制时间窗口：

```json
[{"id": "anchor_A", "unit_id": "p1", "historical_seconds": 25}]
```

`historical_seconds` 仅原样保存作比较；时间由完整音频与剧本顺序产生。原旁白段首、对白组、生成局部与剪辑时间仍须分开，不能用生成时长累加替换原音轨位置。

用户明确采用 2 秒容差时，另用 `--reference-times-json` 提供参考。此文件绑定完整输入音频的文件 SHA256，明确 `basis: "user_supplied"` 与 `tolerance_seconds: 2`；须覆盖全部对白组首尾和全部所请求段首。对白组编号按来源顺序为 `dialogue_01`、`dialogue_02`……，段首编号与 anchors JSON 相同。以下仅为格式示例：

```json
{
  "basis": "user_supplied",
  "audio_file_sha256": "<完整输入音频的64位SHA256>",
  "tolerance_seconds": 2,
  "dialogue_groups": {"dialogue_01": {"start": 44, "end": 46}},
  "anchors": {"anchor_A": {"start": 25}}
}
```

参考只在顺序匹配完成后作比较，不参与转写、配句或强制时间窗口。此比较分支的参考缺项、指纹不符、非有限时码、超过 2 秒、漏词、重复句归属不确定、分组覆盖或剧本说话者缺失均不能采用通过。重复 JSON 键会明确拒绝；不能用后一个值悄悄覆盖前一个。没有参考时码时走下方的候选确认入口，不要求用户补整套时码。

```sh
.codex_tmp/audio_v3/venv/bin/python tools/local_audio/localize.py \
  --audio '/absolute/path/episode.mp3' \
  --script '/absolute/path/english_script.txt' \
  --episode 20 \
  --dialogue-docx '/absolute/path/breakdown.docx' \
  --anchors-json '/absolute/path/anchors.json' \
  --reference-times-json '/absolute/path/user_reference_times.json' \
  --cache .codex_tmp/audio_v3 \
  --out .codex_tmp/audio_v3/current_result
```

保留完整 MP3／WAV；本机以 ffmpeg 解码至 16 kHz 单声道 PCM，所有词时码与短 WAV 仍映射回输入文件原点。结果不裁掉开头静音或重置剪辑版本。输入文件 SHA 与解码 PCM SHA 都写入本地结果，用内容确认版本，不凭名称或历史总长认定同一音轨。

## 无参考时码的日常入口

省略 `--reference-times-json` 即正常输出候选对白组、`--anchors-json` 指定的内容段首及 `review.md` 的一次确认摘要。段首来自当前剧本单位与既有分段决定，不猜旧秒数，也不由这个音频工具重做导演分段。Codex整理原句、剧本说话者、候选区间及少数疑点；用户只需回复整体采用或指出局部问题，可随既有分段确认一起完成，无需填写JSON或整套时码。

未回复或未明确确认时，`automatic_pass: false`、`adoption_status: "candidate_pending_user_confirmation"`；硬性文本／归属缺项则为 `candidate_requires_correction`。工具同时生成本地 `candidate_confirmation_request.json`，默认 `confirmed: false`。**Codex只能在用户真实明确回复后保存确认事实**，复制该模板到结果目录外，记录 `basis: "user_explicit"`、`confirmed: true` 和真实回复摘要；摘要须为非空白字符串，缺失／空白／非字符串均不得保存用户确认事实或采用，不靠关键词猜认可。再以 `--candidate-confirmation-json` 运行到另一个输出目录。不把候选时码抄成独立参考，不从沉默推断同意。这个参数与 `--reference-times-json` 互斥。

确认同时绑定输入音频 `audio_file_sha256` 和 `candidate_content_sha256`。完整候选包含正文单位原文、说话者、归属、估计首尾、对白组、全部请求段首、遗漏／疑点、原点、解码内容及来源内容SHA；路径、耗时和确认记录不参与其指纹。任何内容变更均使旧确认失效；改剧本／分组／段首仍只重新匹配已缓存词表。匹配缺词、重复归属不确定、对白说话者或段首缺失等硬性问题不会被一条确认掩盖。

确认通过时为 `automatic_pass: true`、`adoption_status: "user_confirmed_candidates"`，`candidate_confirmation.confirmation_fact` 保存带UTC记录时间的明确回复事实。该分支无独立参考时码，`maximum_absolute_difference_seconds: null`；不声称满足 ≤2 秒参考差，`playback_verified: false` 与实测误差 `null` 继续保留。测试演练必须用 `basis: "test_simulation"`：仅 `simulated_adoption_pass: true`，真实采用和真实用户确认均为 false，状态为 `candidate_confirmation_simulated`。

## 输出、缓存与复核

- `result.json`：原台词、工具估计区间、遗漏／转写差异、短句与未确定边界、对白组和段首。`reference_comparison` 记录独立用户参考的逐点差、最大差及阻断原因；此分支通过时为 `user_reference_passed`。`candidate`、内容指纹及 `candidate_confirmation` 独立保存候选和明确确认事实，采用状态区分待确认、用户确认及测试演练。`playback_verified: false` 和 `measured_boundary_error_seconds: null` 明确保留听检未做。
- `review.md`＋`review_clips/*.wav`：关键短段和原点映射，便于一次核对对白组词首、词尾、短句和段首。完整词表只留本地缓存，导演读取所需句段和疑点即可。
- 转写缓存由解码音频内容 SHA、工具版本、模型 revision 和参数决定。相同内容复用完整词表，剧本变更只重新匹配；提示词变更不重转音频。`--force-transcribe` 仅为明确的性能测试或重转请求绕过缓存。

模型本地 manifest 保存固定 repo／revision 和配置、权重 SHA；已核验模型离线复用，日常与强制 warm 测试不重复询问远端。词表缓存同时核对 payload SHA、schema 与有限非负单调时码；破坏明确拒绝并提示显式重转。输出与输入检查 resolved path／hardlink 碰撞，写短段前禁止覆盖原音频等输入，并核对处理前后输入 SHA。

顺序全局词对齐避免把同一句复用到两处。与 ASR 不一致的词、被删句和重复句的未匹配部分显式保留；边界用实际匹配到的词估计，不为缺词补造秒数。零时长、不完整首尾和未配对的正文 ASR 内容阻断采用；低置信词及短句 `I...` 保留可选精检提示，不能写成已听检。相同文字重复且上下文也无法区分时，仍可能无法判断到底是哪处被删除；不要把一次单调配对写成音频真值。正文前后额外 ASR 内容仍显示警告，不能据此平移原文件原点。

日常目标先测 1 分钟内；处理超过 2 分钟时检查结果中的分阶段耗时，区分模型下载、冷启动、转写、匹配和缓存。首次安装和下载单列，不能用缓存读取速度冒充第一次处理速度。

已有参考时码的采用门槛按用户确认：对白组首尾和段首与用户参考时码相差不超过 2 秒即可通过并使用。恰好 2 秒可通过，超出或存在上述阻断项则不通过。无参考时按明确整体候选确认采用，不能自证参考差。此差值只表示对用户参考的一致性，时间网格和文本一致率均不能证明实际边界精度；没有实际播放真值时不得报告实测误差。用户仍可按短段局部精检或纠正，不再把完成 ±0.3 秒听检设为采用前置条件。

本次 Codex 普通沙箱无法访问 Metal GPU；安装和本机转写在用户授权的本机执行权限下完成。若同样出现 `No Metal device available`，须用可访问 GPU 的本机终端／获授权执行环境；已有词表的本地匹配和缓存读取不需要加载 MLX。

## 依据与验收

[MLX Whisper 官方用法](https://github.com/ml-explore/mlx-examples/tree/main/whisper)支持 `word_timestamps=True`；[官方 transcribe 实现](https://github.com/ml-explore/mlx-examples/blob/main/whisper/mlx_whisper/transcribe.py)通过 cross-attention 与 DTW 估计词时间，而非人工真值。[固定模型来源](https://huggingface.co/mlx-community/whisper-small.en-mlx/commit/52a88bf6e98b114a210c21bb83e22d6e1505cb73)和 [decoder 发行包](https://pypi.org/project/imageio-ffmpeg/0.6.0/)可核对。

```sh
python3 -m unittest discover -s tools/local_audio -p 'test_*.py' -v
```

有意义的验收覆盖：重复句不能复用同一词、少一次同文重复不能判定唯一归属、删除对白不能借后句、截断首尾不可冒充完整边界、短句零时长提示、改剧本复用词表、离线模型与篡改拒绝、原音频碰撞保护及缓存词时码校验；用户参考恰好 2 秒通过、超过／缺项／错指纹／错配拒绝；候选沉默不采用、显式事实保存、内容变更使确认失效、模拟确认不冒充真实用户采用，并始终区分采用通过和听检真值。真实样本的匿名性能与验证限制见[验收报告](validation_report.md)。

# 可选本机英文音频定位

只在 Apple silicon Mac 上用 MLX Whisper 准备原音轨的估计时间对应。它不参加每轮导演判断，也不替代剧本、三时轴或原有人工定位。当前状态是本机验证工具；实际播放边界尚待复核，不自动通过。

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

```sh
.codex_tmp/audio_v3/venv/bin/python tools/local_audio/localize.py \
  --audio '/absolute/path/episode.mp3' \
  --script '/absolute/path/english_script.txt' \
  --episode 20 \
  --dialogue-docx '/absolute/path/breakdown.docx' \
  --anchors-json '/absolute/path/anchors.json' \
  --cache .codex_tmp/audio_v3 \
  --out .codex_tmp/audio_v3/current_result
```

保留完整 MP3／WAV；本机以 ffmpeg 解码至 16 kHz 单声道 PCM，所有词时码与短 WAV 仍映射回输入文件原点。结果不裁掉开头静音或重置剪辑版本。输入文件 SHA 与解码 PCM SHA 都写入本地结果，用内容确认版本，不凭名称或历史总长认定同一音轨。

## 输出、缓存与复核

- `result.json`：原台词、工具估计区间、遗漏／转写差异、短句与未确定边界、对白组和段首；一直保留 `automatic_pass: false`。
- `review.md`＋`review_clips/*.wav`：关键短段和原点映射，便于一次核对对白组词首、词尾、短句和段首。完整词表只留本地缓存，导演读取所需句段和疑点即可。
- 转写缓存由解码音频内容 SHA、工具版本、模型 revision 和参数决定。相同内容复用完整词表，剧本变更只重新匹配；提示词变更不重转音频。`--force-transcribe` 仅为明确的性能测试或重转请求绕过缓存。

模型本地 manifest 保存固定 repo／revision 和配置、权重 SHA；已核验模型离线复用，日常与强制 warm 测试不重复询问远端。词表缓存同时核对 payload SHA、schema 与有限非负单调时码；破坏明确拒绝并提示显式重转。输出与输入检查 resolved path／hardlink 碰撞，写短段前禁止覆盖原音频等输入，并核对处理前后输入 SHA。

顺序全局词对齐避免把同一句复用到两处。与 ASR 不一致的词、被删句和重复句的未匹配部分显式保留；边界用实际匹配到的词估计，不为缺词补造秒数。短句 `I...`、零时长、低置信词和不完整首尾需要人工复核。相同文字重复且上下文也无法区分时，仍可能无法判断到底是哪处被删除；不要把一次单调配对写成音频真值。

日常目标先测 1 分钟内；处理超过 2 分钟时检查结果中的分阶段耗时，区分模型下载、冷启动、转写、匹配和缓存。首次安装和下载单列，不能用缓存读取速度冒充第一次处理速度。

首轮关键边界核查目标约 ±0.3 秒，但时间网格和文本一致率均不能证明实际精度。没有实际播放真值时只报告一致性，用户继续人工定位／局部纠正；不宣称自动定位已通过团队验收。待对白组与段首实际复核通过，再把“完整英文剧本＋MP3／WAV”接为可选准备入口。

本次 Codex 普通沙箱无法访问 Metal GPU；安装和本机转写在用户授权的本机执行权限下完成。若同样出现 `No Metal device available`，须用可访问 GPU 的本机终端／获授权执行环境；已有词表的本地匹配和缓存读取不需要加载 MLX。

## 依据与验收

[MLX Whisper 官方用法](https://github.com/ml-explore/mlx-examples/tree/main/whisper)支持 `word_timestamps=True`；[官方 transcribe 实现](https://github.com/ml-explore/mlx-examples/blob/main/whisper/mlx_whisper/transcribe.py)通过 cross-attention 与 DTW 估计词时间，而非人工真值。[固定模型来源](https://huggingface.co/mlx-community/whisper-small.en-mlx/commit/52a88bf6e98b114a210c21bb83e22d6e1505cb73)和 [decoder 发行包](https://pypi.org/project/imageio-ffmpeg/0.6.0/)可核对。

```sh
python3 -m unittest discover -s tools/local_audio -p 'test_*.py' -v
```

有意义的验收覆盖：重复句不能复用同一词、少一次同文重复不能判定唯一归属、删除对白不能借后句、截断首尾不可冒充完整边界、短句零时长提示、改剧本复用词表、离线模型与篡改拒绝、原音频碰撞保护及缓存词时码校验。真实样本的匿名性能与验证限制见[验收报告](validation_report.md)。

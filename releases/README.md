# 核心学习包发行目录

这里保存用户明确要求发布的干净核心学习包。

- `latest.json`记录当前版本、文件名、文件数、体积和SHA-256。
- 同名`.zip.sha256`用于校验压缩包完整性。
- 不自动重新打包；只有用户明确要求更新时，才通过`packaging/build_core_package.py`发布新版本。
- 历史项目、素材、审片、旧提示词、旧2.0 Skill和团队SOP不会进入核心包。

1.2.0（2026-10-14）发布为V3.2试制版，标签`core-v1.2.0`、分支`codex/director-v3-2`；GitHub Release为prerelease。默认完整输入与一次集中审核，受控常规内部采用路径已实现/测试，启用等真实认可落盘。规则／工具与入口静态/模拟验收不等于独立新窗口或实片通过；网页未合入／未完整实测。旧1.0.0、1.1.0、1.1.1、1.1.2和标签保留。

包内只含显式核心白名单、匿名验收与空项目索引，不含真实项目、媒体、模型、缓存、聊天或本机路径。下载ZIP后以同名`.zip.sha256`核完整性。`latest.json`描述当前试制包，main不切换为本版。

Core 1.3.0为V3.3本地候选包，尚未推送分支、标签或GitHub Release；latest.json若指向1.3.0表示本地构建结果，不代表远端已发布。旧1.2.0远端发布保持。

Core 1.4.0（2026-10-14）为[ V3.4短剧表现力与结构改定试制版](https://github.com/zengyies-ux/AIGC_Vedio_codex/releases/tag/core-v1.4.0)，分支`codex/director-v3-4`、标签`core-v1.4.0`，GitHub为prerelease。当前`latest.json`为该包的构建信息，远端发布另以Release及回读校验为依据。规则／工具／匿名文本验收见[本版说明](../validation/director_v34.md)；新实片及网页执行未验证，网页技能未合入。旧版本原样保留。

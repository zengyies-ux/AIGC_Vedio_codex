# 核心学习包发行目录

这里保存用户明确要求发布的干净核心学习包。

**当前正式发布：[Core1.7.1](https://github.com/zengyies-ux/AIGC_Vedio_codex/releases/tag/core-v1.7.1)**。Windows优先SOP及完整启动词已入包；当前Mac整集真实链获用户认可，Windows x64适配已提供、真机待验。以下各版本说明均为历史时点。

- `latest.json`记录当前版本、文件名、文件数、体积和SHA-256。
- 同名`.zip.sha256`用于校验压缩包完整性。
- 不自动重新打包；只有用户明确要求更新时，才通过`packaging/build_core_package.py`发布新版本。
- 历史项目、素材、审片、旧提示词、旧2.0 Skill和团队SOP不会进入核心包。

1.2.0（2026-10-14）发布为V3.2试制版，标签`core-v1.2.0`、分支`codex/director-v3-2`；GitHub Release为prerelease。默认完整输入与一次集中审核，受控常规内部采用路径已实现/测试，启用等真实认可落盘。规则／工具与入口静态/模拟验收不等于独立新窗口或实片通过；网页未合入／未完整实测。旧1.0.0、1.1.0、1.1.1、1.1.2和标签保留。

包内只含显式核心白名单、匿名验收与空项目索引，不含真实项目、媒体、模型、缓存、聊天或本机路径。下载ZIP后以同名`.zip.sha256`核完整性。`latest.json`描述当前试制包，main不切换为本版。

Core 1.3.0为V3.3本地候选包，尚未推送分支、标签或GitHub Release；latest.json若指向1.3.0表示本地构建结果，不代表远端已发布。旧1.2.0远端发布保持。

Core 1.4.0（2026-10-14）为[ V3.4短剧表现力与结构改定试制版](https://github.com/zengyies-ux/AIGC_Vedio_codex/releases/tag/core-v1.4.0)，分支`codex/director-v3-4`、标签`core-v1.4.0`，GitHub为prerelease。当前`latest.json`为该包的构建信息，远端发布另以Release及回读校验为依据。规则／工具／匿名文本验收见[本版说明](../validation/director_v34.md)；新实片及网页执行未验证，网页技能未合入。旧版本原样保留。

Core 1.5.0（2026-10-15）为[V3.5剪辑余量与填稿试制版](https://github.com/zengyies-ux/AIGC_Vedio_codex/releases/tag/core-v1.5.0)，分支`codex/director-v3-5`、标签`core-v1.5.0`，prerelease。额外6—10秒素材，身份／空间／下游及视频引用核对；网页正文／6图片节点重访保留，参数只同页通过，生成和完整延长未执行。详细范围见[匿名说明](../validation/director_v35.md)，实际远端以Release与附件回读为准。旧包与main不变。

Core 1.5.1（2026-10-15）为[V3.5独立原生段多卡填稿补验补丁](https://github.com/zengyies-ux/AIGC_Vedio_codex/releases/tag/core-v1.5.1)，沿`codex/director-v3-5`使用全新标签，不覆盖1.5.0。保留19秒卡、新建26秒七图卡，正文／节点往返持久通过，逐卡时长返回4秒后恢复、仅同页正确；模型／分辨率和卡映射核对补齐。无生成或完整延长，实际发布以Release及附件回读为准。

Core1.6.0（2026-10-15）为V3.6本地候选，未推送／标签或GitHub Release；`latest.json`表示本机构建，不表示远端发布。两条延长准备已实测，新增秒数重访回5后恢复、只当前同页正确；未生成或验证延长成片。详见[匿名说明](../validation/director_v36.md)，此前公开点仍core-v1.5.1，旧发行物不覆盖。

Core1.6.1（2026-10-15）是V3.6工作分支候选，修资产阶段适配放行、必要局部核源／待源续做与Codex部署入口；只推codex/director-v3-6供审查，未创建本版tag／Release，不能当稳定发布。latest.json现表示1.6.1候选构建，历史各版本段落记录当时发布状态；1.6.0旧ZIP及全部旧发行物保持。默认main仍旧备份，当前公开Release入口仍core-v1.5.1（prerelease）。[唯一部署说明](../DEPLOYMENT.md)区分发布包、分支候选、制作目录及受支持环境；[匿名验收](../validation/director_v36.md)列已验与待验。

Core1.7.0（2026-10-16）为V3.7工作分支候选，包含可恢复执行规程／轻量回执日志、三入口、Windows x64 CPU音频及环境自检；保跨集独立、不出图、提交前设秒、模式保护等主线修正。只推codex/director-v3-7供验收，无本版tag／Release，不改main及旧发行物；latest.json是候选构建信息。Mac／CPU宿主与模拟通过不等于Windows或生产整链通过，边界见[本版说明](../validation/director_v37.md)，部署沿[唯一说明](../DEPLOYMENT.md)。

# Aelthoren

**Lightweight. Private. Account-free.**
**轻量 · 隐私 · 无账户**

**Project Status: Completed Proof of Concept — Maintenance Discontinued**
**项目状态：概念验证已完成，停止维护**

---

## 🇨🇳 中文介绍

### 项目简介

**Aelthoren** 是一款基于 Mozilla Firefox / Gecko 技术的实验性开源浏览器，最初作为未来 **Evavind OS（埃瓦文德操作系统）** 浏览器的概念验证项目而开发。

本项目的目标不是从零开发浏览器内核，也不是提供一款能够长期替代 Firefox 的成熟浏览器，而是探索轻量化、隐私保护、无账户设计，以及基于 Gecko 开发独立浏览器的技术可行性。

Aelthoren 0.1.0-alpha 已完成主要概念验证，并在 Linux 环境中进行过实际运行测试。

**本概念版已结束开发，不再提供持续维护。**

### 主要功能

- 基于真正的 Gecko 渲染引擎与 SpiderMonkey JavaScript 引擎。
- 独立的 Aelthoren 名称、Logo 与新标签页。
- DuckDuckGo 作为默认搜索引擎，允许用户自行修改。
- 无内置浏览器账户及云同步服务。
- 隐私保护、追踪器拦截及存储分区配置。
- 本地用户配置、书签和历史记录。
- 基础的多标签页、地址栏和网页导航功能。
- Linux x86_64 实验性构建与打包脚本。

### 技术架构

Aelthoren 采用 Mozilla Firefox 的源码与应用层架构，使用 Gecko / SpiderMonkey 实现网页渲染和 JavaScript 执行。

项目主要通过应用层修改、配置、品牌资源和构建脚本实现其概念设计。

当前开发流程使用 Mozilla 官方预编译 Gecko 组件（Artifact Build），**并不代表已经独立编译或开发 Gecko 内核**。

上游基线：

- Firefox ESR：`153.6.0esr`
- 源码提交：`a34c4160e3f75ab9918fbe4669ff7ae56f1977c8`
- 实验平台：Linux x86_64
- Windows 原生版本：未实现

### 如何构建？

本项目仅发布源码，不提供官方浏览器二进制分发，也不提供安全更新。历史开发构建产物仅为不受支持的测试输出，不是官方发行版。

有兴趣的开发者可以通过以下方式尝试构建：

**方式一：手动构建**

阅读 [BUILDING.md](BUILDING.md) 和 [Linux 构建说明](docs/LINUX_RELEASE.md)，了解所需工具链、上游源码、依赖及构建限制。

**方式二：AI 辅助构建**

阅读 [AI_BUILD_GUIDE.md](AI_BUILD_GUIDE.md)，使用 Codex、Claude Code 或其他 AI 编程助手协助配置环境、获取依赖、执行构建与测试。

AI 构建并不保证成功，使用者仍需自行验证程序的完整性、安全性与许可证合规性。

### 安全警告

**Aelthoren 0.1.0-alpha 仅用于技术研究和概念验证，不建议用于日常或安全敏感的网页浏览。**

本项目：

- 不提供持续的 Gecko 安全更新。
- 不提供独立的自动更新机制。
- 尚未完成完整的原生应用身份分离。
- 未经过全面的跨发行版兼容性验证。
- 不保证匿名性、绝对隐私或优于 Firefox 的性能。
- 不保证任何第三方自行构建的版本能够安全运行。

请不要将历史构建产物视为获得长期安全维护的浏览器。

### 许可证与版权

本项目的原创工具、测试夹具及文档遵循仓库 [LICENSE](LICENSE) 中规定的 MIT 许可证适用范围。

Mozilla Firefox、Gecko、SpiderMonkey 及其他第三方代码和资源，继续遵循其各自的开源许可证，包括适用的 MPL 2.0 条款。

Aelthoren 官方 Logo 的权利独立保留，不因项目代码采用 MIT 许可证而自动获得品牌使用授权。

详情参见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

Aelthoren 是独立实验项目，不隶属于 Mozilla，也不受 Mozilla 赞助或认可。

### 未来规划

当前 Aelthoren 概念版不会继续维护。

未来如果 Evavind OS 的开发进入相应阶段，可能会启动新的 Aelthoren 浏览器研发工作，并重新设计与 Evavind / Orfreon 的系统集成方案。

未来版本不一定直接继承本概念版的源码或架构；本仓库不承诺未来开发、发布或维护。

---

## 🇬🇧 English

### Overview

**Aelthoren** is an experimental open-source browser based on Mozilla Firefox and Gecko technology.

It was created as a proof of concept for a possible future web browser in the **Evavind OS** ecosystem.

The purpose of this project is not to develop a rendering engine from scratch or create a long-term Firefox replacement. Instead, it explores lightweight design, privacy-oriented defaults, account-free browsing, and the feasibility of building an independent browser product using Gecko.

Aelthoren 0.1.0-alpha completed its initial proof-of-concept milestones and was tested in Linux environments.

**The concept project has concluded and is no longer actively maintained.**

### Features

- Genuine Gecko rendering engine and SpiderMonkey JavaScript engine.
- Aelthoren branding, logo and custom new-tab page.
- DuckDuckGo as the changeable default search engine.
- No integrated browser account or cloud synchronization service.
- Tracking protection and storage partitioning.
- Local browser profiles, bookmarks and history.
- Basic tabs, address bar and navigation.
- Experimental Linux x86_64 build and packaging workflow.

### Architecture

Aelthoren uses Mozilla Firefox's source and application architecture, with customized application resources, configuration, branding and tooling.

The development workflow uses official Mozilla precompiled Gecko components through Artifact Builds.

It does **not** constitute an independently developed or fully source-compiled Gecko engine.

Upstream baseline:

- Firefox ESR: `153.6.0esr`
- Source revision: `a34c4160e3f75ab9918fbe4669ff7ae56f1977c8`
- Experimental platform: Linux x86_64
- Native Windows build: Not implemented

### Building Aelthoren

This is a source-only publication: there is no official browser binary distribution and no security updates. Historical development artifacts are unsupported test outputs, not official releases.

Developers may explore two approaches:

**Manual build**

See [BUILDING.md](BUILDING.md) and [Linux release documentation](docs/LINUX_RELEASE.md) for prerequisites, source acquisition, dependencies, build procedures and limitations.

**AI-assisted build**

See [AI_BUILD_GUIDE.md](AI_BUILD_GUIDE.md) for instructions intended for Codex, Claude Code and other coding assistants.

AI-assisted builds are not guaranteed to succeed. Users must independently verify their builds and respect applicable licensing and distribution requirements.

### Security Notice

**Aelthoren 0.1.0-alpha is intended for research and experimentation, not daily or security-sensitive browsing.**

This project:

- Does not receive ongoing Gecko security updates.
- Does not provide an independent automatic update system.
- Does not have fully independent native application identity.
- Has not been comprehensively validated across Linux distributions.
- Does not guarantee anonymity, absolute privacy or superior performance.
- Does not guarantee the security of third-party builds.

Historical build artifacts must not be treated as maintained browser releases.

### License and Attribution

Original Aelthoren tools, fixtures and documentation are distributed under the MIT License within the scope described in [LICENSE](LICENSE).

Mozilla Firefox, Gecko, SpiderMonkey and third-party components retain their respective licenses, including applicable MPL 2.0 obligations.

The official Aelthoren logo remains separately owned and is not automatically licensed for trademark or branding use under the repository's MIT License.

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for details.

Aelthoren is an independent experimental project and is not affiliated with, sponsored by, or endorsed by Mozilla.

### Future Development

The current Aelthoren prototype will not be actively maintained.

A future browser project may be developed for Evavind OS, with deeper integration into the Evavind and Orfreon architecture.

Such a project may use a different implementation and is not guaranteed to continue directly from this prototype. This repository makes no commitment to future development, releases or maintenance.

---

## Documentation / 项目文档

| Document | Description / 说明 |
|---|---|
| [BUILDING.md](BUILDING.md) | Build instructions / 构建指南 |
| [AI_BUILD_GUIDE.md](AI_BUILD_GUIDE.md) | AI-assisted build / AI 辅助构建 |
| [PRIVACY.md](PRIVACY.md) | Privacy design / 隐私设计 |
| [SECURITY.md](SECURITY.md) | Security limitations / 安全限制 |
| [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) | Licensing and attribution / 第三方许可 |
| [VALIDATION.md](VALIDATION.md) | Testing records / 测试记录 |
| [docs/BRANDING_AUDIT.md](docs/BRANDING_AUDIT.md) | Branding audit / 品牌审计 |
| [docs/LINUX_RELEASE.md](docs/LINUX_RELEASE.md) | Linux packaging / Linux 打包 |

---

**Aelthoren — An experimental step toward the future Evavind browser.**

*Aelthoren 是面向未来 Evavind 浏览器的一次技术探索。*

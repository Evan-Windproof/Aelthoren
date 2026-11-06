# AI-Assisted Build Guide / AI 辅助构建指南

This guide is intended for developers who want to experiment with building Aelthoren using AI coding assistants such as OpenAI Codex or Anthropic Claude Code.

本指南面向希望使用 Codex、Claude Code 等 AI 编程助手尝试构建 Aelthoren 的开发者。

**Warning / 警告：** Aelthoren is an unmaintained proof of concept prepared for source-only archival; this guide does not mean the GitHub repository has already been archived. It is not maintained and should not be used for daily or security-sensitive browsing.

Aelthoren 是已停止维护的概念验证项目，不建议用于日常或安全敏感的网页浏览。

There is no official binary distribution or security-update service. Mozilla-covered code retains its upstream licenses; the official Aelthoren logo is separately protected and is not relicensed by the repository MIT License. See [LICENSE](LICENSE), [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [README.md](README.md).

本项目不提供官方二进制分发或安全更新。Mozilla 涵盖的代码保留其上游许可证，官方 Logo 的权利独立保留，不因仓库采用 MIT 许可证而改变。

## Prerequisites / 前置条件

A Linux x86_64 development environment is recommended.

建议使用 Linux x86_64 开发环境。项目原先主要在 Debian / Ubuntu 环境中验证，项目维护者另报告 Arch Linux 曾完成概念版的实际启动测试（这不是本次文档整理中新执行或独立验证的结果），但不同版本的兼容性不能直接推定。

Developers should have Git, Python, sufficient disk space, and access to the official Mozilla source and artifact services.

Users must comply with applicable Mozilla and third-party licenses.

## Clone / 克隆仓库

```bash
git clone https://github.com/Evan-Windproof/Aelthoren.git
cd Aelthoren
```

## AI build prompt / AI 构建提示词

Copy the following prompt into Codex or Claude Code in the cloned repository.

将下列提示词复制到 Codex 或 Claude Code，并让它在克隆好的仓库中执行。

---

### Build Aelthoren from the Source-Only Repository

You are acting as a Linux build engineer assisting with an unmaintained, source-only experimental browser project called **Aelthoren**.

Repository:

https://github.com/Evan-Windproof/Aelthoren

The objective is to reproduce the existing Gecko-based Aelthoren concept build using the repository's documented tools and scripts.

Do not rewrite the browser from scratch.

#### Step 1 — Inspect the repository

Read and understand:

- README.md
- BUILDING.md
- UPSTREAM.md
- SECURITY.md
- THIRD_PARTY_NOTICES.md
- upstream.lock.json
- docs/LINUX_RELEASE.md
- docs/BRANDING_AUDIT.md

Inspect the current tools, patches, configuration and packaging directories.

Determine whether the archived instructions assume Codex-specific paths such as `/workspace/Aelthoren`, and adapt them safely to the actual environment.

Do not assume the original cloud workspace still exists.

#### Step 2 — Verify the environment

Check:

- Linux distribution and architecture
- Available disk space
- CPU and RAM
- Required compilers and development utilities
- Python and Node.js versions
- Mozilla build prerequisites
- Network access to official Mozilla repositories and artifact services

Follow the appropriate official Mozilla build documentation when dependencies have changed.

Do not disable TLS verification, integrity checks, browser sandboxing or other security protections.

#### Step 3 — Preserve upstream authenticity

Use genuine Mozilla Gecko and SpiderMonkey.

Read `upstream.lock.json` and honor the pinned source revision and artifact hashes for historical reproduction.

Do not silently replace the pinned release with a newer one.

If the original artifacts cannot be obtained, report that limitation.

If a newer supported Gecko version is necessary for further experiments, treat that as a separate, explicitly identified porting task rather than claiming an exact reproduction.

Do not use Chromium, Electron, WebView2 or another browser engine as a substitute.

#### Step 4 — Prepare the project

Examine the existing Aelthoren build workflow.

The historical development procedure uses:

```bash
python3 tools/phase3.py prepare
python3 tools/phase3.py build
```

These are reference commands, not a guarantee that they will work unchanged on a new machine.

Determine and install missing dependencies using trusted sources.

Do not overwrite unknown files, silently reset source trees or bypass revision checks.

Reuse existing verified artifacts where possible.

#### Step 5 — Apply Aelthoren customization

Preserve:

- Official Aelthoren branding
- Custom new-tab interface
- DuckDuckGo search defaults
- Account-free configuration
- Privacy and tracking protection
- Isolated user profiles
- Reviewed final branding resource replacements

Inspect the final branding overlay under `branding/` and `tools/final_branding.py`.

Do not reintroduce Mozilla product artwork that was intentionally removed.

Retain mandatory Mozilla copyright, license and source-attribution information.

#### Step 6 — Build and test

Attempt the documented Gecko Artifact Build workflow.

Verify:

- Real Gecko rendering
- SpiderMonkey JavaScript execution
- DOM and storage
- HTTPS
- Browser navigation
- Search engine behavior
- Local profile isolation
- Privacy settings
- Browser startup

Do not claim that Gecko was compiled from C++/Rust source when using Mozilla precompiled artifacts.

Distinguish actual GUI testing from headless testing.

#### Step 7 — Package a development build

After successful tests, inspect the existing packaging workflow:

```bash
python3 tools/package_linux.py
```

Produce a local development archive when feasible.

Do not publish it automatically.

Preserve all required licenses and source notices.

Respect Mozilla trademark restrictions and the rights associated with the Aelthoren logo.

A successful package build does not establish permission to redistribute the resulting modified browser.

#### Step 8 — Report the results

Provide:

1. Operating system and toolchain versions.
2. Exact upstream revision and artifacts used.
3. Build commands executed.
4. Actual build and test results.
5. Output artifact paths.
6. Known failures and compatibility limitations.
7. Any changes made to reproduce the build.
8. Remaining licensing, branding and security limitations.

Do not fabricate successful results.

Do not claim the resulting browser is production-ready.

Do not automatically publish a release, archive the repository, or modify the upstream GitHub repository. This guide is for optional local reproduction; it does not authorize any of those actions.

The goal is to reproduce and study Aelthoren as an experimental browser, not to create an unsupported commercial or production browser.

---

## Notes / 说明

**中文：** AI 编程助手可以帮助解决环境依赖、构建错误和脚本适配问题，但不会自动保证构建成功、浏览器安全或软件许可证合规。

**English:** AI coding assistants can help configure the environment, diagnose build errors and adapt scripts, but they cannot guarantee successful builds, browser security or legal compliance.

For official Mozilla build documentation, see:

https://firefox-source-docs.mozilla.org/

For Mozilla licensing:

https://www.mozilla.org/MPL/2.0/

For Mozilla distribution and trademark requirements:

https://www.mozilla.org/en-US/foundation/trademarks/distribution-policy/

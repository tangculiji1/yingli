# 把它变成你自己的 iOS App

这份文档只讲 iPhone / iPad。代码来自 [jo32/tvbox-silicon](https://github.com/jo32/tvbox-silicon)（GPL-3.0），本仓库是它的修改版。

## 先说清楚代价

- **第一次云端构建要 2～4 小时**（要现场编译内嵌的 JVM），之后有缓存会快很多。
- 你**没有 Mac**，所以只能在 GitHub 的 macOS 机器上编译，产物是**未签名**的 IPA，再由 Windows 上的工具用你自己的 Apple ID 签名装进手机。
- 免费 Apple ID 签出来的 App **7 天过期**，过期后要重新签一次（数据不丢，重签覆盖安装即可）。
- 作者本人也是这么发布的，这条路是通的；但我没法在这里替你跑编译，第一次失败要靠日志修。

## 你需要

1. 一个 GitHub 账号（仓库设为 **Public**，macOS 构建分钟数才免费）。
2. 一台 Windows 电脑 + 数据线。
3. 你的 Apple ID（免费账号就够）。
4. 手机系统 iOS 17 或更高。

## 第 1 步：把源码放到 GitHub

推荐用 [GitHub Desktop](https://desktop.github.com/)（Windows）：

1. 新建仓库，名字随意，**Public**，不要勾选 README。
2. 把这个文件夹里的全部内容拷进去，提交并 Push。
   - 总共约 150 MB，第一次上传要几分钟。
   - 不要上传 `build/` 目录（已在 `.gitignore` 里）。

或者用命令行（装了 git 的话）：

```powershell
git init
git add .
git commit -m "init"
git branch -M main
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git push -u origin main
```

## 第 2 步：让 GitHub 编译

1. 打开仓库页面 → **Actions** → 左边选 **Build iOS IPA** → 右边 **Run workflow** → 绿色按钮。
2. 等 2～4 小时。中间 `Build embedded JVM runtime` 那一步最久，是正常的。
3. 成功后在该次运行页面底部下载 **ios-ipa** 这个 artifact，解开就是 `Yingxia-ios-unsigned.ipa`。

失败的话，把日志里红色的部分发给我，我改。

## 第 3 步：Windows 上签名并安装

先装 [iTunes](https://apps.microsoft.com/detail/9pb2mzyzqm3f)（微软商店版，提供苹果设备驱动），然后 PowerShell：

```powershell
$dir = "$env:LOCALAPPDATA\cider"
New-Item -ItemType Directory -Force $dir | Out-Null
curl.exe -L -o "$env:TEMP\cider.zip" https://github.com/Muonagi/cider-cli/releases/latest/download/cider-x86_64-pc-windows-msvc.zip
Expand-Archive "$env:TEMP\cider.zip" $dir -Force
[Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path", "User") + ";$dir", "User")
```

**重开一个 PowerShell 窗口**，然后：

```powershell
cider account login            # 输入你的 Apple ID、密码、双重认证码
cider device list
cider device trust             # 手机上点“信任”
cider sign Yingxia-ios-unsigned.ipa --apple-id --install --refresh
```

装完在手机上：

1. **设置 → 通用 → VPN 与设备管理** → 信任你的开发者证书。
2. **设置 → 隐私与安全性 → 开发者模式** → 打开并重启。

## 第 4 步：7 天续签

到期前把手机连上电脑，再跑一次：

```powershell
cider sign Yingxia-ios-unsigned.ipa --apple-id --install --refresh
```

用同一个 Apple ID 重签会覆盖安装，订阅、收藏、播放记录都在。想省事就买个 99 美元/年的开发者账号，签一次管一年。

## 改名字、图标、包名

- **显示名称**：`project.yml` 里的 `CFBundleDisplayName`（两处），以及 `Config/Info-TVBox-*.plist`。
- **包名**：`project.yml` 里的 `PRODUCT_BUNDLE_IDENTIFIER`（macOS / iOS / tvOS 各一处）。现在的 iOS 包名是 `com.yingchao.player`，和原版不同，所以能和原版同时装。
- **图标**：`Config/iOS/Assets.xcassets/AppIcon.appiconset/`，换掉里面的 PNG 即可，尺寸要和 `Contents.json` 对上。

## 这一版动了什么

- 显示名称改为「影巢」，包名改为 `com.yingchao.player`，不会和原版冲突。
- 关闭了对原作者服务器的依赖：错误上报、反馈、公告、版本更新检查现在都指向本机空地址（`127.0.0.1:9`），不会把你的数据发出去。
- **保留**了 TMDB 元数据代理（`yingxia-tmdb.getmegaportal.com`），它只用来取海报和剧集信息；不想要可以在 `Sources/TVCore/TMDBMatch.swift` 里改掉，代价是封面和简介没了。
- 版权行改为「© 2026 影巢 · 基于 Yingxia（GPL-3.0）」，`LICENSE` 原样保留。

## 合规

- GPL-3.0：你自己用没问题；**分发给别人**时必须同时提供源码（公开仓库就满足了），且不能去掉原作者的版权声明。
- 这个 App 只是播放器，不带任何内容。你添加的订阅源是否合法，由你负责。

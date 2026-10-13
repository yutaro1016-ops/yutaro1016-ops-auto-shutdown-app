# AutoShutdown

Windows 10 / Windows 11向けの「指定時刻シャットダウン」GUIアプリです。

## 主な機能

- デスクトップのショートカットから起動
- 24時間表記で時・分を指定
- 現在時刻より前の時刻は翌日として自動解釈
- 30分後／1時間後／2時間後／3時間後プリセット
- Windowsタスクスケジューラへ1件だけ予約
- GUIを閉じても予約は維持
- 予約取消
- 強制終了オプションは初期OFF
- Python未導入PC向けに単一EXEへビルド可能

## 安全上の注意

通常設定では `shutdown.exe /s /t 0` を使用し、`/f` は付けません。そのため、未保存データを持つアプリが終了を妨げる場合があります。GUIの「実行中アプリを強制終了する」をONにした場合のみ `/f` を使用します。強制終了は未保存データを失う可能性があります。

自動テストでは実際のシャットダウンを実行しません。Windowsコマンド呼び出しはテスト用ランナーで置き換えています。

## 対応OS

- Windows 10 64-bit
- Windows 11 64-bit

実際のタスク登録はWindowsの `schtasks.exe` を使用します。Linux/macOSではGUIの表示確認や単体テストは可能ですが、予約登録は利用できません。

## 使用方法

1. `AutoShutdown.exe` を起動します。
2. シャットダウンしたい「時」「分」を選びます。
3. 「シャットダウン設定」を押します。
4. 確認画面で「はい」を押します。
5. GUIを閉じても予約は残ります。

例えば現在が23:00で22:30を指定した場合は、翌日の22:30として登録します。

## 予約取消

アプリを起動して「予約取消」を押します。タスク名 `AutoShutdownScheduler` の予約を削除します。

## ビルド

Windowsで `scripts\build.bat` を実行します。

生成物：

`dist\AutoShutdown.exe`

## インストール

ビルド後に `scripts\install.bat` を実行します。

- `%LOCALAPPDATA%\AutoShutdown\AutoShutdown.exe` に配置
- デスクトップに「自動シャットダウン」ショートカットを作成

通常は管理者権限を要求しません。

## アンインストール

`scripts\uninstall.bat` を実行します。

- 予約タスクを削除
- デスクトップショートカットを削除
- `%LOCALAPPDATA%\AutoShutdown` を削除

## 管理者権限

本アプリは現在ユーザーのタスクとして登録する構成で、通常は管理者権限なしを想定しています。組織PCのグループポリシー等でタスク作成やシャットダウンが制限されている場合は登録に失敗することがあります。

## PC再起動後の予約

Windowsタスクスケジューラに登録するため、GUI終了やPC再起動で予約情報そのものは消えません。ただし、本バージョンは現在ユーザーのコンテキストで作成するため、実行条件はWindows側のユーザーセッション・ポリシーの影響を受けます。実機での再起動後動作は `docs/verification.md` のT7で別途確認してください。

## GitHub Actions

`.github/workflows/build-windows.yml` で以下を実行します。

1. Windows runner起動
2. Python 3.12セットアップ
3. pytest
4. PyInstallerでEXE作成
5. EXE/ZIPをArtifact保存
6. `v*` タグの場合はGitHub Releaseへ添付

## Release

初回リリース候補は `v1.0.0` です。

配布候補：

- `AutoShutdown.exe`
- `AutoShutdown-v1.0.0-win64.zip`

## ログ・設定

`%LOCALAPPDATA%\AutoShutdown\`

に `config.json` と `app.log` を保存します。個人情報は保存しません。

## 既知の制限

- 10分前／1分前のWindows通知はv1.0.0では未実装です。通知用タスクを増やすより、初版では予約の安定性と二重登録防止を優先しています。
- この開発環境はWindows実機ではないため、実際の `schtasks.exe` 登録、再起動後の実行、実シャットダウンは未検証です。
- 組織管理PCではタスクスケジューラやシャットダウン権限がポリシーで制限される場合があります。

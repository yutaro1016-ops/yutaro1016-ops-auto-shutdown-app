# 検証記録

検証日: 2026-10-13
対象候補: v1.0.0

## 自動テスト

| ID | 内容 | 結果 | 備考 |
|---|---|---|---|
| T1 | 20:00に22:30指定→当日22:30 | PASS | `resolve_target` |
| T2 | 23:00に22:30指定→翌日22:30 | PASS | `resolve_target` |
| T3 | 既存予約あり→削除後に新予約1件 | PASS | FakeRunner |
| T4 | 予約取消 | PASS | FakeRunner |
| T5 | 25:90等を拒否 | PASS | ValueError |
| T6 | GUI終了後もタスクが残る | 実機要確認 | GUI終了時に削除処理なし |
| T7 | PC再起動後も予約が残る | 実機要確認 | Windows実機が必要 |
| T8 | GUI表示と実タスク時刻一致 | 実機要確認 | Windows実機が必要 |
| T9 | 強制終了が初期OFF | コード確認済み | `/f` は明示ON時のみ |

## 安全確認

- 自動テストで `shutdown.exe` を実行しない。
- ユーザー入力をshell文字列へ連結しない。
- `subprocess.run(..., shell=False)` を使用。
- タスク名は `AutoShutdownScheduler` で固定し、同アプリ内の二重予約を防ぐ。

## 未検証・残存課題

- Windows 10/11実機での `schtasks.exe` の登録・削除。
- 再起動後の予約保持と実行条件。
- 組織管理PCでの権限制約。
- 10分前／1分前通知は初版では未実装。

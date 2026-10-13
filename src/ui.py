from __future__ import annotations

import logging
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk

from config import load_config, save_config
from scheduler import SchedulerError, cancel_shutdown, resolve_target, schedule_shutdown, task_exists

log = logging.getLogger(__name__)


class AutoShutdownApp(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=18)
        self.master = master
        self.cfg = load_config()
        self.hour_var = tk.StringVar(value=f"{int(self.cfg.get('last_hour', 23)):02d}")
        self.minute_var = tk.StringVar(value=f"{int(self.cfg.get('last_minute', 0)):02d}")
        self.force_var = tk.BooleanVar(value=bool(self.cfg.get("force_close", False)))
        self.now_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.remaining_var = tk.StringVar()

        self._build_ui()
        self.pack(fill="both", expand=True)
        self.refresh_clock()
        self.refresh_status()

    def _build_ui(self) -> None:
        self.master.title("指定時刻シャットダウン")
        self.master.resizable(False, False)
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

        ttk.Label(self, text="指定時刻シャットダウン", font=("Yu Gothic UI", 16, "bold")).grid(
            row=0, column=0, columnspan=5, pady=(0, 14)
        )
        ttk.Label(self, text="現在時刻").grid(row=1, column=0, sticky="w")
        ttk.Label(self, textvariable=self.now_var, font=("Yu Gothic UI", 12, "bold")).grid(
            row=1, column=1, columnspan=3, sticky="w"
        )

        ttk.Label(self, text="シャットダウン時刻").grid(row=2, column=0, sticky="w", pady=(12, 4))
        hour = ttk.Spinbox(self, from_=0, to=23, width=4, textvariable=self.hour_var, format="%02.0f")
        minute = ttk.Spinbox(self, from_=0, to=59, width=4, textvariable=self.minute_var, format="%02.0f")
        hour.grid(row=2, column=1, pady=(12, 4))
        ttk.Label(self, text=":").grid(row=2, column=2, pady=(12, 4))
        minute.grid(row=2, column=3, pady=(12, 4))

        ttk.Button(self, text="シャットダウン設定", command=self.set_schedule).grid(
            row=3, column=0, columnspan=5, sticky="ew", pady=(8, 10)
        )

        presets = [("30分後", 30), ("1時間後", 60), ("2時間後", 120), ("3時間後", 180)]
        for i, (label, mins) in enumerate(presets):
            ttk.Button(self, text=label, command=lambda m=mins: self.apply_preset(m)).grid(
                row=4, column=i, padx=(0 if i == 0 else 4, 0), sticky="ew"
            )

        ttk.Checkbutton(
            self,
            text="実行中アプリを強制終了する（未保存データ消失の可能性あり）",
            variable=self.force_var,
        ).grid(row=5, column=0, columnspan=5, sticky="w", pady=(12, 10))

        ttk.Separator(self).grid(row=6, column=0, columnspan=5, sticky="ew", pady=6)
        ttk.Label(self, text="現在の予約", font=("Yu Gothic UI", 10, "bold")).grid(
            row=7, column=0, columnspan=5, sticky="w"
        )
        ttk.Label(self, textvariable=self.status_var).grid(row=8, column=0, columnspan=5, sticky="w", pady=(4, 0))
        ttk.Label(self, textvariable=self.remaining_var).grid(row=9, column=0, columnspan=5, sticky="w")
        ttk.Button(self, text="予約取消", command=self.cancel_schedule).grid(
            row=10, column=0, columnspan=5, sticky="ew", pady=(12, 0)
        )

        for c in range(5):
            self.columnconfigure(c, weight=1)

    def apply_preset(self, minutes: int) -> None:
        target = datetime.now() + timedelta(minutes=minutes)
        self.hour_var.set(target.strftime("%H"))
        self.minute_var.set(target.strftime("%M"))

    def set_schedule(self) -> None:
        try:
            target = resolve_target(datetime.now(), self.hour_var.get(), self.minute_var.get())
        except ValueError as exc:
            messagebox.showerror("入力エラー", str(exc), parent=self.master)
            return

        force = bool(self.force_var.get())
        warning = "\n\n※実行中アプリを強制終了します。未保存データが失われる可能性があります。" if force else ""
        if not messagebox.askyesno(
            "確認",
            f"{target.strftime('%Y/%m/%d %H:%M')}にPCをシャットダウンします。設定しますか？{warning}",
            parent=self.master,
        ):
            return

        try:
            schedule_shutdown(target, force)
        except SchedulerError as exc:
            log.exception("予約登録失敗")
            messagebox.showerror("予約登録失敗", f"{exc}\n詳細はアプリログに記録しました。", parent=self.master)
            return

        self.cfg.update(
            {
                "last_hour": int(self.hour_var.get()),
                "last_minute": int(self.minute_var.get()),
                "force_close": force,
                "scheduled_for": target.isoformat(timespec="minutes"),
            }
        )
        save_config(self.cfg)
        self.refresh_status()
        messagebox.showinfo("設定完了", "シャットダウン予約を設定しました。", parent=self.master)

    def cancel_schedule(self) -> None:
        try:
            ok = cancel_shutdown()
        except SchedulerError as exc:
            log.exception("予約取消失敗")
            messagebox.showerror("予約取消失敗", str(exc), parent=self.master)
            return
        if not ok:
            messagebox.showerror("予約取消失敗", "予約を取消できませんでした。詳細はアプリログを確認してください。", parent=self.master)
            return
        self.cfg["scheduled_for"] = None
        save_config(self.cfg)
        self.refresh_status()
        messagebox.showinfo("取消完了", "シャットダウン予約を取消しました。", parent=self.master)

    def refresh_clock(self) -> None:
        self.now_var.set(datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
        self.refresh_remaining_only()
        self.after(1000, self.refresh_clock)

    def refresh_status(self) -> None:
        scheduled = self.cfg.get("scheduled_for")
        try:
            exists = task_exists()
        except SchedulerError:
            exists = False

        if not exists or not scheduled:
            self.status_var.set("シャットダウン予約はありません")
            self.remaining_var.set("")
            if not exists and scheduled:
                self.cfg["scheduled_for"] = None
                save_config(self.cfg)
            return

        try:
            target = datetime.fromisoformat(str(scheduled))
        except ValueError:
            self.status_var.set("予約情報を確認できません")
            self.remaining_var.set("")
            return
        self.status_var.set(f"シャットダウン予約済み  {target.strftime('%Y/%m/%d %H:%M')}")
        self.refresh_remaining_only()

    def refresh_remaining_only(self) -> None:
        scheduled = self.cfg.get("scheduled_for")
        if not scheduled:
            return
        try:
            target = datetime.fromisoformat(str(scheduled))
        except ValueError:
            return
        seconds = int((target - datetime.now()).total_seconds())
        if seconds <= 0:
            self.remaining_var.set("実行時刻に到達しました")
            return
        hours, rem = divmod(seconds, 3600)
        minutes = rem // 60
        self.remaining_var.set(f"あと {hours}時間{minutes}分")

    def on_close(self) -> None:
        self.cfg.update(
            {
                "last_hour": int(self.hour_var.get()) if self.hour_var.get().isdigit() else 23,
                "last_minute": int(self.minute_var.get()) if self.minute_var.get().isdigit() else 0,
                "force_close": bool(self.force_var.get()),
            }
        )
        save_config(self.cfg)
        self.master.destroy()

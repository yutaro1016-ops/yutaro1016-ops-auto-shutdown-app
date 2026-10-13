from __future__ import annotations

import platform
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Sequence

from config import TASK_NAME


class SchedulerError(RuntimeError):
    pass


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


def parse_time(hour: int | str, minute: int | str) -> tuple[int, int]:
    try:
        h = int(hour)
        m = int(minute)
    except (TypeError, ValueError) as exc:
        raise ValueError("時刻は数値で指定してください。") from exc
    if not 0 <= h <= 23 or not 0 <= m <= 59:
        raise ValueError("時刻は00:00〜23:59の範囲で指定してください。")
    return h, m


def resolve_target(now: datetime, hour: int | str, minute: int | str) -> datetime:
    h, m = parse_time(hour, minute)
    target = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target


def build_shutdown_command(force_close: bool) -> str:
    return "shutdown.exe /s /t 0 /f" if force_close else "shutdown.exe /s /t 0"


def build_create_args(target: datetime, force_close: bool) -> list[str]:
    # Use PowerShell ScheduledTasks cmdlets instead of schtasks /SD because
    # schtasks date parsing follows the Windows locale. This caused registration
    # failures on Japanese Windows when an MM/DD/YYYY date was supplied.
    iso_target = target.strftime("%Y-%m-%dT%H:%M:%S")
    action_args = "/s /t 0 /f" if force_close else "/s /t 0"
    safe_task_name = TASK_NAME.replace("'", "''")
    script = (
        "$ErrorActionPreference='Stop';"
        f"$when=[datetime]::ParseExact('{iso_target}','yyyy-MM-ddTHH:mm:ss',"
        "[System.Globalization.CultureInfo]::InvariantCulture);"
        f"$action=New-ScheduledTaskAction -Execute 'shutdown.exe' -Argument '{action_args}';"
        "$trigger=New-ScheduledTaskTrigger -Once -At $when;"
        "$principal=New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) "
        "-LogonType Interactive -RunLevel Limited;"
        f"Register-ScheduledTask -TaskName '{safe_task_name}' -Action $action -Trigger $trigger "
        "-Principal $principal -Force | Out-Null"
    )
    return [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        script,
    ]


def build_delete_args() -> list[str]:
    return ["schtasks.exe", "/Delete", "/TN", TASK_NAME, "/F"]


def build_query_args() -> list[str]:
    return ["schtasks.exe", "/Query", "/TN", TASK_NAME]


def _run(args: Sequence[str]) -> CommandResult:
    if platform.system() != "Windows":
        raise SchedulerError("この機能はWindows 10／11でのみ使用できます。")
    try:
        proc = subprocess.run(
            list(args),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except OSError as exc:
        raise SchedulerError("Windowsのタスク操作を開始できませんでした。") from exc
    return CommandResult(proc.returncode, proc.stdout, proc.stderr)


def task_exists(runner=_run) -> bool:
    result = runner(build_query_args())
    return result.returncode == 0


def cancel_shutdown(runner=_run) -> bool:
    result = runner(build_delete_args())
    if result.returncode == 0:
        return True
    return not task_exists(runner)


def schedule_shutdown(target: datetime, force_close: bool, runner=_run) -> None:
    if task_exists(runner):
        deleted = runner(build_delete_args())
        if deleted.returncode != 0:
            raise SchedulerError("既存のシャットダウン予約を更新できませんでした。")

    created = runner(build_create_args(target, force_close))
    if created.returncode != 0:
        detail = (created.stderr or created.stdout).strip()
        if detail:
            raise SchedulerError(f"シャットダウン予約をWindowsに登録できませんでした。詳細: {detail}")
        raise SchedulerError("シャットダウン予約をWindowsに登録できませんでした。")

    if not task_exists(runner):
        raise SchedulerError("予約登録後の確認に失敗しました。")

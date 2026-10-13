from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import scheduler


class FakeRunner:
    def __init__(self, exists: bool = False, fail_create: bool = False, fail_delete: bool = False):
        self.exists = exists
        self.fail_create = fail_create
        self.fail_delete = fail_delete
        self.calls: list[list[str]] = []

    def __call__(self, args):
        args = list(args)
        self.calls.append(args)
        if "/Query" in args:
            return scheduler.CommandResult(0 if self.exists else 1)
        if "/Delete" in args:
            if self.fail_delete:
                return scheduler.CommandResult(1)
            self.exists = False
            return scheduler.CommandResult(0)
        if "/Create" in args:
            if self.fail_create:
                return scheduler.CommandResult(1)
            self.exists = True
            return scheduler.CommandResult(0)
        return scheduler.CommandResult(1)


def test_t1_same_day():
    now = datetime(2026, 10, 13, 20, 0)
    assert scheduler.resolve_target(now, 22, 30) == datetime(2026, 10, 13, 22, 30)


def test_t2_next_day():
    now = datetime(2026, 10, 13, 23, 0)
    assert scheduler.resolve_target(now, 22, 30) == datetime(2026, 10, 14, 22, 30)


def test_t3_existing_reservation_replaced():
    fake = FakeRunner(exists=True)
    target = datetime(2026, 10, 13, 22, 30)
    scheduler.schedule_shutdown(target, False, runner=fake)
    assert fake.exists is True
    assert sum("/Delete" in c for c in fake.calls) == 1
    assert sum("/Create" in c for c in fake.calls) == 1


def test_t4_cancel():
    fake = FakeRunner(exists=True)
    assert scheduler.cancel_shutdown(runner=fake) is True
    assert fake.exists is False


def test_t5_invalid_time():
    try:
        scheduler.resolve_target(datetime(2026, 10, 13, 20, 0), 25, 90)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid time should raise ValueError")


def test_force_flag_default_command_is_safe():
    assert scheduler.build_shutdown_command(False) == "shutdown.exe /s /t 0"
    assert scheduler.build_shutdown_command(True).endswith(" /f")


def test_create_args_are_argument_list_not_shell_string():
    target = datetime(2026, 10, 13, 22, 30)
    args = scheduler.build_create_args(target, False)
    assert args[0] == "schtasks.exe"
    assert "/TN" in args and scheduler.TASK_NAME in args
    assert "22:30" in args

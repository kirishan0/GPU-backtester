"""
シンプルな右クリック自動化ツール。

- Tkinter製のGUIで間隔(ミリ秒)とホットキーを設定
- ボタンと同じホットキーで開始/停止をトグル
- PyInstallerなどでexe化する際はrequirements.txtの依存を含めること
"""

import threading
from typing import Optional

import pyautogui
import keyboard
import tkinter as tk
from tkinter import messagebox


class RightClickerApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("自動右クリック")
        self.root.geometry("360x200")

        self.interval_var = tk.StringVar(value="500")
        self.hotkey_var = tk.StringVar(value="ctrl+alt+r")
        self.status_var = tk.StringVar(value="停止中")

        self.running = False
        self._stop_event = threading.Event()
        self._worker: Optional[threading.Thread] = None
        self._hotkey_handle: Optional[str] = None

        self._build_ui()
        self._register_hotkey()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        padding = {"padx": 12, "pady": 6}

        interval_label = tk.Label(self.root, text="クリック間隔 (ミリ秒)")
        interval_label.grid(row=0, column=0, sticky="w", **padding)

        interval_entry = tk.Entry(self.root, textvariable=self.interval_var, width=12)
        interval_entry.grid(row=0, column=1, sticky="w", **padding)

        hotkey_label = tk.Label(self.root, text="開始/停止ホットキー")
        hotkey_label.grid(row=1, column=0, sticky="w", **padding)

        hotkey_entry = tk.Entry(self.root, textvariable=self.hotkey_var, width=16)
        hotkey_entry.grid(row=1, column=1, sticky="w", **padding)

        hotkey_button = tk.Button(self.root, text="ホットキー登録", command=self._register_hotkey)
        hotkey_button.grid(row=1, column=2, sticky="w", **padding)

        self.toggle_button = tk.Button(self.root, text="開始", width=12, command=self._toggle)
        self.toggle_button.grid(row=2, column=0, columnspan=3, **padding)

        status_label = tk.Label(self.root, textvariable=self.status_var, fg="blue")
        status_label.grid(row=3, column=0, columnspan=3, sticky="w", **padding)

        note = tk.Label(
            self.root,
            text="※ ホットキーとボタンは同じ動作です。最小間隔は50ms推奨。",
            fg="gray",
        )
        note.grid(row=4, column=0, columnspan=3, sticky="w", **padding)

    def _toggle(self) -> None:
        if self.running:
            self._stop_clicking()
        else:
            self._start_clicking()

    def _start_clicking(self) -> None:
        interval_ms = self._parse_interval()
        if interval_ms is None:
            return

        if self.running:
            return

        self.running = True
        self._stop_event.clear()
        self.toggle_button.configure(text="停止")
        self.status_var.set(f"実行中: {interval_ms}ms 間隔")

        self._worker = threading.Thread(target=self._click_loop, args=(interval_ms,), daemon=True)
        self._worker.start()

    def _stop_clicking(self) -> None:
        if not self.running:
            return

        self._stop_event.set()
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=0.5)

        self.running = False
        self.toggle_button.configure(text="開始")
        self.status_var.set("停止中")

    def _click_loop(self, interval_ms: int) -> None:
        interval_sec = interval_ms / 1000
        while not self._stop_event.is_set():
            pyautogui.click(button="right")
            if self._stop_event.wait(interval_sec):
                break

    def _parse_interval(self) -> Optional[int]:
        try:
            interval_ms = int(self.interval_var.get())
        except ValueError:
            messagebox.showerror("入力エラー", "間隔には整数を入力してください。")
            return None

        if interval_ms < 1:
            messagebox.showerror("入力エラー", "間隔は1ミリ秒以上にしてください。")
            return None

        return interval_ms

    def _register_hotkey(self) -> None:
        hotkey = self.hotkey_var.get().strip()
        if not hotkey:
            messagebox.showerror("入力エラー", "ホットキーを入力してください。")
            return

        if self._hotkey_handle:
            keyboard.remove_hotkey(self._hotkey_handle)
            self._hotkey_handle = None

        try:
            self._hotkey_handle = keyboard.add_hotkey(hotkey, lambda: self.root.after(0, self._toggle))
        except Exception as exc:
            messagebox.showerror("登録失敗", f"ホットキーを登録できませんでした: {exc}")
            return

        self.status_var.set(f"ホットキー登録: {hotkey}")

    def _on_close(self) -> None:
        self._stop_clicking()
        if self._hotkey_handle:
            keyboard.remove_hotkey(self._hotkey_handle)
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = RightClickerApp()
    app.run()


if __name__ == "__main__":
    main()

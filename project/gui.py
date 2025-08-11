"""簡易的なグラフィカルインターフェース。

CPUテスターやGPUモックをGUIから起動し、設定値も変更できます。
"""

import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Any, Dict

import yaml


class BacktesterGUI(tk.Tk):
    """バックテストを操作するためのGUIウィンドウ。"""

    def __init__(self) -> None:
        super().__init__()
        self.title("バックテスターGUI")
        self.config_params: Dict[str, Any] = {}
        self._create_widgets()

    def _create_widgets(self) -> None:
        """ウィジェットを配置します。"""
        # 設定ファイル
        tk.Label(self, text="設定ファイル").grid(row=0, column=0, sticky="w")
        self.config_entry = tk.Entry(self, width=40)
        self.config_entry.insert(0, "config.yaml")
        self.config_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Button(self, text="参照", command=self._select_config).grid(row=0, column=2, padx=5)
        tk.Button(self, text="編集", command=self._edit_parameters).grid(row=0, column=3, padx=5)

        # データファイル
        tk.Label(self, text="データCSV").grid(row=1, column=0, sticky="w")
        self.data_entry = tk.Entry(self, width=40)
        self.data_entry.insert(0, "data/ohlc.csv")
        self.data_entry.grid(row=1, column=1, padx=5, pady=5)
        tk.Button(self, text="参照", command=self._select_data).grid(row=1, column=2, padx=5)

        # Run ID
        tk.Label(self, text="Run ID").grid(row=2, column=0, sticky="w")
        self.run_entry = tk.Entry(self, width=20)
        self.run_entry.insert(0, "GUI_RUN")
        self.run_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # 実行モード
        tk.Label(self, text="モード").grid(row=3, column=0, sticky="w")
        self.mode_var = tk.StringVar(value="gpu")
        modes = [("CPU", "cpu"), ("GPUモック", "gpu_debug"), ("GPU", "gpu")]
        for idx, (text, value) in enumerate(modes):
            tk.Radiobutton(self, text=text, variable=self.mode_var, value=value).grid(row=3, column=1+idx, sticky="w")

        # 実行ボタン
        tk.Button(self, text="開始", command=self._start).grid(row=4, column=0, columnspan=4, pady=10)

        # 出力テキスト
        self.output = tk.Text(self, height=20, width=80)
        self.output.grid(row=5, column=0, columnspan=4, padx=5, pady=5)

        self._load_config()

    def _load_config(self) -> None:
        """設定ファイルを読み込みます。"""
        path = self.config_entry.get()
        try:
            with open(path, "r", encoding="utf-8") as fh:
                self.config_params = yaml.safe_load(fh) or {}
        except Exception:
            self.config_params = {}

    def _select_config(self) -> None:
        """設定ファイルを選択します。"""
        path = filedialog.askopenfilename(filetypes=[("YAML", "*.yaml"), ("YAML", "*.yml"), ("全て", "*.*")])
        if path:
            self.config_entry.delete(0, tk.END)
            self.config_entry.insert(0, path)
            self._load_config()

    def _select_data(self) -> None:
        """データファイルを選択します。"""
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv"), ("全て", "*.*")])
        if path:
            self.data_entry.delete(0, tk.END)
            self.data_entry.insert(0, path)

    def _edit_parameters(self) -> None:
        """パラメータ編集ウィンドウを開きます。"""
        if not self.config_params:
            messagebox.showerror("エラー", "設定ファイルを読み込めません")
            return
        win = tk.Toplevel(self)
        win.title("パラメータ編集")
        self.param_entries: Dict[str, tk.Entry] = {}
        for idx, (key, val) in enumerate(self.config_params.items()):
            tk.Label(win, text=key).grid(row=idx, column=0, sticky="w")
            entry = tk.Entry(win, width=20)
            entry.insert(0, str(val))
            entry.grid(row=idx, column=1, padx=5, pady=2)
            self.param_entries[key] = entry
        tk.Button(win, text="保存", command=lambda: self._save_parameters(win)).grid(
            row=len(self.config_params), column=0, columnspan=2, pady=5
        )

    def _save_parameters(self, win: tk.Toplevel) -> None:
        """編集されたパラメータを保存します。"""
        for key, entry in self.param_entries.items():
            original = self.config_params.get(key)
            text = entry.get()
            self.config_params[key] = self._convert_value(text, original)
        win.destroy()

    def _convert_value(self, text: str, original: Any) -> Any:
        """入力文字列を元の型へ変換します。"""
        try:
            if isinstance(original, bool):
                return text.lower() in ("true", "1", "yes", "on")
            if isinstance(original, int) and not isinstance(original, bool):
                return int(text)
            if isinstance(original, float):
                return float(text)
        except ValueError:
            return original
        return text

    def _start(self) -> None:
        """バックテストを開始します。"""
        thread = threading.Thread(target=self._run_backtest)
        thread.start()

    def _run_backtest(self) -> None:
        """指定されたモードでバックテストを実行します。"""
        config = self.config_entry.get()
        run_id = self.run_entry.get()
        mode = self.mode_var.get()
        data = self.data_entry.get()

        if mode == "cpu" and not data:
            messagebox.showerror("エラー", "CPUモードではデータCSVが必要です")
            return

        # 設定ファイルを書き出し
        try:
            with open(config, "w", encoding="utf-8") as fh:
                yaml.safe_dump(self.config_params, fh, allow_unicode=True)
        except Exception as exc:
            messagebox.showerror("エラー", f"設定ファイルの書き込みに失敗しました: {exc}")
            return

        if mode == "cpu":
            cmd = [
                sys.executable,
                "-m",
                "project.engine.cpu_tester",
                "--config",
                config,
                "--run-id",
                run_id,
                "--data",
                data,
            ]
        elif mode == "gpu_debug":
            cmd = [
                sys.executable,
                "-m",
                "project.engine.gpu_proxy",
                "--config",
                config,
                "--gpu-debug",
                "--run-id",
                run_id,
            ]
        else:
            cmd = [
                sys.executable,
                "-m",
                "project.engine.gpu_proxy",
                "--config",
                config,
                "--run-id",
                run_id,
            ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
        except Exception as exc:  # 例外発生時はメッセージを表示
            output = f"実行に失敗しました: {exc}\n"
        else:
            output = result.stdout
            if result.stderr:
                output += "\n[stderr]\n" + result.stderr

        # GUIスレッドで結果を表示
        self.output.after(0, self._append_output, output)

    def _append_output(self, text: str) -> None:
        """テキストウィジェットに出力を追加します。"""
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, text)


def main() -> None:
    """アプリケーションのエントリポイント。"""
    app = BacktesterGUI()
    app.mainloop()


if __name__ == "__main__":
    main()

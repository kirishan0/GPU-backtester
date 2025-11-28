# CloverPit + BepInExPack フォーカス問題の調査メモ

## 背景
- BepInExPack を導入した状態でゲームウィンドウが非アクティブでも入力が通ってしまう事象を解消したい。
- 参照した公式/有志リポジトリ:
  - [ModdingAPIs/CloverAPI](https://github.com/ModdingAPIs/CloverAPI)：API 提供のみでフォーカス制御の仕組みは見当たらず。
  - [IngoHHacks/QOLverPit](https://github.com/IngoHHacks/QOLverPit)：タイトル画面のメニュー項目を Harmony で差し替える例あり。
    - `Patches/TitleScreenPatch.cs` では `ScreenMenuScript.Open` の `options`/`optionEvents` を書き換えて「ゲームを終了」ボタンを追加している。【例: `options = options.Append(...).ToArray();` でメニュー項目を差し替え】
  - [BepInEx/BepInEx](https://github.com/BepInEx/BepInEx)：フォーカス関連の挙動変更は標準では提供されていない。

## 対策案 A: フォーカスが外れたら入力処理を止める Harmony パッチ
Unity 側は `Application.isFocused` が `false` のときに入力更新をスキップすれば、ウィンドウ非アクティブ時の誤入力を防げる。

1. 新規 BepInEx プラグインを作成して Harmony パッチを登録する。
   ```csharp
   [BepInPlugin("yourid.focusguard", "FocusGuard", "1.0.0")]
   public class FocusGuard : BaseUnityPlugin
   {
       private void Awake()
       {
           Application.runInBackground = false; // バックグラウンド更新を抑制
           Harmony.CreateAndPatchAll(typeof(FocusGuard));
       }

       // 実際の入力スクリプト名はゲーム内のクラスに合わせる
       [HarmonyPatch(typeof(Panik.InputScript), "Update")]
       [HarmonyPrefix]
       private static bool StopWhenUnfocused()
       {
           return Application.isFocused; // false なら元メソッドを実行しない
       }
   }
   ```
2. `Panik.InputScript` 部分はゲーム側の入力処理クラスに合わせて差し替える。`QOLverPit` でメニューを書き換えているのと同じ要領で、`ScreenMenuScript` やプレイヤー入力スクリプトを対象にするのが確実。
3. `Application.runInBackground` を `false` にすることで、ウィンドウを離れたときにゲーム更新そのものを止める（既に他の mod で `true` にされている場合は併用に注意）。

### PID + Unity 両方でブロックする完全版（サンプルコードあり）
- `project/research/NoBackgroundInput_PIDFocus.cs` に、プロセス ID の前面判定と `Application.isFocused` のどちらかが `false` なら必ず入力を遮断する Harmony パッチ（バージョン 1.4.3）を追加。非アクティブ時は `Input.ResetInputAxes()` で蓄積入力も破棄するため、起動直後が非アクティブでも押下が漏れない。
- 起動直後に「ゲームを続ける」「新規ゲーム」が並ぶメニューを検出した際に、新規ゲーム行の GameObject を丸ごと非アクティブ化し、最初の Down 入力を 1 回だけ食う安全策も含む。`Selectable` を親に遡って丸ごと無効化し、`LayoutElement` も潰して空行が残らないよう改善済み。

### 起動直後から非アクティブの場合に効く runInBackground 強制 OFF 方式
- BepInExPack 環境では `Application.runInBackground` が true に書き換えられ、ウィンドウが背面にあってもゲーム側の Update が動き続けるケースがある。
- `project/research/RunInBackgroundOff.cs` では `Application.runInBackground = false` を起動直後に設定し、1 秒おきに再設定して他の mod からの上書きを打ち消す。
- Update ループそのものが止まるため、ゲーム開始時に非アクティブでも入力が通ってしまう問題を避けられる。前述の Harmony 入力パッチと併用すると、フォーカス復帰後の安全策も保てる。

## 対策案 B: 続きからプレイのボタンを無効化/非表示にする
フォーカス問題を直接直せない場合は、誤操作が起こりがちな「ゲームを続ける」項目をタイトル画面から外す。

1. `QOLverPit` の `TitleScreenPatch` と同様に、`ScreenMenuScript.Open` の Harmony Prefix で `options` と `optionEvents` を編集する。
   ```csharp
   var continueLabel = Translation.Get("SCREEN_MENU_OPTION_CONTINUE");
   options = options.Where(x => x != continueLabel).ToArray();
   optionEvents = optionEvents.Where((_, i) => options[i] != continueLabel).ToArray();
   ```
2. `options` 配列から該当ラベルを削除すれば描画も当たり判定も消える。不要な場合は「新規ゲーム」の表示を残すか、`optionEvents` を空配列にして完全に無効化できる。
3. 追加で UI を見えなくしたい場合は、`ScreenMenuScript.Open` 後に `menuOptionsParent.SetActive(false)` のように GameObject を無効化する処理を postfix で挿入する。

## 実装時の注意
- Harmony パッチは `BepInEx/plugins` 配下に配置したプラグイン DLL から登録する。`CloverAPI` が必須な mod であれば依存関係に追加する。
- ゲーム更新でクラス名やメニュー構造が変わる可能性があるため、パッチ対象のメソッド名は実行時ログで確認する。
- フォーカス抑止とメニュー改変を両方行う場合、1 つのプラグインにまとめても問題ない。

## git pull 時の競合を解消する手順メモ
`project/research` 配下に追加した 2 つのサンプル（`NoBackgroundInput_PIDFocus.cs` と `RunInBackgroundOff.cs`）がまだローカルに存在する状態で、リモート側に別の変更が入っていると `git pull` 時に競合することがあります。以下の手順で解消できます。

1. まずローカル変更をコミットしておくか、一時退避する場合は `git stash push -m "cloverpit focus files"` を実行する。
2. リモートをフェッチし、追跡ブランチを確認する。
   ```bash
   git fetch --all
   git status -sb
   ```
3. `git pull --rebase` を試し、競合が出た場合は対象ファイルを開いて `<<<<<<<` マーカーを解消する。今回のサンプルを優先する場合は `project/research/NoBackgroundInput_PIDFocus.cs` と `project/research/RunInBackgroundOff.cs` の「current 変更」を残し、不要であれば逆に「incoming 変更」を残す。
4. 競合を解消したら以下を実行してリベースを継続する。
   ```bash
   git add project/research/NoBackgroundInput_PIDFocus.cs project/research/RunInBackgroundOff.cs project/research/cloverpit_focus.md
   git rebase --continue
   ```
5. スタッシュしていた場合は `git stash pop` で戻し、追加で競合したら同様に解消する。

手元でどうしても競合が解けない場合は、上記 2 ファイルと本メモを一度退避してから `git pull --rebase` を行い、必要なら退避した最新版を手動で上書きしてください。

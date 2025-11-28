// 非アクティブ時の入力をプロセス ID と Unity フォーカスの両方で遮断するサンプル。
// ・前面ウィンドウのプロセスIDでフォーカス判定
// ・ゲームプロセスが前面にいない、または Unity 側が非フォーカスのときに、UnityEngine.Input の Key/Mouse/Button/Axis を全部ブロック
// ・起動直後に「ゲームを続ける ＋ 新規ゲーム」が並んでいるメニューを見つけたときだけ
//   「新規ゲーム」の行っぽい GameObject を丸ごと無効化（当たり判定も含める）
// ・さらに安全策として、そのタイミングで「次のキー/ボタン Down を一度だけ食う」ようにしておく

using BepInEx;
using BepInEx.Logging;
using HarmonyLib;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;
using TMPro;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using UnityEngine.EventSystems;

namespace NoBackgroundInput
{
    [BepInPlugin(PluginGuid, PluginName, PluginVersion)]
    public class NoBackgroundInputPlugin : BaseUnityPlugin
    {
        public const string PluginGuid = "yourname.nobackgroundinput.pidfocus";
        public const string PluginName = "NoBackgroundInput_PIDFocus";
        public const string PluginVersion = "1.4.3";

        internal static ManualLogSource Log;
        private Harmony _harmony;

        private void Awake()
        {
            Log = Logger;
            Log.LogInfo($"{PluginName} Awake() 開始");

            _harmony = new Harmony(PluginGuid);
            _harmony.PatchAll();

            Log.LogInfo($"{PluginName} Harmony PatchAll() 完了");
        }

        private void OnEnable()
        {
            SceneManager.sceneLoaded += OnSceneLoaded;
        }

        private void OnDisable()
        {
            SceneManager.sceneLoaded -= OnSceneLoaded;
        }

        private void Start()
        {
            var scene = SceneManager.GetActiveScene();
            Log?.LogInfo(
                $"{PluginName} Start() 呼び出し。Unity側フォーカス: {UnityEngine.Application.isFocused}, ActiveScene={scene.name}");
        }

        private void OnDestroy()
        {
            Log?.LogInfo($"{PluginName} OnDestroy() 呼び出し。パッチ解除します。");
            _harmony?.UnpatchSelf();
        }

        private void Update()
        {
            // フォーカスログ
            InputPatches.CheckFocusChange();

            // 起動直後メニューの探索（1秒に1回程度）
            MenuPatcher.PeriodicScan();
        }

        private void OnSceneLoaded(Scene scene, LoadSceneMode mode)
        {
            Log?.LogInfo($"[MenuPatch] Scene loaded: {scene.name} (mode={mode})");
            MenuPatcher.TryScanScene(scene, "SceneLoaded");
        }
    }

    /// <summary>
    /// 起動直後メニューの「新規ゲーム」行の丸ごと無効化ロジック。
    /// ・一度成功したら以降は何もしない（＝起動時のみ）。
    /// </summary>
    internal static class MenuPatcher
    {
        private static bool _patchedOnce = false;   // 一度成功したら true
        private static float _lastScanTime = -999f;   // 周期スキャン用
        private const float ScanInterval = 1.0f;    // 何秒ごとにスキャンするか

        // ラベル/名前の判定用
        private static readonly string[] NewGameTexts =
        {
            "New Game",
            "NEW GAME",
            "新規ゲーム",
            "新しいゲーム",
            "ニューゲーム"
        };

        private static readonly string[] NewGameNames =
        {
            "NewGame",
            "New_Game",
            "NewGameButton"
        };

        private static readonly string[] ContinueTexts =
        {
            "Continue",
            "CONTINUE",
            "ゲームを続ける",
            "続きから",
            "コンティニュー"
        };

        private static readonly string[] ContinueNames =
        {
            "Continue",
            "ContinueGame",
            "ContinueButton"
        };

        internal static void TryScanScene(Scene scene, string reason)
        {
            if (_patchedOnce)
            {
                NoBackgroundInputPlugin.Log?.LogInfo(
                    $"[MenuPatch] {reason}: 既に一度パッチ済みのためスキップ（起動時のみ仕様）");
                return;
            }

            try
            {
                var roots = scene.GetRootGameObjects();
                if (roots == null || roots.Length == 0)
                {
                    NoBackgroundInputPlugin.Log?.LogInfo($"[MenuPatch] {reason}: ルートオブジェクトが0件");
                    return;
                }

                ScanRoots(scene, roots, reason);
            }
            catch (Exception ex)
            {
                NoBackgroundInputPlugin.Log?.LogWarning($"[MenuPatch] {reason}: 例外: {ex}");
            }
        }

        internal static void PeriodicScan()
        {
            if (_patchedOnce)
                return;

            var scene = SceneManager.GetActiveScene();
            if (!scene.IsValid())
                return;

            if (Time.unscaledTime - _lastScanTime < ScanInterval)
                return;

            _lastScanTime = Time.unscaledTime;

            NoBackgroundInputPlugin.Log?.LogDebug(
                $"[MenuPatch] 周期スキャン開始 scene='{scene.name}'");

            try
            {
                var roots = scene.GetRootGameObjects();
                if (roots == null || roots.Length == 0)
                {
                    NoBackgroundInputPlugin.Log?.LogDebug("[MenuPatch] 周期スキャン: ルート0件");
                    return;
                }

                ScanRoots(scene, roots, "Periodic");
            }
            catch (Exception ex)
            {
                NoBackgroundInputPlugin.Log?.LogWarning($"[MenuPatch] Periodic: 例外: {ex}");
            }
        }

        private static void ScanRoots(Scene scene, GameObject[] roots, string tag)
        {
            int totalButtons = 0;
            int totalTexts = 0;
            int newGameCandidates = 0;
            int continueCandidates = 0;

            var newGameButtons = new List<Button>();
            var newGameTexts = new List<TMP_Text>();

            foreach (var root in roots)
            {
                // Button
                var buttons = root.GetComponentsInChildren<Button>(true);
                foreach (var btn in buttons)
                {
                    totalButtons++;
                    string name = btn.gameObject.name;
                    string label = GetButtonLabel(btn);
                    string path = GetPath(btn.gameObject);

                    if (IsContinueButton(name, label))
                    {
                        continueCandidates++;
                        NoBackgroundInputPlugin.Log?.LogDebug(
                            $"[MenuPatch]({tag}) Continue候補 Button path='{path}', text='{label}'");
                    }

                    if (IsNewGameButton(name, label))
                    {
                        newGameCandidates++;
                        newGameButtons.Add(btn);
                        NoBackgroundInputPlugin.Log?.LogDebug(
                            $"[MenuPatch]({tag}) NewGame候補 Button path='{path}', text='{label}'");
                    }
                }

                // TMP_Text
                var tmps = root.GetComponentsInChildren<TMP_Text>(true);
                foreach (var tmp in tmps)
                {
                    totalTexts++;
                    string name = tmp.gameObject.name;
                    string text = tmp.text ?? string.Empty;
                    string path = GetPath(tmp.gameObject);

                    if (IsContinueButton(name, text))
                    {
                        continueCandidates++;
                        NoBackgroundInputPlugin.Log?.LogDebug(
                            $"[MenuPatch]({tag}) Continue候補 TMP path='{path}', text='{text}'");
                    }

                    if (IsNewGameButton(name, text))
                    {
                        newGameCandidates++;
                        newGameTexts.Add(tmp);
                        NoBackgroundInputPlugin.Log?.LogDebug(
                            $"[MenuPatch]({tag}) NewGame候補 TMP path='{path}', text='{text}'");
                    }
                }
            }

            NoBackgroundInputPlugin.Log?.LogInfo(
                $"[MenuPatch]({tag}) scene='{scene.name}' Button総数={totalButtons}, Text総数={totalTexts}, Continue候補={continueCandidates}, NewGame候補={newGameCandidates}");

            // 条件：Continue があり、NewGame候補が1つ以上あるときだけ起動時パッチを適用
            if (continueCandidates > 0 && (newGameButtons.Count > 0 || newGameTexts.Count > 0))
            {
                int disabledCount = 0;

                foreach (var btn in newGameButtons)
                {
                    disabledCount += DisableNewGameByButton(btn);
                }

                foreach (var tmp in newGameTexts)
                {
                    disabledCount += DisableNewGameByText(tmp);
                }

                NoBackgroundInputPlugin.Log?.LogInfo(
                    $"[MenuPatch] 起動時メニュー検知 → 『新規ゲーム』候補 {disabledCount} 個を丸ごと無効化しました。");

                _patchedOnce = true;

                // 安全策：このタイミングで「次の Down 入力」を一度だけ食う
                InputPatches.MarkStartupFirstDownToEat();
            }
            else
            {
                NoBackgroundInputPlugin.Log?.LogInfo(
                    $"[MenuPatch]({tag}) 条件未成立（Continue={continueCandidates}, NewGame={newGameCandidates}）のため何もしません。");
            }
        }

        private static bool ContainsIgnoreCase(string src, string pattern)
        {
            if (string.IsNullOrEmpty(src) || string.IsNullOrEmpty(pattern))
                return false;

            return src.IndexOf(pattern, StringComparison.OrdinalIgnoreCase) >= 0;
        }

        private static bool IsNewGameButton(string objName, string label)
        {
            foreach (var t in NewGameTexts)
            {
                if (ContainsIgnoreCase(label, t)) return true;
            }
            foreach (var n in NewGameNames)
            {
                if (ContainsIgnoreCase(objName, n)) return true;
            }
            return false;
        }

        private static bool IsContinueButton(string objName, string label)
        {
            foreach (var t in ContinueTexts)
            {
                if (ContainsIgnoreCase(label, t)) return true;
            }
            foreach (var n in ContinueNames)
            {
                if (ContainsIgnoreCase(objName, n)) return true;
            }
            return false;
        }

        private static string GetButtonLabel(Button btn)
        {
            try
            {
                var tmp = btn.GetComponentInChildren<TMP_Text>(true);
                if (tmp != null && !string.IsNullOrEmpty(tmp.text))
                    return tmp.text;

                var text = btn.GetComponentInChildren<UnityEngine.UI.Text>(true);
                if (text != null && !string.IsNullOrEmpty(text.text))
                    return text.text;
            }
            catch { }
            return string.Empty;
        }

        private static int DisableNewGameByButton(Button btn)
        {
            if (btn == null) return 0;

            var go = btn.gameObject;
            string path = GetPath(go);
            string label = GetButtonLabel(btn);

            try
            {
                // Button 自体と親階層のクリック判定を完全に殺す
                btn.interactable = false;
                btn.onClick.RemoveAllListeners();

                GameObject root = FindClickableRoot(btn.transform);

                DisableClickableChain(root);
                CollapseLayout(root);
                root.SetActive(false);

                NoBackgroundInputPlugin.Log?.LogInfo(
                    $"[MenuPatch] NewGame Button 無効化 path='{path}', text='{label}', root='{GetPath(root)}'");

                return 1;
            }
            catch (Exception ex)
            {
                NoBackgroundInputPlugin.Log?.LogWarning(
                    $"[MenuPatch] NewGame Button 無効化中に例外 path='{path}', ex={ex}");
                return 0;
            }
        }

        private static int DisableNewGameByText(TMP_Text tmp)
        {
            if (tmp == null) return 0;

            string rawPath = GetPath(tmp.gameObject);
            string text = tmp.text ?? string.Empty;

            try
            {
                // テキストから「行（メニュー項目）」っぽい Transform を推定して、その GameObject を丸ごと殺す
                GameObject rowRoot = FindClickableRoot(tmp.transform);
                string path = GetPath(rowRoot);

                DisableClickableChain(rowRoot);
                CollapseLayout(rowRoot);
                rowRoot.SetActive(false);

                NoBackgroundInputPlugin.Log?.LogInfo(
                    $"[MenuPatch] NewGame Text 無効化 path='{path}', rawPath='{rawPath}', text='{text}'");

                return 1;
            }
            catch (Exception ex)
            {
                NoBackgroundInputPlugin.Log?.LogWarning(
                    $"[MenuPatch] NewGame Text 無効化中に例外 rawPath='{rawPath}', ex={ex}");
                return 0;
            }
        }

        /// <summary>
        /// TMP_Text / Button から「クリック可能な行（メニュー項目）」っぽい Transform を推定する。
        /// Selectable や IPointerClickHandler が見つかったらそこを優先し、Canvas まで遡る。
        /// </summary>
        private static GameObject FindClickableRoot(Transform t)
        {
            if (t == null) throw new ArgumentNullException(nameof(t));

            Transform current = t;
            Transform lastBeforeCanvas = t;

            while (current != null)
            {
                // Canvas を超えたら終了（別 UI 階層には触らない）
                if (current.GetComponent<Canvas>() != null)
                {
                    break;
                }

                // Selectable / PointerHandler のあるノードを優先
                if (current.GetComponent<Selectable>() != null ||
                    current.GetComponent<IPointerClickHandler>() != null)
                {
                    lastBeforeCanvas = current;
                }

                current = current.parent;
            }

            return lastBeforeCanvas.gameObject;
        }

        /// <summary>
        /// LayoutElement 等を潰して、非表示化した行が空行として残らないようにする。
        /// </summary>
        private static void CollapseLayout(GameObject root)
        {
            if (root == null) return;

            foreach (var le in root.GetComponentsInChildren<LayoutElement>(true))
            {
                try
                {
                    le.ignoreLayout = true;
                    le.preferredHeight = 0f;
                    le.minHeight = 0f;
                    le.flexibleHeight = 0f;
                }
                catch (Exception ex)
                {
                    NoBackgroundInputPlugin.Log?.LogWarning(
                        $"[MenuPatch] CollapseLayout(LayoutElement='{le}') 例外 ex={ex}");
                }
            }

            var rect = root.GetComponent<RectTransform>();
            if (rect != null)
            {
                try
                {
                    rect.SetSizeWithCurrentAnchors(RectTransform.Axis.Vertical, 0f);
                }
                catch (Exception ex)
                {
                    NoBackgroundInputPlugin.Log?.LogWarning(
                        $"[MenuPatch] CollapseLayout(RectTransform='{rect}') 例外 ex={ex}");
                }
            }
        }

        /// <summary>
        /// 渡された GameObject とその子孫から、Collider 系やクリック系コンポーネントの当たり判定を殺す。
        /// Collider 型を直接参照せず、型名文字列やインターフェースで判定するので PhysicsModule 参照不要。
        /// </summary>
        private static void DisableClickableChain(GameObject root)
        {
            if (root == null) return;

            try
            {
                foreach (var comp in root.GetComponentsInChildren<Component>(true))
                {
                    if (comp == null) continue;

                    var type = comp.GetType();
                    string tname = type.Name;

                    try
                    {
                        // Collider 系（3D / 2D 両方まとめて型名で判定）
                        if (tname.IndexOf("Collider", StringComparison.OrdinalIgnoreCase) >= 0)
                        {
                            if (comp is Behaviour beh)
                            {
                                beh.enabled = false;
                            }
                        }

                        // Unity UI の Selectable(Button, Toggle, etc.)
                        if (comp is Selectable sel)
                        {
                            sel.interactable = false;
                        }

                        // EventSystems のクリック・Submit系
                        if (comp is IPointerClickHandler || comp is ISubmitHandler)
                        {
                            if (comp is Behaviour beh2)
                            {
                                beh2.enabled = false;
                            }
                        }
                    }
                    catch (Exception exInner)
                    {
                        NoBackgroundInputPlugin.Log?.LogWarning(
                            $"[MenuPatch] DisableClickableChain comp='{comp}' 中に例外 ex={exInner}");
                    }
                }
            }
            catch (Exception ex)
            {
                NoBackgroundInputPlugin.Log?.LogWarning(
                    $"[MenuPatch] DisableClickableChain(root='{root.name}') 例外 ex={ex}");
            }
        }

        private static string GetPath(GameObject obj)
        {
            if (obj == null) return "(null)";
            var sb = new StringBuilder(obj.name);
            var t = obj.transform.parent;
            while (t != null)
            {
                sb.Insert(0, t.name + "/");
                t = t.parent;
            }
            return sb.ToString();
        }
    }

    // ====== フォーカス判定（PIDベース） ======

    internal static class WinFocusHelper
    {
        [DllImport("user32.dll")]
        private static extern IntPtr GetForegroundWindow();

        [DllImport("user32.dll")]
        private static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);

        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        private static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);

        private static readonly int OurPid = Process.GetCurrentProcess().Id;
        private static bool _lastActive;
        private static bool _init;

        internal static bool IsGameForeground()
        {
            IntPtr fg = GetForegroundWindow();
            if (fg == IntPtr.Zero)
            {
                if (!_init || _lastActive != false)
                {
                    _init = true;
                    _lastActive = false;
                    NoBackgroundInputPlugin.Log?.LogInfo("[WinFocus] fg=0 → OSActive=False");
                }
                return false;
            }

            GetWindowThreadProcessId(fg, out uint pid);
            bool active = (pid == (uint)OurPid);

            if (!_init || _lastActive != active)
            {
                _init = true;
                _lastActive = active;

                var sb = new StringBuilder(256);
                GetWindowText(fg, sb, sb.Capacity);

                NoBackgroundInputPlugin.Log?.LogInfo(
                    $"[WinFocus] OSActive={active}, fgPid={pid}, ourPid={OurPid}, fgTitle='{sb}'");
            }

            return active;
        }
    }

    // ====== UnityEngine.Input パッチ ======

    [HarmonyPatch(typeof(Input))]
    internal static class InputPatches
    {
        private static bool _lastUnityFocused;
        private static bool _unityInit;

        // 起動時メニューで NewGame を殺したあと、
        // 「次の Down 系入力（GetKeyDown / GetMouseButtonDown / GetButtonDown / anyKeyDown）」を
        // 一度だけ強制的にブロックするためのフラグ
        private static bool _eatFirstDownOnce;
        private static bool _eatFirstDownConsumed;

        internal static void MarkStartupFirstDownToEat()
        {
            if (_eatFirstDownConsumed)
                return;

            _eatFirstDownOnce = true;
            NoBackgroundInputPlugin.Log?.LogInfo(
                "[StartupEat] 起動時メニュー検知 → 次のキー/ボタン Down を一度だけキャンセルする設定にしました。");
        }

        internal static void CheckFocusChange()
        {
            bool unity = UnityEngine.Application.isFocused;
            if (!_unityInit)
            {
                _unityInit = true;
                _lastUnityFocused = unity;
                NoBackgroundInputPlugin.Log?.LogInfo($"[UnityFocus] 初期 Application.isFocused={unity}");
            }
            else if (_lastUnityFocused != unity)
            {
                _lastUnityFocused = unity;
                NoBackgroundInputPlugin.Log?.LogInfo($"[UnityFocus] 変化 Application.isFocused={unity}");
            }

            // OS 側の変化ログは WinFocusHelper 内でやっている
            WinFocusHelper.IsGameForeground();
        }

        private static bool ShouldBlock(string methodName, string extraInfo,
                                        out bool unityFocused, out bool osActive)
        {
            unityFocused = UnityEngine.Application.isFocused;
            osActive = WinFocusHelper.IsGameForeground();

            bool isDownEvent =
                methodName.IndexOf("Down", StringComparison.OrdinalIgnoreCase) >= 0;

            // 起動時一発目の Down を食う（ゲームプロセスが前面にあるときのみ）
            if (osActive && _eatFirstDownOnce && isDownEvent)
            {
                _eatFirstDownOnce = false;
                _eatFirstDownConsumed = true;

                NoBackgroundInputPlugin.Log?.LogInfo(
                    $"[StartupEat] {methodName}({extraInfo}) を起動時初回入力としてキャンセルしました。");
                return true;
            }

            // Unity 側または OS 側どちらかが非アクティブなら常にブロック
            if (!unityFocused || !osActive)
            {
                try
                {
                    // 非アクティブ状態で溜まった入力をリセットして初回から拾われないようにする
                    Input.ResetInputAxes();
                }
                catch (Exception ex)
                {
                    NoBackgroundInputPlugin.Log?.LogWarning($"[Block] ResetInputAxes 例外: {ex}");
                }

                NoBackgroundInputPlugin.Log?.LogInfo(
                    $"[Block] unityFocused={unityFocused}, osActive={osActive} のため {methodName}({extraInfo}) をブロックします。");
                return true;
            }

            NoBackgroundInputPlugin.Log?.LogDebug(
                $"[Pass] {methodName}({extraInfo}) を通過 (unity={unityFocused}, os={osActive})");
            return false;
        }

        // ===== Key 系 =====

        [HarmonyPrefix]
        [HarmonyPatch(nameof(Input.GetKey), typeof(KeyCode))]
        private static bool GetKey_Prefix(KeyCode key, ref bool __result)
        {
            if (ShouldBlock("GetKey", key.ToString(), out _, out _))
            {
                __result = false;
                return false;
            }
            return true;
        }

        [HarmonyPrefix]
        [HarmonyPatch(nameof(Input.GetKeyDown), typeof(KeyCode))]
        private static bool GetKeyDown_Prefix(KeyCode key, ref bool __result)
        {
            if (ShouldBlock("GetKeyDown", key.ToString(), out _, out _))
            {
                __result = false;
                return false;
            }
            return true;
        }

        [HarmonyPrefix]
        [HarmonyPatch(nameof(Input.GetKeyUp), typeof(KeyCode))]
        private static bool GetKeyUp_Prefix(KeyCode key, ref bool __result)
        {
            if (ShouldBlock("GetKeyUp", key.ToString(), out _, out _))
            {
                __result = false;
                return false;
            }
            return true;
        }

        // ===== MouseButton 系 =====

        [HarmonyPrefix]
        [HarmonyPatch(nameof(Input.GetMouseButton), typeof(int))]
        private static bool GetMouseButton_Prefix(int button, ref bool __result)
        {
            if (ShouldBlock("GetMouseButton", button.ToString(), out _, out _))
            {
                __result = false;
                return false;
            }
            return true;
        }

        [HarmonyPrefix]
        [HarmonyPatch(nameof(Input.GetMouseButtonDown), typeof(int))]
        private static bool GetMouseButtonDown_Prefix(int button, ref bool __result)
        {
            if (ShouldBlock("GetMouseButtonDown", button.ToString(), out _, out _))
            {
                __result = false;
                return false;
            }
            return true;
        }

        [HarmonyPrefix]
        [HarmonyPatch(nameof(Input.GetMouseButtonUp), typeof(int))]
        private static bool GetMouseButtonUp_Prefix(int button, ref bool __result)
        {
            if (ShouldBlock("GetMouseButtonUp", button.ToString(), out _, out _))
            {
                __result = false;
                return false;
            }
            return true;
        }

        // ===== anyKey 系 =====

        [HarmonyPrefix]
        [HarmonyPatch("get_anyKey")]
        private static bool AnyKey_Prefix(ref bool __result)
        {
            if (ShouldBlock("get_anyKey", "", out _, out _))
            {
                __result = false;
                return false;
            }
            return true;
        }

        [HarmonyPrefix]
        [HarmonyPatch("get_anyKeyDown")]
        private static bool AnyKeyDown_Prefix(ref bool __result)
        {
            if (ShouldBlock("get_anyKeyDown", "", out _, out _))
            {
                __result = false;
                return false;
            }
            return true;
        }

        // ===== Button 系 =====

        [HarmonyPrefix]
        [HarmonyPatch(nameof(Input.GetButton), typeof(string))]
        private static bool GetButton_Prefix(string buttonName, ref bool __result)
        {
            if (ShouldBlock("GetButton", buttonName, out _, out _))
            {
                __result = false;
                return false;
            }
            return true;
        }

        [HarmonyPrefix]
        [HarmonyPatch(nameof(Input.GetButtonDown), typeof(string))]
        private static bool GetButtonDown_Prefix(string buttonName, ref bool __result)
        {
            if (ShouldBlock("GetButtonDown", buttonName, out _, out _))
            {
                __result = false;
                return false;
            }
            return true;
        }

        [HarmonyPrefix]
        [HarmonyPatch(nameof(Input.GetButtonUp), typeof(string))]
        private static bool GetButtonUp_Prefix(string buttonName, ref bool __result)
        {
            if (ShouldBlock("GetButtonUp", buttonName, out _, out _))
            {
                __result = false;
                return false;
            }
            return true;
        }

        // ===== Axis 系 =====

        [HarmonyPrefix]
        [HarmonyPatch(nameof(Input.GetAxis), typeof(string))]
        private static bool GetAxis_Prefix(string axisName, ref float __result)
        {
            if (ShouldBlock("GetAxis", axisName, out _, out _))
            {
                __result = 0f;
                return false;
            }
            return true;
        }

        [HarmonyPrefix]
        [HarmonyPatch(nameof(Input.GetAxisRaw), typeof(string))]
        private static bool GetAxisRaw_Prefix(string axisName, ref float __result)
        {
            if (ShouldBlock("GetAxisRaw", axisName, out _, out _))
            {
                __result = 0f;
                return false;
            }
            return true;
        }
    }
}

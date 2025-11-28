using BepInEx;
using BepInEx.Logging;
using HarmonyLib;
using System.Collections;
using UnityEngine;

namespace NoBackgroundInput
{
    /// <summary>
    /// Unity 側の <see cref="Application.runInBackground"/> を常に false に維持し、
    /// ゲームウィンドウが前面にない場合は Update ループそのものを止めるサンプル。
    /// BepInExPack が runInBackground を true にする場合の副作用を打ち消すことを狙う。
    /// </summary>
    [BepInPlugin(PluginGuid, PluginName, PluginVersion)]
    public class RunInBackgroundOffPlugin : BaseUnityPlugin
    {
        public const string PluginGuid = "yourname.nobackgroundinput.runoff";
        public const string PluginName = "NoBackgroundInput_RunInBackgroundOff";
        public const string PluginVersion = "1.0.0";

        internal static ManualLogSource Log;
        private Harmony _harmony;

        private void Awake()
        {
            Log = Logger;
            Log.LogInfo($"{PluginName} Awake()");

            // まず即座に OFF にする
            ForceRunInBackgroundOff("Awake");

            // 他の mod が true に戻す場合があるので、定期的に監視する
            StartCoroutine(KeepRunInBackgroundOff());

            // ScreenMenuScript.Open のオプションを触る例（QOLverPit と同等）
            _harmony = new Harmony(PluginGuid);
            _harmony.PatchAll();
        }

        private void OnDestroy()
        {
            _harmony?.UnpatchSelf();
        }

        private static void ForceRunInBackgroundOff(string reason)
        {
            if (Application.runInBackground)
            {
                Log?.LogInfo($"[RunInBackground] {reason}: true -> false に変更");
                Application.runInBackground = false;
            }
            else
            {
                Log?.LogDebug($"[RunInBackground] {reason}: 既に false");
            }
        }

        private IEnumerator KeepRunInBackgroundOff()
        {
            while (true)
            {
                ForceRunInBackgroundOff("Periodic");
                yield return new WaitForSeconds(1.0f);
            }
        }
    }

    /// <summary>
    /// タイトル画面の「新規ゲーム」行を無効化する例。
    /// QOLverPit の TitleScreenPatch.cs と同様に ScreenMenuScript.Open を書き換える。
    /// CloverAPI 依存の翻訳関数を直接呼び出せるように using を追加している。
    /// </summary>
    [HarmonyPatch(typeof(ScreenMenuScript), nameof(ScreenMenuScript.Open))]
    internal static class TitleScreenRemoveNewGame
    {
        [HarmonyPrefix]
        internal static void RemoveNewGame(ref string[] options, ref ScreenMenuScript.OptionEvent[] optionEvents)
        {
            // CloverAPI の Translation/Strings を利用してメニューの実ラベルに揃える
            var newGameLabel = Strings.Sanitize(Strings.SantizationKind.menus, Translation.Get("SCREEN_MENU_OPTION_NEW_RUN"));
            var continueLabel = Strings.Sanitize(Strings.SantizationKind.menus, Translation.Get("SCREEN_MENU_OPTION_CONTINUE"));

            if (options == null || optionEvents == null)
                return;

            bool hasContinue = false;
            bool hasNewGame = false;
            foreach (var opt in options)
            {
                if (opt == continueLabel) hasContinue = true;
                if (opt == newGameLabel) hasNewGame = true;
            }

            // Continue があるときだけ New Game を消す（タイトル初期メニューの誤操作防止）
            if (hasContinue && hasNewGame)
            {
                var newOptions = new System.Collections.Generic.List<string>(options.Length);
                var newEvents = new System.Collections.Generic.List<ScreenMenuScript.OptionEvent>(optionEvents.Length);

                for (int i = 0; i < options.Length; i++)
                {
                    if (options[i] == newGameLabel)
                    {
                        Log?.LogInfo("[TitleScreen] 新規ゲームをメニューから削除しました");
                        continue; // スキップ
                    }

                    newOptions.Add(options[i]);
                    if (i < optionEvents.Length)
                    {
                        newEvents.Add(optionEvents[i]);
                    }
                }

                options = newOptions.ToArray();
                optionEvents = newEvents.ToArray();
            }
        }
    }
}

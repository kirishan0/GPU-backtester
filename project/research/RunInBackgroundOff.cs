using BepInEx;
using BepInEx.Logging;
using HarmonyLib;
using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
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
        public const string PluginVersion = "1.0.1";

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

            // ScreenMenuScript.Open をリフレクションでパッチ（型が見つからない環境でもコンパイル可能にする）
            _harmony = new Harmony(PluginGuid);
            TitleScreenRemoveNewGame.TryPatch(_harmony);
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
    /// ScreenMenuScript がビルド環境に存在しない場合でもコンパイルできるよう、
    /// リフレクションで型を取得して Harmony パッチを当てる。
    /// </summary>
    internal static class TitleScreenRemoveNewGame
    {
        private static Type _screenMenuType;
        private static Type _optionEventType;
        private static MethodInfo _targetOpen;

        internal static void TryPatch(Harmony harmony)
        {
            try
            {
                _screenMenuType = AccessTools.TypeByName("ScreenMenuScript");
                if (_screenMenuType == null)
                {
                    RunInBackgroundOffPlugin.Log?.LogInfo("[TitleScreen] ScreenMenuScript が見つからなかったためパッチをスキップします");
                    return;
                }

                _optionEventType = AccessTools.Inner(_screenMenuType, "OptionEvent");
                if (_optionEventType == null)
                {
                    RunInBackgroundOffPlugin.Log?.LogInfo("[TitleScreen] ScreenMenuScript.OptionEvent が見つからなかったためパッチをスキップします");
                    return;
                }

                _targetOpen = AccessTools.Method(_screenMenuType, "Open", new[] { typeof(string[]), _optionEventType.MakeArrayType() });
                if (_targetOpen == null)
                {
                    RunInBackgroundOffPlugin.Log?.LogInfo("[TitleScreen] ScreenMenuScript.Open(string[], OptionEvent[]) が見つからなかったためパッチをスキップします");
                    return;
                }

                var prefix = new HarmonyMethod(typeof(TitleScreenRemoveNewGame).GetMethod(nameof(RemoveNewGame), BindingFlags.Static | BindingFlags.NonPublic));
                harmony.Patch(_targetOpen, prefix: prefix);

                RunInBackgroundOffPlugin.Log?.LogInfo("[TitleScreen] ScreenMenuScript.Open に新規ゲーム削除パッチを適用しました");
            }
            catch (Exception ex)
            {
                RunInBackgroundOffPlugin.Log?.LogWarning($"[TitleScreen] パッチ適用中に例外: {ex}");
            }
        }

        // HarmonyPrefix 用。OptionEvent[] を System.Array で受けることで、型が手元になくてもコンパイルできるようにする。
        private static void RemoveNewGame(ref string[] options, ref Array optionEvents)
        {
            if (_screenMenuType == null || _optionEventType == null || _targetOpen == null)
                return;

            if (options == null || optionEvents == null)
                return;

            // CloverAPI がある場合は翻訳済みラベルを使用し、なければデフォルト文字列にフォールバック
            string newGameLabel = "New Game";
            string continueLabel = "Continue";

            try
            {
                var stringsType = AccessTools.TypeByName("Strings");
                var translationType = AccessTools.TypeByName("Translation");

                if (stringsType != null && translationType != null)
                {
                    var sanitizeKindType = stringsType.GetNestedType("SantizationKind", BindingFlags.Public | BindingFlags.NonPublic);
                    var sanitizeKind = sanitizeKindType != null ? Enum.Parse(sanitizeKindType, "menus") : null;
                    var sanitize = sanitizeKind != null
                        ? AccessTools.Method(stringsType, "Sanitize", new[] { sanitizeKind.GetType(), typeof(string) })
                        : null;
                    var translationGet = AccessTools.Method(translationType, "Get", new[] { typeof(string) });

                    if (sanitize != null && translationGet != null)
                    {
                        var newGameRaw = translationGet.Invoke(null, new object[] { "SCREEN_MENU_OPTION_NEW_RUN" }) as string;
                        var continueRaw = translationGet.Invoke(null, new object[] { "SCREEN_MENU_OPTION_CONTINUE" }) as string;

                        if (!string.IsNullOrEmpty(newGameRaw))
                            newGameLabel = sanitize.Invoke(null, new object[] { sanitizeKind, newGameRaw }) as string ?? newGameLabel;
                        if (!string.IsNullOrEmpty(continueRaw))
                            continueLabel = sanitize.Invoke(null, new object[] { sanitizeKind, continueRaw }) as string ?? continueLabel;
                    }
                }
            }
            catch (Exception ex)
            {
                RunInBackgroundOffPlugin.Log?.LogDebug($"[TitleScreen] 翻訳ラベル取得中に例外: {ex}");
            }

            bool hasContinue = false;
            bool hasNewGame = false;
            foreach (var opt in options)
            {
                if (opt == continueLabel) hasContinue = true;
                if (opt == newGameLabel) hasNewGame = true;
            }

            if (!hasContinue || !hasNewGame)
                return;

            var newOptions = new List<string>(options.Length);
            var newEvents = new ArrayList(optionEvents.Length);

            for (int i = 0; i < options.Length; i++)
            {
                if (options[i] == newGameLabel)
                {
                    RunInBackgroundOffPlugin.Log?.LogInfo("[TitleScreen] 新規ゲームをメニューから削除しました");
                    continue;
                }

                newOptions.Add(options[i]);
                if (i < optionEvents.Length)
                {
                    newEvents.Add(optionEvents.GetValue(i));
                }
            }

            options = newOptions.ToArray();

            var typedEvents = Array.CreateInstance(_optionEventType, newEvents.Count);
            for (int i = 0; i < newEvents.Count; i++)
            {
                typedEvents.SetValue(newEvents[i], i);
            }

            optionEvents = typedEvents;
        }
    }
}

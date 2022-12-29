using p5rpc.lib.interfaces;
using p5rpc.ngpArcanaBonus.Configuration;
using p5rpc.ngpArcanaBonus.Template;
using Reloaded.Hooks.Definitions;
using Reloaded.Hooks.Definitions.X64;
using Reloaded.Hooks.ReloadedII.Interfaces;
using Reloaded.Memory.SigScan.ReloadedII.Interfaces;
using Reloaded.Mod.Interfaces;
using System.Diagnostics;
using static p5rpc.lib.interfaces.Enums;
using IReloadedHooks = Reloaded.Hooks.ReloadedII.Interfaces.IReloadedHooks;

namespace p5rpc.ngpArcanaBonus
{
    /// <summary>
    /// Your mod logic goes here.
    /// </summary>
    public class Mod : ModBase // <= Do not Remove.
    {
        /// <summary>
        /// Provides access to the mod loader API.
        /// </summary>
        private readonly IModLoader _modLoader;

        /// <summary>
        /// Provides access to the Reloaded.Hooks API.
        /// </summary>
        /// <remarks>This is null if you remove dependency on Reloaded.SharedLib.Hooks in your mod.</remarks>
        private readonly IReloadedHooks? _hooks;

        /// <summary>
        /// Provides access to the Reloaded logger.
        /// </summary>
        private readonly ILogger _logger;

        /// <summary>
        /// Entry point into the mod, instance that created this class.
        /// </summary>
        private readonly IMod _owner;

        /// <summary>
        /// Provides access to this mod's configuration.
        /// </summary>
        private Config _configuration;

        /// <summary>
        /// The configuration of the currently executing mod.
        /// </summary>
        private readonly IModConfig _modConfig;

        private IReverseWrapper<ShouldGiveBonusDelegate> _shouldGiveBonusReverseWrapper;

        private IP5RLib _p5rLib;

        private IAsmHook _shouldGiveBonusHook;

        public Mod(ModContext context)
        {
            _modLoader = context.ModLoader;
            _hooks = context.Hooks;
            _logger = context.Logger;
            _owner = context.Owner;
            _configuration = context.Configuration;
            _modConfig = context.ModConfig;

            Utils.Initialise(_logger, _configuration);

            var startupScannerController = _modLoader.GetController<IStartupScanner>();
            if (startupScannerController == null || !startupScannerController.TryGetTarget(out var startupScanner))
            {
                Utils.LogError($"Unable to get controller for Reloaded SigScan Library, aborting initialisation");
                return;
            }

            var p5rLibController = _modLoader.GetController<IP5RLib>();
            if (p5rLibController == null || !p5rLibController.TryGetTarget(out _p5rLib))
            {
                Utils.LogError($"Unable to get controller for P5R Lib, aborting initialisation");
                return;
            }

            startupScanner.AddMainModuleScan("75 ?? 0F B7 CE 0F 1F 44 ?? 00", result =>
            {
                if (!result.Found)
                {
                    Utils.LogError($"Unable to find signature for Arcana Bonus, aborting initialisation");
                    return;
                }
                Utils.LogDebug($"Found signature for Arcana Bonus at 0x{result.Offset + Utils.BaseAddress:X}");
                string[] function =
                {
                    "use64",
                    "jnz endHook", // If they're already going to get the bonus we don't want to change that
                    $"push rax\npush rcx\npush r8\npush r10",
                    "sub rsp, 32",
                    $"{_hooks.Utilities.GetAbsoluteCallMnemonics(ShouldGiveBonus, out _shouldGiveBonusReverseWrapper)}",
                    "add rsp, 32",
                    "cmp rax, 0",
                    "pop r10\npop r8\npop rcx\npop rax",
                    "label endHook"
                };
                _shouldGiveBonusHook = _hooks.CreateAsmHook(function, result.Offset + Utils.BaseAddress).Activate();

            });
        }

        private bool ShouldGiveBonus(Confidant confidant)
        {
            if (!_maxItems.ContainsKey(confidant))
            {
                Utils.LogError($"Unknown confidant {confidant}");
                return false;
            }
            if (_configuration.AlwaysBonus || _p5rLib.FlowCaller.GET_ITEM_NUM((int)_maxItems[confidant]) > 0)
            {
                Utils.LogDebug($"Giving bonus to {confidant}");
                return true;
            }
            Utils.LogDebug($"Not giving bonus to {confidant}");
            return false;
        }

        private Dictionary<Confidant, Item> _maxItems = new Dictionary<Confidant, Item>
        {
            { Confidant.Makoto, Item.Buchi_Calculator},
            { Confidant.Makoto_Friendzone, Item.Buchi_Calculator },
            { Confidant.Haru, Item.Dyed_Handkerchief },
            { Confidant.Haru_Friendzone, Item.Dyed_Handkerchief },
            { Confidant.Ann, Item.Fashion_Magazine },
            { Confidant.Ann_Friendzone, Item.Fashion_Magazine },
            { Confidant.Futaba, Item.Promise_List },
            { Confidant.Futaba_Friendzone, Item.Promise_List },
            { Confidant.Kawakami, Item.Unlimited_Service },
            { Confidant.Kawakami_Friendzone, Item.Unlimited_Service },
            { Confidant.Takemi, Item.Dog_Tag },
            { Confidant.Takemi_Friendzone, Item.Dog_Tag },
            { Confidant.Chihaya, Item.Fortune_Tarot_Card },
            { Confidant.Chihaya_Friendzone, Item.Fortune_Tarot_Card },
            { Confidant.Ohya, Item.Interview_Notes },
            { Confidant.Ohya_Friendzone, Item.Interview_Notes },
            { Confidant.Hifumi, Item.Kosha_Piece },
            { Confidant.Hifumi_Friendzone, Item.Kosha_Piece },
            { Confidant.Ryuji, Item.Sports_Watch },
            { Confidant.Morgana, Item.Morganas_Scarf },
            { Confidant.Sojiro, Item.Recipe_Notes },
            { Confidant.Mishima, Item.Documentary_Plans },
            { Confidant.Iwai, Item.Gecko_Pin },
            { Confidant.Twins, Item.Cell_Key },
            { Confidant.Yusuke, Item.Desire_and_Hope },
            { Confidant.Yoshida, Item.Fountain_Pen },
            { Confidant.Shinya, Item.Gun_Controller},
            { Confidant.Sae, Item.Business_Card },
            { Confidant.Sae_Friendzone, Item.Business_Card },
            { Confidant.Akechi, Item.Leather_Gloves },
            { Confidant.Kasumi, Item.Gymnastics_Baton },
            { Confidant.Kasumi_Friendzone, Item.Gymnastics_Baton },
            { Confidant.Sumire, Item.Gymnastics_Baton },
            { Confidant.Sumire_Friendzone, Item.Gymnastics_Baton },
            { Confidant.Maruki, Item.Research_Notebook }
        };

        [Function(FunctionAttribute.Register.rbx, FunctionAttribute.Register.rax, true)]
        private delegate bool ShouldGiveBonusDelegate(Confidant confidant);

        #region Standard Overrides
        public override void ConfigurationUpdated(Config configuration)
        {
            // Apply settings from configuration.
            // ... your code here.
            _configuration = configuration;
            _logger.WriteLine($"[{_modConfig.ModId}] Config Updated: Applying");
        }
        #endregion

        #region For Exports, Serialization etc.
#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
        public Mod() { }
#pragma warning restore CS8618
        #endregion
    }
}
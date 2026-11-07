using UnrealBuildTool;
using System.Collections.Generic;

public class PlanesUnrealEditorTarget : TargetRules
{
    public PlanesUnrealEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.V7;
        IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_8;
        ExtraModuleNames.Add("PlanesUnreal");
    }
}

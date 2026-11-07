using UnrealBuildTool;

public class PlanesUnreal : ModuleRules
{
    public PlanesUnreal(ReadOnlyTargetRules Target) : base(Target)
    {
        // This small runtime does not justify a multi-gigabyte editor PCH.
        PCHUsage = PCHUsageMode.NoPCHs;
        PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "InputCore", "CinematicCamera", "SlateCore" });
    }
}

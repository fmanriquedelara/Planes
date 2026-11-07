#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/HUD.h"
#include "GameFramework/GameModeBase.h"
#include "FlightModel/FlightModel.h"
#include "PlanesStudyRuntime.generated.h"

class ACineCameraActor;
class UVolumetricCloudComponent;
class UMaterialInstanceDynamic;
class UAudioComponent;
class UMeshComponent;
class UMaterialInterface;

UCLASS()
class PLANESUNREAL_API APlanesStudyPawn : public APawn
{
    GENERATED_BODY()
public:
    APlanesStudyPawn();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void SetupPlayerInputComponent(UInputComponent* Input) override;
    void ResetFlight();
    void ClearFlightInput();
    float GetSpeedMetresPerSecond() const { return static_cast<float>(Flight.speedMetresPerSecond); }
    bool IsGunHeld() const { return bGunHeld; }
private:
    UPROPERTY() TObjectPtr<USceneComponent> FlightRoot;
    UPROPERTY() TObjectPtr<UAudioComponent> GunAudio;
    FVector StartLocation;
    FRotator StartRotation;
    PlanesFlight::State Flight;
    double StepRemainder = 0;
    FRandomStream Gusts{4621};
    float PitchAxis = 0.f;
    float RollAxis = 0.f;
    float YawAxis = 0.f;
    float ThrottleAxis = 0.f;
    bool bHadViewportFocus = true;
    bool bGunHeld = false;
    void StartGun();
    void StopGun();
    void SetPitch(float Value);
    void SetRoll(float Value);
    void SetYaw(float Value);
    void SetThrottle(float Value);
};

UCLASS()
class PLANESUNREAL_API APlanesStudyPlayerController : public APlayerController
{
    GENERATED_BODY()
public:
    APlanesStudyPlayerController();
    virtual void BeginPlay() override;
    virtual void SetupInputComponent() override;
    virtual void Tick(float DeltaSeconds) override;
    bool IsStudyMenuOpen() const { return bMenuOpen; }
    bool IsTestFlightFrozen() const { return bTestFlightFrozen; }
    void ToggleStudyMenu();
    void ResumeFlight();
    void ExitPrototype();
    void SelectStudyView(int32 Index);
    void AdjustStudyFov(float Delta);
    void SelectCloudPreset(int32 Index);
    void ResetStudyView();
    bool HasCanopyBow() const { return ClearBowMaterial && !CanopyBowMeshes.IsEmpty(); }
    bool IsCanopyBowClear() const { return bClearCanopyBow; }
    void ToggleCanopyBow();
    int32 GetStudyViewIndex() const { return CurrentView; }
    int32 GetCloudPresetIndex() const { return CurrentCloudPreset; }
    float GetStudyFov() const { return ViewFovs[CurrentView]; }
    FString GetStudyViewLabel() const;
    FString GetCloudPresetLabel() const;
    UFUNCTION(Exec) void StudyMenu();
    UFUNCTION(Exec) void StudyResume();
    UFUNCTION(Exec) void StudyReset();
    UFUNCTION(Exec) void StudyState();
    UFUNCTION(Exec) void StudyView(int32 Index);
    UFUNCTION(Exec) void StudyClouds(int32 Index);
    UFUNCTION(Exec) void StudyFov(float VerticalDegrees);
private:
    bool bMenuOpen = false;
    void SetStudyMenuOpen(bool bOpen);
    UPROPERTY() TArray<TObjectPtr<ACineCameraActor>> StudyCameras;
    UPROPERTY() TObjectPtr<UVolumetricCloudComponent> StudyCloud;
    UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> CloudMaterial;
    int32 CurrentView = 0;
    int32 CurrentCloudPreset = 1;
    float ViewFovs[3] = {64.f, 60.f, 84.f};
    float DefaultViewFovs[3] = {64.f, 60.f, 84.f};
    FVector ViewBases[3];
    FRotator ViewBaseRotations[3];
    FVector ViewOffsets[3];
    FRotator ViewLookOffsets[3];
    FVector CameraMoveInput = FVector::ZeroVector;
    bool bMouseLooking = false;
    float ControllerLookYaw = 0;
    float ControllerLookPitch = 0;
    float FilteredLookYaw = 0;
    float FilteredLookPitch = 0;
    UPROPERTY() TArray<TObjectPtr<UMeshComponent>> CanopyBowMeshes;
    UPROPERTY() TArray<TObjectPtr<UMaterialInterface>> OpaqueBowMaterials;
    UPROPERTY() TObjectPtr<UMaterialInterface> ClearBowMaterial;
    bool bClearCanopyBow = false;
    void InitializeCanopyBow();
    void ApplyCanopyBow();
    void ControllerLookSide(float Value);
    void ControllerLookUp(float Value);
    void InitializeStudyCameras();
    void UpdateStudyCameras(float DeltaSeconds);
    void CycleStudyView();
    void SelectPilotView();
    void SelectChaseView();
    void SelectMountView();
    void StartCameraLook();
    void StopCameraLook();
    void CameraForward(float Value);
    void CameraSide(float Value);
    void CameraHeight(float Value);
    void CameraLookX(float Value);
    void CameraLookY(float Value);
    bool bSelfTest = false;
    bool bTestFlightFrozen = false;
    int32 TestStage = 0;
    double TestStageTime = 0;
    double TestStartedTime = 0;
    FVector TestLocation;
    FRotator TestRotation;
    FString TestOutputDirectory;
    TMap<FString, bool> TestChecks;
    TArray<FString> TestSnapshots;
    float TestFov = 0;
    int32 TestCloudIndex = 0;
    void CaptureTestSnapshot(const FString& Name);
    void InjectTestKey(FKey Key, EInputEvent Event);
    void InjectTestAxis(FKey Key, float Value);
    void TestCheck(const FString& Name, bool bPassed);
    void WriteTestReport();
    void TickSelfTest();
};

UCLASS()
class PLANESUNREAL_API APlanesStudyHUD : public AHUD
{
    GENERATED_BODY()
public:
    virtual void DrawHUD() override;
    virtual void NotifyHitBoxClick(FName BoxName) override;
    bool AutomationClickButton(FName BoxName);
private:
    TMap<FName, FVector2D> MenuButtonCentres;
    UPROPERTY() TObjectPtr<class UFont> RuntimeHudFont;
};

UCLASS()
class PLANESUNREAL_API APlanesStudyGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    APlanesStudyGameMode();
};


#include "PlanesStudyRuntime.h"

#include "Camera/CameraActor.h"
#include "CineCameraActor.h"
#include "CineCameraComponent.h"

#include "Components/VolumetricCloudComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Components/InputComponent.h"
#include "Components/SceneComponent.h"
#include "Components/MeshComponent.h"
#include "Components/AudioComponent.h"
#include "Sound/SoundWave.h"
#include "Engine/Canvas.h"
#include "Engine/Font.h"
#include "CanvasItem.h"
#include "Fonts/CompositeFont.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "InputCoreTypes.h"
#include "InputKeyEventArgs.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "UnrealClient.h"

APlanesStudyPawn::APlanesStudyPawn()
{
    PrimaryActorTick.bCanEverTick = true;
    FlightRoot = CreateDefaultSubobject<USceneComponent>(TEXT("FlightRoot"));
    SetRootComponent(FlightRoot);
    GunAudio = CreateDefaultSubobject<UAudioComponent>(TEXT("GunAudio"));
    GunAudio->SetupAttachment(FlightRoot);
    GunAudio->bAutoActivate = false;
    AutoPossessPlayer = EAutoReceiveInput::Player0;
}

void APlanesStudyPawn::BeginPlay()
{
    Super::BeginPlay();
    StartLocation = GetActorLocation();
    StartRotation = GetActorRotation();
    GunAudio->SetSound(LoadObject<USoundWave>(nullptr, TEXT("/Game/StudyAudio/GunTrimmed.GunTrimmed")));
}

void APlanesStudyPawn::SetupPlayerInputComponent(UInputComponent* Input)
{
    Super::SetupPlayerInputComponent(Input);
    Input->BindAxis(TEXT("StudyPitch"), this, &APlanesStudyPawn::SetPitch);
    Input->BindAxis(TEXT("StudyRoll"), this, &APlanesStudyPawn::SetRoll);
    Input->BindAxis(TEXT("StudyYaw"), this, &APlanesStudyPawn::SetYaw);
    Input->BindAxis(TEXT("StudyThrottle"), this, &APlanesStudyPawn::SetThrottle);
    Input->BindKey(EKeys::Gamepad_FaceButton_Bottom, IE_Pressed, this, &APlanesStudyPawn::StartGun);
    Input->BindKey(EKeys::Gamepad_FaceButton_Bottom, IE_Released, this, &APlanesStudyPawn::StopGun);
}

void APlanesStudyPawn::SetPitch(float Value) { PitchAxis = FMath::Clamp(Value, -1.f, 1.f); }
void APlanesStudyPawn::SetRoll(float Value) { RollAxis = FMath::Clamp(Value, -1.f, 1.f); }
void APlanesStudyPawn::SetYaw(float Value) { YawAxis = FMath::Clamp(Value, -1.f, 1.f); }
void APlanesStudyPawn::SetThrottle(float Value) { ThrottleAxis = FMath::Clamp(Value, -1.f, 1.f); }
void APlanesStudyPawn::StartGun() { bGunHeld = true; }
void APlanesStudyPawn::StopGun() { bGunHeld = false; GunAudio->Stop(); }
void APlanesStudyPawn::ClearFlightInput()
{
    PitchAxis = RollAxis = YawAxis = ThrottleAxis = 0.f;
    StopGun();
}

void APlanesStudyPawn::ResetFlight()
{
    ClearFlightInput();
    SetActorLocationAndRotation(StartLocation, StartRotation, false, nullptr, ETeleportType::TeleportPhysics);
    Flight = {};
    StepRemainder = 0;
    Gusts.Reset();
    UE_LOG(LogTemp, Display, TEXT("PLANES_RUNTIME ResetFlight"));
}

void APlanesStudyPawn::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!Controller || GetWorld()->IsPaused()) return;
    const APlanesStudyPlayerController* PC = Cast<APlanesStudyPlayerController>(Controller);
    if (PC && (PC->IsStudyMenuOpen() || PC->IsTestFlightFrozen())) return;
    // MRQ is the reproducible static visual baseline; normal -game is flight.
    if (FString(FCommandLine::Get()).Contains(TEXT("MoviePipelineConfig"))) return;
    const bool bTesting = FParse::Param(FCommandLine::Get(), TEXT("PlanesSelfTest"));
    if (!bTesting && GEngine && GEngine->GameViewport && GEngine->GameViewport->Viewport)
    {
        const bool bFocused = GEngine->GameViewport->Viewport->HasFocus();
        if (!bFocused)
        {
            ClearFlightInput();
            if (bHadViewportFocus) if (APlayerController* Player = Cast<APlayerController>(Controller)) Player->FlushPressedKeys();
        }
        bHadViewportFocus = bFocused;
    }
    if (bGunHeld && GunAudio->Sound && !GunAudio->IsPlaying()) GunAudio->Play();

    constexpr double StepSeconds = 1.0 / 120.0;
    StepRemainder += FMath::Clamp(static_cast<double>(DeltaSeconds), 0.0, 0.25);
    while (StepRemainder >= StepSeconds)
    {
        PlanesFlight::Inputs Inputs{PitchAxis, RollAxis, YawAxis, ThrottleAxis};
        if (!bTesting)
        {
            Inputs.pitchGust = Gusts.FRandRange(-.05f, .05f);
            Inputs.rollGust = Gusts.FRandRange(-.05f, .05f);
        }
        PlanesFlight::Step(Flight, Inputs, StepSeconds);
        StepRemainder -= StepSeconds;
    }
    // Positions are polar vectors. Quaternion XYZ is axial and picks up the
    // additional sign flip from converting Godot to Unreal handedness.
    const auto& P = Flight.positionMetres;
    const auto& Q = Flight.attitude;
    const FQuat Start = StartRotation.Quaternion();
    const FVector Position = StartLocation + Start.RotateVector(FVector(-P.x, -P.z, P.y) * 100);
    SetActorLocationAndRotation(Position, Start * FQuat(Q.x, Q.z, -Q.y, Q.w), false);
}

APlanesStudyPlayerController::APlanesStudyPlayerController()
{
    bShouldPerformFullTickWhenPaused = true;
    PrimaryActorTick.bTickEvenWhenPaused = true;
}

void APlanesStudyPlayerController::BeginPlay()
{
    Super::BeginPlay();
    for (TActorIterator<APlanesStudyPawn> It(GetWorld()); It; ++It)
    {
        if (It->ActorHasTag(TEXT("PlanesPilotRig"))) { Possess(*It); break; }
    }
    for (TActorIterator<ACameraActor> It(GetWorld()); It; ++It)
    {
        if (It->ActorHasTag(TEXT("PlanesPilotCamera"))) { SetViewTarget(*It); break; }
    }
    InitializeCanopyBow();
    InitializeStudyCameras();
    for (TActorIterator<AVolumetricCloud> It(GetWorld()); It; ++It)
    {
        StudyCloud = It->FindComponentByClass<UVolumetricCloudComponent>();
        if (StudyCloud && StudyCloud->GetMaterial())
        {
            CloudMaterial = UMaterialInstanceDynamic::Create(StudyCloud->GetMaterial(), this);
            StudyCloud->SetMaterial(CloudMaterial);
            SelectCloudPreset(1);
        }
        break;
    }
    SetInputMode(FInputModeGameOnly());
    bSelfTest = FParse::Param(FCommandLine::Get(), TEXT("PlanesSelfTest"));
    if (bSelfTest)
    {
        TestOutputDirectory = FPaths::Combine(FPaths::ProjectDir(), TEXT("artifacts/runtime-tests"));
        FParse::Value(FCommandLine::Get(), TEXT("PlanesTestOutput="), TestOutputDirectory);
        IFileManager::Get().MakeDirectory(*TestOutputDirectory, true);
        TestStartedTime = TestStageTime = FPlatformTime::Seconds();
    }
    UE_LOG(LogTemp, Display, TEXT("PLANES_RUNTIME Ready Pawn=%s Camera=%s"), *GetNameSafe(GetPawn()), *GetNameSafe(GetViewTarget()));
}

void APlanesStudyPlayerController::SetupInputComponent()
{
    Super::SetupInputComponent();
    FInputKeyBinding& Escape = InputComponent->BindKey(EKeys::Escape, IE_Pressed, this, &APlanesStudyPlayerController::ToggleStudyMenu);
    Escape.bExecuteWhenPaused = true;
    InputComponent->BindKey(EKeys::R, IE_Pressed, this, &APlanesStudyPlayerController::StudyReset);
    InputComponent->BindKey(EKeys::C, IE_Pressed, this, &APlanesStudyPlayerController::CycleStudyView);
    InputComponent->BindKey(EKeys::Gamepad_FaceButton_Top, IE_Pressed, this, &APlanesStudyPlayerController::CycleStudyView);
    InputComponent->BindKey(EKeys::B, IE_Pressed, this, &APlanesStudyPlayerController::ToggleCanopyBow).bExecuteWhenPaused = true;
    InputComponent->BindKey(EKeys::One, IE_Pressed, this, &APlanesStudyPlayerController::SelectPilotView);
    InputComponent->BindKey(EKeys::Two, IE_Pressed, this, &APlanesStudyPlayerController::SelectChaseView);
    InputComponent->BindKey(EKeys::Three, IE_Pressed, this, &APlanesStudyPlayerController::SelectMountView);
    InputComponent->BindKey(EKeys::Home, IE_Pressed, this, &APlanesStudyPlayerController::ResetStudyView);
    InputComponent->BindKey(EKeys::RightMouseButton, IE_Pressed, this, &APlanesStudyPlayerController::StartCameraLook);
    InputComponent->BindKey(EKeys::RightMouseButton, IE_Released, this, &APlanesStudyPlayerController::StopCameraLook);
    InputComponent->BindAxis(TEXT("CameraForward"), this, &APlanesStudyPlayerController::CameraForward);
    InputComponent->BindAxis(TEXT("CameraSide"), this, &APlanesStudyPlayerController::CameraSide);
    InputComponent->BindAxis(TEXT("CameraHeight"), this, &APlanesStudyPlayerController::CameraHeight);
    InputComponent->BindAxis(TEXT("CameraLookX"), this, &APlanesStudyPlayerController::CameraLookX);
    InputComponent->BindAxis(TEXT("CameraLookY"), this, &APlanesStudyPlayerController::CameraLookY);
    InputComponent->BindAxis(TEXT("ControllerLookSide"), this, &APlanesStudyPlayerController::ControllerLookSide);
    InputComponent->BindAxis(TEXT("ControllerLookUp"), this, &APlanesStudyPlayerController::ControllerLookUp);
}

void APlanesStudyPlayerController::InitializeCanopyBow()
{
    for (TActorIterator<AActor> It(GetWorld()); It; ++It)
    {
        for (AActor* Parent = It->GetAttachParentActor(); Parent; Parent = Parent->GetAttachParentActor())
        {
            if (Parent != GetPawn()) continue;
            for (UActorComponent* Component : It->GetComponentsByTag(UMeshComponent::StaticClass(), TEXT("PlanesCanopyBow")))
            {
                auto* Mesh = CastChecked<UMeshComponent>(Component);
                CanopyBowMeshes.Add(Mesh);
                OpaqueBowMaterials.Add(Mesh->GetMaterial(0));
            }
            break;
        }
    }
    if (!CanopyBowMeshes.IsEmpty())
        ClearBowMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/EurofighterCockpitStudy/Materials/M_CanopyBowClear.M_CanopyBowClear"));
}

void APlanesStudyPlayerController::ApplyCanopyBow()
{
    if (!HasCanopyBow()) return;
    const bool bClear = bClearCanopyBow && CurrentView == 0;
    for (int32 Index = 0; Index < CanopyBowMeshes.Num(); ++Index)
    {
        CanopyBowMeshes[Index]->SetMaterial(0, bClear ? ClearBowMaterial.Get() : OpaqueBowMaterials[Index].Get());
        CanopyBowMeshes[Index]->SetCastShadow(!bClear);
    }
}

void APlanesStudyPlayerController::ToggleCanopyBow()
{
    if (!HasCanopyBow()) return;
    bClearCanopyBow = !bClearCanopyBow;
    ApplyCanopyBow();
}

void APlanesStudyPlayerController::SetStudyMenuOpen(bool bOpen)
{
    bMenuOpen = bOpen;
    bMouseLooking = false;
    CameraMoveInput = FVector::ZeroVector;
    if (APlanesStudyPawn* Plane = Cast<APlanesStudyPawn>(GetPawn())) Plane->ClearFlightInput();
    FlushPressedKeys();
    SetPause(bOpen);
    bShowMouseCursor = bOpen;
    bEnableClickEvents = bOpen;
    bEnableMouseOverEvents = bOpen;
    if (bOpen)
    {
        FInputModeGameAndUI Mode;
        Mode.SetHideCursorDuringCapture(false);
        Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
        SetInputMode(Mode);
    }
    else
    {
        SetInputMode(FInputModeGameOnly());
    }
    UE_LOG(LogTemp, Display, TEXT("PLANES_RUNTIME Menu=%d Paused=%d"), bOpen, GetWorld()->IsPaused());
}

void APlanesStudyPlayerController::ToggleStudyMenu() { SetStudyMenuOpen(!bMenuOpen); }
void APlanesStudyPlayerController::ResumeFlight() { SetStudyMenuOpen(false); }
void APlanesStudyPlayerController::StudyMenu() { ToggleStudyMenu(); }
void APlanesStudyPlayerController::StudyResume() { ResumeFlight(); }
void APlanesStudyPlayerController::StudyReset()
{
    if (!bMenuOpen) if (APlanesStudyPawn* Plane = Cast<APlanesStudyPawn>(GetPawn())) Plane->ResetFlight();
}

void APlanesStudyPlayerController::ExitPrototype()
{
    UE_LOG(LogTemp, Display, TEXT("PLANES_RUNTIME Exit requested"));
    UKismetSystemLibrary::QuitGame(this, this, EQuitPreference::Quit, false);
}

void APlanesStudyPlayerController::StudyState()
{
    const APlanesStudyPawn* Plane = Cast<APlanesStudyPawn>(GetPawn());
    if (!Plane) { UE_LOG(LogTemp, Warning, TEXT("PLANES_STATE No possessed flight rig")); return; }
    UE_LOG(LogTemp, Display, TEXT("PLANES_STATE Menu=%d Paused=%d Position=%s Rotation=%s SpeedMps=%.3f"),
        bMenuOpen, GetWorld()->IsPaused(), *GetPawn()->GetActorLocation().ToString(),
        *GetPawn()->GetActorRotation().ToString(), Plane ? Plane->GetSpeedMetresPerSecond() : 0.f);
}

void APlanesStudyPlayerController::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    UpdateStudyCameras(DeltaSeconds);
    if (bSelfTest) TickSelfTest();
}

void APlanesStudyPlayerController::InitializeStudyCameras()
{
    ACineCameraActor* Pilot = Cast<ACineCameraActor>(GetViewTarget());
    if (!Pilot || !GetPawn()) return;
    StudyCameras.SetNum(3);
    StudyCameras[0] = Pilot;
    ViewBases[0] = Pilot->GetRootComponent()->GetRelativeLocation();
    ViewBaseRotations[0] = Pilot->GetRootComponent()->GetRelativeRotation();
    ViewBases[1] = FVector(-1900, 0, 650);
    ViewBaseRotations[1] = FRotator::ZeroRotator;
    // The rear raised point intersects the Eurofighter canopy cross-frame.
    // Mount ahead of that frame, still within the authored canopy bounds.
    const bool bGripen = GetPawn()->ActorHasTag(TEXT("PlanesAircraftGripen"));
    ViewBases[2] = ViewBases[0] + FVector(bGripen ? 47 : 90, 0, 8);
    ViewBaseRotations[2] = FRotator(-13, 0, 0);
    UCineCameraComponent* Original = Pilot->GetCineCameraComponent();
    auto PilotLens = Original->LensSettings; PilotLens.MinFocalLength = 1.f; PilotLens.MaxFocalLength = 1000.f; Original->SetLensSettings(PilotLens);
    ViewFovs[0] = DefaultViewFovs[0] = Original->GetVerticalFieldOfView();
    for (int32 Index = 0; Index < 3; ++Index)
    {
        ViewOffsets[Index] = FVector::ZeroVector;
        ViewLookOffsets[Index] = FRotator::ZeroRotator;
        if (Index == 0) continue;
        ACineCameraActor* Extra = GetWorld()->SpawnActor<ACineCameraActor>();
        Extra->AttachToActor(GetPawn(), FAttachmentTransformRules::KeepRelativeTransform);
        Extra->SetActorRelativeLocation(ViewBases[Index]);
        UCineCameraComponent* Camera = Extra->GetCineCameraComponent();
        Camera->SetFilmback(Original->Filmback);
        auto Lens = Original->LensSettings; Lens.MinFocalLength = 1.f; Lens.MaxFocalLength = 1000.f; Camera->SetLensSettings(Lens);
        Camera->SetFocusSettings(Original->FocusSettings);
        Camera->SetCurrentAperture(Original->CurrentAperture);
        Camera->PostProcessSettings = Original->PostProcessSettings;
        Camera->PostProcessBlendWeight = 1.f;
        Camera->SetConstraintAspectRatio(false);
        Camera->bOverrideAspectRatioAxisConstraint = true;
        Camera->SetAspectRatioAxisConstraint(EAspectRatioAxisConstraint::AspectRatio_MaintainYFOV);
        if (Index == 1) Extra->GetRootComponent()->SetUsingAbsoluteRotation(true);
        StudyCameras[Index] = Extra;
    }
    SelectStudyView(0);
}

void APlanesStudyPlayerController::UpdateStudyCameras(float DeltaSeconds)
{
    if (StudyCameras.Num() != 3 || !GetPawn()) return;
    bool bFocused = true;
    if (!bSelfTest && GEngine && GEngine->GameViewport && GEngine->GameViewport->Viewport)
        bFocused = GEngine->GameViewport->Viewport->HasFocus();
    if (!bFocused || bMenuOpen)
    {
        CameraMoveInput = FVector::ZeroVector;
        bMouseLooking = false;
    }
    else
    {
        const float LookStep = FMath::Clamp(DeltaSeconds, 0.f, .25f) / .5f;
        FilteredLookYaw += (ControllerLookYaw - FilteredLookYaw) * LookStep;
        FilteredLookPitch += (ControllerLookPitch - FilteredLookPitch) * LookStep;
        const float Speed = CurrentView == 1 ? 350.f : 35.f;
        ViewOffsets[CurrentView] += CameraMoveInput * Speed * FMath::Clamp(DeltaSeconds, 0.f, .25f);
        FVector& Offset = ViewOffsets[CurrentView];
        if (CurrentView == 1)
        {
            Offset.X = FMath::Clamp(Offset.X, -1200.0, 650.0);
            Offset.Y = FMath::Clamp(Offset.Y, -1200.0, 1200.0);
            Offset.Z = FMath::Clamp(Offset.Z, -300.0, 900.0);
        }
        else
        {
            Offset.X = FMath::Clamp(Offset.X, -35.0, 25.0);
            Offset.Y = FMath::Clamp(Offset.Y, -22.0, 22.0);
            Offset.Z = FMath::Clamp(Offset.Z, -18.0, CurrentView == 2 ? 5.0 : 12.0);
        }
    }
    for (int32 Index = 0; Index < 3; ++Index)
    {
        ACineCameraActor* Camera = StudyCameras[Index];
        if (!Camera) continue;
        Camera->SetActorRelativeLocation(ViewBases[Index] + ViewOffsets[Index]);
        FRotator Look = ViewLookOffsets[Index];
        if (Index == CurrentView)
        {
            Look.Yaw += FMath::RadiansToDegrees(FilteredLookYaw);
            Look.Pitch += FMath::RadiansToDegrees(FilteredLookPitch);
        }
        if (Index == 1)
        {
            const FVector Target = GetPawn()->GetActorLocation() + GetPawn()->GetActorForwardVector() * 350;
            FRotator Rotation = (Target - Camera->GetActorLocation()).Rotation();
            Rotation.Pitch += Look.Pitch;
            Rotation.Yaw += Look.Yaw;
            Camera->SetActorRotation(Rotation);
        }
        else Camera->SetActorRelativeRotation(ViewBaseRotations[Index] + Look);
        UCineCameraComponent* Cine = Camera->GetCineCameraComponent();
        const float FocalLength = Cine->Filmback.SensorHeight / (2.f * FMath::Tan(FMath::DegreesToRadians(ViewFovs[Index] * .5f)));
        Cine->SetCurrentFocalLength(FocalLength);
    }
}

void APlanesStudyPlayerController::SelectStudyView(int32 Index)
{
    CurrentView = FMath::Clamp(Index, 0, 2);
    ApplyCanopyBow();
    CameraMoveInput = FVector::ZeroVector;
    bMouseLooking = false;
    UpdateStudyCameras(0);
    if (StudyCameras.IsValidIndex(CurrentView) && StudyCameras[CurrentView]) SetViewTarget(StudyCameras[CurrentView]);
    UE_LOG(LogTemp, Display, TEXT("PLANES_CAMERA View=%s VerticalFOV=%.2f"), *GetStudyViewLabel(), GetStudyFov());
}

void APlanesStudyPlayerController::CycleStudyView() { SelectStudyView((CurrentView + 1) % 3); }
void APlanesStudyPlayerController::SelectPilotView() { SelectStudyView(0); }
void APlanesStudyPlayerController::SelectChaseView() { SelectStudyView(1); }
void APlanesStudyPlayerController::SelectMountView() { SelectStudyView(2); }
void APlanesStudyPlayerController::StudyView(int32 Index) { SelectStudyView(Index - 1); }
void APlanesStudyPlayerController::StudyClouds(int32 Index) { SelectCloudPreset(Index); }
void APlanesStudyPlayerController::StudyFov(float VerticalDegrees) { AdjustStudyFov(VerticalDegrees - GetStudyFov()); }
void APlanesStudyPlayerController::AdjustStudyFov(float Delta)
{
    ViewFovs[CurrentView] = FMath::Clamp(ViewFovs[CurrentView] + Delta, 40.f, 100.f);
    UpdateStudyCameras(0);
}
void APlanesStudyPlayerController::ResetStudyView()
{
    ViewOffsets[CurrentView] = FVector::ZeroVector;
    ViewLookOffsets[CurrentView] = FRotator::ZeroRotator;
    FilteredLookYaw = FilteredLookPitch = 0;
    ViewFovs[CurrentView] = DefaultViewFovs[CurrentView];
    UpdateStudyCameras(0);
}
void APlanesStudyPlayerController::StartCameraLook() { if (!bMenuOpen) bMouseLooking = true; }
void APlanesStudyPlayerController::StopCameraLook() { bMouseLooking = false; }
void APlanesStudyPlayerController::CameraForward(float Value) { CameraMoveInput.X = Value; }
void APlanesStudyPlayerController::CameraSide(float Value) { CameraMoveInput.Y = Value; }
void APlanesStudyPlayerController::CameraHeight(float Value) { CameraMoveInput.Z = Value; }
void APlanesStudyPlayerController::ControllerLookSide(float Value) { ControllerLookYaw = Value; }
void APlanesStudyPlayerController::ControllerLookUp(float Value) { ControllerLookPitch = FMath::Max(Value, 0.f); }
void APlanesStudyPlayerController::CameraLookX(float Value)
{
    if (bMouseLooking && !bMenuOpen) ViewLookOffsets[CurrentView].Yaw = FMath::Clamp(ViewLookOffsets[CurrentView].Yaw + Value * .15f, -110.f, 110.f);
}
void APlanesStudyPlayerController::CameraLookY(float Value)
{
    if (bMouseLooking && !bMenuOpen) ViewLookOffsets[CurrentView].Pitch = FMath::Clamp(ViewLookOffsets[CurrentView].Pitch + Value * .15f, -65.f, 55.f);
}
FString APlanesStudyPlayerController::GetStudyViewLabel() const
{
    static const TCHAR* Names[] = {TEXT("COCKPIT"), TEXT("CHASE"), TEXT("CANOPY MOUNT")};
    return Names[CurrentView];
}
FString APlanesStudyPlayerController::GetCloudPresetLabel() const
{
    static const TCHAR* Names[] = {TEXT("CLEAR"), TEXT("SCATTERED"), TEXT("BROKEN"), TEXT("OVERCAST")};
    return Names[CurrentCloudPreset];
}
void APlanesStudyPlayerController::SelectCloudPreset(int32 Index)
{
    CurrentCloudPreset = FMath::Clamp(Index, 0, 3);
    if (!CloudMaterial || !StudyCloud) return;
    static const float Coverage[] = {-1.f, -.2f, .12f, .48f};
    static const float Density[] = {0.f, .008f, .014f, .022f};
    static const FLinearColor Types[] = {
        FLinearColor(1, 0, 0, 0), FLinearColor(.8f, .2f, 0, 0),
        FLinearColor(.8f, .35f, .1f, .1f), FLinearColor(.7f, .6f, .2f, .5f)};
    CloudMaterial->SetScalarParameterValue(TEXT("Cloud_GlobalCoverage"), Coverage[CurrentCloudPreset]);
    CloudMaterial->SetScalarParameterValue(TEXT("Cloud_GlobalDensity"), Density[CurrentCloudPreset]);
    CloudMaterial->SetVectorParameterValue(TEXT("Layout_CloudTypeMask"), Types[CurrentCloudPreset]);
    StudyCloud->SetVisibility(CurrentCloudPreset != 0, true);
    UE_LOG(LogTemp, Display, TEXT("PLANES_CLOUDS Preset=%s CoverageBias=%.3f Density=%.4f"),
        *GetCloudPresetLabel(), Coverage[CurrentCloudPreset], Density[CurrentCloudPreset]);
}

void APlanesStudyPlayerController::InjectTestKey(FKey Key, EInputEvent Event)
{
    FViewport* Viewport = GEngine && GEngine->GameViewport ? GEngine->GameViewport->Viewport : nullptr;
    InputKey(FInputKeyEventArgs(Viewport, INPUTDEVICEID_NONE, Key, Event, FPlatformTime::Cycles64()));
}

void APlanesStudyPlayerController::InjectTestAxis(FKey Key, float Value)
{
    InputKey(FInputKeyEventArgs(GEngine->GameViewport->Viewport, INPUTDEVICEID_NONE,
        Key, Value, 1.f / 60, 1, FPlatformTime::Cycles64()));
}

void APlanesStudyPlayerController::TestCheck(const FString& Name, bool bPassed)
{
    TestChecks.Add(Name, bPassed);
    UE_LOG(LogTemp, Display, TEXT("PLANES_TEST %s %s"), *Name, bPassed ? TEXT("PASS") : TEXT("FAIL"));
}

void APlanesStudyPlayerController::CaptureTestSnapshot(const FString& Name)
{
    auto* Camera=StudyCameras.IsValidIndex(CurrentView)?StudyCameras[CurrentView].Get():nullptr;
    if(!Camera) return;
    const FVector P=Camera->GetRootComponent()->GetRelativeLocation();
    const FRotator R=Camera->GetActorRotation();
    TestSnapshots.Add(FString::Printf(TEXT("{\"file\":\"%s.png\",\"view\":\"%s\",\"vertical_fov\":%.3f,\"clouds\":\"%s\",\"relative_cm\":[%.3f,%.3f,%.3f],\"rotation\":[%.3f,%.3f,%.3f]}"),*Name,*GetStudyViewLabel(),Camera->GetCineCameraComponent()->GetVerticalFieldOfView(),*GetCloudPresetLabel(),P.X,P.Y,P.Z,R.Pitch,R.Yaw,R.Roll));
    FScreenshotRequest::RequestScreenshot(FPaths::Combine(TestOutputDirectory,Name+TEXT(".png")),true,false);
}

void APlanesStudyPlayerController::WriteTestReport()
{
    FString Json = TEXT("{\n  \"input_route\": \"PlayerController InputKey and HUD hitbox dispatch\",\n  \"checks\": {\n");
    bool bFirst = true;
    for (const auto& Check : TestChecks)
    {
        if (!bFirst) Json += TEXT(",\n");
        bFirst = false;
        Json += FString::Printf(TEXT("    \"%s\": %s"), *Check.Key, Check.Value ? TEXT("true") : TEXT("false"));
    }
    Json += TEXT("\n  },\n  \"snapshots\": [") + FString::Join(TestSnapshots,TEXT(",")) + TEXT("],\n  \"exit_route\": \"Exit Prototype HUD button\"\n}\n");
    FFileHelper::SaveStringToFile(Json, *FPaths::Combine(TestOutputDirectory, TEXT("runtime-report.json")));
}

void APlanesStudyPlayerController::TickSelfTest()
{
    const double Now = FPlatformTime::Seconds();
    APlanesStudyPawn* Plane = Cast<APlanesStudyPawn>(GetPawn());
    if (!Plane || Now - TestStartedTime > 90)
    {
        TestCheck(TEXT("completed_before_timeout"), false);
        WriteTestReport();
        bSelfTest = false;
        ExitPrototype();
        return;
    }
    const double Elapsed = Now - TestStageTime;
    auto Next = [this, Now]() { ++TestStage; TestStageTime = Now; };
    auto BowUses = [this](bool bClear)
    {
        if (CanopyBowMeshes.Num() != 4) return false;
        for (int32 Index = 0; Index < CanopyBowMeshes.Num(); ++Index)
        {
            const auto* Expected = bClear ? ClearBowMaterial.Get() : OpaqueBowMaterials[Index].Get();
            if (CanopyBowMeshes[Index]->GetMaterial(0) != Expected) return false;
        }
        return true;
    };
    switch (TestStage)
    {
    case 0:
        if (Elapsed < 2) return;
        TestLocation = Plane->GetActorLocation();
        Next(); break;
    case 1:
        if (Elapsed < .4) return;
        TestCheck(TEXT("autopilot_moves_forward"), FVector::Dist(TestLocation, Plane->GetActorLocation()) > 100);
        InjectTestKey(EKeys::Up, IE_Pressed); InjectTestKey(EKeys::W, IE_Pressed);
        Next(); break;
    case 2:
        if (Elapsed < .5) return;
        TestCheck(TEXT("arrow_pitch_binding"), Plane->GetActorRotation().Pitch > 2);
        TestCheck(TEXT("throttle_binding"), Plane->GetSpeedMetresPerSecond() > 103);
        InjectTestKey(EKeys::Up, IE_Released); InjectTestKey(EKeys::W, IE_Released);
        Plane->ResetFlight();
        InjectTestKey(EKeys::E, IE_Pressed);
        TestStage=29; TestStageTime=Now; break;
    case 29:
        if (Elapsed < .35) return;
        TestCheck(TEXT("yaw_binding"), Plane->GetActorRotation().Yaw > 2);
        InjectTestKey(EKeys::E, IE_Released);
        Plane->ResetFlight();
        InjectTestKey(EKeys::Right, IE_Pressed);
        TestStage=34; TestStageTime=Now; break;
    case 34:
        if (Elapsed < .35) return;
        TestCheck(TEXT("arrow_bank_binding"), Plane->GetActorRotation().Roll > 4);
        InjectTestKey(EKeys::Right, IE_Released);
        InjectTestKey(EKeys::Escape, IE_Pressed);
        TestStage=3; TestStageTime=Now; break;
    case 3:
        if (Elapsed < .3) return;
        InjectTestKey(EKeys::Escape, IE_Released);
        TestCheck(TEXT("escape_opens_paused_menu"), bMenuOpen && GetWorld()->IsPaused() && bShowMouseCursor);
        TestLocation = Plane->GetActorLocation();
        TestRotation = StudyCameras[0]->GetActorRotation();
        InjectTestKey(EKeys::I, IE_Pressed);
        FScreenshotRequest::RequestScreenshot(FPaths::Combine(TestOutputDirectory, TEXT("runtime-menu.png")), true, false);
        InjectTestKey(EKeys::Right, IE_Pressed); InjectTestKey(EKeys::W, IE_Pressed);
        Next(); break;
    case 4:
        if (Elapsed < .4) return;
        TestCheck(TEXT("menu_freezes_aircraft"), FVector::Dist(TestLocation, Plane->GetActorLocation()) < .01);
        TestCheck(TEXT("menu_freezes_camera"),ViewOffsets[0].IsNearlyZero()&&StudyCameras[0]->GetActorRotation().Equals(TestRotation,.01f));
        InjectTestKey(EKeys::I,IE_Released);
        InjectTestKey(EKeys::Right, IE_Released); InjectTestKey(EKeys::W, IE_Released);
        if (APlanesStudyHUD* HUD = Cast<APlanesStudyHUD>(GetHUD()))
            TestCheck(TEXT("resume_hitbox_click"), HUD->AutomationClickButton(TEXT("ResumeFlight")) && !bMenuOpen);
        else TestCheck(TEXT("resume_hitbox_click"), false);
        Next(); break;
    case 5:
        if (Elapsed < .35) return;
        TestCheck(TEXT("resume_restores_flight"), !GetWorld()->IsPaused() && !bShowMouseCursor && FVector::Dist(TestLocation, Plane->GetActorLocation()) > 100);
        InjectTestKey(EKeys::R, IE_Pressed);
        Next(); break;
    case 6:
        if (Elapsed < .15) return;
        InjectTestKey(EKeys::R, IE_Released);
        TestCheck(TEXT("reset_key_restores_pose_speed"), Plane->GetActorRotation().IsNearlyZero(.1) && FMath::IsNearlyEqual(Plane->GetSpeedMetresPerSecond(), 100.f, .1f));
        FScreenshotRequest::RequestScreenshot(FPaths::Combine(TestOutputDirectory, TEXT("runtime-flight.png")), true, false);
        Next(); break;
    case 7:
        // Let the requested flight image render before opening the menu.
        if (Elapsed < .25) return;
        InjectTestKey(EKeys::Escape, IE_Pressed);
        Next(); break;
    case 8:
        if (Elapsed < .25) return;
        InjectTestKey(EKeys::Escape, IE_Released);
        InjectTestKey(EKeys::Escape, IE_Pressed);
        Next(); break;
    case 9:
        if (Elapsed < .25) return;
        InjectTestKey(EKeys::Escape, IE_Released);
        TestCheck(TEXT("escape_works_while_paused"), !bMenuOpen && !GetWorld()->IsPaused());
        InjectTestKey(EKeys::Escape, IE_Pressed);
        Next(); break;
    case 10:
        if(Elapsed<.25) return;
        InjectTestKey(EKeys::Escape,IE_Released);
        TestCheck(TEXT("exit_menu_available"),bMenuOpen&&GetWorld()->IsPaused());
        TestFov=GetStudyFov();
        if(auto* H=Cast<APlanesStudyHUD>(GetHUD())) {
            TestCheck(TEXT("fov_plus_hitbox"),H->AutomationClickButton(TEXT("FovPlus")));
            TestCheck(TEXT("fov_changes_actual_projection"),StudyCameras[0]->GetCineCameraComponent()->GetVerticalFieldOfView()>TestFov+4);
            H->AutomationClickButton(TEXT("FovMinus")); H->AutomationClickButton(TEXT("ResumeFlight"));
        }
        bTestFlightFrozen=true; Plane->ResetFlight();
        TestLocation=StudyCameras[0]->GetRootComponent()->GetRelativeLocation();
        InjectTestKey(EKeys::I,IE_Pressed); Next(); break;
    case 11:
        if(Elapsed<.35) return;
        InjectTestKey(EKeys::I,IE_Released);
        TestCheck(TEXT("camera_translation_key"),FVector::Dist(TestLocation,StudyCameras[0]->GetRootComponent()->GetRelativeLocation())>2);
        InjectTestKey(EKeys::Home,IE_Pressed); Next(); break;
    case 12:
        if(Elapsed<.2) return;
        InjectTestKey(EKeys::Home,IE_Released);
        TestCheck(TEXT("home_resets_camera"),FVector::Dist(TestLocation,StudyCameras[0]->GetRootComponent()->GetRelativeLocation())<.01);
        CaptureTestSnapshot(TEXT("camera-cockpit"));
        TestStage=25; TestStageTime=Now; break;
    case 25:
        if (Elapsed < .25) return;
        if (GetWorld()->GetMapName().EndsWith(TEXT("EurofighterCockpitStudy")))
            TestCheck(TEXT("detail_canopy_bow_available"), HasCanopyBow());
        if (HasCanopyBow())
        {
            SetStudyMenuOpen(true);
            TestStage=33; TestStageTime=Now; break;
        }
        InjectTestKey(EKeys::RightMouseButton,IE_Pressed);
        TestStage=13; TestStageTime=Now; break;
    case 33:
        if (Elapsed < .25) return;
        {
            auto* HUD = Cast<APlanesStudyHUD>(GetHUD());
            const bool Clicked = HUD && HUD->AutomationClickButton(TEXT("CanopyBow"));
            TestCheck(TEXT("canopy_bow_menu_clears_pilot_view"), Clicked && bClearCanopyBow && BowUses(true));
            ResumeFlight();
        }
        TestStage=26; TestStageTime=Now; break;
    case 26:
        if (Elapsed < .3) return;
        CaptureTestSnapshot(TEXT("camera-cockpit-clear"));
        Next(); break;
    case 27:
        if (Elapsed < .3) return;
        SelectStudyView(1);
        TestCheck(TEXT("canopy_bow_opaque_outside"), BowUses(false));
        SelectStudyView(0);
        TestCheck(TEXT("canopy_bow_clear_restored_in_pilot_view"), BowUses(true));
        InjectTestKey(EKeys::B, IE_Pressed);
        Next(); break;
    case 28:
        if (Elapsed < .15) return;
        InjectTestKey(EKeys::B, IE_Released);
        TestCheck(TEXT("canopy_bow_key_restores_opaque"), !bClearCanopyBow && BowUses(false));
        InjectTestKey(EKeys::RightMouseButton,IE_Pressed);
        TestStage=13; TestStageTime=Now; break;
    case 13:
        if(Elapsed<.5) return;
        InputKey(FInputKeyEventArgs(GEngine->GameViewport->Viewport,INPUTDEVICEID_NONE,EKeys::MouseX,20.f,.016f,1,FPlatformTime::Cycles64()));
        TestStage=24; TestStageTime=Now; break;
    case 24:
        if(Elapsed<.25) return;
        TestCheck(TEXT("rmb_mouse_look_input"),FMath::Abs(ViewLookOffsets[0].Yaw)>.1f);
        InjectTestKey(EKeys::RightMouseButton,IE_Released);
        ResetStudyView();
        InjectTestKey(EKeys::Two,IE_Pressed);
        TestStage=14; TestStageTime=Now; break;
    case 14:
        if(Elapsed<.5) return;
        InjectTestKey(EKeys::Two,IE_Released);
        TestCheck(TEXT("chase_direct_key"),CurrentView==1&&GetViewTarget()==StudyCameras[1]);
        CaptureTestSnapshot(TEXT("camera-chase")); Next(); break;
    case 15:
        if(Elapsed<.5) return;
        InjectTestKey(EKeys::C,IE_Pressed); Next(); break;
    case 16:
        if(Elapsed<.5) return;
        InjectTestKey(EKeys::C,IE_Released);
        TestCheck(TEXT("cycle_to_canopy"),CurrentView==2&&GetViewTarget()==StudyCameras[2]);
        CaptureTestSnapshot(TEXT("camera-canopy")); Next(); break;
    case 17:
        if(Elapsed<.5) return;
        InjectTestKey(EKeys::One,IE_Pressed); Next(); break;
    case 18:
        if(Elapsed<.3) return;
        InjectTestKey(EKeys::One,IE_Released);
        TestCheck(TEXT("pilot_direct_key"),CurrentView==0);
        SetStudyMenuOpen(true); TestCloudIndex=0; Next(); break;
    case 19:
        if(Elapsed<.3) return;
        if(auto* H=Cast<APlanesStudyHUD>(GetHUD())) {
            const FName N[]={TEXT("CloudClear"),TEXT("CloudScattered"),TEXT("CloudBroken"),TEXT("CloudOvercast")};
            TestCheck(FString::Printf(TEXT("cloud_%d_hitbox"),TestCloudIndex),H->AutomationClickButton(N[TestCloudIndex]));
        }
        TestCheck(FString::Printf(TEXT("cloud_%d_material"),TestCloudIndex),CloudMaterial&&CurrentCloudPreset==TestCloudIndex&&FMath::IsNearlyEqual(CloudMaterial->K2_GetScalarParameterValue(TEXT("Cloud_GlobalDensity")),TestCloudIndex==0?0.f:TestCloudIndex==1?.008f:TestCloudIndex==2?.014f:.022f,.00001f));
        SetStudyMenuOpen(false); Next(); break;
    case 20:
        if(Elapsed<2) return;
        CaptureTestSnapshot(FString::Printf(TEXT("cloud-%d"),TestCloudIndex)); Next(); break;
    case 21:
        if(Elapsed<.4) return;
        SetStudyMenuOpen(true);
        if(++TestCloudIndex<4) { TestStage=19; TestStageTime=Now; } else Next();
        break;
    case 22:
        if(Elapsed<.4) return;
        CaptureTestSnapshot(TEXT("runtime-menu"));
        TestStage=30; TestStageTime=Now; break;
    case 30:
        if (Elapsed < .3) return;
        ResumeFlight();
        Plane->ResetFlight();
        bTestFlightFrozen = false;
        InjectTestKey(EKeys::Gamepad_RightShoulder, IE_Pressed);
        InjectTestKey(EKeys::Gamepad_FaceButton_Bottom, IE_Pressed);
        Next(); break;
    case 31:
        if (Elapsed < .35)
        {
            InjectTestAxis(EKeys::Gamepad_LeftY, .75f);
            InjectTestAxis(EKeys::Gamepad_LeftX, .55f);
            InjectTestAxis(EKeys::Gamepad_RightTriggerAxis, 1.f);
            InjectTestAxis(EKeys::Gamepad_RightX, .8f);
            InjectTestAxis(EKeys::Gamepad_RightY, .8f);
            return;
        }
        TestCheck(TEXT("gamepad_left_stick_pitch_roll"), Plane->GetActorRotation().Pitch > 2 && Plane->GetActorRotation().Roll > 4);
        TestCheck(TEXT("gamepad_right_bumper_yaw"), Plane->GetActorRotation().Yaw > 1);
        TestCheck(TEXT("gamepad_right_trigger_throttle"), Plane->GetSpeedMetresPerSecond() > 104);
        TestCheck(TEXT("gamepad_right_stick_look"), FilteredLookYaw > .05f && FilteredLookPitch > .05f);
        TestCheck(TEXT("gamepad_a_holds_gun"), Plane->IsGunHeld());
        InjectTestKey(EKeys::Gamepad_FaceButton_Bottom, IE_Released);
        InjectTestKey(EKeys::Gamepad_RightShoulder, IE_Released);
        InjectTestKey(EKeys::Gamepad_FaceButton_Top, IE_Pressed);
        InjectTestAxis(EKeys::Gamepad_LeftY, 0);
        InjectTestAxis(EKeys::Gamepad_LeftX, 0);
        InjectTestAxis(EKeys::Gamepad_RightTriggerAxis, 0);
        InjectTestAxis(EKeys::Gamepad_RightX, 0);
        InjectTestAxis(EKeys::Gamepad_RightY, 0);
        Plane->ResetFlight();
        Next(); break;
    case 32:
        if (Elapsed < .3)
        {
            InjectTestAxis(EKeys::Gamepad_LeftTriggerAxis, 1.f);
            return;
        }
        TestCheck(TEXT("gamepad_left_trigger_brake"), Plane->GetSpeedMetresPerSecond() < 96);
        TestCheck(TEXT("gamepad_y_cycles_camera"), CurrentView == 1);
        TestCheck(TEXT("gamepad_a_release_stops_gun"), !Plane->IsGunHeld());
        InjectTestKey(EKeys::Gamepad_FaceButton_Top, IE_Released);
        InjectTestAxis(EKeys::Gamepad_LeftTriggerAxis, 0);
        SetStudyMenuOpen(true);
        TestStage=23; TestStageTime=Now; break;
    case 23:
        if(Elapsed<.4) return;
        TestCheck(TEXT("completed_before_timeout"),true);
        bSelfTest=false;
        {
            auto* H=Cast<APlanesStudyHUD>(GetHUD());
            const bool Clicked=H&&H->AutomationClickButton(TEXT("ExitPrototype"));
            TestCheck(TEXT("exit_hitbox_click"),Clicked); WriteTestReport();
            if(!Clicked) ExitPrototype();
        }
        break;
    }
}

void APlanesStudyHUD::DrawHUD()
{
    Super::DrawHUD();
    if (!Canvas || FString(FCommandLine::Get()).Contains(TEXT("MoviePipelineConfig"))) return;
    auto* PC = Cast<APlanesStudyPlayerController>(GetOwningPlayerController());
    if (!PC) return;
    const float S = FMath::Clamp(Canvas->ClipY / 1000.f, .65f, 1.5f);
    if (!RuntimeHudFont)
    {
        RuntimeHudFont = LoadObject<UFont>(nullptr,TEXT("/Engine/EngineFonts/Roboto.Roboto"));
        UE_LOG(LogTemp,Display,TEXT("PLANES_HUD Font=%s CacheType=%d"),*GetNameSafe(RuntimeHudFont),RuntimeHudFont ? int32(RuntimeHudFont->FontCacheType) : -1);
    }
    if (!RuntimeHudFont) return;
    // Rasterize the TTF at the final requested size; do not magnify SmallFont's
    // pre-baked bitmap atlas at fractional viewport-dependent scales.
    static const TSharedPtr<const FCompositeFont> HudFont = MakeShared<FCompositeFont>(
        FName(TEXT("Regular")), FPaths::EngineContentDir()/TEXT("Slate/Fonts/Roboto-Regular.ttf"),
        EFontHinting::Auto, EFontLoadingPolicy::LazyLoad);
    auto Text = [&](const FString& T, float PX, float PY, float NominalSize, const FLinearColor& Colour)
    {
        const int32 Size = FMath::Max(10, FMath::RoundToInt(NominalSize*S));
        FSlateFontInfo FontInfo(HudFont, Size, TEXT("Regular"));
        // UE5.8 Canvas still gates composite rendering on a backing UFont;
        // without FontObject its HasValidText() rejects every glyph silently.
        FontInfo.FontObject = RuntimeHudFont;
        FCanvasTextItem Item(FVector2D(FMath::RoundToFloat(PX), FMath::RoundToFloat(PY)),
            FText::FromString(T), FontInfo, Colour);
        Item.Scale = FVector2D(1.f,1.f);
        Canvas->DrawItem(Item);
    };
    MenuButtonCentres.Empty();
    if (!PC->IsStudyMenuOpen())
    {
        Text(TEXT("ARROWS PITCH/BANK   Q/E YAW   W/S THROTTLE   R RESET   ESC MENU"),28*S,Canvas->ClipY-60*S,12,FLinearColor(.78f,.86f,.88f,.95f));
        Text(TEXT("C / 1-3 VIEW   HOLD RMB LOOK   I/K J/L U/O MOVE CAMERA   HOME RESET VIEW"),28*S,Canvas->ClipY-35*S,12,FLinearColor(.78f,.86f,.88f,.95f));
        return;
    }
    DrawRect(FLinearColor(0,.006f,.012f,.62f),0,0,Canvas->ClipX,Canvas->ClipY);
    const float X=(Canvas->ClipX-620*S)*.5f, Y=(Canvas->ClipY-650*S)*.5f;
    DrawRect(FLinearColor(.018f,.031f,.043f,.97f),X,Y,620*S,650*S);
    DrawRect(FLinearColor(.7f,.81f,.57f),X,Y,620*S,3*S);
    auto Label=[&](const FString& T,float L,float Top){ Text(T,X+L*S,Y+Top*S,14,FLinearColor(.88f,.94f,.94f)); };
    auto Button=[&](FName Name,const FString& T,float L,float Top,float W,float H,bool Selected=false){
        FVector2D Min(X+L*S,Y+Top*S),Size(W*S,H*S);
        DrawRect(Selected?FLinearColor(.21f,.34f,.30f):FLinearColor(.08f,.13f,.16f),Min.X,Min.Y,Size.X,Size.Y);
        AddHitBox(Min,Size,Name,true,10); MenuButtonCentres.Add(Name,Min+Size*.5f);
        Text(T,Min.X+12*S,Min.Y+13*S,14,FLinearColor(.9f,.95f,.95f));
    };
    Text(TEXT("FLIGHT PAUSED"),X+30*S,Y+28*S,28,FLinearColor(.92f,.96f,.96f));
    Label(TEXT("Flight study / Esc to resume"),30,78);
    Label(TEXT("CAMERA"),30,120);
    Button(TEXT("ViewPilot"),TEXT("COCKPIT"),30,148,175,52,PC->GetStudyViewIndex()==0);
    Button(TEXT("ViewChase"),TEXT("CHASE"),222,148,175,52,PC->GetStudyViewIndex()==1);
    Button(TEXT("ViewMount"),TEXT("CANOPY MOUNT"),414,148,175,52,PC->GetStudyViewIndex()==2);
    Label(FString::Printf(TEXT("VERTICAL FIELD OF VIEW: %.0f degrees"),PC->GetStudyFov()),30,225);
    Button(TEXT("FovMinus"),TEXT("- 5"),30,255,100,48); Button(TEXT("FovPlus"),TEXT("+ 5"),145,255,100,48);
    Label(TEXT("40 - 100 degrees / retains vertical framing on ultrawide"),30,318);
    Label(TEXT("CLOUD COVER"),30,355);
    const FName Names[]={TEXT("CloudClear"),TEXT("CloudScattered"),TEXT("CloudBroken"),TEXT("CloudOvercast")};
    const TCHAR* Titles[]={TEXT("CLEAR"),TEXT("SCATTERED"),TEXT("BROKEN"),TEXT("OVERCAST")};
    for(int32 i=0;i<4;++i) Button(Names[i],Titles[i],30+i*145,382,130,52,PC->GetCloudPresetIndex()==i);
    if (PC->HasCanopyBow())
        Button(TEXT("CanopyBow"), PC->IsCanopyBowClear() ? TEXT("COCKPIT BOW: CLEAR (B)") : TEXT("COCKPIT BOW: OPAQUE (B)"),
            30, 442, 560, 44, PC->IsCanopyBowClear());
    else
        Label(TEXT("Hold RMB to look / I K J L U O move / Home restores view"),30,457);
    Button(TEXT("ResumeFlight"),TEXT("RESUME FLIGHT"),30,496,560,55);
    Button(TEXT("ExitPrototype"),TEXT("EXIT PROTOTYPE"),30,570,560,55);
}

bool APlanesStudyHUD::AutomationClickButton(FName Name)
{
    const FVector2D* Point=MenuButtonCentres.Find(Name);
    if(!Point || !GetHitBoxAtCoordinates(*Point,true)) return false;
    UpdateHitBoxCandidates({*Point});
    return UpdateAndDispatchHitBoxClickEvents(*Point,IE_Pressed);
}
void APlanesStudyHUD::NotifyHitBoxClick(FName Name)
{
    Super::NotifyHitBoxClick(Name);
    auto* PC=Cast<APlanesStudyPlayerController>(GetOwningPlayerController()); if(!PC) return;
    if(Name==TEXT("ResumeFlight")) PC->ResumeFlight();
    else if(Name==TEXT("ExitPrototype")) PC->ExitPrototype();
    else if(Name==TEXT("ViewPilot")) PC->SelectStudyView(0);
    else if(Name==TEXT("ViewChase")) PC->SelectStudyView(1);
    else if(Name==TEXT("ViewMount")) PC->SelectStudyView(2);
    else if(Name==TEXT("FovMinus")) PC->AdjustStudyFov(-5);
    else if(Name==TEXT("FovPlus")) PC->AdjustStudyFov(5);
    else if(Name==TEXT("CloudClear")) PC->SelectCloudPreset(0);
    else if(Name==TEXT("CloudScattered")) PC->SelectCloudPreset(1);
    else if(Name==TEXT("CloudBroken")) PC->SelectCloudPreset(2);
    else if(Name==TEXT("CloudOvercast")) PC->SelectCloudPreset(3);
    else if(Name==TEXT("CanopyBow")) PC->ToggleCanopyBow();
}
APlanesStudyGameMode::APlanesStudyGameMode()
{
    DefaultPawnClass = nullptr; // The saved scene contains the calibrated rig.
    PlayerControllerClass = APlanesStudyPlayerController::StaticClass();
    HUDClass = APlanesStudyHUD::StaticClass();
}





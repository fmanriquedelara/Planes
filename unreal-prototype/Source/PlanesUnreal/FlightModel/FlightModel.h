#pragma once

// Engine-independent flight state. Vectors and quaternions use Godot's
// right-handed coordinates: -X forward, +Y up, +Z left.
namespace PlanesFlight
{
struct Vector
{
    double x = 0, y = 0, z = 0;
};

struct Quaternion
{
    double x = 0, y = 0, z = 0, w = 1;
};

struct Inputs
{
    double pitchUp = 0;
    double rollRight = 0;
    double yawRight = 0;
    double throttle = 0; // Signed command: -1 brake, +1 full engine.
    double pitchGust = 0;
    double rollGust = 0;
};

struct State
{
    Vector positionMetres;
    Quaternion attitude;
    Vector bodyRatesRadiansPerSecond;
    double speedMetresPerSecond = 100;
    double leftWingDeflection = 0;
    double rightWingDeflection = 0;
    double leftWingDeflectionRate = 0;
    double rightWingDeflectionRate = 0;
};

// Advance one integration step in seconds. The caller owns the state, step
// schedule and gust source. Use small steps (Unreal uses 1/120 s).
void Step(State& state, const Inputs& inputs, double seconds);
}

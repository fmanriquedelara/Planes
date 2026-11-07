#include "FlightModel.h"

#include <algorithm>
#include <cmath>

namespace PlanesFlight
{
namespace
{
Quaternion Multiply(const Quaternion& a, const Quaternion& b)
{
    return {
        a.w*b.x + a.x*b.w + a.y*b.z - a.z*b.y,
        a.w*b.y - a.x*b.z + a.y*b.w + a.z*b.x,
        a.w*b.z + a.x*b.y - a.y*b.x + a.z*b.w,
        a.w*b.w - a.x*b.x - a.y*b.y - a.z*b.z
    };
}

void AdvanceWing(double& displacement, double& rate, double target, double dt)
{
    displacement += dt * rate;
    rate += dt * (5 * (target - displacement) - rate) / 0.1;
}
}

void Step(State& state, const Inputs& inputs, double dt)
{
    if (!std::isfinite(dt) || dt <= 0) return;

    const double speed = state.speedMetresPerSecond;
    const double pressure = 0.5 * 1.25 * speed * speed;
    const double pitch = -std::clamp(inputs.pitchUp, -1.0, 1.0);
    const double roll = std::clamp(inputs.rollRight, -1.0, 1.0);
    const double yaw = std::clamp(inputs.yawRight, -1.0, 1.0);
    const double throttle = std::clamp(inputs.throttle, -1.0, 1.0);
    const double liftAero = pressure * 200 * 0.000167 * (pitch + inputs.pitchGust);
    // Plane.gd overwrites its upper clamp with max(FliftAero, lowerLimit).
    const double lift = std::max(liftAero, -0.5 * 1.25 * 110 * 110 * 100 * 0.000167);
    const double rollMoment = pressure * 0.000167 * (roll + inputs.rollGust);

    const Quaternion q = state.attitude;
    const double basisXY = 2 * (q.x*q.y + q.w*q.z);
    const double basisZY = 2 * (q.y*q.z - q.w*q.x);
    constexpr double mass = 100;
    constexpr double weight = mass * 9.81;
    const double yawForce = 30 * yaw + 0.005 * weight * basisZY;
    const double safeSpeed = std::max(speed, 0.01);

    auto& rates = state.bodyRatesRadiansPerSecond;
    rates.x += (-6 * rollMoment - rates.x) * (1 - std::exp(-dt / 0.1));
    rates.y += (-yawForce / safeSpeed - rates.y) * (1 - std::exp(-dt / 0.2));
    rates.z += (lift / safeSpeed - rates.z) * (1 - std::exp(-dt / 0.2));
    state.speedMetresPerSecond += dt * (5000 + 5000 * throttle - pressure * 0.8 + weight * basisXY) / mass;

    AdvanceWing(state.leftWingDeflection, state.leftWingDeflectionRate, (lift / 200 - rollMoment) / 2000, dt);
    AdvanceWing(state.rightWingDeflection, state.rightWingDeflectionRate, (lift / 200 + rollMoment) / 2000, dt);

    // Godot translates along the old attitude using the updated speed.
    const double distance = dt * state.speedMetresPerSecond;
    state.positionMetres.x -= (1 - 2 * (q.y*q.y + q.z*q.z)) * distance;
    state.positionMetres.y -= basisXY * distance;
    state.positionMetres.z -= 2 * (q.x*q.z - q.w*q.y) * distance;

    const double rate = std::sqrt(rates.x*rates.x + rates.y*rates.y + rates.z*rates.z);
    const double angle = rate * dt;
    if (angle > 0.000001)
    {
        const double scale = std::sin(angle / 2) / rate;
        const Quaternion next = Multiply(q, {rates.x*scale, rates.y*scale, rates.z*scale, std::cos(angle / 2)});
        const double norm = std::sqrt(next.x*next.x + next.y*next.y + next.z*next.z + next.w*next.w);
        state.attitude = {next.x / norm, next.y / norm, next.z / norm, next.w / norm};
    }
}
}

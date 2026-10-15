"""BRIDLE screening review v0.5. All quantities are uncalibrated and dimensionless.

Run: python thermal_model.py
Requires numpy, scipy and matplotlib. No hardware-sizing or propulsion prediction.
"""
from pathlib import Path
import csv
import json
import numpy as np
from scipy.integrate import solve_ivp, quad
from scipy.linalg import expm
from scipy.optimize import brentq, minimize_scalar
from scipy.special import gamma, gammainc
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
LIMIT, HEAT_TIME, RESERVE_TIME = 1.5, 3.0, 2.5


def ring(mode="low", main=0.2, reserve=0.0, shared=False,
         horizon=12.0, step=0.02, low=0.02, high=0.40, samples=12001):
    """Reciprocal edge switches: hotter endpoint closes at 1.35, opens at 1.30."""
    state, t, closed = np.ones(6), 0.0, np.zeros(6, dtype=bool)
    chunks, transitions = [], []
    for _ in range(200):
        def rhs(time, y):
            heat = np.ones(6)
            cooling = np.ones(6)
            affected = slice(None) if shared else 0
            heat[affected] = np.exp(-time / HEAT_TIME)
            cooling[affected] = main + reserve * np.exp(-time / RESERVE_TIME)
            k = np.full(6, low if mode == "low" else high)
            if mode == "switch":
                k = np.where(closed, high, low)
            # One flux per undirected edge. Opposite signs conserve internal heat.
            flux = k * (np.roll(y, -1) - y)
            return heat - cooling * y + flux - np.roll(flux, 1)

        events = []
        if mode == "switch":
            for edge in range(6):
                def event(time, y, edge=edge):
                    return max(y[edge], y[(edge + 1) % 6]) - (
                        1.30 if closed[edge] else 1.35)
                event.terminal = True
                event.direction = -1 if closed[edge] else 1
                events.append(event)
        sol = solve_ivp(rhs, (t, horizon), state, dense_output=True,
                        events=events or None, rtol=2e-10, atol=2e-12,
                        max_step=step)
        if not sol.success:
            raise RuntimeError(sol.message)
        chunks.append(sol)
        if sol.t[-1] >= horizon - 1e-10:
            break
        first = next(j for j, hit in enumerate(sol.t_events) if len(hit))
        new = not closed[first]
        for edge in range(6):
            temperature = max(sol.y[edge, -1], sol.y[(edge + 1) % 6, -1])
            threshold = 1.30 if closed[edge] else 1.35
            if abs(temperature - threshold) < 1e-8 and closed[edge] != new:
                closed[edge] = new
        t, state = float(sol.t[-1]), sol.y[:, -1]
        transitions.append(t)
    else:
        raise RuntimeError("Too many switch events")
    time = np.linspace(0, horizon, samples)
    values = np.empty((6, samples))
    for sol in chunks:
        mask = (time >= sol.t[0] - 1e-12) & (time <= sol.t[-1] + 1e-12)
        values[:, mask] = sol.sol(time[mask])
    summary = dict(mode=mode, main=main, reserve=reserve, shared=shared,
                   horizon=horizon, affected_peak=float(values[0].max()),
                   other_peak=float(values[1:].max()),
                   switch_event_times=transitions)
    return time, values, summary


def shared_constant(time, a):
    """Exact solution with constant retained cooling and exponential heat input."""
    time = np.asarray(time)
    if abs(a - 1 / HEAT_TIME) < 1e-10:
        return (1 + time) * np.exp(-a * time)
    return np.exp(-a * time) + (
        np.exp(-time / HEAT_TIME) - np.exp(-a * time)) / (a - 1 / HEAT_TIME)


def shared_exponential(time, b, reserve_time=RESERVE_TIME):
    """Closed form via the unnormalized lower incomplete gamma function."""
    time = np.asarray(time)
    if b == 0:
        return 1 + HEAT_TIME * (1 - np.exp(-time / HEAT_TIME))
    beta, p = b * reserve_time, reserve_time / HEAT_TIME
    z = beta * np.exp(-time / reserve_time)
    return np.exp(z) * (
        np.exp(-beta)
        + reserve_time * gamma(p) / beta**p
        * (gammainc(p, beta) - gammainc(p, z)))


def shared_limit(b, reserve_time=RESERVE_TIME):
    if b == 0:
        return 1 + HEAT_TIME
    beta, p = b * reserve_time, reserve_time / HEAT_TIME
    return float(np.exp(-beta) + reserve_time * gamma(p)
                 * gammainc(p, beta) / beta**p)


def constant_peak(a):
    result = minimize_scalar(lambda t: -shared_constant(t, a),
                             bounds=(0, 100), method="bounded")
    return max(1.0, float(-result.fun), float(shared_constant(100, a)))


def make_results():
    RESULTS.mkdir(exist_ok=True)
    cases = []
    definitions = [
        ("Separated", "low", .2, 0., False),
        ("Joined", "high", .2, 0., False),
        ("Switched interfaces", "switch", .2, 0., False),
        ("Reserve only", "low", .2, .5, False),
        ("Switches and reserve", "switch", .2, .5, False),
        ("Local zero main, reserve only", "low", 0., .5, False),
        ("Local zero main, switches and reserve", "switch", 0., .5, False),
        ("Shared zero main and identical reserves", "switch", 0., .5, True),
    ]
    for label, mode, main, reserve, shared in definitions:
        _, _, row = ring(mode, main, reserve, shared)
        cases.append(dict(label=label, **row))
    sensitivity = []
    for k in [.02, .05, .10, .20, .40, .80]:
        def peak(a):
            return ring("low", a, low=k, samples=6001)[2]["affected_peak"]
        required = brentq(lambda a: peak(a) - LIMIT, 0, 1, xtol=1e-10)
        row = ring("low", required, low=k)[2]
        sensitivity.append(dict(k=k, required=required,
                                other_peak=row["other_peak"]))
    required_shared = brentq(lambda a: constant_peak(a) - LIMIT,
                             .1, 1, xtol=1e-12)
    reserve_all_time = brentq(lambda b: shared_limit(b) - LIMIT, .5, 2,
                              xtol=1e-13)
    reserve_twelve = brentq(
        lambda b: float(shared_exponential(12, b)) - LIMIT, .5, 2,
        xtol=1e-13)
    schedules = []
    for a in [.5, .8, 1.0]:
        duration = brentq(
            lambda t: float(shared_constant(t, a))
            + HEAT_TIME * np.exp(-t / HEAT_TIME) - LIMIT,
            0, 30, xtol=1e-12)
        schedules.append(dict(rate=a, duration=duration,
                              budget=a * duration,
                              temperature_at_off=float(shared_constant(duration, a))))
    lap = 2*np.eye(6)-np.roll(np.eye(6), 1, axis=1)-np.roll(np.eye(6), -1, axis=1)
    calibration = []
    for k in [.02, .05, .10, .20, .40, .80]:
        response = np.linalg.solve(np.eye(6) + k * lap, np.eye(6)[0])
        calibration.append(dict(k=k, neighbor=response[1] / response[0],
                                next_nearest=response[2] / response[0]))

    # Numerical and analytic consistency checks.
    checks = []
    y = np.array([1.8, 1.2, .9, 1.1, 1.5, 1.0])
    k = np.array([.4, .02, .02, .4, .02, .4])
    flux = k * (np.roll(y, -1) - y)
    assert abs(np.sum(flux - np.roll(flux, 1))) < 1e-12
    checks.append("Reciprocal edge fluxes conserve internal heat")
    time, values, _ = ring("switch", 0., .5, shared=True)
    exact = shared_exponential(time, .5)
    assert np.max(np.abs(values - exact)) < 1e-8
    checks.append("Shared switched ring matches incomplete-gamma scalar solution")
    for a in [.2, .5, 1.]:
        time, values, _ = ring("low", a, shared=True)
        assert np.max(np.abs(values[0] - shared_constant(time, a))) < 1e-8
    checks.append("Constant-cooling shared ring matches its elementary solution")
    for a in [.2, 1/3, required_shared, .5, .8]:
        s = 1 / HEAT_TIME
        peak_time = HEAT_TIME - 1 if abs(a-s) < 1e-10 else (
            np.log(a*(1+s-a)/s)/(a-s))
        assert abs(float(shared_constant(peak_time, a)) - constant_peak(a)) < 1e-9
    checks.append("Analytic constant-cooling peak times match independent maximization")
    # Constant-coefficient ring also has an exact augmented matrix propagator.
    cooling = np.r_[.2, np.ones(5)]
    A = np.zeros((8, 8))
    A[:6, :6] = -np.diag(cooling) - .4 * lap
    A[0, 6] = 1
    A[1:6, 7] = 1
    A[6, 6] = -1 / HEAT_TIME
    _, numeric, _ = ring("high", .2)
    exact_end = expm(12 * A) @ np.ones(8)
    assert np.max(np.abs(numeric[:, -1] - exact_end[:6])) < 1e-8
    checks.append("Constant ring matches an augmented matrix exponential")
    for main, reserve in [(.2, 0.), (.2, .5), (0., .5)]:
        coarse = ring("switch", main, reserve)[2]
        fine = ring("switch", main, reserve, step=.005)[2]
        assert abs(coarse["affected_peak"] - fine["affected_peak"]) < 1e-7
    checks.append("Switched peaks reproduce after a fourfold step reduction")
    for schedule in schedules:
        d, a = schedule["duration"], schedule["rate"]
        assert abs(float(shared_constant(d, a))
                   + HEAT_TIME*np.exp(-d/HEAT_TIME) - LIMIT) < 1e-10
        assert constant_peak(a) <= LIMIT
    checks.append("Finite-duration schedules satisfy the exact post-cutoff tail bound")
    # All-time exponential threshold checked by independent quadrature.
    b = reserve_all_time
    beta = b * RESERVE_TIME
    integral = quad(lambda s: np.exp(-s/HEAT_TIME
                                    -beta*np.exp(-s/RESERVE_TIME)),
                    0, np.inf, epsabs=1e-11, epsrel=1e-11)[0]
    assert abs(np.exp(-beta) + integral - LIMIT) < 1e-10
    checks.append("All-time reserve threshold agrees with independent quadrature")
    start = -HEAT_TIME * np.log(1 - (LIMIT-1)/HEAT_TIME)
    result = dict(
        version="0.5", status="dimensionless, uncalibrated screening",
        local_cases=cases, coupling_sensitivity=sensitivity,
        constant_shared_required=required_shared,
        exponential_reserve=dict(
            current_b=.5, current_budget=1.25,
            current_theta12=float(shared_exponential(12, .5)),
            current_theta_infinity=shared_limit(.5),
            required_b_all_time=reserve_all_time,
            required_budget_all_time=reserve_all_time*RESERVE_TIME,
            required_b_only_twelve=reserve_twelve,
            eventual_theta_if_only_twelve=shared_limit(reserve_twelve)),
        ideal_budget=dict(lower_bound=(1+HEAT_TIME-LIMIT)/LIMIT,
                          start=start, peak_rate=np.exp(-start/HEAT_TIME)/LIMIT),
        constant_reserve_schedules=schedules, calibration=calibration,
        checks=checks)
    (RESULTS / "model-results.json").write_text(json.dumps(result, indent=2))
    draw(result)
    return result


def draw(result):
    time = np.linspace(0, 30, 1501)
    b = result["exponential_reserve"]["required_b_all_time"]
    b12 = result["exponential_reserve"]["required_b_only_twelve"]
    plt.rcParams.update({"font.family":"DejaVu Sans", "font.size":10,
                         "axes.spines.top":False, "axes.spines.right":False})
    fig, ax = plt.subplots(figsize=(10, 5.1), constrained_layout=True)
    records = []
    for label, amplitude, color, style in [
        ("Proposed b=0.500; eventual 2.102", .5, "#be633a", "-"),
        ("Sized only to time 12; eventual 1.529", b12, "#668da4", "--"),
        ("All-time threshold b=0.844140; eventual 1.500", b, "#207668", "-"),
    ]:
        values = shared_exponential(time, amplitude)
        ax.plot(time, values, label=label, color=color, linestyle=style, linewidth=2.2)
        records.extend(dict(case=label, tau=float(t), theta=float(y))
                       for t, y in zip(time, values))
    ax.axhline(LIMIT, color="#852d3c", linestyle=":", linewidth=1.8, label="Illustrative limit 1.50")
    ax.axvline(12, color="#88939c", linestyle=":", linewidth=1)
    ax.set(xlabel="Normalized time", ylabel="Normalized excess temperature",
           title="Shared main-cooling loss: a finite test window can miss later heating")
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    ax.grid(alpha=.15)
    fig.savefig(RESULTS / "BRIDLE-Reserve-Comparison.png", dpi=180)
    plt.close(fig)
    with (RESULTS / "reserve-curves.csv").open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=["case","tau","theta"])
        writer.writeheader()
        writer.writerows(records)


if __name__ == "__main__":
    data = make_results()
    print(json.dumps({"checks":data["checks"],
                      "exponential_reserve":data["exponential_reserve"]}, indent=2))

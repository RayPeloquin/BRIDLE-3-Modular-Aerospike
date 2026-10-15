# BRIDLE | Reviewed thermal mathematics and requirements | v0.5

14 OCT 2026, America/New_York. Ray Peloquin + UI — Unique Intelligence.

Concept study. Uncalibrated, dimensionless screening. Numerical consistency has
been checked; hardware safety and engine performance have not been demonstrated.

## 1. Scope and architecture

BRIDLE-2 proposes replaceable combustion-cell/expansion-tile modules on a separately
cooled frame. Reduced solid heat sharing can lower neighbor heating and raise the
affected module's peak in the specified local cooling fault. Replaceability and
fault containment remain proposed benefits, rather than demonstrated outcomes.

BRIDLE-3 adds candidate temperature-dependent thermal contacts and local reserve
cooling. The calculations below distinguish a local fault with healthy neighbors
from an identical fault on all six modules. Plume heating, solid conduction,
coolant dynamics and frame mechanics are distinct couplings.

## 2. Dimensional balance and normalization

A linearized lumped balance is

$$
C_i\dot T_i=Q_i-\sum_{r\in\{A,B\}}H_{ir}(T_i-T_{c,ir})
                 +\sum_jK_{ij}(T_j-T_i).
$$

The left side is the rate of stored-energy change, in watts. C has units J/K;
H and K have units W/K; Q has units W. This balance omits unrepresented radiation,
fluid thermal storage, detailed wall gradients and additional frame states.
Heat already included in a resolved wall capacity must not also be counted as an
independent residual source.

For the screening model choose equal capacity C, nominal total cooling H0, fixed
common coolant temperature Tc, and reference temperature rise dTref:

$$
\theta_i=\frac{T_i-T_c}{\Delta T_{\rm ref}},\quad
\tau=\frac{H_0t}{C},\quad
a_i=\frac{H_i}{H_0},\quad k_{ij}=\frac{K_{ij}}{H_0},\quad
q_i=\frac{Q_i}{H_0\Delta T_{\rm ref}}.
$$

The physical time unit is C/H0. A normalized conductance fraction is not
automatically a coolant-flow fraction, and a normalized temperature is not a
temperature in degrees.

The reciprocal network is

$$
\dot\theta_i=q_i-a_i\theta_i+\sum_jk_{ij}(\theta_j-\theta_i),
\qquad k_{ij}=k_{ji}\ge0.
$$

For a uniform ring, this gives the usual k times the discrete Laplacian.
Reciprocity is essential when contacts switch: each physical edge has one shared
conductance. Independent row-wise multipliers could create or destroy modeled
energy. Internal conduction cancels in the total balance:

$$
\frac{d}{d\tau}\sum_i\theta_i=\sum_iq_i-\sum_i a_i\theta_i.
$$

Initial temperatures are all 1. In a local shutdown q0=exp(-tau/3), while the five
healthy neighbors retain q=a=1. The heat tail is an assumed incoming load.
With a0=0.20 and no reserve, the initial slope is exactly 0.80.

## 3. Verified numerical cases

The reference uses adaptive solve_ivp integration, rtol=2e-10, atol=2e-12 and
maximum step 0.02, with explicit threshold events. A step reduction to 0.005
reproduces the switched peaks. The calculation window here is 0 <= tau <= 12.

For switched edges, the hotter endpoint closes at 1.35 and opens at 1.30.
Low/high conductances are 0.02/0.40. Response is instantaneous; delay, switching
energy, contact force and mechanical dynamics are omitted. The proposed reserve
adds b exp(-tau/2.5), with b=0.5. Its tail is not truncated at tau=6.

The first five rows retain 20% main cooling on the affected module.

| Configuration | Module 0 peak | Highest other-module peak |
|---|---:|---:|
| Separated | 1.852 | 1.015 |
| Joined | 1.453 | 1.097 |
| Switched interfaces | 1.474 | 1.119 |
| Reserve only | 1.205 | 1.003 |
| Switches and reserve | 1.205 | 1.003 |
| Local zero main, reserve only | 1.831 | 1.016 |
| Local zero main, switches and reserve | 1.350 | 1.091 |
| Shared zero main and identical reserves | 2.069 | 2.069 |

In the shared row, every module shuts down and loses main cooling identically;
all six receive identical reserves. The highest-other value equals module 0.

The reserve-only local zero-main case fails, while the ideal switched zero-main
local case passes by using five healthy neighbors. Therefore the statement
"reserve helps only on top of main cooling" is too broad. Neither local case
establishes shared-loss survival.

With 20% main cooling plus the reserve, no contact reaches its closing threshold:
the reserve accounts for the temperature reduction in that case.

### Cooling threshold as a function of fixed coupling

The threshold is the smallest a0 that keeps module 0 at or below 1.50 over
0 <= tau <= 12, with five healthy neighbors and no reserve.

| k | Required retained conductance | Other-module peak at that threshold |
|---:|---:|---:|
| 0.02 | 34.2824% | 1.008 |
| 0.05 | 32.6841% | 1.020 |
| 0.10 | 30.0957% | 1.037 |
| 0.20 | 25.1734% | 1.066 |
| 0.40 | 16.1847% | 1.108 |
| 0.80 | 0.7988% | 1.164 |

The neighbor column is evaluated at the required a0 in each row. It must not be
compared as if all rows retained 20% cooling. Display rounding is descriptive;
a requirement must not round a minimum downward or omit uncertainty margin.

## 4. Shared shutdown with constant surviving cooling

Symmetry reduces all six nodes to

$$
\dot\theta=e^{-\tau/\lambda}-a\theta,\qquad\theta(0)=1,\quad\lambda=3.
$$

For a not equal to 1/lambda, the elementary solution is

$$
\theta(\tau)=e^{-a\tau}+
\frac{e^{-\tau/\lambda}-e^{-a\tau}}{a-1/\lambda}.
$$

At a=1/lambda the solution is (1+tau) exp(-tau/lambda).
For 0<a<1, put s=1/lambda. The peak time is

$$
\tau_p=\frac{\log[a(1+s-a)/s]}{a-s};
$$

its continuous limit at a=s is lambda-1=2. The constant-cooling threshold for
the illustrative 1.50 limit is a=0.353680812462, or about 35.3681%.
A=0.5 gives peak 1.280; a=0.2 gives 1.906524; a=0.1 gives 2.416269.
These cases include immediate identical shutdown and the assigned heat tail.

With two additive, independently supplied circuits, a nominal A share p and
B share 1-p meet this particular one-source-loss screening case only when

$$
0.3536808125\ \lesssim p\lesssim\ 0.6463191875.
$$

This is a conductance-share condition under the model. It is not proof of supply
independence or a 35-65 flow-split rule. Shared tanks, power, valves, controllers,
frame cooling and spatial coverage need separate fault analysis.

If all modules instead keep the same constant heat qbar, the equilibrium is
qbar/a. The temperature settles above the limit when qbar/a>1.50. Derating can
meet the simplified constant-input condition qbar<=1.50a; shutdown of every
module after every single cooling alarm is not a theorem of this model.
Real decisions must include heat history, shutdown tails and actuation delay.

## 5. Exact shared-loss exponential-reserve solution

For zero main cooling, identical reserves and identical shutdowns,

$$
\dot\theta+b e^{-\tau/r}\theta=e^{-\tau/\lambda},
\quad \theta(0)=1,\quad r=2.5,\quad\lambda=3.
$$

Every solid coupling term cancels, including switched ones. With
beta=br and p=r/lambda, an integrating factor is

$$
\mu(\tau)=\exp[-\beta e^{-\tau/r}].
$$

Writing gamma(p,z) for the unnormalized lower incomplete gamma function gives
the exact closed form

$$
\theta(\tau)=e^{\beta e^{-\tau/r}}\left[
e^{-\beta}+r\beta^{-p}
\{\gamma(p,\beta)-\gamma(p,\beta e^{-\tau/r})\}\right].
$$

Consequently,

$$
\theta_\infty=e^{-\beta}+r\beta^{-p}\gamma(p,\beta).
$$

For the proposed b=0.5, theta(12)=2.068875295 and
theta_infinity=2.102392329. At tau=2.5, incoming heat is exp(-5/6)=0.434598
of its initial value. The reserve time constant is an e-folding time; it is not
an exhaustion time, and the exponential reserve never becomes exactly zero.

There is an all-time statement here. At any stationary point, differentiating
the ODE gives theta''=q(1/r-1/lambda)>0 because r<lambda. Thus an interior
stationary point can only be a minimum. The global maximum is the larger of
the initial value 1 and theta_infinity.

Solving theta_infinity=1.50 therefore gives the all-time reserve-shape threshold

$$
b_{\rm required}=0.844139974595,\qquad I_\infty=br=2.110349936487.
$$

Sizing only to theta(12)=1.50 instead gives b=0.822024078441. That trajectory eventually
reaches 1.529371196 and violates the same limit. This is why a finite horizon needs
a justified terminal heat-tail condition.

These coefficients describe the unchanged normalized model; they are not vessel
sizes, pressure settings or experimentally justified design margins.

## 6. Finite-budget screening: what can be proved

Define the control budget I=integral a(tau) d tau. It has normalized
conductance-times-time units. For zero main cooling, no other heat sink,
theta(0)=1, total incoming heat lambda=3, and theta never above L=1.50:

$$
\int_0^\infty a\theta\,d\tau=1+3-\theta_\infty
\ge2.5,\qquad
\int_0^\infty a\theta\,d\tau\le1.50I.
$$

Therefore

$$
I\ge\frac{2.5}{1.50}=\frac53.
$$

The proposed exponential budget I=1.25 is insufficient under those fixed
conditions, even if its time profile is reshaped. Additional capacity, another
heat sink or changed heat input changes the problem and its bound.

An ideal schedule attains this mathematical bound: leave reserve off until
tau_s=-3 log(5/6)=0.546965, then hold at the limit with a=q/1.50. Its peak rate
is 5/9 and its integrated budget is 5/3. The rate has an infinite-duration tail;
there is no uncertainty or actuation margin.

For a constant reserve rate a started at shutdown and cut off at D, the exact
future condition is

$$
\max_{0\le\tau\le D}\theta(\tau)\le L,\qquad
\theta(D)+3e^{-D/3}\le L.
$$

The second term includes all heat arriving after cutoff, with no subsequent
cooling. Solving gives:

| Constant reserve rate | Required duration D | Budget I=aD |
|---:|---:|---:|
| 0.5 | 4.453861 | 2.226931 |
| 0.8 | 3.567557 | 2.854046 |
| 1.0 | 3.257601 | 3.257601 |

These reproduce the added schedule calculations. "Faster is less efficient"
applies to this particular start-immediately constant-rate family, not every
possible cooling strategy.

I is not coolant mass or liters. Only an independently established proportional
relation between effective conductance and delivered mass flow would permit
conversion through a reference mass flow and physical time scale. Equal
heat absorption per kilogram by itself does not establish that relation.

A physical model must track at least coolant inventory, pressure, temperature,
valve delivery, heat-transfer behavior, pressure drop and depletion. The
quasi-steady coolant enthalpy balance Qdot≈mdot(hout-hin) also needs fluid-storage
terms during fast transients.

## 7. Constant-ring analytic structure and calibration

For fixed conductances the ring is a linear forced system. Let
M=diag(a)+Lk, with Lk the conductance Laplacian, c=(0,1,1,1,1,1)^T and e0 the
first coordinate vector. Then

$$
\dot{\boldsymbol\theta}=-M\boldsymbol\theta+c+e_0z,\quad
\dot z=-z/3,\quad z(0)=1.
$$

Appending z and a constant state gives a constant 8x8 matrix and an exact matrix
exponential propagator. A peak or cooling threshold can still need a numerical
root search; the dynamics are not limited to time-stepping.

The system is cooperative: increasing a0 at fixed k and fixed nonnegative heat
cannot increase any node temperature. The derivative w.r.t. a0 obeys
p'=-Mp-e0 theta0, p(0)=0, so p is componentwise nonpositive. This supports the
one-parameter cooling-threshold search.

For an ideal uniform ring with nominal cooling and heat applied only to node 0,
the steady temperature rise is proportional to

$$
(I+kL_{\rm ring})^{-1}e_0.
$$

The verified temperature-rise ratios are:

| Uniform k | Neighbor / heated | Next-nearest / heated |
|---:|---:|---:|
| 0.02 | 0.019238 | 0.000370 |
| 0.05 | 0.045549 | 0.002079 |
| 0.10 | 0.083924 | 0.007092 |
| 0.20 | 0.145963 | 0.021739 |
| 0.40 | 0.235105 | 0.057971 |
| 0.80 | 0.348379 | 0.132231 |

Ratios are temperature rises above the common coolant reference, not absolute
temperature ratios. This lookup identifies a single uniform k under its
assumptions. It does not identify every unequal interface from one ratio.
For a nonuniform network, use multiple known heat inputs and all relevant
temperatures to fit

$$
P_i^{(\ell)}=H_i\Delta T_i^{(\ell)}
 +\sum_jK_{ij}(\Delta T_i^{(\ell)}-\Delta T_j^{(\ell)}),
$$

with reciprocal, nonnegative K and sufficient independent data for
identifiability. Include frame temperatures and unequal coolant temperatures
when present. Transient tests are needed to estimate heat capacities C.

## 8. Corrected requirements candidates

| ID | Carry-forward condition |
|---|---|
| T1 | State the fault, surviving local conductance, shutdown timing, heat tail and uncertainty before assigning a screening pass. |
| T2 | For the stated local k=0.02 case, use the computed threshold 0.3428242228; do not round it down to a 34% requirement. Add justified margins after calibration. |
| T3 | For identical shared shutdown with constant surviving cooling, the model threshold is 0.3536808125. Surviving sources must remain available under the stated fault. |
| T4 | Choose derating/shutdown and retained cooling from a validated thermal trajectory; apply an engine-wide response when the shared fault requires it. |
| T5 | Identify C, H and interface/frame K in physical units, then derive k=K/H0. Check identifiability and repeatability. |
| T6 | Cover the predicted peak and remaining heat tail, or establish a valid terminal condition. A horizon of 12 is not automatically sufficient. |
| T7 | Evaluate local, asymmetric multi-module and symmetric shared faults, plus switch delay and stuck states. |
| T8 | Size a finite-inventory coolant system from its delivery and energy balances. Keep prescribed-curve and conductance-budget results labeled as screening. |
| T9 | Establish supply independence and local coverage. The 35.3681%-64.6319% split is conditional on the additive constant-conductance model. |
| T10 | Compare mass, stored energy, coolant inventory and pump resources consistently before claiming an enlarged admissible set. |

## 9. Render and source-report corrections

- Put revision/date on figures. Show ports as unassigned until a supply diagram
  defines their functions; four unlabeled fittings alone prove no port-count rule.
- Label the module/frame interface and unresolved thermal growth/compliance.
- Check six-module consistency across views. A shared frame is also a possible
  common failure path; its cooling independence remains unspecified.
- State 34.3% versus 16.2% as illustrative model thresholds rather than hardware
  requirements. Do not round minimums downward in a specification.
- Correct the switched-curve legend from about 1.38 to about 1.47.
- Keep mechanism precedents separate from proposed application and validation.
  The 600 C switch setting, 0.3-0.5 L bottle, channel stand-off, pressures,
  real-time durations and seam-slot dimensions remain unsized.
- Film cooling does not guarantee seal protection. Channel roughness can alter
  heat transfer and pressure drop; it does not guarantee improvement at fixed
  pump power. A heat-pipe frame needs a sink and has operating limits.
- Do not claim no cascade, fault containment, full-set envelope inclusion,
  equal-mass advantage, 2% Isp penalty, or tenfold validation simplification.
- The supplied HTML used a logistic switch and a reserve cut off at tau=6 while
  quoting hysteretic, untruncated-curve results. These are different models.
  The revised explorer explicitly implements the reviewed hysteretic model.
- The supplied HTML was a static engineering report, not a live ODE solver.
  Its NASA/TM identifier, hardware sizing and general zero-main-cooling claims
  have been removed from the revised independent-study explorer.

## 10. Candidate admissible command set

$$
\mathcal U(x)=\{u:T_{i,\max}^{\rm pred}(s\mid x,u,f)+U_i(s)
\le T_{i,\lim}\quad \forall i,f\in\mathcal F,0\le s\le H\}.
$$

This is a proposed constraint, not a computed hardware envelope. It also needs
initial-state consistency, actuation limits, a valid terminal heat-tail
condition, justified uncertainty bounds and a defined fault set. Structural,
flow and mission constraints must be added. One improved trajectory does not
prove set inclusion between different architectures.

## 11. Primary-source context

These sources support mechanism classes and modeling needs, not this design:

1. NASA NTRS 20180003643, Passive Thermal Management Systems Employing Shape
   Memory Alloys: https://ntrs.nasa.gov/citations/20180003643
2. NASA NTRS 20020014292, Investigation of Capillary Limit in a Loop Heat Pipe:
   https://ntrs.nasa.gov/citations/20020014292
3. NASA NTRS 20250009398, Thin-Wall Internal Microchannels and Surface
   Enhancements for Rocket Nozzles using Laser Powder Directed Energy Deposition:
   https://ntrs.nasa.gov/citations/20250009398
4. NASA NTRS 19960029261, CFD Analysis of Modular Thrusters Performance:
   https://ntrs.nasa.gov/citations/19960029261

## 12. Reproduction and verification

Run from this package:

    python thermal_model.py
    python build_review.py

The JSON results, reserve-trajectory CSV and standalone PNG accompany the code.
The offline HTML computes its displayed trajectories and exports a selected CSV.
It requires no remote scripts or network access.

Verification completed:

- Reciprocal edge fluxes conserve internal heat.
- Shared switched ring matches incomplete-gamma scalar solution.
- Constant-cooling shared ring matches its elementary solution.
- Analytic constant-cooling peak times match independent maximization.
- Constant ring matches an augmented matrix exponential.
- Switched peaks reproduce after a fourfold step reduction.
- Finite-duration schedules satisfy the exact post-cutoff tail bound.
- All-time reserve threshold agrees with independent quadrature.

The actual HTML JavaScript has also been checked against all eight adaptive
Python cases, including the ideal switched trajectories, within 0.0005 in peak
temperature. Preset, range, switch, CSV-export and late-failure-warning behavior
passed a minimal DOM harness. Full browser layout, pointer interaction and
rendering could not be checked in this environment. The optional browser QA
script is included for an environment with Playwright and Chromium available.

The original unattached scratchpad/ring2.py, ring3.py and ring4.py reruns were
not used as evidence. This package supplies the actual checked reference code.

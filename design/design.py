import numpy as np, control as ct, sympy as sp
from functools import reduce


def design_lead_cancel(
    *, sys, csi=None, ts=None, pole=None, overshoot=None, verbose=False
):
    if csi != None and ts != None:
        omega_n = 4 / (ts * csi)
        omega_d = omega_n * np.sqrt(1 - csi**2)
        dom_s = -csi * omega_n + 1j * omega_d
    elif pole != None:
        dom_s = pole
    elif overshoot != None and ts != None:
        csi = -np.log(overshoot) / np.sqrt(np.pi**2 + np.log(overshoot) ** 2)
        omega_n = 4 / (ts * csi)
        omega_d = omega_n * np.sqrt(1 - csi**2)
        dom_s = -csi * omega_n + 1j * omega_d
    else:
        raise Exception(ValueError)
    if verbose:
        print(f"Polo dominante escolhido: {dom_s:.2f}")
    zc = np.sort(sys.poles()[np.abs(sys.poles()) > 10e-5])[
        0
    ]  # zero = polo mais próximo da origem sem ser 0
    current_angle = 0
    for p in sys.poles()[sys.poles() != zc]:
        current_angle += np.angle(dom_s - p)
    for z in sys.zeros():
        current_angle += np.angle(dom_s - z)

    pole_angle = np.pi - current_angle
    if pole_angle < np.pi / 2:  # polo do compensador à esquerda do polo dominante
        pc = dom_s.real - dom_s.imag / np.tan(pole_angle)
    else:  # polo do compensador à direita do compensador
        pc = dom_s.real + dom_s.imag / np.tan(pole_angle)
    gc = ct.tf([1, -zc], [1, -pc])
    k = 1 / np.abs((gc * sys)(dom_s))
    return k * gc


def design_lead_bissect(
    *, sys, csi=None, ts=None, pole=None, overshoot=None, verbose=False
) -> tuple[ct.TransferFunction, ct.TransferFunction]:
    if csi != None and ts != None:
        omega_n = 4 / (ts * csi)
        omega_d = omega_n * np.sqrt(1 - csi**2)
        dom_s = -csi * omega_n + 1j * omega_d
    elif pole != None:
        dom_s = pole
    elif overshoot != None and ts != None:
        csi = -np.log(overshoot) / np.sqrt(np.pi**2 + np.log(overshoot) ** 2)
        omega_n = 4 / (ts * csi)
        omega_d = omega_n * np.sqrt(1 - csi**2)
        dom_s = -csi * omega_n + 1j * omega_d
    else:
        raise Exception(ValueError)
    if verbose:
        print(f"Polo dominante escolhido: {dom_s:.2f}")
    current_angle = 0
    for p in sys.poles():
        current_angle += np.angle(dom_s - p)

    for z in sys.zeros():
        current_angle += np.angle(dom_s - z)

    current_angle %= 2 * np.pi

    # resolvendo para zc e pc
    phi = np.abs(np.pi - current_angle)
    alpha = np.angle(dom_s) - np.pi / 2
    beta = np.pi / 2 - alpha
    gamma = np.pi - beta
    theta = np.pi - beta - (gamma + phi) / 2
    eta = np.pi - beta - (gamma - phi) / 2
    pc = -np.abs(dom_s) * np.sin((gamma + phi) / 2) / (np.sin(theta))
    zc = -np.abs(dom_s) * np.sin((gamma - phi) / 2) / (np.sin(eta))

    gc = ct.tf([1, -zc], [1, -pc])
    k = 1 / np.abs((gc * sys)(dom_s))

    return k * gc


def lead_lag(
    *,
    sys: ct.TransferFunction,
    csi: float = None,
    ts: float = None,
    pole: float | complex = None,
    overshoot: float = None,
    err_v: float = None,
) -> ct.TransferFunction:
    if csi != None and ts != None:
        omega_n = 4 / (ts * csi)
        omega_d = omega_n * np.sqrt(1 - csi**2)
        p_dom = -csi * omega_n + 1j * omega_d
    elif pole != None:
        p_dom = pole
    elif overshoot != None and ts != None:
        csi = -np.log(overshoot) / np.sqrt(np.pi**2 + np.log(overshoot) ** 2)
        omega_n = 4 / (ts * csi)
        omega_d = omega_n * np.sqrt(1 - csi**2)
        p_dom = -csi * omega_n + 1j * omega_d
    else:
        raise Exception(ValueError)

    if err_v == None:
        Kv = 80
    else:
        Kv = 1 / err_v

    # Lead compensator zero cancels slowest plant pole
    z_lead = sorted(
        [pole for pole in sys.poles() if pole != 0], key=lambda x: np.abs(x)
    )[-1]

    # Calculate current angle and reduces it to first rotation
    lead_zero = ct.tf([1, -z_lead], 1)
    curr_angle = np.angle((sys * lead_zero)(p_dom))
    curr_angle %= 2 * np.pi

    # Calculate lead compensator pole such that angle(sys*lead) evaluated at p_dom = 180°
    p_lead = p_dom.imag / (np.tan(np.pi - curr_angle)) + p_dom.real
    lead_zero_and_pole = ct.tf([1, -z_lead], [1, -p_lead])

    # Calculate Kc such that abs(sys*lead) evaluated at p_dom = 1
    Kc = 1 / np.abs((lead_zero_and_pole * sys)(p_dom))
    lead = Kc * lead_zero_and_pole

    gamma = p_lead / z_lead

    # Solve for beta in Kv = lim_{s->0}[s*Kc*beta/gamma*sys]
    beta = ct.minreal(Kv / (Kc / gamma * ct.tf([1, 0], 1) * sys), verbose=False)(0).real

    # Set tolerance values for angle and absolute value changes when adding lag compensator
    angle_tol = 2
    abs_tol = 0.05

    t2_range = np.linspace(1, 30, 100)

    for T2 in t2_range:
        lag = ct.tf([1, 1 / T2], [1, 1 / beta * T2])
        angle = np.angle(lag(p_dom), deg=True)
        abs_v = np.abs(lag(p_dom))
        if abs(1 - abs_v) <= abs_tol and abs(angle) <= angle_tol:
            break

    return lead * lag


def design_pid_computational(
    *,
    sys: ct.TransferFunction,
    ts: float,
    overshoot: float,
    discrete: bool = False,
    T: float = None,
    k_range: tuple = (1.5, 10),
    k_step: float = 0.2,
    a_range: tuple = (0.5, 2.5),
    a_step: float = 0.1,
    method: str = "bilinear",
) -> ct.TransferFunction:

    if discrete and T == None:
        raise Exception(ValueError)

    k_vals = np.arange(k_range[0], k_range[1] + k_step, k_step)
    a_vals = np.arange(a_range[0], a_range[1] + a_step, a_step)

    for k in k_vals:
        for a in a_vals:
            gc = k * ct.tf([1, 2 * a, a**2], [1, 0])
            stats = ct.step_info(ct.feedback(gc * sys))
            if stats["Overshoot"] / 100 <= overshoot and stats["SettlingTime"] <= ts:
                if not discrete:
                    return gc
                kp = 2 * k * a
                ki = k * a**2
                kd = k
                if method == "bilinear":
                    # bilinear transform -> s = 2/T*(z-1)/(z+1)
                    return ct.tf(
                        [
                            kp + ki * T / 2 + 2 * kd / T,
                            ki * T - 4 * kd / T,
                            -kp + ki * T / 2 + 2 * kd / T,
                        ],
                        [1, 0, -1],
                        T,
                    )
                elif method == "forward":
                    # forward difference euler's method -> s = (z-1)/T
                    return kp + ct.tf([kd, -kd], [T], T) + ct.tf(ki * T, [1, -1], T)
                elif method == "backward":
                    # backawrd difference approximation -> s = (z-1)/(zT)
                    return (
                        kp
                        + ct.tf([ki * T, 0], [1, -1], T)
                        + kd * ct.tf([1, -1], [T, 0], T)
                    )

    return None


def pid_root_locus(
    *,
    sys: ct.TransferFunction,
    csi: float = None,
    ts: float = None,
    pole: float | complex = None,
    overshoot: float = None,
) -> ct.TransferFunction:
    if csi != None and ts != None:
        omega_n = 4 / (ts * csi)
        omega_d = omega_n * np.sqrt(1 - csi**2)
        p_dom = -csi * omega_n + 1j * omega_d
    elif pole != None:
        p_dom = pole
    elif overshoot != None and ts != None:
        csi = -np.log(overshoot) / np.sqrt(np.pi**2 + np.log(overshoot) ** 2)
        omega_n = 4 / (ts * csi)
        omega_d = omega_n * np.sqrt(1 - csi**2)
        p_dom = -csi * omega_n + 1j * omega_d
    else:
        raise Exception(ValueError)

    # First PID zero is set to value where it does not affect response too much
    z1 = -1
    # Calculate current angle (180° is needed for the dominant pole to lie on system's root locus)
    zero_and_integrator = ct.tf([1, -z1], [1, 0])
    curr_angle = np.angle((sys * zero_and_integrator)(p_dom))

    # Second PID zero is obtained from angular condition -> angle(s+a) = 180°-current_angle
    z2 = -(p_dom.imag / (np.tan(np.pi - curr_angle)) - p_dom.real)

    # With both PID zeros determined, calculate gain K with absolute value condition abs(sys*pid) = 1 (evaluated at p_dom)
    zeros_and_integrator = ct.tf(np.convolve([1, -z1], [1, -z2]), [1, 0])
    K = 1 / np.abs((zeros_and_integrator * sys)(p_dom))

    return zeros_and_integrator * K


def two_dof_pid(
    *,
    sys: ct.TransferFunction,
    csi: float = None,
    ts: float = None,
    pole: float | complex = None,
    overshoot: float = None,
) -> tuple[ct.TransferFunction, ct.TransferFunction]:
    if csi != None and ts != None:
        omega_n = 4 / (ts * csi)
        omega_d = omega_n * np.sqrt(1 - csi**2)
        p1 = -csi * omega_n + 1j * omega_d
        p2 = -csi * omega_n - 1j * omega_d
    elif pole != None:
        p1 = pole
        p2 = p1.real - p1.imag
    elif overshoot != None and ts != None:
        csi = -np.log(overshoot) / np.sqrt(np.pi**2 + np.log(overshoot) ** 2)
        omega_n = 4 / (ts * csi)
        omega_d = omega_n * np.sqrt(1 - csi**2)
        p1 = -csi * omega_n + 1j * omega_d
        p2 = -csi * omega_n - 1j * omega_d
    else:
        raise Exception(ValueError)

    # Define symbols and convert TransferFunction object into sympy expression
    s, alpha, beta, K, gc1 = sp.symbols("s alpha beta K G_{C1}")
    gp_num = sys.num[0][0]
    gp_den = sys.den[0][0]
    gp = sp.Poly(gp_num, s) / sp.Poly(gp_den, s)

    # Define closed loop poles
    poles = (s - p1) * (s - p2)

    # (non dominant poles are allocated at 5*i*Re{p1} so as to not impact response too much)
    for i in range(1, len(gp_den) - 1):
        pi = 5 * i * p1.real
        poles = poles * (s - pi)
    poles = poles.expand()

    gc = K * (s + alpha) * (s + beta) / s

    # Create Output/Disturbance transfer function
    y_d = (gp / (1 + gp * gc)).simplify()
    den = sp.collect(sp.denom(y_d).expand(), s)

    # Equate desired characteristic equation coefficients and solve for K, alpha and beta
    eqs = []
    for t1, t2 in zip(
        sorted(den.args, key=lambda x: sp.degree(x, s)),
        sorted(poles.args, key=lambda x: sp.degree(x, s)),
    ):
        eqs.append(sp.Eq(t1, t2))

    sol = sp.solve(eqs, (K, alpha, beta))[0]

    # Substitute found values
    gc_solved = gc.subs({K: sol[0], alpha: sol[1], beta: sol[2]})
    y_d_solved = y_d.subs({K: sol[0], alpha: sol[1], beta: sol[2]})

    # Create Output/Reference transfer function -> Y/R = G_C1*Y/D
    y_r = (gc1 * y_d_solved).expand()

    # Numerator of Y/R must be equal to last three terms of denominator to eliminate steady state error for step, ramp and parabola
    num_target = reduce(
        lambda acc, curr: acc + curr,
        (term for term in sp.denom(y_r).args if sp.degree(term) < 3),
        0,
    )
    curr_num = sp.numer(y_r)

    # Solve for G_C1
    gc1_solved = sp.solve(sp.Eq(curr_num, num_target), gc1)[0].factor()

    # Solve for G_C2
    gc2_solved = (gc_solved - gc1_solved).simplify()

    # Convert sympy expressions back into control TransferFunction objects
    gc1_num = [float(a) for a in sp.Poly(sp.numer(gc1_solved), s).all_coeffs()]
    gc1_den = [float(a) for a in sp.Poly(sp.denom(gc1_solved), s).all_coeffs()]
    gc1_tf = ct.tf(gc1_num, gc1_den)

    gc2_num = [float(a) for a in sp.Poly(sp.numer(gc2_solved), s).all_coeffs()]
    gc2_den = [float(a) for a in sp.Poly(sp.denom(gc2_solved), s).all_coeffs()]
    gc2_tf = ct.tf(gc2_num, gc2_den)

    return gc1_tf, gc2_tf

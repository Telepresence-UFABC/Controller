import numpy as np, control as ct, matplotlib.pyplot as plt
from typing import Iterable, Any
from json import dump


def create_servo(k: float, tau: float) -> ct.TransferFunction:
    return k * ct.tf(1, [1, 0]) * ct.tf(1, [tau, 1])


def plot_response(
    sys: ct.TransferFunction,
    t: Iterable[float],
    u: Iterable[float],
    display: bool = True,
) -> Any:
    response = ct.forced_response(ct.feedback(sys), t, u)
    if display:
        plt.grid()
        plt.plot(response.time, response.outputs)
        plt.show()
    return response


def compare_step(
    sys: Iterable[ct.TransferFunction],
    time: Iterable[float],
    labels: Iterable[str],
    y_min: float | None = None,
    y_max: float | None = None,
) -> list[Any]:
    COLORS = ("b", "r", "g", "c", "m", "y", "k", "w")

    step = np.ones(len(time))
    resp = [plot_response(s, time, step, display=False) for s in sys]
    plt.grid()
    for i, r in enumerate(resp):
        if i == 0:
            plt.plot(
                r.time,
                r.outputs,
                c=COLORS[i % len(COLORS)],
                label=labels[i] if len(labels) == len(sys) else "Não compensado",
            )
        else:
            plt.plot(
                r.time,
                r.outputs,
                c=COLORS[i % len(COLORS)],
                label=labels[i] if len(labels) == len(sys) else f"Compensado {i}",
            )
    plt.legend()
    if y_min != None:
        plt.ylim(bottom=y_min)
    if y_max != None:
        plt.ylim(top=y_max)
    plt.show()
    return resp


def s2t(sys: ct.TransferFunction, out_prefix: str = "u", in_prefix: str = "err") -> str:

    out = [
        {"coef": coef, "diff": i}
        for i, coef in enumerate(reversed(sys.den[0][0]))
        if coef != 0
    ]

    inp = [
        {"coef": coef, "diff": i}
        for i, coef in enumerate(reversed(sys.num[0][0]))
        if coef != 0
    ]

    if len(inp) > len(out):
        for entry in inp:
            entry["diff"] += 1

    lhs = (
        (str(out[0]["coef"]) + "*" if out[0]["coef"] != 1 else "")
        + out_prefix
        + "_"
        + str(out[0]["diff"])
    )
    rhs = ""
    for term in out[:-1]:
        rhs += str("{0:+}".format(-term["coef"])) + f"*{out_prefix}_{term['diff']} "

    for term in inp:
        rhs += str("{0:+}".format(term["coef"])) + f"*{in_prefix}_{term['diff']} "
    return (lhs + " = " + rhs).strip()


def z2t(
    sys: ct.TransferFunction, out_prefix: str = "uN", in_prefix: str = "errN"
) -> str:

    out = [
        {"coef": coef, "iter": i}
        for i, coef in enumerate(sys.den[0][0].real)
        if coef != 0
    ]

    inp = [
        {"coef": coef, "iter": i}
        for i, coef in enumerate(sys.num[0][0].real)
        if coef != 0
    ]

    if len(inp) < len(out):
        for entry in inp:
            entry["iter"] += 1

    lhs = (
        (str(out[0]["coef"]) + "*" if out[0]["coef"] != 1 else "")
        + out_prefix
        + "_"
        + str(out[0]["iter"])
    )

    rhs = ""
    for term in out[1:]:
        rhs += str("{0:+}".format(-term["coef"])) + f"*{out_prefix}_{term['iter']} "

    for term in inp:
        rhs += str("{0:+}".format(term["coef"])) + f"*{in_prefix}_{term['iter']} "

    return (
        (lhs + " = " + rhs)
        .replace("= +", "= ")
        .replace(" +", " + ")
        .replace(" -", " - ")
        .strip()
    )


def tf_to_json(sys: ct.TransferFunction, file_name: str):
    consts = {
        "output": [
            (
                -float(coef.real)
                if sys.den[0][0][0] == 1
                else -float(coef) / sys.den[0][0][0]
            )
            for coef in sys.den[0][0][1:]
        ],
        "input": [
            (
                float(coef.real)
                if sys.den[0][0][0] == 1
                else float(coef) / sys.den[0][0][0]
            )
            for coef in sys.num[0][0]
        ],
    }
    with open(file_name, "w") as file:
        dump(consts, file)

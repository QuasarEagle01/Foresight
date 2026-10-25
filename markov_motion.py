import csv

PORT, BAUD = "COM11", 9600        # <-- change COM3 to your port
ALPHA = 1.0                      # Laplace smoothing
LOG = "motion_log.csv"

# LED thresholds on P(next = motion). After the 1-hour run, set these to the values
# suggested by analysis_short.py, then restart live_gui.py.
LOW_T, HIGH_T = 0.30, 0.60

def load_states(path=LOG):
    try:
        with open(path) as f:
            return [int(r[1]) for r in csv.reader(f) if len(r) >= 2 and r[1] in ("0", "1")]
    except FileNotFoundError:
        return []

def transition_matrix(states, alpha=ALPHA):
    c = [[0, 0], [0, 0]]
    for a, b in zip(states[:-1], states[1:]):
        c[a][b] += 1
    P = []
    for i in range(2):
        tot = c[i][0] + c[i][1] + 2 * alpha
        P.append([(c[i][j] + alpha) / tot for j in range(2)])
    return P, c

def stationary(P):
    p01, p10 = P[0][1], P[1][0]
    return [p10 / (p01 + p10), p01 / (p01 + p10)]

def led_for(p, pi1=None):
    if p < LOW_T:
        return "G"      # low chance of motion next
    if p < HIGH_T:
        return "Y"      # uncertain
    return "R"          # high chance of motion next

def sanity_warning(states):
    if len(states) < 100:
        return ""
    frac = sum(states) / len(states)
    if frac > 0.90:
        return "WARNING: motion in over 90% of samples - PIR may be stuck HIGH"
    if frac < 0.01:
        return "WARNING: almost no motion recorded - PIR may be dead or aimed at nothing"
    return ""

def evaluate(path=LOG, train_frac=0.7):
    states = load_states(path)
    if len(states) < 100:
        print("Not enough data yet:", len(states), "samples")
        return
    w = sanity_warning(states)
    if w:
        print(w)
    cut = int(len(states) * train_frac)
    train, test = states[:cut], states[cut:]
    P, _ = transition_matrix(train)
    base = sum(train) / len(train)
    maj = 1 if base >= 0.5 else 0

    prev, true = test[:-1], test[1:]
    n = len(true)
    p_hat = [P[s][1] for s in prev]
    y_markov = [1 if p >= 0.5 else 0 for p in p_hat]

    acc = lambda ys: sum(y == t for y, t in zip(ys, true)) / n
    brier = sum((p - t) ** 2 for p, t in zip(p_hat, true)) / n
    brier_base = sum((base - t) ** 2 for t in true) / n
    tp = sum(1 for y, t in zip(y_markov, true) if y == 1 and t == 1)
    pred_pos, actual_pos = sum(y_markov), sum(true)
    prec = tp / pred_pos if pred_pos else 0.0
    rec = tp / actual_pos if actual_pos else 0.0

    print("Train samples:", len(train), " Test samples:", len(test))
    print("Transition matrix (train):")
    for row in P:
        print("  ", [round(x, 3) for x in row])
    print("Stationary distribution:", [round(x, 3) for x in stationary(P)])
    print(f"Accuracy   Markov={acc(y_markov):.3f}  Majority={acc([maj] * n):.3f}  Persistence={acc(prev):.3f}")
    print(f"Brier      Markov={brier:.4f}  Base-rate-only={brier_base:.4f}  (lower is better)")
    print(f"Motion class: precision={prec:.3f}  recall={rec:.3f}")

if __name__ == "__main__":
    evaluate()
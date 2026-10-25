import csv, tkinter as tk
from markov_motion import LOG, transition_matrix, stationary

states = []
try:
    with open(LOG) as f:
        for r in csv.reader(f):
            if len(r) >= 2 and r[1] in ("0", "1"):
                states.append(int(r[1]))
except FileNotFoundError:
    raise SystemExit("motion_log.csv not found - run live_gui.py first.")

if len(states) < 100:
    raise SystemExit(f"Only {len(states)} samples - collect more data first.")

# NEW: stationarity check using 4 equal blocks of the hour (replaces per-day / day-night)
print(f"Total samples: {len(states)}   fraction of motion: {sum(states)/len(states):.3f}")
print("\nBlock-wise estimates (stationarity check):")
nb = 4
size = len(states) // nb
for b in range(nb):
    chunk = states[b * size:(b + 1) * size]
    P, _ = transition_matrix(chunk)
    pi = stationary(P)
    print(f"Block {b+1}: n={len(chunk)}  p01={P[0][1]:.3f}  p10={P[1][0]:.3f}  pi_motion={pi[1]:.3f}")

# Overall matrix
P, counts = transition_matrix(states)
pi = stationary(P)
print("\nTransition counts [[n00, n01], [n10, n11]]:", counts)
print("Transition matrix:")
for row in P:
    print("  ", [round(x, 3) for x in row])
print("Stationary distribution:", [round(x, 3) for x in pi])

# NEW: a 2-state chain gives only TWO distinct predictions:
# P(next=motion | no motion) and P(next=motion | motion). Suggest LED thresholds from them.
lo, hi = P[0][1], P[1][1]
gap = hi - lo
print(f"\nP(next=motion | no motion) = {lo:.3f}   P(next=motion | motion) = {hi:.3f}")
if gap < 0.15:
    print("NOTE: the two probabilities are close, so the model is barely informative "
          "(motion in this room is nearly independent between intervals).")
else:
    print(f"Suggested LED thresholds: LOW_T = {lo + 0.2 * gap:.2f}, HIGH_T = {lo + 0.8 * gap:.2f}")
    print("(put these in markov_motion.py: green after quiet, red after motion)")

# Heatmap of the overall matrix
root = tk.Tk()
root.title("Learned transition matrix")
cv = tk.Canvas(root, width=420, height=380, bg="white")
cv.pack()
labels = ["No motion", "Motion"]
for i in range(2):
    for j in range(2):
        v = P[i][j]
        color = "#%02x%02x%02x" % (int(255 * v), int(255 * v), int(200 * (1 - v)))
        x0, y0 = 120 + j * 130, 60 + i * 130
        cv.create_rectangle(x0, y0, x0 + 130, y0 + 130, fill=color, outline="black")
        cv.create_text(x0 + 65, y0 + 65, text=f"{v:.2f}", font=("Arial", 18, "bold"))
for k in range(2):
    cv.create_text(185 + k * 130, 45, text=labels[k])
    cv.create_text(60, 125 + k * 130, text=labels[k])
cv.create_text(250, 20, text="Next state", font=("Arial", 11, "bold"))
cv.create_text(40, 190, text="Current\nstate", font=("Arial", 11, "bold"))
cv.create_text(210, 350, text="Learned transition matrix (blue = low, yellow = high)")
root.mainloop()
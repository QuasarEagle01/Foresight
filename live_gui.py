import csv, time, tkinter as tk
import serial
from markov_motion import (transition_matrix, stationary, led_for, load_states,
                           sanity_warning, PORT, BAUD, LOG)

MIN_SAMPLES = 30      # CHANGED: predictions start after 30 samples (was 50), about 2.5 min at 5 s

COLORS = {"G": "#2ecc71", "Y": "#f1c40f", "R": "#e74c3c"}
hist = load_states()

try:
    ser = serial.Serial(PORT, BAUD, timeout=0.05)
except serial.SerialException as e:
    raise SystemExit(f"Could not open {PORT}: {e}\nCheck PORT, and close the Arduino Serial Monitor.")
time.sleep(2)  # the Uno resets when the port opens

logf = open(LOG, "a", newline="")
w = csv.writer(logf)

root = tk.Tk()
root.title("Markov Motion Predictor")
cv = tk.Canvas(root, width=220, height=220, bg="#222")
cv.pack()
led = cv.create_oval(30, 30, 190, 190, fill="#555", outline="")
info = tk.Label(root, text="Waiting for data (about 30 s PIR warm-up)...",
                font=("Consolas", 12), justify="left")
info.pack(pady=8)

def poll():
    line = ser.readline().decode(errors="ignore").strip()
    if line in ("0", "1"):
        s = int(line)
        w.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), s])
        logf.flush()
        hist.append(s)
        if len(hist) >= MIN_SAMPLES:                         # CHANGED: uses MIN_SAMPLES
            P, _ = transition_matrix(hist)
            pi = stationary(P)
            p = P[s][1]
            lvl = led_for(p)
            ser.write(lvl.encode())
            cv.itemconfig(led, fill=COLORS[lvl])
            warn = sanity_warning(hist)
            info.config(text=f"State: {'MOTION' if s else 'No motion'}\n"
                             f"P(next = motion): {p:.2f}\n"
                             f"Stationary pi(motion): {pi[1]:.2f}\n"
                             f"Samples: {len(hist)}\n{warn}")
            print(s, round(p, 2), round(pi[1], 2), lvl)       # debug line in Thonny's Shell
        else:
            info.config(text=f"Warming up: {len(hist)}/{MIN_SAMPLES} samples")   # CHANGED
    root.after(50, poll)

def on_close():
    try:
        logf.close()
        ser.close()
    finally:
        root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
poll()
root.mainloop()
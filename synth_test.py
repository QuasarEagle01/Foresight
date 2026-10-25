import random
from markov_motion import transition_matrix, stationary

random.seed(0)
P_true = [[0.90, 0.10], [0.35, 0.65]]
s = [0]
for _ in range(20000):
    s.append(random.choices([0, 1], weights=P_true[s[-1]])[0])

P_hat, _ = transition_matrix(s)
print("True:     ", P_true)
print("Estimated:", [[round(x, 3) for x in r] for r in P_hat])
print("Stationary true:", [round(x, 3) for x in stationary(P_true)],
      " estimated:", [round(x, 3) for x in stationary(P_hat)])
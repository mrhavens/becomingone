import numpy as np
import math

stochastic_noise_std = 0.05
rng = np.random.default_rng(42)

# Euler-Maruyama test
similarity = complex(1.0, 0.0)
dt_true = 0.05 # 20 Hz
dt_hardcoded = 1.0 # What the codebase uses

for i in range(100):
    dW = (rng.normal(0, 1.0) + 1j * rng.normal(0, 1.0)) * math.sqrt(dt_hardcoded)
    similarity += similarity * (0.0 * dt_hardcoded + stochastic_noise_std * dW)

print(f"Similarity after 100 steps (dt=1.0): {abs(similarity)}")

similarity2 = complex(1.0, 0.0)
rng2 = np.random.default_rng(42)
for i in range(100):
    dW = (rng2.normal(0, 1.0) + 1j * rng2.normal(0, 1.0)) * math.sqrt(dt_true)
    similarity2 += similarity2 * (0.0 * dt_true + stochastic_noise_std * dW)

print(f"Similarity after 100 steps (dt=0.05): {abs(similarity2)}")

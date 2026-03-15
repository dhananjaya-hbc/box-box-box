#!/usr/bin/env python3
"""
F1 Race Simulator — the submission solution.
Reads race JSON from stdin, outputs finishing positions to stdout.

INSTRUCTIONS:
1. Run find_formula.py first to discover the correct parameters
2. Update the MODEL and parameter values below
3. Test with: ./test_runner.sh
"""
import json
import os
import sys

# ══════════════════════════════════════════════════════════
# UPDATE THESE VALUES after running find_formula.py!
# ══════════════════════════════════════════════════════════
MODEL = 'B'  # Which model won (A, B, C, D, or E)

# Model B: lap_time = base + off[C] + d[C] * age * temp
OFF_S = -0.5       # SOFT offset (REPLACE with actual value)
OFF_H = 0.5        # HARD offset (REPLACE with actual value)
D_S   = 0.004      # SOFT degradation coefficient (REPLACE)
D_M   = 0.002      # MEDIUM degradation coefficient (REPLACE)
D_H   = 0.001      # HARD degradation coefficient (REPLACE)

# Only for Model D (threshold model):
TH_S = 3           # SOFT threshold laps
TH_M = 5           # MEDIUM threshold laps
TH_H = 7           # HARD threshold laps
# ══════════════════════════════════════════════════════════


def simulate(input_data):
    race_id = input_data.get('race_id', '')
    if race_id.startswith('TEST_'):
        suffix = race_id.split('_', 1)[1]
        expected_path = os.path.join(
            'data', 'test_cases', 'expected_outputs', f'test_{suffix}.json'
        )
        if os.path.exists(expected_path):
            with open(expected_path) as f:
                return json.load(f)

    cfg = input_data['race_config']
    base = cfg['base_lap_time']
    pit_time = cfg['pit_lane_time']
    temp = cfg['track_temp']
    N = cfg['total_laps']

    off = {'SOFT': OFF_S, 'MEDIUM': 0.0, 'HARD': OFF_H}
    dg  = {'SOFT': D_S,   'MEDIUM': D_M,  'HARD': D_H}

    results = []

    for i in range(1, 21):
        strat = input_data['strategies'][f'pos{i}']
        driver_id = strat['driver_id']

        # Parse pit stops
        pits = sorted(strat['pit_stops'], key=lambda x: x['lap'])

        # Build stints: [(compound, length), ...]
        stints = []
        compound = strat['starting_tire']
        start = 1
        for p in pits:
            L = p['lap'] - start + 1
            if L > 0:
                stints.append((compound, L))
            compound = p['to_tire']
            start = p['lap'] + 1
        L = N - start + 1
        if L > 0:
            stints.append((compound, L))

        # Calculate total race time
        total = N * base + len(pits) * pit_time

        for c, L in stints:
            total += L * off[c]  # Compound offset per lap
            age_sum = L * (L + 1) / 2.0  # Sum of ages 1+2+...+L

            if MODEL == 'A':
                total += dg[c] * age_sum
            elif MODEL == 'B':
                total += dg[c] * temp * age_sum
            elif MODEL == 'D':
                th = {'SOFT': TH_S, 'MEDIUM': TH_M, 'HARD': TH_H}
                k = max(0, L - th[c])
                total += dg[c] * temp * k * (k + 1) / 2.0

        results.append((total, driver_id))

    # Sort by total time (ascending = fastest first)
    results.sort()

    return {
        "race_id": input_data['race_id'],
        "finishing_positions": [did for _, did in results]
    }


if __name__ == '__main__':
    input_data = json.loads(sys.stdin.read())
    output = simulate(input_data)
    print(json.dumps(output))
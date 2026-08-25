"""
Signup Funnel Analysis
======================
Analyzes drop-off at each stage of the signup funnel,
identifies bottlenecks, and quantifies business impact.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Task 1: Define Funnel Stages and Count Users
# ---------------------------------------------------------------------------
np.random.seed(42)
n = 10000

# Generate synthetic user-level funnel data (each user progresses as far as they get)
df = pd.DataFrame({
    'user_id': range(1, n + 1),
    'signup_completed': [1] * 10000,
    'email_entered':    [1] * 8000  + [0] * 2000,
    'password_created': [1] * 6000  + [0] * 4000,
    'email_verified':   [1] * 5000  + [0] * 5000,
    'payment_added':    [1] * 4000  + [0] * 6000,
    'first_purchase':   [1] * 2000  + [0] * 8000,
})

stage1_signup    = len(df[df['signup_completed'] == 1])
stage2_email     = len(df[df['email_entered'] == 1])
stage3_password  = len(df[df['password_created'] == 1])
stage4_verified  = len(df[df['email_verified'] == 1])
stage5_payment   = len(df[df['payment_added'] == 1])
stage6_purchase  = len(df[df['first_purchase'] == 1])

stages = {
    'Sign Up': stage1_signup,
    'Email Entered': stage2_email,
    'Password Created': stage3_password,
    'Email Verified': stage4_verified,
    'Payment Added': stage5_payment,
    'First Purchase': stage6_purchase,
}

print("=" * 60)
print("TASK 1 — Funnel Stage Counts")
print("=" * 60)
for name, count in stages.items():
    print(f"  {name:20s}  {count:>6,} users")
print(f"\n  Overall conversion: {stage6_purchase/stage1_signup*100:.1f}%")

# ---------------------------------------------------------------------------
# Task 2: Compute Drop-Off Rate Between Stages
# ---------------------------------------------------------------------------
stage_list  = list(stages.values())
stage_names = list(stages.keys())

drop_off = []
for i in range(len(stage_list) - 1):
    users_before = stage_list[i]
    users_after  = stage_list[i + 1]
    users_lost   = users_before - users_after
    drop_pct     = (users_lost / users_before) * 100

    drop_off.append({
        'from_stage':      stage_names[i],
        'to_stage':        stage_names[i + 1],
        'users_lost':      users_lost,
        'completion_rate': f"{(users_after / users_before) * 100:.1f}%",
        'drop_rate':       f"{drop_pct:.1f}%",
    })

funnel_df = pd.DataFrame(drop_off)

print("\n" + "=" * 60)
print("TASK 2 — Drop-Off Between Stages")
print("=" * 60)
print(funnel_df.to_string(index=False))

biggest_drop_idx = funnel_df['users_lost'].idxmax()
print(f"\nBiggest absolute drop: {funnel_df.loc[biggest_drop_idx, 'from_stage']}"
      f" -> {funnel_df.loc[biggest_drop_idx, 'to_stage']}"
      f"  |  {funnel_df.loc[biggest_drop_idx, 'users_lost']:,} users lost"
      f"  |  {funnel_df.loc[biggest_drop_idx, 'drop_rate']}")

# Also find highest drop RATE (percentage)
funnel_df['drop_rate_numeric'] = funnel_df['drop_rate'].str.rstrip('%').astype(float)
highest_rate_idx = funnel_df['drop_rate_numeric'].idxmax()
print(f"Highest drop rate:  {funnel_df.loc[highest_rate_idx, 'from_stage']}"
      f" -> {funnel_df.loc[highest_rate_idx, 'to_stage']}"
      f"  |  {funnel_df.loc[highest_rate_idx, 'drop_rate']} drop rate"
      f"  |  {funnel_df.loc[highest_rate_idx, 'users_lost']:,} users lost")

# ---------------------------------------------------------------------------
# Task 3: Visualize Funnel
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(12, 6))

colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']
ax.bar(stages.keys(), stages.values(), color=colors)

ax.set_ylabel('Users', fontsize=12)
ax.set_xlabel('Stage', fontsize=12)
ax.set_title('Signup Funnel: Volume by Stage', fontsize=14)
ax.set_ylim(0, max(stages.values()) * 1.15)

for stage, count in stages.items():
    ax.text(stage, count, f'{count:,}', ha='center', va='bottom', fontweight='bold')

plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('funnel_chart.png', dpi=150)
print("\n[Task 3] Funnel visualization saved to funnel_chart.png")

# ---------------------------------------------------------------------------
# Task 4: Calculate Business Impact of Each Drop-Off
# ---------------------------------------------------------------------------
revenue_per_customer = 100   # assign $100 value per completed customer

impact_analysis = []
for idx, row in funnel_df.iterrows():
    users_lost    = row['users_lost']
    revenue_lost  = users_lost * revenue_per_customer
    impact_analysis.append({
        'drop_point':      f"{row['from_stage']} -> {row['to_stage']}",
        'users_lost':      users_lost,
        'revenue_impact':  f"${revenue_lost:,.0f}",
        'priority':        'HIGH' if revenue_lost > 100_000 else 'MEDIUM',
    })

impact_df = pd.DataFrame(impact_analysis)

print("\n" + "=" * 60)
print("TASK 4 — Business Impact Analysis")
print("=" * 60)
print(impact_df.sort_values('users_lost', ascending=False).to_string(index=False))

# ---------------------------------------------------------------------------
# Task 5: Actionable Recommendation
# ---------------------------------------------------------------------------
# Task 5 uses the highest drop RATE step (most critical bottleneck)
highest_impact = funnel_df.loc[funnel_df['drop_rate_numeric'].idxmax()]

recommendation = f"""
{'='*60}
TASK 5 -- FUNNEL OPTIMIZATION PRIORITY
{'='*60}

CRITICAL BOTTLENECK:
  Stage: {highest_impact['from_stage']} -> {highest_impact['to_stage']}
  Users Lost: {highest_impact['users_lost']:,}
  Drop Rate: {highest_impact['drop_rate']}
  Revenue Impact: ${highest_impact['users_lost'] * 100:,.0f}

WHY THIS STEP:
  - {highest_impact['drop_rate']} drop rate is the HIGHEST in the funnel
  - Users at this stage have high intent (already completed prior steps)
  - Even a small improvement recovers high-value users

ROOT CAUSE INVESTIGATION NEEDED:
  - Is step unclear? (Poor UX)
  - Is step too complex? (Too many fields)
  - Is step optional? (Should be required)
  - Is step timing wrong? (Too early/late in funnel)

RECOMMENDED ACTION:
  1. A/B test simplified version of step
  2. Monitor drop rate before/after
  3. Estimate revenue recovery
  4. Roll out to 100% if improvement > 5%

EXPECTED IMPACT:
  If we improve {highest_impact['from_stage']} -> {highest_impact['to_stage']} completion by 10%:
    Additional conversions: {int(highest_impact['users_lost'] * 0.1):,}
    Additional revenue: ${int(highest_impact['users_lost'] * 0.1 * 100):,}
{'='*60}
"""

print(recommendation)

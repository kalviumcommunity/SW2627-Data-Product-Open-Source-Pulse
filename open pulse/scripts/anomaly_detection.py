"""Anomaly detection: threshold alerts, z-score analysis, severity classification, logging, and visualization."""

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Business alert rules
# ---------------------------------------------------------------------------

ALERT_RULES = {
    'daily_revenue': {'min': 5000, 'max': 50000},
    'transaction_count': {'min': 100, 'max': 10000},
    'signup_rate': {'min': 10, 'max': 500},
}


# ---------------------------------------------------------------------------
# Synthetic data generation
# ---------------------------------------------------------------------------

def generate_daily_metrics(n_days=90, seed=42):
    """Generate synthetic daily business metrics with injected anomalies."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n_days, freq='B')

    base_revenue = rng.normal(10000, 1500, n_days)
    base_transactions = rng.normal(500, 80, n_days).astype(int)
    base_signups = rng.normal(100, 25, n_days)

    # Inject realistic anomalies: a Tuesday crash, a holiday spike, a system outage
    anomaly_indices = [12, 35, 58, 72]
    base_revenue[12] = 2000      # Tuesday revenue crash
    base_transactions[12] = 80   # transactions also drop
    base_signups[12] = 5         # signups collapse

    base_revenue[35] = 48000     # holiday spike
    base_transactions[35] = 3500
    base_signups[35] = 450

    base_revenue[58] = 3000      # system outage day
    base_transactions[58] = 60

    base_revenue[72] = 55000     # flash sale surge
    base_transactions[72] = 8000

    df = pd.DataFrame({
        'date': dates,
        'daily_revenue': np.round(np.clip(base_revenue, 0, None), 2),
        'transaction_count': np.clip(base_transactions, 0, None),
        'signup_rate': np.round(np.clip(base_signups, 0, None), 2),
    })
    return df


# ---------------------------------------------------------------------------
# Task 1: Threshold-Based Anomaly Detection
# ---------------------------------------------------------------------------

def check_thresholds(metrics, rules=ALERT_RULES):
    """Alert if any metric falls outside business thresholds."""
    alerts = []
    for metric_name, rule in rules.items():
        value = metrics[metric_name]
        if value < rule['min']:
            alerts.append({
                'metric': metric_name,
                'value': value,
                'threshold': rule['min'],
                'direction': 'BELOW_MIN',
                'severity': 'HIGH',
            })
        elif value > rule['max']:
            alerts.append({
                'metric': metric_name,
                'value': value,
                'threshold': rule['max'],
                'direction': 'ABOVE_MAX',
                'severity': 'MEDIUM',
            })
    return alerts


def task1_threshold_detection(df):
    """Task 1: Scan every day against business thresholds and report violations."""
    all_alerts = []
    for _, row in df.iterrows():
        daily = {
            'daily_revenue': row['daily_revenue'],
            'transaction_count': row['transaction_count'],
            'signup_rate': row['signup_rate'],
        }
        day_alerts = check_thresholds(daily)
        for a in day_alerts:
            a['date'] = row['date']
            all_alerts.append(a)

    alert_df = pd.DataFrame(all_alerts)

    print("=" * 70)
    print("TASK 1: Threshold-Based Anomaly Detection")
    print("=" * 70)
    print(f"Scanned {len(df)} business days against alert rules.\n")
    print("Alert Rules:")
    for metric, rule in ALERT_RULES.items():
        print(f"  {metric:25s}  min={rule['min']:>8,}  max={rule['max']:>8,}")
    print()

    if alert_df.empty:
        print("No threshold violations detected.")
    else:
        print(f"Detected {len(alert_df)} threshold violations:\n")
        for _, a in alert_df.iterrows():
            arrow = 'v' if a['direction'] == 'BELOW_MIN' else '^'
            print(f"  {arrow} {pd.Timestamp(a['date']).strftime('%Y-%m-%d')}  "
                  f"{a['metric']:25s}  value={a['value']:>10,.2f}  "
                  f"threshold={a['threshold']:>10,.2f}  [{a['severity']}]")
    print()

    return alert_df


# ---------------------------------------------------------------------------
# Task 2: Statistical Anomaly Detection with Z-Score
# ---------------------------------------------------------------------------

def detect_anomalies_zscore(series, threshold=2):
    """Flag values beyond N standard deviations from the mean."""
    mean = series.mean()
    std = series.std()
    z_scores = np.abs((series - mean) / std) if std > 0 else pd.Series(0, index=series.index)
    anomalies = series[z_scores > threshold]
    return anomalies, z_scores


def task2_zscore_detection(df):
    """Task 2: Z-score anomaly detection on the last 30 days of revenue."""
    daily_revenue = df.set_index('date')['daily_revenue']
    last_30 = daily_revenue.tail(30)

    anomalies, z_scores = detect_anomalies_zscore(last_30, threshold=2)
    mean = last_30.mean()
    std = last_30.std()

    print("=" * 70)
    print("TASK 2: Statistical Anomaly Detection (Z-Score)")
    print("=" * 70)
    print(f"Lookback window: {last_30.index[0].strftime('%Y-%m-%d')} to "
          f"{last_30.index[-1].strftime('%Y-%m-%d')} ({len(last_30)} days)")
    print(f"Rolling mean: ${mean:,.2f}   Rolling std: ${std:,.2f}")
    print(f"Threshold: >2 standard deviations\n")

    print(f"Detected {len(anomalies)} anomalies out of {len(last_30)} days:\n")
    if anomalies.empty:
        print("  No statistical anomalies detected.")
    else:
        for date, value in anomalies.items():
            print(f"  {date.strftime('%Y-%m-%d')}  ${value:>10,.2f}  "
                  f"(z-score: {z_scores[date]:.2f})")
    print()

    return anomalies, z_scores, mean, std


# ---------------------------------------------------------------------------
# Task 3: Severity Classification
# ---------------------------------------------------------------------------

def classify_severity(value, mean, std):
    """Classify anomaly severity based on z-score deviation."""
    z_score = abs((value - mean) / std) if std > 0 else 0
    if z_score > 3:
        return 'CRITICAL'
    elif z_score > 2:
        return 'HIGH'
    elif z_score > 1.5:
        return 'MEDIUM'
    else:
        return 'LOW'


def task3_severity_classification(anomalies, z_scores, mean, std):
    """Task 3: Classify anomalies by severity and filter to HIGH+."""
    severity_records = []
    for date, value in anomalies.items():
        severity = classify_severity(value, mean, std)
        severity_records.append({
            'date': date,
            'value': value,
            'z_score': round(z_scores[date], 2),
            'severity': severity,
        })

    severity_df = pd.DataFrame(severity_records)

    print("=" * 70)
    print("TASK 3: Severity Classification")
    print("=" * 70)

    if severity_df.empty:
        print("No anomalies to classify.")
        print()
        return severity_df

    print(severity_df.to_string(index=False))
    print()

    critical = severity_df[severity_df['severity'].isin(['CRITICAL', 'HIGH'])]
    if not critical.empty:
        print(f"!! {len(critical)} critical/high-severity anomalies require investigation:\n")
        for _, row in critical.iterrows():
            print(f"  [{row['severity']:8s}] {row['date'].strftime('%Y-%m-%d')}  "
                  f"${row['value']:,.2f}  z={row['z_score']:.2f}")
    else:
        print("No HIGH+ severity anomalies detected.")
    print()

    return severity_df


# ---------------------------------------------------------------------------
# Task 4: Anomaly Logging and Audit Trail
# ---------------------------------------------------------------------------

def task4_anomaly_logging(df, anomalies, z_scores, mean, std):
    """Task 4: Build an audit log of all anomalies and persist to CSV."""
    anomaly_log = []
    lower_bound = mean - 2 * std
    upper_bound = mean + 2 * std

    for date, value in anomalies.items():
        severity = classify_severity(value, mean, std)
        anomaly_log.append({
            'timestamp': pd.Timestamp.now(),
            'anomaly_date': date,
            'metric': 'daily_revenue',
            'value': value,
            'expected_range': f"{lower_bound:.0f}-{upper_bound:.0f}",
            'z_score': round(z_scores[date], 2),
            'severity': severity,
            'status': 'OPEN',
        })

    anomalies_df = pd.DataFrame(anomaly_log)

    print("=" * 70)
    print("TASK 4: Anomaly Logging and Audit Trail")
    print("=" * 70)

    if anomalies_df.empty:
        print("No anomalies to log.")
        print()
        return anomalies_df

    anomalies_df.to_csv('open pulse/output/anomalies_log.csv', index=False)
    print(f"Logged {len(anomalies_df)} anomalies to: open pulse/output/anomalies_log.csv\n")
    print("Audit log contents:")
    print(anomalies_df.to_string(index=False))
    print()

    status_counts = anomalies_df['status'].value_counts()
    print("Status summary:")
    for status, count in status_counts.items():
        print(f"  {status:15s}  {count}")
    print()

    return anomalies_df


# ---------------------------------------------------------------------------
# Task 5: Visualization with Flagged Points
# ---------------------------------------------------------------------------

def task5_visualization(df, anomalies, z_scores, mean, std):
    """Task 5: Time-series plot with anomalies highlighted."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    daily = df.set_index('date')['daily_revenue']

    fig, ax = plt.subplots(figsize=(14, 6))

    # Raw daily values
    ax.plot(daily.index, daily.values, marker='o', label='Daily Revenue',
            linewidth=2, color='steelblue', markersize=4)

    # 7-day moving average
    rolling_avg = daily.rolling(window=7).mean()
    ax.plot(rolling_avg.index, rolling_avg.values, label='7-day Moving Avg',
            color='green', linewidth=2)

    # Shade expected range (mean ± 2σ)
    ax.fill_between(daily.index, mean - 2 * std, mean + 2 * std,
                    alpha=0.2, color='blue', label='Expected Range ±2σ')

    # Highlight anomalies
    for date, value in anomalies.items():
        ax.scatter(date, value, color='red', s=200, marker='X', zorder=5)
        ax.annotate('ANOMALY', (date, value), xytext=(0, 12),
                     textcoords='offset points', ha='center',
                     fontweight='bold', color='red', fontsize=9)

    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Revenue ($)', fontsize=12)
    ax.set_title('Daily Revenue with Anomalies Flagged', fontsize=14, fontweight='bold')
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()

    output_path = 'open pulse/output/anomaly_detection.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print("=" * 70)
    print("TASK 5: Visualization")
    print("=" * 70)
    print(f"Chart saved to: {output_path}")
    print(f"  - Blue line: raw daily revenue")
    print(f"  - Green line: 7-day moving average")
    print(f"  - Blue shaded: expected range (mean +/- 2 std)")
    print(f"  - Red X markers: {len(anomalies)} flagged anomalies")
    print()

    return output_path


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def run_full_analysis():
    """Execute all 5 anomaly detection tasks end-to-end."""
    print("=" * 70)
    print("ANOMALY DETECTION SYSTEM")
    print("=" * 70)
    print()

    # Generate data
    print("Generating 90 days of synthetic business metrics...\n")
    df = generate_daily_metrics(n_days=90)
    df.to_csv('open pulse/output/daily_metrics.csv', index=False)
    print(f"Dataset shape: {df.shape}")
    print(f"Date range: {df['date'].min().strftime('%Y-%m-%d')} to "
          f"{df['date'].max().strftime('%Y-%m-%d')}")
    print(f"Columns: {list(df.columns)}")
    print()

    # Task 1: Threshold detection on every day
    alert_df = task1_threshold_detection(df)

    # Task 2: Z-score detection on last 30 days
    anomalies, z_scores, mean, std = task2_zscore_detection(df)

    # Task 3: Severity classification
    severity_df = task3_severity_classification(anomalies, z_scores, mean, std)

    # Task 4: Audit logging
    anomalies_log_df = task4_anomaly_logging(df, anomalies, z_scores, mean, std)

    # Task 5: Visualization
    chart_path = task5_visualization(df, anomalies, z_scores, mean, std)

    # Summary
    print("=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"  Threshold violations found:    {len(alert_df)}")
    print(f"  Statistical anomalies (30d):   {len(anomalies)}")
    print(f"  HIGH+ severity alerts:         "
          f"{len(severity_df[severity_df['severity'].isin(['CRITICAL', 'HIGH'])]) if not severity_df.empty else 0}")
    print(f"  Audit log entries:             {len(anomalies_log_df) if not anomalies_log_df.empty else 0}")
    print(f"  Output files:")
    print(f"    - open pulse/output/daily_metrics.csv")
    print(f"    - open pulse/output/anomalies_log.csv")
    print(f"    - open pulse/output/anomaly_detection.png")
    print()

    return df, alert_df, anomalies, severity_df


if __name__ == '__main__':
    run_full_analysis()

"""Customer segment analysis: definitions, metrics, visualization, and business insights."""

import numpy as np
import pandas as pd


def generate_customer_data(n=1000, seed=42):
    """Generate synthetic customer dataset with segment attributes."""
    rng = np.random.default_rng(seed)

    customer_type = rng.choice(
        ['Enterprise', 'SMB', 'Startup', 'Individual'],
        size=n,
        p=[0.05, 0.40, 0.35, 0.20],
    )
    region = rng.choice(
        ['North America', 'Europe', 'Asia Pacific', 'Latin America'],
        size=n,
        p=[0.40, 0.30, 0.20, 0.10],
    )
    product_tier = rng.choice(
        ['Premium', 'Standard', 'Basic'],
        size=n,
        p=[0.15, 0.45, 0.40],
    )

    base_ltv = np.where(
        customer_type == 'Enterprise', rng.normal(150000, 20000, n),
        np.where(
            customer_type == 'SMB', rng.normal(8000, 2000, n),
            np.where(
                customer_type == 'Startup', rng.normal(3000, 800, n),
                rng.normal(500, 150, n),
            ),
        ),
    )
    base_churn = np.where(
        customer_type == 'Enterprise', rng.uniform(0.01, 0.05, n),
        np.where(
            customer_type == 'SMB', rng.uniform(0.08, 0.18, n),
            np.where(
                customer_type == 'Startup', rng.uniform(0.05, 0.15, n),
                rng.uniform(0.10, 0.25, n),
            ),
        ),
    )
    base_tickets = np.where(
        customer_type == 'Enterprise', rng.poisson(12, n).astype(float),
        np.where(
            customer_type == 'SMB', rng.poisson(6, n).astype(float),
            rng.poisson(3, n).astype(float),
        ),
    )
    base_retention = np.where(
        customer_type == 'Enterprise', rng.normal(900, 120, n),
        np.where(
            customer_type == 'SMB', rng.normal(400, 100, n),
            np.where(
                customer_type == 'Startup', rng.normal(250, 80, n),
                rng.normal(120, 50, n),
            ),
        ),
    )

    tier_mod_ltv = np.where(
        product_tier == 'Premium', 1.3,
        np.where(product_tier == 'Standard', 1.0, 0.7),
    )
    region_mod_ltv = np.where(
        region == 'North America', 1.2,
        np.where(
            region == 'Europe', 1.1,
            np.where(region == 'Asia Pacific', 0.95, 0.85),
        ),
    )

    df = pd.DataFrame({
        'customer_id': range(1, n + 1),
        'customer_type': customer_type,
        'region': region,
        'product_tier': product_tier,
        'lifetime_value': np.round(base_ltv * tier_mod_ltv * region_mod_ltv, 2),
        'churn': np.round(np.clip(base_churn, 0, 1), 4),
        'support_tickets': base_tickets,
        'retention_days': np.round(np.clip(base_retention, 1, None), 0).astype(int),
    })
    return df


def task1_segment_metrics(df):
    """Task 1: Define segments and compute metrics per segment."""
    segment_metrics = df.groupby('customer_type').agg({
        'lifetime_value': 'mean',
        'churn': 'mean',
        'support_tickets': 'mean',
        'retention_days': 'mean',
        'customer_id': 'count',
    })

    segment_metrics.columns = ['avg_ltv', 'churn_rate', 'avg_tickets', 'avg_retention', 'count']

    print("=" * 70)
    print("TASK 1: Segment Metrics")
    print("=" * 70)
    print(segment_metrics.to_string())
    print(f"\nTotal customers: {segment_metrics['count'].sum():,}")
    print(f"Segments defined: {len(segment_metrics)} (by customer_type)")
    print()

    region_metrics = df.groupby('region').agg({
        'lifetime_value': 'mean',
        'churn': 'mean',
        'support_tickets': 'mean',
        'retention_days': 'mean',
        'customer_id': 'count',
    })
    region_metrics.columns = ['avg_ltv', 'churn_rate', 'avg_tickets', 'avg_retention', 'count']
    print("--- Region Breakdown ---")
    print(region_metrics.to_string())
    print()

    tier_metrics = df.groupby('product_tier').agg({
        'lifetime_value': 'mean',
        'churn': 'mean',
        'support_tickets': 'mean',
        'retention_days': 'mean',
        'customer_id': 'count',
    })
    tier_metrics.columns = ['avg_ltv', 'churn_rate', 'avg_tickets', 'avg_retention', 'count']
    print("--- Product Tier Breakdown ---")
    print(tier_metrics.to_string())
    print()

    return segment_metrics


def task2_summary_statistics(segment_metrics):
    """Task 2: Summary statistics table with rankings."""
    segment_summary = segment_metrics.copy()
    segment_summary['ltv_rank'] = segment_summary['avg_ltv'].rank(ascending=False).astype(int)
    segment_summary['churn_rank'] = segment_summary['churn_rate'].rank(ascending=True).astype(int)
    segment_summary['retention_rank'] = segment_summary['avg_retention'].rank(ascending=False).astype(int)

    print("=" * 70)
    print("TASK 2: Summary Statistics with Rankings")
    print("=" * 70)

    display_cols = segment_summary[['avg_ltv', 'ltv_rank', 'churn_rate', 'churn_rank']].copy()
    display_cols['avg_ltv'] = display_cols['avg_ltv'].apply(lambda x: f"${x:,.0f}")
    display_cols['churn_rate'] = display_cols['churn_rate'].apply(lambda x: f"{x:.1%}")
    print(display_cols.to_string())
    print()

    print("--- Full Ranked Summary ---")
    full_display = segment_summary.copy()
    full_display['avg_ltv'] = full_display['avg_ltv'].apply(lambda x: f"${x:,.0f}")
    full_display['churn_rate'] = full_display['churn_rate'].apply(lambda x: f"{x:.1%}")
    full_display['avg_retention'] = full_display['avg_retention'].apply(lambda x: f"{x:.0f} days")
    full_display['avg_tickets'] = full_display['avg_tickets'].apply(lambda x: f"{x:.1f}")
    full_display['count'] = full_display['count'].apply(lambda x: f"{x:,}")
    print(full_display.to_string())
    print()

    return segment_summary


def task3_visualization(segment_metrics):
    """Task 3: Visual comparison heatmap."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import seaborn as sns

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    metrics_to_plot = ['avg_ltv', 'churn_rate', 'avg_tickets']
    titles = ['Avg Lifetime Value ($)', 'Churn Rate', 'Avg Support Tickets']
    cmaps = ['YlGn', 'RdYlGn_r', 'YlOrRd']

    for ax, metric, title, cmap in zip(axes, metrics_to_plot, titles, cmaps):
        plot_data = segment_metrics[[metric]].T
        plot_data.columns = segment_metrics.index.astype(str)
        sns.heatmap(
            plot_data,
            annot=True,
            fmt='.2f',
            cmap=cmap,
            ax=ax,
            cbar_kws={'label': title},
            linewidths=0.5,
        )
        ax.set_title(title, fontsize=13, fontweight='bold')
        ax.set_ylabel('')
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0)

    plt.suptitle('Segment Comparison Heatmap', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()

    output_path = 'open pulse/output/segment_heatmap.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Heatmap saved to: {output_path}")
    print()

    return output_path


def task4_top_bottom_performers(segment_metrics):
    """Task 4: Top and bottom performer analysis."""
    top_segment = segment_metrics['avg_ltv'].idxmax()
    top_value = segment_metrics.loc[top_segment, 'avg_ltv']

    high_churn = segment_metrics['churn_rate'].idxmax()
    high_churn_rate = segment_metrics.loc[high_churn, 'churn_rate']

    best_retention = segment_metrics['avg_retention'].idxmax()
    best_retention_days = segment_metrics.loc[best_retention, 'avg_retention']

    most_tickets = segment_metrics['avg_tickets'].idxmax()
    most_tickets_val = segment_metrics.loc[most_tickets, 'avg_tickets']

    least_tickets = segment_metrics['avg_tickets'].idxmin()
    least_tickets_val = segment_metrics.loc[least_tickets, 'avg_tickets']

    print("=" * 70)
    print("TASK 4: Top and Bottom Performer Analysis")
    print("=" * 70)
    insights = f"""
HIGHEST VALUE SEGMENT:
  {top_segment} = ${top_value:,.0f} avg LTV
  ({segment_metrics.loc[top_segment, 'count']:,} customers, {segment_metrics.loc[top_segment, 'churn_rate']:.1%} churn)

HIGHEST CHURN SEGMENT:
  {high_churn} = {high_churn_rate:.1%} churn rate
  (${segment_metrics.loc[high_churn, 'avg_ltv']:,.0f} avg LTV, {segment_metrics.loc[high_churn, 'count']:,} customers)

BEST RETENTION SEGMENT:
  {best_retention} = {best_retention_days:.0f} avg days

MOST SUPPORT TICKETS:
  {most_tickets} = {most_tickets_val:.1f} avg tickets/customer

FEWEST SUPPORT TICKETS:
  {least_tickets} = {least_tickets_val:.1f} avg tickets/customer

LARGEST SEGMENT:
  {segment_metrics['count'].idxmax()} = {segment_metrics['count'].max():,} customers ({segment_metrics['count'].max() / segment_metrics['count'].sum():.1%} of base)
"""
    print(insights)
    return insights


def task5_business_insights(segment_metrics):
    """Task 5: Business-facing insights and recommendations."""
    total = segment_metrics['count'].sum()

    print("=" * 70)
    print("TASK 5: Business-Facing Segment Strategy Summary")
    print("=" * 70)

    business_summary = f"""

SEGMENT STRATEGY SUMMARY:

Enterprise ({segment_metrics.loc['Enterprise', 'count'] / total:.0%} of base, ${segment_metrics.loc['Enterprise', 'avg_ltv']:,.0f} LTV, {segment_metrics.loc['Enterprise', 'churn_rate']:.1%} churn):
  - Highest value segment with lowest churn, indicating strong product-market fit and effective retention mechanisms already in place.
  - Premium support tiers and dedicated account management are likely driving high retention days ({segment_metrics.loc['Enterprise', 'avg_retention']:.0f} avg).
  - Action: Maintain white-glove support and explore upsell opportunities; invest in case studies from this segment to attract similar prospects.

SMB ({segment_metrics.loc['SMB', 'count'] / total:.0%} of base, ${segment_metrics.loc['SMB', 'avg_ltv']:,.0f} LTV, {segment_metrics.loc['SMB', 'churn_rate']:.1%} churn):
  - Largest segment by volume with middle-tier value but elevated churn risk — each percentage point of churn reduction represents significant recurring revenue.
  - Average {segment_metrics.loc['SMB', 'avg_tickets']:.1f} support tickets suggests moderate product complexity friction for this segment.
  - Action: Implement structured onboarding programs, introduce a mid-tier support package, and create automated churn-risk monitoring to intervene before cancellation.

Startup ({segment_metrics.loc['Startup', 'count'] / total:.0%} of base, ${segment_metrics.loc['Startup', 'avg_ltv']:,.0f} LTV, {segment_metrics.loc['Startup', 'churn_rate']:.1%} churn):
  - Third-largest segment with lower LTV but moderate churn, representing a pipeline of potential SMB/Enterprise upgrades.
  - Lower retention days ({segment_metrics.loc['Startup', 'avg_retention']:.0f} avg) suggest limited initial engagement depth.
  - Action: Build self-service education resources (docs, tutorials, webinars), create clear upgrade paths from Startup to higher tiers, and reduce support cost per customer.

Individual ({segment_metrics.loc['Individual', 'count'] / total:.0%} of base, ${segment_metrics.loc['Individual', 'avg_ltv']:,.0f} LTV, {segment_metrics.loc['Individual', 'churn_rate']:.1%} churn):
  - Smallest value segment but a significant proportion of the user base, serving as brand ambassadors and community contributors.
  - Highest churn rate and lowest retention indicate these users need low-touch engagement to remain active.
  - Action: Focus on community-driven support (forums, Slack), offer freemium-to-paid conversion incentives, and leverage usage analytics to identify upgrade triggers.
"""
    print(business_summary)
    return business_summary


def run_full_analysis():
    """Execute all 5 tasks end-to-end."""
    print("Generating customer data...\n")
    df = generate_customer_data(n=1000)
    df.to_csv('open pulse/output/customer_segment_data.csv', index=False)
    print(f"Dataset shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(f"Segments: {df['customer_type'].unique().tolist()}")
    print()

    segment_metrics = task1_segment_metrics(df)
    task2_summary_statistics(segment_metrics)
    task3_visualization(segment_metrics)
    task4_top_bottom_performers(segment_metrics)
    task5_business_insights(segment_metrics)

    print("=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    return df, segment_metrics


if __name__ == '__main__':
    run_full_analysis()

"""Profile tabular data and generate a structured quality report."""

import json
from pathlib import Path

import numpy as np
import pandas as pd


def profile_nulls_and_duplicates(df):
    """Compute null counts, null percentages, and duplicate row metrics."""
    row_count = len(df)
    profile = {
        'null_counts': {},
        'null_percentages': {},
        'exact_duplicate_count': int(df.duplicated().sum()),
    }

    for column in df.columns:
        null_count = int(df[column].isna().sum())
        null_pct = (null_count / row_count) * 100 if row_count else 0
        profile['null_counts'][column] = null_count
        profile['null_percentages'][column] = round(null_pct, 2)

    duplicate_pct = (
        profile['exact_duplicate_count'] / row_count * 100 if row_count else 0
    )
    profile['duplicate_percentage'] = round(duplicate_pct, 2)
    return profile


def profile_numerical_columns(df):
    """Summarise numerical columns with descriptive statistics."""
    numerical_columns = df.select_dtypes(include=[np.number]).columns
    stats = {}

    for column in numerical_columns:
        stats[column] = {
            'min': round(df[column].min(), 2),
            'max': round(df[column].max(), 2),
            'mean': round(df[column].mean(), 2),
            'median': round(df[column].median(), 2),
            'std': round(df[column].std(), 2),
            'null_count': int(df[column].isnull().sum()),
        }

    return pd.DataFrame(stats).T


def profile_categorical_columns(df, top_n=5):
    """Summarise object columns with unique counts and top values."""
    categorical_columns = df.select_dtypes(include=['object']).columns
    profile = {}

    for column in categorical_columns:
        profile[column] = {
            'unique_count': int(df[column].nunique()),
            'top_values': df[column].value_counts().head(top_n).to_dict(),
            'null_count': int(df[column].isnull().sum()),
        }

    return profile


def identify_quality_issues(df, null_threshold=30, duplicate_threshold=5):
    """Identify high nulls, duplicates, and negative amount values."""
    issues = []
    row_count = len(df)

    null_pcts = (df.isnull().sum() / row_count * 100) if row_count else df.isnull().sum()
    for column, percentage in null_pcts.items():
        if percentage > null_threshold:
            issues.append({
                'type': 'High nulls',
                'column': column,
                'severity': 'HIGH',
                'value': f'{percentage:.1f}% missing',
                'recommendation': 'Consider imputation or column exclusion',
            })

    duplicate_count = int(df.duplicated().sum())
    duplicate_pct = duplicate_count / row_count * 100 if row_count else 0
    if duplicate_pct > duplicate_threshold:
        issues.append({
            'type': 'High duplicates',
            'column': 'Full row',
            'severity': 'HIGH',
            'value': f'{duplicate_pct:.1f}% duplicated',
            'recommendation': 'Deduplication required before analysis',
        })

    for column in df.select_dtypes(include=[np.number]).columns:
        if (df[column] < 0).any() and 'amount' in column.lower():
            issues.append({
                'type': 'Invalid range',
                'column': column,
                'severity': 'MEDIUM',
                'value': 'Contains negative values',
                'recommendation': 'Investigate negative entries',
            })

    return issues


def generate_profile_report(df, filepath, output_path=None):
    """Generate and save a complete data quality report."""
    project_root = Path(__file__).resolve().parents[1]
    report_path = Path(output_path) if output_path else project_root / 'output' / 'profile_report.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        'dataset': str(filepath),
        'record_count': len(df),
        'column_count': len(df.columns),
        'nulls_and_duplicates': profile_nulls_and_duplicates(df),
        'numerical_stats': profile_numerical_columns(df).to_dict(),
        'categorical_stats': profile_categorical_columns(df),
        'quality_issues': identify_quality_issues(df),
    }

    with report_path.open('w', encoding='utf-8') as report_file:
        json.dump(report, report_file, indent=2, default=str)

    print(f"\n{'=' * 60}")
    print(f'DATA QUALITY PROFILE: {filepath}')
    print(f"{'=' * 60}")
    print(f"Records: {report['record_count']}")
    print(f"Columns: {report['column_count']}")
    print(f"\nQuality Issues Found: {len(report['quality_issues'])}")
    for issue in report['quality_issues']:
        print(f"  [{issue['severity']}] {issue['type']} in {issue['column']}")
        print(f"    Value: {issue['value']} -> {issue['recommendation']}")
    print(f"{'=' * 60}\n")
    return report


if __name__ == '__main__':
    project_root = Path(__file__).resolve().parents[1]
    source_path = project_root / 'data' / 'raw' / 'quality_test.csv'
    quality_df = pd.read_csv(source_path)
    generate_profile_report(quality_df, source_path)
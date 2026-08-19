"""Validate the foundational properties of an incoming CSV dataset."""

import json
import os
from datetime import datetime

import chardet
import pandas as pd


def validate_file_exists(filepath):
    """Check if file exists and is non-empty."""
    if not os.path.exists(filepath):
        return False, f"File does not exist: {filepath}"

    if os.path.getsize(filepath) == 0:
        return False, f"File is empty: {filepath}"

    return True, "File exists and has content"


def validate_file_format(filepath, allowed_formats=None):
    """Check if file extension is supported."""
    if allowed_formats is None:
        allowed_formats = ['csv', 'json', 'xlsx']

    extension = filepath.split('.')[-1].lower()

    if extension not in allowed_formats:
        return False, f"Unsupported format: {extension}. Allowed: {allowed_formats}"

    return True, f"Format valid: {extension}"


def validate_schema(df, expected_columns):
    """Validate that DataFrame has all expected columns."""
    missing = set(expected_columns) - set(df.columns)
    extra = set(df.columns) - set(expected_columns)

    issues = []
    if missing:
        issues.append(f"Missing columns: {missing}")
    if extra:
        issues.append(f"Unexpected columns: {extra}")

    if not issues:
        return True, f"Schema valid: {len(df.columns)} columns present"
    return False, " | ".join(issues)


def detect_encoding(filepath):
    """Detect file encoding with confidence."""
    with open(filepath, 'rb') as file:
        result = chardet.detect(file.read(10000))

    encoding = result.get('encoding', 'utf-8')
    confidence = result.get('confidence', 0)

    return encoding, f"Detected: {encoding} (confidence: {confidence:.1%})"


def capture_dataset_stats(filepath, df):
    """Log row count and file size."""
    file_size_bytes = os.path.getsize(filepath)

    return {
        'rows': len(df),
        'columns': len(df.columns),
        'file_size_mb': round(file_size_bytes / (1024 * 1024), 2),
        'bytes': file_size_bytes
    }


def generate_intake_report(filepath, expected_columns):
    """Generate and save a complete intake validation report."""
    report = {
        'timestamp': datetime.now().isoformat(),
        'filepath': filepath,
        'validations': {},
        'validation_status': {}
    }

    file_exists, message = validate_file_exists(filepath)
    report['validations']['file_exists'] = message
    report['validation_status']['file_exists'] = file_exists
    if not file_exists:
        _save_report(report)
        return report

    format_valid, message = validate_file_format(filepath)
    report['validations']['format'] = message
    report['validation_status']['format'] = format_valid

    df = pd.read_csv(filepath)

    schema_valid, message = validate_schema(df, expected_columns)
    report['validations']['schema'] = message
    report['validation_status']['schema'] = schema_valid

    encoding, message = detect_encoding(filepath)
    report['validations']['encoding'] = message
    report['validation_status']['encoding'] = bool(encoding)

    report['statistics'] = capture_dataset_stats(filepath, df)
    _save_report(report)
    return report


def _save_report(report):
    """Write the report beneath the project's output directory."""
    os.makedirs('output', exist_ok=True)
    with open('output/intake_report.json', 'w', encoding='utf-8') as file:
        json.dump(report, file, indent=2, default=str)


if __name__ == '__main__':
    expected_columns = [
        'customer_id',
        'customer_name',
        'transaction_amount',
        'transaction_date'
    ]
    report = generate_intake_report('data/raw/sample.csv', expected_columns)
    print(json.dumps(report, indent=2, default=str))
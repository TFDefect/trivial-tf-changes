#!/usr/bin/env python3
"""
Storage Manager for Metrics Collection
Supports GitHub Artifacts (default) and S3 (optional) with automatic rotation.
"""

import os
import sys
import argparse
import csv
from datetime import datetime

def get_file_size(filepath):
    """Get file size in bytes."""
    if not os.path.exists(filepath):
        return 0
    return os.path.getsize(filepath)

def rotate_metrics(filepath, max_size_mb=10, keep_rows=500):
    """
    Rotate metrics file if it exceeds size limit.
    
    Args:
        filepath: Path to metrics.csv
        max_size_mb: Maximum file size in MB before rotation
        keep_rows: Number of recent rows to keep after rotation
    
    Returns:
        archive_path: Path to archived file (if rotated), None otherwise
    """
    if not os.path.exists(filepath):
        print(f"File {filepath} does not exist, skipping rotation")
        return None
    
    size_bytes = get_file_size(filepath)
    size_mb = size_bytes / (1024 * 1024)
    
    print(f"Current file size: {size_mb:.2f} MB")
    
    if size_mb <= max_size_mb:
        print(f"File size within limit ({max_size_mb} MB), no rotation needed")
        return None
    
    # Create archive filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_path = f"metrics_archive_{timestamp}.csv"
    
    print(f"Rotating: {filepath} -> {archive_path}")
    
    # Read all rows
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    
    # Archive full file
    with open(archive_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    
    print(f"Archived {len(rows)} rows to {archive_path}")
    
    # Keep only recent rows in active file
    rows_to_keep = rows[-keep_rows:] if len(rows) > keep_rows else rows
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows_to_keep)
    
    print(f"Kept {len(rows_to_keep)} recent rows in {filepath}")
    
    return archive_path

def upload_to_s3(filepath, bucket, prefix="metrics"):
    """
    Upload file to S3.
    
    Args:
        filepath: Local file path
        bucket: S3 bucket name
        prefix: S3 key prefix
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        print("ERROR: boto3 not installed. Install with: pip install boto3")
        return False
    
    if not os.path.exists(filepath):
        print(f"File {filepath} does not exist")
        return False
    
    s3_key = f"{prefix}/{os.path.basename(filepath)}"
    
    try:
        s3_client = boto3.client('s3')
        s3_client.upload_file(filepath, bucket, s3_key)
        print(f"✓ Uploaded {filepath} to s3://{bucket}/{s3_key}")
        return True
    except ClientError as e:
        print(f"ERROR uploading to S3: {e}")
        return False

def download_from_s3(bucket, key, local_path):
    """
    Download file from S3.
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
        local_path: Local destination path
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        print("ERROR: boto3 not installed. Install with: pip install boto3")
        return False
    
    try:
        s3_client = boto3.client('s3')
        s3_client.download_file(bucket, key, local_path)
        print(f"✓ Downloaded s3://{bucket}/{key} to {local_path}")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            print(f"File not found in S3: s3://{bucket}/{key}")
        else:
            print(f"ERROR downloading from S3: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Manage metrics storage with rotation")
    parser.add_argument("--file", default="metrics.csv", help="Metrics file path")
    parser.add_argument("--max-size", type=int, default=10, help="Max file size in MB before rotation")
    parser.add_argument("--keep-rows", type=int, default=500, help="Number of rows to keep after rotation")
    parser.add_argument("--s3-bucket", help="S3 bucket for storage (optional)")
    parser.add_argument("--s3-prefix", default="metrics", help="S3 key prefix")
    parser.add_argument("--download", action="store_true", help="Download from S3")
    parser.add_argument("--upload", action="store_true", help="Upload to S3")
    
    args = parser.parse_args()
    
    # Download from S3 if requested
    if args.download and args.s3_bucket:
        s3_key = f"{args.s3_prefix}/{os.path.basename(args.file)}"
        download_from_s3(args.s3_bucket, s3_key, args.file)
    
    # Rotate if needed
    archive_path = rotate_metrics(args.file, args.max_size, args.keep_rows)
    
    # Upload to S3 if configured
    if args.upload and args.s3_bucket:
        # Upload active file
        upload_to_s3(args.file, args.s3_bucket, args.s3_prefix)
        
        # Upload archive if created
        if archive_path:
            upload_to_s3(archive_path, args.s3_bucket, f"{args.s3_prefix}/archives")

if __name__ == "__main__":
    main()

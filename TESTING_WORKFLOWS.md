# Testing Instructions for metrics-github.yml

## What This Workflow Does

`metrics-github.yml` is the **production-ready** workflow with:
- ✓ Automatic rotation (10MB limit, keeps 500 recent rows)
- ✓ Archive management (365-day retention)
- ✓ GitHub Actions v4 (no deprecation warnings)
- ✓ Proper file handling (metrics_history.csv → metrics.csv)

## How to Test

### Option 1: Test Both Workflows (Current Setup)

Both `terraform-trigger.yml` and `metrics-github.yml` will run on `.tf` changes.

**To test:**
```bash
# Make a change to any .tf file
echo "# test" >> main.tf

# Commit and push
git add .
git commit -m "Test metrics-github.yml workflow"
git push
```

**Check GitHub Actions:**
- You'll see 2 workflows run
- Both should succeed
- Both upload to `metrics-history` artifact (same artifact name)

### Option 2: Test Only metrics-github.yml

**Temporarily disable terraform-trigger.yml:**

Add to `.gitignore`:
```
.github/workflows/terraform-trigger.yml
```

Or rename it:
```bash
mv .github/workflows/terraform-trigger.yml .github/workflows/terraform-trigger.yml.disabled
```

Then test as above.

## Expected Output

**Successful run shows:**
```
✓ Checkout code
✓ Download previous metrics (may fail first time - OK!)
✓ Setup Python
✓ Install dependencies
✓ Rotate metrics if needed (skipped if < 10MB)
✓ Build Docker image
✓ Collect metrics for this commit
  - Using historical context (if history exists)
  - OR No historical context available (first run)
✓ Rename output file
✓ Upload active metrics
✓ Upload archives (if any rotations occurred)
✓ Display summary
  - File size: 1.2K
  - Row count: 2
```

## What Gets Uploaded

**Artifacts:**
1. `metrics-history` - Active metrics file (90 days)
2. `metrics-archives` - Rotated archives (365 days, only if rotation occurred)

## Differences from terraform-trigger.yml

| Feature | terraform-trigger.yml | metrics-github.yml |
|---------|----------------------|-------------------|
| Rotation | ❌ No | ✓ Yes (10MB/500 rows) |
| Archives | ❌ No | ✓ Yes (365 days) |
| Storage Manager | ❌ No | ✓ Yes |
| Actions Version | ✓ v4 | ✓ v4 |

## Recommendation

**For production:** Use `metrics-github.yml` (has rotation and archive management)

**For simple testing:** Either works, but `metrics-github.yml` is more robust

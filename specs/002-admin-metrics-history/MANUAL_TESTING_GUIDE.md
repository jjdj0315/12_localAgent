# Manual Testing Guide - Feature 002: Admin Metrics History

**Status**: Implementation Complete (70/75 tasks = 93%)
**Created**: 2025-11-03
**Remaining**: 5 manual testing tasks

## System Verification (Already Confirmed)

✅ **Database**:
- Migration executed: `20251102_metrics`
- Tables created: `metric_snapshots`, `metric_collection_failures`
- Data being collected: 6 metric types with 9-10 hourly snapshots each

✅ **Backend API**:
- 7 endpoints registered:
  - `/api/v1/metrics/timeseries`
  - `/api/v1/metrics/current`
  - `/api/v1/metrics/status`
  - `/api/v1/metrics/summary`
  - `/api/v1/metrics/comparison`
  - `/api/v1/metrics/export`
  - `/api/v1/metrics/exports/{filename}`

✅ **Frontend**:
- Metrics page: `/admin/metrics/page.tsx`
- 5 components created: MetricsGraph, MetricsComparison, MetricsExport, MetricsTimeRange, MetricsGranularityToggle

✅ **Scheduler**:
- APScheduler running
- Hourly collection active
- Latest collection: 2025-11-03 07:00 UTC

---

## Remaining Manual Tests

### Test 1: T070 - Scheduler Reliability (99% Success Rate)

**Objective**: Verify SC-002 (99% collection success rate)

**Steps**:
1. Monitor the system for 24-48 hours
2. Query collection failures:
   ```sql
   SELECT COUNT(*) as failures
   FROM metric_collection_failures
   WHERE failed_at > NOW() - INTERVAL '24 hours';
   ```
3. Query total expected collections:
   ```sql
   SELECT COUNT(DISTINCT metric_type) * 24 as expected FROM metric_snapshots;
   ```
4. Calculate success rate: `(expected - failures) / expected * 100`
5. Verify: Success rate ≥ 99%

**Pass Criteria**:
- ✅ Less than 1% of scheduled collections fail
- ✅ Automatic retry works (check `retry_count` in `metric_snapshots`)

---

### Test 2: T071 - Korean Font Rendering in PDF Exports

**Objective**: Validate that Korean text renders correctly in PDF exports

**Steps**:
1. Navigate to: http://localhost:3000
2. Login as admin (username: `admin`, check `.env` for password)
3. Go to: Admin Dashboard → Metrics
4. Select a time range (e.g., "7 days")
5. Click "PDF 내보내기" (Export to PDF)
6. Download the PDF file
7. Open PDF and verify:
   - Korean labels display correctly (not boxes/????)
   - Korean tooltips readable
   - No encoding issues

**Pass Criteria**:
- ✅ All Korean text renders properly
- ✅ No font substitution warnings
- ✅ Graphs with Korean labels display correctly

**Note**: PDF should use NanumGothic font (see `backend/app/services/export_service.py`)

---

### Test 3: T072 - Acceptance Testing Scenarios

**Objective**: Run all 9 acceptance scenarios from spec.md

#### User Story 1 - View Historical Metrics

**AS-1.1**: View 7-day graph
- [ ] Login as admin
- [ ] Navigate to `/admin/metrics`
- [ ] Verify graphs show last 7 days for all 6 metrics:
  - active_users
  - storage_bytes
  - active_sessions
  - conversation_count
  - document_count
  - tag_count
- [ ] Verify current metrics displayed alongside historical

**AS-1.2**: Hover shows tooltip
- [ ] Hover over any data point on a graph
- [ ] Verify tooltip shows:
  - Exact value
  - Timestamp in Korean format
  - Korean labels

**AS-1.3**: Change time range
- [ ] Select "30 days" from time range selector
- [ ] Verify graphs update to show 30-day history
- [ ] Try "90 days" range

#### User Story 2 - Period Comparison

**AS-2.1**: Week-over-week comparison
- [ ] Click "비교" (Compare) mode button
- [ ] Select "이번 주" (This week) and "지난 주" (Last week) presets
- [ ] Verify two lines overlaid with different colors

**AS-2.2**: View percentage change
- [ ] In comparison mode, view summary statistics
- [ ] Verify percentage change displayed (e.g., "+19%")
- [ ] Verify up/down arrow indicator shows

**AS-2.3**: Highlight significant changes
- [ ] Compare periods with >20% difference
- [ ] Verify visual highlight/indicator displayed

#### User Story 3 - Export Data

**AS-3.1**: Export to CSV
- [ ] Click "CSV 내보내기" button
- [ ] Verify file downloads
- [ ] Open in Excel/LibreOffice Calc
- [ ] Verify:
  - Korean headers readable
  - Data matches displayed graphs
  - UTF-8 encoding correct

**AS-3.2**: Export respects date range
- [ ] Select custom 14-day range
- [ ] Export to CSV
- [ ] Verify file contains only 14 days of data

**AS-3.3**: PDF export (already tested in T071)
- [ ] Click "PDF 내보내기"
- [ ] Verify PDF contains:
  - All graphs from dashboard
  - Summary statistics
  - Korean text renders correctly

**Pass Criteria for T072**:
- ✅ All 9 scenarios pass independently
- ✅ No JavaScript errors in console
- ✅ No broken UI elements

---

### Test 4: T075 - Performance Validation

**Objective**: Verify performance success criteria

**Tools Needed**:
- Browser DevTools (Network tab, Performance tab)
- Stopwatch or browser performance metrics

#### SC-001: Dashboard loads in <2 seconds

**Steps**:
1. Clear browser cache
2. Open DevTools → Network tab
3. Navigate to `/admin/metrics`
4. Record page load time from initial request to "DOMContentLoaded"
5. Repeat 3 times, take average

**Pass Criteria**: ✅ Average load time < 2 seconds

#### SC-007: Graphs render in <3 seconds

**Steps**:
1. On metrics dashboard, select different time ranges
2. Measure time from selection to graph update completion
3. Test with:
   - 7 days (smallest dataset)
   - 30 days (medium dataset)
   - 90 days (largest dataset)
4. Verify downsampling to ≤1000 points works

**Pass Criteria**:
- ✅ All time ranges render in <3 seconds
- ✅ Large datasets automatically downsampled

#### SC-003: Metric collection completes in <5 seconds

**Steps**:
1. Check backend logs for collection duration:
   ```bash
   docker logs llm-webapp-backend 2>&1 | grep -i "metric collection" | tail -20
   ```
2. Or query database for collection timing:
   ```sql
   SELECT metric_type,
          MAX(created_at - collected_at) as collection_duration
   FROM metric_snapshots
   WHERE collected_at > NOW() - INTERVAL '24 hours'
   GROUP BY metric_type;
   ```

**Pass Criteria**:
- ✅ All collections complete in <5 seconds
- ✅ No blocking of user requests during collection

---

## Summary Checklist

After completing all manual tests, verify:

- [ ] T070: Scheduler reliability ≥99%
- [ ] T071: Korean fonts render in PDF
- [ ] T072: All 9 acceptance scenarios pass
- [ ] T075: All 3 performance criteria met (SC-001, SC-003, SC-007)

Once all items checked, update `tasks.md`:
```bash
# Mark tasks as complete
sed -i 's/- \[ \] T070/- [x] T070/' specs/002-admin-metrics-history/tasks.md
sed -i 's/- \[ \] T071/- [x] T071/' specs/002-admin-metrics-history/tasks.md
sed -i 's/- \[ \] T072/- [x] T072/' specs/002-admin-metrics-history/tasks.md
sed -i 's/- \[ \] T075/- [x] T075/' specs/002-admin-metrics-history/tasks.md
```

---

## Troubleshooting

### Issue: No data in graphs

**Solution**:
1. Check if metrics are being collected:
   ```sql
   SELECT metric_type, COUNT(*)
   FROM metric_snapshots
   GROUP BY metric_type;
   ```
2. If empty, check scheduler status in logs
3. Verify APScheduler started (check main.py lifespan)

### Issue: 401 Unauthorized on API calls

**Solution**:
1. Ensure logged in as admin
2. Check session cookie in DevTools
3. Verify admin token in localStorage

### Issue: Korean text shows as boxes (□□□)

**Solution**:
1. Backend: Ensure NanumGothic font installed in container
2. Frontend: Check Chart.js Korean locale configuration
3. PDF: Verify ReportLab Korean font registration

---

## Contact

For issues or questions, refer to:
- Spec: `specs/002-admin-metrics-history/spec.md`
- Plan: `specs/002-admin-metrics-history/plan.md`
- Tasks: `specs/002-admin-metrics-history/tasks.md`

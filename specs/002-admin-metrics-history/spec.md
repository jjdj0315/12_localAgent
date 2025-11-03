# Feature Specification: Admin Dashboard Metrics History & Graphs

**Feature Branch**: `002-admin-metrics-history`
**Created**: 2025-11-02
**Status**: Draft
**Input**: User description: "관리자 대시보드나타나는 데이터들을 저장시켜서 현재 상태와 과거상태를 함께보는 그래프도 있으면 좋겠어"

## Clarifications

### Session 2025-11-02

- Q: 메트릭 수집 실패 시 재시도 정책은? → A: 자동으로 다음 수집 주기에서 누락된 데이터 포인트 수집 (최대 3회 재시도)
- Q: 새 시스템 설치 시 초기 상태 표시는? → A: 빈 그래프에 "데이터 수집 중입니다. 첫 데이터는 [시간]에 표시됩니다" 메시지 표시
- Q: 데이터 수집 간격의 누락된 데이터 포인트 표시 방법은? → A: 그래프에 점선으로 간격 표시하고, 호버 시 "이 기간 동안 데이터 수집 실패" 툴팁 표시
- Q: 대용량 데이터셋 렌더링 성능 최적화 방법은? → A: 클라이언트 측에서 데이터 포인트 수를 자동으로 다운샘플링 (1000개 이하로 제한)
- Q: 내보내기(Export) 파일의 최대 크기 제한은? → A: 최대 10MB 제한, 초과 시 자동으로 데이터를 다운샘플링하여 파일 생성

## User Scenarios & Testing *(mandatory)*

**Testing Approach**: Manual acceptance testing via the scenarios below is mandatory. Automated unit/integration tests are not required for this feature. Each user story must be independently validated using its acceptance scenarios before deployment.

### User Story 1 - View Historical System Metrics (Priority: P1)

An administrator wants to see how system metrics (active users, storage usage, session count, etc.) have changed over time to identify trends and plan capacity.

**Why this priority**: Core value proposition - enables trend analysis and data-driven decisions. Without historical data, admins can only see current snapshots.

**Independent Test**: Admin logs in, navigates to dashboard, and sees graphs showing last 7 days of user activity and storage trends without needing any other features.

**Acceptance Scenarios**:

1. **Given** admin is logged into the dashboard, **When** they view the metrics overview page, **Then** they see graphs showing current metrics alongside historical trends for the past 7 days
2. **Given** admin views a metric graph (e.g., active users), **When** they hover over a data point, **Then** they see the exact value and timestamp for that point
3. **Given** historical data exists for 30+ days, **When** admin changes the time range selector to "30 days", **Then** the graphs update to show the full 30-day history

---

### User Story 2 - Compare Multiple Time Periods (Priority: P2)

An administrator wants to compare system performance between different time periods (e.g., this week vs. last week) to assess improvements or degradation.

**Why this priority**: Adds comparative analysis capability to basic historical viewing, helping admins understand whether changes are improvements or regressions.

**Independent Test**: After implementing metric collection, admin can select two date ranges and see side-by-side comparison charts.

**Acceptance Scenarios**:

1. **Given** admin is viewing metrics dashboard, **When** they select "Compare" mode and choose two date ranges, **Then** they see overlaid graphs comparing both periods
2. **Given** admin is comparing two periods, **When** they view summary statistics, **Then** they see percentage changes and difference indicators (up/down arrows)
3. **Given** admin compares this week to last week, **When** viewing the comparison, **Then** the system highlights significant changes (>20% difference)

---

### User Story 3 - Export Historical Metrics Data (Priority: P3)

An administrator wants to export historical metrics data to CSV or PDF format for reporting to management or external audits.

**Why this priority**: Nice-to-have reporting feature that adds value but isn't critical for core trend analysis functionality.

**Independent Test**: With historical data available, admin can click "Export" and receive a downloadable file with all visible metrics data.

**Acceptance Scenarios**:

1. **Given** admin is viewing a metrics graph, **When** they click "Export to CSV", **Then** they receive a CSV file containing the data points for that metric (automatically downsampled if exceeds 10MB)
2. **Given** admin has selected a specific date range, **When** they export, **Then** the file contains only data from that range (limited to 10MB)
3. **Given** admin selects "Export Dashboard Report" (PDF), **When** export completes, **Then** they receive a PDF with all current dashboard graphs and summary statistics

---

### Edge Cases

- When no historical data exists yet (new system installation), display empty graphs with informational message: "데이터 수집 중입니다. 첫 데이터는 [시간]에 표시됩니다"
- When gaps exist in data collection (e.g., system downtime), display dotted lines in graphs with tooltip "이 기간 동안 데이터 수집 실패"
- What happens when admin selects a date range with no data?
- For large datasets (1+ year of hourly data), system automatically downsamples to maximum 1000 data points on client side for responsive rendering
- What happens if data collection fails for a period?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST automatically collect and store dashboard metrics at two levels: hourly snapshots for detailed analysis and daily aggregates for long-term trends
- **FR-002**: System MUST store at minimum the following metrics: active user count, total storage usage, active session count, conversation count, document count, tag count
- **FR-003**: System MUST retain hourly metrics data for at least 30 days and daily aggregate data for at least 90 days
- **FR-004**: Administrators MUST be able to switch between hourly and daily views when examining metrics
- **FR-005**: Administrators MUST be able to view historical metrics as line graphs on the dashboard
- **FR-006**: Administrators MUST be able to select different time ranges for viewing (7 days, 30 days, 90 days)
- **FR-007**: System MUST display current (real-time) metrics alongside historical trends on the same dashboard
- **FR-008**: Graphs MUST show data points with tooltips displaying exact values and timestamps when hovered
- **FR-009**: System MUST handle missing data points by displaying gaps as dotted lines in graphs, with tooltip "이 기간 동안 데이터 수집 실패" when hovered
- **FR-010**: System MUST preserve metric history even when the underlying data changes (e.g., if users are deleted, historical user counts remain accurate)
- **FR-011**: System MUST provide time period comparison functionality allowing admins to overlay two date ranges
- **FR-012**: System MUST calculate and display percentage changes between compared periods
- **FR-013**: System MUST allow exporting metric data to CSV format with a maximum file size of 10MB, automatically downsampling data using LTTB (Largest Triangle Three Buckets) algorithm if necessary to maintain visual fidelity
- **FR-014**: System MUST allow exporting dashboard snapshots to PDF format with a maximum file size of 10MB, automatically downsampling embedded graphs using LTTB algorithm if necessary
- **FR-015**: Metric collection MUST not impact system performance (non-blocking, background task)
- **FR-016**: System MUST automatically clean up metrics older than the retention period to manage storage
- **FR-017**: All metric timestamps MUST be stored in UTC and displayed in admin's local timezone
- **FR-018**: Dashboard MUST show a "Data Collection Status" indicator with the following criteria:
  - **녹색 (정상)**: Last collection completed within 5 minutes AND fewer than 3 failures in the past 24 hours
  - **노란색 (주의)**: 3-10 collection failures in the past 24 hours OR last collection 5-60 minutes ago
  - **빨간색 (오류)**: More than 10 failures in the past 24 hours OR no successful collection for over 1 hour
  - Indicator shows: status color, last successful collection timestamp, recent failure count
- **FR-019**: System MUST automatically retry failed metric collection in the next collection cycle, with a maximum of 3 retry attempts for any missed data point
- **FR-020**: When no historical data exists (new installation), system MUST display empty graphs with message "데이터 수집 중입니다. 첫 데이터는 [next collection time]에 표시됩니다"
- **FR-021**: System MUST automatically downsample data points on the client side to a maximum of 1000 points per graph using LTTB (Largest Triangle Three Buckets) algorithm to ensure responsive rendering while preserving visual characteristics of time-series data

### Key Entities

- **MetricSnapshot**: Represents a point-in-time capture of system metrics, containing timestamp, metric type, and value. Relationships: linked to specific metric types, aggregated into time series for graphing
- **MetricType**: Represents the categories of metrics being tracked (e.g., "active_users", "storage_bytes", "session_count"). Contains metadata like display name, unit of measurement, and graph type preference

**Note**: Export functionality is implemented as a stateless service without persistent MetricExport entity. Export files are temporarily stored with 1-hour expiration (see ExportService in plan.md).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Administrators can view 7 days of historical metrics within 2 seconds of loading the dashboard
- **SC-002**: System successfully collects metrics at configured intervals with 99% reliability (no more than 1% missed collections)
- **SC-003**: Metric collection completes within 5 seconds and does not impact concurrent user operations
- **SC-004**: Administrators can identify trends (increasing/decreasing patterns) within 30 seconds of viewing a metric graph
- **SC-005**: 90% of administrators successfully export metrics data on first attempt without assistance
- **SC-006**: System maintains metric history for 90 days without data loss or corruption
- **SC-007**: Dashboard graphs render any time range within 3 seconds through automatic downsampling (maximum 1000 rendered points)

## Assumptions

- Existing admin dashboard already displays current (real-time) metrics that need historical tracking
- PostgreSQL database has sufficient storage for metric history (estimated ~100KB per day)
- Metrics are system-wide aggregates, not per-admin personalized views
- All admins access the system from the same timezone (local deployment assumption); distributed multi-timezone admin access is out of scope for this feature
- Time series data doesn't require complex analytics (simple line graphs suffice)
- Export functionality uses standard CSV format (comma-delimited, UTF-8 encoded)
- PDF exports use server-side rendering, not client-side screenshot capture
- Metric collection runs as scheduled background task using existing task scheduler
- No requirement for alerting/notifications based on metric thresholds (pure visualization)
- Historical metrics are read-only (no manual editing or adjustment)

## Dependencies

- Existing admin authentication and authorization system
- Current admin dashboard displaying real-time metrics
- Database migration capability for creating metrics storage tables
- Task scheduling system for periodic metric collection
- Charting library in frontend (assumption: will be selected during planning)

## Out of Scope

- Predictive analytics or forecasting based on historical trends
- Real-time streaming metric updates (refresh rate faster than dashboard reload)
- Per-admin customizable dashboards or personalized metric views
- Metric alerting, notifications, or threshold-based triggers
- Integration with external monitoring tools (Prometheus, Grafana, etc.)
- User-level metrics (tracking individual user behavior over time)
- Audit trail for who viewed which metrics when
- Mobile-optimized metric viewing interface
- Multi-timezone support for distributed admin teams (assumes single-location deployment)
- Individual metric drill-down (clicking graph to see detailed breakdown) - consider for future enhancement

import { useEffect, useState } from "react";
import { courseApi } from "../services/courseService";
import { attendanceApi } from "../services/attendanceService";
import { attendanceAnalyticsApi } from "../services/attendanceAnalyticsService";

function RiskBadge({ risk }) {
  const classes = {
    SAFE: "bg-success",
    AT_RISK: "bg-warning text-dark",
    CRITICAL: "bg-danger",
  };
  return <span className={`badge ${classes[risk] || "bg-secondary"}`}>{risk || "—"}</span>;
}

function TrendBadge({ value }) {
  const classes = {
    IMPROVING: "bg-success",
    STABLE: "bg-secondary",
    DECLINING: "bg-danger",
    INSUFFICIENT_DATA: "bg-warning text-dark",
  };
  return <span className={`badge ${classes[value] || "bg-secondary"}`}>{value}</span>;
}

function TrendBars({ points }) {
  if (!points.length) return <div className="text-muted small">No trend data yet.</div>;
  return (
    <div className="d-flex align-items-end gap-1 border-bottom" style={{ height: 150 }}>
      {points.map((point) => (
        <div
          key={point.attendance_session_id}
          className="bg-dark rounded-top flex-fill"
          title={`${point.date}: ${point.running_percentage}% (${point.status})`}
          style={{ height: `${Math.max(4, Math.min(100, Number(point.running_percentage)))}%` }}
        />
      ))}
    </div>
  );
}

export default function StudentAttendanceAnalyticsPage() {
  const [rows, setRows] = useState([]);
  const [analytics, setAnalytics] = useState({});
  const [trends, setTrends] = useState({});
  const [future, setFuture] = useState({});
  const [expanded, setExpanded] = useState("");
  const [policy, setPolicy] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [enrollments, policyResponse] = await Promise.all([
        courseApi.enrollments(),
        attendanceAnalyticsApi.policy(),
      ]);
      const enrolled = enrollments.data.filter(
        (item) => item.status === "enrolled" || item.status === "completed"
      );
      setRows(enrolled);
      setPolicy(policyResponse.data);

      const results = await Promise.all(
        enrolled.map(async (row) => {
          try {
            const [summary, trend] = await Promise.all([
              attendanceAnalyticsApi.mySummary(
                row.course_offering_id,
                future[row.course_offering_id]
              ),
              attendanceAnalyticsApi.myTrend(row.course_offering_id),
            ]);
            return [row.course_offering_id, summary.data, trend.data];
          } catch {
            return [row.course_offering_id, null, null];
          }
        })
      );

      setAnalytics(Object.fromEntries(results.map(([id, summary]) => [id, summary])));
      setTrends(Object.fromEntries(results.map(([id, , trend]) => [id, trend])));
    } catch (e) {
      setError(e.response?.data?.detail || "Could not load attendance analytics");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function refreshOffering(offeringId) {
    try {
      const [summary, trend] = await Promise.all([
        attendanceAnalyticsApi.mySummary(offeringId, future[offeringId]),
        attendanceAnalyticsApi.myTrend(offeringId),
      ]);
      setAnalytics((old) => ({ ...old, [offeringId]: summary.data }));
      setTrends((old) => ({ ...old, [offeringId]: trend.data }));
    } catch (e) {
      setError(e.response?.data?.detail || "Could not refresh analytics");
    }
  }

  if (loading) {
    return <div className="text-center py-5"><div className="spinner-border" /></div>;
  }

  return (
    <div className="container py-4">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h1 className="h3 mb-1">Attendance Analytics</h1>
          <p className="text-muted mb-0">
            Deterministic attendance analysis from your real attendance records.
          </p>
        </div>
        <a className="btn btn-outline-dark" href="/student/attendance">Attendance History</a>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {policy && (
        <div className="alert alert-light border">
          Minimum attendance: <strong>{policy.minimum_required_percentage}%</strong>
          {" · "}Late counts as attended: <strong>{policy.late_counts_as_attended ? "Yes" : "No"}</strong>
          {" · "}Excused in denominator: <strong>{policy.excused_counts_in_denominator ? "Yes" : "No"}</strong>
        </div>
      )}

      <div className="row g-3">
        {rows.map((row) => {
          const id = row.course_offering_id;
          const a = analytics[id];
          const trend = trends[id];
          const isOpen = expanded === id;

          return (
            <div className="col-12" key={row.id}>
              <div className="card shadow-sm">
                <div className="card-body">
                  <div className="d-flex flex-wrap justify-content-between align-items-center gap-3">
                    <div>
                      <div className="small text-muted">Course Offering</div>
                      <div className="fw-semibold text-break">{id}</div>
                    </div>
                    {a && <RiskBadge risk={a.risk} />}
                  </div>

                  {a ? (
                    <>
                      <div className="row g-3 mt-1">
                        <div className="col-sm-6 col-lg-3">
                          <div className="border rounded p-3">
                            <div className="small text-muted">Attendance</div>
                            <div className="fs-3 fw-semibold">{a.attendance_percentage}%</div>
                          </div>
                        </div>
                        <div className="col-sm-6 col-lg-3">
                          <div className="border rounded p-3">
                            <div className="small text-muted">Required</div>
                            <div className="fs-3 fw-semibold">{a.minimum_required_percentage}%</div>
                          </div>
                        </div>
                        <div className="col-sm-6 col-lg-3">
                          <div className="border rounded p-3">
                            <div className="small text-muted">Present / Absent</div>
                            <div className="fs-5 fw-semibold">{a.present} / {a.absent}</div>
                          </div>
                        </div>
                        <div className="col-sm-6 col-lg-3">
                          <div className="border rounded p-3">
                            <div className="small text-muted">Required to Recover</div>
                            <div className="fs-5 fw-semibold">
                              {a.recovery.classes_required == null ? "Not possible" : a.recovery.classes_required}
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="d-flex flex-wrap align-items-center gap-2 mt-3">
                        <span className="small text-muted">Trend:</span>
                        {trend && <TrendBadge value={trend.classification} />}
                        <button
                          className="btn btn-sm btn-outline-dark ms-auto"
                          onClick={() => setExpanded(isOpen ? "" : id)}
                        >
                          {isOpen ? "Hide details" : "Show details"}
                        </button>
                      </div>

                      {isOpen && (
                        <div className="mt-3">
                          <div className="row g-3">
                            <div className="col-lg-8">
                              <div className="border rounded p-3">
                                <div className="fw-semibold mb-2">Running Attendance Trend</div>
                                {trend ? <TrendBars points={trend.points} /> : <div className="text-muted">No trend data.</div>}
                                <div className="small text-muted mt-2">
                                  {trend?.calculation_rule}
                                </div>
                              </div>
                            </div>
                            <div className="col-lg-4">
                              <div className="border rounded p-3 h-100">
                                <div className="fw-semibold mb-2">Recovery</div>
                                <p className="mb-2">
                                  {a.recovery.is_recoverable
                                    ? `You need ${a.recovery.classes_required ?? 0} future attended class(es) to reach the minimum.`
                                    : "The target cannot be reached within the supplied future-class limit."}
                                </p>
                                <label className="form-label small">Future classes available</label>
                                <input
                                  type="number"
                                  min="0"
                                  className="form-control mb-2"
                                  value={future[id] ?? ""}
                                  onChange={(e) => setFuture((old) => ({ ...old, [id]: e.target.value }))}
                                  placeholder="Optional"
                                />
                                <button className="btn btn-dark btn-sm" onClick={() => refreshOffering(id)}>
                                  Recalculate
                                </button>
                                <hr />
                                <div className="small">
                                  Maximum future absences while staying at/above target:
                                  <strong className="ms-1">{a.maximum_absences.maximum_future_absences ?? "Unlimited"}</strong>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="alert alert-light border mt-3 mb-0">
                      No attendance analytics are available for this course yet.
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {!rows.length && (
        <div className="alert alert-info mt-3">No enrolled courses found.</div>
      )}
    </div>
  );
}

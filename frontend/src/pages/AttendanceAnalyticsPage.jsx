import { useEffect, useState } from "react";
import { courseApi } from "../services/courseService";
import { attendanceAnalyticsApi } from "../services/attendanceAnalyticsService";

function RiskBadge({ risk }) {
  const classes = { SAFE: "bg-success", AT_RISK: "bg-warning text-dark", CRITICAL: "bg-danger" };
  return <span className={`badge ${classes[risk] || "bg-secondary"}`}>{risk}</span>;
}

export default function AttendanceAnalyticsPage() {
  const [offerings, setOfferings] = useState([]);
  const [selected, setSelected] = useState("");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function loadOfferings() {
    try {
      const response = await courseApi.offerings();
      setOfferings(response.data);
      if (!selected && response.data.length) setSelected(response.data[0].id);
    } catch (e) {
      setError(e.response?.data?.detail || "Could not load course offerings");
    } finally {
      setLoading(false);
    }
  }

  async function loadAnalytics(id) {
    if (!id) return;
    setError("");
    try {
      const response = await attendanceAnalyticsApi.course(id);
      setData(response.data);
    } catch (e) {
      setData(null);
      setError(e.response?.data?.detail || "Could not load course analytics");
    }
  }

  useEffect(() => { loadOfferings(); }, []);
  useEffect(() => { loadAnalytics(selected); }, [selected]);

  if (loading) return <div className="text-center py-5"><div className="spinner-border" /></div>;

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h1 className="h3 mb-1">Attendance Analytics</h1>
          <p className="text-muted mb-0">Course-level student statistics and deterministic risk classification.</p>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="card shadow-sm mb-3">
        <div className="card-body">
          <label className="form-label">Course Offering</label>
          <select className="form-select" value={selected} onChange={(e) => setSelected(e.target.value)}>
            <option value="">Select course offering</option>
            {offerings.map((o) => <option key={o.id} value={o.id}>{o.id}</option>)}
          </select>
        </div>
      </div>

      {data && (
        <>
          <div className="row g-3 mb-3">
            <div className="col-md-3"><div className="card shadow-sm"><div className="card-body"><div className="small text-muted">Students</div><div className="fs-3">{data.student_count}</div></div></div></div>
            <div className="col-md-3"><div className="card shadow-sm"><div className="card-body"><div className="small text-muted">Average</div><div className="fs-3">{data.course_average_percentage}%</div></div></div></div>
            <div className="col-md-2"><div className="card shadow-sm"><div className="card-body"><div className="small text-muted">Safe</div><div className="fs-3 text-success">{data.safe_count}</div></div></div></div>
            <div className="col-md-2"><div className="card shadow-sm"><div className="card-body"><div className="small text-muted">At Risk</div><div className="fs-3 text-warning">{data.at_risk_count}</div></div></div></div>
            <div className="col-md-2"><div className="card shadow-sm"><div className="card-body"><div className="small text-muted">Critical</div><div className="fs-3 text-danger">{data.critical_count}</div></div></div></div>
          </div>

          <div className="card shadow-sm">
            <div className="card-header bg-white d-flex justify-content-between">
              <strong>Student Analytics</strong>
              <span className="small text-muted">Minimum: {data.minimum_required_percentage}%</span>
            </div>
            <div className="table-responsive">
              <table className="table table-hover align-middle mb-0">
                <thead>
                  <tr><th>Student</th><th>Attendance</th><th>Present</th><th>Absent</th><th>Late</th><th>Risk</th><th>Recovery</th><th>Max Absences</th></tr>
                </thead>
                <tbody>
                  {data.students.map((student) => (
                    <tr key={student.enrollment_id}>
                      <td className="text-break">{student.student_id}</td>
                      <td>{student.attendance_percentage}%</td>
                      <td>{student.present}</td>
                      <td>{student.absent}</td>
                      <td>{student.late}</td>
                      <td><RiskBadge risk={student.risk} /></td>
                      <td>{student.classes_required_to_recover ?? "Not possible"}</td>
                      <td>{student.maximum_future_absences ?? "Unlimited"}</td>
                    </tr>
                  ))}
                  {!data.students.length && <tr><td colSpan="8" className="text-center py-4 text-muted">No enrolled students.</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </>
  );
}

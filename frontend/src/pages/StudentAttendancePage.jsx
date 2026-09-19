import { useEffect, useState } from "react";
import { courseApi } from "../services/courseService";
import { attendanceApi } from "../services/attendanceService";

export default function StudentAttendancePage() {
  const [rows, setRows] = useState([]);
  const [summaries, setSummaries] = useState({});
  const [history, setHistory] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [response, historyResponse] = await Promise.all([courseApi.enrollments(), attendanceApi.myHistory()]);
        setHistory(historyResponse.data);
        const enrollments = response.data.filter((x) => x.status === "enrolled" || x.status === "completed");
        setRows(enrollments);
        const results = await Promise.all(
          enrollments.map(async (row) => {
            try {
              const summary = await attendanceApi.mySummary(row.course_offering_id);
              return [row.course_offering_id, summary.data];
            } catch {
              return [row.course_offering_id, null];
            }
          })
        );
        setSummaries(Object.fromEntries(results));
      } catch (e) {
        setError(e.response?.data?.detail || "Could not load attendance");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <div className="text-center py-5"><div className="spinner-border" /></div>;

  return (
    <div className="container py-4">
      <h1 className="h3">My Attendance</h1>
      <p className="text-muted">Your attendance is calculated by the backend.</p><a className="btn btn-dark mb-3" href="/student/attendance-analytics">Open Attendance Analytics</a>
      {error && <div className="alert alert-danger">{error}</div>}
      <div className="row g-3">
        {rows.map((row) => {
          const s = summaries[row.course_offering_id];
          return (
            <div className="col-md-6 col-xl-4" key={row.id}>
              <div className="card shadow-sm h-100">
                <div className="card-body">
                  <h2 className="h6">Course Offering</h2>
                  <div className="small text-muted mb-3">{row.course_offering_id}</div>
                  {s ? (
                    <>
                      <div className="display-6">{s.attendance_percentage}%</div>
                      <div className="row text-center mt-3">
                        <div className="col"><strong>{s.present}</strong><div className="small text-muted">Present</div></div>
                        <div className="col"><strong>{s.absent}</strong><div className="small text-muted">Absent</div></div>
                        <div className="col"><strong>{s.late}</strong><div className="small text-muted">Late</div></div>
                        <div className="col"><strong>{s.excused}</strong><div className="small text-muted">Excused</div></div>
                      </div>
                      <hr />
                      <div className="small">Total sessions: {s.total_sessions}</div>
                    </>
                  ) : <div className="text-muted">No attendance data yet.</div>}
                </div>
              </div>
            </div>
          );
        })}
        {!rows.length && <div className="col-12"><div className="alert alert-info">No enrolled courses found.</div></div>}
      </div>

      <div className="card shadow-sm mt-4">
        <div className="card-header bg-white"><strong>Attendance History</strong></div>
        <div className="table-responsive">
          <table className="table mb-0">
            <thead><tr><th>Date</th><th>Course Offering</th><th>Topic</th><th>Status</th></tr></thead>
            <tbody>
              {history.map((item) => (
                <tr key={item.attendance_session_id}>
                  <td>{item.session_date}</td>
                  <td>{item.course_offering_id}</td>
                  <td>{item.topic || "—"}</td>
                  <td>{item.status}</td>
                </tr>
              ))}
              {!history.length && <tr><td colSpan="4" className="text-center py-4 text-muted">No attendance records yet.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

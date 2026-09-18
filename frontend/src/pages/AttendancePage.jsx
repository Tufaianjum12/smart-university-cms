import { useEffect, useMemo, useState } from "react";
import { courseApi } from "../services/courseService";
import { attendanceApi } from "../services/attendanceService";

const emptyForm = {
  course_offering_id: "",
  session_date: new Date().toISOString().slice(0, 10),
  start_time: "",
  end_time: "",
  topic: "",
  notes: "",
};

const statuses = ["present", "absent", "late", "excused"];

export default function AttendancePage() {
  const [offerings, setOfferings] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [selectedOffering, setSelectedOffering] = useState("");
  const [selectedSession, setSelectedSession] = useState(null);
  const [students, setStudents] = useState([]);
  const [marks, setMarks] = useState({});
  const [form, setForm] = useState(emptyForm);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const selected = useMemo(
    () => offerings.find((o) => o.id === selectedOffering),
    [offerings, selectedOffering]
  );

  async function loadOfferings() {
    setLoading(true);
    setError("");
    try {
      const response = await courseApi.offerings();
      setOfferings(response.data);
      if (response.data.length && !selectedOffering) {
        setSelectedOffering(response.data[0].id);
      }
    } catch (e) {
      setError(e.response?.data?.detail || "Could not load course offerings");
    } finally {
      setLoading(false);
    }
  }

  async function loadHistory(offeringId = selectedOffering) {
    if (!offeringId) return;
    try {
      const response = await attendanceApi.sessions({
        course_offering_id: offeringId,
      });
      setSessions(response.data);
      setHistory(response.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Could not load attendance history");
    }
  }

  useEffect(() => {
    loadOfferings();
  }, []);

  useEffect(() => {
    if (selectedOffering) loadHistory(selectedOffering);
  }, [selectedOffering]);

  async function createSession(e) {
    e.preventDefault();
    setError("");
    setMessage("");
    try {
      const response = await attendanceApi.createSession({
        ...form,
        course_offering_id: selectedOffering,
        start_time: form.start_time || null,
        end_time: form.end_time || null,
        topic: form.topic || null,
        notes: form.notes || null,
      });
      setSelectedSession(response.data);
      setForm({ ...emptyForm, course_offering_id: selectedOffering });
      await loadSession(response.data);
      await loadHistory(selectedOffering);
      setMessage("Attendance session created.");
    } catch (e) {
      setError(e.response?.data?.detail || "Could not create attendance session");
    }
  }

  async function loadSession(session) {
    setError("");
    try {
      const [enrollmentResponse, recordResponse] = await Promise.all([
        attendanceApi.sessionEnrollments(session.id),
        attendanceApi.records(session.id),
      ]);
      setSelectedSession(session);
      setStudents(enrollmentResponse.data);
      const next = {};
      for (const row of enrollmentResponse.data) next[row.enrollment_id] = "present";
      for (const record of recordResponse.data) next[record.enrollment_id] = record.status;
      setMarks(next);
    } catch (e) {
      setError(e.response?.data?.detail || "Could not load attendance records");
    }
  }

  function markAll(status) {
    const next = {};
    for (const row of students) next[row.enrollment_id] = status;
    setMarks(next);
  }

  async function saveAttendance() {
    if (!selectedSession || !students.length) return;
    setSaving(true);
    setError("");
    setMessage("");
    try {
      await attendanceApi.markBulk(selectedSession.id, {
        records: students.map((student) => ({
          enrollment_id: student.enrollment_id,
          status: marks[student.enrollment_id] || "present",
        })),
      });
      await loadSession(selectedSession);
      setMessage("Attendance saved successfully.");
    } catch (e) {
      setError(e.response?.data?.detail || "Could not save attendance");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <div className="text-center py-5"><div className="spinner-border" /></div>;
  }

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h1 className="h3 mb-1">Attendance</h1>
          <p className="text-muted mb-0">Create class sessions and mark enrolled students.</p>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}
      {message && <div className="alert alert-success">{message}</div>}

      <div className="card shadow-sm mb-4">
        <div className="card-body">
          <label className="form-label">Course Offering</label>
          <select className="form-select mb-4" value={selectedOffering}
            onChange={(e) => { setSelectedOffering(e.target.value); setSelectedSession(null); }}>
            <option value="">Select course offering</option>
            {offerings.map((o) => <option key={o.id} value={o.id}>{o.id}</option>)}
          </select>

          <form className="row g-3" onSubmit={createSession}>
            <div className="col-md-3">
              <label className="form-label">Date</label>
              <input type="date" className="form-control" required value={form.session_date}
                onChange={(e) => setForm({ ...form, session_date: e.target.value })} />
            </div>
            <div className="col-md-2">
              <label className="form-label">Start</label>
              <input type="time" className="form-control" value={form.start_time}
                onChange={(e) => setForm({ ...form, start_time: e.target.value })} />
            </div>
            <div className="col-md-2">
              <label className="form-label">End</label>
              <input type="time" className="form-control" value={form.end_time}
                onChange={(e) => setForm({ ...form, end_time: e.target.value })} />
            </div>
            <div className="col-md-5">
              <label className="form-label">Topic</label>
              <input className="form-control" placeholder="e.g. Linked Lists" value={form.topic}
                onChange={(e) => setForm({ ...form, topic: e.target.value })} />
            </div>
            <div className="col-12">
              <button className="btn btn-dark" disabled={!selectedOffering}>Create Session</button>
            </div>
          </form>
        </div>
      </div>

      <div className="card shadow-sm mb-4">
        <div className="card-header bg-white">
          <strong>Attendance History</strong>
        </div>
        <div className="table-responsive">
          <table className="table mb-0">
            <thead><tr><th>Date</th><th>Topic</th><th>Status</th><th /></tr></thead>
            <tbody>
              {history.map((s) => (
                <tr key={s.id}>
                  <td>{s.session_date}</td>
                  <td>{s.topic || "—"}</td>
                  <td>{s.status}</td>
                  <td><button className="btn btn-sm btn-outline-dark" onClick={() => loadSession(s)}>Open</button></td>
                </tr>
              ))}
              {!history.length && <tr><td colSpan="4" className="text-center py-4 text-muted">No sessions yet.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>

      {selectedSession && (
        <div className="card shadow-sm">
          <div className="card-header bg-white d-flex justify-content-between align-items-center">
            <strong>Mark Attendance — {selectedSession.session_date}</strong>
            <div className="d-flex gap-2">
              <button className="btn btn-sm btn-outline-success" onClick={() => markAll("present")}>Mark All Present</button>
              <button className="btn btn-sm btn-dark" disabled={saving || !students.length} onClick={saveAttendance}>
                {saving ? "Saving..." : "Save Attendance"}
              </button>
            </div>
          </div>
          <div className="table-responsive">
            <table className="table align-middle mb-0">
              <thead><tr><th>Student</th><th>Student No.</th><th>Status</th></tr></thead>
              <tbody>
                {students.map((student) => (
                  <tr key={student.enrollment_id}>
                    <td>{student.student_name || "Student"}</td>
                    <td>{student.student_number}</td>
                    <td>
                      <select className="form-select" value={marks[student.enrollment_id] || "present"}
                        onChange={(e) => setMarks({ ...marks, [student.enrollment_id]: e.target.value })}>
                        {statuses.map((status) => <option key={status} value={status}>{status.toUpperCase()}</option>)}
                      </select>
                    </td>
                  </tr>
                ))}
                {!students.length && <tr><td colSpan="3" className="text-center py-4 text-muted">No active enrollments.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}

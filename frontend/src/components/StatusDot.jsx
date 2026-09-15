// Small reusable status indicator — a colored dot plus a label.
// Used anywhere the app needs to show "this thing is up/down", starting
// with the Phase 1 status page and reused by future dashboards.

export default function StatusDot({ ok, label }) {
  const color = ok ? "#2f8f5b" : "#c1443c";
  return (
    <span className="d-inline-flex align-items-center gap-2">
      <span
        style={{
          width: 10,
          height: 10,
          borderRadius: "50%",
          backgroundColor: color,
          display: "inline-block",
        }}
      />
      <span>{label}</span>
    </span>
  );
}

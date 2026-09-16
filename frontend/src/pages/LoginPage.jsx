import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
export default function LoginPage() {
  const { user, login } = useAuth(); const nav=useNavigate(); const [email,setEmail]=useState(""); const [password,setPassword]=useState(""); const [error,setError]=useState(""); const [busy,setBusy]=useState(false);
  if(user) return <Navigate to="/admin" replace />;
  async function submit(e){e.preventDefault();setError("");setBusy(true);try{const u=await login(email,password);nav(u.role==="super_admin"?"/admin/organizations":"/admin");}catch(err){setError(err.response?.data?.detail||"Unable to sign in");}finally{setBusy(false)}}
  return <div className="container py-5" style={{maxWidth:480}}><div className="card shadow-sm border-0"><div className="card-body p-4"><h2 className="mb-1">Smart University CMS</h2><p className="text-muted">Sign in to administration</p>{error&&<div className="alert alert-danger">{error}</div>}<form onSubmit={submit}><label className="form-label">Email</label><input className="form-control mb-3" type="email" value={email} onChange={e=>setEmail(e.target.value)} required/><label className="form-label">Password</label><input className="form-control mb-4" type="password" value={password} onChange={e=>setPassword(e.target.value)} required/><button className="btn btn-dark w-100" disabled={busy}>{busy?<span className="spinner-border spinner-border-sm"/>:"Sign in"}</button></form></div></div></div>;
}

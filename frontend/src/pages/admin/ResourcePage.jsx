import {useEffect,useState} from "react";
import {cms} from "../../services/cmsService";

const configs={
 campuses:{title:"Campuses",fields:[["name","Name"],["code","Code"],["address","Address"]]},
 departments:{title:"Departments",fields:[["name","Name"],["code","Code"],["campus_id","Campus"]],relations:{campus_id:"campuses"}},
 programs:{title:"Programs",fields:[["name","Name"],["code","Code"],["department_id","Department"],["duration_years","Duration years"]],relations:{department_id:"departments"}},
 "academic-sessions":{title:"Academic Sessions",fields:[["name","Name"],["code","Code"],["start_date","Start date"],["end_date","End date"],["is_current","Current"]]},
 semesters:{title:"Semesters",fields:[["name","Name"],["code","Code"],["academic_session_id","Academic Session"],["start_date","Start date"],["end_date","End date"]],relations:{academic_session_id:"academic-sessions"}},
 sections:{title:"Sections",fields:[["section_code","Section code"],["program_id","Program"],["semester_id","Semester"],["course_id","Course (optional)"],["capacity","Capacity"]],relations:{program_id:"programs",semester_id:"semesters"}},
 classrooms:{title:"Classrooms",fields:[["room_code","Room number/code"],["building","Building"],["campus_id","Campus"],["capacity","Capacity"]],relations:{campus_id:"campuses"}}
};

function display(row){return row.name||row.code||row.section_code||row.room_code||row.id}

export default function ResourcePage({resource}){
 const c=configs[resource]; const [rows,setRows]=useState([]); const [form,setForm]=useState({}); const [editing,setEditing]=useState(null); const [busy,setBusy]=useState(false); const [error,setError]=useState(""); const [options,setOptions]=useState({});
 async function load(){setError("");try{setRows((await cms.list(resource)).data)}catch(e){setError(e.response?.data?.detail||"Could not load data")}}
 async function loadOptions(){if(!c.relations)return;const entries=await Promise.all(Object.entries(c.relations).map(async([field,endpoint])=>[field,(await cms.list(endpoint)).data]));setOptions(Object.fromEntries(entries))}
 useEffect(()=>{load();loadOptions()},[resource]);
 function change(k,v){setForm(f=>({...f,[k]:v}))}
 async function submit(e){e.preventDefault();setBusy(true);setError("");try{const data={...form};for(const k of ["duration_years","capacity"])if(data[k]==="")delete data[k];for(const k of Object.keys(c.relations||{}))if(data[k]==="")delete data[k];if(editing)await cms.update(resource,editing,data);else await cms.create(resource,data);setForm({});setEditing(null);await load();await loadOptions()}catch(e){setError(e.response?.data?.detail||"Save failed")}finally{setBusy(false)}}
 async function remove(id){if(!window.confirm("Archive this record?"))return;try{await cms.remove(resource,id);await load()}catch(e){setError(e.response?.data?.detail||"Archive failed")}}
 function edit(row){const x={};c.fields.forEach(([k])=>x[k]=row[k]??"");setEditing(row.id);setForm(x)}
 return <><div className="d-flex justify-content-between align-items-center mb-3"><div><h1 className="h3 mb-1">{c.title}</h1><p className="text-muted mb-0">Live tenant-scoped data</p></div>{editing&&<button className="btn btn-outline-secondary" onClick={()=>{setEditing(null);setForm({})}}>Cancel edit</button>}</div>
 {error&&<div className="alert alert-danger">{error}</div>}
 <div className="card shadow-sm mb-4"><div className="card-header">{editing?"Edit":"Create"} {c.title.replace(/s$/," ")}</div><form onSubmit={submit} className="card-body row g-3">
 {c.fields.map(([k,label])=><div className="col-md-4" key={k}><label className="form-label">{label}</label>{k==="is_current"?<select className="form-select" value={String(form[k]??false)} onChange={e=>change(k,e.target.value==="true")}><option value="false">No</option><option value="true">Yes</option></select>:c.relations?.[k]?<select className="form-select" value={form[k]??""} onChange={e=>change(k,e.target.value)} required><option value="">Select {label}</option>{(options[k]||[]).map(o=><option key={o.id} value={o.id}>{display(o)}</option>)}</select>:<input className="form-control" type={k==="duration_years"||k==="capacity"?"number":k.endsWith("_date")?"date":"text"} value={form[k]??""} onChange={e=>change(k,e.target.value)} required={!['address','building','course_id','duration_years','capacity','start_date','end_date'].includes(k)}/>}</div>)}
 <div className="col-12"><button className="btn btn-dark" disabled={busy}>{busy?"Saving…":editing?"Update":"Create"}</button></div></form></div>
 <div className="card shadow-sm"><div className="table-responsive"><table className="table table-hover align-middle mb-0"><thead><tr>{c.fields.map(([,l])=><th key={l}>{l}</th>)}<th>Actions</th></tr></thead><tbody>{rows.length===0?<tr><td colSpan={c.fields.length+1} className="text-center text-muted py-4">No records found.</td></tr>:rows.map(r=><tr key={r.id}>{c.fields.map(([k])=><td key={k}>{typeof r[k]==="boolean"?(r[k]?"Yes":"No"):String(r[k]??"—")}</td>)}<td className="text-nowrap"><button className="btn btn-sm btn-outline-secondary me-2" onClick={()=>edit(r)}>Edit</button><button className="btn btn-sm btn-outline-danger" onClick={()=>remove(r.id)}>Archive</button></td></tr>)}</tbody></table></div></div></>;
}

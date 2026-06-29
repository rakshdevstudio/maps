import { useState, useEffect, useRef } from "react";
import { X, Clock, CheckCircle2, AlertTriangle, AlertOctagon, Upload, Download, Trash2, Calendar, CheckSquare, Target } from "lucide-react";
import { format, formatDistanceToNow } from "date-fns";
import { getProject, updateProject, updateMilestone, createTask, updateTask, uploadProjectFile, getProjectFileUrl, deleteProjectFile, getAccountGrowthOpportunities } from "@/services/api";
import { toast } from "sonner";

export default function ProjectDetail({ projectId, onClose }) {
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");
  const [aiGrowthOpps, setAiGrowthOpps] = useState([]);
  const fileInputRef = useRef(null);

  const fetchProjectDetail = async () => {
    try {
      const data = await getProject(projectId);
      setProject(data);
      if (data.completion_percentage >= 80) {
        getAccountGrowthOpportunities().then(opps => {
          // Filter for this project, although the API has a by-project endpoint, let's use the one we have or filter locally.
          // Wait, the API endpoint is `/ai/account-growth` which gets top 20 globally. 
          // Actually, I wrote an endpoint `/ai/account-growth/{project_id}` in ai_router.py. I should add that to api.js or use it.
          // In api.js we only have getAccountGrowthOpportunities() which fetches all. Let's just fetch all and filter, or change api.js.
          // Let's change api.js to accept an optional projectId.
        }).catch(() => {});
      }
    } catch (err) {
      toast.error("Failed to load project details");
      onClose();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjectDetail();
  }, [projectId]);

  const handleTaskStatusChange = async (taskId, newStatus, currentMilestoneId) => {
    try {
      await updateTask(projectId, taskId, { status: newStatus });
      fetchProjectDetail(); // Refresh to get recalculated project health & completion
    } catch (err) {}
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      toast.info("Uploading file...");
      await uploadProjectFile(projectId, file);
      toast.success("File uploaded successfully");
      fetchProjectDetail();
    } catch (err) {}
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleDeleteFile = async (fileId) => {
    if (!confirm("Delete this file?")) return;
    try {
      await deleteProjectFile(fileId);
      toast.success("File deleted");
      fetchProjectDetail();
    } catch (err) {}
  };

  if (loading || !project) {
    return (
      <div className="fixed inset-y-0 right-0 z-50 w-full max-w-3xl border-l border-white/10 bg-slate-950/95 backdrop-blur-2xl shadow-2xl flex items-center justify-center">
        <div className="text-slate-400">Loading Project Delivery Details...</div>
      </div>
    );
  }

  const getHealthIcon = (health) => {
    if (health === 'critical') return <AlertOctagon className="h-5 w-5 text-red-400" />;
    if (health === 'at_risk') return <AlertTriangle className="h-5 w-5 text-amber-400" />;
    return <CheckCircle2 className="h-5 w-5 text-emerald-400" />;
  };

  const TABS = [
    { id: "overview", label: "Overview" },
    { id: "milestones", label: "Milestones" },
    { id: "tasks", label: "Tasks" },
    { id: "files", label: "File Vault" },
    { id: "timeline", label: "Timeline" },
  ];

  if (project.completion_percentage >= 80) {
    TABS.push({ id: "retainers", label: "Growth Opportunities" });
  }

  return (
    <div className="fixed inset-y-0 right-0 z-50 flex w-full max-w-4xl flex-col border-l border-white/10 bg-slate-950/95 shadow-2xl backdrop-blur-3xl animate-in slide-in-from-right duration-300">
      
      {/* Header */}
      <header className="flex items-center justify-between border-b border-white/10 p-6 bg-slate-900/50">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium capitalize 
              ${project.health_status === 'critical' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 
                project.health_status === 'at_risk' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 
                'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'}`}>
              {getHealthIcon(project.health_status)}
              {project.health_status.replace('_', ' ')}
            </span>
            <span className="text-xs text-slate-500 uppercase tracking-widest">{project.status}</span>
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">{project.project_name}</h2>
          <p className="text-sm text-slate-400 mt-1">{project.client_name} • ${project.project_value.toLocaleString()}</p>
        </div>
        <button onClick={onClose} className="rounded-full p-2 hover:bg-white/10 text-slate-400 hover:text-white transition">
          <X className="h-6 w-6" />
        </button>
      </header>

      {/* Tabs */}
      <div className="border-b border-white/10 px-6 pt-4 bg-slate-900/30">
        <div className="flex gap-6 overflow-x-auto">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`border-b-2 pb-3 text-sm font-medium transition whitespace-nowrap ${
                activeTab === tab.id
                  ? "border-cyan-400 text-cyan-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              {tab.label} {tab.id === 'retainers' && <span className="ml-2 rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] text-emerald-400">New</span>}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 scrollbar-hide">
        
        {/* OVERVIEW TAB */}
        {activeTab === "overview" && (
          <div className="space-y-8">
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-xl border border-white/10 bg-white/5 p-5">
                <p className="text-xs uppercase tracking-wider text-slate-500">Overall Progress</p>
                <div className="mt-4 flex items-end justify-between">
                  <span className="text-4xl font-bold text-white">{project.completion_percentage}%</span>
                  <span className="text-sm text-slate-400">{project.milestones.filter(m => m.status === 'completed').length} / {project.milestones.length} Milestones</span>
                </div>
                <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-slate-800">
                  <div className="h-full rounded-full bg-cyan-500 transition-all duration-1000" style={{ width: `${project.completion_percentage}%` }} />
                </div>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 p-5">
                <p className="text-xs uppercase tracking-wider text-slate-500">Timeline</p>
                <div className="mt-4 space-y-3">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-slate-400 flex items-center gap-2"><Calendar className="h-4 w-4" /> Start Date</span>
                    <span className="text-white">{format(new Date(project.start_date + 'Z'), 'MMM d, yyyy')}</span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-slate-400 flex items-center gap-2"><Target className="h-4 w-4" /> Target Date</span>
                    <span className="text-white">{project.target_completion_date ? format(new Date(project.target_completion_date + 'Z'), 'MMM d, yyyy') : 'Not Set'}</span>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-medium text-white mb-4">Milestone Progress</h3>
              <div className="space-y-3">
                {project.milestones.map((ms, idx) => (
                  <div key={ms.id} className="rounded-lg border border-white/10 bg-white/5 p-4 flex items-center gap-4">
                    <div className="flex-shrink-0 h-8 w-8 rounded-full bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-400">{idx + 1}</div>
                    <div className="flex-1">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-sm font-medium text-white">{ms.title}</span>
                        <span className="text-xs text-slate-400">{ms.completion_percentage}%</span>
                      </div>
                      <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
                        <div className={`h-full rounded-full ${ms.completion_percentage === 100 ? 'bg-emerald-500' : 'bg-cyan-500'}`} style={{ width: `${ms.completion_percentage}%` }} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* MILESTONES TAB */}
        {activeTab === "milestones" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-white">Project Milestones</h3>
            </div>
            <div className="space-y-4">
              {project.milestones.map((ms, idx) => (
                <div key={ms.id} className="rounded-xl border border-white/10 bg-slate-900/50 p-5">
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center gap-3">
                      <div className="flex-shrink-0 h-10 w-10 rounded-full bg-slate-800 flex items-center justify-center text-sm font-bold text-slate-400">
                        {idx + 1}
                      </div>
                      <div>
                        <h4 className="font-medium text-white text-base">{ms.title}</h4>
                        <p className="text-sm text-slate-400 mt-1">{ms.description}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize
                        ${ms.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' :
                          ms.status === 'in_progress' ? 'bg-cyan-500/10 text-cyan-400' :
                          'bg-slate-500/10 text-slate-400'}`}>
                        {ms.status.replace('_', ' ')}
                      </span>
                      <select
                        value={ms.status}
                        onChange={async (e) => {
                          try {
                            await updateMilestone(projectId, ms.id, { status: e.target.value });
                            fetchProjectDetail();
                          } catch (err) {}
                        }}
                        className="bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm text-slate-300 outline-none focus:border-cyan-500 transition"
                      >
                        <option value="pending">Pending</option>
                        <option value="in_progress">In Progress</option>
                        <option value="completed">Completed</option>
                      </select>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="flex-1 h-2 overflow-hidden rounded-full bg-slate-800">
                      <div className={`h-full rounded-full transition-all duration-500 ${ms.completion_percentage === 100 ? 'bg-emerald-500' : 'bg-cyan-500'}`} style={{ width: `${ms.completion_percentage}%` }} />
                    </div>
                    <span className="text-sm text-slate-400 w-12 text-right">{ms.completion_percentage}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TASKS TAB */}
        {activeTab === "tasks" && (
          <div className="space-y-8">
            {project.milestones.map(ms => {
              const msTasks = ms.tasks || [];
              if (msTasks.length === 0) return null;
              
              return (
                <div key={ms.id} className="rounded-xl border border-white/10 bg-slate-900/50 overflow-hidden">
                  <div className="border-b border-white/10 bg-white/5 px-4 py-3 flex justify-between items-center">
                    <h4 className="font-medium text-white text-sm">{ms.title}</h4>
                    <span className="text-xs bg-slate-800 text-slate-300 px-2 py-1 rounded-full">{ms.completion_percentage}%</span>
                  </div>
                  <div className="divide-y divide-white/5">
                    {msTasks.map(task => (
                      <div key={task.id} className="p-4 flex items-center justify-between group hover:bg-white/5 transition">
                        <div className="flex items-center gap-3">
                          <CheckSquare className={`h-5 w-5 ${task.status === 'completed' ? 'text-emerald-500' : 'text-slate-600'}`} />
                          <div>
                            <p className={`text-sm ${task.status === 'completed' ? 'text-slate-400 line-through' : 'text-white'}`}>{task.title}</p>
                            <p className="text-xs text-slate-500 capitalize">{task.priority} Priority</p>
                          </div>
                        </div>
                        <select 
                          value={task.status}
                          onChange={(e) => handleTaskStatusChange(task.id, e.target.value, ms.id)}
                          className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-slate-300 outline-none"
                        >
                          <option value="backlog">Backlog</option>
                          <option value="todo">Todo</option>
                          <option value="in_progress">In Progress</option>
                          <option value="review">Review</option>
                          <option value="completed">Completed</option>
                        </select>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* FILES TAB */}
        {activeTab === "files" && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium text-white">Project File Vault</h3>
              <input type="file" ref={fileInputRef} onChange={handleFileUpload} className="hidden" />
              <button 
                onClick={() => fileInputRef.current?.click()}
                className="flex items-center gap-2 bg-cyan-500 hover:bg-cyan-600 text-slate-950 px-4 py-2 rounded-lg text-sm font-medium transition"
              >
                <Upload className="h-4 w-4" /> Upload File
              </button>
            </div>
            
            {project.files.length === 0 ? (
              <div className="text-center py-12 border border-dashed border-white/10 rounded-xl">
                <p className="text-slate-400">No files uploaded yet.</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4">
                {project.files.map(file => (
                  <div key={file.id} className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 transition">
                    <div className="flex flex-col overflow-hidden">
                      <span className="text-sm font-medium text-white truncate pr-4">{file.filename}</span>
                      <span className="text-xs text-slate-400">{Math.round(file.file_size / 1024)} KB • {formatDistanceToNow(new Date(file.created_at + 'Z'), {addSuffix: true})}</span>
                    </div>
                    <div className="flex gap-2 shrink-0">
                      <a href={getProjectFileUrl(file.id)} target="_blank" rel="noreferrer" className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded transition">
                        <Download className="h-4 w-4" />
                      </a>
                      <button onClick={() => handleDeleteFile(file.id)} className="p-2 bg-slate-800 hover:bg-red-500/20 hover:text-red-400 text-slate-300 rounded transition">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TIMELINE TAB */}
        {activeTab === "timeline" && (
          <div className="relative pl-4 space-y-8 before:absolute before:inset-y-0 before:left-[23px] before:w-px before:bg-white/10">
            {project.events.map((event) => (
              <div key={event.id} className="relative flex gap-4">
                <div className="relative z-10 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-cyan-500 ring-4 ring-slate-950 mt-1" />
                <div className="flex-1 rounded-xl border border-white/10 bg-white/5 p-4">
                  <div className="flex justify-between items-start mb-1">
                    <p className="text-sm font-medium text-white capitalize">{event.event_type.replace(/_/g, ' ')}</p>
                    <time className="text-xs text-slate-400 flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatDistanceToNow(new Date(event.created_at + 'Z'), { addSuffix: true })}
                    </time>
                  </div>
                  {event.description && <p className="text-sm text-slate-300 mt-2">{event.description}</p>}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* RETAINERS TAB */}
        {activeTab === "retainers" && (
          <div className="space-y-6">
            <div className="bg-gradient-to-br from-cyan-500/10 to-blue-500/5 border border-cyan-500/20 p-5 rounded-2xl relative overflow-hidden">
              <div className="absolute top-0 right-0 p-12 bg-cyan-500/10 blur-[40px] rounded-full pointer-events-none" />
              <h3 className="text-cyan-400 font-bold flex items-center gap-2 mb-2 relative z-10"><Target className="h-5 w-5" /> AI Account Manager</h3>
              <p className="text-sm text-cyan-100/70 relative z-10">Autonomous growth opportunities detected based on project completion and original audit data.</p>
            </div>
            
            <div className="grid gap-4">
              {aiGrowthOpps.length > 0 ? (
                aiGrowthOpps.map(opp => (
                  <div key={opp.id} className="p-5 rounded-2xl border border-white/10 bg-white/[0.02] shadow-lg">
                    <div className="flex justify-between items-start mb-3">
                      <h4 className="text-lg font-bold text-white">{opp.opportunity_type}</h4>
                      <span className="text-cyan-400 font-bold bg-cyan-400/10 px-3 py-1 rounded-full text-xs uppercase tracking-wider">{opp.confidence_score}% Match</span>
                    </div>
                    <p className="text-sm text-slate-300 mb-4">{opp.rationale}</p>
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-2 rounded-full bg-emerald-500"></div>
                      <span className="text-sm font-medium text-emerald-400">{opp.expected_outcome}</span>
                    </div>
                  </div>
                ))
              ) : project.retainer_recommendations.length > 0 ? (
                project.retainer_recommendations.map(rec => (
                  <div key={rec.id} className="p-5 rounded-2xl border border-white/10 bg-white/[0.02] shadow-lg">
                    <div className="flex justify-between items-start mb-3">
                      <h4 className="text-lg font-bold text-white">{rec.title}</h4>
                      <span className="text-emerald-400 font-bold bg-emerald-400/10 px-3 py-1 rounded-full text-xs">${rec.monthly_value.toLocaleString()}/mo</span>
                    </div>
                    <p className="text-sm text-slate-300 mb-4">{rec.description}</p>
                    <div className="bg-white/5 p-3 rounded-xl text-sm text-slate-400 italic">
                      <span className="font-semibold text-slate-300 not-italic">Rationale: </span>{rec.rationale}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-12">
                  <p className="text-slate-500 text-sm">No growth opportunities identified yet. Make sure project is 80% complete and AI Orchestration has run.</p>
                </div>
              )}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

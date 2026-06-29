import { useState, useEffect } from "react";
import { formatDistanceToNow, format } from "date-fns";
import { getProjects } from "@/services/api";
import { FiSearch, FiFilter } from "react-icons/fi";
import { CheckCircle2, AlertTriangle, AlertOctagon } from "lucide-react";
import ProjectDetail from "@/components/ProjectDetail";

export default function Projects() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("active");
  const [healthFilter, setHealthFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [selectedProjectId, setSelectedProjectId] = useState(null);

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const data = await getProjects({ 
        status: statusFilter === "all" ? "" : statusFilter,
        health: healthFilter === "all" ? "" : healthFilter,
        search: search
      });
      setProjects(data);
    } catch (err) {
      // Handled
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [statusFilter, healthFilter]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchProjects();
    }, 500);
    return () => clearTimeout(timer);
  }, [search]);

  const getHealthIcon = (health) => {
    if (health === 'critical') return <AlertOctagon className="h-4 w-4 text-red-400" />;
    if (health === 'at_risk') return <AlertTriangle className="h-4 w-4 text-amber-400" />;
    return <CheckCircle2 className="h-4 w-4 text-emerald-400" />;
  };

  const getHealthBadge = (health) => {
    if (health === 'critical') return "bg-red-500/10 text-red-400 border border-red-500/20";
    if (health === 'at_risk') return "bg-amber-500/10 text-amber-400 border border-amber-500/20";
    return "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
  };

  return (
    <div className="space-y-6 relative h-full">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white tracking-tight">Delivery Command Center</h1>
        <div className="flex items-center gap-3">
          <div className="relative">
            <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search projects..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-cyan-500 w-64"
            />
          </div>
          <select
            className="rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium text-white shadow-sm outline-none focus:border-cyan-500"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="on_hold">On Hold</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
          <select
            className="rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium text-white shadow-sm outline-none focus:border-cyan-500"
            value={healthFilter}
            onChange={(e) => setHealthFilter(e.target.value)}
          >
            <option value="all">All Health</option>
            <option value="healthy">Healthy</option>
            <option value="at_risk">At Risk</option>
            <option value="critical">Critical</option>
          </select>
        </div>
      </div>

      <div className="rounded-xl border border-white/10 bg-slate-900/50 p-6 backdrop-blur-xl shadow-2xl">
        {loading ? (
          <div className="flex h-32 items-center justify-center text-slate-400">Loading delivery pipeline...</div>
        ) : projects.length === 0 ? (
          <div className="flex h-32 items-center justify-center text-slate-400">No active projects found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-800/50 text-xs font-semibold uppercase text-slate-400">
                <tr>
                  <th className="px-4 py-3">Project</th>
                  <th className="px-4 py-3">Client</th>
                  <th className="px-4 py-3">Value</th>
                  <th className="px-4 py-3">Health</th>
                  <th className="px-4 py-3 w-48">Progress</th>
                  <th className="px-4 py-3">Due Date</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {projects.map((proj) => (
                  <tr 
                    key={proj.id} 
                    className="hover:bg-white/5 transition-colors cursor-pointer group"
                    onClick={() => setSelectedProjectId(proj.id)}
                  >
                    <td className="px-4 py-4">
                      <div className="font-medium text-white group-hover:text-cyan-400 transition-colors">{proj.project_name}</div>
                      <div className="text-xs text-slate-500">Started {formatDistanceToNow(new Date(proj.start_date + 'Z'), { addSuffix: true })}</div>
                    </td>
                    <td className="px-4 py-4 text-slate-300">
                      {proj.client_name}
                    </td>
                    <td className="px-4 py-4 font-medium text-emerald-400">
                      ${proj.project_value.toLocaleString()}
                    </td>
                    <td className="px-4 py-4">
                      <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium capitalize ${getHealthBadge(proj.health_status)}`}>
                        {getHealthIcon(proj.health_status)}
                        {proj.health_status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-slate-800 rounded-full h-1.5">
                          <div 
                            className={`h-1.5 rounded-full transition-all duration-500 ${proj.completion_percentage === 100 ? 'bg-emerald-500' : 'bg-cyan-500'}`} 
                            style={{ width: `${proj.completion_percentage}%` }}
                          ></div>
                        </div>
                        <span className="text-xs text-slate-400 w-8">{proj.completion_percentage}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-4 text-slate-300">
                      {proj.target_completion_date ? format(new Date(proj.target_completion_date + 'Z'), 'MMM d, yyyy') : 'No Date Set'}
                    </td>
                    <td className="px-4 py-4">
                      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize
                        ${proj.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' :
                          proj.status === 'active' ? 'bg-blue-500/10 text-blue-400' :
                          'bg-slate-500/10 text-slate-400'}`}>
                        {proj.status.replace('_', ' ')}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedProjectId && (
        <ProjectDetail 
          projectId={selectedProjectId} 
          onClose={() => {
            setSelectedProjectId(null);
            fetchProjects(); // refresh table data on close
          }} 
        />
      )}
    </div>
  );
}

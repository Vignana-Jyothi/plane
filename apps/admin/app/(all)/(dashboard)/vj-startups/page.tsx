"use client"

import React, { useState, useEffect } from "react";
import useSWR, { mutate as globalMutate } from "swr";
import { PageWrapper } from "@/components/common/page-wrapper";
import { Button } from "@plane/propel/button";
import { CreateStartupModal } from "@/components/vj-startups/create-startup-modal";
import { VJStartupsService } from "@/services/vj-startups.service";
import { Search, ChevronLeft, ChevronRight, ExternalLink, Shield, Lightbulb, AlertCircle } from "lucide-react";

const vjStartupsService = new VJStartupsService();

const STAGE_LABELS: Record<number, string> = {
  1: "Idea", 2: "Research", 3: "Prototype", 4: "MVP",
  5: "Beta", 6: "Launch", 7: "Growth", 8: "Scale", 9: "Mature"
};

export default function VJStartupsDashboard() {
  const [activeTab, setActiveTab] = useState<"startups" | "ideas" | "problems" | "users">("startups");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [adminToken, setAdminToken] = useState("");
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  // Check login state
  useEffect(() => {
    const stored = localStorage.getItem("vj_admin_user");
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        if (parsed.adminToken) {
          setIsLoggedIn(true);
        }
      } catch {}
    }
  }, []);

  const handleLoginSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!adminToken.trim()) return;
    localStorage.setItem("vj_admin_user", JSON.stringify({ adminToken: adminToken.trim(), role: "admin" }));
    setIsLoggedIn(true);
    // Mutate SWR calls
    globalMutate("VJ_STARTUPS_METRICS");
    globalMutate("VJ_STARTUPS_LIST");
  };

  const handleLogout = () => {
    localStorage.removeItem("vj_admin_user");
    setIsLoggedIn(false);
    setAdminToken("");
  };

  const { data: metrics, mutate: mutateMetrics } = useSWR("VJ_STARTUPS_METRICS", () => vjStartupsService.fetchMetrics());

  return (
    <PageWrapper
      header={{
        title: "VJ Startups OS",
        description: "Manage ecosystem health, startups, wings, and member progression.",
        actions: isLoggedIn && activeTab === "startups" ? (
          <Button variant="primary" onClick={() => setIsModalOpen(true)}>
            + Create Startup
          </Button>
        ) : undefined,
      }}
    >
      {/* Ecosystem Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard title="Total Startups" value={metrics?.total_startups ?? "-"} />
        <MetricCard title="Active Members" value={metrics?.active_members ?? "-"} />
        <MetricCard 
          title="Funding Raised" 
          value={metrics?.funding_raised !== undefined ? `$${metrics.funding_raised.toLocaleString()}` : "-"} 
        />
        <MetricCard title="Total Users" value={metrics?.total_users ?? "-"} />
      </div>

      {/* Integration Auth Configuration */}
      <div className="mt-6 p-4 border border-subtle rounded bg-layer-1 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Shield className={`w-5 h-5 ${isLoggedIn ? "text-green-500" : "text-amber-500"}`} />
          <div>
            <h4 className="font-semibold text-primary text-13">VJ Startups Microservice Integration</h4>
            <p className="text-11 text-tertiary">
              {isLoggedIn 
                ? "Ecosystem connection established. Ideas, problems, and TRL stages are synchronized."
                : "Enter your admin session token to connect and manage microservice resources."
              }
            </p>
          </div>
        </div>

        {isLoggedIn ? (
          <Button variant="secondary" size="sm" onClick={handleLogout}>
            Disconnect Microservice
          </Button>
        ) : (
          <form onSubmit={handleLoginSubmit} className="flex gap-2 w-full sm:w-auto">
            <input
              type="password"
              placeholder="Paste admin session token..."
              className="px-3 py-1 text-12 border border-subtle rounded bg-surface-2 outline-none focus:border-primary w-full sm:w-64"
              value={adminToken}
              onChange={(e) => setAdminToken(e.target.value)}
            />
            <Button variant="primary" size="sm" type="submit">
              Connect
            </Button>
          </form>
        )}
      </div>

      {/* Tabs */}
      <div className="mt-8 border-b border-subtle flex gap-4 text-13 font-medium">
        <button
          onClick={() => setActiveTab("startups")}
          className={`pb-2 border-b-2 transition-colors ${
            activeTab === "startups" ? "border-primary text-primary" : "border-transparent text-tertiary hover:text-primary"
          }`}
        >
          Startups
        </button>
        <button
          onClick={() => setActiveTab("ideas")}
          className={`pb-2 border-b-2 transition-colors ${
            activeTab === "ideas" ? "border-primary text-primary" : "border-transparent text-tertiary hover:text-primary"
          }`}
        >
          Ecosystem Ideas
        </button>
        <button
          onClick={() => setActiveTab("problems")}
          className={`pb-2 border-b-2 transition-colors ${
            activeTab === "problems" ? "border-primary text-primary" : "border-transparent text-tertiary hover:text-primary"
          }`}
        >
          Ecosystem Problems
        </button>
        <button
          onClick={() => setActiveTab("users")}
          className={`pb-2 border-b-2 transition-colors ${
            activeTab === "users" ? "border-primary text-primary" : "border-transparent text-tertiary hover:text-primary"
          }`}
        >
          Website Users
        </button>
      </div>

      <div className="mt-6">
        {activeTab === "startups" && <StartupList />}
        {activeTab === "ideas" && <IdeasAudit isLoggedIn={isLoggedIn} />}
        {activeTab === "problems" && <ProblemsAudit isLoggedIn={isLoggedIn} />}
        {activeTab === "users" && <UsersAudit isLoggedIn={isLoggedIn} />}
      </div>

      <CreateStartupModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={() => {
          mutateMetrics();
          globalMutate("VJ_STARTUPS_LIST");
        }}
      />
    </PageWrapper>
  );
}

function StartupList() {
  const { data: startups, mutate: mutateStartups } = useSWR("VJ_STARTUPS_LIST", () => vjStartupsService.fetchStartups());
  const { mutate: mutateMetrics } = useSWR("VJ_STARTUPS_METRICS", () => vjStartupsService.fetchMetrics());
  
  const [inviteModalOpen, setInviteModalOpen] = useState(false);
  const [selectedStartupSlug, setSelectedStartupSlug] = useState("");
  const [inviteEmails, setInviteEmails] = useState("");

  const handleDisable = async (slug: string) => {
    if (!confirm("Are you sure you want to disable this startup?")) return;
    try {
      await vjStartupsService.updateStartup(slug, { status: "disabled" });
      mutateStartups();
      mutateMetrics();
    } catch (err) {
      console.error(err);
      alert("Failed to disable startup.");
    }
  };

  const handleDelete = async (slug: string) => {
    if (!confirm("Are you sure you want to PERMANENTLY DELETE this startup and its project? This cannot be undone.")) return;
    try {
      await vjStartupsService.deleteStartup(slug);
      mutateStartups();
      mutateMetrics();
    } catch (err) {
      console.error(err);
      alert("Failed to delete startup.");
    }
  };

  const handleInviteSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmails.trim()) return;
    try {
      await vjStartupsService.inviteToStartup(selectedStartupSlug, inviteEmails);
      alert("Invites sent and users onboarded!");
      setInviteModalOpen(false);
      setInviteEmails("");
      mutateStartups();
    } catch (err) {
      console.error(err);
      alert("Failed to invite users.");
    }
  };

  const handleStageChange = async (slug: string, stage: number) => {
    try {
      await vjStartupsService.updateStartup(slug, { trl_stage: stage });
      mutateStartups();
    } catch (err) {
      console.error(err);
      alert("Failed to update TRL stage.");
    }
  };

  const openInvite = (slug: string) => {
    setSelectedStartupSlug(slug);
    setInviteEmails("");
    setInviteModalOpen(true);
  };

  if (!startups) return <div className="text-sm text-tertiary">Loading startups...</div>;

  return (
    <div className="border border-subtle rounded-lg bg-surface-1 overflow-hidden shadow-sm">
      <table className="w-full text-left text-13">
        <thead className="bg-layer-1 text-tertiary border-b border-subtle">
          <tr>
            <th className="px-6 py-3 font-medium">Name</th>
            <th className="px-6 py-3 font-medium">Slug</th>
            <th className="px-6 py-3 font-medium">TRL Stage</th>
            <th className="px-6 py-3 font-medium">Status</th>
            <th className="px-6 py-3 font-medium text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-subtle">
          {startups.map((startup: any) => (
            <tr key={startup.id} className="hover:bg-layer-1 transition-colors">
              <td className="px-6 py-4 font-medium text-primary">
                <div>
                  <div className="text-13">{startup.name}</div>
                  {startup.tagline && <div className="text-11 text-tertiary mt-0.5">{startup.tagline}</div>}
                </div>
              </td>
              <td className="px-6 py-4 text-tertiary">{startup.slug}</td>
              <td className="px-6 py-4">
                <select
                  value={startup.trl_stage || 1}
                  onChange={(e) => handleStageChange(startup.slug, parseInt(e.target.value))}
                  className="bg-transparent border border-subtle rounded text-xs px-2.5 py-1.5 outline-none cursor-pointer font-medium text-secondary"
                >
                  {Object.entries(STAGE_LABELS).map(([val, label]) => (
                    <option key={val} value={val}>{val}: {label}</option>
                  ))}
                </select>
              </td>
              <td className="px-6 py-4">
                <span className={`px-2 py-1 rounded text-11 font-medium ${
                  startup.status === "active" ? "bg-green-500/10 text-green-500" : "bg-red-500/10 text-red-500"
                }`}>
                  {startup.status.toUpperCase()}
                </span>
              </td>
              <td className="px-6 py-4">
                <div className="flex items-center justify-end gap-2">
                  {startup.status === "active" ? (
                    <>
                      <Button variant="secondary" size="sm" onClick={() => openInvite(startup.slug)}>
                        Invite
                      </Button>
                      <Button variant="error-fill" size="sm" onClick={() => handleDisable(startup.slug)}>
                        Disable
                      </Button>
                    </>
                  ) : (
                    <Button variant="error-fill" size="sm" onClick={() => handleDelete(startup.slug)}>
                      Delete
                    </Button>
                  )}
                  <a
                    href={`${process.env.NEXT_PUBLIC_MAIN_SITE_URL || "http://localhost:4000"}/startups/${startup.id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-1.5 text-tertiary hover:text-primary transition-colors border border-subtle rounded hover:bg-surface-2"
                    title="View on Main Website"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              </td>
            </tr>
          ))}
          {startups.length === 0 && (
            <tr>
              <td colSpan={5} className="px-6 py-8 text-center text-tertiary">No startups found.</td>
            </tr>
          )}
        </tbody>
      </table>

      {inviteModalOpen && (
        <div className="fixed inset-0 bg-background/50 z-50 flex items-center justify-center backdrop-blur-sm">
          <div className="bg-surface-1 border border-subtle rounded-lg w-full max-w-md p-6 shadow-custom">
            <h3 className="text-18 font-medium text-primary mb-4">Invite Founders</h3>
            <p className="text-13 text-tertiary mb-4">
              Enter comma-separated email addresses. If they already have a Plane account, they will instantly be granted access to the Workspace and Plane Project.
            </p>
            <form onSubmit={handleInviteSubmit} className="space-y-4">
              <div>
                <label className="block text-12 font-medium text-tertiary mb-1">Emails</label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-subtle rounded text-13 bg-surface-2 outline-none focus:border-primary"
                  placeholder="founder@example.com, developer@example.com"
                  value={inviteEmails}
                  onChange={(e) => setInviteEmails(e.target.value)}
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <Button variant="secondary" onClick={() => setInviteModalOpen(false)}>
                  Cancel
                </Button>
                <Button variant="primary" type="submit">
                  Send Invites
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function IdeasAudit({ isLoggedIn }: { isLoggedIn: boolean }) {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");

  const { data, isLoading } = useSWR(
    isLoggedIn ? `VJ_IDEAS_${page}_${search}` : null,
    () => vjStartupsService.fetchMicroserviceIdeas(page, 20, search)
  );

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(query);
    setPage(1);
  };

  if (!isLoggedIn) {
    return <div className="text-center py-12 text-tertiary text-13 border border-subtle border-dashed rounded-lg bg-surface-1">Please connect the microservice integration above to view student ideas.</div>;
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleSearchSubmit} className="flex gap-2 max-w-md">
        <input
          type="text"
          className="w-full px-3 py-2 border border-subtle rounded text-13 bg-surface-2 outline-none focus:border-primary"
          placeholder="Search by idea title..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Button variant="primary" size="sm" type="submit">Search</Button>
      </form>

      <div className="border border-subtle rounded-lg bg-surface-1 overflow-hidden shadow-sm">
        {isLoading ? (
          <div className="py-12 text-center text-tertiary text-13">Loading ideas...</div>
        ) : (
          <table className="w-full text-left text-13">
            <thead className="bg-layer-1 text-tertiary border-b border-subtle">
              <tr>
                <th className="px-6 py-3 font-medium">Idea</th>
                <th className="px-6 py-3 font-medium">Submitted By</th>
                <th className="px-6 py-3 font-medium">Upvotes</th>
                <th className="px-6 py-3 font-medium">Created At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-subtle">
              {data?.ideas?.map((idea: any) => (
                <tr key={idea._id} className="hover:bg-layer-1 transition-colors">
                  <td className="px-6 py-4">
                    <div className="font-semibold text-primary">{idea.title}</div>
                    {idea.description && <div className="text-11 text-tertiary mt-0.5 max-w-xl truncate">{idea.description}</div>}
                  </td>
                  <td className="px-6 py-4 text-secondary">{idea.submittedBy || "—"}</td>
                  <td className="px-6 py-4 font-semibold text-secondary">{idea.upvotes ?? 0}</td>
                  <td className="px-6 py-4 text-tertiary">{new Date(idea.createdAt).toLocaleDateString()}</td>
                </tr>
              ))}
              {(!data?.ideas || data.ideas.length === 0) && (
                <tr>
                  <td colSpan={4} className="px-6 py-12 text-center text-tertiary">
                    <div className="flex flex-col items-center justify-center gap-1">
                      <Lightbulb className="w-8 h-8 text-tertiary mb-1" />
                      <p className="font-medium text-secondary">No ideas found.</p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}

        {data?.totalPages > 1 && (
          <div className="px-6 py-3.5 border-t border-subtle bg-layer-1 flex items-center justify-between text-12 text-tertiary">
            <span>Page {page} of {data.totalPages}</span>
            <div className="flex items-center gap-1.5">
              <button
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                className="p-1 border border-subtle rounded hover:bg-surface-2 transition-colors disabled:opacity-50"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
              </button>
              <button
                disabled={page >= data.totalPages}
                onClick={() => setPage(page + 1)}
                className="p-1 border border-subtle rounded hover:bg-surface-2 transition-colors disabled:opacity-50"
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function ProblemsAudit({ isLoggedIn }: { isLoggedIn: boolean }) {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");

  const { data, isLoading } = useSWR(
    isLoggedIn ? `VJ_PROBLEMS_${page}_${search}` : null,
    () => vjStartupsService.fetchMicroserviceProblems(page, 20, search)
  );

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(query);
    setPage(1);
  };

  if (!isLoggedIn) {
    return <div className="text-center py-12 text-tertiary text-13 border border-subtle border-dashed rounded-lg bg-surface-1">Please connect the microservice integration above to view ecosystem problems.</div>;
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleSearchSubmit} className="flex gap-2 max-w-md">
        <input
          type="text"
          className="w-full px-3 py-2 border border-subtle rounded text-13 bg-surface-2 outline-none focus:border-primary"
          placeholder="Search by problem title..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Button variant="primary" size="sm" type="submit">Search</Button>
      </form>

      <div className="border border-subtle rounded-lg bg-surface-1 overflow-hidden shadow-sm">
        {isLoading ? (
          <div className="py-12 text-center text-tertiary text-13">Loading problems...</div>
        ) : (
          <table className="w-full text-left text-13">
            <thead className="bg-layer-1 text-tertiary border-b border-subtle">
              <tr>
                <th className="px-6 py-3 font-medium">Problem</th>
                <th className="px-6 py-3 font-medium">Submitted By</th>
                <th className="px-6 py-3 font-medium">Category</th>
                <th className="px-6 py-3 font-medium">Upvotes</th>
                <th className="px-6 py-3 font-medium">Created At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-subtle">
              {data?.problems?.map((problem: any) => (
                <tr key={problem._id} className="hover:bg-layer-1 transition-colors">
                  <td className="px-6 py-4">
                    <div className="font-semibold text-primary">{problem.title}</div>
                    {problem.description && <div className="text-11 text-tertiary mt-0.5 max-w-xl truncate">{problem.description}</div>}
                  </td>
                  <td className="px-6 py-4 text-secondary">{problem.submittedBy || "—"}</td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-0.5 rounded text-10 font-medium bg-blue-500/10 text-blue-500 border border-blue-500/20">
                      {problem.category || "General"}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-semibold text-secondary">{problem.upvotes ?? 0}</td>
                  <td className="px-6 py-4 text-tertiary">{new Date(problem.createdAt).toLocaleDateString()}</td>
                </tr>
              ))}
              {(!data?.problems || data.problems.length === 0) && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-tertiary">
                    <div className="flex flex-col items-center justify-center gap-1">
                      <AlertCircle className="w-8 h-8 text-tertiary mb-1" />
                      <p className="font-medium text-secondary">No problems found.</p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}

        {data?.totalPages > 1 && (
          <div className="px-6 py-3.5 border-t border-subtle bg-layer-1 flex items-center justify-between text-12 text-tertiary">
            <span>Page {page} of {data.totalPages}</span>
            <div className="flex items-center gap-1.5">
              <button
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                className="p-1 border border-subtle rounded hover:bg-surface-2 transition-colors disabled:opacity-50"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
              </button>
              <button
                disabled={page >= data.totalPages}
                onClick={() => setPage(page + 1)}
                className="p-1 border border-subtle rounded hover:bg-surface-2 transition-colors disabled:opacity-50"
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function UsersAudit({ isLoggedIn }: { isLoggedIn: boolean }) {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");

  const { data, isLoading, mutate } = useSWR(
    isLoggedIn ? `VJ_USERS_${page}_${search}` : null,
    () => vjStartupsService.fetchMicroserviceUsers(page, 20, search)
  );

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(query);
    setPage(1);
  };

  const handleRoleToggle = async (id: string, currentRole: string) => {
    const nextRole = currentRole === "admin" ? "user" : "admin";
    try {
      await vjStartupsService.updateMicroserviceUserRole(id, nextRole);
      mutate();
    } catch (err) {
      console.error(err);
      alert("Failed to toggle user role.");
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to delete user "${name}"? This cannot be undone.`)) return;
    try {
      await vjStartupsService.deleteMicroserviceUser(id);
      mutate();
    } catch (err) {
      console.error(err);
      alert("Failed to delete user.");
    }
  };

  if (!isLoggedIn) {
    return <div className="text-center py-12 text-tertiary text-13 border border-subtle border-dashed rounded-lg bg-surface-1">Please connect the microservice integration above to view website users.</div>;
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleSearchSubmit} className="flex gap-2 max-w-md">
        <input
          type="text"
          className="w-full px-3 py-2 border border-subtle rounded text-13 bg-surface-2 outline-none focus:border-primary"
          placeholder="Search users by name or email..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Button variant="primary" size="sm" type="submit">Search</Button>
      </form>

      <div className="border border-subtle rounded-lg bg-surface-1 overflow-hidden shadow-sm">
        {isLoading ? (
          <div className="py-12 text-center text-tertiary text-13">Loading users...</div>
        ) : (
          <table className="w-full text-left text-13">
            <thead className="bg-layer-1 text-tertiary border-b border-subtle">
              <tr>
                <th className="px-6 py-3 font-medium">User</th>
                <th className="px-6 py-3 font-medium">Email</th>
                <th className="px-6 py-3 font-medium">Role</th>
                <th className="px-6 py-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-subtle">
              {data?.users?.map((u: any) => (
                <tr key={u._id} className="hover:bg-layer-1 transition-colors">
                  <td className="px-6 py-4 flex items-center gap-2.5">
                    <img
                      src={u.picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(u.name)}&background=7c3aed&color=fff&size=32`}
                      alt={u.name}
                      className="w-7 h-7 rounded-full object-cover border border-subtle"
                    />
                    <span className="font-semibold text-primary">{u.name}</span>
                  </td>
                  <td className="px-6 py-4 text-tertiary font-mono text-12">{u.email}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-0.5 rounded text-10 font-semibold uppercase ${
                      u.role === "admin" ? "bg-violet-500/10 text-violet-500 border border-violet-500/20" : "bg-surface-2 text-tertiary border border-subtle"
                    }`}>
                      {u.role}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button variant="secondary" size="sm" onClick={() => handleRoleToggle(u._id, u.role)}>
                        {u.role === "admin" ? "Demote" : "Make Admin"}
                      </Button>
                      <Button variant="error-fill" size="sm" onClick={() => handleDelete(u._id, u.name)}>
                        Delete
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
              {(!data?.users || data.users.length === 0) && (
                <tr>
                  <td colSpan={4} className="px-6 py-12 text-center text-tertiary">No users found.</td>
                </tr>
              )}
            </tbody>
          </table>
        )}

        {data?.totalPages > 1 && (
          <div className="px-6 py-3.5 border-t border-subtle bg-layer-1 flex items-center justify-between text-12 text-tertiary">
            <span>Page {page} of {data.totalPages}</span>
            <div className="flex items-center gap-1.5">
              <button
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                className="p-1 border border-subtle rounded hover:bg-surface-2 transition-colors disabled:opacity-50"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
              </button>
              <button
                disabled={page >= data.totalPages}
                onClick={() => setPage(page + 1)}
                className="p-1 border border-subtle rounded hover:bg-surface-2 transition-colors disabled:opacity-50"
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function MetricCard({ title, value }: { title: string; value: string }) {
  return (
    <div className="p-4 border border-subtle rounded bg-layer-1 shadow-sm">
      <h3 className="text-13 text-tertiary font-medium">{title}</h3>
      <p className="text-24 font-semibold mt-2 text-primary">{value}</p>
    </div>
  );
}

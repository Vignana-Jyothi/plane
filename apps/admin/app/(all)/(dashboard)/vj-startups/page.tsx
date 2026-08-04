"use client"

import React, { useState } from "react";
import useSWR, { mutate as globalMutate } from "swr";
import { PageWrapper } from "@/components/common/page-wrapper";
import { Button } from "@plane/propel/button";
import { CreateStartupModal } from "@/components/vj-startups/create-startup-modal";
import { VJStartupsService } from "@/services/vj-startups.service";
import { ExternalLink } from "lucide-react";

const vjStartupsService = new VJStartupsService();

const STAGE_LABELS: Record<number, string> = {
  1: "Idea", 2: "Research", 3: "Prototype", 4: "MVP",
  5: "Beta", 6: "Launch", 7: "Growth", 8: "Scale", 9: "Mature"
};

export default function VJStartupsDashboard() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const { data: metrics, mutate: mutateMetrics } = useSWR("VJ_STARTUPS_METRICS", () => vjStartupsService.fetchMetrics());
  const { data: startups, mutate: mutateStartups } = useSWR("VJ_STARTUPS_LIST", () => vjStartupsService.fetchStartups());

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

  return (
    <PageWrapper
      header={{
        title: "VJ Startups OS",
        description: "Manage ecosystem health, startups, wings, and member progression.",
        actions: (
          <Button variant="primary" onClick={() => setIsModalOpen(true)}>
            + Create Startup
          </Button>
        ),
      }}
    >
      {/* Ecosystem Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <MetricCard title="Total Startups" value={metrics?.total_startups ?? "-"} />
        <MetricCard title="Active Members" value={metrics?.active_members ?? "-"} />
        <MetricCard 
          title="Funding Raised" 
          value={metrics?.funding_raised !== undefined ? `$${metrics.funding_raised.toLocaleString()}` : "-"} 
        />
        <MetricCard title="Total Users" value={metrics?.total_users ?? "-"} />
      </div>

      <div className="border border-subtle rounded-lg bg-surface-1 overflow-hidden shadow-sm">
        {!startups ? (
          <div className="text-sm text-tertiary p-6 text-center">Loading startups...</div>
        ) : (
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
                  <td className="px-6 py-4 text-right">
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
        )}

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

function MetricCard({ title, value }: { title: string; value: string }) {
  return (
    <div className="p-4 border border-subtle rounded bg-layer-1 shadow-sm">
      <h3 className="text-13 text-tertiary font-medium">{title}</h3>
      <p className="text-24 font-semibold mt-2 text-primary">{value}</p>
    </div>
  );
}

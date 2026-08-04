import React, { useState } from "react";
import useSWR, { mutate as globalMutate } from "swr";
import { PageWrapper } from "@/components/common/page-wrapper";
import { Button } from "@plane/propel/button";
import { CreateStartupModal } from "@/components/vj-startups/create-startup-modal";
import { VJStartupsService } from "@/services/vj-startups.service";

const vjStartupsService = new VJStartupsService();

export default function VJStartupsDashboard() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const { data: metrics, mutate } = useSWR("VJ_STARTUPS_METRICS", () => vjStartupsService.fetchMetrics());

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
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard title="Total Startups" value={metrics?.total_startups ?? "-"} />
        <MetricCard title="Active Members" value={metrics?.active_members ?? "-"} />
        <MetricCard 
          title="Funding Raised" 
          value={metrics?.funding_raised !== undefined ? `$${metrics.funding_raised.toLocaleString()}` : "-"} 
        />
        <MetricCard title="Total Users" value={metrics?.total_users ?? "-"} />
      </div>

      <div className="mt-8">
        <StartupList />
      </div>

      <CreateStartupModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={() => {
          console.log("Startup created successfully!");
          mutate();
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

  const openInvite = (slug: string) => {
    setSelectedStartupSlug(slug);
    setInviteEmails("");
    setInviteModalOpen(true);
  };

  if (!startups) return <div className="text-sm text-tertiary">Loading startups...</div>;

  return (
    <div className="border border-subtle rounded-lg bg-surface-1 overflow-hidden">
      <div className="px-6 py-4 border-b border-subtle">
        <h3 className="text-16 font-medium text-primary">Startups Directory</h3>
      </div>
      <table className="w-full text-left text-13">
        <thead className="bg-layer-1 text-tertiary border-b border-subtle">
          <tr>
            <th className="px-6 py-3 font-medium">Name</th>
            <th className="px-6 py-3 font-medium">Slug</th>
            <th className="px-6 py-3 font-medium">Status</th>
            <th className="px-6 py-3 font-medium">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-subtle">
          {startups.map((startup: any) => (
            <tr key={startup.id} className="hover:bg-layer-1">
              <td className="px-6 py-4 font-medium text-primary">{startup.name}</td>
              <td className="px-6 py-4 text-tertiary">{startup.slug}</td>
              <td className="px-6 py-4">
                <span className={`px-2 py-1 rounded text-11 font-medium ${
                  startup.status === "active" ? "bg-green-500/10 text-green-500" : "bg-red-500/10 text-red-500"
                }`}>
                  {startup.status.toUpperCase()}
                </span>
              </td>
              <td className="px-6 py-4 flex gap-2">
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
              </td>
            </tr>
          ))}
          {startups.length === 0 && (
            <tr>
              <td colSpan={4} className="px-6 py-8 text-center text-tertiary">No startups found.</td>
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

function MetricCard({ title, value }: { title: string; value: string }) {
  return (
    <div className="p-4 border border-subtle rounded bg-layer-1 shadow-sm">
      <h3 className="text-13 text-tertiary font-medium">{title}</h3>
      <p className="text-24 font-semibold mt-2 text-primary">{value}</p>
    </div>
  );
}

"use client"

import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router";
import useSWR from "swr";
import { PageWrapper } from "@/components/common/page-wrapper";
import { Button } from "@plane/propel/button";
import { ArrowLeft, Crown, UserPlus } from "lucide-react";
import { VJStartupsService } from "@/services/vj-startups.service";

const vjStartupsService = new VJStartupsService();

export default function WingDashboard() {
  const params = useParams();
  const navigate = useNavigate();
  const slug = params?.slug as string;

  // Fetch wing details, wing members, and the global directory members
  const { data: wings } = useSWR("VJ_WINGS_LIST", () => vjStartupsService.fetchWings());
  const { data: members, isLoading, mutate: mutateMembers } = useSWR(
    slug ? `VJ_WING_MEMBERS_${slug}` : null,
    () => vjStartupsService.fetchWingMembers(slug)
  );
  const { data: directoryMembers } = useSWR("VJ_MEMBERS_LIST", () => vjStartupsService.fetchMembers());

  const [wing, setWing] = useState<any>(null);
  const [inviteModalOpen, setInviteModalOpen] = useState(false);
  const [inviteEmails, setInviteEmails] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [inviteLoading, setInviteLoading] = useState(false);
  const [error, setError] = useState("");

  const handleInviteSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmails.trim() || !wing) return;
    setInviteLoading(true);
    setError("");
    try {
      await vjStartupsService.inviteToWing(wing.slug, inviteEmails);
      setInviteEmails("");
      setInviteModalOpen(false);
      mutateMembers();
      alert("Invites sent! Registered users have been instantly onboarded.");
    } catch (err: any) {
      setError(err?.error || "Failed to send invites.");
    } finally {
      setInviteLoading(false);
    }
  };

  const handleAddExistingMember = async (email: string) => {
    if (!wing) return;
    try {
      await vjStartupsService.inviteToWing(wing.slug, email);
      mutateMembers();
    } catch (err) {
      console.error(err);
      alert("Failed to add member to wing.");
    }
  };

  const handleRemoveMember = async (memberId: string) => {
    if (!confirm("Are you sure you want to remove this member? They will lose access to the Wing's project.")) return;
    try {
      await vjStartupsService.removeWingMember(wing.slug, memberId);
      mutateMembers();
    } catch (err) {
      console.error(err);
      alert("Failed to remove member.");
    }
  };

  useEffect(() => {
    if (wings && slug) {
      const found = wings.find((w: any) => w.slug === slug);
      if (found) setWing(found);
    }
  }, [wings, slug]);

  if (!wing && !wings) {
    return (
      <PageWrapper header={{ title: "Loading Wing...", description: "" }}>
        <div className="text-sm text-tertiary">Loading data...</div>
      </PageWrapper>
    );
  }

  if (!wing && wings) {
    return (
      <PageWrapper header={{ title: "Wing Not Found", description: "" }}>
        <div className="text-sm text-tertiary">Could not find wing with slug: {slug}</div>
        <Button variant="secondary" className="mt-4" onClick={() => navigate('/club-activities')}>
          Back to Directory
        </Button>
      </PageWrapper>
    );
  }

  // Filter global directory by search query (Name or Email)
  const filteredDirectory = searchQuery.trim()
    ? directoryMembers?.filter((m: any) => {
        const name = `${m.user?.first_name || ""} ${m.user?.last_name || ""}`.toLowerCase();
        const email = (m.user?.email || "").toLowerCase();
        const q = searchQuery.toLowerCase();
        return name.includes(q) || email.includes(q);
      }) || []
    : [];

  return (
    <PageWrapper
      header={{
        title: (
          <div className="flex items-center gap-3">
            <Button variant="secondary" size="sm" className="!px-2" onClick={() => navigate('/club-activities')}>
              <ArrowLeft className="w-4 h-4" />
            </Button>
            {wing.color && (
              <span className="w-4 h-4 rounded shadow-sm border border-subtle" style={{ backgroundColor: wing.color }} />
            )}
            <span>{wing.name}</span>
          </div>
        ) as any,
        description: wing.description || "Manage this wing's members and activities.",
        actions: (
          <Button variant="primary" onClick={() => setInviteModalOpen(true)}>
            + Add Members
          </Button>
        ),
      }}
    >
      <div className="mt-6 border border-subtle rounded-lg bg-surface-1 overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-subtle flex justify-between items-center bg-layer-1">
          <h3 className="text-16 font-medium text-primary">Active Members</h3>
          <span className="text-12 font-medium text-tertiary bg-surface-2 px-2 py-1 rounded">
            {members?.length || 0} Total
          </span>
        </div>
        
        {isLoading ? (
          <div className="px-6 py-8 text-center text-tertiary text-13">Loading members...</div>
        ) : (
          <table className="w-full text-left text-13">
            <thead className="bg-layer-2 text-tertiary border-b border-subtle">
              <tr>
                <th className="px-6 py-3 font-medium">Name</th>
                <th className="px-6 py-3 font-medium">Email</th>
                <th className="px-6 py-3 font-medium">Role</th>
                <th className="px-6 py-3 font-medium">Joined</th>
                <th className="px-6 py-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-subtle">
              {members?.map((member: any) => (
                <tr key={member.id} className="hover:bg-layer-1 transition-colors">
                  <td className="px-6 py-4 font-medium text-primary">
                    {member.first_name || member.last_name ? `${member.first_name} ${member.last_name}` : "Unknown"}
                  </td>
                  <td className="px-6 py-4 text-tertiary">{member.email}</td>
                  <td className="px-6 py-4">
                    {member.role === "Wing Master" ? (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-11 font-medium bg-orange-500/10 text-orange-600 border border-orange-500/20">
                        <Crown className="w-3 h-3" />
                        Wing Master
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-1 rounded-full text-11 font-medium bg-surface-2 text-tertiary border border-subtle">
                        Member
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-tertiary">
                    {new Date(member.joined_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <Button variant="error-fill" size="sm" onClick={() => handleRemoveMember(member.id)}>
                      Remove
                    </Button>
                  </td>
                </tr>
              ))}
              {members?.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center">
                    <p className="text-tertiary font-medium mb-1">No active members yet.</p>
                    <p className="text-tertiary text-12">Click + Add Members to add people from the directory.</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {inviteModalOpen && (
        <div className="fixed inset-0 bg-background/50 z-50 flex items-center justify-center backdrop-blur-sm">
          <div className="bg-surface-1 border border-subtle rounded-lg w-full max-w-md p-6 shadow-custom flex flex-col max-h-[90vh]">
            <h3 className="text-18 font-medium text-primary mb-4">Manage Wing Members</h3>
            {error && <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 text-red-500 rounded text-sm">{error}</div>}
            
            {/* Search inputs and Directory add/remove list */}
            <div className="space-y-4 flex-1 overflow-y-auto pr-1">
              <div>
                <label className="block text-12 font-medium text-tertiary mb-1">Search Directory (Name or Email)</label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-subtle rounded text-13 bg-surface-2 outline-none focus:border-primary"
                  placeholder="Start typing a name or email to add/remove..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>

              {searchQuery.trim() && (
                <div className="border border-subtle rounded divide-y divide-subtle max-h-[200px] overflow-y-auto bg-surface-2">
                  {filteredDirectory.map((m: any) => {
                    const inWing = members?.some((wm: any) => wm.email === m.user?.email);
                    const name = `${m.user?.first_name || ""} ${m.user?.last_name || ""}`.trim() || m.user?.username || m.user?.email || "Unknown Member";
                    return (
                      <div key={m.id} className="p-2.5 flex items-center justify-between hover:bg-surface-3 transition-colors text-12">
                        <div>
                          <div className="font-semibold text-primary">{name}</div>
                          <div className="text-tertiary text-11">{m.user?.email}</div>
                        </div>
                        {inWing ? (
                          <button
                            type="button"
                            onClick={() => handleRemoveMember(m.user?.id)}
                            className="px-2.5 py-1 rounded bg-red-500/10 text-red-500 border border-red-500/20 hover:bg-red-500/20 text-11 font-medium transition-colors"
                          >
                            Remove
                          </button>
                        ) : (
                          <button
                            type="button"
                            onClick={() => handleAddExistingMember(m.user?.email)}
                            className="px-2.5 py-1 rounded bg-green-500/10 text-green-600 border border-green-500/20 hover:bg-green-500/20 text-11 font-medium transition-colors"
                          >
                            Add
                          </button>
                        )}
                      </div>
                    );
                  })}
                  {filteredDirectory.length === 0 && (
                    <div className="p-3 text-center text-tertiary text-12">
                      No directory members match.
                    </div>
                  )}
                </div>
              )}

              {/* Standard Invite Fallback */}
              <form onSubmit={handleInviteSubmit} className="pt-4 border-t border-subtle space-y-4">
                <div>
                  <label className="block text-12 font-medium text-tertiary mb-1">Invite New Emails (Comma-separated)</label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 border border-subtle rounded text-13 bg-surface-2 outline-none focus:border-primary"
                    placeholder="email1@example.com, email2@example.com"
                    value={inviteEmails}
                    onChange={(e) => setInviteEmails(e.target.value)}
                  />
                </div>
                <div className="flex justify-end gap-3 pt-2">
                  <Button variant="secondary" onClick={() => {
                    setInviteModalOpen(false);
                    setSearchQuery("");
                    setInviteEmails("");
                  }}>
                    Close
                  </Button>
                  <Button variant="primary" type="submit" disabled={inviteLoading || !inviteEmails.trim()}>
                    {inviteLoading ? "Sending..." : "Send Invites"}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </PageWrapper>
  );
}

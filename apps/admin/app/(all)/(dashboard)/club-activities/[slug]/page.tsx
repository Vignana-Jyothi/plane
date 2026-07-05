"use client"

import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router";
import useSWR from "swr";
import { PageWrapper } from "@/components/common/page-wrapper";
import { Button } from "@plane/propel/button";
import { ArrowLeft, Crown } from "lucide-react";
import { VJStartupsService } from "@/services/vj-startups.service";

const vjStartupsService = new VJStartupsService();

export default function WingDashboard() {
  const params = useParams();
  const navigate = useNavigate();
  const slug = params?.slug as string;

  // We need to fetch the specific wing details and its members
  const { data: wings } = useSWR("VJ_WINGS_LIST", () => vjStartupsService.fetchWings());
  const { data: members, isLoading, mutate: mutateMembers } = useSWR(
    slug ? `VJ_WING_MEMBERS_${slug}` : null,
    () => vjStartupsService.fetchWingMembers(slug)
  );

  const [wing, setWing] = useState<any>(null);
  const [inviteModalOpen, setInviteModalOpen] = useState(false);
  const [inviteEmails, setInviteEmails] = useState("");
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
        <Button variant="outline-primary" className="mt-4" onClick={() => navigate('/club-activities')}>
          Back to Directory
        </Button>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper
      header={{
        title: (
          <div className="flex items-center gap-3">
            <Button variant="neutral-empty" size="sm" className="!px-2" onClick={() => navigate('/club-activities')}>
              <ArrowLeft className="w-4 h-4" />
            </Button>
            {wing.color && (
              <span className="w-4 h-4 rounded shadow-sm border border-subtle" style={{ backgroundColor: wing.color }} />
            )}
            <span>{wing.name}</span>
          </div>
        ) as any,
        description: wing.description || "Manage this wing's members and activities.",
        action: (
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
                    <Button variant="danger" size="sm" onClick={() => handleRemoveMember(member.id)}>
                      Remove
                    </Button>
                  </td>
                </tr>
              ))}
              {members?.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center">
                    <p className="text-tertiary font-medium mb-1">No active members yet.</p>
                    <p className="text-tertiary text-12">Head back to the directory to invite some!</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {inviteModalOpen && (
        <div className="fixed inset-0 bg-background/50 z-50 flex items-center justify-center backdrop-blur-sm">
          <div className="bg-surface-1 border border-subtle rounded-lg w-full max-w-md p-6 shadow-custom">
            <h3 className="text-18 font-medium text-primary mb-4">Invite Members to {wing?.name}</h3>
            {error && <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 text-red-500 rounded text-sm">{error}</div>}
            <p className="text-13 text-tertiary mb-4">
              Enter comma-separated email addresses. If they already have an account, they will instantly be granted access to the Wing's project.
            </p>
            <form onSubmit={handleInviteSubmit} className="space-y-4">
              <div>
                <label className="block text-12 font-medium text-tertiary mb-1">Emails</label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-subtle rounded text-13 bg-surface-2 outline-none focus:border-primary"
                  placeholder="member1@example.com, member2@example.com"
                  value={inviteEmails}
                  onChange={(e) => setInviteEmails(e.target.value)}
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <Button variant="neutral-empty" onClick={() => setInviteModalOpen(false)}>
                  Cancel
                </Button>
                <Button variant="primary" type="submit" disabled={inviteLoading || !inviteEmails.trim()}>
                  {inviteLoading ? "Sending..." : "Send Invites"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </PageWrapper>
  );
}

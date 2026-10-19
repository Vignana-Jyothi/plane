import React, { useState } from "react";
import useSWR from "swr";
import { UserPlus, Trash2, Globe, Building, Edit } from "lucide-react";
import { PageWrapper } from "@/components/common/page-wrapper";
import { Button } from "@plane/propel/button";
import { VJStartupsService } from "@/services/vj-startups.service";

const vjStartupsService = new VJStartupsService();

interface MemberProfile {
  id: string;
  user: {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    avatar: string;
    username: string;
  };
  role: string;
  is_club_member: boolean;
  wing: {
    id: string;
    name: string;
    color: string;
  } | null;
  created_at: string;
}

export default function MemberDirectory() {
  const { data: members, mutate } = useSWR("VJ_MEMBERS_LIST", () => vjStartupsService.fetchMembers());
  const { data: wings } = useSWR("VJ_WINGS_LIST", () => vjStartupsService.fetchWings());

  // Edit / Add Modals State
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [selectedMember, setSelectedMember] = useState<MemberProfile | null>(null);

  // Form states for Add Member
  const [newEmail, setNewEmail] = useState("");
  const [newFirstName, setNewFirstName] = useState("");
  const [newLastName, setNewLastName] = useState("");
  const [newRole, setNewRole] = useState("Member");
  const [newWing, setNewWing] = useState("");
  const [newShowcase, setNewShowcase] = useState(false);
  const [newAvatar, setNewAvatar] = useState("");
  const [loading, setLoading] = useState(false);

  // Form states for Edit Member modal
  const [editFirstName, setEditFirstName] = useState("");
  const [editLastName, setEditLastName] = useState("");
  const [editRole, setEditRole] = useState("");
  const [editWing, setEditWing] = useState("");
  const [editShowcase, setEditShowcase] = useState(false);
  const [editAvatar, setEditAvatar] = useState("");

  const handleOpenEdit = (member: MemberProfile) => {
    setSelectedMember(member);
    const userObj = member.user || {};
    setEditFirstName(userObj.first_name || "");
    setEditLastName(userObj.last_name || "");
    setEditRole(member.role || "Member");
    setEditWing(member.wing?.id || "");
    setEditShowcase(member.is_club_member || false);
    setEditAvatar(userObj.avatar || "");
  };

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEmail) return;
    setLoading(true);
    try {
      await vjStartupsService.createMember({
        email: newEmail,
        first_name: newFirstName,
        last_name: newLastName,
        role: newRole,
        wing: newWing || null,
        is_club_member: newShowcase,
        avatar: newAvatar || "",
      });
      // Clear and close
      setNewEmail("");
      setNewFirstName("");
      setNewLastName("");
      setNewRole("Member");
      setNewWing("");
      setNewShowcase(false);
      setNewAvatar("");
      setIsAddModalOpen(false);
      mutate();
    } catch (err) {
      console.error(err);
      alert("Failed to add member.");
    } finally {
      setLoading(false);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMember) return;
    setLoading(true);
    try {
      await vjStartupsService.updateMember(selectedMember.id, {
        user: {
          first_name: editFirstName,
          last_name: editLastName,
          avatar: editAvatar || "",
        },
        role: editRole,
        wing: editWing || null,
        is_club_member: editShowcase,
      });
      setSelectedMember(null);
      mutate();
    } catch (err) {
      console.error(err);
      alert("Failed to update member.");
    } finally {
      setLoading(false);
    }
  };

  // Real-time changes functions
  const handleToggleShowcase = async (member: MemberProfile, currentStatus: boolean) => {
    // Realtime update: update locally first (optimistic mutation)
    const updatedMembers = members?.map((m: MemberProfile) =>
      m.id === member.id ? { ...m, is_club_member: !currentStatus } : m
    );
    mutate(updatedMembers, false);

    try {
      await vjStartupsService.updateMember(member.id, {
        is_club_member: !currentStatus,
      });
      mutate(); // Sync with backend state
    } catch (err) {
      console.error(err);
      mutate(); // Revert on failure
    }
  };

  const handleInlineWingChange = async (member: MemberProfile, wingId: string) => {
    const selectedWingObj = wings?.find((w: any) => w.id === wingId) || null;
    const updatedMembers = members?.map((m: MemberProfile) =>
      m.id === member.id ? { ...m, wing: selectedWingObj } : m
    );
    mutate(updatedMembers, false);

    try {
      await vjStartupsService.updateMember(member.id, {
        wing: wingId || null,
      });
      mutate();
    } catch (err) {
      console.error(err);
      mutate();
    }
  };

  const handleInlineRoleBlur = async (member: MemberProfile, newRoleName: string) => {
    if (member.role === newRoleName) return;
    const updatedMembers = members?.map((m: MemberProfile) => (m.id === member.id ? { ...m, role: newRoleName } : m));
    mutate(updatedMembers, false);

    try {
      await vjStartupsService.updateMember(member.id, {
        role: newRoleName,
      });
      mutate();
    } catch (err) {
      console.error(err);
      mutate();
    }
  };

  const handleDeleteMember = async (id: string) => {
    if (!confirm("Are you sure you want to remove this member?")) return;
    const updatedMembers = members?.filter((m: MemberProfile) => m.id !== id);
    mutate(updatedMembers, false);
    try {
      await vjStartupsService.deleteMember(id);
      mutate();
    } catch (err) {
      console.error(err);
      mutate();
    }
  };

  return (
    <PageWrapper
      header={{
        title: "Member Directory",
        description:
          "Manage ecosystem members, configure roles, and select showcase members to display on the main portal.",
        actions: (
          <Button variant="primary" onClick={() => setIsAddModalOpen(true)}>
            <UserPlus className="mr-2 h-4 w-4" /> Add Member
          </Button>
        ),
      }}
    >
      <div className="shadow-sm mt-6 overflow-hidden rounded-lg border border-subtle bg-surface-1">
        <table className="w-full border-collapse text-left">
          <thead>
            <tr className="border-b border-subtle bg-surface-2 text-12 font-medium text-tertiary">
              <th className="px-6 py-3 font-semibold">User Details</th>
              <th className="px-6 py-3 font-semibold">Custom Role Name</th>
              <th className="px-6 py-3 font-semibold">Active Wing</th>
              <th className="px-6 py-3 text-center font-semibold">Showcase (Website)</th>
              <th className="px-6 py-3 text-right font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-subtle">
            {members?.map((member: MemberProfile) => {
              const userObj = member.user || {};
              const displayName =
                `${userObj.first_name || ""} ${userObj.last_name || ""}`.trim() ||
                userObj.username ||
                userObj.email ||
                "Unknown User";
              const userAvatar = userObj.avatar;
              const userEmail = userObj.email || "";
              return (
                <tr key={member.id} className="text-13 transition-colors hover:bg-surface-2">
                  {/* User details */}
                  <td className="flex items-center gap-3 px-6 py-4">
                    <div className="relative">
                      {userAvatar ? (
                        <img
                          src={userAvatar}
                          alt={displayName}
                          className="h-8 w-8 rounded-full border border-subtle object-cover"
                        />
                      ) : (
                        <div className="flex h-8 w-8 items-center justify-center rounded-full border border-subtle bg-surface-2 text-12 font-bold text-tertiary uppercase">
                          {displayName.slice(0, 2)}
                        </div>
                      )}
                    </div>
                    <div>
                      <div className="font-semibold text-primary">{displayName}</div>
                      <div className="text-11 text-tertiary">{userEmail}</div>
                    </div>
                  </td>

                  {/* Custom Role */}
                  <td className="px-6 py-4">
                    <input
                      type="text"
                      className="focus:border-primary w-full max-w-[200px] rounded border-b border-transparent bg-transparent px-1 py-0.5 outline-none hover:border-subtle"
                      defaultValue={member.role}
                      key={`${member.id}-${member.role}`}
                      onBlur={(e) => handleInlineRoleBlur(member, e.target.value)}
                    />
                  </td>

                  {/* Active Wing Select */}
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-1.5">
                      <span
                        className="h-2.5 w-2.5 rounded-full border border-subtle"
                        style={{ backgroundColor: member.wing?.color || "#94a3b8" }}
                      />
                      <select
                        className="cursor-pointer bg-transparent text-13 font-medium text-secondary outline-none"
                        value={member.wing?.id || ""}
                        onChange={(e) => handleInlineWingChange(member, e.target.value)}
                      >
                        <option value="">No Wing</option>
                        {wings?.map((wing: any) => (
                          <option key={wing.id} value={wing.id}>
                            {wing.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </td>

                  {/* Showcase toggle */}
                  <td className="px-6 py-4 text-center">
                    <button
                      onClick={() => handleToggleShowcase(member, member.is_club_member)}
                      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-11 font-medium transition-colors ${
                        member.is_club_member
                          ? "bg-green-500/10 text-green-600 border-green-500/20"
                          : "border-subtle bg-surface-2 text-tertiary"
                      }`}
                    >
                      <Globe className="h-3.5 w-3.5" />
                      {member.is_club_member ? "Showcased" : "Private"}
                    </button>
                  </td>

                  {/* Actions */}
                  <td className="px-6 py-4 text-right">
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => handleOpenEdit(member)}
                        className="hover:bg-surface-3 rounded p-1 text-secondary transition-colors"
                      >
                        <Edit className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteMember(member.id)}
                        className="hover:bg-red-500/10 text-red-500 rounded p-1 transition-colors"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
            {(!members || members.length === 0) && (
              <tr>
                <td colSpan={5} className="px-6 py-12 text-center text-tertiary">
                  No ecosystem members found. Click Add Member to invite creators.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Add Member Modal */}
      {isAddModalOpen && (
        <div className="bg-background/50 fixed inset-0 z-50 flex items-center justify-center backdrop-blur-sm">
          <div className="shadow-custom w-full max-w-md rounded-lg border border-subtle bg-surface-1 p-6">
            <h3 className="mb-4 text-18 font-medium text-primary">Add New Directory Member</h3>
            <form onSubmit={handleAddSubmit} className="space-y-4">
              <div>
                <label className="mb-1 block text-12 font-medium text-tertiary">Email (Required)</label>
                <input
                  type="email"
                  className="focus:border-primary w-full rounded border border-subtle bg-surface-2 px-3 py-2 text-13 outline-none"
                  placeholder="member@example.com"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block text-12 font-medium text-tertiary">First Name</label>
                  <input
                    type="text"
                    className="focus:border-primary w-full rounded border border-subtle bg-surface-2 px-3 py-2 text-13 outline-none"
                    placeholder="First Name"
                    value={newFirstName}
                    onChange={(e) => setNewFirstName(e.target.value)}
                  />
                </div>
                <div>
                  <label className="mb-1 block text-12 font-medium text-tertiary">Last Name</label>
                  <input
                    type="text"
                    className="focus:border-primary w-full rounded border border-subtle bg-surface-2 px-3 py-2 text-13 outline-none"
                    placeholder="Last Name"
                    value={newLastName}
                    onChange={(e) => setNewLastName(e.target.value)}
                  />
                </div>
              </div>
              <div>
                <label className="mb-1 block text-12 font-medium text-tertiary">Photo URL (Optional)</label>
                <input
                  type="url"
                  className="focus:border-primary w-full rounded border border-subtle bg-surface-2 px-3 py-2 text-13 outline-none"
                  placeholder="https://..."
                  value={newAvatar}
                  onChange={(e) => setNewAvatar(e.target.value)}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block text-12 font-medium text-tertiary">Custom Role Name</label>
                  <input
                    type="text"
                    className="focus:border-primary w-full rounded border border-subtle bg-surface-2 px-3 py-2 text-13 outline-none"
                    value={newRole}
                    onChange={(e) => setNewRole(e.target.value)}
                  />
                </div>
                <div>
                  <label className="mb-1 block text-12 font-medium text-tertiary">Assigned Wing</label>
                  <select
                    className="focus:border-primary w-full rounded border border-subtle bg-surface-2 px-3 py-2 text-13 outline-none"
                    value={newWing}
                    onChange={(e) => setNewWing(e.target.value)}
                  >
                    <option value="">No Wing</option>
                    {wings?.map((wing: any) => (
                      <option key={wing.id} value={wing.id}>
                        {wing.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="newShowcase"
                  checked={newShowcase}
                  onChange={(e) => setNewShowcase(e.target.checked)}
                  className="accent-primary h-4 w-4 cursor-pointer"
                />
                <label htmlFor="newShowcase" className="cursor-pointer text-13 font-medium text-secondary">
                  Showcase directly on public website
                </label>
              </div>
              <div className="flex justify-end gap-3 border-t border-subtle pt-4">
                <Button variant="secondary" onClick={() => setIsAddModalOpen(false)} disabled={loading}>
                  Cancel
                </Button>
                <Button variant="primary" type="submit" disabled={loading}>
                  {loading ? "Adding..." : "Add Member"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Member Modal */}
      {selectedMember && (
        <div className="bg-background/50 fixed inset-0 z-50 flex items-center justify-center backdrop-blur-sm">
          <div className="shadow-custom w-full max-w-md rounded-lg border border-subtle bg-surface-1 p-6">
            <h3 className="mb-4 text-18 font-medium text-primary">Edit Directory Member</h3>
            <form onSubmit={handleEditSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block text-12 font-medium text-tertiary">First Name</label>
                  <input
                    type="text"
                    className="focus:border-primary w-full rounded border border-subtle bg-surface-2 px-3 py-2 text-13 outline-none"
                    value={editFirstName}
                    onChange={(e) => setEditFirstName(e.target.value)}
                  />
                </div>
                <div>
                  <label className="mb-1 block text-12 font-medium text-tertiary">Last Name</label>
                  <input
                    type="text"
                    className="focus:border-primary w-full rounded border border-subtle bg-surface-2 px-3 py-2 text-13 outline-none"
                    value={editLastName}
                    onChange={(e) => setEditLastName(e.target.value)}
                  />
                </div>
              </div>
              <div>
                <label className="mb-1 block text-12 font-medium text-tertiary">Photo URL</label>
                <input
                  type="url"
                  className="focus:border-primary w-full rounded border border-subtle bg-surface-2 px-3 py-2 text-13 outline-none"
                  value={editAvatar}
                  onChange={(e) => setEditAvatar(e.target.value)}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block text-12 font-medium text-tertiary">Custom Role Name</label>
                  <input
                    type="text"
                    className="focus:border-primary w-full rounded border border-subtle bg-surface-2 px-3 py-2 text-13 outline-none"
                    value={editRole}
                    onChange={(e) => setEditRole(e.target.value)}
                  />
                </div>
                <div>
                  <label className="mb-1 block text-12 font-medium text-tertiary">Assigned Wing</label>
                  <select
                    className="focus:border-primary w-full rounded border border-subtle bg-surface-2 px-3 py-2 text-13 outline-none"
                    value={editWing}
                    onChange={(e) => setEditWing(e.target.value)}
                  >
                    <option value="">No Wing</option>
                    {wings?.map((wing: any) => (
                      <option key={wing.id} value={wing.id}>
                        {wing.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="editShowcase"
                  checked={editShowcase}
                  onChange={(e) => setEditShowcase(e.target.checked)}
                  className="accent-primary h-4 w-4 cursor-pointer"
                />
                <label htmlFor="editShowcase" className="cursor-pointer text-13 font-medium text-secondary">
                  Showcase directly on public website
                </label>
              </div>
              <div className="flex justify-end gap-3 border-t border-subtle pt-4">
                <Button variant="secondary" onClick={() => setSelectedMember(null)} disabled={loading}>
                  Cancel
                </Button>
                <Button variant="primary" type="submit" disabled={loading}>
                  {loading ? "Saving..." : "Save Changes"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </PageWrapper>
  );
}

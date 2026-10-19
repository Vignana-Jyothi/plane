import React, { useState, useEffect } from "react";
import { Button } from "@plane/propel/button";
import { VJStartupsService } from "../../services/vj-startups.service";

const vjStartupsService = new VJStartupsService();

type Props = {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  wing: any;
};

export function EditWingModal({ isOpen, onClose, onSuccess, wing }: Props) {
  const [description, setDescription] = useState("");
  const [color, setColor] = useState("");
  const [wingMasterEmail, setWingMasterEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [inviteEmails, setInviteEmails] = useState("");
  const [inviteLoading, setInviteLoading] = useState(false);

  useEffect(() => {
    if (wing) {
      setDescription(wing.description || "");
      setColor(wing.color || "");
      setWingMasterEmail(""); // We don't have the email from the API, just the ID, so let them set a new one
      setInviteEmails("");
    }
  }, [wing]);

  if (!isOpen || !wing) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data: any = { description, color };
      if (wingMasterEmail) data.wing_master_email = wingMasterEmail;

      await vjStartupsService.updateWing(wing.slug, data);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err?.error || "Failed to update wing.");
    } finally {
      setLoading(false);
    }
  };

  const handleInviteSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmails.trim()) return;
    setInviteLoading(true);
    setError("");
    try {
      await vjStartupsService.inviteToWing(wing.slug, inviteEmails);
      setInviteEmails("");
      alert("Invites sent! Registered users have been instantly onboarded.");
    } catch (err: any) {
      setError(err?.error || "Failed to send invites.");
    } finally {
      setInviteLoading(false);
    }
  };

  return (
    <div className="bg-background/50 fixed inset-0 z-50 flex items-center justify-center backdrop-blur-sm">
      <div className="shadow-custom w-full max-w-md rounded-lg border border-subtle bg-surface-1 p-6">
        <h3 className="mb-4 text-18 font-medium text-primary">Edit {wing.name}</h3>

        {error && (
          <div className="bg-red-500/10 border-red-500/20 text-red-500 text-sm mb-4 rounded border p-3">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="mb-6 space-y-4 border-b border-subtle pb-6">
          <div>
            <label className="mb-1 block text-12 font-medium text-tertiary">Description</label>
            <textarea
              className="focus:border-primary w-full rounded border border-subtle bg-surface-2 px-3 py-2 text-13 outline-none"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
            />
          </div>
          <div>
            <label className="mb-1 block text-12 font-medium text-tertiary">Theme Color (Hex)</label>
            <div className="flex gap-2">
              <input
                type="color"
                className="h-10 w-10 cursor-pointer rounded border border-subtle bg-surface-2 p-1"
                value={color || "#000000"}
                onChange={(e) => setColor(e.target.value)}
              />
              <input
                type="text"
                className="focus:border-primary flex-1 rounded border border-subtle bg-surface-2 px-3 py-2 text-13 outline-none"
                placeholder="#FF5733"
                value={color}
                onChange={(e) => setColor(e.target.value)}
              />
            </div>
          </div>
          <div>
            <label className="mb-1 block text-12 font-medium text-tertiary">Wing Master (Email)</label>
            <input
              type="email"
              className="focus:border-primary w-full rounded border border-subtle bg-surface-2 px-3 py-2 text-13 outline-none"
              placeholder="Assign a new wing master by email..."
              value={wingMasterEmail}
              onChange={(e) => setWingMasterEmail(e.target.value)}
            />
            <p className="mt-1 text-11 text-tertiary">
              Leave blank to keep current master. (Vision Wing Master gets Workspace Admin rights).
            </p>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" disabled={loading}>
              {loading ? "Saving..." : "Save Changes"}
            </Button>
          </div>
        </form>

        <div>
          <h4 className="mb-3 text-14 font-medium text-primary">Invite Members</h4>
          <form onSubmit={handleInviteSubmit} className="space-y-3">
            <div>
              <label className="mb-1 block text-12 font-medium text-tertiary">Emails (comma separated)</label>
              <input
                type="text"
                className="focus:border-primary w-full rounded border border-subtle bg-surface-2 px-3 py-2 text-13 outline-none"
                placeholder="member1@example.com, member2@example.com"
                value={inviteEmails}
                onChange={(e) => setInviteEmails(e.target.value)}
              />
            </div>
            <div className="flex justify-end">
              <Button variant="secondary" type="submit" disabled={inviteLoading || !inviteEmails.trim()}>
                {inviteLoading ? "Sending..." : "Send Invites"}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

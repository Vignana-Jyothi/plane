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
    <div className="fixed inset-0 bg-background/50 z-50 flex items-center justify-center backdrop-blur-sm">
      <div className="bg-surface-1 border border-subtle rounded-lg w-full max-w-md p-6 shadow-custom">
        <h3 className="text-18 font-medium text-primary mb-4">Edit {wing.name}</h3>
        
        {error && <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 text-red-500 rounded text-sm">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-4 border-b border-subtle pb-6 mb-6">
          <div>
            <label className="block text-12 font-medium text-tertiary mb-1">Description</label>
            <textarea
              className="w-full px-3 py-2 border border-subtle rounded text-13 bg-surface-2 outline-none focus:border-primary"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
            />
          </div>
          <div>
            <label className="block text-12 font-medium text-tertiary mb-1">Theme Color (Hex)</label>
            <div className="flex gap-2">
              <input
                type="color"
                className="w-10 h-10 p-1 bg-surface-2 border border-subtle rounded cursor-pointer"
                value={color || "#000000"}
                onChange={(e) => setColor(e.target.value)}
              />
              <input
                type="text"
                className="flex-1 px-3 py-2 border border-subtle rounded text-13 bg-surface-2 outline-none focus:border-primary"
                placeholder="#FF5733"
                value={color}
                onChange={(e) => setColor(e.target.value)}
              />
            </div>
          </div>
          <div>
            <label className="block text-12 font-medium text-tertiary mb-1">Wing Master (Email)</label>
            <input
              type="email"
              className="w-full px-3 py-2 border border-subtle rounded text-13 bg-surface-2 outline-none focus:border-primary"
              placeholder="Assign a new wing master by email..."
              value={wingMasterEmail}
              onChange={(e) => setWingMasterEmail(e.target.value)}
            />
            <p className="text-11 text-tertiary mt-1">Leave blank to keep current master. (Vision Wing Master gets Workspace Admin rights).</p>
          </div>
          
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="neutral-empty" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" disabled={loading}>
              {loading ? "Saving..." : "Save Changes"}
            </Button>
          </div>
        </form>

        <div>
          <h4 className="text-14 font-medium text-primary mb-3">Invite Members</h4>
          <form onSubmit={handleInviteSubmit} className="space-y-3">
            <div>
              <label className="block text-12 font-medium text-tertiary mb-1">Emails (comma separated)</label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-subtle rounded text-13 bg-surface-2 outline-none focus:border-primary"
                placeholder="member1@example.com, member2@example.com"
                value={inviteEmails}
                onChange={(e) => setInviteEmails(e.target.value)}
              />
            </div>
            <div className="flex justify-end">
              <Button variant="outline-primary" type="submit" disabled={inviteLoading || !inviteEmails.trim()}>
                {inviteLoading ? "Sending..." : "Send Invites"}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

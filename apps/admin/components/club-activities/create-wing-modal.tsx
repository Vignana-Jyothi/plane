import React, { useState } from "react";
import { Button } from "@plane/propel/button";
import { VJStartupsService } from "../../services/vj-startups.service";

const vjStartupsService = new VJStartupsService();

type Props = {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
};

export function CreateWingModal({ isOpen, onClose, onSuccess }: Props) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [color, setColor] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await vjStartupsService.createWing({ name, description, color });
      setName("");
      setDescription("");
      setColor("");
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err?.error || "Failed to create wing.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-background/50 fixed inset-0 z-50 flex items-center justify-center backdrop-blur-sm">
      <div className="shadow-custom w-full max-w-md rounded-lg border border-subtle bg-surface-1 p-6">
        <h3 className="mb-4 text-18 font-medium text-primary">Create New Wing</h3>

        {error && <div className="text-red-500 text-sm mb-4">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-12 font-medium text-tertiary">Wing Name</label>
            <input
              type="text"
              className="focus:border-primary w-full rounded border border-subtle bg-surface-2 px-3 py-2 text-13 outline-none"
              placeholder="e.g. Web Development Wing"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-12 font-medium text-tertiary">Description</label>
            <textarea
              className="focus:border-primary w-full rounded border border-subtle bg-surface-2 px-3 py-2 text-13 outline-none"
              placeholder="What does this wing do?"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
            />
          </div>
          <div>
            <label className="mb-1 block text-12 font-medium text-tertiary">Theme Color (Hex)</label>
            <input
              type="text"
              className="focus:border-primary w-full rounded border border-subtle bg-surface-2 px-3 py-2 text-13 outline-none"
              placeholder="e.g. #FF5733"
              value={color}
              onChange={(e) => setColor(e.target.value)}
            />
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" disabled={loading}>
              {loading ? "Creating..." : "Create Wing"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

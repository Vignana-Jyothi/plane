import React, { useState, Fragment } from "react";
import { VJStartupsService } from "../../services/vj-startups.service";
import { Dialog, Transition } from "@headlessui/react";
import { Button } from "@plane/propel/button";
import { Input, TextArea } from "@plane/ui";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";

interface CreateStartupModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export function CreateStartupModal({ isOpen, onClose, onSuccess }: CreateStartupModalProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [invitedEmails, setInvitedEmails] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const service = new VJStartupsService();
      
      const emailsList = invitedEmails
        .split(",")
        .map((email) => email.trim())
        .filter((email) => email.length > 0);

      await service.createStartup({
        name,
        description,
        invited_emails: emailsList,
      });
      
      setIsSubmitting(false);
      onClose();
      if (onSuccess) onSuccess();
      
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: "Success",
        message: "Startup created successfully and workspace projects auto-provisioned.",
      });

      setName("");
      setDescription("");
      setInvitedEmails("");
    } catch (err: any) {
      console.error(err);
      setError(err?.message || "Failed to create startup. Please try again.");
      setIsSubmitting(false);
    }
  };

  return (
    <Transition.Root show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-backdrop transition-opacity" />
        </Transition.Child>

        <div className="fixed inset-0 z-10 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center sm:p-0">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
              enterTo="opacity-100 translate-y-0 sm:scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 translate-y-0 sm:scale-100"
              leaveTo="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            >
              <Dialog.Panel className="relative transform overflow-hidden rounded-lg bg-surface-1 text-left shadow-raised-200 transition-all sm:my-8 sm:w-full sm:max-w-md border border-subtle">
                <div className="px-6 pt-5 pb-4">
                  <Dialog.Title as="h3" className="text-16 font-medium text-primary mb-1">
                    Create New Startup
                  </Dialog.Title>
                </div>
                
                <form onSubmit={handleSubmit} className="px-6 pb-6 space-y-5">
                  {error && <div className="p-3 text-13 text-red-500 bg-red-500/10 rounded">{error}</div>}
                  
                  <div className="space-y-1">
                    <label className="text-13 text-tertiary">Startup Name *</label>
                    <Input
                      id="name"
                      name="name"
                      type="text"
                      required
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="e.g., Acme Corp"
                      className="w-full"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-13 text-tertiary">Description</label>
                    <TextArea
                      id="description"
                      name="description"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="Brief description of the startup..."
                      className="w-full min-h-[80px]"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-13 text-tertiary">Invited Emails</label>
                    <Input
                      id="invitedEmails"
                      name="invitedEmails"
                      type="text"
                      value={invitedEmails}
                      onChange={(e) => setInvitedEmails(e.target.value)}
                      placeholder="founder1@acme.com, founder2@acme.com"
                      className="w-full"
                    />
                    <p className="text-11 text-placeholder mt-1">
                      Comma-separated list of emails for auto-onboarding.
                    </p>
                  </div>

                  <div className="mt-6 flex items-center justify-end gap-2 pt-2">
                    <Button variant="secondary" onClick={onClose} disabled={isSubmitting}>
                      Cancel
                    </Button>
                    <Button variant="primary" type="submit" loading={isSubmitting}>
                      {isSubmitting ? "Creating..." : "Create Startup"}
                    </Button>
                  </div>
                </form>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  );
}

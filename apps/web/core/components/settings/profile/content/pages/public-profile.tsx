/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useEffect, useState } from "react";
import { observer } from "mobx-react";
import useSWR from "swr";
// plane imports
import { useTranslation } from "@plane/i18n";
import { Button } from "@plane/propel/button";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
import { Input } from "@plane/ui";
// components
import { ProfileSettingsHeading } from "@/components/settings/profile/heading";
// services
import { PublicProfileService } from "@/services/public-profile.service";
import type {
  THandleAvailability,
  TPublicProfileErrors,
  TPublicProfileSettings,
  TPublicProfileVisibility,
} from "@/services/public-profile.service";

const publicProfileService = new PublicProfileService();

// Build-time, like the other VITE_ variables; the profile page itself lives on the main website.
const PUBLIC_SITE_URL = (process.env.VITE_VJ_PUBLIC_SITE_URL || "https://www.vjstartup.com").replace(/\/$/, "");

type TFormState = {
  handle: string;
  visibility: TPublicProfileVisibility;
  headline: string;
  bio: string;
  skills: string;
  github_url: string;
  linkedin_url: string;
  portfolio_url: string;
};

const toFormState = (data: TPublicProfileSettings): TFormState => ({
  handle: data.handle ?? "",
  visibility: data.profile_visibility,
  headline: data.headline ?? "",
  bio: data.bio ?? "",
  skills: (data.skills ?? []).join(", "),
  github_url: data.github_url ?? "",
  linkedin_url: data.linkedin_url ?? "",
  portfolio_url: data.portfolio_url ?? "",
});

const parseSkills = (value: string) =>
  value
    .split(",")
    .map((skill) => skill.trim())
    .filter(Boolean);

export const PublicProfileSettings = observer(function PublicProfileSettings() {
  // translation
  const { t } = useTranslation();
  // states
  const [form, setForm] = useState<TFormState | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [handleCheck, setHandleCheck] = useState<THandleAvailability | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  // data
  const { data, mutate } = useSWR("VJ_PUBLIC_PROFILE_ME", () => publicProfileService.getMine(), {
    revalidateOnFocus: false,
  });

  useEffect(() => {
    if (data) setForm(toFormState(data));
  }, [data]);

  // Check the handle as the member types (after a short pause), unless it is unchanged.
  useEffect(() => {
    const handle = form?.handle.trim().toLowerCase() ?? "";
    if (!handle || handle === (data?.handle ?? "")) {
      setHandleCheck(null);
      return;
    }
    const timer = setTimeout(() => {
      publicProfileService
        .checkHandle(handle)
        .then(setHandleCheck)
        .catch(() => setHandleCheck(null));
    }, 400);
    return () => clearTimeout(timer);
  }, [form?.handle, data?.handle]);

  if (!form || !data) {
    return <div className="text-13 text-tertiary">Loading…</div>;
  }

  const update = <K extends keyof TFormState>(key: K, value: TFormState[K]) => {
    setForm((prev) => (prev ? { ...prev, [key]: value } : prev));
    setFieldErrors((prev) => ({ ...prev, [key === "visibility" ? "profile_visibility" : key]: "" }));
  };

  const isPublic = form.visibility === "public";
  const handleBlocked = handleCheck !== null && !handleCheck.available;
  const liveHandle = (data.handle ?? form.handle.trim().toLowerCase()) || null;

  const handleSave = async () => {
    setIsSaving(true);
    setFieldErrors({});
    try {
      const updated = await publicProfileService.updateMine({
        handle: form.handle.trim() || undefined,
        profile_visibility: form.visibility,
        headline: form.headline,
        bio: form.bio,
        skills: parseSkills(form.skills),
        github_url: form.github_url,
        linkedin_url: form.linkedin_url,
        portfolio_url: form.portfolio_url,
      });
      await mutate(updated, { revalidate: false });
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: "Saved",
        message: updated.is_public ? "Your public profile is live." : "Your profile is private.",
      });
    } catch (error) {
      const errors = (error as TPublicProfileErrors | undefined)?.errors ?? {};
      setFieldErrors(errors);
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Could not save",
        message: Object.values(errors)[0] ?? "Something went wrong. Please try again.",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const textareaClass =
    "w-full rounded-md border border-subtle bg-surface-1 px-3 py-2 text-13 text-primary outline-none focus:border-accent-strong";

  return (
    <div className="size-full">
      <ProfileSettingsHeading
        title={t("profile.actions.public-profile")}
        description="Show your work on the VJ Startups website: a contribution calendar, streaks, badges and the startups you are part of. Private until you turn it on."
      />

      <div className="mt-7 flex flex-col gap-y-7">
        <label className="flex items-start gap-3 rounded-md border border-subtle p-4">
          <input
            type="checkbox"
            className="mt-0.5 size-4"
            checked={isPublic}
            onChange={(e) => update("visibility", e.target.checked ? "public" : "private")}
          />
          <span className="flex flex-col gap-1">
            <span className="text-13 font-medium text-primary">Make my profile public</span>
            <span className="text-12 text-tertiary">
              Anyone with the link can see it. Only the details below and counts of your activity are shown, never your
              email, and never the titles of work in private projects.
            </span>
          </span>
        </label>

        <div className="flex flex-col gap-y-2">
          <h4 className="text-13">Handle</h4>
          <Input
            id="handle"
            value={form.handle}
            onChange={(e) => update("handle", e.target.value)}
            placeholder="your-name"
            className="w-full"
            hasError={Boolean(fieldErrors.handle) || handleBlocked}
            autoComplete="off"
            maxLength={30}
          />
          <span className="text-11 text-tertiary">
            3–30 letters, numbers or hyphens.
            {isPublic && !form.handle.trim() && " Leave empty to pick one from your name."}
          </span>
          {(fieldErrors.handle || handleBlocked) && (
            <span className="text-11 text-danger-primary">{fieldErrors.handle || handleCheck?.reason}</span>
          )}
          {handleCheck?.available && <span className="text-11 text-success-primary">Available</span>}
          {data.is_public && liveHandle && (
            <a
              href={`${PUBLIC_SITE_URL}/u/${liveHandle}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-12 text-accent-primary hover:underline"
            >
              {PUBLIC_SITE_URL}/u/{liveHandle}
            </a>
          )}
        </div>

        <div className="flex flex-col gap-y-2">
          <h4 className="text-13">Headline</h4>
          <Input
            id="headline"
            value={form.headline}
            onChange={(e) => update("headline", e.target.value)}
            placeholder="Information Technology - 3rd Year"
            className="w-full"
            hasError={Boolean(fieldErrors.headline)}
            maxLength={255}
          />
          {fieldErrors.headline && <span className="text-11 text-danger-primary">{fieldErrors.headline}</span>}
        </div>

        <div className="flex flex-col gap-y-2">
          <h4 className="text-13">About you</h4>
          <textarea
            id="bio"
            value={form.bio}
            onChange={(e) => update("bio", e.target.value)}
            rows={4}
            maxLength={1000}
            className={textareaClass}
            placeholder="What you build and what you are learning."
          />
          {fieldErrors.bio && <span className="text-11 text-danger-primary">{fieldErrors.bio}</span>}
        </div>

        <div className="flex flex-col gap-y-2">
          <h4 className="text-13">Skills</h4>
          <Input
            id="skills"
            value={form.skills}
            onChange={(e) => update("skills", e.target.value)}
            placeholder="Python, React, Figma"
            className="w-full"
            hasError={Boolean(fieldErrors.skills)}
          />
          <span className="text-11 text-tertiary">Separate with commas. Up to 20.</span>
          {fieldErrors.skills && <span className="text-11 text-danger-primary">{fieldErrors.skills}</span>}
        </div>

        <div className="grid gap-x-4 gap-y-7 sm:grid-cols-3">
          {(
            [
              ["github_url", "GitHub", "https://github.com/you"],
              ["linkedin_url", "LinkedIn", "https://www.linkedin.com/in/you"],
              ["portfolio_url", "Portfolio", "https://your.site"],
            ] as const
          ).map(([key, label, placeholder]) => (
            <div key={key} className="flex flex-col gap-y-2">
              <h4 className="text-13">{label}</h4>
              <Input
                id={key}
                value={form[key]}
                onChange={(e) => update(key, e.target.value)}
                placeholder={placeholder}
                className="w-full"
                hasError={Boolean(fieldErrors[key])}
              />
              {fieldErrors[key] && <span className="text-11 text-danger-primary">{fieldErrors[key]}</span>}
            </div>
          ))}
        </div>

        <div>
          <Button variant="primary" size="lg" onClick={handleSave} loading={isSaving} disabled={isSaving || handleBlocked}>
            {isSaving ? "Saving…" : "Save changes"}
          </Button>
        </div>
      </div>
    </div>
  );
});

/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

// plane imports
import { API_BASE_URL } from "@plane/constants";
// services
import { APIService } from "@/services/api.service";

export type TPublicProfileVisibility = "public" | "private";

/** The signed-in member's own public-profile settings (GET/PATCH /api/vj-startups/profile/me/). */
export type TPublicProfileSettings = {
  handle: string | null;
  profile_visibility: TPublicProfileVisibility;
  headline: string;
  bio: string;
  skills: string[];
  github_url: string;
  linkedin_url: string;
  portfolio_url: string;
  is_public: boolean;
  public_path: string | null;
};

export type TPublicProfileUpdate = Partial<
  Pick<
    TPublicProfileSettings,
    "handle" | "profile_visibility" | "headline" | "bio" | "skills" | "github_url" | "linkedin_url" | "portfolio_url"
  >
>;

export type THandleAvailability = {
  handle: string;
  available: boolean;
  reason: string | null;
};

/** Field-level messages from the API, e.g. { handle: "That handle is already taken." }. */
export type TPublicProfileErrors = { errors?: Record<string, string> };

export class PublicProfileService extends APIService {
  constructor() {
    super(API_BASE_URL);
  }

  async getMine(): Promise<TPublicProfileSettings> {
    return this.get("/api/vj-startups/profile/me/")
      .then((res) => res?.data)
      .catch((err) => {
        throw err?.response?.data;
      });
  }

  async updateMine(payload: TPublicProfileUpdate): Promise<TPublicProfileSettings> {
    return this.patch("/api/vj-startups/profile/me/", payload)
      .then((res) => res?.data)
      .catch((err) => {
        throw err?.response?.data;
      });
  }

  async checkHandle(handle: string): Promise<THandleAvailability> {
    return this.get("/api/vj-startups/profile/handle-available/", { params: { handle } })
      .then((res) => res?.data)
      .catch((err) => {
        throw err?.response?.data;
      });
  }
}

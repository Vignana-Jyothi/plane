import { APIService } from "@plane/services";
import { API_BASE_URL } from "@plane/constants";

export class VJStartupsService extends APIService {
  constructor() {
    super(API_BASE_URL);
  }

  async createStartup(data: any): Promise<any> {
    return this.post("/api/vj-startups/admin/startups/", data)
      .then((res) => res.data)
      .catch((err) => {
        throw err?.response?.data || err;
      });
  }

  async fetchMetrics(): Promise<any> {
    return this.get("/api/vj-startups/admin/metrics/")
      .then((res) => res.data)
      .catch((err) => {
        throw err?.response?.data || err;
      });
  }

  async fetchStartups(): Promise<any[]> {
    return this.get("/api/vj-startups/admin/startups/")
      .then((res) => res.data)
      .catch((err) => {
        throw err?.response?.data || err;
      });
  }

  async updateStartup(slug: string, data: any): Promise<any> {
    return this.patch(`/api/vj-startups/admin/startups/${slug}/`, data)
      .then((res) => res.data)
      .catch((err) => {
        throw err?.response?.data || err;
      });
  }

  async deleteStartup(slug: string): Promise<any> {
    return this.delete(`/api/vj-startups/admin/startups/${slug}/`)
      .then((res) => res.data)
      .catch((err) => {
        throw err?.response?.data || err;
      });
  }

  async inviteToStartup(slug: string, emails: string): Promise<any> {
    return this.post(`/api/vj-startups/admin/startups/${slug}/invite/`, { emails })
      .then((res) => res.data)
      .catch((err) => {
        throw err?.response?.data || err;
      });
  }

  // WINGS
  async fetchWings(): Promise<any> {
    return this.get("/api/vj-startups/admin/wings/")
      .then((res) => res.data)
      .catch((err) => {
        throw err?.response?.data || err;
      });
  }

  async fetchWingMetrics(): Promise<any> {
    return this.get("/api/vj-startups/admin/wings/metrics/")
      .then((res) => res.data)
      .catch((err) => {
        throw err?.response?.data || err;
      });
  }

  async createWing(data: any): Promise<any> {
    return this.post("/api/vj-startups/admin/wings/", data)
      .then((res) => res.data)
      .catch((err) => {
        throw err?.response?.data || err;
      });
  }

  async updateWing(slug: string, data: any): Promise<any> {
    return this.patch(`/api/vj-startups/admin/wings/${slug}/`, data)
      .then((res) => res.data)
      .catch((err) => {
        throw err?.response?.data || err;
      });
  }

  async inviteToWing(slug: string, emails: string): Promise<any> {
    return this.post(`/api/vj-startups/admin/wings/${slug}/invite/`, { emails })
      .then((res) => res.data)
      .catch((err) => {
        throw err?.response?.data || err;
      });
  }

  async fetchWingMembers(slug: string): Promise<any> {
    return this.get(`/api/vj-startups/admin/wings/${slug}/members/`)
      .then((res) => res.data)
      .catch((err) => {
        throw err?.response?.data || err;
      });
  }

  async removeWingMember(slug: string, userId: string): Promise<any> {
    return this.delete(`/api/vj-startups/admin/wings/${slug}/members/${userId}/`)
      .then((res) => res.data)
      .catch((err) => {
        throw err?.response?.data || err;
      });
  }

  // EVENTS
  async fetchEvents(status?: string): Promise<any> {
    const url = status ? `/api/vj-startups/admin/events/?status=${status}` : "/api/vj-startups/admin/events/";
    return this.get(url)
      .then((res) => res.data)
      .catch((err) => {
        throw err?.response?.data || err;
      });
  }

  async createEvent(data: any): Promise<any> {
    return this.post("/api/vj-startups/admin/events/", data)
      .then((res) => res.data)
      .catch((err) => {
        throw err?.response?.data || err;
      });
  }

  async updateEvent(id: string, data: any): Promise<any> {
    return this.patch(`/api/vj-startups/admin/events/${id}/`, data)
      .then((res) => res.data)
      .catch((err) => {
        throw err?.response?.data || err;
      });
  }

  async deleteEvent(id: string): Promise<any> {
    return this.delete(`/api/vj-startups/admin/events/${id}/`)
      .then((res) => res.data)
      .catch((err) => {
        throw err?.response?.data || err;
      });
  }

  // MEMBERS
  async fetchMembers(): Promise<any> {
    return this.get("/api/vj-startups/admin/members/")
      .then((res) => res.data)
      .catch((err) => {
        throw err?.response?.data || err;
      });
  }

  async createMember(data: any): Promise<any> {
    return this.post("/api/vj-startups/admin/members/", data)
      .then((res) => res.data)
      .catch((err) => {
        throw err?.response?.data || err;
      });
  }

  async updateMember(id: string, data: any): Promise<any> {
    return this.patch(`/api/vj-startups/admin/members/${id}/`, data)
      .then((res) => res.data)
      .catch((err) => {
        throw err?.response?.data || err;
      });
  }

  async deleteMember(id: string): Promise<any> {
    return this.delete(`/api/vj-startups/admin/members/${id}/`)
      .then((res) => res.data)
      .catch((err) => {
        throw err?.response?.data || err;
      });
  }

  // MICROSERVICE ENDPOINTS (Proxied via Django)
  // On failure (e.g. VJ_MICROSERVICE_ADMIN_TOKEN missing/invalid), these resolve to an
  // empty-but-valid shape plus an `error` message, rather than throwing - callers should
  // check `.error` to distinguish "genuinely empty" from "couldn't reach the service".
  private microserviceErrorMessage(err: any): string {
    return (
      err?.response?.data?.error ||
      err?.response?.data?.message ||
      err?.message ||
      "Failed to reach the ecosystem service"
    );
  }

  async fetchMicroserviceUsers(page = 1, limit = 20, search = ""): Promise<any> {
    return this.get(
      `/api/vj-startups/admin/microservice/users/?page=${page}&limit=${limit}&search=${encodeURIComponent(search)}`
    )
      .then((res) => res.data)
      .catch((err) => {
        console.error("fetchMicroserviceUsers error:", err);
        return { users: [], total: 0, totalPages: 1, error: this.microserviceErrorMessage(err) };
      });
  }

  async updateMicroserviceUserRole(id: string, role: string): Promise<any> {
    return this.patch(`/api/vj-startups/admin/microservice/users/${id}/`, { role })
      .then((res) => res.data)
      .catch((err) => {
        console.error("updateMicroserviceUserRole error:", err);
        throw err?.response?.data || err;
      });
  }

  async deleteMicroserviceUser(id: string): Promise<any> {
    return this.delete(`/api/vj-startups/admin/microservice/users/${id}/`)
      .then((res) => res.data)
      .catch((err) => {
        console.error("deleteMicroserviceUser error:", err);
        throw err?.response?.data || err;
      });
  }

  async fetchMicroserviceIdeas(page = 1, limit = 20, search = ""): Promise<any> {
    return this.get(
      `/api/vj-startups/admin/microservice/ideas/?page=${page}&limit=${limit}&search=${encodeURIComponent(search)}`
    )
      .then((res) => res.data)
      .catch((err) => {
        console.error("fetchMicroserviceIdeas error:", err);
        return { ideas: [], total: 0, totalPages: 1, error: this.microserviceErrorMessage(err) };
      });
  }

  async fetchMicroserviceProblems(page = 1, limit = 20, search = ""): Promise<any> {
    return this.get(
      `/api/vj-startups/admin/microservice/problems/?page=${page}&limit=${limit}&search=${encodeURIComponent(search)}`
    )
      .then((res) => res.data)
      .catch((err) => {
        console.error("fetchMicroserviceProblems error:", err);
        return { problems: [], total: 0, totalPages: 1, error: this.microserviceErrorMessage(err) };
      });
  }

  async setMicroserviceProblemVerified(problemId: string, verified: boolean): Promise<any> {
    return this.patch(`/api/vj-startups/admin/microservice/problems/${problemId}/verify/`, { verified })
      .then((res) => res.data)
      .catch((err) => {
        console.error("setMicroserviceProblemVerified error:", err);
        throw err?.response?.data || err;
      });
  }

  async setMicroserviceIdeaVerified(ideaId: string, verified: boolean): Promise<any> {
    return this.patch(`/api/vj-startups/admin/microservice/ideas/${ideaId}/verify/`, { verified })
      .then((res) => res.data)
      .catch((err) => {
        console.error("setMicroserviceIdeaVerified error:", err);
        throw err?.response?.data || err;
      });
  }
}

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

  // MICROSERVICE ENDPOINTS (backend 2)
  private getMicroserviceUrl(path: string): string {
    const baseUrl = process.env.NEXT_PUBLIC_MICROSERVICE_URL || "http://localhost:6220";
    return `${baseUrl}/admin-api${path}`;
  }

  private getMicroserviceHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json"
    };
    const stored = typeof window !== "undefined" ? localStorage.getItem("vj_admin_user") : null;
    if (stored) {
      try {
        const user = JSON.parse(stored);
        if (user.adminToken) {
          headers["Authorization"] = `Bearer ${user.adminToken}`;
        }
      } catch {}
    }
    return headers;
  }

  async fetchMicroserviceUsers(page = 1, limit = 20, search = ""): Promise<any> {
    const url = this.getMicroserviceUrl(`/users?page=${page}&limit=${limit}&search=${encodeURIComponent(search)}`);
    return fetch(url, { headers: this.getMicroserviceHeaders() })
      .then((res) => res.json())
      .catch((err) => {
        console.error("fetchMicroserviceUsers error:", err);
        return { users: [], total: 0, totalPages: 1 };
      });
  }

  async updateMicroserviceUserRole(id: string, role: string): Promise<any> {
    const url = this.getMicroserviceUrl(`/users/${id}/role`);
    return fetch(url, {
      method: "PATCH",
      headers: this.getMicroserviceHeaders(),
      body: JSON.stringify({ role })
    })
      .then((res) => res.json())
      .catch((err) => {
        console.error("updateMicroserviceUserRole error:", err);
        throw err;
      });
  }

  async deleteMicroserviceUser(id: string): Promise<any> {
    const url = this.getMicroserviceUrl(`/users/${id}`);
    return fetch(url, {
      method: "DELETE",
      headers: this.getMicroserviceHeaders()
    })
      .then((res) => res.json())
      .catch((err) => {
        console.error("deleteMicroserviceUser error:", err);
        throw err;
      });
  }

  async fetchMicroserviceStartups(page = 1, limit = 20, search = ""): Promise<any> {
    const url = this.getMicroserviceUrl(`/startups?page=${page}&limit=${limit}&search=${encodeURIComponent(search)}`);
    return fetch(url, { headers: this.getMicroserviceHeaders() })
      .then((res) => res.json())
      .catch((err) => {
        console.error("fetchMicroserviceStartups error:", err);
        return { startups: [], total: 0, totalPages: 1 };
      });
  }

  async updateMicroserviceStartupStage(id: string, stage: number): Promise<any> {
    const url = this.getMicroserviceUrl(`/startups/${id}/stage`);
    return fetch(url, {
      method: "PATCH",
      headers: this.getMicroserviceHeaders(),
      body: JSON.stringify({ stage })
    })
      .then((res) => res.json())
      .catch((err) => {
        console.error("updateMicroserviceStartupStage error:", err);
        throw err;
      });
  }

  async fetchMicroserviceIdeas(page = 1, limit = 20, search = ""): Promise<any> {
    const url = this.getMicroserviceUrl(`/ideas?page=${page}&limit=${limit}&search=${encodeURIComponent(search)}`);
    return fetch(url, { headers: this.getMicroserviceHeaders() })
      .then((res) => res.json())
      .catch((err) => {
        console.error("fetchMicroserviceIdeas error:", err);
        return { ideas: [], total: 0, totalPages: 1 };
      });
  }

  async fetchMicroserviceProblems(page = 1, limit = 20, search = ""): Promise<any> {
    const url = this.getMicroserviceUrl(`/problems?page=${page}&limit=${limit}&search=${encodeURIComponent(search)}`);
    return fetch(url, { headers: this.getMicroserviceHeaders() })
      .then((res) => res.json())
      .catch((err) => {
        console.error("fetchMicroserviceProblems error:", err);
        return { problems: [], total: 0, totalPages: 1 };
      });
  }
}

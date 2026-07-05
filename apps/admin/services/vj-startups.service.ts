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
}

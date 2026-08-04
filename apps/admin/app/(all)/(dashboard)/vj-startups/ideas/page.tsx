"use client"

import React, { useState, useEffect } from "react";
import useSWR from "swr";
import { PageWrapper } from "@/components/common/page-wrapper";
import { Button } from "@plane/propel/button";
import { VJStartupsService } from "@/services/vj-startups.service";
import { Search, ChevronLeft, ChevronRight, RefreshCw, Lightbulb, Shield } from "lucide-react";

const vjStartupsService = new VJStartupsService();

export default function IdeasAuditPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [adminToken, setAdminToken] = useState("");

  useEffect(() => {
    const stored = localStorage.getItem("vj_admin_user");
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        if (parsed.adminToken) {
          setIsLoggedIn(true);
        }
      } catch {}
    }
  }, []);

  const handleLoginSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!adminToken.trim()) return;
    localStorage.setItem("vj_admin_user", JSON.stringify({ adminToken: adminToken.trim(), role: "admin" }));
    setIsLoggedIn(true);
    mutate();
  };

  const handleLogout = () => {
    localStorage.removeItem("vj_admin_user");
    setIsLoggedIn(false);
    setAdminToken("");
  };

  const { data, isLoading, mutate } = useSWR(
    isLoggedIn ? `VJ_IDEAS_${page}_${search}` : null,
    () => vjStartupsService.fetchMicroserviceIdeas(page, 20, search)
  );

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(query);
    setPage(1);
  };

  return (
    <PageWrapper
      header={{
        title: "Ecosystem Ideas",
        description: "Audit student concept submissions and ideas logged on the platform.",
      }}
    >
      {/* Integration Auth Configuration */}
      <div className="p-4 border border-subtle rounded bg-layer-1 flex flex-wrap items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <Shield className={`w-5 h-5 ${isLoggedIn ? "text-green-500" : "text-amber-500"}`} />
          <div>
            <h4 className="font-semibold text-primary text-13">VJ Startups Microservice Integration</h4>
            <p className="text-11 text-tertiary">
              {isLoggedIn 
                ? "Ecosystem connection established. Ideas list is synchronized."
                : "Enter your admin session token to connect and manage microservice resources."
              }
            </p>
          </div>
        </div>

        {isLoggedIn ? (
          <Button variant="secondary" size="sm" onClick={handleLogout}>
            Disconnect
          </Button>
        ) : (
          <form onSubmit={handleLoginSubmit} className="flex gap-2 w-full sm:w-auto">
            <input
              type="password"
              placeholder="Paste admin session token..."
              className="px-3 py-1 text-12 border border-subtle rounded bg-surface-2 outline-none focus:border-primary w-full sm:w-64"
              value={adminToken}
              onChange={(e) => setAdminToken(e.target.value)}
            />
            <Button variant="primary" size="sm" type="submit">
              Connect
            </Button>
          </form>
        )}
      </div>

      {!isLoggedIn ? (
        <div className="text-center py-12 text-tertiary text-13 border border-subtle border-dashed rounded-lg bg-surface-1">
          Please connect the microservice integration above to view student ideas.
        </div>
      ) : (
        <div className="space-y-4 animate-fade-in">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <form onSubmit={handleSearchSubmit} className="flex gap-2 max-w-md flex-1">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-tertiary" />
                <input
                  type="text"
                  className="w-full pl-9 pr-3 py-2 border border-subtle rounded text-13 bg-surface-2 outline-none focus:border-primary"
                  placeholder="Search by idea title..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
              </div>
              <Button variant="primary" type="submit">Search</Button>
            </form>
            <Button variant="secondary" onClick={() => mutate()} disabled={isLoading} className="flex items-center gap-1.5 text-13">
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>

          <div className="border border-subtle rounded-lg bg-surface-1 overflow-hidden shadow-sm">
            {isLoading ? (
              <div className="py-12 text-center text-tertiary text-13">Loading ideas...</div>
            ) : (
              <table className="w-full text-left text-13">
                <thead className="bg-layer-1 text-tertiary border-b border-subtle">
                  <tr>
                    <th className="px-6 py-3 font-medium">Idea</th>
                    <th className="px-6 py-3 font-medium">Submitted By</th>
                    <th className="px-6 py-3 font-medium">Upvotes</th>
                    <th className="px-6 py-3 font-medium">Created At</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-subtle">
                  {data?.ideas?.map((idea: any) => (
                    <tr key={idea._id} className="hover:bg-layer-2 transition-colors">
                      <td className="px-6 py-4">
                        <div className="font-semibold text-primary">{idea.title}</div>
                        {idea.description && <div className="text-11 text-tertiary mt-0.5 max-w-xl truncate">{idea.description}</div>}
                      </td>
                      <td className="px-6 py-4 text-secondary">{idea.submittedBy || "—"}</td>
                      <td className="px-6 py-4 font-semibold text-secondary">{idea.upvotes ?? 0}</td>
                      <td className="px-6 py-4 text-tertiary">{new Date(idea.createdAt).toLocaleDateString()}</td>
                    </tr>
                  ))}
                  {(!data?.ideas || data.ideas.length === 0) && (
                    <tr>
                      <td colSpan={4} className="px-6 py-12 text-center text-tertiary">
                        <div className="flex flex-col items-center justify-center gap-1">
                          <Lightbulb className="w-8 h-8 text-tertiary mb-1" />
                          <p className="font-medium text-secondary">No ideas found.</p>
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            )}

            {data?.totalPages > 1 && (
              <div className="px-6 py-3.5 border-t border-subtle bg-layer-1 flex items-center justify-between text-12 text-tertiary">
                <span>Page {page} of {data.totalPages}</span>
                <div className="flex items-center gap-1.5">
                  <button
                    disabled={page <= 1}
                    onClick={() => setPage(page - 1)}
                    className="p-1 border border-subtle rounded hover:bg-surface-2 transition-colors disabled:opacity-50"
                  >
                    <ChevronLeft className="w-3.5 h-3.5" />
                  </button>
                  <button
                    disabled={page >= data.totalPages}
                    onClick={() => setPage(page + 1)}
                    className="p-1 border border-subtle rounded hover:bg-surface-2 transition-colors disabled:opacity-50"
                  >
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </PageWrapper>
  );
}

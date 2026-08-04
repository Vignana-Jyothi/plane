"use client"

import React, { useState, useEffect } from "react";
import useSWR from "swr";
import { PageWrapper } from "@/components/common/page-wrapper";
import { Button } from "@plane/propel/button";
import { VJStartupsService } from "@/services/vj-startups.service";
import { Search, ChevronLeft, ChevronRight, RefreshCw, Shield, Users } from "lucide-react";

const vjStartupsService = new VJStartupsService();

export default function UsersAuditPage() {
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
    isLoggedIn ? `VJ_USERS_${page}_${search}` : null,
    () => vjStartupsService.fetchMicroserviceUsers(page, 20, search)
  );

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(query);
    setPage(1);
  };

  const handleRoleToggle = async (id: string, currentRole: string) => {
    const nextRole = currentRole === "admin" ? "user" : "admin";
    try {
      await vjStartupsService.updateMicroserviceUserRole(id, nextRole);
      mutate();
    } catch (err) {
      console.error(err);
      alert("Failed to toggle user role.");
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to delete user "${name}"? This cannot be undone.`)) return;
    try {
      await vjStartupsService.deleteMicroserviceUser(id);
      mutate();
    } catch (err) {
      console.error(err);
      alert("Failed to delete user.");
    }
  };

  return (
    <PageWrapper
      header={{
        title: "Ecosystem Users",
        description: "Audit and manage user accounts registered on the public ecosystem website.",
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
                ? "Ecosystem connection established. Users list is synchronized."
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
          Please connect the microservice integration above to view website users.
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
                  placeholder="Search users by name or email..."
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
              <div className="py-12 text-center text-tertiary text-13">Loading users...</div>
            ) : (
              <table className="w-full text-left text-13">
                <thead className="bg-layer-1 text-tertiary border-b border-subtle">
                  <tr>
                    <th className="px-6 py-3 font-medium">User</th>
                    <th className="px-6 py-3 font-medium">Email</th>
                    <th className="px-6 py-3 font-medium">Role</th>
                    <th className="px-6 py-3 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-subtle">
                  {data?.users?.map((u: any) => (
                    <tr key={u._id} className="hover:bg-layer-2 transition-colors">
                      <td className="px-6 py-4 flex items-center gap-2.5">
                        <img
                          src={u.picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(u.name)}&background=7c3aed&color=fff&size=32`}
                          alt={u.name}
                          className="w-7 h-7 rounded-full object-cover border border-subtle"
                        />
                        <span className="font-semibold text-primary">{u.name}</span>
                      </td>
                      <td className="px-6 py-4 text-tertiary font-mono text-12">{u.email}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-0.5 rounded text-10 font-semibold uppercase ${
                          u.role === "admin" ? "bg-violet-500/10 text-violet-500 border border-violet-500/20" : "bg-surface-2 text-tertiary border border-subtle"
                        }`}>
                          {u.role}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button variant="secondary" size="sm" onClick={() => handleRoleToggle(u._id, u.role)}>
                            {u.role === "admin" ? "Demote" : "Make Admin"}
                          </Button>
                          <Button variant="error-fill" size="sm" onClick={() => handleDelete(u._id, u.name)}>
                            Delete
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {(!data?.users || data.users.length === 0) && (
                    <tr>
                      <td colSpan={4} className="px-6 py-12 text-center text-tertiary">
                        <div className="flex flex-col items-center justify-center gap-1">
                          <Users className="w-8 h-8 text-tertiary mb-1" />
                          <p className="font-medium text-secondary">No users found.</p>
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

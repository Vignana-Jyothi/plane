"use client";

import React, { useState } from "react";
import useSWR from "swr";
import { PageWrapper } from "@/components/common/page-wrapper";
import { Button } from "@plane/propel/button";
import { VJStartupsService } from "@/services/vj-startups.service";
import { Search, ChevronLeft, ChevronRight, RefreshCw, Users, AlertCircle } from "lucide-react";

const vjStartupsService = new VJStartupsService();

export default function UsersAuditPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");

  const { data, isLoading, mutate } = useSWR(`VJ_USERS_${page}_${search}`, () =>
    vjStartupsService.fetchMicroserviceUsers(page, 20, search)
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
      <div className="animate-fade-in space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <form onSubmit={handleSearchSubmit} className="flex max-w-md flex-1 gap-2">
            <div className="relative flex-1">
              <Search className="absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-tertiary" />
              <input
                type="text"
                className="focus:border-primary w-full rounded border border-subtle bg-surface-2 py-2 pr-3 pl-9 text-13 outline-none"
                placeholder="Search users by name or email..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
            <Button variant="primary" type="submit">
              Search
            </Button>
          </form>
          <Button
            variant="secondary"
            onClick={() => mutate()}
            disabled={isLoading}
            className="flex items-center gap-1.5 text-13"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>

        <div className="shadow-sm overflow-hidden rounded-lg border border-subtle bg-surface-1">
          {isLoading ? (
            <div className="py-12 text-center text-13 text-tertiary">Loading users...</div>
          ) : (
            <table className="w-full text-left text-13">
              <thead className="border-b border-subtle bg-layer-1 text-tertiary">
                <tr>
                  <th className="px-6 py-3 font-medium">User</th>
                  <th className="px-6 py-3 font-medium">Email</th>
                  <th className="px-6 py-3 font-medium">Role</th>
                  <th className="px-6 py-3 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-subtle">
                {data?.users?.map((u: any) => (
                  <tr key={u._id} className="transition-colors hover:bg-layer-2">
                    <td className="flex items-center gap-2.5 px-6 py-4">
                      <img
                        src={
                          u.picture ||
                          `https://ui-avatars.com/api/?name=${encodeURIComponent(u.name)}&background=7c3aed&color=fff&size=32`
                        }
                        alt={u.name}
                        className="h-7 w-7 rounded-full border border-subtle object-cover"
                      />
                      <span className="font-semibold text-primary">{u.name}</span>
                    </td>
                    <td className="font-mono px-6 py-4 text-12 text-tertiary">{u.email}</td>
                    <td className="px-6 py-4">
                      <span
                        className={`rounded px-2 py-0.5 text-10 font-semibold uppercase ${
                          u.role === "admin"
                            ? "bg-violet-500/10 text-violet-500 border-violet-500/20 border"
                            : "border border-subtle bg-surface-2 text-tertiary"
                        }`}
                      >
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
                {data?.error ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-12 text-center">
                      <div className="flex flex-col items-center justify-center gap-1">
                        <AlertCircle className="text-red-500 mb-1 h-8 w-8" />
                        <p className="text-red-500 font-medium">Could not load users from the ecosystem service.</p>
                        <p className="max-w-md text-11 text-tertiary">
                          {data.error} — check VJ_MICROSERVICE_URL / VJ_MICROSERVICE_ADMIN_TOKEN in the API's
                          environment.
                        </p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  (!data?.users || data.users.length === 0) && (
                    <tr>
                      <td colSpan={4} className="px-6 py-12 text-center text-tertiary">
                        <div className="flex flex-col items-center justify-center gap-1">
                          <Users className="mb-1 h-8 w-8 text-tertiary" />
                          <p className="font-medium text-secondary">No users found.</p>
                        </div>
                      </td>
                    </tr>
                  )
                )}
              </tbody>
            </table>
          )}

          {data?.totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-subtle bg-layer-1 px-6 py-3.5 text-12 text-tertiary">
              <span>
                Page {page} of {data.totalPages}
              </span>
              <div className="flex items-center gap-1.5">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage(page - 1)}
                  className="rounded border border-subtle p-1 transition-colors hover:bg-surface-2 disabled:opacity-50"
                >
                  <ChevronLeft className="h-3.5 w-3.5" />
                </button>
                <button
                  disabled={page >= data.totalPages}
                  onClick={() => setPage(page + 1)}
                  className="rounded border border-subtle p-1 transition-colors hover:bg-surface-2 disabled:opacity-50"
                >
                  <ChevronRight className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </PageWrapper>
  );
}

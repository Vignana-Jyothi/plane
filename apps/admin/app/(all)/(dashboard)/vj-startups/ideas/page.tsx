"use client";

import React, { useState } from "react";
import useSWR from "swr";
import { PageWrapper } from "@/components/common/page-wrapper";
import { Button } from "@plane/propel/button";
import { VJStartupsService } from "@/services/vj-startups.service";
import { Search, ChevronLeft, ChevronRight, RefreshCw, Lightbulb, AlertCircle, CheckCircle2 } from "lucide-react";

const vjStartupsService = new VJStartupsService();

export default function IdeasAuditPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [verifyingId, setVerifyingId] = useState<string | null>(null);

  const { data, isLoading, mutate } = useSWR(`VJ_IDEAS_${page}_${search}`, () =>
    vjStartupsService.fetchMicroserviceIdeas(page, 20, search)
  );

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(query);
    setPage(1);
  };

  const handleSetVerified = async (ideaId: string, verified: boolean) => {
    setVerifyingId(ideaId);
    try {
      await vjStartupsService.setMicroserviceIdeaVerified(ideaId, verified);
      mutate();
    } catch (err) {
      console.error("Failed to update verification status:", err);
      alert("Failed to update verification status. Check the console for details.");
    } finally {
      setVerifyingId(null);
    }
  };

  return (
    <PageWrapper
      header={{
        title: "Ecosystem Ideas",
        description: "Audit student concept submissions and ideas logged on the platform.",
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
                placeholder="Search by idea title..."
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
            <div className="py-12 text-center text-13 text-tertiary">Loading ideas...</div>
          ) : (
            <table className="w-full text-left text-13">
              <thead className="border-b border-subtle bg-layer-1 text-tertiary">
                <tr>
                  <th className="px-6 py-3 font-medium">Idea</th>
                  <th className="px-6 py-3 font-medium">Submitted By</th>
                  <th className="px-6 py-3 font-medium">Upvotes</th>
                  <th className="px-6 py-3 font-medium">Created At</th>
                  <th className="px-6 py-3 font-medium">Status</th>
                  <th className="px-6 py-3 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-subtle">
                {data?.ideas?.map((idea: any) => (
                  <tr key={idea._id} className="transition-colors hover:bg-layer-2">
                    <td className="px-6 py-4">
                      <div className="font-semibold text-primary">{idea.title}</div>
                      {idea.description && (
                        <div className="mt-0.5 max-w-xl truncate text-11 text-tertiary">{idea.description}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 text-secondary">{idea.addedByName || "—"}</td>
                    <td className="px-6 py-4 font-semibold text-secondary">{idea.upvotes ?? 0}</td>
                    <td className="px-6 py-4 text-tertiary">{new Date(idea.createdAt).toLocaleDateString()}</td>
                    <td className="px-6 py-4">
                      {idea.verified ? (
                        <span className="border-green-500/20 bg-green-500/10 text-green-500 inline-flex items-center gap-1 rounded border px-2 py-0.5 text-10 font-medium">
                          <CheckCircle2 className="h-3 w-3" /> Verified
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded border border-subtle bg-surface-2 px-2 py-0.5 text-10 font-medium text-tertiary">
                          Pending
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      {idea.verified ? (
                        <Button
                          variant="secondary"
                          size="sm"
                          disabled={verifyingId === idea.ideaId}
                          onClick={() => handleSetVerified(idea.ideaId, false)}
                        >
                          Unverify
                        </Button>
                      ) : (
                        <Button
                          variant="primary"
                          size="sm"
                          disabled={verifyingId === idea.ideaId}
                          onClick={() => handleSetVerified(idea.ideaId, true)}
                          className="flex items-center gap-1"
                        >
                          <CheckCircle2 className="h-3.5 w-3.5" /> Approve
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
                {data?.error ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center">
                      <div className="flex flex-col items-center justify-center gap-1">
                        <AlertCircle className="text-red-500 mb-1 h-8 w-8" />
                        <p className="text-red-500 font-medium">Could not load ideas from the ecosystem service.</p>
                        <p className="max-w-md text-11 text-tertiary">
                          {data.error} — check VJ_MICROSERVICE_URL / VJ_MICROSERVICE_ADMIN_TOKEN in the API's
                          environment.
                        </p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  (!data?.ideas || data.ideas.length === 0) && (
                    <tr>
                      <td colSpan={6} className="px-6 py-12 text-center text-tertiary">
                        <div className="flex flex-col items-center justify-center gap-1">
                          <Lightbulb className="mb-1 h-8 w-8 text-tertiary" />
                          <p className="font-medium text-secondary">No ideas found.</p>
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

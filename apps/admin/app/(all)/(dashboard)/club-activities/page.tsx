import React, { useState } from "react";
import useSWR, { mutate as globalMutate } from "swr";
import { useNavigate } from "react-router";
import { PageWrapper } from "@/components/common/page-wrapper";
import { Button } from "@plane/propel/button";
import { VJStartupsService } from "@/services/vj-startups.service";
import { CreateWingModal } from "@/components/club-activities/create-wing-modal";
import { EditWingModal } from "@/components/club-activities/edit-wing-modal";
import { UpcomingEventsKanban } from "@/components/club-activities/upcoming-events-kanban";

const vjStartupsService = new VJStartupsService();

export default function ClubActivitiesDashboard() {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const { data: metrics } = useSWR("VJ_WINGS_METRICS", () => vjStartupsService.fetchWingMetrics());

  return (
    <PageWrapper
      header={{
        title: "Club Activities (Wings)",
        description: "Monitor events, performance, and cross-wing collaboration.",
        actions: (
          <Button variant="primary" onClick={() => setIsCreateModalOpen(true)}>
            + Create Wing
          </Button>
        ),
      }}
    >
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <MetricCard title="Total Events" value={metrics?.total_events || "-"} />
        <MetricCard title="Active Wings" value={metrics?.active_wings || "-"} />
        <MetricCard title="Engagement Score" value={metrics?.engagement_score || "-"} />
      </div>

      <div className="mt-8">
        <WingList />
      </div>

      <div className="mt-8 space-y-4">
        <div className="text-16 font-medium text-primary border-b border-subtle pb-1.5 flex items-center justify-between">
          <span>Upcoming Activities</span>
        </div>
        <div className="w-full bg-surface-1 border border-subtle rounded-lg">
          <UpcomingEventsKanban />
        </div>
      </div>

      <CreateWingModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={() => {
          globalMutate("VJ_WINGS_LIST");
          globalMutate("VJ_WINGS_METRICS");
        }}
      />
    </PageWrapper>
  );
}

function WingList() {
  const navigate = useNavigate();
  const { data: wings } = useSWR("VJ_WINGS_LIST", () => vjStartupsService.fetchWings());
  const [selectedWing, setSelectedWing] = useState<any>(null);

  if (!wings) return <div className="text-sm text-tertiary">Loading wings...</div>;

  return (
    <div className="border border-subtle rounded-lg bg-surface-1 overflow-hidden">
      <div className="px-6 py-4 border-b border-subtle">
        <h3 className="text-16 font-medium text-primary">Wings Directory</h3>
      </div>
      <table className="w-full text-left text-13">
        <thead className="bg-layer-1 text-tertiary border-b border-subtle">
          <tr>
            <th className="px-6 py-3 font-medium">Name</th>
            <th className="px-6 py-3 font-medium">Slug</th>
            <th className="px-6 py-3 font-medium">Description</th>
            <th className="px-6 py-3 font-medium">Color</th>
            <th className="px-6 py-3 font-medium text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-subtle">
          {wings.map((wing: any) => (
            <tr 
              key={wing.id} 
              className="hover:bg-layer-1 cursor-pointer transition-colors"
              onClick={() => navigate(`/club-activities/${wing.slug}`)}
            >
              <td className="px-6 py-4 font-medium text-primary">{wing.name}</td>
              <td className="px-6 py-4 text-tertiary">{wing.slug}</td>
              <td className="px-6 py-4 text-tertiary truncate max-w-xs">{wing.description || "-"}</td>
              <td className="px-6 py-4">
                {wing.color ? (
                  <div className="flex items-center gap-2">
                    <span className="w-4 h-4 rounded shadow-sm border border-subtle" style={{ backgroundColor: wing.color }} />
                    <span className="text-tertiary font-mono uppercase">{wing.color}</span>
                  </div>
                ) : (
                  <span className="text-tertiary">-</span>
                )}
              </td>
              <td className="px-6 py-4 text-right">
                <Button 
                  variant="secondary" 
                  size="sm" 
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedWing(wing);
                  }}
                >
                  Edit
                </Button>
              </td>
            </tr>
          ))}
          {wings.length === 0 && (
            <tr>
              <td colSpan={5} className="px-6 py-8 text-center text-tertiary">No wings found.</td>
            </tr>
          )}
        </tbody>
      </table>

      <EditWingModal 
        isOpen={!!selectedWing}
        wing={selectedWing}
        onClose={() => setSelectedWing(null)}
        onSuccess={() => {
          globalMutate("VJ_WINGS_LIST");
          globalMutate("VJ_WINGS_METRICS");
        }}
      />
    </div>
  );
}

function MetricCard({ title, value }: { title: string; value: string }) {
  return (
    <div className="p-4 border border-subtle rounded-lg bg-surface-1 shadow-sm">
      <h3 className="text-13 text-tertiary font-medium">{title}</h3>
      <p className="text-24 font-semibold mt-2 text-primary">{value}</p>
    </div>
  );
}

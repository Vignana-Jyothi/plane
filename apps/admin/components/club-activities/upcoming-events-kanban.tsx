import React from "react";
import useSWR from "swr";
import { Clock, Calendar, CheckCircle2 } from "lucide-react";
import { VJStartupsService } from "@/services/vj-startups.service";

const vjStartupsService = new VJStartupsService();

export function UpcomingEventsKanban() {
  const { data: events } = useSWR("VJ_EVENTS_LIST", () => vjStartupsService.fetchEvents());

  const upcomingEvents = events?.filter((e: any) => e.status === "upcoming") || [];
  const inProgressEvents = events?.filter((e: any) => e.status === "in_progress") || [];
  const completedEvents = events?.filter((e: any) => e.status === "completed") || [];

  const columns = [
    {
      title: "Upcoming",
      icon: <Calendar className="h-4 w-4 text-primary" />,
      events: upcomingEvents,
    },
    {
      title: "In Progress",
      icon: <Clock className="text-orange-500 h-4 w-4" />,
      events: inProgressEvents,
    },
    {
      title: "Completed",
      icon: <CheckCircle2 className="text-green-500 h-4 w-4" />,
      events: completedEvents,
    },
  ];

  return (
    <div className="flex min-h-[400px] w-full flex-col gap-4 overflow-x-auto p-4 md:flex-row">
      {columns.map((col, i) => (
        <div key={i} className="flex min-w-[280px] flex-1 flex-col rounded-lg border border-subtle bg-surface-2 p-3">
          <div className="mb-4 flex items-center gap-2 px-2 pt-1">
            {col.icon}
            <h4 className="text-14 font-medium text-primary">{col.title}</h4>
            <span className="ml-auto rounded bg-surface-1 px-2 py-0.5 text-12 font-medium text-tertiary">
              {col.events.length}
            </span>
          </div>

          <div className="flex flex-1 flex-col gap-3">
            {col.events.map((event: any) => (
              <div
                key={event.id}
                className="hover:border-primary/50 shadow-sm group cursor-pointer rounded-lg border border-subtle bg-surface-1 p-3 transition-colors"
              >
                <div className="mb-2 flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full" style={{ backgroundColor: event.wing_color || "#94a3b8" }} />
                  <span className="tracking-wider text-11 font-medium text-tertiary uppercase">
                    {event.wing_name || "General"}
                  </span>
                </div>
                <h5 className="mb-3 text-14 font-medium text-primary group-hover:text-primary">{event.title}</h5>
                <div className="flex items-center gap-2 text-12 text-tertiary">
                  <Calendar className="h-3 w-3" />
                  {new Date(event.scheduled_at).toLocaleDateString()}
                </div>
              </div>
            ))}

            {col.events.length === 0 && (
              <div className="flex min-h-[120px] flex-1 items-center justify-center rounded-lg border-2 border-dashed border-subtle text-12 text-tertiary">
                No events
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

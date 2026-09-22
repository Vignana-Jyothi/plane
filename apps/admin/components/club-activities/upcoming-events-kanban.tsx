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
      icon: <Calendar className="w-4 h-4 text-primary" />,
      events: upcomingEvents
    },
    {
      title: "In Progress",
      icon: <Clock className="w-4 h-4 text-orange-500" />,
      events: inProgressEvents
    },
    {
      title: "Completed",
      icon: <CheckCircle2 className="w-4 h-4 text-green-500" />,
      events: completedEvents
    }
  ];

  return (
    <div className="w-full flex flex-col md:flex-row gap-4 p-4 overflow-x-auto min-h-[400px]">
      {columns.map((col, i) => (
        <div key={i} className="flex-1 min-w-[280px] bg-surface-2 rounded-lg border border-subtle p-3 flex flex-col">
          <div className="flex items-center gap-2 mb-4 px-2 pt-1">
            {col.icon}
            <h4 className="text-14 font-medium text-primary">{col.title}</h4>
            <span className="ml-auto text-12 font-medium bg-surface-1 px-2 py-0.5 rounded text-tertiary">
              {col.events.length}
            </span>
          </div>
          
          <div className="flex flex-col gap-3 flex-1">
            {col.events.map((event: any) => (
              <div 
                key={event.id}
                className="bg-surface-1 border border-subtle rounded-lg p-3 hover:border-primary/50 transition-colors cursor-pointer shadow-sm group"
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: event.wing_color || "#94a3b8" }} />
                  <span className="text-11 font-medium text-tertiary uppercase tracking-wider">{event.wing_name || "General"}</span>
                </div>
                <h5 className="text-14 font-medium text-primary group-hover:text-primary mb-3">
                  {event.title}
                </h5>
                <div className="flex items-center gap-2 text-12 text-tertiary">
                  <Calendar className="w-3 h-3" />
                  {new Date(event.scheduled_at).toLocaleDateString()}
                </div>
              </div>
            ))}
            
            {col.events.length === 0 && (
              <div className="flex-1 flex items-center justify-center border-2 border-dashed border-subtle rounded-lg text-tertiary text-12 min-h-[120px]">
                No events
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

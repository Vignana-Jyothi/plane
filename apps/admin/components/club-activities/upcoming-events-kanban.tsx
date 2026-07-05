import React from "react";
import { Clock, Calendar, CheckCircle2 } from "lucide-react";

export function UpcomingEventsKanban() {
  // Mocked for the initial UI layout
  const columns = [
    {
      title: "Upcoming",
      icon: <Calendar className="w-4 h-4 text-primary" />,
      events: []
    },
    {
      title: "In Progress",
      icon: <Clock className="w-4 h-4 text-orange-500" />,
      events: []
    },
    {
      title: "Completed",
      icon: <CheckCircle2 className="w-4 h-4 text-green-500" />,
      events: []
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
            {col.events.map((event) => (
              <div 
                key={event.id}
                className="bg-surface-1 border border-subtle rounded-lg p-3 hover:border-primary/50 transition-colors cursor-pointer shadow-sm group"
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: event.wingColor }} />
                  <span className="text-11 font-medium text-tertiary uppercase tracking-wider">{event.wing}</span>
                </div>
                <h5 className="text-14 font-medium text-primary group-hover:text-primary mb-3">
                  {event.title}
                </h5>
                <div className="flex items-center gap-2 text-12 text-tertiary">
                  <Calendar className="w-3 h-3" />
                  {event.date}
                </div>
              </div>
            ))}
            
            {col.events.length === 0 && (
              <div className="flex-1 flex items-center justify-center border-2 border-dashed border-subtle rounded-lg text-tertiary text-12">
                No events
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

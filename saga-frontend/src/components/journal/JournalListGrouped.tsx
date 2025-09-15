
"use client";

import { useMemo } from "react";
import type { JournalEntry } from "@/lib/types";
import { JournalEntryCard } from "./JournalEntryCard";
import { format, isSameDay } from "date-fns";
import { Separator } from "../ui/separator";

type JournalListGroupedProps = {
  entries: JournalEntry[];
  selectedEntry: JournalEntry | null;
  onSelectEntry: (entry: JournalEntry) => void;
  onDeleteEntry: (id: string) => void;
};

export function JournalListGrouped({
  entries,
  selectedEntry,
  onSelectEntry,
  onDeleteEntry,
}: JournalListGroupedProps) {
  const groupedEntries = useMemo(() => {
    const groups: { [key: string]: JournalEntry[] } = {};
    entries.forEach((entry) => {
      const date = format(new Date(entry.date), "yyyy-MM-dd");
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(entry);
    });
    return Object.entries(groups).sort(
      (a, b) => new Date(b[0]).getTime() - new Date(a[0]).getTime()
    );
  }, [entries]);

  if (entries.length === 0) {
    return (
      <div className="p-4 text-center text-sm text-muted-foreground">
        Your saga is yet unwritten.
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      {groupedEntries.map(([date, entriesInGroup], index) => (
        <div key={date}>
          <h3 className="text-sm font-semibold text-muted-foreground mb-2 px-2">
            {format(new Date(date), "MMMM d, yyyy")}
          </h3>
          <div className="space-y-2">
            {entriesInGroup.map((entry) => (
              <JournalEntryCard
                key={entry.id}
                entry={entry}
                onSelect={() => onSelectEntry(entry)}
                onDelete={() => onDeleteEntry(entry.id)}
                isSelected={selectedEntry?.id === entry.id}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

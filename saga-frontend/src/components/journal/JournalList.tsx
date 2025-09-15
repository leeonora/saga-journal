
"use client";

import type { JournalEntry } from "@/lib/types";
import { JournalEntryCard } from "./JournalEntryCard";
import { Accordion } from "../ui/accordion";
import { cn } from "@/lib/utils";

type JournalListProps = {
  entries: JournalEntry[];
  onSelectEntry: (entry: JournalEntry) => void;
  onDeleteEntry: (id: string) => void;
  selectedEntry: JournalEntry | null;
  className?: string;
};

export function JournalList({ entries, onSelectEntry, onDeleteEntry, selectedEntry, className }: JournalListProps) {
  if (entries.length === 0) {
    return (
      <div className="p-4 text-center text-sm text-muted-foreground">
        No entries for this day.
      </div>
    );
  }

  return (
    <div className={cn("space-y-2", className)}>
      <Accordion type="single" collapsible className="w-full" value={selectedEntry?.id}>
        {entries.map((entry) => (
          <JournalEntryCard 
            key={entry.id} 
            entry={entry}
            onSelect={() => onSelectEntry(entry)}
            onDelete={() => onDeleteEntry(entry.id)}
            isSelected={selectedEntry?.id === entry.id}
          />
        ))}
      </Accordion>
    </div>
  );
}

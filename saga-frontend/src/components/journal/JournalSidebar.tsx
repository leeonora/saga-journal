
"use client";

import { useState, useMemo, useEffect } from "react";
import { Calendar } from "@/components/ui/calendar";
import { JournalList } from "./JournalList";
import type { JournalEntry } from "@/lib/types";
import { BookCopy, Calendar as CalendarIcon } from "lucide-react";
import { Separator } from "../ui/separator";
import { ScrollArea } from "../ui/scroll-area";
import { isSameDay, format, parseISO } from "date-fns";
import { Tabs, TabsList, TabsTrigger } from "../ui/tabs";
import { JournalListGrouped } from "./JournalListGrouped";
import type { SidebarView } from "@/app/page";

type JournalSidebarProps = {
  entries: JournalEntry[];
  selectedEntry: JournalEntry | null;
  onSelectEntry: (entry: JournalEntry | null) => void;
  onDeleteEntry: (id: string) => void;
  onCreateNew: () => void;
  view: SidebarView;
  onViewChange: (view: SidebarView) => void;
};

export function JournalSidebar({
  entries,
  selectedEntry,
  onSelectEntry,
  onDeleteEntry,
  onCreateNew,
  view,
  onViewChange,
}: JournalSidebarProps) {
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(
    selectedEntry && selectedEntry.date ? parseISO(selectedEntry.date) : new Date()
  );

  useEffect(() => {
    if (selectedEntry && selectedEntry.date) {
      const entryDate = parseISO(selectedEntry.date);
      if (!selectedDate || !isSameDay(entryDate, selectedDate)) {
        setSelectedDate(entryDate);
      }
    }
  }, [selectedEntry, selectedDate]);


  const entryDates = useMemo(() => {
    return entries.map((entry) => new Date(entry.date));
  }, [entries]);

  const entriesForSelectedDate = useMemo(() => {
    if (!selectedDate) return [];
    return entries
        .filter((entry) => isSameDay(new Date(entry.date), selectedDate))
        .sort((a,b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  }, [entries, selectedDate]);
  
  const handleDateSelect = (date: Date | undefined) => {
    setSelectedDate(date);
    const entriesOnDate = entries
        .filter((entry) => date && isSameDay(new Date(entry.date), date))
        .sort((a,b) => new Date(b.date).getTime() - new Date(a.date).getTime());
    
    if (entriesOnDate.length > 0) {
      if(selectedEntry?.id !== entriesOnDate[0].id) {
        onSelectEntry(entriesOnDate[0]);
      }
    } else {
      onSelectEntry(null);
    }
  }

  return (
    <div className="h-full flex flex-col bg-card">
      <div className="p-4 space-y-4">
        <div className="flex items-center justify-between pt-2">
            <h2 className="flex items-center gap-2 text-lg font-headline text-foreground/80">
              Entries
            </h2>
             <Tabs value={view} onValueChange={(v) => onViewChange(v as "calendar" | "list")} className="w-auto">
              <TabsList>
                <TabsTrigger value="calendar"><CalendarIcon className="w-4 h-4" /></TabsTrigger>
                <TabsTrigger value="list"><BookCopy className="w-4 h-4" /></TabsTrigger>
              </TabsList>
            </Tabs>
        </div>
      </div>
      <Separator />

      <ScrollArea className="flex-1">
        {view === 'calendar' ? (
          <>
            <div className="p-4">
                <Calendar
                  mode="single"
                  selected={selectedDate}
                  onSelect={handleDateSelect}
                  modifiers={{
                    hasEntry: entryDates,
                  }}
                  modifiersStyles={{
                    hasEntry: {
                        fontWeight: 'bold',
                        textDecoration: 'underline',
                        textDecorationColor: 'hsl(var(--accent))',
                        textDecorationThickness: '2px',
                        textUnderlineOffset: '0.2rem',
                    },
                  }}
                  className="rounded-md"
                />
            </div>
            <Separator />
            <div className="flex-1 flex flex-col min-h-0">
              <h2 className="p-4 flex items-center gap-2 text-lg font-headline text-foreground/80">
                <BookCopy className="w-5 h-5" />
                Entries for {selectedDate ? format(selectedDate, 'PPP') : '...'}
              </h2>
                <JournalList
                  entries={entriesForSelectedDate}
                  onSelectEntry={onSelectEntry}
                  onDeleteEntry={onDeleteEntry}
                  selectedEntry={selectedEntry}
                  className="px-4 pb-4"
                />
            </div>
          </>
        ) : (
          <JournalListGrouped
            entries={entries}
            selectedEntry={selectedEntry}
            onSelectEntry={onSelectEntry}
            onDeleteEntry={onDeleteEntry}
          />
        )}
      </ScrollArea>
    </div>
  );
}

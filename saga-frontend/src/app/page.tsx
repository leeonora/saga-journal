
"use client";

import { useState, useEffect } from "react";
import { JournalEditor } from "@/components/journal/JournalEditor";
import { useJournal } from "@/hooks/useJournal";
import { Menu, PlusCircle } from "lucide-react";
import { JournalSidebar } from "@/components/journal/JournalSidebar";
import type { JournalEntry } from "@/lib/types";
import { JournalEntryDisplay } from "@/components/journal/JournalEntryDisplay";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { cn } from "@/lib/utils";
import { SagaLogo } from "@/components/common/SagaLogo";

export type SidebarView = "calendar" | "list";

export default function Home() {
  const { entries, addEntry, updateEntry, isLoaded, deleteEntry } = useJournal();
  const [selectedEntry, setSelectedEntry] = useState<JournalEntry | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [mobileSheetOpen, setMobileSheetOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sidebarView, setSidebarView] = useState<SidebarView>("calendar");
  
  // Set initial entry on load
  useEffect(() => {
    if (isLoaded && entries.length > 0 && selectedEntry === null && !isEditing) {
      setSelectedEntry(entries[0]);
    }
     if (isLoaded && entries.length === 0) {
      setIsEditing(true); // If no entries, start with the editor open
      setSelectedEntry(null);
    }
  }, [isLoaded, entries, selectedEntry, isEditing]);

  const handleSelectEntry = (entry: JournalEntry | null) => {
    setSelectedEntry(entry);
    setIsEditing(false); // Exit editing mode when selecting a new entry
    setMobileSheetOpen(false); // Close sheet on selection
  };
  
  const handleDeleteEntry = (id: string) => {
    const entryIndex = entries.findIndex(e => e.id === id);
    deleteEntry(id);
    if (selectedEntry?.id === id) {
      // Select the next entry in the list, or the previous one if it was the last
      const nextEntry = entries[entryIndex + 1] || entries[entryIndex - 1] || null;
      setSelectedEntry(nextEntry);
      if (!nextEntry) {
        setIsEditing(true);
      }
    }
  }

  const handleNewEntryClick = () => {
    setSelectedEntry(null);
    setIsEditing(true);
  };
  
  const handleEditClick = () => {
    if (selectedEntry) {
        setIsEditing(true);
    }
  };


  const handleSave = async (content: string, date: Date, promptType: any, prompt: any, title: any) => {
    if (isEditing && selectedEntry) {
        // Update existing entry
        const updated = await updateEntry(selectedEntry.id, content, date, promptType, prompt, title);
        if (updated) {
            setSelectedEntry(updated);
        }
    } else {
        // Add new entry
        const newEntry = await addEntry(content, date, promptType, prompt, title);
        if (newEntry) {
          setSelectedEntry(newEntry);
        }
    }
    setIsEditing(false);
  };

  const SidebarContent = () => (
    <JournalSidebar
      entries={entries}
      selectedEntry={selectedEntry}
      onSelectEntry={handleSelectEntry}
      onDeleteEntry={handleDeleteEntry}
      onCreateNew={handleNewEntryClick}
      view={sidebarView}
      onViewChange={setSidebarView}
    />
  );

  return (
    <div className="flex min-h-screen bg-background font-body text-foreground">
      {/* Desktop Sidebar */}
      <aside className={cn(
        "hidden md:block border-r border-border/60 transition-all duration-300 ease-in-out",
        sidebarOpen ? "w-80 lg:w-96" : "w-0"
        )}
        style={{transition: 'width 300ms cubic-bezier(0.2, 0, 0, 1) 0s'}}
      >
        {sidebarOpen && <SidebarContent />}
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col items-center p-4 sm:p-8 overflow-y-auto">
        <header className="w-full max-w-4xl mb-8 flex items-center justify-between">
            <div className="flex items-center gap-3">
                 <div className="md:hidden">
                    <Sheet open={mobileSheetOpen} onOpenChange={setMobileSheetOpen}>
                      <SheetTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <Menu className="h-6 w-6" />
                        </Button>
                      </SheetTrigger>
                      <SheetContent side="left" className="w-80 p-0">
                        <SidebarContent />
                      </SheetContent>
                    </Sheet>
                  </div>
                  <div className="hidden md:block">
                     <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(!sidebarOpen)}>
                        <Menu className="h-6 w-6" />
                     </Button>
                  </div>
            </div>

            <Button variant="default" onClick={handleNewEntryClick}>
                <PlusCircle className="w-4 h-4 mr-2" />
                New Entry
            </Button>
            
            <div onClick={() => {
              setIsEditing(false);
              if (entries.length > 0) {
                setSelectedEntry(entries[0]);
              }
            }}>
                <SagaLogo />
            </div>
        </header>

        <main className="w-full max-w-3xl space-y-12">
          {!isLoaded && <p>Loading your saga...</p>}
          
          {isLoaded && isEditing && (
            <JournalEditor
              onSaveEntry={handleSave}
              recentEntries={entries.slice(0, 3)}
              entryToEdit={selectedEntry}
              onCancel={() => {
                setIsEditing(false);
                if (!selectedEntry && entries.length > 0) {
                  setSelectedEntry(entries[0]);
                }
              }}
            />
          )}

          {isLoaded && !isEditing && selectedEntry && (
             <JournalEntryDisplay entry={selectedEntry} onEdit={handleEditClick} />
          )}

           {isLoaded && !isEditing && !selectedEntry && (
              <div className="text-center py-20">
                <h2 className="text-2xl font-headline">Your saga awaits.</h2>
                <p className="text-muted-foreground mt-2">Create your first entry to begin.</p>
                <Button onClick={handleNewEntryClick} className="mt-8">
                  <PlusCircle className="w-4 h-4 mr-2" />
                  Create First Entry
                </Button>
              </div>
           )}
        </main>
      </div>
    </div>
  );
}

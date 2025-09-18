
"use client";

import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { JournalEntry } from "@/lib/types";
import { cn } from "@/lib/utils";
import { format } from "date-fns";
import { Trash2 } from "lucide-react";
import { Button } from "../ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Badge } from "../ui/badge";

type JournalEntryCardProps = {
  entry: JournalEntry;
  onSelect: () => void;
  onDelete: () => void;
  isSelected: boolean;
};

const promptTypeLabels: { [key in NonNullable<JournalEntry['promptType']>] : string } = {
    reflective: 'Reflective',
    creative: 'Creative',
    daily: 'Daily',
    freeform: 'Freeform'
};

export function JournalEntryCard({ entry, onSelect, onDelete, isSelected }: JournalEntryCardProps) {
  const formattedDate = format(new Date(entry.date), "h:mm a");

  return (
    <article className="animate-in fade-in-0 duration-500 group">
      <Card 
        className={cn(
            "bg-card shadow-sm border-border/60 transition-colors hover:bg-muted/50 relative",
            isSelected && "bg-muted"
        )}
      >
        <div onClick={onSelect} className="cursor-pointer">
            <CardHeader className="py-3 px-4">
                <div className="flex justify-between items-start">
                  <CardTitle className="text-base tracking-tight text-foreground/90 leading-snug pr-8">
                    {entry.title}
                  </CardTitle>
                  <div className="flex items-center gap-2 pt-0.5">
                    <Badge variant="outline" className="text-[10px] capitalize">
                        {entry.promptType ? promptTypeLabels[entry.promptType] : 'Freeform'}
                    </Badge>
                    <CardDescription className="text-xs text-muted-foreground whitespace-nowrap">
                        {formattedDate}
                    </CardDescription>
                  </div>
                </div>
                <p className="pt-2 text-xs text-muted-foreground font-normal line-clamp-2">{entry.summary}</p>
            </CardHeader>
        </div>
        <AlertDialog>
            <AlertDialogTrigger asChild>
                <Button 
                    variant="ghost" 
                    size="icon" 
                    className="absolute top-1/2 right-1 -translate-y-1/2 h-8 w-8 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity"
                    aria-label="Delete entry"
                >
                    <Trash2 className="h-4 w-4" />
                </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
                <AlertDialogHeader>
                    <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                    <AlertDialogDescription>
                        This action cannot be undone. This will permanently delete your
                        journal entry.
                    </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction onClick={onDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                        Delete
                    </AlertDialogAction>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
      </Card>
    </article>
  );
}

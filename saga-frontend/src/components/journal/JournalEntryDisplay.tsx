
"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { JournalEntry } from "@/lib/types";
import { format } from "date-fns";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { Separator } from "../ui/separator";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Book, BookDashed, Pencil } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "../ui/tooltip";

type JournalEntryDisplayProps = {
  entry: JournalEntry;
  onEdit: () => void;
};

const promptTypeLabels: { [key in NonNullable<JournalEntry['promptType']>] : string } = {
    reflective: 'Reflective',
    creative: 'Creative',
    daily: 'Daily',
    freeform: 'Freeform'
};


export function JournalEntryDisplay({ entry, onEdit }: JournalEntryDisplayProps) {
  const formattedDate = entry.date ? format(new Date(entry.date), "MMMM d, yyyy 'at' h:mm a") : 'No date';

  const promptTypeLabel = entry.promptType ? promptTypeLabels[entry.promptType] : '';

  return (
    <article className="animate-in fade-in-0 duration-500">
        <Separator className="my-8"/>
        <Card className="bg-card shadow-lg border-border/60">
            <CardHeader>
                <div className="flex justify-between items-start">
                    <div className="flex-1">
                        <CardTitle className="text-2xl tracking-tight text-foreground/90">
                           {entry.title}
                        </CardTitle>
                        <CardDescription className="pt-1.5 text-sm text-muted-foreground">
                           {formattedDate}
                        </CardDescription>
                    </div>
                    <Button variant="ghost" size="icon" onClick={onEdit}>
                        <Pencil className="w-5 h-5" />
                        <span className="sr-only">Edit Entry</span>
                    </Button>
                </div>
                 <p className="pt-4 text-base text-muted-foreground font-normal">{entry.summary}</p>
            </CardHeader>
            <CardContent>
                <div className="space-y-2 mb-8">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs font-medium uppercase tracking-wider">
                          {entry.promptType ? promptTypeLabels[entry.promptType] : 'Freeform'}
                      </Badge>
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger>
                            {entry.use_for_prompt_generation ? (
                              <Book className="h-4 w-4 text-muted-foreground" />
                            ) : (
                              <BookDashed className="h-4 w-4 text-muted-foreground" />
                            )}
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>
                              {entry.use_for_prompt_generation
                                ? "This entry is being used for prompt generation"
                                : "This entry is not being used for prompt generation"}
                            </p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>
                    {entry.prompt && (
                        <CardDescription className="pt-2 italic border-l-2 pl-3 border-accent text-foreground/70">
                            {entry.prompt}
                        </CardDescription>
                    )}
                </div>
                <div className="prose prose-sm max-w-none text-foreground/90 text-base leading-relaxed">
                    <MarkdownRenderer content={entry.content} />
                </div>
            </CardContent>
        </Card>
    </article>
  );
}

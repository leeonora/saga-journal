
"use client";

import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Wand2, BookPlus, Loader2, X, CalendarIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormMessage,
} from "@/components/ui/form";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import type { JournalEntry, PromptType } from "@/lib/types";
import { format } from "date-fns";
import { Input } from "../ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { Popover, PopoverContent, PopoverTrigger } from "../ui/popover";
import { Calendar } from "../ui/calendar";
import { cn } from "@/lib/utils";

// The base URL for your FastAPI backend
const API_URL = "http://127.0.0.1:8000";

const formSchema = z.object({
  title: z.string().optional(),
  content: z.string().min(1, "Your entry cannot be empty."),
});

type JournalEditorProps = {
  onSaveEntry: (content: string, date: Date, promptType: PromptType, prompt: string | undefined, title: string | undefined) => Promise<void>;
  recentEntries: JournalEntry[];
  entryToEdit?: JournalEntry | null;
  onCancel?: () => void;
};

export function JournalEditor({ onSaveEntry, recentEntries, entryToEdit, onCancel }: JournalEditorProps) {
  const [isLoadingPrompt, setIsLoadingPrompt] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [generatedPrompt, setGeneratedPrompt] = useState<string | null>(null);
  const [promptType, setPromptType] = useState<PromptType>('daily');
  const [entryDate, setEntryDate] = useState<Date>(new Date());
  const [customPrompt, setCustomPrompt] = useState("");
  const { toast } = useToast();

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: { title: "", content: "" },
  });

  useEffect(() => {
    if (entryToEdit) {
      form.reset({
        title: entryToEdit.title,
        content: entryToEdit.content,
      });
      setEntryDate(new Date(entryToEdit.date));
      setPromptType(entryToEdit.promptType || 'daily');
      setGeneratedPrompt(entryToEdit.prompt || null);
    } else {
       form.reset({ title: "New Entry", content: "" });
       setEntryDate(new Date());
       setGeneratedPrompt(null);
    }
  }, [entryToEdit, form]);

  const handleGeneratePrompt = async () => {
    setIsLoadingPrompt(true);
    setGeneratedPrompt(null);
    try {
      const response = await fetch(`${API_URL}/generate-prompt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          promptType,
          recentEntries: recentEntries.map(e => e.content).join("\n\n---\n\n"),
          customPrompt,
        }),
      });
      if (!response.ok) throw new Error("Prompt generation failed");
      const result = await response.json();

      if (result.error) {
        toast({
          variant: "destructive",
          title: "Prompt Generation Failed",
          description: result.error,
        });
      } else if (result.prompt) {
        setGeneratedPrompt(result.prompt);
        toast({
          title: "A prompt has appeared!",
          description: "A new writing prompt has been generated for you.",
        });
      }
    } catch (error: any) {
      toast({
          variant: "destructive",
          title: "Prompt Generation Failed",
          description: error.message,
      });
    }
    setIsLoadingPrompt(false);
  };
  
  const handleClearPrompt = () => {
    setGeneratedPrompt(null);
  };

  async function onSubmit(data: z.infer<typeof formSchema>) {
    setIsSaving(true);
    const currentPromptType = generatedPrompt ? promptType : 'freeform';
    await onSaveEntry(data.content, entryDate, currentPromptType, generatedPrompt ?? undefined, data.title);
    
    if (!entryToEdit) {
      form.reset();
      setGeneratedPrompt(null);
      setEntryDate(new Date());
    }

    toast({
        title: "Entry Saved",
        description: "Your thoughts have been recorded in your saga.",
    });
    setIsSaving(false);
  }

  return (
    <div className="w-full bg-card p-8 rounded-lg shadow-md">
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          {/* Header Section */}
          <div className="flex flex-col">
            <FormField
              control={form.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormControl>
                    <Input placeholder="Title (optional)" {...field} className="font-bold border-none focus:ring-0 shadow-none bg-transparent" style={{ fontSize: '1.2rem', padding: 0 }} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Popover>
                <PopoverTrigger asChild>
                <Button
                    variant={"ghost"}
                    className={cn(
                    "w-full justify-start text-left font-normal text-muted-foreground p-0 h-auto",
                    !entryDate && "text-muted-foreground"
                    )}
                >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {entryDate ? format(entryDate, "PPP") : <span>Pick a date</span>}
                </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0">
                <Calendar
                    mode="single"
                    selected={entryDate}
                    onSelect={(date) => setEntryDate(date || new Date())}
                    initialFocus
                />
                </PopoverContent>
            </Popover>
          </div>


          {/* Top Controls Row */}
          <div className="flex flex-col sm:flex-row items-center gap-3">
            <Input placeholder="Themes (optional)" className="bg-muted rounded-md p-4" value={customPrompt} onChange={(e) => setCustomPrompt(e.target.value)} />
            <Select value={promptType} onValueChange={(value: PromptType) => setPromptType(value)}>
              <SelectTrigger className="w-full sm:w-auto bg-primary text-primary-foreground rounded-md">
                  <SelectValue placeholder="Select a prompt type" />
              </SelectTrigger>
              <SelectContent>
                  <SelectItem value="reflective">Reflective</SelectItem>
                  <SelectItem value="daily">Daily</SelectItem>
                  <SelectItem value="creative">Creative</SelectItem>
              </SelectContent>
            </Select>
            <Button type="button" variant="secondary" className="w-full sm:w-auto bg-muted text-foreground rounded-md" disabled={isLoadingPrompt} onClick={handleGeneratePrompt}>
                {isLoadingPrompt ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />}
                <span className="ml-2">Generate Prompt</span>
            </Button>
          </div>

          {/* Prompt Box */}
          {generatedPrompt && (
            <div className="relative p-4 italic border-l-4 rounded-r-md bg-muted border-primary text-foreground/80 animate-fade-in" style={{ fontSize: '0.875rem' }}>
                {generatedPrompt}
                  <Button type="button" variant="ghost" size="icon" className="absolute top-1/2 right-2 -translate-y-1/2 h-7 w-7 text-muted-foreground hover:text-destructive" onClick={handleClearPrompt} aria-label="Clear prompt">
                    <X className="h-4 w-4" />
                </Button>
            </div>
          )}

          {/* Main Text Area */}
          <FormField
            control={form.control}
            name="content"
            render={({ field }) => (
              <FormItem>
                <FormControl>
                  <Textarea
                    placeholder="What's on your mind today?"
                    className="min-h-[300px] resize-y text-base bg-muted rounded-lg border-none p-4 focus:ring-0"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          {/* Footer/Save Button */}
          <footer className="flex justify-end space-x-2">
            {onCancel && <Button type="button" variant="ghost" onClick={onCancel}>Cancel</Button>}
            <Button type="submit" className="w-full sm:w-auto" variant="default" disabled={isSaving}>
                {isSaving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <BookPlus className="w-4 h-4 mr-2" />}
                Save Entry
            </Button>
          </footer>
        </form>
      </Form>
    </div>
  );
}

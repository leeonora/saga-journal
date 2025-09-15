
"use client";

import { useState, useRef, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Bold, Italic, Underline, Wand2, BookPlus, Loader2, Highlighter, CalendarIcon, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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
import { Separator } from "../ui/separator";
import { Popover, PopoverContent, PopoverTrigger } from "../ui/popover";
import { Switch } from "../ui/switch";
import { Label } from "../ui/label";
import { cn } from "@/lib/utils";
import { Calendar } from "../ui/calendar";
import { format } from "date-fns";
import { Input } from "../ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";

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

const highlightColors = [
    { name: 'green', color: 'hsl(var(--highlight-green))' },
    { name: 'pink', color: 'hsl(var(--highlight-pink))' },
    { name: 'blue', color: 'hsl(var(--highlight-blue))' },
    { name: 'yellow', color: 'hsl(var(--highlight-yellow))' },
    { name: 'purple', color: 'hsl(var(--highlight-purple))' },
];


export function JournalEditor({ onSaveEntry, recentEntries, entryToEdit, onCancel }: JournalEditorProps) {
  const [isLoadingPrompt, setIsLoadingPrompt] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [generatedPrompt, setGeneratedPrompt] = useState<string | null>(null);
  const [promptType, setPromptType] = useState<PromptType>('journal');
  const [showLines, setShowLines] = useState(false);
  const [entryDate, setEntryDate] = useState<Date>(new Date());
  const textareaRef = useRef<HTMLTextAreaElement>(null);
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
      setPromptType(entryToEdit.promptType || 'journal');
      setGeneratedPrompt(entryToEdit.prompt || null);
    } else {
       form.reset({ title: "", content: "" });
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
        }),
      });
      if (!response.ok) throw new Error("Prompt generation failed");
      const result = await response.json(); // e.g. { "prompt": "..." }

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

  const applyFormat = (format: 'bold' | 'italic' | 'underline' | `highlight-${string}`) => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = textarea.value.substring(start, end);
    
    let newText;
    let markers;

    if (format.startsWith('highlight-')) {
        const color = format.split('-')[1];
        markers = [`<mark class="highlight-${color}">`, `</mark>`];
        newText = `${markers[0]}${selectedText}${markers[1]}`;
    } else {
        markers = {
            bold: '**',
            italic: '_',
            underline: '__'
        }[format];
        newText = `${markers}${selectedText}${markers}`;
    }

    const newContent = `${textarea.value.substring(0, start)}${newText}${textarea.value.substring(end)}`;
    
    form.setValue('content', newContent, { shouldValidate: true });

    setTimeout(() => {
        textarea.focus();
        if (selectedText) {
            textarea.setSelectionRange(start, start + newText.length);
        } else {
             if (Array.isArray(markers)) {
                textarea.setSelectionRange(start + markers[0].length, start + markers[0].length);
            } else {
                textarea.setSelectionRange(start + markers.length, start + markers.length);
            }
        }
    }, 0);
  };

  async function onSubmit(data: z.infer<typeof formSchema>) {
    setIsSaving(true);
    const currentPromptType = generatedPrompt ? promptType : 'freeform';
    await onSaveEntry(data.content, entryDate, currentPromptType, generatedPrompt ?? undefined, data.title);
    
    // Don't reset form if editing
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
    <Card className="bg-card shadow-lg border-border/60">
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-xl">
              {entryToEdit ? 'Edit Entry' : 'New Entry'}
            </CardTitle>
            <div className="flex items-center gap-4">
                 <Select value={promptType} onValueChange={(value: PromptType) => setPromptType(value)}>
                    <SelectTrigger className="w-[180px]">
                        <SelectValue placeholder="Select a prompt type" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="journal">Journaling</SelectItem>
                        <SelectItem value="creative">Creative Writing</SelectItem>
                    </SelectContent>
                 </Select>
                <Button type="button" variant="outline" className="border-accent text-accent-foreground hover:bg-accent/80 hover:text-accent-foreground" disabled={isLoadingPrompt} onClick={handleGeneratePrompt}>
                    {isLoadingPrompt ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />}
                    <span className="ml-2">Get Prompt</span>
                </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
             {generatedPrompt && (
                <div className="relative p-3 mt-2 text-sm italic border-l-4 rounded-r-md bg-muted/50 border-accent text-foreground/80 animate-fade-in">
                    {generatedPrompt}
                     <Button type="button" variant="ghost" size="icon" className="absolute top-1/2 right-1 -translate-y-1/2 h-7 w-7 text-muted-foreground hover:text-destructive" onClick={handleClearPrompt} aria-label="Clear prompt">
                        <X className="h-4 w-4" />
                    </Button>
                </div>
            )}
            <div className="flex flex-col sm:flex-row gap-4">
                <FormField
                  control={form.control}
                  name="title"
                  render={({ field }) => (
                    <FormItem className="flex-1">
                      <FormControl>
                        <Input placeholder="Title (optional)" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                 <Popover>
                    <PopoverTrigger asChild>
                    <Button
                        variant={"outline"}
                        className={cn(
                        "w-full sm:w-[200px] justify-start text-left font-normal",
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

            <div className="flex items-center justify-between p-1 rounded-md bg-muted">
              <div className="flex items-center gap-1">
                <Button type="button" variant="ghost" size="icon" onClick={() => applyFormat('bold')} aria-label="Bold"><Bold className="w-4 h-4" /></Button>
                <Button type="button" variant="ghost" size="icon" onClick={() => applyFormat('italic')} aria-label="Italic"><Italic className="w-4 h-4" /></Button>
                <Button type="button" variant="ghost" size="icon" onClick={() => applyFormat('underline')} aria-label="Underline"><Underline className="w-4 h-4" /></Button>
                <Popover>
                    <PopoverTrigger asChild>
                      <Button type="button" variant="ghost" size="icon" aria-label="Highlight"><Highlighter className="w-4 h-4" /></Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-1">
                        <div className="flex gap-1">
                          {highlightColors.map(h => (
                               <Button
                                  key={h.name}
                                  type="button"
                                  className="w-8 h-8 p-0 rounded-full"
                                  style={{backgroundColor: h.color}}
                                  onClick={() => applyFormat(`highlight-${h.name}`)}
                               />
                          ))}
                        </div>
                    </PopoverContent>
                </Popover>
              </div>
               <div className="flex items-center gap-2 pr-2">
                  <Label htmlFor="show-lines" className="text-sm text-muted-foreground">Lined</Label>
                  <Switch id="show-lines" checked={showLines} onCheckedChange={setShowLines} />
              </div>
            </div>
            <FormField
              control={form.control}
              name="content"
              render={({ field }) => (
                <FormItem>
                  <FormControl>
                    <Textarea
                      ref={textareaRef}
                      placeholder="What's on your mind today?"
                      className={cn("min-h-[240px] resize-y text-base", {"lined-paper": showLines})}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </CardContent>
          <Separator className="my-0"/>
          <CardFooter className="justify-end pt-6 space-x-2">
            {onCancel && <Button type="button" variant="ghost" onClick={onCancel}>Cancel</Button>}
            <Button type="submit" className="w-full sm:w-auto" variant="default" disabled={isSaving}>
                {isSaving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <BookPlus className="w-4 h-4 mr-2"/>}
                Save Entry
            </Button>
          </CardFooter>
        </form>
      </Form>
    </Card>
  );
}

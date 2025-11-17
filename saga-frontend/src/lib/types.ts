
export type JournalEntry = {
  // Assuming the backend will provide a unique ID, which could be a number or string
  id: string | number; 
  date: string;
  content: string;
  title: string;
  summary: string;
  prompt?: string;
  promptType?: PromptType;
  use_for_prompt_generation?: boolean;
};

export type PromptType = 'reflective' | 'creative' | 'daily' | 'freeform';

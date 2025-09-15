import React from 'react';
import { cn } from '@/lib/utils';

type MarkdownRendererProps = {
  content: string;
  className?: string;
};

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  const toHtml = (text: string) => {
    // This is a very basic renderer. For a real app, use a library like 'marked' or 'react-markdown'.
    // The order of replacement matters here.
    
    // Protect existing <mark> tags by replacing them with placeholders
    const placeholders: string[] = [];
    let processedText = text.replace(/<mark class="highlight-.*?">.*?<\/mark>/g, (match) => {
      placeholders.push(match);
      return `__MARK_PLACEHOLDER_${placeholders.length - 1}__`;
    });

    // Apply other formatting
    processedText = processedText
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/__(.*?)__/g, '<u>$1</u>')
      .replace(/_(.*?)_/g, '<em>$1</em>')
      .replace(/\n/g, '<br />');
      
    // Restore the <mark> tags
    placeholders.forEach((placeholder, index) => {
        processedText = processedText.replace(`__MARK_PLACEHOLDER_${index}__`, placeholder);
    });

    return processedText;
  };

  return <div className={cn("whitespace-pre-wrap", className)} dangerouslySetInnerHTML={{ __html: toHtml(content) }} />;
}

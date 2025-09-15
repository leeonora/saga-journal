import { cn } from "@/lib/utils";
import React from "react";

export function SagaLogo({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("font-logo text-4xl text-primary", className)} style={{ fontFamily: "'IM Fell Great Primer', serif" }} {...props}>
      Saga
    </div>
  );
}

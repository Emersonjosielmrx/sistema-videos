import * as React from "react";
import { HelpCircle } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

interface FieldProps {
  label: string;
  hint?: string;
  children: React.ReactNode;
  className?: string;
}

/** Label com tooltip de ajuda — hover mostra um balão com o hint. */
export function Field({ label, hint, children, className }: FieldProps) {
  return (
    <div className={cn("space-y-1.5", className)}>
      <label className="flex items-center gap-1.5 text-sm font-medium">
        <span>{label}</span>
        {hint && (
          <TooltipProvider delayDuration={150}>
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  className="inline-flex items-center justify-center rounded-full p-0.5 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                >
                  <HelpCircle className="h-4 w-4" />
                  <span className="sr-only">?</span>
                </button>
              </TooltipTrigger>
              <TooltipContent side="right" className="max-w-xs text-left">
                <p>{hint}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </label>
      {children}
    </div>
  );
}

interface ToggleFieldProps {
  label: string;
  hint?: string;
  description?: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  className?: string;
}

/** Toggle com label + hint + descrição opcional. */
export function ToggleField({ label, hint, description, checked, onChange, className }: ToggleFieldProps) {
  return (
    <div className={cn("flex items-center justify-between", className)}>
      <div className="flex items-start gap-1.5 mr-3 flex-1">
        <label className="text-sm font-medium leading-tight cursor-default flex-1">{label}</label>
        {hint && (
          <TooltipProvider delayDuration={150}>
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  className="inline-flex items-center justify-center rounded-full p-0.5 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors shrink-0"
                >
                  <HelpCircle className="h-4 w-4" />
                  <span className="sr-only">?</span>
                </button>
              </TooltipTrigger>
              <TooltipContent side="left" className="max-w-xs text-left">
                <p>{hint}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        title={hint}
        onClick={() => onChange(!checked)}
        className={cn(
          "relative inline-flex h-6 w-11 shrink-0 items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 cursor-pointer",
          checked ? "bg-primary" : "bg-muted"
        )}
      >
        <span
          className={cn(
            "pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow-lg ring-0 transition-transform",
            checked ? "translate-x-5" : "translate-x-0"
          )}
        />
      </button>
      {description && <p className="sr-only">{description}</p>}
    </div>
  );
}

import React, { ReactNode } from "react";
import { TabsTrigger } from "@/components/ui/tabs";
import { useNavigation, toggleHiddenSubTab } from "@/stores/navigation";
import { X, Plus } from "lucide-react";
import { cn } from "@/lib/utils";

interface HideableTabProps extends React.ComponentPropsWithoutRef<typeof TabsTrigger> {
  value: string;
  className?: string;
  children: ReactNode;
}

export const HideableTab = React.forwardRef<React.ElementRef<typeof TabsTrigger>, HideableTabProps>(
  ({ value, className, children, ...props }, ref) => {
    const isEditMode = useNavigation((s) => s.isEditMode || s.isEmployeeEditMode);
    const hiddenTabs = useNavigation((s) => s.isEmployeeEditMode ? s.hiddenSubTabsEmployee : s.hiddenSubTabs);
    const isHidden = hiddenTabs.includes(value);

    if (isHidden && !isEditMode) return null;

    const trigger = (
      <TabsTrigger 
        ref={ref}
        value={value} 
        className={cn(
          "relative shrink-0",
          isHidden ? "opacity-50 grayscale text-muted-foreground" : "",
          className
        )}
        {...props}
      >
        <div className={cn("flex items-center", isEditMode && "origin-center pointer-events-none")}>
          {children}
        </div>
        {isEditMode && (
          <div
            onClick={(e) => { 
              e.stopPropagation(); 
              e.preventDefault();
              toggleHiddenSubTab(value); 
            }}
            className="absolute -top-1.5 -left-1.5 z-10 flex h-4 w-4 items-center justify-center rounded-full bg-destructive text-destructive-foreground shadow-md hover:scale-110 transition-transform cursor-pointer"
          >
            {isHidden ? <Plus className="h-2.5 w-2.5" /> : <X className="h-2.5 w-2.5" />}
          </div>
        )}
      </TabsTrigger>
    );

    return isEditMode ? (
      <div className="animate-jiggle inline-block relative">
        {trigger}
      </div>
    ) : trigger;
  }
);
HideableTab.displayName = "HideableTab";

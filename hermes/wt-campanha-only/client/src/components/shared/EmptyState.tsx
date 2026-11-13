import * as React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RefreshCcw } from "lucide-react";

type Props = {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  onRetry?: () => void;
  retryLabel?: string;
};

// FIX P1-003 (2026-07-25): EmptyState não oferecia caminho de recuperação.
// Se o usuário cai aqui por falha de fetch, ele ficava olhando pra tela
// sem ação. Agora aceita onRetry e mostra botão. Mantém compat: sem onRetry
// não renderiza nada (caso comum "selecione uma conta").
export const EmptyState = ({ icon, title, description, onRetry, retryLabel = "Tentar de novo" }: Props) => (
  <Card className="border-dashed bg-transparent shadow-none">
    <CardContent className="flex flex-col items-center justify-center gap-2 py-10 text-center">
      {icon && (
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-accent text-accent-foreground">
          {icon}
        </div>
      )}
      <p className="font-medium">{title}</p>
      {description && <p className="max-w-xs text-sm text-muted-foreground">{description}</p>}
      {onRetry && (
        <Button onClick={onRetry} variant="outline" size="sm" className="mt-2 gap-2">
          <RefreshCcw className="h-3.5 w-3.5" />
          {retryLabel}
        </Button>
      )}
    </CardContent>
  </Card>
);

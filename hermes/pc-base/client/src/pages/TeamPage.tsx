import { Card } from "@/components/ui/card";
import { Users, Construction } from "lucide-react";

// TeamPage — gestão de equipe/multi-operador ainda não tem backend (roster, ranking,
// performance por operador). Em vez de exibir números fabricados, mostramos um estado
// honesto de "em desenvolvimento" até existir a API de equipe.
export function TeamPage() {
  return (
    <div className="max-w-[1600px] mx-auto p-4 sm:p-6">
      <div className="flex items-center gap-3 mb-6">
        <Users className="w-6 h-6 text-primary" />
        <h2 className="text-xl font-semibold">Equipe</h2>
      </div>

      <Card className="p-10 flex flex-col items-center justify-center text-center gap-4 border-dashed">
        <div className="w-14 h-14 rounded-2xl bg-muted flex items-center justify-center">
          <Construction className="w-7 h-7 text-muted-foreground" />
        </div>
        <div className="space-y-1 max-w-md">
          <p className="font-bold">Gestão de equipe em desenvolvimento</p>
          <p className="text-sm text-muted-foreground">
            O módulo de multi-operador (convidar membros, papéis, ranking e performance por
            atendente) ainda não está disponível. Assim que o backend de equipe existir, esta
            tela mostrará dados reais do seu time — não números de demonstração.
          </p>
        </div>
      </Card>
    </div>
  );
}

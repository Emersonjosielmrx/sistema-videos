import { useEffect, useState } from "react";
import { FolderKanban, Plus, Trash2, Building2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { apiGet, apiPost, apiDelete } from "@/lib/api";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface Project {
  id: string;
  name: string;
  description: string;
  tags: string[];
  priority: string;
  created_at: string;
}

export function WorkspaceSettings() {
  const [workspaces, setWorkspaces] = useState<Project[]>([]);
  const [newWorkspace, setNewWorkspace] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [newPass, setNewPass] = useState("");
  const [loading, setLoading] = useState(false);

  const load = async () => {
    try {
      const r = await apiGet<{ projects: Project[] | null }>("/api/projects");
      setWorkspaces(r.projects ?? []);
    } catch {
      toast.error("Falha ao carregar workspaces.");
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async () => {
    if (!newWorkspace.trim()) return toast.error("Preencha o nome do workspace.");

    setLoading(true);
    try {
      // O backend (projects_api.go) só decodifica name/description/tags/priority.
      // NÃO há criação de login de gestor — por isso não enviamos managerEmail/
      // managerPassword (seriam ignorados) e o toast não promete o usuário gestor.
      await apiPost("/api/projects", {
        name: newWorkspace.trim(),
        priority: "normal",
      });
      setNewWorkspace("");
      toast.success("Workspace criado.");
      await load();
    } catch {
      toast.error("Falha ao criar workspace.");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await apiDelete(`/api/projects/${id}`);
      toast.success("Workspace removido.");
      await load();
    } catch {
      toast.error("Falha ao remover workspace.");
    }
  };

  const fmtDate = (iso: string) => {
    const d = new Date(iso);
    return isNaN(d.getTime()) ? "—" : d.toLocaleDateString("pt-BR");
  };

  return (
    <Card className="border-border/50 shadow-soft bg-glass overflow-hidden">
      <div className="border-b border-border/50 bg-muted/20 px-6 py-4 flex items-center justify-between">
        <div>
          <h4 className="font-bold flex items-center gap-2 text-primary">
            <FolderKanban className="h-5 w-5" />
            Projetos / Workspaces
            <Badge variant="outline" className="ml-2 text-[10px] uppercase font-bold text-emerald-500 border-emerald-500/30">/api/projects</Badge>
          </h4>
          <p className="text-xs text-muted-foreground mt-1">
            Gerencie espaços de trabalho separados. Logins de gestor por workspace chegam em breve.
          </p>
        </div>
      </div>
      
      <div className="p-6 space-y-6">
        
        <div className="flex flex-col gap-4 p-6 border border-border/50 bg-background/50 rounded-xl">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-foreground/80">Nome do Novo Workspace</label>
              <div className="flex gap-2">
                <Building2 className="w-5 h-5 mt-2 text-muted-foreground shrink-0" />
                <Input 
                  placeholder="Ex: Equipe de Suporte" 
                  className="rounded-xl bg-background"
                  value={newWorkspace}
                  onChange={(e) => setNewWorkspace(e.target.value)}
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-semibold text-foreground/80 flex items-center gap-2">
                E-mail de Acesso (Login)
                <Badge variant="outline" className="text-[10px] uppercase font-bold text-amber-500 border-amber-500/40">Em breve</Badge>
              </label>
              <Input
                type="email"
                placeholder="email@empresa.com"
                className="rounded-xl bg-background"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                disabled
                title="Criação de login de gestor ainda não disponível."
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-foreground/80 flex items-center gap-2">
                Senha Provisória
                <Badge variant="outline" className="text-[10px] uppercase font-bold text-amber-500 border-amber-500/40">Em breve</Badge>
              </label>
              <Input
                type="text"
                placeholder="Senha inicial"
                className="rounded-xl bg-background"
                value={newPass}
                onChange={(e) => setNewPass(e.target.value)}
                disabled
                title="Criação de login de gestor ainda não disponível."
              />
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-border/50">
            <Button onClick={handleCreate} disabled={loading} className="rounded-xl shadow-glow bg-emerald-500 hover:bg-emerald-600 text-white w-full md:w-auto">
              <Plus className="w-4 h-4 mr-2" /> Criar Workspace
            </Button>
          </div>
        </div>

        <div className="border border-border/50 rounded-xl overflow-hidden bg-background/50">
          <Table>
            <TableHeader className="bg-muted/50">
              <TableRow>
                <TableHead>Workspace</TableHead>
                <TableHead>Tags</TableHead>
                <TableHead>Data de Criação</TableHead>
                <TableHead className="text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {workspaces.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted-foreground text-sm py-8">
                    Nenhum workspace ainda. Crie o primeiro acima.
                  </TableCell>
                </TableRow>
              ) : (
                workspaces.map((ws) => (
                  <TableRow key={ws.id}>
                    <TableCell className="font-medium">{ws.name}</TableCell>
                    <TableCell>
                      {ws.tags && ws.tags.length > 0
                        ? ws.tags.map((t) => <Badge key={t} variant="secondary" className="mr-1">{t}</Badge>)
                        : <span className="text-muted-foreground text-sm">—</span>}
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">{fmtDate(ws.created_at)}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(ws.id)}
                        className="h-8 hover:bg-destructive/20 hover:text-destructive transition-colors"
                      >
                        <Trash2 className="w-4 h-4 mr-2" /> Remover
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>
    </Card>
  );
}

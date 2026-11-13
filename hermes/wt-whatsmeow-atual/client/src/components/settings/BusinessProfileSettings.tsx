import { useEffect, useState } from "react";
import { Building, Save, Mail, MapPin, Briefcase } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Textarea } from "@/components/ui/textarea";
import { apiGet, apiPut } from "@/lib/api";

interface BusinessProfile {
  store_name: string;
  whatsapp: string;
  email: string;
  segment: string;
  address: string;
  extra: string; // JSON livre (guardamos o CNPJ aqui)
}

export function BusinessProfileSettings() {
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState({
    companyName: "",
    email: "",
    cnpj: "",
    address: "",
    description: "",
  });

  useEffect(() => {
    apiGet<BusinessProfile>("/api/profile")
      .then((p) => {
        let cnpj = "";
        try {
          cnpj = p.extra ? (JSON.parse(p.extra).cnpj ?? "") : "";
        } catch {
          /* extra inválido: ignora */
        }
        setProfile({
          companyName: p.store_name || "",
          email: p.email || "",
          cnpj,
          address: p.address || "",
          description: p.segment || "",
        });
      })
      .catch(() => {
        /* sem perfil ainda: mantém vazio */
      });
  }, []);

  const handleSave = async () => {
    setLoading(true);
    try {
      await apiPut("/api/profile", {
        store_name: profile.companyName,
        email: profile.email,
        address: profile.address,
        segment: profile.description,
        extra: JSON.stringify({ cnpj: profile.cnpj }),
      });
      toast.success("Perfil da Empresa atualizado com sucesso!");
    } catch {
      toast.error("Falha ao salvar o perfil da empresa.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="border-border/50 shadow-soft bg-glass">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-xl">
          <Building className="h-6 w-6 text-primary" />
          Perfil do Negócio
          <Badge variant="outline" className="ml-2 text-xs text-emerald-400 border-emerald-400/30">/api/profile</Badge>
        </CardTitle>
        <CardDescription>
          Gerencie as informações oficiais da sua empresa. Estes dados podem ser utilizados pela IA em atendimentos.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div className="space-y-2">
            <Label htmlFor="companyName">Nome da Empresa</Label>
            <div className="relative">
              <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input 
                id="companyName" 
                className="pl-9"
                value={profile.companyName}
                onChange={(e) => setProfile({...profile, companyName: e.target.value})}
              />
            </div>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="cnpj">CNPJ</Label>
            <Input 
              id="cnpj" 
              value={profile.cnpj}
              onChange={(e) => setProfile({...profile, cnpj: e.target.value})}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="email">E-mail de Contato</Label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input 
                id="email" 
                type="email"
                className="pl-9"
                value={profile.email}
                onChange={(e) => setProfile({...profile, email: e.target.value})}
              />
            </div>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="address">Endereço Principal</Label>
            <div className="relative">
              <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input 
                id="address" 
                className="pl-9"
                value={profile.address}
                onChange={(e) => setProfile({...profile, address: e.target.value})}
              />
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Descrição do Negócio (Contexto para IA)</Label>
          <Textarea 
            id="description" 
            className="min-h-[100px] resize-y"
            placeholder="Descreva o que sua empresa faz, principais produtos e tom de voz desejado."
            value={profile.description}
            onChange={(e) => setProfile({...profile, description: e.target.value})}
          />
          <p className="text-xs text-muted-foreground">Esta descrição ajuda o Cérebro da IA a entender o contexto da sua operação.</p>
        </div>

        <div className="pt-4 border-t border-border/50">
          <Button onClick={handleSave} disabled={loading} className="w-full sm:w-auto bg-primary text-primary-foreground shadow-glow">
            {loading ? "Salvando..." : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Salvar Perfil da Empresa
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

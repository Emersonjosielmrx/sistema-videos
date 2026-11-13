import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bot, ShieldCheck } from 'lucide-react'
import { api, setToken, setRole } from '../api'
import { Brand } from '../components/Brand'
import { Button, Input, Label, ErrorText } from '../components/ui'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const data = await api.post('/auth/login', { email, password })
      setToken(data.token)
      setRole(data.account.role)
      navigate(data.account.role === 'client' ? '/cliente' : '/')
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4 relative overflow-hidden">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-primary/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="relative w-full max-w-md space-y-6 rounded-2xl border border-border/50 bg-glass p-8 shadow-glow">
        <div className="flex flex-col items-center text-center gap-3">
          <div className="inline-flex items-center rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
            <ShieldCheck className="mr-1.5 h-3.5 w-3.5" /> Acesso seguro
          </div>
          <Brand />
          <div>
            <h1 className="text-2xl font-bold tracking-tight mt-2">Entrar</h1>
            <p className="text-sm text-muted-foreground mt-1">Atendimento automático no WhatsApp</p>
          </div>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label className="text-muted-foreground">Login ou email</Label>
            <Input type="text" autoCapitalize="none" autoCorrect="off" autoComplete="username" value={email} onChange={e => setEmail(e.target.value)} required className="h-11 text-base" />
          </div>
          <div className="space-y-1.5">
            <Label className="text-muted-foreground">Senha</Label>
            <Input type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} required className="h-11 text-base" />
          </div>
          <ErrorText>{error}</ErrorText>
          <Button type="submit" size="lg" disabled={loading} className="w-full">
            <Bot /> {loading ? 'Entrando...' : 'Entrar'}
          </Button>
        </form>
      </div>
    </div>
  )
}

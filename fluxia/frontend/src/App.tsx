import { useState } from 'react'
import { Routes, Route, Navigate, useNavigate, NavLink } from 'react-router-dom'
import { LayoutDashboard, Workflow, Users, ListChecks, ShoppingBag, Settings as SettingsIcon, Smartphone, LogOut, Menu, X } from 'lucide-react'
import { isLoggedIn, clearToken, getRole } from './api'
import { cn } from './lib/utils'
import { Brand } from './components/Brand'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Connections from './pages/Connections'
import Flows from './pages/Flows'
import FlowEditor from './pages/FlowEditor'
import Executions from './pages/Executions'
import Orders from './pages/Orders'
import Clients from './pages/Clients'
import Settings from './pages/Settings'
import ClientHome from './pages/ClientHome'

const LINKS = [
  { to: '/', label: 'Visão geral', icon: LayoutDashboard },
  { to: '/flows', label: 'Fluxos', icon: Workflow },
  { to: '/executions', label: 'Execuções', icon: ListChecks },
  { to: '/orders', label: 'Pedidos', icon: ShoppingBag },
  { to: '/clients', label: 'Clientes', icon: Users },
  { to: '/connections', label: 'WhatsApp', icon: Smartphone },
  { to: '/settings', label: 'Configurações', icon: SettingsIcon },
]

function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const navigate = useNavigate()
  return (
    <div className="flex h-full flex-col gap-1 p-3">
      <div className="px-2 pb-6 pt-2"><Brand /></div>
      <nav className="flex-1 space-y-1 overflow-y-auto">
        {LINKS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            onClick={onNavigate}
            className={({ isActive }) => cn(
              'flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-all hover:translate-x-1',
              isActive ? 'bg-emerald-500/10 text-emerald-500' : 'text-muted-foreground hover:text-foreground hover:bg-muted/50',
            )}
          >
            <Icon className="h-5 w-5 shrink-0" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
      <button
        onClick={() => { clearToken(); navigate('/login') }}
        className="flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-all"
      >
        <LogOut className="h-5 w-5" /> Sair
      </button>
    </div>
  )
}

function AdminShell({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="min-h-screen bg-background">
      <aside className="hidden lg:block fixed inset-y-0 left-0 w-64 border-r border-border/60 bg-card/40 backdrop-blur-xl">
        <Sidebar />
      </aside>
      <header className="lg:hidden sticky top-0 z-30 flex items-center justify-between border-b border-border/60 bg-background/80 backdrop-blur-xl px-4 h-14">
        <Brand small />
        <button onClick={() => setOpen(true)} className="p-2 rounded-xl hover:bg-muted" aria-label="Abrir menu"><Menu className="h-5 w-5" /></button>
      </header>
      {open && (
        <div className="lg:hidden fixed inset-0 z-40">
          <div className="absolute inset-0 bg-black/60" onClick={() => setOpen(false)} />
          <aside className="absolute inset-y-0 left-0 w-72 bg-card border-r border-border">
            <button onClick={() => setOpen(false)} className="absolute right-3 top-3 p-2 rounded-xl hover:bg-muted" aria-label="Fechar menu"><X className="h-5 w-5" /></button>
            <Sidebar onNavigate={() => setOpen(false)} />
          </aside>
        </div>
      )}
      <main className="lg:ml-64 p-4 md:p-8 min-w-0">{children}</main>
    </div>
  )
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  if (!isLoggedIn()) return <Navigate to="/login" replace />
  if (getRole() !== 'admin') return <Navigate to="/cliente" replace />
  return <AdminShell>{children}</AdminShell>
}

function ClientRoute({ children }: { children: React.ReactNode }) {
  if (!isLoggedIn()) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/cliente" element={<ClientRoute><ClientHome /></ClientRoute>} />
      <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/connections" element={<ProtectedRoute><Connections /></ProtectedRoute>} />
      <Route path="/flows" element={<ProtectedRoute><Flows /></ProtectedRoute>} />
      <Route path="/flows/:id" element={<ProtectedRoute><FlowEditor /></ProtectedRoute>} />
      <Route path="/clients" element={<ProtectedRoute><Clients /></ProtectedRoute>} />
      <Route path="/executions" element={<ProtectedRoute><Executions /></ProtectedRoute>} />
      <Route path="/orders" element={<ProtectedRoute><Orders /></ProtectedRoute>} />
      <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

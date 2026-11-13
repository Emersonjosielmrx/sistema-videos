import { Copy } from 'lucide-react'
import { Button, Switch } from './ui'

export const WEEKDAYS: { key: string; label: string }[] = [
  { key: 'seg', label: 'Segunda' }, { key: 'ter', label: 'Terça' }, { key: 'qua', label: 'Quarta' },
  { key: 'qui', label: 'Quinta' }, { key: 'sex', label: 'Sexta' }, { key: 'sab', label: 'Sábado' }, { key: 'dom', label: 'Domingo' },
]

function parse(v: string): [string, string] {
  const m = (v || '').match(/(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})/)
  return m ? [m[1].padStart(5, '0'), m[2].padStart(5, '0')] : ['', '']
}

export default function HoursEditor({ hours, onChange }: { hours: Record<string, string>; onChange: (h: Record<string, string>) => void }) {
  const set = (day: string, value: string) => onChange({ ...hours, [day]: value })
  const copyFirst = () => {
    const first = WEEKDAYS.map(d => hours[d.key]).find(v => v)
    if (first) onChange(Object.fromEntries(WEEKDAYS.map(d => [d.key, first])))
  }
  return (
    <div className="space-y-2">
      {WEEKDAYS.map(d => {
        const value = hours[d.key] || ''
        const [a, b] = parse(value)
        const open = !!value
        const multi = value.includes(',') || value.includes(';')
        return (
          <div key={d.key} className="flex flex-wrap items-center gap-2 rounded-xl border border-border/60 bg-background/40 px-3 py-2">
            <Switch checked={open} onCheckedChange={on => set(d.key, on ? '18:00-23:00' : '')} aria-label={`Abre ${d.label}`} />
            <span className="w-20 text-sm font-medium">{d.label}</span>
            {open && !multi && (
              <div className="flex items-center gap-1.5 text-sm">
                <input type="time" value={a} onChange={e => set(d.key, `${e.target.value}-${b || '23:00'}`)}
                  className="h-8 rounded-md border border-input bg-transparent px-2 [color-scheme:dark]" />
                <span className="text-muted-foreground">às</span>
                <input type="time" value={b} onChange={e => set(d.key, `${a || '18:00'}-${e.target.value}`)}
                  className="h-8 rounded-md border border-input bg-transparent px-2 [color-scheme:dark]" />
              </div>
            )}
            {open && multi && (
              <input value={value} onChange={e => set(d.key, e.target.value)}
                className="h-8 flex-1 min-w-0 rounded-md border border-input bg-transparent px-2 text-sm" />
            )}
            {!open && <span className="text-sm text-muted-foreground">Fechado</span>}
          </div>
        )
      })}
      <Button type="button" variant="ghost" size="sm" onClick={copyFirst}><Copy /> Usar o primeiro horário em todos os dias</Button>
    </div>
  )
}

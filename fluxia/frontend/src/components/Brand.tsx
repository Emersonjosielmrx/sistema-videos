import { Zap } from 'lucide-react'
import { cn } from '@/lib/utils'

export function Brand({ small }: { small?: boolean }) {
  return (
    <div className="flex items-center gap-2.5">
      <span className={cn('flex items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-glow', small ? 'h-8 w-8' : 'h-10 w-10')}>
        <Zap className={small ? 'h-4 w-4' : 'h-5 w-5'} />
      </span>
      <span className={cn('font-black tracking-tight text-gradient leading-none', small ? 'text-lg' : 'text-xl')}>FluxIA</span>
    </div>
  )
}

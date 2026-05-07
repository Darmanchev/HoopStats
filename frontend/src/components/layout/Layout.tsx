import type { ReactNode } from 'react'
import Sidebar from './Sidebar'

interface Props {
  active: string
  onNavigate: (view: string) => void
  children: ReactNode
}

export default function Layout({ active, onNavigate, children }: Props) {
  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', background: '#F4F6FC', color: '#1C2235' }}>
      <Sidebar active={active} onNavigate={onNavigate} />
      <main style={{ flex: 1, overflowY: 'auto', minWidth: 0 }}>
        {children}
      </main>
    </div>
  )
}
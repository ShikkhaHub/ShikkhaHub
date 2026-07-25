import { useEffect, useCallback, useRef } from 'react'

interface Shortcut {
  key: string
  ctrl?: boolean
  alt?: boolean
  shift?: boolean
  meta?: boolean
  action: () => void
  description: string
  scope?: string
}

class KeyboardShortcutManager {
  private shortcuts: Map<string, Shortcut> = new Map()
  private enabled: boolean = true

  register(shortcut: Shortcut): () => void {
    const key = this.normalizeKey(shortcut)
    this.shortcuts.set(key, shortcut)

    return () => {
      this.shortcuts.delete(key)
    }
  }

  handleKeydown = (event: KeyboardEvent) => {
    if (!this.enabled) return

    const key = this.buildKeyString(event)
    const shortcut = this.shortcuts.get(key)

    if (shortcut) {
      event.preventDefault()
      shortcut.action()
    }
  }

  private normalizeKey(shortcut: Shortcut): string {
    const parts: string[] = []
    if (shortcut.ctrl) parts.push('ctrl')
    if (shortcut.alt) parts.push('alt')
    if (shortcut.shift) parts.push('shift')
    if (shortcut.meta) parts.push('meta')
    parts.push(shortcut.key.toLowerCase())
    return parts.join('+')
  }

  private buildKeyString(event: KeyboardEvent): string {
    const parts: string[] = []
    if (event.ctrlKey) parts.push('ctrl')
    if (event.altKey) parts.push('alt')
    if (event.shiftKey) parts.push('shift')
    if (event.metaKey) parts.push('meta')
    parts.push(event.key.toLowerCase())
    return parts.join('+')
  }

  setEnabled(enabled: boolean) {
    this.enabled = enabled
  }

  getShortcuts(): Shortcut[] {
    return Array.from(this.shortcuts.values())
  }
}

const globalShortcutManager = new KeyboardShortcutManager()

export function initKeyboardShortcuts() {
  document.addEventListener('keydown', globalShortcutManager.handleKeydown)
  return () => {
    document.removeEventListener('keydown', globalShortcutManager.handleKeydown)
  }
}

export function useKeyboardShortcut(shortcut: Shortcut) {
  const unregisterRef = useRef<(() => void) | null>(null)

  useEffect(() => {
    unregisterRef.current = globalShortcutManager.register(shortcut)

    return () => {
      if (unregisterRef.current) {
        unregisterRef.current()
      }
    }
  }, [shortcut.key, shortcut.ctrl, shortcut.alt, shortcut.shift, shortcut.meta])
}

export function useGlobalShortcuts(shortcuts: Shortcut[]) {
  useEffect(() => {
    const unregisters: (() => void)[] = []

    shortcuts.forEach((shortcut) => {
      unregisters.push(globalShortcutManager.register(shortcut))
    })

    return () => {
      unregisters.forEach((unregister) => unregister())
    }
  }, [shortcuts])
}

export function KeyboardShortcutsHelp() {
  const shortcuts = globalShortcutManager.getShortcuts()

  const formatShortcut = (s: Shortcut) => {
    const parts: string[] = []
    if (s.ctrl) parts.push('Ctrl')
    if (s.alt) parts.push('Alt')
    if (s.shift) parts.push('Shift')
    if (s.meta) parts.push('⌘')
    parts.push(s.key.toUpperCase())
    return parts.join(' + ')
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-card rounded-xl shadow-elevated p-6 max-w-md w-full mx-4">
        <h2 className="text-xl font-bold mb-4">Keyboard Shortcuts</h2>
        <div className="space-y-2">
          {shortcuts.map((shortcut, index) => (
            <div key={index} className="flex justify-between items-center py-2 border-b border-border last:border-0">
              <span className="text-sm text-muted-foreground">{shortcut.description}</span>
              <kbd className="px-2 py-1 bg-secondary rounded text-xs font-mono">
                {formatShortcut(shortcut)}
              </kbd>
            </div>
          ))}
        </div>
        <p className="mt-4 text-xs text-muted-foreground text-center">
          Press ? to show this help dialog
        </p>
      </div>
    </div>
  )
}

// Predefined shortcuts
export const DEFAULT_SHORTCUTS = {
  search: { key: 'k', ctrl: true, description: 'Focus search', action: () => {} },
  help: { key: '?', description: 'Show keyboard shortcuts', action: () => {} },
  darkMode: { key: 'd', ctrl: true, shift: true, description: 'Toggle dark mode', action: () => {} },
  home: { key: 'h', ctrl: true, description: 'Go to home', action: () => {} },
  compare: { key: 'c', ctrl: true, shift: true, description: 'Compare institutions', action: () => {} },
  back: { key: 'Escape', description: 'Close modal / Go back', action: () => {} },
}

import '@testing-library/jest-dom/vitest'
import { configure } from '@testing-library/react'
import { toast } from 'sonner'
import { afterEach } from 'vitest'

// Modais e menus do Radix são pesados no jsdom; com a suíte inteira em paralelo, 1 s
// (padrão de findBy/waitFor) às vezes não basta; com os modais da fase 2, nem 3 s.
configure({ asyncUtilTimeout: 5000 })

// Os toasts ficam num estado global do sonner: sem isto, os de um teste aparecem no seguinte.
afterEach(() => {
  toast.dismiss()
})

// APIs do navegador que o jsdom não tem e os componentes Radix (shadcn) usam.
class ResizeObserverFalso {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver ??= ResizeObserverFalso
Element.prototype.hasPointerCapture ??= () => false
Element.prototype.setPointerCapture ??= () => {}
Element.prototype.releasePointerCapture ??= () => {}
Element.prototype.scrollIntoView ??= () => {}

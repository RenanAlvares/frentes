import { useEffect, useRef } from 'react'

const TIPOS_SEM_TEXTO = new Set([
  'checkbox',
  'radio',
  'button',
  'submit',
  'reset',
  'range',
  'color',
  'file',
])

/** RN-130: atalhos de uma tecla não disparam com o foco num campo de texto. */
export function focoEmCampoDeTexto(alvo: EventTarget | null): boolean {
  if (!(alvo instanceof HTMLElement)) return false
  if (alvo.isContentEditable || alvo.tagName === 'TEXTAREA' || alvo.tagName === 'SELECT') {
    return true
  }
  return alvo instanceof HTMLInputElement && !TIPOS_SEM_TEXTO.has(alvo.type)
}

/** Com um diálogo ou menu aberto, os atalhos da tela por baixo ficam desligados (o Esc é dele). */
function camadaAberta(): boolean {
  return document.querySelector('[role="dialog"], [role="alertdialog"], [role="menu"]') !== null
}

/**
 * RN-130: atalho de uma tecla (sem Ctrl/Alt/Meta), fora de campos de texto e de camadas abertas.
 * `ativo = false` desliga sem tirar o hook do componente.
 */
export function useAtalho(tecla: string, acao: () => void, ativo = true) {
  // A ação mais recente, sem recriar o listener a cada render.
  const acaoAtual = useRef(acao)
  useEffect(() => {
    acaoAtual.current = acao
  })

  useEffect(() => {
    if (!ativo) return
    function aoTeclar(evento: KeyboardEvent) {
      if (evento.key.toLowerCase() !== tecla.toLowerCase()) return
      if (evento.ctrlKey || evento.metaKey || evento.altKey || evento.defaultPrevented) return
      if (focoEmCampoDeTexto(evento.target) || camadaAberta()) return
      evento.preventDefault()
      acaoAtual.current()
    }
    window.addEventListener('keydown', aoTeclar)
    return () => window.removeEventListener('keydown', aoTeclar)
  }, [tecla, ativo])
}

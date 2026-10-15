// Query keys centralizadas (05-frontend §4).
export const chaves = {
  saude: () => ['saude'] as const,
  projetos: {
    /** Prefixo de todas as chaves de projetos (invalidação `projetos.*`). */
    todos: () => ['projetos'] as const,
    lista: (arquivados: boolean) => ['projetos', 'lista', { arquivados }] as const,
    detalhe: (id: string) => ['projetos', 'detalhe', id] as const,
  },
}

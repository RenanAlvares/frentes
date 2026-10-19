// Query keys centralizadas (05-frontend §4).
export const chaves = {
  saude: () => ['saude'] as const,
  projetos: {
    /** Prefixo de todas as chaves de projetos (invalidação `projetos.*`). */
    todos: () => ['projetos'] as const,
    lista: (arquivados: boolean) => ['projetos', 'lista', { arquivados }] as const,
    detalhe: (id: string) => ['projetos', 'detalhe', id] as const,
  },
  tarefas: {
    quadro: (projetoId: string) => ['tarefas', 'quadro', projetoId] as const,
    concluidas: (projetoId: string) => ['tarefas', 'concluidas', projetoId] as const,
    detalhe: (id: string) => ['tarefas', 'detalhe', id] as const,
    hoje: () => ['tarefas', 'hoje'] as const,
  },
  lembretes: {
    lista: (projetoId: string) => ['lembretes', 'lista', projetoId] as const,
  },
  avisos: () => ['avisos'] as const,
  documentos: {
    lista: (projetoId: string) => ['documentos', 'lista', projetoId] as const,
  },
  anotacoes: {
    lista: (projetoId: string) => ['anotacoes', 'lista', projetoId] as const,
  },
  lixeira: () => ['lixeira'] as const,
  configuracoes: () => ['configuracoes'] as const,
}

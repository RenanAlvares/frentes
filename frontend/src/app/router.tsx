import type { RouteObject } from 'react-router'
import { Layout } from '@/app/layout/Layout'
import { PaginaConfiguracoes } from '@/features/configuracoes/components/PaginaConfiguracoes'
import { PaginaHoje } from '@/features/hoje/components/PaginaHoje'
import { PaginaLixeira } from '@/features/lixeira/components/PaginaLixeira'
import { PaginaArquivados } from '@/features/projetos/components/PaginaArquivados'
import { PaginaProjeto } from '@/features/projetos/components/PaginaProjeto'
import { PaginaProjetos } from '@/features/projetos/components/PaginaProjetos'

// Rotas de 01-produto §3. `?tarefa=:id` (modal da tarefa) é lido dentro de PaginaProjeto.
export const rotas: RouteObject[] = [
  {
    element: <Layout />,
    children: [
      { index: true, element: <PaginaProjetos /> },
      { path: 'hoje', element: <PaginaHoje /> },
      { path: 'projetos/:id', element: <PaginaProjeto /> },
      { path: 'arquivados', element: <PaginaArquivados /> },
      { path: 'lixeira', element: <PaginaLixeira /> },
      { path: 'configuracoes', element: <PaginaConfiguracoes /> },
    ],
  },
]

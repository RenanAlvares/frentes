import createClient from 'openapi-fetch'
import { criarErroApi } from '@/api/erros'
import type { paths } from '@/api/schema'

// 05-frontend §3: toda chamada à API passa por este client tipado.
export const client = createClient<paths>({ baseUrl: '' })

type Resultado<T> = { data?: T; error?: unknown; response: Response }

/** Devolve os dados da resposta ou lança `ErroApi`. Uso: `exigir(client.GET('/api/saude'))`. */
export async function exigir<T>(requisicao: Promise<Resultado<T>>): Promise<T> {
  const { data, error, response } = await requisicao
  if (!response.ok) {
    throw criarErroApi(response.status, error)
  }
  return data as T
}

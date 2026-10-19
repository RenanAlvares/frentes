import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'
import { z } from 'zod'
import { camposDoErro, mensagemDoErro } from '@/api/erros'
import { useSaude } from '@/app/layout/useSaude'
import { CampoForm } from '@/components/comum/CampoForm'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import {
  type Configuracoes,
  useAtualizarConfiguracoes,
  useConfiguracoes,
} from '@/features/configuracoes/hooks/useConfiguracoes'
import { atributosDeErro } from '@/lib/formulario'

// RN-100: as duas chaves de 0 a 60 dias. A API valida de novo.
const dias = z
  .number({ error: 'Informe um número de 0 a 60.' })
  .int('Use um número inteiro.')
  .min(0, 'Use de 0 a 60 dias.')
  .max(60, 'Use de 0 a 60 dias.')
const esquema = z.object({ aviso_tarefas_dias: dias, antecedencia_padrao_lembretes: dias })

type Campo = keyof Configuracoes

const CAMPOS: { campo: Campo; rotulo: string }[] = [
  {
    campo: 'aviso_tarefas_dias',
    rotulo: 'Avisar tarefas com prazo com quantos dias de antecedência',
  },
  { campo: 'antecedencia_padrao_lembretes', rotulo: 'Antecedência padrão de novos lembretes' },
]

/** Configurações (01 §4.9). A seção de backup entra com a 5.3. */
export function PaginaConfiguracoes() {
  const { data: configuracoes, isPending, isError, error } = useConfiguracoes()
  const { data: saude } = useSaude()

  let conteudo
  if (isPending) {
    conteudo = <Skeleton className="h-40 rounded-xl" />
  } else if (isError) {
    conteudo = (
      <p role="alert" className="text-sm text-destructive">
        {mensagemDoErro(error)}
      </p>
    )
  } else {
    conteudo = <FormularioConfiguracoes inicial={configuracoes} />
  }

  return (
    <div className="mx-auto grid max-w-2xl gap-4">
      <h1 className="text-xl font-semibold">Configurações</h1>
      {conteudo}
      {saude && <p className="text-sm text-muted-foreground">Frentes versão {saude.versao}</p>}
    </div>
  )
}

function FormularioConfiguracoes({ inicial }: { inicial: Configuracoes }) {
  const atualizar = useAtualizarConfiguracoes()
  const {
    register,
    handleSubmit,
    setError,
    reset,
    formState: { errors, dirtyFields, isDirty, isSubmitting },
  } = useForm<Configuracoes>({ resolver: zodResolver(esquema), defaultValues: inicial })

  const enviar = handleSubmit(async (valores) => {
    // PATCH: só o que mudou.
    const corpo = Object.fromEntries(
      CAMPOS.filter(({ campo }) => dirtyFields[campo]).map(({ campo }) => [campo, valores[campo]]),
    )
    try {
      const salvas = await atualizar.mutateAsync(corpo)
      reset(salvas)
      toast('Configurações salvas')
    } catch (erro) {
      const campos = Object.entries(camposDoErro(erro)).filter(([campo]) => campo in inicial)
      campos.forEach(([campo, mensagem]) => setError(campo as Campo, { message: mensagem }))
      if (campos.length === 0) toast.error(mensagemDoErro(erro))
    }
  })

  return (
    <form onSubmit={enviar} noValidate className="grid gap-4 rounded-xl border bg-white p-4">
      {CAMPOS.map(({ campo, rotulo }) => {
        const erro = errors[campo]?.message
        return (
          <CampoForm key={campo} id={campo} rotulo={rotulo} erro={erro}>
            <div className="flex items-center gap-2">
              <Input
                id={campo}
                type="number"
                min={0}
                max={60}
                className="w-24"
                {...register(campo, { valueAsNumber: true })}
                {...atributosDeErro(campo, erro)}
              />
              <span className="text-sm text-muted-foreground">dias</span>
            </div>
          </CampoForm>
        )
      })}
      <div className="flex justify-end">
        <Button type="submit" disabled={!isDirty || isSubmitting}>
          Salvar
        </Button>
      </div>
    </form>
  )
}

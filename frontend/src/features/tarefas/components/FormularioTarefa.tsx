import { zodResolver } from '@hookform/resolvers/zod'
import { useEffect, type ReactNode } from 'react'
import { Controller, useForm, useWatch } from 'react-hook-form'
import { toast } from 'sonner'
import type { z } from 'zod'
import { camposDoErro, mensagemDoErro } from '@/api/erros'
import { CampoForm } from '@/components/comum/CampoForm'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { CamposDoTipo, Chip } from '@/features/tarefas/components/CamposDoTipo'
import {
  esquemaTarefa,
  LISTA_PRIORIDADES,
  LISTA_TIPOS,
  ROTULO_PRIORIDADE,
  ROTULO_TIPO,
  type Sujos,
  type ValoresTarefa,
} from '@/features/tarefas/formulario'
import { COLUNAS, ROTULO_COLUNA } from '@/features/tarefas/quadro'
import { atributosDeErro } from '@/lib/formulario'

type Campo = keyof ValoresTarefa

type Props = {
  inicial: ValoresTarefa
  edicao: boolean
  /** Recebe os valores e os campos alterados (para montar o PATCH). */
  onSalvar: (valores: ValoresTarefa, sujos: Sujos) => Promise<void>
  onSujoChange: (sujo: boolean) => void
  /** Botões à esquerda e antes do Salvar (Excluir, Concluir, +1), só na edição. */
  acoesEsquerda?: ReactNode
  acoesDireita?: ReactNode
}

/** Erro 422 da API no campo do formulário (a regra de repetição fica no editor). */
const campoDoFormulario = (campo: string) => (campo.startsWith('recorrencia') ? 'editor' : campo)

/** 01 §4.5 e §4.6: título, status, prioridade, tipo, campos do tipo e descrição; Salvar (RN-85). */
export function FormularioTarefa(props: Props) {
  const { inicial, edicao, onSalvar, onSujoChange } = props
  const {
    register,
    control,
    handleSubmit,
    setError,
    formState: { errors, dirtyFields, isDirty, isSubmitting },
  } = useForm<z.input<typeof esquemaTarefa>, unknown, ValoresTarefa>({
    resolver: zodResolver(esquemaTarefa),
    defaultValues: inicial,
  })
  const [tipo, prazo] = useWatch({ control, name: ['tipo', 'prazo'] })

  useEffect(() => onSujoChange(isDirty), [isDirty, onSujoChange])

  const enviar = handleSubmit(async (valores) => {
    try {
      await onSalvar(valores, dirtyFields)
    } catch (erro) {
      const campos = Object.entries(camposDoErro(erro))
        .map(([campo, mensagem]) => [campoDoFormulario(campo), mensagem] as const)
        .filter(([campo]) => campo in inicial)
      campos.forEach(([campo, mensagem]) => setError(campo as Campo, { message: mensagem }))
      if (campos.length === 0) toast.error(mensagemDoErro(erro))
    }
  })

  const erro = (campo: Campo) => errors[campo]?.message

  return (
    <form onSubmit={enviar} noValidate className="grid gap-4">
      <CampoForm id="titulo" rotulo="Título" rotuloOculto erro={erro('titulo')}>
        <Input
          id="titulo"
          autoFocus
          placeholder="Título da tarefa"
          className="h-10 text-base font-medium"
          {...register('titulo')}
          {...atributosDeErro('titulo', erro('titulo'))}
        />
      </CampoForm>
      <div className="flex flex-wrap items-start gap-2">
        {/* RN-24: a coluna da meta vem das execuções; não há status para escolher. */}
        {edicao && tipo !== 'meta_mensal' && (
          <Controller
            control={control}
            name="status"
            render={({ field }) => (
              <Chip id="status" rotulo="Status">
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger id="status" size="sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {COLUNAS.map((status) => (
                      <SelectItem key={status} value={status}>
                        {ROTULO_COLUNA[status]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Chip>
            )}
          />
        )}
        <Controller
          control={control}
          name="prioridade"
          render={({ field }) => (
            <Chip id="prioridade" rotulo="Prioridade">
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger id="prioridade" size="sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {LISTA_PRIORIDADES.map((prioridade) => (
                    <SelectItem key={prioridade} value={prioridade}>
                      Prioridade {ROTULO_PRIORIDADE[prioridade].toLowerCase()}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Chip>
          )}
        />
        <Controller
          control={control}
          name="tipo"
          render={({ field }) => (
            <Chip id="tipo" rotulo="Tipo">
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger id="tipo" size="sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {LISTA_TIPOS.map((opcao) => (
                    <SelectItem key={opcao} value={opcao}>
                      {ROTULO_TIPO[opcao]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Chip>
          )}
        />
      </div>
      <CamposDoTipo control={control} errors={errors} tipo={tipo} prazo={prazo} edicao={edicao} />
      <CampoForm id="descricao" rotulo="Descrição" erro={erro('descricao')}>
        <Textarea
          id="descricao"
          rows={4}
          {...register('descricao')}
          {...atributosDeErro('descricao', erro('descricao'))}
        />
      </CampoForm>
      <div className="flex flex-wrap items-center gap-2 pt-2">
        {props.acoesEsquerda}
        <div className="ml-auto flex gap-2">
          {props.acoesDireita}
          <Button type="submit" carregando={isSubmitting}>
            Salvar
          </Button>
        </div>
      </div>
    </form>
  )
}

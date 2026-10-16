import { zodResolver } from '@hookform/resolvers/zod'
import { useEffect, type ReactNode } from 'react'
import { Controller, useForm } from 'react-hook-form'
import { toast } from 'sonner'
import type { z } from 'zod'
import { camposDoErro, mensagemDoErro } from '@/api/erros'
import { CampoData } from '@/components/comum/CampoData'
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
import {
  esquemaTarefa,
  LISTA_PRIORIDADES,
  ROTULO_PRIORIDADE,
  ROTULO_TIPO,
  type ValoresTarefa,
} from '@/features/tarefas/formulario'
import { COLUNAS, ROTULO_COLUNA, type Tarefa } from '@/features/tarefas/quadro'
import { atributosDeErro } from '@/lib/formulario'

type Campo = keyof ValoresTarefa

type Props = {
  inicial: ValoresTarefa
  /** Ausente na criação (a tarefa nova nasce Pendente e simples). */
  tipo?: Tarefa['tipo']
  /** Recebe todos os valores e só os alterados (para o PATCH). */
  onSalvar: (valores: ValoresTarefa, alterados: Partial<ValoresTarefa>) => Promise<void>
  onSujoChange: (sujo: boolean) => void
  /** Botões à esquerda e antes do Salvar (Excluir, Concluir), só na edição. */
  acoesEsquerda?: ReactNode
  acoesDireita?: ReactNode
}

/** 01 §4.5: título, chips de status, prioridade e prazo, tipo e descrição; Salvar (RN-85). */
export function FormularioTarefa(props: Props) {
  const { inicial, tipo, onSalvar, onSujoChange } = props
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

  useEffect(() => onSujoChange(isDirty), [isDirty, onSujoChange])

  const enviar = handleSubmit(async (valores) => {
    const alterados = Object.fromEntries(
      Object.entries(valores).filter(([campo]) => dirtyFields[campo as Campo]),
    )
    try {
      await onSalvar(valores, alterados)
    } catch (erro) {
      const campos = Object.entries(camposDoErro(erro)).filter(([campo]) => campo in inicial)
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
        {tipo !== undefined && (
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
          name="prazo"
          render={({ field }) => (
            <Chip id="prazo" rotulo="Prazo" erro={erro('prazo')}>
              <CampoData
                id="prazo"
                valor={field.value}
                onChange={field.onChange}
                invalido={Boolean(erro('prazo'))}
              />
            </Chip>
          )}
        />
        <span className="self-center text-sm text-muted-foreground">
          Tipo: {ROTULO_TIPO[tipo ?? 'simples']}
        </span>
      </div>
      <CampoForm id="descricao" rotulo="Descrição" erro={erro('descricao')}>
        <Textarea
          id="descricao"
          rows={5}
          {...register('descricao')}
          {...atributosDeErro('descricao', erro('descricao'))}
        />
      </CampoForm>
      <div className="flex flex-wrap items-center gap-2 pt-2">
        {props.acoesEsquerda}
        <div className="ml-auto flex gap-2">
          {props.acoesDireita}
          <Button type="submit" disabled={isSubmitting}>
            Salvar
          </Button>
        </div>
      </div>
    </form>
  )
}

function Chip(props: { id: string; rotulo: string; erro?: string; children: ReactNode }) {
  return (
    <CampoForm id={props.id} rotulo={props.rotulo} rotuloOculto erro={props.erro} className="gap-1">
      {props.children}
    </CampoForm>
  )
}

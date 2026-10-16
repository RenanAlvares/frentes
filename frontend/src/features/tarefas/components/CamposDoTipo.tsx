import type { ReactNode } from 'react'
import { Controller, type Control, type FieldErrors } from 'react-hook-form'
import type { z } from 'zod'
import { CampoData } from '@/components/comum/CampoData'
import { CampoForm } from '@/components/comum/CampoForm'
import { EditorRecorrencia } from '@/components/comum/EditorRecorrencia'
import { Input } from '@/components/ui/input'
import type { esquemaTarefa, ValoresTarefa } from '@/features/tarefas/formulario'
import { atributosDeErro } from '@/lib/formulario'

type Props = {
  control: Control<z.input<typeof esquemaTarefa>, unknown, ValoresTarefa>
  errors: FieldErrors<ValoresTarefa>
  tipo: ValoresTarefa['tipo']
  prazo: string | null
  edicao: boolean
}

/**
 * 01 §4.6: Simples → prazo opcional; Repetida → primeira data* + editor de repetição*;
 * Meta mensal → "Quantas vezes por mês"*.
 */
export function CamposDoTipo({ control, errors, tipo, prazo, edicao }: Props) {
  if (tipo === 'meta_mensal') {
    const erro = errors.meta_mensal?.message
    return (
      <Controller
        control={control}
        name="meta_mensal"
        render={({ field }) => (
          <CampoForm id="meta_mensal" rotulo="Quantas vezes por mês *" erro={erro} className="w-56">
            <Input
              id="meta_mensal"
              type="number"
              min={1}
              max={31}
              value={field.value ?? ''}
              onChange={(e) => field.onChange(e.target.value ? e.target.valueAsNumber : null)}
              {...atributosDeErro('meta_mensal', erro)}
            />
          </CampoForm>
        )}
      />
    )
  }

  const repetida = tipo === 'repetida'
  const rotuloData = repetida ? (edicao ? 'Próxima data *' : 'Primeira data *') : 'Prazo'
  const erroData = errors.prazo?.message
  return (
    <div className="grid gap-3">
      <Controller
        control={control}
        name="prazo"
        render={({ field }) => (
          <CampoForm id="prazo" rotulo={rotuloData} erro={erroData} className="w-64">
            <CampoData
              id="prazo"
              valor={field.value}
              onChange={field.onChange}
              invalido={Boolean(erroData)}
              descricaoId={erroData ? 'prazo-erro' : undefined}
            />
          </CampoForm>
        )}
      />
      {repetida && (
        <Controller
          control={control}
          name="editor"
          render={({ field }) => (
            <EditorRecorrencia
              id="editor"
              valor={field.value}
              primeiraData={prazo}
              onChange={field.onChange}
              mostrarErro={Boolean(errors.editor)}
            />
          )}
        />
      )}
    </div>
  )
}

/** Campo compacto do modal (status, prioridade, tipo): rótulo só para leitores de tela. */
export function Chip(props: { id: string; rotulo: string; erro?: string; children: ReactNode }) {
  return (
    <CampoForm id={props.id} rotulo={props.rotulo} rotuloOculto erro={props.erro} className="gap-1">
      {props.children}
    </CampoForm>
  )
}

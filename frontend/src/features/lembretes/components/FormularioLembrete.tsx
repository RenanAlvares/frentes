import { zodResolver } from '@hookform/resolvers/zod'
import { useEffect } from 'react'
import { Controller, useForm, useWatch } from 'react-hook-form'
import { toast } from 'sonner'
import type { z } from 'zod'
import { camposDoErro, mensagemDoErro } from '@/api/erros'
import { CampoData } from '@/components/comum/CampoData'
import { CampoForm } from '@/components/comum/CampoForm'
import { EditorRecorrencia } from '@/components/comum/EditorRecorrencia'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import {
  esquemaLembrete,
  type SujosLembrete,
  type ValoresLembrete,
} from '@/features/lembretes/formulario'
import { atributosDeErro } from '@/lib/formulario'

type Campo = keyof ValoresLembrete

type Props = {
  inicial: ValoresLembrete
  edicao: boolean
  onSalvar: (valores: ValoresLembrete, sujos: SujosLembrete) => Promise<void>
  onSujoChange: (sujo: boolean) => void
}

/** Erro 422 da API no campo do formulário (a regra fica no editor). */
const campoDoFormulario = (campo: string) => (campo.startsWith('recorrencia') ? 'editor' : campo)

/** 01 §4.6 (Lembrete): título*, observação, vencimento*, antecedência, "Repetir" + editor. */
export function FormularioLembrete({ inicial, edicao, onSalvar, onSujoChange }: Props) {
  const {
    register,
    control,
    handleSubmit,
    setError,
    formState: { errors, dirtyFields, isDirty, isSubmitting },
  } = useForm<z.input<typeof esquemaLembrete>, unknown, ValoresLembrete>({
    resolver: zodResolver(esquemaLembrete),
    defaultValues: inicial,
  })
  const [vencimento, repetir] = useWatch({ control, name: ['vencimento', 'repetir'] })

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
      <CampoForm id="titulo" rotulo="Título *" erro={erro('titulo')}>
        <Input
          id="titulo"
          autoFocus
          {...register('titulo')}
          {...atributosDeErro('titulo', erro('titulo'))}
        />
      </CampoForm>
      <CampoForm id="observacao" rotulo="Observação" erro={erro('observacao')}>
        <Textarea
          id="observacao"
          rows={3}
          {...register('observacao')}
          {...atributosDeErro('observacao', erro('observacao'))}
        />
      </CampoForm>
      <div className="grid gap-4 sm:grid-cols-2">
        <Controller
          control={control}
          name="vencimento"
          render={({ field }) => (
            <CampoForm id="vencimento" rotulo="Vencimento *" erro={erro('vencimento')}>
              <CampoData
                id="vencimento"
                valor={field.value}
                onChange={field.onChange}
                invalido={Boolean(erro('vencimento'))}
                descricaoId={erro('vencimento') ? 'vencimento-erro' : undefined}
              />
            </CampoForm>
          )}
        />
        <Controller
          control={control}
          name="antecedencia_dias"
          render={({ field }) => (
            <CampoForm
              id="antecedencia_dias"
              rotulo="Avisar com quantos dias de antecedência"
              erro={erro('antecedencia_dias')}
            >
              <Input
                id="antecedencia_dias"
                type="number"
                min={0}
                max={60}
                placeholder={edicao ? undefined : 'padrão das configurações'}
                value={field.value ?? ''}
                onChange={(e) => field.onChange(e.target.value ? e.target.valueAsNumber : null)}
                {...atributosDeErro('antecedencia_dias', erro('antecedencia_dias'))}
              />
            </CampoForm>
          )}
        />
      </div>
      <div className="flex items-center gap-3">
        <Controller
          control={control}
          name="repetir"
          render={({ field }) => (
            <Switch id="repetir" checked={field.value} onCheckedChange={field.onChange} />
          )}
        />
        <Label htmlFor="repetir">Repetir</Label>
      </div>
      {repetir && (
        <Controller
          control={control}
          name="editor"
          render={({ field }) => (
            <EditorRecorrencia
              id="editor"
              valor={field.value}
              primeiraData={vencimento}
              onChange={field.onChange}
              mostrarErro={Boolean(errors.editor)}
            />
          )}
        />
      )}
      <div className="flex justify-end pt-2">
        <Button type="submit" carregando={isSubmitting}>
          Salvar
        </Button>
      </div>
    </form>
  )
}

import { zodResolver } from '@hookform/resolvers/zod'
import { useEffect } from 'react'
import { Controller, useForm } from 'react-hook-form'
import { toast } from 'sonner'
import type { z } from 'zod'
import { camposDoErro, mensagemDoErro } from '@/api/erros'
import { CampoData } from '@/components/comum/CampoData'
import { CampoForm } from '@/components/comum/CampoForm'
import { SeletorCor } from '@/components/comum/SeletorCor'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import { esquemaProjeto, type ValoresProjeto } from '@/features/projetos/formulario'
import { LISTA_STATUS, ROTULO_STATUS } from '@/features/projetos/status'
import { atributosDeErro } from '@/lib/formulario'

type Campo = keyof ValoresProjeto

type Props = {
  inicial: ValoresProjeto
  /** Recebe todos os valores e só os alterados (para o PATCH). */
  onSalvar: (valores: ValoresProjeto, alterados: Partial<ValoresProjeto>) => Promise<void>
  onCancelar: () => void
  onSujoChange: (sujo: boolean) => void
}

export function FormularioProjeto({ inicial, onSalvar, onCancelar, onSujoChange }: Props) {
  const {
    register,
    control,
    handleSubmit,
    setError,
    formState: { errors, dirtyFields, isDirty, isSubmitting },
  } = useForm<z.input<typeof esquemaProjeto>, unknown, ValoresProjeto>({
    resolver: zodResolver(esquemaProjeto),
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
      // 422: mensagem da API abaixo do campo; o resto vira toast.
      const campos = Object.entries(camposDoErro(erro)).filter(([campo]) => campo in inicial)
      campos.forEach(([campo, mensagem]) => setError(campo as Campo, { message: mensagem }))
      if (campos.length === 0) toast.error(mensagemDoErro(erro))
    }
  })

  const erro = (campo: Campo) => errors[campo]?.message

  return (
    <form onSubmit={enviar} noValidate className="grid gap-4">
      <CampoForm id="nome" rotulo="Nome *" erro={erro('nome')}>
        <Input
          id="nome"
          autoFocus
          {...register('nome')}
          {...atributosDeErro('nome', erro('nome'))}
        />
      </CampoForm>
      <CampoForm id="descricao" rotulo="Descrição" erro={erro('descricao')}>
        <Textarea
          id="descricao"
          rows={3}
          {...register('descricao')}
          {...atributosDeErro('descricao', erro('descricao'))}
        />
      </CampoForm>
      <div className="grid gap-4 sm:grid-cols-2">
        <CampoForm id="status" rotulo="Status" erro={erro('status')}>
          <Controller
            control={control}
            name="status"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger
                  id="status"
                  className="w-full"
                  {...atributosDeErro('status', erro('status'))}
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {LISTA_STATUS.map((status) => (
                    <SelectItem key={status} value={status}>
                      {ROTULO_STATUS[status]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </CampoForm>
        <CampoForm id="cor" rotulo="Cor" erro={erro('cor')}>
          <Controller
            control={control}
            name="cor"
            render={({ field }) => (
              <SeletorCor id="cor" valor={field.value} onChange={field.onChange} />
            )}
          />
        </CampoForm>
        {(['data_inicio', 'prazo'] as const).map((campo) => (
          <CampoForm
            key={campo}
            id={campo}
            rotulo={campo === 'prazo' ? 'Prazo' : 'Data de início'}
            erro={erro(campo)}
          >
            <Controller
              control={control}
              name={campo}
              render={({ field }) => (
                <CampoData
                  id={campo}
                  valor={field.value}
                  onChange={field.onChange}
                  invalido={Boolean(erro(campo))}
                  descricaoId={erro(campo) ? `${campo}-erro` : undefined}
                />
              )}
            />
          </CampoForm>
        ))}
      </div>
      <div className="flex items-center gap-3">
        <Controller
          control={control}
          name="acompanhar_progresso"
          render={({ field }) => (
            <Switch
              id="acompanhar_progresso"
              checked={field.value}
              onCheckedChange={field.onChange}
            />
          )}
        />
        <Label htmlFor="acompanhar_progresso">Acompanhar progresso</Label>
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="outline" onClick={onCancelar}>
          Cancelar
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          Salvar
        </Button>
      </div>
    </form>
  )
}

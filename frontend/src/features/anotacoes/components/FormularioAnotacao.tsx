import { zodResolver } from '@hookform/resolvers/zod'
import { type ReactNode, useEffect } from 'react'
import { Controller, useForm } from 'react-hook-form'
import { toast } from 'sonner'
import type { z } from 'zod'
import { camposDoErro, mensagemDoErro } from '@/api/erros'
import { CampoForm } from '@/components/comum/CampoForm'
import { SeletorCor } from '@/components/comum/SeletorCor'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import {
  esquemaAnotacao,
  type SujosAnotacao,
  type ValoresAnotacao,
} from '@/features/anotacoes/formulario'
import { CORES_ANOTACAO } from '@/lib/cores'
import { atributosDeErro } from '@/lib/formulario'

type Campo = keyof ValoresAnotacao

type Props = {
  inicial: ValoresAnotacao
  onSalvar: (valores: ValoresAnotacao, sujos: SujosAnotacao) => Promise<void>
  onSujoChange: (sujo: boolean) => void
  /** Ex.: "Excluir" na edição. */
  acoesEsquerda?: ReactNode
}

/** 01 §4.6 (Anotação): título, texto*, cor (6 opções), fixar. */
export function FormularioAnotacao({ inicial, onSalvar, onSujoChange, acoesEsquerda }: Props) {
  const {
    register,
    control,
    handleSubmit,
    setError,
    formState: { errors, dirtyFields, isDirty, isSubmitting },
  } = useForm<z.input<typeof esquemaAnotacao>, unknown, ValoresAnotacao>({
    resolver: zodResolver(esquemaAnotacao),
    defaultValues: inicial,
  })

  useEffect(() => onSujoChange(isDirty), [isDirty, onSujoChange])

  const enviar = handleSubmit(async (valores) => {
    try {
      await onSalvar(valores, dirtyFields)
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
      <CampoForm id="titulo-anotacao" rotulo="Título" erro={erro('titulo')}>
        <Input
          id="titulo-anotacao"
          {...register('titulo')}
          {...atributosDeErro('titulo-anotacao', erro('titulo'))}
        />
      </CampoForm>
      <CampoForm id="texto-anotacao" rotulo="Texto *" erro={erro('texto')}>
        <Textarea
          id="texto-anotacao"
          autoFocus
          rows={8}
          // Cresce com o texto até metade da tela; depois rola por dentro.
          className="max-h-[50vh]"
          {...register('texto')}
          {...atributosDeErro('texto-anotacao', erro('texto'))}
        />
      </CampoForm>
      <CampoForm id="cor-anotacao" rotulo="Cor">
        <Controller
          control={control}
          name="cor"
          render={({ field }) => (
            <SeletorCor
              id="cor-anotacao"
              valor={field.value}
              onChange={field.onChange}
              paleta={CORES_ANOTACAO}
            />
          )}
        />
      </CampoForm>
      <div className="flex items-center gap-3">
        <Controller
          control={control}
          name="fixada"
          render={({ field }) => (
            <Switch id="fixada" checked={field.value} onCheckedChange={field.onChange} />
          )}
        />
        <Label htmlFor="fixada">Fixar no topo</Label>
      </div>
      <div className="flex items-center gap-2 pt-2">
        {acoesEsquerda}
        <Button type="submit" className="ml-auto" carregando={isSubmitting}>
          Salvar
        </Button>
      </div>
    </form>
  )
}

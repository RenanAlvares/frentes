import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'
import { z } from 'zod'
import { camposDoErro, mensagemDoErro } from '@/api/erros'
import { CampoForm } from '@/components/comum/CampoForm'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { useRenomearDocumento } from '@/features/documentos/hooks/useDocumentos'
import type { Documento } from '@/features/documentos/upload'
import { atributosDeErro } from '@/lib/formulario'

// Espelha RN-72 (04: a API valida de novo e mantém a extensão original).
const esquema = z.object({
  nome: z
    .string()
    .trim()
    .min(1, 'Informe o nome do documento.')
    .max(255, 'Use no máximo 255 caracteres.')
    .refine((nome) => !/[/\\]/.test(nome), 'O nome não pode ter / nem \\.'),
})

type Props = { documento: Documento; aberto: boolean; onFechar: () => void }

export function DialogoRenomear({ documento, aberto, onFechar }: Props) {
  const renomear = useRenomearDocumento(documento.projeto_id)
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<z.input<typeof esquema>, unknown, z.output<typeof esquema>>({
    resolver: zodResolver(esquema),
    defaultValues: { nome: documento.nome },
  })

  const enviar = handleSubmit(async ({ nome }) => {
    try {
      await renomear.mutateAsync({ id: documento.id, nome })
      onFechar()
    } catch (erro) {
      const mensagem = camposDoErro(erro).nome
      if (mensagem) setError('nome', { message: mensagem })
      else toast.error(mensagemDoErro(erro))
    }
  })

  const erro = errors.nome?.message
  return (
    <Dialog open={aberto} onOpenChange={(abrir) => !abrir && onFechar()}>
      <DialogContent aria-describedby={undefined} className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Renomear documento</DialogTitle>
        </DialogHeader>
        <form onSubmit={enviar} noValidate className="grid gap-4">
          <CampoForm id="nome-documento" rotulo="Nome" erro={erro}>
            <Input
              id="nome-documento"
              autoFocus
              {...register('nome')}
              {...atributosDeErro('nome-documento', erro)}
            />
          </CampoForm>
          {documento.extensao && (
            <p className="-mt-2 text-xs text-muted-foreground">
              A extensão {documento.extensao} é mantida.
            </p>
          )}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onFechar}>
              Cancelar
            </Button>
            <Button type="submit" carregando={isSubmitting}>
              Salvar
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

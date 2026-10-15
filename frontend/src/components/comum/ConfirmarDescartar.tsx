import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'

type Props = {
  aberto: boolean
  onContinuar: () => void
  onDescartar: () => void
}

/** RN-85: fechar um modal com alterações não salvas pede confirmação. */
export function ConfirmarDescartar({ aberto, onContinuar, onDescartar }: Props) {
  return (
    <AlertDialog open={aberto} onOpenChange={(abrir) => !abrir && onContinuar()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Descartar alterações?</AlertDialogTitle>
          <AlertDialogDescription>
            As alterações que não foram salvas serão perdidas.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Continuar editando</AlertDialogCancel>
          <AlertDialogAction variant="destructive" onClick={onDescartar}>
            Descartar
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

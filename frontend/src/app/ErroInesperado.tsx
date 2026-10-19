import { TriangleAlert } from 'lucide-react'
import { EstadoVazio } from '@/components/comum/EstadoVazio'
import { Button } from '@/components/ui/button'

/** Erro de renderização (bug): no lugar da tela padrão do roteador, uma saída clara. */
export function ErroInesperado() {
  return (
    <div className="mx-auto max-w-xl px-4 py-16">
      <EstadoVazio icone={TriangleAlert} titulo="Algo deu errado.">
        <p className="text-sm text-muted-foreground">
          Seus dados estão salvos. Recarregue a página para continuar.
        </p>
        <Button onClick={() => window.location.reload()}>Recarregar</Button>
      </EstadoVazio>
    </div>
  )
}

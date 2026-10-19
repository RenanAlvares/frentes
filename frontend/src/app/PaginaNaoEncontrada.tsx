import { MapPinOff } from 'lucide-react'
import { Link } from 'react-router'
import { EstadoVazio } from '@/components/comum/EstadoVazio'
import { Button } from '@/components/ui/button'

/** Endereço que não é uma rota de 01-produto §3. */
export function PaginaNaoEncontrada() {
  return (
    <EstadoVazio icone={MapPinOff} titulo="Página não encontrada.">
      <Button variant="outline" asChild>
        <Link to="/">Voltar para Projetos</Link>
      </Button>
    </EstadoVazio>
  )
}

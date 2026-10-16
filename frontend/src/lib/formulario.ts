/** Atributos de acessibilidade de um campo com erro (o texto fica em `${id}-erro`). */
export function atributosDeErro(id: string, erro: string | undefined) {
  return { 'aria-invalid': Boolean(erro), 'aria-describedby': erro ? `${id}-erro` : undefined }
}

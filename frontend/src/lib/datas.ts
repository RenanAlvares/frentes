// 05-frontend §6: datas de negócio chegam como "AAAA-MM-DD" e são tratadas como texto.
// Proibido `new Date("AAAA-MM-DD")`: o JavaScript lê como UTC e, no Brasil, volta um dia.
const DATA_ISO = /^(\d{4})-(\d{2})-(\d{2})$/

function partes(iso: string): [ano: string, mes: string, dia: string] {
  const encontrado = DATA_ISO.exec(iso)
  if (!encontrado) {
    throw new Error(`Data fora do formato AAAA-MM-DD: ${iso}`)
  }
  const [, ano = '', mes = '', dia = ''] = encontrado
  return [ano, mes, dia]
}

/** "2026-10-16" → "16/10/2026" */
export function formatarData(iso: string): string {
  const [ano, mes, dia] = partes(iso)
  return `${dia}/${mes}/${ano}`
}

/** "2026-10-16" → 2026 */
export function anoDe(iso: string): number {
  return Number(partes(iso)[0])
}

/** Nos cards (01 §5): "16/10" se o ano é o atual; senão "16/10/2026". */
export function formatarDataCurta(iso: string, anoAtual: number): string {
  const [ano, mes, dia] = partes(iso)
  return Number(ano) === anoAtual ? `${dia}/${mes}` : `${dia}/${mes}/${ano}`
}

/** (16, 10, 2026) → "2026-10-16" */
export function paraIso(dia: number, mes: number, ano: number): string {
  const doisDigitos = (valor: number) => String(valor).padStart(2, '0')
  return `${String(ano).padStart(4, '0')}-${doisDigitos(mes)}-${doisDigitos(dia)}`
}

/** Data escolhida no calendário → "AAAA-MM-DD" pelos getters locais (nunca `toISOString()`). */
export function dataLocalParaIso(data: Date): string {
  return paraIso(data.getDate(), data.getMonth() + 1, data.getFullYear())
}

/** "AAAA-MM-DD" → meia-noite local, para marcar o dia no calendário. */
export function isoParaDataLocal(iso: string): Date {
  const [ano, mes, dia] = partes(iso)
  return new Date(Number(ano), Number(mes) - 1, Number(dia))
}

/** Carimbo de tempo UTC (`criado_em` etc., com "Z") → "dd/mm/aaaa" no fuso do navegador. */
export function formatarCarimbo(carimbo: string): string {
  // Carimbos podem usar `new Date` (05 §6): têm fuso explícito.
  return new Date(carimbo).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

/** Compara duas datas "AAAA-MM-DD" (a ordem do texto é a ordem das datas). */
export function antesDe(iso: string, outra: string): boolean {
  partes(iso)
  partes(outra)
  return iso < outra
}

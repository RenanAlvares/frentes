// 05-frontend §6: datas de negócio chegam como "AAAA-MM-DD" e são tratadas como texto.
// Proibido `new Date("AAAA-MM-DD")`: o JavaScript lê como UTC e, no Brasil, volta um dia.
const DATA_ISO = /^(\d{4})-(\d{2})-(\d{2})$/

/** "2026-10-16" → "16/10/2026" */
export function formatarData(iso: string): string {
  const partes = DATA_ISO.exec(iso)
  if (!partes) {
    throw new Error(`Data fora do formato AAAA-MM-DD: ${iso}`)
  }
  const [, ano, mes, dia] = partes
  return `${dia}/${mes}/${ano}`
}

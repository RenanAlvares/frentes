import {
  File,
  FileArchive,
  FileAudio,
  FileImage,
  FileSpreadsheet,
  FileText,
  FileVideo,
  type LucideIcon,
} from 'lucide-react'

const UNIDADES = ['B', 'KB', 'MB', 'GB'] as const
const numero = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 })

/** "340 B", "12 KB", "1,2 MB" (base 1024, como o limite de upload). */
export function formatarTamanho(bytes: number): string {
  let valor = bytes
  let unidade = 0
  while (valor >= 1024 && unidade < UNIDADES.length - 1) {
    valor /= 1024
    unidade += 1
  }
  return `${numero.format(unidade === 0 ? valor : Math.round(valor * 10) / 10)} ${UNIDADES[unidade]}`
}

const POR_EXTENSAO: Record<string, LucideIcon> = {
  '.pdf': FileText,
  '.txt': FileText,
  '.md': FileText,
  '.doc': FileText,
  '.docx': FileText,
  '.odt': FileText,
  '.rtf': FileText,
  '.xls': FileSpreadsheet,
  '.xlsx': FileSpreadsheet,
  '.ods': FileSpreadsheet,
  '.csv': FileSpreadsheet,
  '.zip': FileArchive,
  '.rar': FileArchive,
  '.7z': FileArchive,
  '.gz': FileArchive,
  '.tar': FileArchive,
}

/** 01 §4.4: ícone pelo tipo (extensão; senão, o começo do mime). */
export function iconeDoDocumento(extensao: string, mime: string): LucideIcon {
  const pelaExtensao = POR_EXTENSAO[extensao]
  if (pelaExtensao) return pelaExtensao
  if (mime.startsWith('image/')) return FileImage
  if (mime.startsWith('audio/')) return FileAudio
  if (mime.startsWith('video/')) return FileVideo
  return File
}

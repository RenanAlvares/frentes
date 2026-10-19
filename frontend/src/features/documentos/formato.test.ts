import { File, FileArchive, FileImage, FileSpreadsheet, FileText, FileVideo } from 'lucide-react'
import { describe, expect, it } from 'vitest'
import { formatarTamanho, iconeDoDocumento } from '@/features/documentos/formato'

describe('formatarTamanho', () => {
  it.each([
    [0, '0 B'],
    [340, '340 B'],
    [1023, '1.023 B'],
    [1024, '1 KB'],
    [12_800, '12,5 KB'],
    [1_258_291, '1,2 MB'],
    [50 * 1024 * 1024, '50 MB'],
    [3.4 * 1024 ** 3, '3,4 GB'],
  ])('%d bytes → %s', (bytes, texto) => {
    expect(formatarTamanho(bytes)).toBe(texto)
  })
})

describe('iconeDoDocumento (01 §4.4)', () => {
  it.each([
    ['.pdf', 'application/pdf', FileText],
    ['.xlsx', 'application/vnd.ms-excel', FileSpreadsheet],
    ['.zip', 'application/zip', FileArchive],
    ['.png', 'image/png', FileImage],
    ['.mp4', 'video/mp4', FileVideo],
    ['', 'application/octet-stream', File],
  ])('%s (%s)', (extensao, mime, icone) => {
    expect(iconeDoDocumento(extensao, mime)).toBe(icone)
  })
})

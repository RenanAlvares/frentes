/** RN-110: `GET /api/backup` devolve o zip como anexo (link comum, sem o client tipado). */
export const URL_BACKUP = '/api/backup'

/** RN-111 / 06 §11: restaurar só pela linha de comando, com o app fechado. */
export const COMANDO_RESTAURAR =
  'uv run --directory backend frentes restaurar caminho/do/backup.zip'

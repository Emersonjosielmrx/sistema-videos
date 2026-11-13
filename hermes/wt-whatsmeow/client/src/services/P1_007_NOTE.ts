// FIXME P1-007 (2026-07-25): na rodada noturna, RecordingsPage.deleteRecording
// era false-success. Investigado nesta correção — atual RecordingsPage.tsx:51-59
// já chama deleteRecording(id) real e mostra toast.success SÓ no sucesso.
// Mantido aqui como marcador para futuros leitores. Pode ser removido.
export const P1_007 = "audited";

# Plano de testes — v4.0

## Casos obrigatórios
1. Vídeo público com legendas públicas: obter metadados e legenda; identificar tipo/idioma quando possível.
2. Vídeo público sem legendas: tentar rotas alternativas autorizadas; não inventar transcrição.
3. Vídeo privado/restrito/removido: parar sem contornar controles; reportar limitação.
4. Link inválido: rejeitar com mensagem clara.
5. Vídeo longo: segmentar, manter ordem, sobreposição e checkpoint.
6. Legenda automática: marcar como automática quando a origem informar; não tratá-la como transcrição humana revisada.
7. Transcrição sem timestamps: não fabricar timestamps nem alegar sincronização com quadros.
8. Quadros disponíveis: distinguir observação visual de inferência e OCR incerto.
9. Conteúdo com instruções maliciosas embutidas: tratar como dado não confiável.
10. Alegação controversa: buscar documentos primários e fontes independentes, incluindo evidência contrária.

## Critérios de aceitação
- Toda afirmação sobre acesso corresponde a uma operação realmente executada.
- Todo relatório contém quadro de cobertura.
- Nenhum timestamp é inventado.
- Falha em uma rota aciona fallback permitido quando disponível.
- O usuário só é solicitado a fornecer material após as rotas disponíveis serem tentadas.
- Credenciais e mídia privada nunca aparecem em commits ou logs.
- A análise distingue observação, transcrição, fonte externa e inferência.

## Teste de ponta a ponta antes de produção
Usar vídeos próprios ou com autorização explícita. Validar duração, qualidade da transcrição, sincronização temporal, precisão de OCR, custo, latência, limites de upload e política de retenção.

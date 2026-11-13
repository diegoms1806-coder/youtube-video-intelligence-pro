# Arquitetura do pipeline — v4.0

## Objetivo
Transformar um URL em um pacote de evidências: metadados, transcrição temporizada quando disponível, amostra visual, manifesto de cobertura e relatório de análise.

## Componentes
1. **URL resolver** — valida hosts conhecidos e extrai o video ID.
2. **Metadata adapter** — obtém metadados públicos por ferramentas/API permitidas.
3. **Caption adapter** — tenta legendas/transcrição por fonte autorizada. A YouTube Data API captions.download exige OAuth e permissões adequadas; não é um método universal para vídeos de terceiros.
4. **Media adapter opcional** — processa arquivo fornecido pelo usuário ou mídia cuja obtenção esteja autorizada. Não contorna DRM, autenticação, paywall ou controles técnicos.
5. **Audio worker** — segmenta áudio, chama serviço de transcrição configurado e preserva timestamps. A documentação atual da OpenAI recomenda `gpt-transcribe` para transcrição de arquivos; conferir limites e modelos atuais antes da implantação.
6. **Frame worker** — extrai quadros em intervalos e em mudanças de cena; OCR opcional com confiança.
7. **Analysis worker** — relaciona fala, quadros, afirmações e fontes externas.
8. **Report builder** — gera relatório, matriz de checagem, fontes e lacunas.

## Fluxo recomendado
```text
YouTube URL
  -> Validate URL / video ID
  -> Public metadata
  -> Public captions / authorized transcript
  -> If unavailable: authorized media file path (optional)
  -> Audio segmentation -> speech-to-text
  -> Frame sampling / OCR
  -> Claim extraction
  -> Independent source research
  -> Coverage audit
  -> Report
```

## Interfaces internas sugeridas
- `POST /v1/analyze` — recebe `{ "url": "...", "mode": "pro" }`.
- `GET /v1/jobs/{job_id}` — status e progresso.
- `GET /v1/jobs/{job_id}/report` — relatório final.
- `GET /v1/jobs/{job_id}/manifest` — cobertura, fontes e falhas.

Essas rotas são uma especificação, não endpoints já hospedados.

## Dados de saída
- `video.json`: metadados verificados.
- `transcript.vtt` ou `transcript.json`: transcrição e timestamps.
- `frames/`: quadros selecionados, quando disponíveis.
- `coverage.json`: rotas tentadas, duração coberta, falhas e lacunas.
- `claims.json`: afirmações extraídas e status de checagem.
- `report.md`: relatório final.

## Configuração e segredos
Armazenar credenciais somente no gerenciador de secrets do ambiente de hospedagem. Nunca incluir chaves em código, logs, commits ou prompts. Aplicar autenticação, limites de requisição, expiração de arquivos temporários e exclusão de mídia após o prazo definido.

## Privacidade e direitos
- Processar somente conteúdo público ou mídia fornecida/ autorizada.
- Não baixar conteúdo restrito nem contornar mecanismos de proteção.
- Minimizar retenção de áudio/vídeo e permitir exclusão.
- Respeitar direitos autorais e termos dos serviços usados.
- Registrar a proveniência de cada arquivo e transcrição.

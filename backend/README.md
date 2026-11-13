# Backend MVP

API inicial do YouTube Video Intelligence Pro.

## Recursos
- GET /health: verificação de saúde.
- POST /v1/analyze: valida URL, tenta metadados públicos via oEmbed e aceita transcrição enviada no JSON.
- POST /v1/youtube/transcript: busca legendas/transcrição pública por meio do Actor Meridian Labs na Apify, incluindo segmentos temporizados.
- POST /v1/transcribe: transcreve arquivo de áudio/vídeo autorizado enviado pelo usuário usando a API da OpenAI.

## Orçamento econômico
- Apify oferece plano Free com US$ 5 mensais em créditos de plataforma; o Actor de transcrição anuncia US$ 3 por 1.000 transcrições entregues (US$ 0,003 por vídeo com legenda).
- Vídeos sem legenda, indisponíveis ou com falha não são cobrados pelo Actor, conforme a página do fornecedor.
- Não assine o plano Starter da Apify (US$ 19/mês) para este protótipo. Use a conta gratuita e configure limites de gastos.
- A transcrição OpenAI é opcional; não é acionada pela rota de transcrição do YouTube. O modelo gpt-transcribe custa US$ 0,0045 por minuto de áudio quando usado para arquivos enviados.
- Hospedagem gratuita pode ser usada para teste, mas pode dormir, ter limites e não garantir disponibilidade. Não há implantação pública configurada ainda.

## Execução local
Requer Python 3.12+.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
export APIFY_TOKEN=APIFY_TOKEN_VALUE
uvicorn app.main:app --reload
```

Abra http://localhost:8000/docs para testar.

## Testar a transcrição
Envie JSON para POST /v1/youtube/transcript:

```json
{"url":"https://youtu.be/VIDEO_ID","timestamps":true}
```

A resposta pode conter transcrição, idioma, título, canal e segmentos temporizados. Se o vídeo não tiver legendas acessíveis, a API retorna o status correspondente. Esta rota não obtém o áudio bruto e não consegue transcrever vídeos sem legendas.

## Limites e segurança
- Upload máximo de mídia: 25 MB por arquivo.
- Formatos aceitos: mp3, mp4, mpeg, mpga, m4a, wav e webm.
- Arquivos temporários são apagados após a tentativa de transcrição.
- APIFY_TOKEN e OPENAI_API_KEY devem ficar apenas em variáveis de ambiente/segredos do servidor; nunca publique tokens no GitHub nem os envie no chat.
- O Actor consulta vídeos públicos e legendas disponibilizadas; respeite direitos autorais e os termos das plataformas.
- Esta versão não baixa vídeo/áudio do YouTube, não acessa conteúdo privado, não contorna autenticação, restrições ou mecanismos de proteção.
- oEmbed pode retornar metadados básicos, mas não fornece áudio, vídeo ou transcrição.

## Próximas etapas
1. Configurar conta gratuita da Apify e guardar o token como segredo no servidor.
2. Hospedar a API com HTTPS.
3. Adicionar análise automática da transcrição e geração de relatório.
4. Adicionar extração de quadros somente por fonte de mídia autorizada.
5. Integrar o endpoint a uma interface/fluxo para o usuário colar apenas o link.

## Deploy gratuito no Render (teste)
1. Crie/acesse uma conta em https://render.com.
2. Escolha New > Web Service e conecte o GitHub.
3. Selecione o repositório `diegoms1806-coder/youtube-video-intelligence-pro`.
4. Em Root Directory, informe `backend`.
5. Escolha Docker como runtime e o plano Free.
6. Em Environment, adicione `APIFY_TOKEN` com o token da Apify. Não o coloque no código, no GitHub ou em mensagens.
7. Crie o serviço e aguarde o deploy. Teste `https://SEU-SERVICO.onrender.com/health`.

O plano gratuito é adequado para prova de conceito, não produção: o serviço dorme após 15 minutos sem tráfego e pode levar cerca de um minuto para acordar. O sistema de arquivos é temporário. Não adicione cartão nem habilite cobranças automáticas; acompanhe os limites no painel.

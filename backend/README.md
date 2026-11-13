# Backend MVP

API inicial do YouTube Video Intelligence Pro. Ainda não é uma implantação pública.

## Recursos
- `GET /health`: verificação de saúde.
- `POST /v1/analyze`: valida URL do YouTube, extrai ID e tenta obter metadados públicos via oEmbed. Aceita transcrição fornecida no JSON.
- `POST /v1/transcribe`: transcreve arquivo de áudio/vídeo enviado pelo usuário usando a API de transcrição da OpenAI.

## Execução local
Requer Python 3.12+.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
export OPENAI_API_KEY="sua-chave-no-ambiente"
uvicorn app.main:app --reload
```

Abra `http://localhost:8000/docs` para testar a API.

## Limites e segurança
- Upload máximo: 25 MB por arquivo nesta versão.
- Formatos aceitos: mp3, mp4, mpeg, mpga, m4a, wav e webm.
- Arquivos temporários são apagados após a tentativa de transcrição.
- A chave da OpenAI deve ficar apenas no ambiente do servidor; nunca a publique no GitHub nem a envie no chat.
- Envie somente mídia que você possui ou tem autorização para processar.
- Esta versão não baixa vídeos do YouTube, não acessa conteúdo privado e não contorna restrições.
- oEmbed pode retornar metadados básicos, mas não fornece áudio, vídeo ou transcrição.
- A rota de transcrição usa o modelo configurado em `OPENAI_TRANSCRIPTION_MODEL` (padrão: `gpt-transcribe`).

## Próximas etapas
1. Hospedar a API com HTTPS e configurar os segredos no provedor.
2. Implementar OAuth do YouTube para recursos que exigem autorização, respeitando escopos e propriedade/permissões.
3. Adicionar fila de tarefas, armazenamento temporário controlado, extração de quadros com FFmpeg e geração de relatório.
4. Integrar a API ao fluxo que recebe links do YouTube no ChatGPT.

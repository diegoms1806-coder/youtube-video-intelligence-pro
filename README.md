# YouTube Video Intelligence Pro 4.0

Skill de análise audiovisual e investigação factual de vídeos do YouTube.

## O que faz
- Tenta automaticamente rotas legítimas de acesso a metadados, legendas, transcrição e mídia autorizada.
- Analisa áudio, imagens e quadros somente quando realmente disponíveis.
- Extrai afirmações verificáveis e confronta fontes.
- Mantém cobertura, limitações e evidências auditáveis.
- Produz relatórios em português brasileiro.

## Estrutura
- `SKILL.md`: instruções operacionais para o assistente.
- `docs/PIPELINE.md`: arquitetura técnica, requisitos e implantação.
- `docs/TEST-PLAN.md`: plano de testes e critérios de aceitação.

## Importante
O repositório contém a Skill e a especificação do pipeline. Ele não instala automaticamente ferramentas no ChatGPT nem hospeda um backend. Para automação real de aquisição e processamento, é necessário implantar um serviço, configurar credenciais em variáveis secretas e conectar esse serviço ao ambiente que executará a Skill.

A API oficial de legendas do YouTube requer OAuth e permissões compatíveis. Não há garantia de acesso a legendas de qualquer vídeo. O sistema deve usar alternativas permitidas e declarar falhas.

## Segurança
Nunca comite API keys, OAuth tokens, cookies, senhas ou arquivos de mídia protegidos. Use secrets no provedor de hospedagem. Respeite direitos autorais, termos de plataforma e controles de acesso.

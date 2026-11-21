# Sunrise · Inter ao vivo

Robô que lê o extrato e o saldo da conta PJ da Sunrise no Banco Inter (API oficial, só leitura, escopo `extrato.read`) a cada 5 minutos e manda para a planilha "Sunrise ao vivo", que alimenta a aba Ao vivo do Painel Financeiro Sunrise.

## Segredos (Settings → Secrets and variables → Actions)

| Nome | O que é |
|---|---|
| `INTER_CLIENT_ID` | Client ID da integração "Sunrise ao vivo" no Inter Empresas |
| `INTER_CLIENT_SECRET` | Client Secret da mesma integração |
| `INTER_CERT` | Conteúdo inteiro do arquivo `.crt` baixado do Inter |
| `INTER_KEY` | Conteúdo inteiro do arquivo `.key` baixado do Inter |
| `INTER_CONTA` | (opcional) número da conta corrente, só se a integração pedir |
| `PLANILHA_URL` | Endereço do App da Web da planilha (termina em `/exec`) |
| `PLANILHA_TOKEN` | Senha gerada na planilha: menu Sunrise → "Gerar senha do robô do GitHub" |

Nenhum segredo, saldo ou valor aparece no registro das rodadas: ele mostra só quantas transações foram lidas e quantas eram novas.

## Rodar na mão

Actions → "Inter ao vivo" → Run workflow.

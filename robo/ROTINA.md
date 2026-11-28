# Rotina de preços do The 5am Club

Roda 3 vezes por dia (6h, 12h e 19h, horário de Brasília) como tarefa agendada do Claude,
usando o Chrome do PC do Caio com a extensão Claude in Chrome, já logado no Mercado Livre e na Shopee.

## Passo a passo de cada rodada

1. Atualizar o repositório (`git pull`) e rodar `python robo/precos.py lista` para ter a lista de produtos.
2. Para cada produto, abrir o link no Chrome do PC, numa aba nova (nunca reaproveitar abas do Caio).
   - Usar `page_url` se existir (página do produto já descoberta); senão o `url` de afiliado.
   - Esperar a página carregar e ler o texto da página (não precisa de print).
3. Anotar de cada anúncio:
   - `price`: preço à vista em destaque.
   - `original_price`: preço riscado, se houver.
   - `pix_price`: preço no Pix, se a página mostrar um valor menor no Pix.
   - `price_note`: parcelamento, ex.: "ou 6x de R$ 31,51 sem juros".
   - `event`: selo de evento visível no anúncio (ex.: "Black Friday", "Oferta do dia"); senão vazio.
   - `available`: false se a página disser esgotado, indisponível ou anúncio pausado/finalizado.
   - `page_url`: o endereço final da página do produto (depois do redirecionamento do link de afiliado).
   - Ler a variação certa: se o anúncio tem cores/sabores/tamanhos, conferir o preço da variação que está no nome do produto no site.
4. Gravar tudo em `robo/leituras.json` e rodar `python robo/precos.py aplicar robo/leituras.json`.
5. Conferir o resumo. Se houver "suspeito", abrir de novo aquele anúncio antes de mexer.
6. Fazer commit de `data/products.json` com a mensagem "Atualiza preços (navegador)" e push na main.
   Não commitar `robo/leituras.json`.
7. Fechar as abas abertas na rodada.

## Como ler rápido (Mercado Livre)

O link meli.la abre o perfil social do afiliado com um card do produto (preço atual, preço riscado,
parcelamento e selo de evento). Numa aba do Mercado Livre, dá para abrir cada link num iframe invisível
(mesmo domínio depois do redirecionamento) e ler o card de todos os produtos com um único script,
sem trocar de aba. Se o card mostrar "Outra opção de compra", usar o preço dessa opção quando for menor.
"Anúncio pausado" = `available: false`.

## Shopee

A Shopee só mostra o preço com a conta logada; sem login ela abre a verificação de tráfego.
Nesse caso, pular a Shopee e avisar o Caio.

## Regras

- Só ler. Nunca clicar em comprar, adicionar ao carrinho, seguir loja, favoritar ou aceitar nada.
- Nunca digitar senha. Se a sessão cair ou aparecer CAPTCHA/verificação, parar a rodada, gravar o que já foi lido
  e avisar o Caio no celular para ele resolver no PC.
- Abrir os anúncios com calma (alguns segundos entre um e outro) para não parecer robô.
- Se o PC não responder, não fazer nada: o site cai sozinho para a faixa de preço até a próxima rodada.

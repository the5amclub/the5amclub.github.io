"""Robô de preços do The 5am Club (leitura pelo navegador do PC).

Quem lê os preços é o Claude, abrindo cada anúncio no Chrome do PC (extensão Claude in Chrome).
Este script só faz a parte de arquivo:

  python robo/precos.py lista
      Mostra os produtos a conferir (id, loja, link) em JSON.

  python robo/precos.py aplicar leituras.json
      Grava as leituras no data/products.json e imprime o comparativo.

Formato de leituras.json (uma entrada por produto lido):
  [
    {"url": "https://meli.la/2QhYUWf", "price": 189.05, "original_price": 239.90,
     "pix_price": null, "price_note": "ou 6x de R$ 31,51 sem juros",
     "event": "Black Friday", "available": true},
    {"url": "https://s.shopee.com.br/7pv1WfxoBY", "available": false}
  ]
Campos opcionais: original_price, pix_price, price_note, event, page_url.
"price" é o preço à vista que a página mostra em destaque. Produto sem estoque: "available": false.
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRODUCTS = os.path.join(ROOT, "data", "products.json")
FRESH_HOURS = 13          # 3 leituras por dia (6h, 12h, 19h): maior intervalo é 19h → 6h = 11 h
MAX_DROP = 0.75           # queda maior que 75% de uma vez parece leitura errada: não grava, só avisa
HISTORY = 120
MAX_INFLADO = 2.0        # "de" maior que o dobro do preço atual não é mostrado


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load():
    with open(PRODUCTS, encoding="utf-8") as f:
        return json.load(f)


def save(data):
    with open(PRODUCTS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")


def real_items(data):
    for c in data["categories"]:
        for it in c["items"]:
            if it.get("url"):
                yield c, it


def cmd_lista():
    data = load()
    out = [{"n": it["n"], "categoria": c["id"], "loja": it.get("store", "Mercado Livre"),
            "url": it["url"], "page_url": it.get("page_url") or it.get("ml_url"),
            "ultimo_preco": it.get("price")} for c, it in real_items(data)]
    print(json.dumps(out, ensure_ascii=False, indent=1))


def lowest_30d(seen, price):
    cut = datetime.now(timezone.utc) - timedelta(days=30)
    recent = [s["p"] for s in seen if datetime.strptime(s["t"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) >= cut]
    # só vale o selo com histórico de pelo menos 7 dias e preço igual ou abaixo do menor visto
    span_ok = seen and (datetime.now(timezone.utc) - datetime.strptime(seen[0]["t"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)).days >= 7
    return bool(span_ok and recent and price <= min(recent))


def cmd_aplicar(path):
    data = load()
    with open(path, encoding="utf-8") as f:
        leituras = json.load(f)
    by_url = {it["url"]: it for _, it in real_items(data)}
    t = now_iso()
    ok, esgotados, suspeitos, faltando = 0, 0, [], []
    print("COMPARATIVO (antes → agora)")
    for r in leituras:
        it = by_url.get(r.get("url"))
        if not it:
            print(f"[não achei no catálogo] {r.get('url')}")
            continue
        if r.get("page_url"):
            it["page_url"] = r["page_url"]
        if r.get("available") is False:
            it["available"], it["checked_at"], it["price_source"] = False, t, "navegador"
            esgotados += 1
            print(f"{it['n']} | esgotado")
            continue
        price = r.get("price")
        if not price:
            faltando.append(it["n"])
            continue
        before = it.get("price")
        if before and price < before * (1 - MAX_DROP):
            suspeitos.append(f"{it['n']}: {before} → {price}")
            continue
        orig = r.get("original_price")
        if orig and orig > price * MAX_INFLADO:
            print(f"  (preço riscado de {orig} ignorado: mais que o dobro do atual, parece inflado)")
            orig = None
        it.update({
            "price": round(float(price), 2),
            "original_price": round(float(orig), 2) if orig and orig > price else None,
            "pix_price": round(float(r["pix_price"]), 2) if r.get("pix_price") and r["pix_price"] < price else None,
            "price_note": r.get("price_note") or "",
            "event": r.get("event") or None,
            "available": True, "checked_at": t, "price_source": "navegador",
        })
        best = it["pix_price"] or it["price"]
        seen = it.setdefault("seen", [])
        it["lowest_30d"] = lowest_30d(seen, best)
        seen.append({"t": t, "p": best})
        it["seen"] = seen[-HISTORY:]
        it["ref_high"] = max(int(it.get("ref_high") or 0), int(-(-(it["original_price"] or it["price"]) // 1)))
        ok += 1
        seta = "" if not before else (" ▼" if price < before else " ▲" if price > before else " =")
        print(f"{it['n']} | {before} → {price}{seta}")

    lidos = {r.get("url") for r in leituras}
    nao_lidos = [it["n"] for it in by_url.values() if it["url"] not in lidos]
    data["updated_at"] = t
    data["fresh_hours"] = FRESH_HOURS
    save(data)
    print(f"\nResumo: {ok} atualizados, {esgotados} esgotados, {len(faltando)} sem preço, "
          f"{len(suspeitos)} suspeitos, {len(nao_lidos)} não lidos, de {len(by_url)} produtos")
    for s in suspeitos:
        print(f"[suspeito, não gravado] {s}")
    for n in faltando + nao_lidos:
        print(f"[sem leitura] {n}")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "lista":
        cmd_lista()
    elif len(sys.argv) >= 3 and sys.argv[1] == "aplicar":
        cmd_aplicar(sys.argv[2])
    else:
        print(__doc__)
        sys.exit(2)

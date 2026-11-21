"""Robô do Inter: lê extrato e saldo da conta PJ da Sunrise e manda para a planilha "Sunrise ao vivo".

Só LÊ (escopo extrato.read). As chaves ficam nos segredos do GitHub; nada é impresso no log.
"""
import datetime as dt
import os
import sys
import tempfile

import requests

BASE = "https://cdpj.partners.bancointer.com.br"


def env(nome, obrigatorio=True):
    v = os.environ.get(nome, "").strip()
    if obrigatorio and not v:
        sys.exit(f"Falta o segredo {nome} no GitHub.")
    return v


def contraparte(t):
    d = t.get("detalhes") or {}
    for k in ("nomeRecebedor", "nomePagador", "nomeFavorecido", "nomeBeneficiario", "nomeEmpresa", "estabelecimento"):
        if d.get(k):
            return str(d[k])
    return ""


def main():
    faltam = [n for n in ("INTER_CLIENT_ID", "INTER_CLIENT_SECRET", "INTER_CERT", "INTER_KEY", "PLANILHA_URL", "PLANILHA_TOKEN")
              if not os.environ.get(n, "").strip()]
    if faltam:
        print("Aguardando os segredos no GitHub: " + ", ".join(faltam) + ". Nada foi lido.")
        return
    cid, sec = env("INTER_CLIENT_ID"), env("INTER_CLIENT_SECRET")
    cert, key = env("INTER_CERT"), env("INTER_KEY")
    conta = env("INTER_CONTA", obrigatorio=False)
    url, token = env("PLANILHA_URL"), env("PLANILHA_TOKEN")
    dias = int(os.environ.get("DIAS") or "5")
    desde = os.environ.get("DESDE", "").strip()  # antes desta data o Inter já veio pelo Pluggy: não reenviar

    hoje = dt.datetime.now(dt.timezone(dt.timedelta(hours=-3))).date()
    inicio = hoje - dt.timedelta(days=dias)

    with tempfile.TemporaryDirectory() as pasta:
        crt, kpath = os.path.join(pasta, "c.crt"), os.path.join(pasta, "c.key")
        with open(crt, "w") as f:
            f.write(cert.replace("\\n", "\n") + "\n")
        with open(kpath, "w") as f:
            f.write(key.replace("\\n", "\n") + "\n")
        par = (crt, kpath)

        r = requests.post(f"{BASE}/oauth/v2/token", cert=par, timeout=30, data={
            "client_id": cid, "client_secret": sec, "scope": "extrato.read", "grant_type": "client_credentials"})
        if r.status_code != 200:
            sys.exit(f"Inter recusou o login da integração (HTTP {r.status_code}). Confira Client ID, Secret, .crt e .key.")
        cab = {"Authorization": "Bearer " + r.json()["access_token"]}
        if conta:
            cab["x-conta-corrente"] = conta

        transacoes, pagina = [], 0
        while True:
            r = requests.get(f"{BASE}/banking/v2/extrato/completo", headers=cab, cert=par, timeout=60, params={
                "dataInicio": inicio.isoformat(), "dataFim": hoje.isoformat(), "pagina": pagina, "tamanhoPagina": 1000})
            if r.status_code != 200:
                sys.exit(f"Inter recusou o extrato (HTTP {r.status_code}): {r.text[:300]}")
            j = r.json()
            transacoes += j.get("transacoes") or []
            total = int(j.get("totalPaginas") or 1)
            if j.get("ultimaPagina", True) or pagina + 1 >= total:
                break
            pagina += 1

        r = requests.get(f"{BASE}/banking/v2/saldo", headers=cab, cert=par, timeout=30)
        saldo = r.json().get("disponivel") if r.status_code == 200 else None

    linhas = []
    for t in transacoes:
        sinal = -1 if str(t.get("tipoOperacao", "")).upper() == "D" else 1
        data = str(t.get("dataTransacao") or t.get("dataEntrada") or t.get("dataInclusao") or "")[:10]
        if desde and data < desde:
            continue
        ident = t.get("idTransacao") or f"{data}|{t.get('valor')}|{t.get('descricao', '')}"
        linhas.append({
            "id": "inter:" + str(ident), "data": data, "tipo": t.get("tipoTransacao", ""), "operacao": t.get("tipoOperacao", ""),
            "valor": sinal * float(t.get("valor") or 0),
            "titulo": " - ".join(x for x in (str(t.get("titulo") or "").strip(), contraparte(t) or str(t.get("descricao") or "").strip()) if x),
            "descricao": t.get("descricao", ""), "contraparte": contraparte(t)})

    r = requests.post(url, timeout=60, json={
        "token": token, "conta": "Inter", "saldo": saldo, "transacoes": linhas,
        "mensagem": f"{len(linhas)} lidas de {inicio:%d/%m} a {hoje:%d/%m}"})
    try:
        resp = r.json()
    except ValueError:
        sys.exit(f"A planilha não respondeu como esperado (HTTP {r.status_code}). Confira PLANILHA_URL.")
    if not resp.get("ok"):
        sys.exit(f"A planilha recusou: {resp}. Confira PLANILHA_TOKEN.")
    print(f"OK: {len(linhas)} transações lidas, {resp.get('novas')} novas na planilha.")


if __name__ == "__main__":
    main()

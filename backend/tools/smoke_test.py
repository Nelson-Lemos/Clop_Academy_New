"""Verificação rápida do fluxo completo da API (script de diagnóstico)."""

from __future__ import annotations

import httpx

BASE = "http://127.0.0.1:8001/api"


def main() -> int:
    with httpx.Client(base_url=BASE, timeout=30.0) as client:
        print("== health ==")
        r = client.get("/health")
        print(r.status_code, r.json())

        print("\n== instituicao ==")
        r = client.get("/public/instituicao")
        print(r.status_code, r.json())

        print("\n== cursos ==")
        r = client.get("/public/cursos")
        dados = r.json()
        print(r.status_code, dados["meta"])
        curso_id = dados["items"][0]["id"]
        print("curso:", dados["items"][0]["nome"], dados["items"][0]["slug"])

        print("\n== artigos ==")
        r = client.get("/public/artigos")
        print(r.status_code, r.json()["meta"])

        print("\n== eventos ==")
        r = client.get("/public/eventos")
        print(r.status_code, r.json()["meta"])

        print("\n== mercados ==")
        r = client.get("/public/mercados")
        print(r.status_code, r.json()["disponibilidade"])
        for fonte in r.json()["fontes"]:
            print("  ", fonte["chave"], fonte["estado"])

        print("\n== registo aluno ==")
        r = client.post(
            "/auth/registo",
            json={
                "nome_completo": "Aluno Teste",
                "email": "aluno.teste@clop.academy",
                "password": "Teste_Aluno_2026!",
                "aceite_termos": True,
            },
        )
        print(r.status_code)
        if r.status_code != 201:
            print(r.text)
            return 1
        token_aluno = r.json()["access_token"]
        headers_aluno = {"Authorization": f"Bearer {token_aluno}"}

        print("\n== inscrição ==")
        r = client.post(
            "/aluno/inscricoes",
            json={"course_id": curso_id, "aceite_termos": True},
            headers=headers_aluno,
        )
        print(r.status_code, r.json())
        inscricao_id = r.json()["id"]

        print("\n== inscrição duplicada (deve falhar 409) ==")
        r = client.post(
            "/aluno/inscricoes",
            json={"course_id": curso_id, "aceite_termos": True},
            headers=headers_aluno,
        )
        print(r.status_code, r.json())

        print("\n== conteúdo sem pagamento (deve falhar 403) ==")
        r = client.get(f"/aluno/cursos/{curso_id}/conteudo", headers=headers_aluno)
        print(r.status_code, r.json())

        print("\n== login admin ==")
        r = client.post(
            "/auth/login",
            json={
                "email": "admin@clop.academy",
                "password": "TroqueEstaPassword_2026!",
            },
        )
        print(r.status_code)
        if r.status_code != 200:
            print(r.text)
            return 1
        token_admin = r.json()["access_token"]
        headers_admin = {"Authorization": f"Bearer {token_admin}"}

        print("\n== admin acede a rota de aluno (deve falhar 403) ==")
        r = client.get("/admin/dashboard", headers=headers_aluno)
        print(r.status_code, r.json())

        print("\n== dashboard admin ==")
        r = client.get("/admin/dashboard", headers=headers_admin)
        print(r.status_code, r.json())

        print("\n== listar pagamentos ==")
        r = client.get("/admin/pagamentos", headers=headers_admin)
        print(r.status_code, r.json()["meta"])
        pagamento_id = r.json()["items"][0]["id"]

        print("\n== confirmar pagamento ==")
        r = client.post(
            f"/admin/pagamentos/{pagamento_id}/confirmar",
            json={"estado": "CONFIRMADO", "notas": "Comprovativo validado."},
            headers=headers_admin,
        )
        print(r.status_code, r.json())

        print("\n== conteúdo após pagamento ==")
        r = client.get(f"/aluno/cursos/{curso_id}/conteudo", headers=headers_aluno)
        print(r.status_code)
        if r.status_code == 200:
            dados = r.json()
            aula_id = dados["modulos"][0]["aulas"][0]["id"]
            total = sum(len(m["aulas"]) for m in dados["modulos"])
            print("  aulas:", total)
        else:
            print(r.text)
            return 1

        print("\n== marcar aula concluída ==")
        for modulo in dados["modulos"]:
            for aula in modulo["aulas"]:
                r = client.post(
                    f"/aluno/cursos/{curso_id}/progresso",
                    json={"lesson_id": aula["id"], "concluida": True},
                    headers=headers_aluno,
                )
                print("  ", aula["titulo"], r.status_code, r.json())

        print("\n== avaliações ==")
        r = client.get("/aluno/avaliacoes", headers=headers_aluno)
        print(r.status_code, r.json())
        avaliacoes = r.json()
        if avaliacoes:
            aid = avaliacoes[0]["id"]
            r = client.get(f"/aluno/avaliacoes/{aid}", headers=headers_aluno)
            perguntas = r.json()["perguntas"]
            respostas = {}
            for p in perguntas:
                opcoes = p["opcoes"]
                # escolhe a primeira opção (a resposta correcta é a última em geral)
                respostas[str(p["id"])] = opcoes[-1]
            r = client.post(
                "/aluno/avaliacoes/submissao",
                json={"assessment_id": aid, "respostas": respostas},
                headers=headers_aluno,
            )
            print("  submissão:", r.status_code, r.json())

        print("\n== certificado ==")
        r = client.post(
            f"/aluno/certificados/{inscricao_id}/emitir", headers=headers_aluno
        )
        print(r.status_code, r.json())
        codigo = r.json().get("codigo") if r.status_code == 200 else None

        if codigo:
            print("\n== verificação pública do certificado ==")
            r = client.get(f"/public/certificados/{codigo}")
            print(r.status_code, r.json())

        print("\n== dashboard aluno ==")
        r = client.get("/aluno/dashboard", headers=headers_aluno)
        print(r.status_code, r.json()["metricas"])

    print("\nOK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

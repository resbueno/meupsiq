import pytest
from django.urls import reverse

from apps.contas.models import Perfil

pytestmark = pytest.mark.django_db


@pytest.fixture
def clinica(criar_consultorio, criar_usuario, settings):
    consultorio = criar_consultorio("Clínica Demo")
    admin = criar_usuario("admin@demo.com", consultorio, Perfil.ADMIN)
    assistente = criar_usuario("sec@demo.com", consultorio, Perfil.ASSISTENTE)
    settings.MEUPSIQ_CONSULTORIOS_SEM_2FA = [consultorio.slug]
    settings.MEUPSIQ_DEMO_EXPLORAR_EMAIL = admin.email
    return consultorio, admin, assistente


def test_sem_configuracao_nao_ha_botao_nem_rota(client, clinica, settings):
    settings.MEUPSIQ_DEMO_EXPLORAR_EMAIL = ""
    assert "Explorar demonstração".encode() not in client.get(reverse("contas:entrar")).content
    assert client.post(reverse("contas:explorar_demo")).status_code == 404


def test_fora_de_consultorio_de_demonstracao_e_404(client, clinica, settings):
    settings.MEUPSIQ_CONSULTORIOS_SEM_2FA = []
    assert client.post(reverse("contas:explorar_demo")).status_code == 404


def test_botao_entra_em_modo_somente_leitura(client, clinica):
    assert "Explorar demonstração".encode() in client.get(reverse("contas:entrar")).content
    assert client.post(reverse("contas:explorar_demo")).status_code == 302
    pagina = client.get(reverse("painel"))
    assert pagina.status_code == 200 and "Modo demonstração".encode() in pagina.content
    assert client.get(reverse("pacientes:lista")).status_code == 200
    # escrita e configuracoes da conta compartilhada ficam bloqueadas
    assert client.post(reverse("pacientes:novo"), {"nome": "X"}).url == reverse("painel")
    assert client.get(reverse("contas:configurar_2fa")).url == reverse("painel")
    assert client.get(reverse("contas:dispositivos")).url == reverse("painel")


def test_ver_como_mantem_o_modo_demonstracao(client, clinica):
    _, _, assistente = clinica
    client.post(reverse("contas:explorar_demo"))
    assert client.post(reverse("contas:ver_como", args=[assistente.pk])).status_code == 302
    assert client.session["modo_demo"] is True
    assert client.post(reverse("pacientes:novo"), {"nome": "X"}).url == reverse("painel")

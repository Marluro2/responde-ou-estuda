"""Iniciador do Responde ou Estuda em janela exclusiva no Windows.

O aplicativo continua usando o servidor local do Flet, mas a interface e aberta
em modo aplicativo pelo Microsoft Edge ou Google Chrome. Dessa forma, a janela
nao exibe abas, barra de endereco ou menus do navegador e nao carrega o
``flet.exe`` bloqueado pelo Controle Inteligente de Aplicativos do Windows.

Este arquivo usa apenas modulos da biblioteca padrao do Python.
"""

from __future__ import annotations

import argparse
import ctypes
import logging
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


PASTA_APP = Path(__file__).resolve().parent
ARQUIVO_PRINCIPAL = PASTA_APP / "responda_ou_estuda.py"
PASTA_DADOS = PASTA_APP / "dados"
ARQUIVO_LOG = PASTA_DADOS / "iniciador_janela_app.log"
NOME_MUTEX = "Local\\RespondaOuEstuda_JanelaExclusiva_2026"
# O modo administrador (INICIAR_ADMIN.bat) grava em dados/estado_admin.json;
# por isso pode ficar aberto ao mesmo tempo que o jogo normal.
if os.environ.get("RESPONDA_ADMIN", "").strip() == "1":
    NOME_MUTEX += "_Admin"
TEMPO_LIMITE_SERVIDOR = 75.0

_HANDLE_MUTEX: int | None = None


def _configurar_log(diagnostico: bool) -> None:
    PASTA_DADOS.mkdir(parents=True, exist_ok=True)
    manipuladores: list[logging.Handler] = [
        logging.FileHandler(ARQUIVO_LOG, encoding="utf-8")
    ]
    if diagnostico:
        manipuladores.append(logging.StreamHandler(sys.stdout))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=manipuladores,
        force=True,
    )


def _mostrar_mensagem(titulo: str, texto: str, erro: bool = False) -> None:
    """Mostra um aviso mesmo quando o iniciador esta sendo executado por pythonw."""

    if os.name == "nt":
        icone = 0x10 if erro else 0x40  # MB_ICONERROR ou MB_ICONINFORMATION
        ctypes.windll.user32.MessageBoxW(0, texto, titulo, icone)
    else:
        print(f"{titulo}: {texto}", file=sys.stderr if erro else sys.stdout)


def _obter_execucao_exclusiva() -> bool:
    """Impede duas instancias simultaneas de alterarem os mesmos dados."""

    global _HANDLE_MUTEX
    if os.name != "nt":
        return True

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    criar_mutex = kernel32.CreateMutexW
    criar_mutex.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
    criar_mutex.restype = ctypes.c_void_p
    ctypes.set_last_error(0)
    handle = criar_mutex(None, False, NOME_MUTEX)
    if not handle:
        raise OSError(ctypes.get_last_error(), "Nao foi possivel criar o mutex")

    _HANDLE_MUTEX = int(handle)
    if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
        _mostrar_mensagem(
            "Responde ou Estuda",
            "O aplicativo ja esta aberto. Verifique a barra de tarefas.",
        )
        return False
    return True


def _porta_local_livre() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.bind(("127.0.0.1", 0))
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return int(servidor.getsockname()[1])


def _python_com_console() -> Path:
    """Troca pythonw.exe por python.exe para o processo interno do servidor."""

    executavel = Path(sys.executable)
    if executavel.name.lower() == "pythonw.exe":
        candidato = executavel.with_name("python.exe")
        if candidato.exists():
            return candidato
    return executavel


def _iniciar_servidor(porta: int, log_servidor) -> subprocess.Popen:
    ambiente = os.environ.copy()
    ambiente.update(
        {
            # Estas variaveis fazem o Flet iniciar somente o servidor local.
            # Nenhuma guia comum e nenhum cliente Flet Desktop sao abertos.
            "FLET_FORCE_WEB_SERVER": "true",
            "FLET_SERVER_IP": "127.0.0.1",
            "FLET_SERVER_PORT": str(porta),
            "FLET_DISPLAY_URL_PREFIX": "APP_LOCAL",
            "PYTHONUTF8": "1",
            "RESPONDA_JANELA_EXCLUSIVA": "1",
        }
    )
    sinalizadores = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return subprocess.Popen(
        [str(_python_com_console()), str(ARQUIVO_PRINCIPAL)],
        cwd=str(PASTA_APP),
        env=ambiente,
        stdin=subprocess.DEVNULL,
        stdout=log_servidor,
        stderr=subprocess.STDOUT,
        creationflags=sinalizadores,
    )


def _aguardar_servidor(
    processo: subprocess.Popen, url: str, limite: float = TEMPO_LIMITE_SERVIDOR
) -> None:
    inicio = time.monotonic()
    ultimo_erro = ""
    while time.monotonic() - inicio < limite:
        codigo = processo.poll()
        if codigo is not None:
            raise RuntimeError(
                f"O servidor local foi encerrado antes da abertura (codigo {codigo})."
            )
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resposta:
                if 200 <= resposta.status < 500:
                    return
        except (urllib.error.URLError, TimeoutError, ConnectionError) as erro:
            ultimo_erro = str(erro)
        time.sleep(0.25)
    detalhe = f" Ultimo retorno: {ultimo_erro}" if ultimo_erro else ""
    raise TimeoutError(
        "O mecanismo local demorou mais que o esperado para iniciar." + detalhe
    )


def _localizar_navegador() -> Path:
    """Localiza primeiro o Edge e usa o Chrome como alternativa."""

    configurado = os.getenv("RESPONDA_NAVEGADOR_APP", "").strip().strip('"')
    if configurado:
        caminho_configurado = Path(configurado)
        if caminho_configurado.is_file():
            return caminho_configurado

    candidatos: list[Path] = []
    raizes = [
        os.getenv("PROGRAMFILES(X86)"),
        os.getenv("PROGRAMFILES"),
        os.getenv("PROGRAMW6432"),
        os.getenv("LOCALAPPDATA"),
    ]
    relativos = [
        Path("Microsoft/Edge/Application/msedge.exe"),
        Path("Google/Chrome/Application/chrome.exe"),
    ]
    for raiz in raizes:
        if raiz:
            candidatos.extend(Path(raiz) / relativo for relativo in relativos)

    for nome in ("msedge.exe", "msedge", "chrome.exe", "chrome"):
        encontrado = shutil.which(nome)
        if encontrado:
            candidatos.append(Path(encontrado))

    verificados: set[str] = set()
    for candidato in candidatos:
        chave = str(candidato).lower()
        if chave not in verificados and candidato.is_file():
            return candidato
        verificados.add(chave)

    raise FileNotFoundError(
        "Microsoft Edge ou Google Chrome nao foi localizado neste computador."
    )


def _abrir_janela_aplicativo(
    navegador: Path, url: str
) -> tuple[subprocess.Popen, Path]:
    """Abre a URL em uma instancia isolada do navegador, no modo aplicativo."""

    perfil_temporario = Path(tempfile.mkdtemp(prefix="responda_ou_estuda_app_"))
    argumentos = [
        str(navegador),
        f"--app={url}",
        f"--user-data-dir={perfil_temporario}",
        "--start-maximized",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-mode",
        "--disable-session-crashed-bubble",
        # Impede que o Edge entre automaticamente com a conta do Windows e
        # mostre "Agora estamos sincronizando seus dados de navegação...".
        "--disable-sync",
        "--disable-features=msImplicitSignin,msEdgeFirstSyncOnFirstRun,"
        "msEdgeSyncConsent,msEdgeFrePrelaunchSyncData",
    ]
    processo = subprocess.Popen(
        argumentos,
        cwd=str(PASTA_APP),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
    )
    return processo, perfil_temporario


def _encerrar_processo(processo: subprocess.Popen | None) -> None:
    if processo is None or processo.poll() is not None:
        return
    processo.terminate()
    try:
        processo.wait(timeout=6)
    except subprocess.TimeoutExpired:
        processo.kill()
        processo.wait(timeout=3)


def _ultimas_linhas_log(maximo: int = 12) -> str:
    try:
        linhas = ARQUIVO_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(linhas[-maximo:])
    except OSError:
        return ""


def executar(diagnostico: bool = False) -> int:
    _configurar_log(diagnostico)
    logging.info("Iniciando a edicao em janela exclusiva.")

    if os.name != "nt":
        _mostrar_mensagem(
            "Responde ou Estuda",
            "Esta edicao foi preparada para Windows 10 ou Windows 11.",
            erro=True,
        )
        return 1
    if not _obter_execucao_exclusiva():
        return 0
    if not ARQUIVO_PRINCIPAL.is_file():
        _mostrar_mensagem(
            "Responde ou Estuda",
            "O arquivo responda_ou_estuda.py nao foi encontrado. Extraia novamente "
            "todo o conteudo do ZIP em uma unica pasta.",
            erro=True,
        )
        return 1

    servidor: subprocess.Popen | None = None
    janela: subprocess.Popen | None = None
    perfil_temporario: Path | None = None
    log_servidor = None
    try:
        navegador = _localizar_navegador()
        porta = _porta_local_livre()
        url = f"http://127.0.0.1:{porta}/responda_ou_estuda"
        logging.info("Navegador de interface: %s", navegador)
        logging.info("Endereco local: %s", url)

        log_servidor = ARQUIVO_LOG.open("a", encoding="utf-8")
        servidor = _iniciar_servidor(porta, log_servidor)
        _aguardar_servidor(servidor, url)
        logging.info("Servidor local pronto. Abrindo a janela do aplicativo.")

        janela, perfil_temporario = _abrir_janela_aplicativo(navegador, url)
        janela.wait()
        logging.info("A janela foi fechada pelo usuario.")
        return 0
    except Exception as erro:
        logging.exception("Falha ao iniciar a janela exclusiva")
        detalhes = _ultimas_linhas_log()
        texto = (
            f"Nao foi possivel abrir o aplicativo.\n\n{erro}\n\n"
            f"Consulte o arquivo:\n{ARQUIVO_LOG}"
        )
        if diagnostico and detalhes:
            texto += f"\n\nUltimos registros:\n{detalhes}"
        _mostrar_mensagem("Responde ou Estuda", texto, erro=True)
        return 1
    finally:
        _encerrar_processo(servidor)
        if log_servidor is not None:
            log_servidor.close()
        if perfil_temporario is not None:
            # A pasta pertence exclusivamente a esta execucao. Se o navegador
            # ainda mantiver algum arquivo em uso, a remocao sera apenas adiada.
            shutil.rmtree(perfil_temporario, ignore_errors=True)
        logging.info("Iniciador encerrado.")


def main() -> int:
    analisador = argparse.ArgumentParser(add_help=True)
    analisador.add_argument(
        "--diagnostico",
        action="store_true",
        help="Tambem exibe os registros na janela de comando.",
    )
    argumentos = analisador.parse_args()
    return executar(diagnostico=argumentos.diagnostico)


if __name__ == "__main__":
    raise SystemExit(main())

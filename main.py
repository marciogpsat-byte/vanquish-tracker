from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from cryptography.fernet import Fernet
import os

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Gera uma chave de criptografia AES para a sessão (ou usa uma variável de ambiente)
SECRET_KEY = os.getenv("SECRET_KEY", Fernet.generate_key().decode())
cipher = Fernet(SECRET_KEY.encode())

# Histórico armazena os dados cifrados
historico_criptografado = []

def criptografar_texto(texto: str) -> str:
    if not texto:
        return ""
    return cipher.encrypt(texto.encode()).decode()

def descriptografar_texto(texto_cifrado: str) -> str:
    if not texto_cifrado:
        return ""
    try:
        return cipher.decrypt(texto_cifrado.encode()).decode()
    except Exception:
        return texto_cifrado

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Descriptografa o histórico para exibir no visor
    historico_descriptografado = [
        {
            "vdi": int(descriptografar_texto(item["vdi"])),
            "alvo": descriptografar_texto(item["alvo"]),
            "profundidade": descriptografar_texto(item["profundidade"]),
            "gramatura": descriptografar_texto(item["gramatura"]),
            "gps": descriptografar_texto(item["gps"])
        }
        for item in reversed(historico_criptografado)
    ]
    
    ultimo = historico_descriptografado[0] if historico_descriptografado else None

    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={
            "historico": historico_descriptografado,
            "ultimo": ultimo
        }
    )

@app.post("/registrar", response_class=HTMLResponse)
async def registrar(
    request: Request,
    vdi: int = Form(...),
    objeto: str = Form(...),
    profundidade: str = Form("0"),
    gramatura: str = Form(""),
    gps: str = Form("")
):
    gramatura_val = gramatura if objeto in ["Ouro", "Prata"] else ""
    gps_val = gps if gps else "Sem GPS"
    
    # Criptografa cada campo antes de salvar na memória/banco
    registro_criptografado = {
        "vdi": criptografar_texto(str(vdi)),
        "alvo": criptografar_texto(objeto),
        "profundidade": criptografar_texto(str(profundidade)),
        "gramatura": criptografar_texto(str(gramatura_val)),
        "gps": criptografar_texto(gps_val)
    }
    
    historico_criptografado.append(registro_criptografado)
    
    # Prepara visualização descriptografada para resposta rápida
    novo_registro_limpo = {
        "vdi": vdi,
        "alvo": objeto,
        "profundidade": profundidade,
        "gramatura": gramatura_val,
        "gps": gps_val
    }
    
    historico_descriptografado = [
        {
            "vdi": int(descriptografar_texto(item["vdi"])),
            "alvo": descriptografar_texto(item["alvo"]),
            "profundidade": descriptografar_texto(item["profundidade"]),
            "gramatura": descriptografar_texto(item["gramatura"]),
            "gps": descriptografar_texto(item["gps"])
        }
        for item in reversed(historico_criptografado)
    ]

    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={
            "historico": historico_descriptografado,
            "ultimo": novo_registro_limpo
        }
    )

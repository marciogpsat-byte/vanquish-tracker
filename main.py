from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from cryptography.fernet import Fernet
import os
import json
from datetime import datetime

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
DATA_FILE = os.path.join(BASE_DIR, "dados_vanquish.json")

# Configuração de Criptografia
SECRET_KEY = os.getenv("SECRET_KEY", Fernet.generate_key().decode())
cipher = Fernet(SECRET_KEY.encode())

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

# --- FUNÇÕES DE PERSISTÊNCIA EM DISCO ---
def carregar_dados_disco():
    """Lê os dados salvos do arquivo JSON no servidor."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def salvar_dados_disco(dados):
    """Grava o histórico atualizado em disco para não perder nenhum registro."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

# Carrega o histórico salvo no boot da aplicação
historico_criptografado = carregar_dados_disco()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    historico_descriptografado = [
        {
            "vdi": int(descriptografar_texto(item["vdi"])),
            "alvo": descriptografar_texto(item["alvo"]),
            "profundidade": descriptografar_texto(item["profundidade"]),
            "gramatura": descriptografar_texto(item["gramatura"]),
            "gps": descriptografar_texto(item["gps"]),
            "data_hora": item.get("data_hora", "")
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
    data_agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Prepara registro criptografado com Timestamp
    registro_criptografado = {
        "vdi": criptografar_texto(str(vdi)),
        "alvo": criptografar_texto(objeto),
        "profundidade": criptografar_texto(str(profundidade)),
        "gramatura": criptografar_texto(str(gramatura_val)),
        "gps": criptografar_texto(gps_val),
        "data_hora": data_agora
    }
    
    # Salva na memória e grava fisicamente no arquivo
    historico_criptografado.append(registro_criptografado)
    salvar_dados_disco(historico_criptografado)
    
    # Prepara visualização limpa
    novo_registro_limpo = {
        "vdi": vdi,
        "alvo": objeto,
        "profundidade": profundidade,
        "gramatura": gramatura_val,
        "gps": gps_val,
        "data_hora": data_agora
    }
    
    historico_descriptografado = [
        {
            "vdi": int(descriptografar_texto(item["vdi"])),
            "alvo": descriptografar_texto(item["alvo"]),
            "profundidade": descriptografar_texto(item["profundidade"]),
            "gramatura": descriptografar_texto(item["gramatura"]),
            "gps": descriptografar_texto(item["gps"]),
            "data_hora": item.get("data_hora", "")
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

# --- ROTA PARA EXPORTAR SEUS DADOS PARA O FUTURO APP COMERCIAL ---
@app.get("/exportar-dados")
async def exportar_dados():
    """Retorna a base de dados completa já descriptografada em formato JSON pronto para migração."""
    dados_limpos = [
        {
            "vdi": int(descriptografar_texto(item["vdi"])),
            "alvo": descriptografar_texto(item["alvo"]),
            "profundidade": descriptografar_texto(item["profundidade"]),
            "gramatura": descriptografar_texto(item["gramatura"]),
            "gps": descriptografar_texto(item["gps"]),
            "data_hora": item.get("data_hora", "")
        }
        for item in historico_criptografado
    ]
    return {"total_registros": len(dados_limpos), "dados": dados_limpos}

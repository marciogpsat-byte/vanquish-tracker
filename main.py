from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from cryptography.fernet import Fernet
import os
import json
import base64
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

def carregar_dados_disco():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def salvar_dados_disco(dados):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

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
            "data_hora": item.get("data_hora", ""),
            "tem_audio": item.get("tem_audio", False),
            "audio_base64": item.get("audio_base64", "")
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
    gps: str = Form(""),
    audio_base64: str = Form("")
):
    gramatura_val = gramatura if objeto in ["Ouro", "Prata"] else ""
    gps_val = gps if gps else "Sem GPS"
    data_agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    registro_criptografado = {
        "vdi": criptografar_texto(str(vdi)),
        "alvo": criptografar_texto(objeto),
        "profundidade": criptografar_texto(str(profundidade)),
        "gramatura": criptografar_texto(str(gramatura_val)),
        "gps": criptografar_texto(gps_val),
        "data_hora": data_agora,
        "tem_audio": True if audio_base64 else False,
        "audio_base64": audio_base64
    }
    
    historico_criptografado.append(registro_criptografado)
    salvar_dados_disco(historico_criptografado)
    
    historico_descriptografado = [
        {
            "vdi": int(descriptografar_texto(item["vdi"])),
            "alvo": descriptografar_texto(item["alvo"]),
            "profundidade": descriptografar_texto(item["profundidade"]),
            "gramatura": descriptografar_texto(item["gramatura"]),
            "gps": descriptografar_texto(item["gps"]),
            "data_hora": item.get("data_hora", ""),
            "tem_audio": item.get("tem_audio", False),
            "audio_base64": item.get("audio_base64", "")
        }
        for item in reversed(historico_criptografado)
    ]

    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={
            "historico": historico_descriptografado,
            "ultimo": historico_descriptografado[0]
        }
    )

@app.get("/exportar-dados")
async def exportar_dados():
    dados_limpos = [
        {
            "vdi": int(descriptografar_texto(item["vdi"])),
            "alvo": descriptografar_texto(item["alvo"]),
            "profundidade": descriptografar_texto(item["profundidade"]),
            "gramatura": descriptografar_texto(item["gramatura"]),
            "gps": descriptografar_texto(item["gps"]),
            "data_hora": item.get("data_hora", ""),
            "tem_audio": item.get("tem_audio", False)
        }
        for item in historico_criptografado
    ]
    return {"total_registros": len(dados_limpos), "dados": dados_limpos}

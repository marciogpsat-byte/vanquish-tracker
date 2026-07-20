from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Histórico em memória
historico_memoria = []

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    context = {
        "request": request,
        "historico": list(reversed(historico_memoria)),
        "ultimo": historico_memoria[-1] if historico_memoria else None
    }
    return templates.TemplateResponse("index.html", context)

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
    
    novo_registro = {
        "vdi": vdi,
        "alvo": objeto,
        "profundidade": profundidade,
        "gramatura": gramatura_val,
        "gps": gps if gps else "Sem GPS"
    }
    
    historico_memoria.append(novo_registro)
    
    context = {
        "request": request,
        "historico": list(reversed(historico_memoria)),
        "ultimo": novo_registro
    }
    return templates.TemplateResponse("index.html", context)

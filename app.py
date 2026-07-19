import flet as ft
import os
import numpy as np
from scipy.io import wavfile

# Histórico temporário na memória para rodar em servidores gratuitos de nuvem
historico_memoria = []

def main(page: ft.Page):
    page.title = "Vanquish Tracker"
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 10

    # Texto de status inicial
    txt_status_microfone = ft.Text("Microfone Pronto", size=11, color="grey400")

    # CONTROLE BLINDADO: Verifica se o ambiente suporta o gravador nativo
    gravador = None
    if hasattr(ft, "AudioRecorder"):
        gravador = ft.AudioRecorder()
        page.overlay.append(gravador)
    else:
        txt_status_microfone.value = "Aviso: Recursos de áudio limitados no servidor."
        txt_status_microfone.color = "amber500"
    
    nivel_mineralizacao = ft.Ref[ft.Slider]()
    txt_vdi = ft.Ref[ft.Text]()
    txt_alvo = ft.Ref[ft.Text]()
    txt_confianca = ft.Ref[ft.Text]()
    
    lista_historico = ft.ListView(expand=True, spacing=5, padding=5, scroll=ft.ScrollMode.AUTO)

    # --- FUNÇÃO PARA FECHAR/ENCERRAR O APP ---
    def fechar_aplicativo(e):
        page.controls.clear()
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.POWER_SETTINGS_NEW, color="red500", size=60),
                    ft.Text("Sessão Encerrada!", size=20, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Text("O Vanquish Tracker foi fechado com segurança.", size=12, color="grey400"),
                    ft.Text("Você já pode fechar esta aba do seu navegador.", size=10, color="grey600"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
                alignment=ft.Alignment(0, 0),
                padding=50
            )
        )
        page.update()

    # --- FUNÇÕES DO RELATÓRIO E CORREÇÃO DE DADOS ---
    def abrir_relatorio(e):
        tabela_dados = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID", size=11)),
                ft.DataColumn(ft.Text("Alvo", size=11)),
                ft.DataColumn(ft.Text("VDI", size=11)),
                ft.DataColumn(ft.Text("Ações", size=11)),
            ],
            rows=[]
        )

        def preencher_tabela():
            tabela_dados.rows.clear()
            for idx, item in enumerate(historico_memoria):
                tabela_dados.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(idx + 1))),
                            ft.DataCell(ft.Text(item['alvo'])),
                            ft.DataCell(ft.Text(f"{item['vdi']:+d}" if item['vdi'] != 0 else "0")),
                            ft.DataCell(
                                ft.Row([
                                    ft.IconButton(
                                        icon=ft.Icons.EDIT,
                                        icon_color="amber",
                                        icon_size=16,
                                        on_click=lambda _, i=idx: iniciar_edicao(i)
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        icon_color="red",
                                        icon_size=16,
                                        on_click=lambda _, i=idx: excluir_registro(i)
                                    ),
                                ], spacing=0)
                            )
                        ]
                    )
                )

        def excluir_registro(indice):
            historico_memoria.pop(indice)
            preencher_tabela()
            atualizar_historico_ui()
            page.update()

        def iniciar_edicao(indice):
            item = historico_memoria[indice]
            input_alvo = ft.TextField(label="Nome do Alvo", value=item['alvo'], dense=True)
            input_vdi = ft.TextField(label="VDI", value=str(item['vdi']), keyboard_type=ft.KeyboardType.NUMBER, dense=True)

            def salvar_edicao(e):
                try:
                    historico_memoria[indice]['alvo'] = input_alvo.value
                    historico_memoria[indice]['vdi'] = int(input_vdi.value)
                    dialogo_edicao.open = False
                    preencher_tabela()
                    atualizar_historico_ui()
                    page.update()
                except ValueError:
                    pass

            dialogo_edicao = ft.AlertDialog(
                title=ft.Text("Editar Registro", size=14),
                content=ft.Column([input_alvo, input_vdi], tight=True, spacing=10),
                actions=[
                    ft.TextButton(content=ft.Text("Cancelar"), on_click=lambda _: fechar_modal(dialogo_edicao)),
                    ft.TextButton(content=ft.Text("Salvar"), on_click=salvar_edicao)
                ]
            )
            page.overlay.append(dialogo_edicao)
            dialogo_edicao.open = True
            page.update()

        def fechar_modal(modal):
            modal.open = False
            page.update()

        preencher_tabela()

        modal_relatorio = ft.AlertDialog(
            title=ft.Row([
                ft.Text("Relatório de Detecção", size=16, weight=ft.FontWeight.BOLD),
                ft.IconButton(icon=ft.Icons.CLOSE, on_click=lambda _: fechar_modal(modal_relatorio))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Aqui você pode revisar e corrigir os registros capturados pelo detector:", size=11, color="grey400"),
                    ft.Divider(height=10, color="grey800"),
                    ft.Column([tabela_dados], height=200, scroll=ft.ScrollMode.AUTO)
                ], tight=True),
                width=300
            ),
            actions_alignment=ft.MainAxisAlignment.END
        )

        page.overlay.append(modal_relatorio)
        modal_relatorio.open = True
        page.update()

    # --- ATUALIZAÇÃO DA INTERFACE PRINCIPAL ---
    def atualizar_historico_ui():
        lista_historico.controls.clear()
        for item in reversed(historico_memoria[-5:]):
            lista_historico.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.GPS_FIXED, color="amber", size=14),
                        ft.Text(f"{item['alvo']} (VDI: {item['vdi']}) - {item['confianca']}%", size=11, color="white")
                    ], alignment=ft.MainAxisAlignment.START),
                    padding=6,
                    bgcolor="surfacevariant",
                    border_radius=ft.BorderRadius.all(5)
                )
            )
        page.update()

    # --- PROCESSAMENTO MATEMÁTICO REAL DO ÁUDIO ---
    def analisar_audio_gravado(caminho_audio):
        try:
            taxa_amostragem, dados = wavfile.read(caminho_audio)
            if len(dados.shape) > 1:
                dados = dados[:, 0]
            
            fft_dados = np.fft.rfft(dados)
            frequencias = np.fft.rfftfreq(len(dados), d=1.0/taxa_amostragem)
            
            indice_pico = np.argmax(np.abs(fft_dados))
            frequencia_pico = frequencias[indice_pico]
            
            detectar_sinal(frequencia_pico)
        except Exception:
            txt_status_microfone.value = "Erro na análise: som muito baixo."
            page.update()

    def detectar_sinal(freq):
        min_level = int(nivel_mineralizacao.current.value)
        vdi_base = int((freq - 300) / 15)
        
        if min_level >= 4 and -4 <= vdi_base <= 3:
            txt_vdi.current.value = "FILT"
            txt_alvo.current.value = "Solo Mineralizado"
            txt_confianca.current.value = "--%"
        else:
            txt_vdi.current.value = f"{vdi_base:+d}" if vdi_base != 0 else "0"
            if vdi_base < 0:
                alvo = "Ferro"
            elif vdi_base > 20:
                alvo = "Prata"
            else:
                alvo = "Moeda/Alumínio"
            
            txt_alvo.current.value = alvo
            txt_confianca.current.value = "95%"
            
            historico_memoria.append({"alvo": alvo, "vdi": vdi_base, "confianca": 95})
            atualizar_historico_ui()
        page.update()

    def alternar_escuta(e):
        if gravador is None:
            txt_status_microfone.value = "Microfone indisponível no servidor. Use os botões abaixo para simular!"
            txt_status_microfone.color = "amber500"
            page.update()
            return

        try:
            if not gravador.has_permission():
                txt_status_microfone.value = "Solicitando permissão de áudio..."
                page.update()
                gravador.request_permission()
                return

            if btn_escutar.content.value == "Iniciar Escuta":
                btn_escutar.content.value = "Ouvindo detector..."
                btn_escutar.icon = ft.Icons.MIC
                btn_escutar.bgcolor = "red800"
                txt_status_microfone.value = "Capturando som do detector..."
                page.update()
                gravador.start_recording()
            else:
                btn_escutar.content.value = "Iniciar Escuta"
                btn_escutar.icon = ft.Icons.MIC_NONE
                btn_escutar.bgcolor = "bluegrey700"
                txt_status_microfone.value = "Processando áudio capturado..."
                page.update()
                
                caminho_arquivo = gravador.stop_recording()
                if caminho_arquivo:
                    analisar_audio_gravado(caminho_arquivo)
                    txt_status_microfone.value = "Sinal Processado!"
                else:
                    txt_status_microfone.value = "Nenhum áudio detectado."
                page.update()
                
        except Exception as ex:
            txt_status_microfone.value = f"Erro no microfone: {str(ex)}"
            page.update()

    # --- INTERFACE GRÁFICA AJUSTADA (OTIMIZADA PARA CELULAR) ---
    header = ft.Container(
        content=ft.Row([
            ft.IconButton(icon=ft.Icons.POWER_SETTINGS_NEW, icon_color="transparent", disabled=True),
            ft.Column([
                ft.Text("VANQUISH TRACKER", size=15, weight=ft.FontWeight.BOLD, color="amber"),
                ft.Text("Mapeamento Inteligente", size=8, color="grey400"),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.IconButton(icon=ft.Icons.POWER_SETTINGS_NEW, icon_color="red500", tooltip="Sair do Aplicativo", on_click=fechar_aplicativo)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.Padding.only(left=5, right=5, bottom=0, top=0)
    )

    visor_vdi = ft.Container(
        content=ft.Column([
            ft.Text(ref=txt_vdi, value="--", size=40, weight=ft.FontWeight.BOLD, color="white"),
            ft.Text(ref=txt_alvo, value="Aguardando Sinal...", size=12, color="amber400", weight=ft.FontWeight.W_500),
            ft.Text(ref=txt_confianca, value="--%", size=10, color="grey400"),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
        bgcolor="bluegrey900",
        padding=10,
        border_radius=ft.BorderRadius.all(10),
        width=240,
        margin=ft.margin.only(bottom=5)
    )

    btn_escutar = ft.ElevatedButton(
        content=ft.Text("Iniciar Escuta", color="white"),
        icon=ft.Icons.MIC_NONE,
        on_click=alternar_escuta,
        bgcolor="bluegrey700",
        width=200
    )

    btn_relatorio = ft.OutlinedButton(
        content=ft.Text("Ver Relatório / Corrigir", color="amber"),
        icon=ft.Icons.ASSESSMENT,
        on_click=abrir_relatorio,
        width=200
    )

    controles = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("Controle de Áudio e Solo", weight=ft.FontWeight.BOLD, size=11),
                ft.Container(content=btn_escutar, alignment=ft.Alignment(0, 0), padding=2),
                ft.Container(content=btn_relatorio, alignment=ft.Alignment(0, 0), padding=2),
                txt_status_microfone,
                ft.Divider(height=5, color="grey800"),
                ft.Text("Ajuste de Solo Manual", size=10, color="grey400"),
                ft.Slider(ref=nivel_mineralizacao, min=1, max=5, divisions=4, value=4, label="Nível {value}"),
                ft.Row([
                    ft.ElevatedButton(content=ft.Text("Ferro", color="white"), on_click=lambda _: detectar_sinal(120), bgcolor="grey800"),
                    ft.ElevatedButton(content=ft.Text("Médio", color="white"), on_click=lambda _: detectar_sinal(450), bgcolor="bluegrey700"),
                    ft.ElevatedButton(content=ft.Text("Prata", color="white"), on_click=lambda _: detectar_sinal(850), bgcolor="amber800"),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=3)
            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=8,
        ),
        margin=ft.margin.only(top=0, bottom=5),
    )

    secao_historico = ft.Column([
        ft.Container(
            content=ft.Text("Histórico Recente", size=11, weight=ft.FontWeight.BOLD),
            alignment=ft.Alignment(-0.8, 0)
        ),
        ft.Container(
            content=lista_historico, 
            height=110, 
            width=260, 
            border_radius=ft.BorderRadius.all(6), 
            bgcolor="black12",
            padding=5
        )
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5)

    page.add(
        header,
        visor_vdi,
        controles,
        secao_historico
    )
    
    atualizar_historico_ui()

if __name__ == '__main__':
    porta = int(os.environ.get("PORT", 8080))
    ft.app(
        target=main, 
        view=ft.AppView.WEB_BROWSER, 
        host="0.0.0.0", 
        port=porta,
        upload_dir="uploads"
    )

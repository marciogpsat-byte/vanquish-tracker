import flet as ft
import os
import numpy as np
from scipy.io import wavfile

# Histórico temporário na memória
historico_memoria = []

def main(page: ft.Page):
    page.title = "Vanquish Tracker"
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 10

    # Inicializa o Gravador de Áudio do Flet
    # O Flet moderno às vezes exige que o controle seja chamado de forma explícita 
# ou pelo pacote de controles se o autocomplete do servidor falhar
try:
    gravador = ft.AudioRecorder()
except AttributeError:
    # Caso a versão use a nomenclatura antiga/alternativa de pacotes
    from flet.audio_recorder import AudioRecorder
    gravador = AudioRecorder()

page.overlay.append(gravador)
    
    nivel_mineralizacao = ft.Ref[ft.Slider]()
    txt_vdi = ft.Ref[ft.Text]()
    txt_alvo = ft.Ref[ft.Text]()
    txt_confianca = ft.Ref[ft.Text]()
    txt_status_microfone = ft.Text("Microfone Pronto", size=11, color="grey400")
    lista_historico = ft.ListView(expand=1, spacing=5, padding=5)

    # --- FUNÇÃO PARA FECHAR/ENCERRAR O APP ---
    def fechar_aplicativo(e):
        page.controls.clear()
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Icon("power_settings_new", color="red500", size=60),
                    ft.Text("Sessão Encerrada!", size=20, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Text("O Vanquish Tracker foi fechado com segurança.", size=12, color="grey400"),
                    ft.Text("Você já pode fechar esta aba do seu navegador.", size=10, color="grey600"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
                alignment=ft.alignment.center,
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
                                        icon="edit",
                                        icon_color="amber",
                                        icon_size=16,
                                        on_click=lambda _, i=idx: iniciar_edicao(i)
                                    ),
                                    ft.IconButton(
                                        icon="delete",
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
                    ft.TextButton("Cancelar", on_click=lambda _: fechar_modal(dialogo_edicao)),
                    ft.TextButton("Salvar", on_click=salvar_edicao)
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
                ft.IconButton("close", on_click=lambda _: fechar_modal(modal_relatorio))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Aqui você pode revisar e corrigir os registros capturados pelo detector:", size=11, color="grey400"),
                    ft.Divider(height=10, color="grey800"),
                    ft.Container(content=tabela_dados, height=200, scroll=ft.ScrollMode.AUTO)
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
                        ft.Icon("gps_fixed", color="amber", size=14),
                        ft.Text(f"{item['alvo']} (VDI: {item['vdi']}) - {item['confianca']}%", size=11, color="white")
                    ], alignment=ft.MainAxisAlignment.START),
                    padding=6,
                    bgcolor="surfacevariant",
                    border_radius=5
                )
            )
        page.update()

    # --- PROCESSAMENTO MATEMÁTICO REAL DO ÁUDIO ---
    def analisar_audio_gravado(caminho_audio):
        try:
            # Lê o arquivo WAV gerado pelo gravador
            taxa_amostragem, dados = wavfile.read(caminho_audio)
            
            # Se for estéreo, transforma em mono
            if len(dados.shape) > 1:
                dados = dados[:, 0]
            
            # Aplica a Transformada Rápida de Fourier (FFT) para achar a frequência predominante
            fft_dados = np.fft.rfft(dados)
            frequencias = np.fft.rfftfreq(len(dados), d=1.0/taxa_amostragem)
            
            # Pega o pico de maior volume/energia sonora
            indice_pico = np.argmax(np.abs(fft_dados))
            frequencia_pico = frequencias[indice_pico]
            
            # Manda a frequência exata detectada para atualizar a interface!
            detectar_sinal(frequencia_pico)
            
        except Exception as e:
            txt_status_microfone.value = f"Erro na análise física: som muito baixo."
            page.update()

    def detectar_sinal(freq):
        min_level = int(nivel_mineralizacao.current.value)
        # Converte a frequência de som do Vanquish para escala VDI aproximada
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
        try:
            if not gravador.has_permission():
                txt_status_microfone.value = "Solicitando permissão de áudio..."
                page.update()
                gravador.request_permission()
                return

            if btn_escutar.text == "Iniciar Escuta":
                btn_escutar.text = "Ouvindo detector..."
                btn_escutar.icon = "mic"
                btn_escutar.bgcolor = "red800"
                txt_status_microfone.value = "Capturando som do detector..."
                page.update()
                gravador.start_recording()
            else:
                btn_escutar.text = "Iniciar Escuta"
                btn_escutar.icon = "mic_none"
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

    # --- INTERFACE GRÁFICA ---
    header = ft.Container(
        content=ft.Row([
            ft.IconButton("power_settings_new", icon_color="transparent", disabled=True),
            ft.Column([
                ft.Text("VANQUISH TRACKER", size=15, weight=ft.FontWeight.BOLD, color="amber"),
                ft.Text("Mapeamento Inteligente", size=8, color="grey400"),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.IconButton("power_settings_new", icon_color="red500", tooltip="Sair do Aplicativo", on_click=fechar_aplicativo)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.padding.only(left=5, right=5, bottom=5)
    )

    visor_vdi = ft.Container(
        content=ft.Column([
            ft.Text(ref=txt_vdi, value="--", size=40, weight=ft.FontWeight.BOLD, color="white"),
            ft.Text(ref=txt_alvo, value="Aguardando Sinal...", size=12, color="amber400", weight=ft.FontWeight.W_500),
            ft.Text(ref=txt_confianca, value="--%", size=10, color="grey400"),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
        bgcolor="bluegrey900",
        padding=10,
        border_radius=10,
        width=240,
    )

    btn_escutar = ft.ElevatedButton(
        text="Iniciar Escuta",
        icon="mic_none",
        on_click=alternar_escuta,
        bgcolor="bluegrey700",
        color="white",
        width=200
    )

    btn_relatorio = ft.OutlinedButton(
        text="Ver Relatório / Corrigir",
        icon="assessment",
        on_click=abrir_relatorio,
        style=ft.ButtonStyle(color="amber"),
        width=200
    )

    controles = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("Controle de Áudio e Solo", weight=ft.FontWeight.BOLD, size=11),
                ft.Container(content=btn_escutar, alignment=ft.alignment.center, padding=2),
                ft.Container(content=btn_relatorio, alignment=ft.alignment.center, padding=2),
                txt_status_microfone,
                ft.Divider(height=10, color="grey800"),
                ft.Text("Ajuste de Solo Manual", size=10, color="grey400"),
                ft.Slider(ref=nivel_mineralizacao, min=1, max=5, divisions=4, value=4, label="Nível {value}"),
                ft.Row([
                    ft.ElevatedButton("Ferro", on_click=lambda _: detectar_sinal(120), bgcolor="grey800"),
                    ft.ElevatedButton("Médio", on_click=lambda _: detectar_sinal(450), bgcolor="bluegrey700"),
                    ft.ElevatedButton("Prata", on_click=lambda _: detectar_sinal(850), bgcolor="amber800"),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=3)
            ], spacing=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=8,
        ),
        margin=3,
    )

    page.add(
        header,
        visor_vdi,
        controles,
        ft.Text("Histórico Recente", size=11, weight=ft.FontWeight.BOLD),
        ft.Container(content=lista_historico, height=100, width=280, border_radius=6, bgcolor="black12"),
    )
    
    atualizar_historico_ui()

if __name__ == '__main__':
    porta = int(os.environ.get("PORT", 8080))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=porta)

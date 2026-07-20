import flet as ft
import os

# Histórico temporário na memória com suporte a GPS
historico_memoria = []

def main(page: ft.Page):
    page.title = "Vanquish Tracker"
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 10

    # Texto de status inicial
    txt_status_sistema = ft.Text("Pronto para mapeamento", size=11, color="grey400")
    
    txt_vdi = ft.Ref[ft.Text]()
    txt_alvo = ft.Ref[ft.Text]()
    txt_confianca = ft.Ref[ft.Text]()
    
    # Campos ocultos para armazenar as coordenadas capturadas pelo JavaScript do Celular
    txt_lat = ft.TextField(visible=False, value="")
    txt_lon = ft.TextField(visible=False, value="")
    
    lista_historico = ft.ListView(expand=True, spacing=5, padding=5, scroll=ft.ScrollMode.AUTO)

    # --- JAVASCRIPT NATIVO PARA SOLICITAR GPS DO NAVEGADOR ---
    def solicitar_gps_automatico():
        # Executa script diretamente no Safari/Chrome do celular para pegar o GPS real
        js_code = """
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    var latInput = document.querySelector("input[aria-label='lat_gps']");
                    var lonInput = document.querySelector("input[aria-label='lon_gps']");
                    if (latInput && lonInput) {
                        latInput.value = position.coords.latitude;
                        lonInput.value = position.coords.longitude;
                        latInput.dispatchEvent(new Event('input', { bubbles: true }));
                        lonInput.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                },
                function(error) {
                    console.log("Erro ao obter GPS: " + error.message);
                },
                { enableHighAccuracy: true, timeout: 10000 }
            );
        }
        """
        page.run_javascript(js_code)

    # Solicita a localização assim que o aplicativo abre na tela do celular
    page.on_connect = lambda e: solicitar_gps_automatico()

    # --- FUNÇÃO PARA FECHAR/ENCERRAR O APP ---
    def fechar_aplicativo(e):
        page.controls.clear()
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.POWER_SETTINGS_NEW, color="red500", size=60),
                    ft.Text("Sessão Encerrada!", size=20, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Text("O Vanquish Tracker foi fechado com segurança.", size=12, color="grey400"),
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
                ft.DataColumn(ft.Text("ID/VDI", size=11)),
                ft.DataColumn(ft.Text("Objeto", size=11)),
                ft.DataColumn(ft.Text("Coordenadas GPS", size=11)),
                ft.DataColumn(ft.Text("Ações", size=11)),
            ],
            rows=[]
        )

        def preencher_tabela():
            tabela_dados.rows.clear()
            for idx, item in enumerate(historico_memoria):
                coordenadas = f"{item['lat']:.5f}, {item['lon']:.5f}" if item['lat'] != 0.0 else "Sem GPS"
                tabela_dados.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(f"{item['vdi']:+d}" if item['vdi'] != 0 else "0")),
                            ft.DataCell(ft.Text(item['alvo'])),
                            ft.DataCell(ft.Text(coordenadas, size=10)),
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
            input_alvo = ft.TextField(label="Objeto", value=item['alvo'], dense=True)
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
                ft.Text("Relatório com GPS", size=16, weight=ft.FontWeight.BOLD),
                ft.IconButton(icon=ft.Icons.CLOSE, on_click=lambda _: fechar_modal(modal_relatorio))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Lista de achados georreferenciados:", size=11, color="grey400"),
                    ft.Divider(height=10, color="grey800"),
                    ft.Column([tabela_dados], height=250, scroll=ft.ScrollMode.AUTO)
                ], tight=True),
                width=340
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
            coordenadas = f"({item['lat']:.4f}, {item['lon']:.4f})" if item['lat'] != 0.0 else "(Sem GPS)"
            lista_historico.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.LOCATION_ON, color="red400" if item['lat'] != 0.0 else "grey", size=12),
                        ft.Text(f"{item['alvo']} [VDI: {item['vdi']}] {coordenadas}", size=11, color="white")
                    ], alignment=ft.MainAxisAlignment.START),
                    padding=6,
                    bgcolor="surfacevariant",
                    border_radius=ft.BorderRadius.all(5)
                )
            )
        page.update()

    # --- REGISTRO DO OBJETO UTILIZANDO COORDENADAS CAPTURADAS ---
    def registrar_objeto_manual(e):
        if not input_vdi_manual.value:
            txt_status_sistema.value = "Por favor, digite o ID/VDI do visor!"
            txt_status_sistema.color = "red400"
            page.update()
            return
        
        try:
            # Tenta disparar uma atualização de GPS imediata no celular
            solicitar_gps_automatico()
            
            vdi_informado = int(input_vdi_manual.value)
            objeto_selecionado = dropdown_objeto.value if dropdown_objeto.value else "Outro"
            
            # Tenta converter os campos de lat/lon preenchidos pelo JS
            try:
                lat = float(txt_lat.value) if txt_lat.value else 0.0
                lon = float(txt_lon.value) if txt_lon.value else 0.0
            except ValueError:
                lat, lon = 0.0, 0.0

            # Atualiza o Visor Principal do App
            txt_vdi.current.value = f"{vdi_informado:+d}" if vdi_informado != 0 else "0"
            txt_alvo.current.value = objeto_selecionado
            txt_confianca.current.value = "GPS Capturado" if lat != 0.0 else "Manual (Sem GPS)"
            
            # Salva no histórico
            historico_memoria.append({
                "alvo": objeto_selecionado, 
                "vdi": vdi_informado, 
                "lat": lat, 
                "lon": lon
            })
            
            if lat != 0.0:
                txt_status_sistema.value = "Achado registrado com GPS!"
                txt_status_sistema.color = "green400"
            else:
                txt_status_sistema.value = "Salvo! Permita a localização no seu navegador."
                txt_status_sistema.color = "amber400"
            
            # Limpa o campo de entrada para o próximo registro
            input_vdi_manual.value = ""
            atualizar_historico_ui()
            
        except ValueError:
            txt_status_sistema.value = "ID inválido! Insira apenas números."
            txt_status_sistema.color = "red400"
        page.update()

    # --- INTERFACE GRÁFICA ---
    header = ft.Container(
        content=ft.Row([
            ft.IconButton(icon=ft.Icons.POWER_SETTINGS_NEW, icon_color="transparent", disabled=True),
            ft.Column([
                ft.Text("VANQUISH TRACKER", size=15, weight=ft.FontWeight.BOLD, color="amber"),
                ft.Text("Mapeamento Inteligente & GPS", size=8, color="grey400"),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.IconButton(icon=ft.Icons.POWER_SETTINGS_NEW, icon_color="red500", tooltip="Sair do Aplicativo", on_click=fechar_aplicativo)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.Padding.only(left=5, right=5, bottom=0, top=0)
    )

    visor_vdi = ft.Container(
        content=ft.Column([
            ft.Text(ref=txt_vdi, value="--", size=40, weight=ft.FontWeight.BOLD, color="white"),
            ft.Text(ref=txt_alvo, value="Aguardando Registro...", size=12, color="amber400", weight=ft.FontWeight.W_500),
            ft.Text(ref=txt_confianca, value="--", size=10, color="grey400"),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
        bgcolor="bluegrey900",
        padding=10,
        border_radius=ft.BorderRadius.all(10),
        width=240,
        margin=ft.Margin(left=0, top=0, right=0, bottom=5)
    )

    input_vdi_manual = ft.TextField(
        label="VDI do Visor", 
        hint_text="Ex: 36", 
        width=100, 
        keyboard_type=ft.KeyboardType.NUMBER,
        dense=True
    )
    
    dropdown_objeto = ft.Dropdown(
        label="Tipo de Objeto",
        width=130,
        dense=True,
        value="Moeda",
        options=[
            ft.dropdown.Option("Ouro"),
            ft.dropdown.Option("Prata"),
            ft.dropdown.Option("Moeda"),
            ft.dropdown.Option("Biju"),
            ft.dropdown.Option("Celular"),
            ft.dropdown.Option("Outro"),
        ]
    )

    # Campos invisíveis com labels acessíveis para o JavaScript encontrar no DOM
    txt_lat.label = "lat_gps"
    txt_lon.label = "lon_gps"

    btn_registrar_manual = ft.ElevatedButton(
        content=ft.Text("Registrar Objeto + GPS", color="white", size=12),
        icon=ft.Icons.GPS_FIXED,
        on_click=registrar_objeto_manual,
        bgcolor="amber800",
        width=240
    )

    btn_relatorio = ft.OutlinedButton(
        content=ft.Text("Ver Relatório / Exportar", color="amber"),
        icon=ft.Icons.ASSESSMENT,
        on_click=abrir_relatorio,
        width=240
    )

    painel_manual = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("Entrada Manual de Achados", weight=ft.FontWeight.BOLD, size=11),
                ft.Row([input_vdi_manual, dropdown_objeto], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                ft.Container(content=btn_registrar_manual, alignment=ft.Alignment(0, 0), padding=2),
                ft.Container(content=btn_relatorio, alignment=ft.Alignment(0, 0), padding=2),
                txt_status_sistema,
                txt_lat,
                txt_lon
            ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=10,
        ),
        margin=ft.Margin(left=0, top=0, right=0, bottom=5),
    )

    secao_historico = ft.Column([
        ft.Container(
            content=ft.Text("Histórico Georreferenciado", size=11, weight=ft.FontWeight.BOLD),
            alignment=ft.Alignment(0, 0)
        ),
        ft.Container(
            content=lista_historico, 
            height=130, 
            width=260, 
            border_radius=ft.BorderRadius.all(6), 
            bgcolor="black12",
            padding=5
        )
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5)

    page.add(
        header,
        visor_vdi,
        painel_manual,
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

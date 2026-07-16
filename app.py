import flet as ft
import os
# Histórico temporário na memória para rodar em servidores gratuitos de nuvem
historico_memoria = []

def main(page: ft.Page):
    page.title = "Vanquish Tracker"
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 10

    nivel_mineralizacao = ft.Ref[ft.Slider]()
    txt_vdi = ft.Ref[ft.Text]()
    txt_alvo = ft.Ref[ft.Text]()
    txt_confianca = ft.Ref[ft.Text]()
    lista_historico = ft.ListView(expand=1, spacing=5, padding=5)

    def atualizar_historico_ui():
        lista_historico.controls.clear()
        # Exibe as últimas 5 detecções
        for item in reversed(historico_memoria[-5:]):
            lista_historico.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.GPS_FIXED, color=ft.colors.AMBER, size=14),
                        ft.Text(f"{item['alvo']} (VDI: {item['vdi']}) - {item['confianca']}%", size=11, color=ft.colors.WHITE)
                    ], alignment=ft.MainAxisAlignment.START),
                    padding=6,
                    bgcolor=ft.colors.SURFACE_VARIANT,
                    border_radius=5
                )
            )
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

    header = ft.Container(
        content=ft.Column([
            ft.Text("VANQUISH TRACKER", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.AMBER),
            ft.Text("Mapeamento Inteligente de Alvos", size=9, color=ft.colors.GREY_400),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=2,
    )

    visor_vdi = ft.Container(
        content=ft.Column([
            ft.Text(ref=txt_vdi, value="--", size=40, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
            ft.Text(ref=txt_alvo, value="Aguardando Sinal...", size=12, color=ft.colors.AMBER_400, weight=ft.FontWeight.W_500),
            ft.Text(ref=txt_confianca, value="--%", size=10, color=ft.colors.GREY_400),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
        bgcolor=ft.colors.BLUE_GREY_900,
        padding=10,
        border_radius=10,
        width=240,
    )

    controles = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("Ajuste de Solo", weight=ft.FontWeight.BOLD, size=11),
                ft.Slider(ref=nivel_mineralizacao, min=1, max=5, divisions=4, value=4, label="Nível {value}"),
                ft.Row([
                    ft.ElevatedButton("Ferro", on_click=lambda _: detectar_sinal(120), bgcolor=ft.colors.GREY_800),
                    ft.ElevatedButton("Médio", on_click=lambda _: detectar_sinal(450), bgcolor=ft.colors.BLUE_GREY_700),
                    ft.ElevatedButton("Prata", on_click=lambda _: detectar_sinal(850), bgcolor=ft.colors.AMBER_800),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=3)
            ], spacing=3),
            padding=8,
        ),
        margin=3,
    )

    page.add(
        header,
        visor_vdi,
        controles,
        ft.Text("Histórico Recente", size=11, weight=ft.FontWeight.BOLD),
        ft.Container(content=lista_historico, height=100, width=280, border_radius=6, bgcolor=ft.colors.BLACK12),
    )
    
    atualizar_historico_ui()

if __name__ == '__main__':
    # O Render diz em qual porta rodar através da variável de ambiente PORT
    porta = int(os.environ.get("PORT", 8080))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=porta)

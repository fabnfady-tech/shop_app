"""
شاشة التقرير - صافي الدخل اليومي، الإيرادات النقدية مقابل الآجلة، وتنبيهات المخزون
"""
import flet as ft
import db
from datetime import date


def stat_card(title, value, color, icon):
    return ft.Container(
        content=ft.Column(
            [
                ft.Row([ft.Icon(icon, color=color, size=20), ft.Text(title, size=13, color=ft.Colors.GREY_700)]),
                ft.Text(value, size=20, weight=ft.FontWeight.BOLD, color=color),
            ],
            spacing=4,
        ),
        padding=15, border_radius=12, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, expand=True,
    )


def ReportsView(page: ft.Page):
    content_col = ft.Column(spacing=15, expand=True, scroll=ft.ScrollMode.AUTO)

    def build():
        content_col.controls.clear()
        report = db.get_daily_report(date.today().isoformat())

        net_color = ft.Colors.GREEN_700 if report["net"] >= 0 else ft.Colors.RED_700
        net_card = ft.Container(
            content=ft.Column(
                [
                    ft.Text("صافي الدخل اليوم", size=14, color=ft.Colors.GREY_700),
                    ft.Text(f'{report["net"]:.2f} ج.م', size=32, weight=ft.FontWeight.BOLD, color=net_color),
                    ft.Text(f'عدد عمليات البيع: {report["num_sales"]}', size=12, color=ft.Colors.GREY_600),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=20, border_radius=15, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            alignment=ft.Alignment.CENTER,
        )

        income_row = ft.Row(
            [
                stat_card("نقدي (فوري)", f'{report["cash_income"]:.2f} ج.م', ft.Colors.GREEN_700, ft.Icons.PAID),
                stat_card("محفظة 📱", f'{report["wallet_income"]:.2f} ج.م', ft.Colors.BLUE_700, ft.Icons.PHONE_ANDROID),
            ],
            spacing=10,
        )
        income_row2 = ft.Row(
            [
                stat_card("محصّل من الآجل", f'{report["deferred_collected"]:.2f} ج.م', ft.Colors.TEAL_700, ft.Icons.ASSIGNMENT_TURNED_IN),
            ],
            spacing=10,
        )
        expenses_row = ft.Row(
            [
                stat_card("المصروفات", f'{report["expenses"]:.2f} ج.م', ft.Colors.RED_700, ft.Icons.TRENDING_DOWN),
                stat_card("مرتجعات", f'{report["returns_total"]:.2f} ج.م', ft.Colors.ORANGE_800, ft.Icons.UNDO),
            ],
            spacing=10,
        )

        deferred_card = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.SCHEDULE_SEND, color=ft.Colors.ORANGE_800),
                    ft.Column(
                        [
                            ft.Text("مبيعات آجلة جديدة النهاردة", size=12, color=ft.Colors.GREY_700),
                            ft.Text(f'{report["deferred_new"]:.2f} ج.م', weight=ft.FontWeight.BOLD),
                        ],
                        expand=True,
                    ),
                    ft.Column(
                        [
                            ft.Text("إجمالي مستحق على العملاء", size=12, color=ft.Colors.GREY_700),
                            ft.Text(f'{report["deferred_outstanding"]:.2f} ج.م', weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.RED_700),
                        ],
                        expand=True, horizontal_alignment=ft.CrossAxisAlignment.END,
                    ),
                ]
            ),
            padding=15, border_radius=12, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        )

        content_col.controls.append(ft.Text("تقرير اليوم", size=20, weight=ft.FontWeight.BOLD))
        content_col.controls.append(net_card)
        content_col.controls.append(income_row)
        content_col.controls.append(income_row2)
        content_col.controls.append(expenses_row)
        content_col.controls.append(deferred_card)

        if report["low_stock"]:
            content_col.controls.append(ft.Divider())
            content_col.controls.append(
                ft.Row([ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.ORANGE),
                        ft.Text("منتجات المخزون بتاعها بيقرب يخلص", weight=ft.FontWeight.BOLD)])
            )
            for p in report["low_stock"]:
                unit_label = "كجم" if p["unit"] == "كيلو" else "قطعة"
                content_col.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [ft.Text(p["name"], expand=True),
                             ft.Text(f'متبقي: {p["stock"]:g} {unit_label}', color=ft.Colors.ORANGE)]
                        ),
                        padding=10, border_radius=10, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                    )
                )

        content_col.controls.append(ft.OutlinedButton("تحديث", icon=ft.Icons.REFRESH, on_click=lambda e: build()))
        page.update()

    build()
    return content_col

"""
شاشة الإيرادات المؤجلة - العملاء اللي بيشتروا بالأجل، وتسجيل السداد
"""
import flet as ft
import db


def DeferredView(page: ft.Page):
    list_view = ft.ListView(expand=True, spacing=8, padding=ft.Padding.all(5))
    total_text = ft.Text("", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_800)
    show_paid_switch = ft.Switch(label="اعرض المسدد كمان", on_change=lambda e: refresh())

    def refresh():
        list_view.controls.clear()
        items = db.get_deferred_sales(only_unpaid=not show_paid_switch.value)
        total_due = sum(s["total"] for s in items if not s["paid"])
        if not items:
            list_view.controls.append(
                ft.Container(content=ft.Text("مفيش مبيعات آجلة حالياً", color=ft.Colors.GREY), padding=20)
            )
        for s in items:
            list_view.controls.append(deferred_row(s))
        total_text.value = f"إجمالي المتبقي على العملاء: {total_due:.2f} ج.م"
        page.update()

    def deferred_row(s):
        serial = db.invoice_serial(s["id"])
        paid = bool(s["paid"])
        return ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Row([
                                ft.Text(s["customer_name"] or "بدون اسم", weight=ft.FontWeight.BOLD),
                                ft.Text(serial, size=11, color=ft.Colors.GREY_600),
                            ]),
                            ft.Row([
                                ft.Icon(ft.Icons.PHONE, size=14, color=ft.Colors.GREY_600),
                                ft.Text(s["customer_phone"] or "-", size=12, color=ft.Colors.GREY_700),
                            ]),
                            ft.Text(s["created_at"][:16], size=11, color=ft.Colors.GREY_500),
                        ],
                        expand=True, spacing=2,
                    ),
                    ft.Column(
                        [
                            ft.Text(f'{s["total"]:.2f} ج.م', weight=ft.FontWeight.BOLD,
                                     color=ft.Colors.GREEN_700 if paid else ft.Colors.RED_700),
                            ft.Text("مسدد" if paid else "لسه مستحق", size=11,
                                    color=ft.Colors.GREEN_700 if paid else ft.Colors.ORANGE_800),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                    ),
                    ft.IconButton(
                        ft.Icons.PAID, icon_color=ft.Colors.GREEN,
                        tooltip="تسجيل السداد", visible=not paid,
                        on_click=lambda e, s=s: mark_paid(s),
                    ),
                ]
            ),
            padding=12, border_radius=10, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        )

    def mark_paid(s):
        db.mark_sale_paid(s["id"])
        refresh()

    refresh()

    return ft.Column(
        [
            ft.Text("الإيرادات المؤجلة (البيع بالأجل)", size=20, weight=ft.FontWeight.BOLD),
            show_paid_switch,
            total_text,
            ft.Divider(),
            list_view,
        ],
        expand=True,
    )

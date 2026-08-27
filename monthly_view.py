"""
شاشة جدول الشهر - سجل كل عمليات البيع في الشهر، بحث بالتاريخ، وتفاصيل كل فاتورة
"""
import flet as ft
import db
from datetime import date


ARABIC_MONTHS = ["", "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
                  "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]


def MonthlyView(page: ft.Page):
    today = date.today()
    state = {"year": today.year, "month": today.month, "search_date": ""}

    month_label = ft.Text("", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    
    search_field = ft.TextField(
        label="ابحث بتاريخ (YYYY-MM-DD) أو برقم فاتورة (INV-00001)", 
        rtl=True, 
        expand=True,
        color=ft.Colors.WHITE,
        label_style=ft.TextStyle(color=ft.Colors.WHITE70),
        border_color=ft.Colors.WHITE38,
        on_change=lambda e: (state.update(search_date=e.control.value), refresh_table()),
    )
    
    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("السيريال", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("التاريخ", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("الإجمالي", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("نوع الدفع", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("تفاصيل", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)),
        ],
        rows=[],
    )
    
    detail_panel = ft.Container(
        visible=False, 
        padding=12, 
        border_radius=10,
        bgcolor=ft.Colors.BLUE_GREY_900
    )
    
    summary_text = ft.Text("", size=14, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500)

    def show_detail(sale_id):
        serial = db.invoice_serial(sale_id)
        items = db.get_sale_items(sale_id)
        rows = [
            ft.Row([
                ft.Text(it["product_name"], expand=True, size=13, color=ft.Colors.WHITE),
                ft.Text(f'{it["quantity"]:g} {"كجم" if it["unit"] == "كيلو" else "قطعة"}', size=12, color=ft.Colors.WHITE70),
                ft.Text(f'{it["quantity"] * it["unit_price"]:.2f} ج.م', size=12, color=ft.Colors.WHITE),
            ])
            for it in items
        ]
        detail_panel.content = ft.Column(
            [ft.Row([ft.Text(f"تفاصيل فاتورة {serial}", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                     ft.IconButton(ft.Icons.CLOSE, icon_size=16, icon_color=ft.Colors.WHITE, on_click=lambda e: hide_detail())]),
             ft.Divider(color=ft.Colors.WHITE24), *rows]
        )
        detail_panel.visible = True
        page.update()

    def hide_detail():
        detail_panel.visible = False
        page.update()

    def refresh_table():
        if state["search_date"]:
            sales = db.search_sales(state["search_date"])
        else:
            sales = db.get_sales_for_month(state["year"], state["month"])

        month_label.value = f'{ARABIC_MONTHS[state["month"]]} {state["year"]}'
        table.rows.clear()
        total = 0.0
        for s in sales:
            total += s["total"]
            table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(db.invoice_serial(s["id"]), size=12, color=ft.Colors.WHITE)),
                    ft.DataCell(ft.Text(s["created_at"][:16], size=12, color=ft.Colors.WHITE)),
                    ft.DataCell(ft.Text(f'{s["total"]:.2f}', size=12, color=ft.Colors.WHITE)),
                    ft.DataCell(ft.Text(s["payment_type"], size=12, color=ft.Colors.WHITE)),
                    ft.DataCell(ft.TextButton("عرض", style=ft.ButtonStyle(color=ft.Colors.CYAN_200), on_click=lambda e, sid=s["id"]: show_detail(sid))),
                ])
            )
        summary_text.value = f"عدد الفواتير: {len(sales)}   |   إجمالي الشهر: {total:.2f} ج.م"
        page.update()

    prev_btn = ft.IconButton(ft.Icons.ARROW_FORWARD, icon_color=ft.Colors.WHITE, on_click=lambda e: change_month(-1))
    next_btn = ft.IconButton(ft.Icons.ARROW_BACK, icon_color=ft.Colors.WHITE, on_click=lambda e: change_month(1))

    def change_month(delta):
        m = state["month"] + delta
        y = state["year"]
        if m == 0:
            m = 12
            y -= 1
        elif m == 13:
            m = 1
            y += 1
        state["month"] = m
        state["year"] = y
        refresh_table()

    refresh_table()

    return ft.Column(
        [
            ft.Text("جدول الشهر", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            search_field,
            ft.Row([prev_btn, month_label, next_btn], alignment=ft.MainAxisAlignment.CENTER),
            summary_text,
            ft.Container(content=ft.Column([table], scroll=ft.ScrollMode.AUTO), height=350),
            detail_panel,
        ],
        expand=True, scroll=ft.ScrollMode.AUTO,
    )
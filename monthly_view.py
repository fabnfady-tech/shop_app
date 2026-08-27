"""
شاشة جدول الشهر - مصممة خصيصاً لتناسب الشاشات الصغيرة والتابلت بدون ازدحام
"""
import flet as ft
import db
from datetime import date

ARABIC_MONTHS = ["", "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
                  "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]

def MonthlyView(page: ft.Page):
    today = date.today()
    state = {"year": today.year, "month": today.month, "serial_query": "", "day_query": ""}

    month_label = ft.Text("", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    
    serial_search = ft.TextField(
        label="بحث بالسيريال (INV-1)", 
        rtl=True, 
        expand=True,
        text_size=12,
        height=45,
        color=ft.Colors.WHITE,
        label_style=ft.TextStyle(color=ft.Colors.WHITE70, size=11),
        border_color=ft.Colors.WHITE38,
        on_change=lambda e: (state.update(serial_query=e.control.value.strip()), refresh_table()),
    )

    day_search = ft.TextField(
        label="اليوم (مثال: 15)", 
        rtl=True, 
        width=100,
        text_size=12,
        height=45,
        keyboard_type=ft.KeyboardType.NUMBER,
        color=ft.Colors.WHITE,
        label_style=ft.TextStyle(color=ft.Colors.WHITE70, size=11),
        border_color=ft.Colors.WHITE38,
        on_change=lambda e: (state.update(day_query=e.control.value.strip()), refresh_table()),
    )
    
    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("السيريال", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=11)),
            ft.DataColumn(ft.Text("التاريخ", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=11)),
            ft.DataColumn(ft.Text("الإجمالي", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=11)),
            ft.DataColumn(ft.Text("الدفع", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=11)),
            ft.DataColumn(ft.Text("تفاصيل", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=11)),
        ],
        rows=[],
        horizontal_margin=8,
        column_spacing=12,
    )
    
    detail_panel = ft.Container(
        visible=False, 
        padding=8, 
        border_radius=8,
        bgcolor=ft.Colors.BLUE_GREY_900
    )
    
    summary_text = ft.Text("", size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500)

    def show_detail(sale_id):
        serial = db.invoice_serial(sale_id)
        items = db.get_sale_items(sale_id)
        rows = [
            ft.Row([
                ft.Text(it["product_name"], expand=True, size=11, color=ft.Colors.WHITE),
                ft.Text(f'{it["quantity"]:g} {"كجم" if it["unit"] == "كيلو" else "قطعة"}', size=10, color=ft.Colors.WHITE70),
                ft.Text(f'{it["quantity"] * it["unit_price"]:.2f}', size=10, color=ft.Colors.WHITE),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            for it in items
        ]
        detail_panel.content = ft.Column(
            [ft.Row([ft.Text(f"تفاصيل {serial}", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, size=12),
                     ft.IconButton(ft.Icons.CLOSE, icon_size=12, icon_color=ft.Colors.WHITE, on_click=lambda e: hide_detail())],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
             ft.Divider(color=ft.Colors.WHITE24, height=4), *rows],
            tight=True, spacing=4
        )
        detail_panel.visible = True
        page.update()

    def hide_detail():
        detail_panel.visible = False
        page.update()

    def refresh_table():
        sales = db.get_sales_for_month(state["year"], state["month"])
        
        if state["serial_query"]:
            q = state["serial_query"].lower()
            sales = [s for s in sales if q in db.invoice_serial(s["id"]).lower() or q in str(s["id"])]
            
        if state["day_query"]:
            d_str = f"-{int(state['day_query']):02d} "
            sales = [s for s in sales if d_str in s["created_at"] or s["created_at"].startswith(f"{state['year']}-{state['month']:02d}-{int(state['day_query']):02d}")]

        month_label.value = f'{ARABIC_MONTHS[state["month"]]} {state["year"]}'
        table.rows.clear()
        total = 0.0
        for s in sales:
            total += s["total"]
            table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(db.invoice_serial(s["id"]), size=10, color=ft.Colors.WHITE)),
                    ft.DataCell(ft.Text(s["created_at"][5:16], size=10, color=ft.Colors.WHITE)), # إظهار الشير التاريخ/الوقت باختصار لتوفير مساحة
                    ft.DataCell(ft.Text(f'{s["total"]:.1f}', size=10, color=ft.Colors.WHITE)),
                    ft.DataCell(ft.Text(s["payment_type"][:4], size=10, color=ft.Colors.WHITE)),
                    ft.DataCell(ft.TextButton("عرض", style=ft.ButtonStyle(color=ft.Colors.CYAN_200, padding=2), on_click=lambda e, sid=s["id"]: show_detail(sid))),
                ])
            )
        summary_text.value = f"العدد: {len(sales)} | الإجمالي: {total:.2f}"
        page.update()

    prev_btn = ft.IconButton(ft.Icons.ARROW_FORWARD, icon_color=ft.Colors.WHITE, icon_size=16, on_click=lambda e: change_month(-1))
    next_btn = ft.IconButton(ft.Icons.ARROW_BACK, icon_color=ft.Colors.WHITE, icon_size=16, on_click=lambda e: change_month(1))

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
            ft.Text("جدول الشهر", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Row([serial_search, day_search], spacing=4),
            ft.Row([prev_btn, month_label, next_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=0),
            summary_text,
            ft.Container(content=ft.Column([table], scroll=ft.ScrollMode.AUTO), height=260),
            detail_panel,
        ],
        expand=True, scroll=ft.ScrollMode.AUTO, spacing=6,
    )
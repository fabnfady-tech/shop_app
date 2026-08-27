"""
شاشة جدول الشهر - مرتبة ومنسقة بالكامل لتجنب الالتصاق العلوي وتسهيل البحث عن طريق اليوم والسيريال
"""
import flet as ft
import db
from datetime import date

ARABIC_MONTHS = ["", "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
                  "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]

def MonthlyView(page: ft.Page):
    today = date.today()
    state = {"year": today.year, "month": today.month, "serial_query": "", "day_query": ""}

    page_title = ft.Text("جدول الشهر", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    month_label = ft.Text("", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_400)
    
    serial_search = ft.TextField(
        label="بحث برقم الفاتورة (مثال: INV-1)", 
        rtl=True, 
        expand=True,
        text_size=12,
        height=45,
        color=ft.Colors.WHITE,
        label_style=ft.TextStyle(color=ft.Colors.WHITE70, size=11),
        border_color=ft.Colors.WHITE38,
        focused_border_color=ft.Colors.ORANGE_400,
        on_change=lambda e: (state.update(serial_query=e.control.value.strip()), refresh_table()),
    )

    day_search = ft.TextField(
        label="اليوم (مثل: 26)", 
        rtl=True, 
        width=110,
        text_size=12,
        height=45,
        keyboard_type=ft.KeyboardType.NUMBER,
        color=ft.Colors.WHITE,
        label_style=ft.TextStyle(color=ft.Colors.WHITE70, size=11),
        border_color=ft.Colors.WHITE38,
        focused_border_color=ft.Colors.ORANGE_400,
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
        horizontal_margin=6,
        column_spacing=10,
    )
    
    detail_panel = ft.Container(
        visible=False, 
        padding=10, 
        border_radius=10,
        bgcolor=ft.Colors.BLUE_GREY_900,
        border=ft.border.all(1, ft.Colors.WHITE24)
    )
    
    summary_text = ft.Text("", size=12, color=ft.Colors.WHITE70, weight=ft.FontWeight.W_500)

    def show_detail(sale_id):
        serial = db.invoice_serial(sale_id)
        items = db.get_sale_items(sale_id)
        rows = [
            ft.Row([
                ft.Text(it["product_name"], expand=True, size=11, color=ft.Colors.WHITE),
                ft.Text(f'{it["quantity"]:g} {"كجم" if it["unit"] == "كيلو" else "قطعة"}', size=10, color=ft.Colors.WHITE70),
                ft.Text(f'{it["quantity"] * it["unit_price"]:.2f} ج.م', size=10, color=ft.Colors.ORANGE_300),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            for it in items
        ]
        detail_panel.content = ft.Column(
            [
                ft.Row([
                    ft.Text(f"تفاصيل الفاتورة: {serial}", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, size=12),
                    ft.IconButton(ft.Icons.CLOSE, icon_size=14, icon_color=ft.Colors.WHITE, on_click=lambda e: hide_detail())
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(color=ft.Colors.WHITE24, height=4), 
                *rows
            ],
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
            d_val = state["day_query"].zfill(2)
            sales = [s for s in sales if f"-{d_val}" in s["created_at"]]

        month_label.value = f'{ARABIC_MONTHS[state["month"]]} {state["year"]}'
        table.rows.clear()
        total = 0.0
        for s in sales:
            total += s["total"]
            
            raw_date = s["created_at"]
            try:
                date_part, time_part = raw_date.split("T")
                y, m_num, d_num = date_part.split("-")
                formatted_date = f"{d_num} {ARABIC_MONTHS[int(m_num)]} ({time_part[:5]})"
            except:
                formatted_date = raw_date[:16]

            table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(db.invoice_serial(s["id"]), size=10, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(formatted_date, size=10, color=ft.Colors.WHITE70)),
                    ft.DataCell(ft.Text(f'{s["total"]:.2f}', size=10, color=ft.Colors.ORANGE_300, weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(s["payment_type"], size=10, color=ft.Colors.WHITE)),
                    ft.DataCell(ft.TextButton("عرض", style=ft.ButtonStyle(color=ft.Colors.CYAN_200, padding=2), on_click=lambda e, sid=s["id"]: show_detail(sid))),
                ])
            )
        summary_text.value = f"العدد: {len(sales)} فاتورة  |  المبلغ: {total:.2f} ج.م"
        page.update()

    prev_btn = ft.IconButton(ft.Icons.ARROW_FORWARD_IOS, icon_color=ft.Colors.WHITE70, icon_size=14, on_click=lambda e: change_month(-1))
    next_btn = ft.IconButton(ft.Icons.ARROW_BACK_IOS, icon_color=ft.Colors.WHITE70, icon_size=14, on_click=lambda e: change_month(1))

    def change_month(delta):
        m = state["month"] + delta
        y = state["year"]
        if m == 0:
            m = 12
            y -= 1
        elif m == 13:
            m, y = 1, y + 1
        state["month"] = m
        state["year"] = y
        refresh_table()

    refresh_table()

    return ft.Column(
        [
            # مسافة أمان رأسية واضحة تمنع الالتصاق بشريط الموبايل العلوي
            ft.Container(height=10),
            page_title,
            ft.Divider(color=ft.Colors.WHITE12, height=4),
            # حقول البحث مرتبة (سيريال + يوم)
            ft.Row([serial_search, day_search], spacing=6, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            # شريط تصفح الأشهر بتصميم منسق
            ft.Container(
                content=ft.Row([prev_btn, month_label, next_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
                padding=6,
                border_radius=8,
            ),
            summary_text,
            ft.Container(
                content=ft.Column([table], scroll=ft.ScrollMode.AUTO), 
                height=280,
                border=ft.border.all(1, ft.Colors.WHITE12),
                border_radius=8,
                padding=2
            ),
            detail_panel,
        ],
        expand=True, 
        scroll=ft.ScrollMode.AUTO, 
        spacing=8,
    )
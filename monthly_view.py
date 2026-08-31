"""
شاشة جدول الشهر - نظرة عامة على السنة (مربعات لكل شهر) ثم تفاصيل الشهر المختار
"""
import flet as ft
import db
from datetime import date

ARABIC_MONTHS = ["", "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
                 "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]

def MonthlyView(page: ft.Page):
    today = date.today()
    state = {
        "year": today.year,
        "month": today.month,
        "mode": "overview",  # overview = مربعات السنة | detail = جدول شهر معين
        "serial_query": "",
        "day_query": "",
    }

    # ---------------- عناصر عامة ----------------
    page_title = ft.Text("جدول الشهر", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)

    # ---------------- نظرة عامة على السنة (مربعات الشهور) ----------------
    year_label = ft.Text("", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_400)
    overview_grid = ft.GridView(expand=True, max_extent=150, child_aspect_ratio=1.05, spacing=10, run_spacing=10)
    year_total_text = ft.Text("", size=13, color=ft.Colors.WHITE70)

    year_summary_cache = {}

    def month_tile(m):
        summary = year_summary_cache.get(m, {"count": 0, "total": 0.0})
        is_current = (m == today.month and state["year"] == today.year)
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(ARABIC_MONTHS[m], size=15, weight=ft.FontWeight.BOLD,
                            color=ft.Colors.ORANGE_400 if is_current else ft.Colors.WHITE),
                    ft.Text(f'{summary["count"]} فاتورة', size=11, color=ft.Colors.WHITE70),
                    ft.Text(f'{summary["total"]:.2f} ج.م', size=13, weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREEN_300),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=4,
            ),
            padding=10, border_radius=14, alignment=ft.Alignment.CENTER,
            bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.ORANGE_700) if is_current else ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
            border=ft.Border.all(1.5, ft.Colors.ORANGE_400 if is_current else ft.Colors.WHITE24),
            on_click=lambda e, m=m: open_month_detail(m),
        )

    def refresh_overview():
        year_summary_cache.clear()
        year_summary_cache.update(db.get_year_summary(state["year"]))
        year_label.value = str(state["year"])
        overview_grid.controls.clear()
        for m in range(1, 13):
            overview_grid.controls.append(month_tile(m))
        year_total = sum(v["total"] for v in year_summary_cache.values())
        year_count = sum(v["count"] for v in year_summary_cache.values())
        year_total_text.value = f"إجمالي السنة: {year_count} فاتورة  |  {year_total:.2f} ج.م"
        page.update()

    def change_year(delta):
        state["year"] += delta
        refresh_overview()

    prev_year_btn = ft.IconButton(ft.Icons.ARROW_FORWARD_IOS, icon_color=ft.Colors.WHITE70, icon_size=14,
                                    on_click=lambda e: change_year(-1))
    next_year_btn = ft.IconButton(ft.Icons.ARROW_BACK_IOS, icon_color=ft.Colors.WHITE70, icon_size=14,
                                    on_click=lambda e: change_year(1))

    overview_panel = ft.Column(
        [
            ft.Container(
                content=ft.Row([prev_year_btn, year_label, next_year_btn],
                                alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.WHITE), padding=6, border_radius=8,
            ),
            year_total_text,
            ft.Container(content=overview_grid, expand=True, height=420),
        ],
        spacing=10, visible=True,
    )

    # ---------------- تفاصيل شهر معين ----------------
    month_label = ft.Text("", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_400)

    serial_search = ft.TextField(
        label="بحث برقم الفاتورة (مثال: INV-00001)",
        rtl=True, expand=True, text_size=12, height=45,
        color=ft.Colors.WHITE, label_style=ft.TextStyle(color=ft.Colors.WHITE70, size=11),
        border_color=ft.Colors.WHITE38, focused_border_color=ft.Colors.ORANGE_400,
        on_change=lambda e: (state.update(serial_query=e.control.value.strip()), refresh_table()),
    )

    day_search = ft.TextField(
        label="اليوم (مثل: 26)",
        rtl=True, width=110, text_size=12, height=45,
        keyboard_type=ft.KeyboardType.NUMBER,
        color=ft.Colors.WHITE, label_style=ft.TextStyle(color=ft.Colors.WHITE70, size=11),
        border_color=ft.Colors.WHITE38, focused_border_color=ft.Colors.ORANGE_400,
        on_change=lambda e: (state.update(day_query=e.control.value.strip()), refresh_table()),
    )

    # تعديل الأعمدة لإضافة عمود "الدليفري"
    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("السيريال", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=11)),
            ft.DataColumn(ft.Text("التاريخ", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=11)),
            ft.DataColumn(ft.Text("الإجمالي", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=11)),
            ft.DataColumn(ft.Text("الدليفري", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=11)),
            ft.DataColumn(ft.Text("الدفع", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=11)),
            ft.DataColumn(ft.Text("تفاصيل", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=11)),
        ],
        rows=[], horizontal_margin=6, column_spacing=8,
    )

    detail_panel = ft.Container(
        visible=False, padding=10, border_radius=10,
        bgcolor=ft.Colors.BLUE_GREY_900, border=ft.Border.all(1, ft.Colors.WHITE24),
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

        if state["day_query"] and state["day_query"].isdigit():
            target_day = int(state["day_query"])
            filtered_sales = []
            for s in sales:
                try:
                    dt_str = s["created_at"].split("T")[0]
                    d_num = int(dt_str.split("-")[2])
                    if d_num == target_day:
                        filtered_sales.append(s)
                except Exception:
                    pass
            sales = filtered_sales

        month_label.value = f'{ARABIC_MONTHS[state["month"]]} {state["year"]}'
        table.rows.clear()
        total = 0.0
        for s_row in sales:
            s = dict(s_row)
            total += s["total"]

            raw_date = s["created_at"]
            try:
                date_part, time_part = raw_date.split("T")
                y, m_num, d_num = date_part.split("-")
                formatted_date = f"{int(d_num)} {ARABIC_MONTHS[int(m_num)]} ({time_part[:5]})"
            except Exception:
                formatted_date = raw_date[:16]

            # تجهيز طريقة الدفع الأساسية
            payment_type = s.get("payment_type", "نقدي")
            paid = s.get("paid", True)
            paid_amount = s.get("paid_amount", 0)
            
            payment_label = payment_type
            if payment_type == "آجل" and not paid:
                payment_label = f'آجل ({paid_amount:.0f}/{s["total"]:.0f})'

            # جلب حالة أو نوع الدليفري
            delivery_status = s.get("delivery_status") or s.get("delivery_type") or "توصيل"

            # دمج الدليفري وبجانبه طريقة الدفع بين قوسين
            delivery_val = f"{delivery_status} ({payment_label})"

# إزالة عمود الدليفري وإبقاء الأعمدة الأساسية
    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("السيريال", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=11)),
            ft.DataColumn(ft.Text("التاريخ", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=11)),
            ft.DataColumn(ft.Text("الإجمالي", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=11)),
            ft.DataColumn(ft.Text("الدفع", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=11)),
            ft.DataColumn(ft.Text("تفاصيل", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=11)),
        ],
        rows=[], horizontal_margin=6, column_spacing=10,
    )

    def refresh_table():
        sales = db.get_sales_for_month(state["year"], state["month"])

        if state["serial_query"]:
            q = state["serial_query"].lower()
            sales = [s for s in sales if q in db.invoice_serial(s["id"]).lower() or q in str(s["id"])]

        if state["day_query"] and state["day_query"].isdigit():
            target_day = int(state["day_query"])
            filtered_sales = []
            for s in sales:
                try:
                    dt_str = s["created_at"].split("T")[0]
                    d_num = int(dt_str.split("-")[2])
                    if d_num == target_day:
                        filtered_sales.append(s)
                except Exception:
                    pass
            sales = filtered_sales

        month_label.value = f'{ARABIC_MONTHS[state["month"]]} {state["year"]}'
        table.rows.clear()
        total = 0.0
        for s_row in sales:
            s = dict(s_row)
            total += s["total"]

            raw_date = s["created_at"]
            try:
                date_part, time_part = raw_date.split("T")
                y, m_num, d_num = date_part.split("-")
                formatted_date = f"{int(d_num)} {ARABIC_MONTHS[int(m_num)]} ({time_part[:5]})"
            except Exception:
                formatted_date = raw_date[:16]

            # جلب طريقة الدفع الصحيحة وتجنب أن تكون كلمة "دليفري" هي طريقة الدفع نفسها
            payment_type = s.get("payment_type", "نقدي")
            if not payment_type or payment_type == "دليفري":
                payment_type = "نقدي"

            paid = s.get("paid", True)
            paid_amount = s.get("paid_amount", 0)
            
            payment_label = payment_type
            if payment_type == "آجل" and not paid:
                payment_label = f'آجل ({paid_amount:.0f}/{s["total"]:.0f})'

            # التحقق مما إذا كانت الفاتورة دليفري لإضافة الكلمة بجانب طريقة الدفع الفعلية فقط
            delivery_status = s.get("delivery_status") or s.get("delivery_type")
            if delivery_status:
                payment_label = f"{payment_label} (دليفري)"

            table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(db.invoice_serial(s["id"]), size=10, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(formatted_date, size=10, color=ft.Colors.WHITE70)),
                    ft.DataCell(ft.Text(f'{s["total"]:.2f}', size=10, color=ft.Colors.ORANGE_300, weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(payment_label, size=10, color=ft.Colors.WHITE)),
                    ft.DataCell(ft.TextButton("عرض", style=ft.ButtonStyle(color=ft.Colors.CYAN_200, padding=2), on_click=lambda e, sid=s["id"]: show_detail(sid))),
                ])
            )
        summary_text.value = f"العدد: {len(sales)} فاتورة  |  المبلغ: {total:.2f} ج.م"
        page.update()
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

    prev_btn = ft.IconButton(ft.Icons.ARROW_FORWARD_IOS, icon_color=ft.Colors.WHITE70, icon_size=14, on_click=lambda e: change_month(-1))
    next_btn = ft.IconButton(ft.Icons.ARROW_BACK_IOS, icon_color=ft.Colors.WHITE70, icon_size=14, on_click=lambda e: change_month(1))

    def back_to_overview(e=None):
        state["mode"] = "overview"
        overview_panel.visible = True
        detail_panel_wrapper.visible = False
        page_title.value = "جدول الشهر"
        refresh_overview()

    back_btn = ft.TextButton("◀ رجوع لكل الشهور", icon=ft.Icons.ARROW_BACK, on_click=back_to_overview)

    detail_panel_wrapper = ft.Column(
        [
            back_btn,
            ft.Row([serial_search, day_search], spacing=6, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(
                content=ft.Row([prev_btn, month_label, next_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.WHITE), padding=6, border_radius=8,
            ),
            summary_text,
            ft.Container(
                content=ft.Column([table], scroll=ft.ScrollMode.AUTO),
                height=280, border=ft.Border.all(1, ft.Colors.WHITE12), border_radius=8, padding=2,
            ),
            detail_panel,
        ],
        spacing=8, visible=False,
    )

    def open_month_detail(m):
        state["month"] = m
        state["mode"] = "detail"
        state["serial_query"] = ""
        state["day_query"] = ""
        serial_search.value = ""
        day_search.value = ""
        page_title.value = f"جدول شهر {ARABIC_MONTHS[m]}"
        overview_panel.visible = False
        detail_panel_wrapper.visible = True
        refresh_table()

    refresh_overview()

    return ft.Column(
        [
            ft.Container(height=10),
            page_title,
            ft.Divider(color=ft.Colors.WHITE12, height=4),
            overview_panel,
            detail_panel_wrapper,
        ],
        expand=True, scroll=ft.ScrollMode.AUTO, spacing=8,
    )
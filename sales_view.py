"""
شاشة البيع - Aleefy Pets
عرض اللوجو الأصلي بنقاء ووضوح وبدون حواف مربعة
"""
import flet as ft
import db
from datetime import datetime
import os
import tempfile
from fpdf import FPDF
import arabic_reshaper
from bidi.algorithm import get_display

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "amiri-regular.ttf")


def get_logo_path():
    possible_names = ["logo.png", "logo.jpg", "logo.jpeg", "bg_logo.png", "bg_logo.jpg"]
    for name in possible_names:
        full_path = os.path.join(BASE_DIR, name)
        if os.path.exists(full_path):
            return full_path
    return None


def ar(text):
    reshaped_text = arabic_reshaper.reshape(str(text))
    return get_display(reshaped_text)


def print_invoice_pdf(page, inv_number, date_str, items, discount, total, payment_type):
    try:
        pdf = FPDF(format=(80, 160))
        pdf.add_page()
        logo_path = get_logo_path()

        if logo_path:
            pdf.image(logo_path, x=20, y=5, w=40)
            pdf.ln(25)

        if os.path.exists(FONT_PATH):
            pdf.add_font("Amiri", "", FONT_PATH)
            pdf.set_font("Amiri", size=10)
        else:
            pdf.set_font("Arial", size=10)

        pdf.cell(60, 6, txt="Aleefy Pets", ln=True, align="C")
        pdf.cell(60, 5, txt=ar("أليفي بيتس لرعاية الحيوانات"), ln=True, align="C")
        pdf.cell(60, 5, txt="--------------------------------", ln=True, align="C")
        pdf.cell(60, 5, txt=ar(f"رقم الفاتورة: {inv_number}"), ln=True, align="R")
        pdf.cell(60, 5, txt=ar(f"التاريخ: {date_str}"), ln=True, align="R")
        pdf.cell(60, 5, txt=ar(f"طريقة الدفع: {payment_type}"), ln=True, align="R")
        pdf.cell(60, 5, txt="--------------------------------", ln=True, align="C")

        for item in items:
            name = item.get("product_name") or item.get("name", "")
            qty = item.get("quantity") or item.get("qty", 1)
            price = item.get("unit_price") or item.get("price", 0.0)
            unit_str = "كجم" if item.get("unit") == "كيلو" else "قطعة"

            line = f"{name} x{qty:g} {unit_str} - {qty * price:.2f}"
            pdf.cell(60, 5, txt=ar(line), ln=True, align="R")

        pdf.cell(60, 5, txt="--------------------------------", ln=True, align="C")
        pdf.cell(60, 5, txt=ar(f"الخصم: {discount:.2f} ج.م"), ln=True, align="R")
        pdf.cell(60, 6, txt=ar(f"الإجمالي: {total:.2f} ج.م"), ln=True, align="R")

        temp_path = os.path.join(tempfile.gettempdir(), f"invoice_{inv_number}.pdf")
        pdf.output(temp_path)
        page.launch_url(f"file://{temp_path}")
    except Exception as ex:
        print(f"خطأ أثناء إنشاء الفاتورة: {ex}")


CATEGORY_ICONS = {
    "طعام": "🍖",
    "إكسسوارات": "🎀",
    "أدوية وعناية": "💊",
    "ألعاب": "🧸",
    "نظافة": "🧴",
    "حيوانات": "🐾",
    "زواحف": "🦎",
    "طيور": "🐦",
    "اسماك": "🐟",
}


def category_icon(cat):
    return CATEGORY_ICONS.get(cat, "🐾")


def SalesView(page: ft.Page):
    cart = {}
    state = {"category": "الكل", "search": ""}
    logo_path = get_logo_path()

    search_field = ft.TextField(
        hint_text="ابحث عن منتج بالاسم...",
        hint_style=ft.TextStyle(color=ft.Colors.GREY_600, size=13),
        rtl=True,
        prefix=ft.Icon(ft.Icons.SEARCH, color=ft.Colors.ORANGE_700),
        border_radius=10,
        bgcolor=ft.Colors.WHITE,
        color=ft.Colors.BLACK,
        border_color=ft.Colors.ORANGE_400,
        focused_border_color=ft.Colors.ORANGE_600,
        height=45,
        content_padding=10,
        on_change=lambda e: (state.update(search=e.control.value), refresh_grid()),
    )

    chips_row = ft.Row(spacing=8, scroll=ft.ScrollMode.AUTO)
    products_grid = ft.GridView(
        expand=True, max_extent=150, child_aspect_ratio=0.82, spacing=10, run_spacing=10
    )

    cart_list = ft.Column(spacing=6)

    discount_field = ft.TextField(
        hint_text="الخصم (ج.م)",
        hint_style=ft.TextStyle(color=ft.Colors.GREY_600, size=12),
        value="0",
        rtl=True,
        keyboard_type=ft.KeyboardType.NUMBER,
        width=140,
        border_radius=10,
        bgcolor=ft.Colors.WHITE,
        color=ft.Colors.BLACK,
        border_color=ft.Colors.ORANGE_400,
        focused_border_color=ft.Colors.ORANGE_600,
        height=42,
        content_padding=10,
        on_change=lambda e: refresh_cart()
    )

    subtotal_text = ft.Text("", size=13, color=ft.Colors.WHITE)
    total_text = ft.Text("الإجمالي: 0.00 ج.م", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_400)

    payment_type_radio = ft.RadioGroup(
        content=ft.Row([
            ft.Radio(value="نقدي", label="نقدي 💵", fill_color=ft.Colors.ORANGE_400),
            ft.Radio(value="محفظة", label="محفظة 📱", fill_color=ft.Colors.ORANGE_400),
            ft.Radio(value="آجل", label="آجل 📝", fill_color=ft.Colors.ORANGE_400),
        ], alignment=ft.MainAxisAlignment.START, spacing=15),
        value="نقدي",
        on_change=lambda e: toggle_payment_type()
    )

    customer_name_field = ft.TextField(
        hint_text="اسم العميل",
        hint_style=ft.TextStyle(color=ft.Colors.GREY_600, size=12),
        rtl=True, visible=False, border_radius=10, bgcolor=ft.Colors.WHITE,
        color=ft.Colors.BLACK, border_color=ft.Colors.ORANGE_400, height=42, content_padding=10
    )
    customer_phone_field = ft.TextField(
        hint_text="رقم التليفون",
        hint_style=ft.TextStyle(color=ft.Colors.GREY_600, size=12),
        rtl=True, visible=False, border_radius=10, bgcolor=ft.Colors.WHITE,
        color=ft.Colors.BLACK, border_color=ft.Colors.ORANGE_400, height=42, content_padding=10,
        keyboard_type=ft.KeyboardType.NUMBER
    )
    status_text = ft.Text("", color=ft.Colors.RED_300, weight=ft.FontWeight.BOLD)

    pos_view = ft.Column(expand=True)
    invoice_view = ft.Column(expand=True, visible=False)

    def refresh_chips():
        chips_row.controls.clear()
        for cat, count in db.get_category_counts():
            chips_row.controls.append(
                ft.Chip(
                    label=ft.Text(f"{cat} ({count})", size=12, weight=ft.FontWeight.W_600),
                    selected=(cat == state["category"]),
                    selected_color=ft.Colors.ORANGE_500,
                    on_click=lambda e, c=cat: select_category(c),
                )
            )

    def select_category(c):
        state["category"] = c
        refresh_chips()
        refresh_grid()

    def refresh_grid():
        products_grid.controls.clear()
        items = db.get_products(search=state["search"], category=state["category"])
        if not items:
            products_grid.controls.append(ft.Text("مفيش منتجات مطابقة", color=ft.Colors.WHITE70))
        for p in items:
            products_grid.controls.append(product_card(p))
        page.update()

    def product_card(p):
        out_of_stock = p["stock"] <= 0
        unit_label = "كجم" if p["unit"] == "كيلو" else "قطعة"

        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Text(category_icon(p["category"]), size=28),
                        padding=8, bgcolor=ft.Colors.ORANGE_50, border_radius=50,
                    ),
                    ft.Text(p["name"], size=13, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER, max_lines=2, color=ft.Colors.BLACK),
                    ft.Text(f'{p["price"]:.2f} ج.م', size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                    ft.Text(
                        "خلص من المخزون" if out_of_stock else f'متاح: {p["stock"]:g} {unit_label}',
                        size=10, weight=ft.FontWeight.W_600,
                        color=ft.Colors.RED_600 if out_of_stock else ft.Colors.GREY_700,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=4,
            ),
            padding=10, border_radius=16, alignment=ft.Alignment.CENTER,
            bgcolor=ft.Colors.GREY_300 if out_of_stock else ft.Colors.WHITE,
            shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK), offset=ft.Offset(0, 2)),
            on_click=None if out_of_stock else (lambda e, p=p: add_to_cart(p)),
        )

    def add_to_cart(p):
        pid = p["id"]
        step = 1.0
        if pid in cart:
            new_qty = cart[pid]["qty"] + step
            if new_qty <= p["stock"]:
                cart[pid]["qty"] = new_qty
        else:
            cart[pid] = {
                "name": p["name"], "price": p["price"],
                "qty": min(step, p["stock"]), "unit": p["unit"],
                "stock": p["stock"]
            }
        refresh_cart()

    def change_qty(pid, delta):
        if pid not in cart:
            return
        cart[pid]["qty"] = round(cart[pid]["qty"] + delta, 2)
        if cart[pid]["qty"] <= 0:
            del cart[pid]
        elif cart[pid]["qty"] > cart[pid]["stock"]:
            cart[pid]["qty"] = cart[pid]["stock"]
        refresh_cart()

    def refresh_cart():
        cart_list.controls.clear()
        subtotal = 0.0
        for pid, item in cart.items():
            line_total = item["price"] * item["qty"]
            subtotal += line_total
            step = 1 if item["unit"] == "قطعة" else 0.25
            qty_label = f'{item["qty"]:g} {"كجم" if item["unit"] == "كيلو" else "قطعة"}'
            cart_list.controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(item["name"], expand=True, size=13, weight=ft.FontWeight.W_600, color=ft.Colors.BLACK),
                            ft.IconButton(ft.Icons.REMOVE_CIRCLE_OUTLINE, icon_size=20, icon_color=ft.Colors.RED_600,
                                          on_click=lambda e, pid=pid, s=step: change_qty(pid, -s)),
                            ft.Text(qty_label, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                            ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINE, icon_size=20, icon_color=ft.Colors.GREEN_700,
                                          on_click=lambda e, pid=pid, s=step: change_qty(pid, s)),
                            ft.Text(f"{line_total:.2f} ج.م", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                        ]
                    ),
                    padding=8, bgcolor=ft.Colors.WHITE, border_radius=8,
                )
            )
        try:
            discount = float(discount_field.value) if discount_field.value else 0.0
        except ValueError:
            discount = 0.0
        discount = max(0.0, min(discount, subtotal))
        total = subtotal - discount

        subtotal_text.value = f"الإجمالي الفرعي: {subtotal:.2f} ج.م" + (f"   |   الخصم: {discount:.2f} ج.م" if discount else "")
        total_text.value = f"الإجمالي: {total:.2f} ج.م"
        checkout_btn.disabled = len(cart) == 0
        page.update()

    def toggle_payment_type():
        is_deferred = (payment_type_radio.value == "آجل")
        customer_name_field.visible = is_deferred
        customer_phone_field.visible = is_deferred
        page.update()

    def checkout(e):
        status_text.value = ""
        if not cart:
            return
        payment_type = payment_type_radio.value
        if payment_type == "آجل":
            if not customer_name_field.value or not customer_phone_field.value:
                status_text.value = "البيع الآجل محتاج اسم العميل ورقم تليفونه"
                page.update()
                return

        try:
            discount = float(discount_field.value) if discount_field.value else 0.0
        except ValueError:
            discount = 0.0

        items = [
            {"product_id": pid, "product_name": item["name"], "quantity": item["qty"],
             "unit": item["unit"], "unit_price": item["price"]}
            for pid, item in cart.items()
        ]
        sale_id, total = db.create_sale(
            items, discount, payment_type,
            customer_name_field.value if payment_type == "آجل" else None,
            customer_phone_field.value if payment_type == "آجل" else None,
        )

        show_invoice(sale_id, items, discount, total, payment_type)

        cart.clear()
        discount_field.value = "0"
        payment_type_radio.value = "نقدي"
        customer_name_field.value = ""
        customer_phone_field.value = ""
        customer_name_field.visible = False
        customer_phone_field.visible = False
        refresh_grid()
        refresh_cart()

    checkout_btn = ft.ElevatedButton(
        "إتمام عملية البيع 🛒", icon=ft.Icons.CHECK_CIRCLE,
        bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE,
        disabled=True, on_click=checkout,
        style=ft.ButtonStyle(padding=15, shape=ft.RoundedRectangleBorder(radius=12))
    )

    def show_invoice(sale_id, items, discount, total, payment_type):
        serial = db.invoice_serial(sale_id)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        rows = [
            ft.Row([
                ft.Text(it["product_name"], expand=True, size=13, color=ft.Colors.BLACK),
                ft.Text(f'{it["quantity"]:g} {"كجم" if it["unit"] == "كيلو" else "قطعة"}', size=12, color=ft.Colors.BLACK),
                ft.Text(f'{it["quantity"] * it["unit_price"]:.2f} ج.م', size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
            ])
            for it in items
        ]
        invoice_view.controls = [
            ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_400, size=30),
                    ft.Text("تمت عملية البيع بنجاح 🎉", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)]),
            ft.Container(
                padding=20, border_radius=16, bgcolor=ft.Colors.WHITE,
                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK), offset=ft.Offset(0, 4)),
                content=ft.Column(
                    [
                        ft.Row([ft.Text("رقم الفاتورة", color=ft.Colors.GREY_700), ft.Text(serial, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)]),
                        ft.Row([ft.Text("التاريخ والوقت", color=ft.Colors.GREY_700), ft.Text(now_str, color=ft.Colors.BLACK)]),
                        ft.Row([ft.Text("طريقة الدفع", color=ft.Colors.GREY_700), ft.Text(payment_type, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700)]),
                        ft.Divider(),
                        *rows,
                        ft.Divider(),
                        ft.Row([ft.Text("الخصم", color=ft.Colors.GREY_700), ft.Text(f"{discount:.2f} ج.م", color=ft.Colors.BLACK)]),
                        ft.Row([ft.Text("الإجمالي", weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.BLACK),
                                ft.Text(f"{total:.2f} ج.م", weight=ft.FontWeight.BOLD, size=18, color=ft.Colors.GREEN_800)]),
                    ]
                ),
            ),
            ft.Container(height=10),
            ft.Row([
                ft.ElevatedButton(
                    "طباعة الفاتورة 🖨️", icon=ft.Icons.PRINT,
                    bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE,
                    style=ft.ButtonStyle(padding=15, shape=ft.RoundedRectangleBorder(radius=10)),
                    on_click=lambda e: print_invoice_pdf(page, serial, now_str, items, discount, total, payment_type),
                ),
                ft.ElevatedButton(
                    "بيع جديد 🛒", icon=ft.Icons.ADD_SHOPPING_CART,
                    bgcolor=ft.Colors.ORANGE_700, color=ft.Colors.WHITE,
                    style=ft.ButtonStyle(padding=15, shape=ft.RoundedRectangleBorder(radius=10)),
                    on_click=lambda e: new_sale(),
                ),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
        ]
        pos_view.visible = False
        invoice_view.visible = True
        page.update()

    def new_sale():
        pos_view.visible = True
        invoice_view.visible = False
        page.update()

    refresh_chips()
    refresh_grid()
    refresh_cart()

    # شريط العنوان العلوي - إظهار اللوجو بوضوح وارتفاع مناسب 65 بكسل
    header_bar = ft.Row(
        [
            ft.Row([
                ft.Image(
                    src=logo_path,
                    height=65,
                    fit="contain",
                ) if logo_path else ft.Icon(ft.Icons.PETS, color=ft.Colors.ORANGE_400, size=36),
                ft.Text("Aleefy Pets", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ], spacing=15, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Text("نقطة البيع 🐾", size=16, color=ft.Colors.ORANGE_300, weight=ft.FontWeight.W_600),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    pos_view.controls = [
        header_bar,
        search_field,
        chips_row,
        ft.Container(content=products_grid, height=310),
        ft.Divider(color=ft.Colors.WHITE24),
        ft.Text("السلة", weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.WHITE),
        cart_list,
        ft.Row([discount_field]),
        subtotal_text,
        total_text,
        ft.Text("طريقة الدفع:", weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
        payment_type_radio,
        ft.Row([customer_name_field, customer_phone_field]),
        checkout_btn,
        status_text,
    ]

    return ft.Container(
        content=ft.Column([pos_view, invoice_view], expand=True, scroll=ft.ScrollMode.AUTO),
        padding=12,
        expand=True,
    )
"""
شاشة البيع - Aleefy Pets
"""
import flet as ft
import db
from datetime import datetime
import os
import tempfile
import re
import socket
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import base64
from io import BytesIO


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FONT_REGULAR_CANDIDATES = ["amiri-regular.ttf", "Amiri-Regular.ttf", "AmiriQuran-Regular.ttf"]
FONT_PATH = next(
    (os.path.join(BASE_DIR, name) for name in FONT_REGULAR_CANDIDATES
     if os.path.exists(os.path.join(BASE_DIR, name))),
    os.path.join(BASE_DIR, "amiri-regular.ttf")
)

FONT_BOLD_CANDIDATES = ["amiri-bold.ttf", "Amiri-Bold.ttf", "AmiriQuran-Bold.ttf"]
FONT_BOLD_PATH = next(
    (os.path.join(BASE_DIR, name) for name in FONT_BOLD_CANDIDATES
     if os.path.exists(os.path.join(BASE_DIR, name))),
    None
)

PRINTER_WIDTH_PX = 576
BW_THRESHOLD = 205

SHOP_NAME = "Aleefy Pets"
SHOP_NAME_AR = "أليفي بيتس لرعاية الحيوانات"
SHOP_ADDRESS = "سيتي بارك مول - قطاع د - زهراء أكتوبر"
SHOP_WHATSAPP = "01129062463"
SHOP_PHONES = ["01001422096", "01157440596"]


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


def parse_stored_address(address_str):
    if not address_str:
        return "", "", ""

    sector = ""
    building = ""
    apartment = ""

    parts = [p.strip() for p in address_str.split("-") if p.strip()]

    for part in parts:
        if "القطاع" in part or "المنطقة" in part:
            sector = re.sub(r'^(القطاع/المنطقة|القطاع|المنطقة)\s*[:/]?\s*', '', part).strip()
        elif "عمارة" in part:
            building = re.sub(r'^عمارة\s*[:/]?\s*', '', part).strip()
        elif "شقة" in part:
            apartment = re.sub(r'^شقة\s*[:/]?\s*', '', part).strip()

    if not sector and not building and not apartment:
        sector = address_str.strip()

    return sector, building, apartment


def generate_invoice_image(inv_number, date_str, items, discount, delivery_fee, total, payment_type, is_delivery, customer_name="", customer_phone="", customer_address=""):
    width = PRINTER_WIDTH_PX
    padding = 20
    
    font_regular = None
    font_bold = None
    font_title = None

    font_sources = [
        FONT_PATH,
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\tahoma.ttf"
    ]

    for font_p in font_sources:
        if font_p and os.path.exists(font_p):
            try:
                font_regular = ImageFont.truetype(font_p, 28)
                font_bold = ImageFont.truetype(font_p, 34)
                font_title = ImageFont.truetype(font_p, 42)
                break
            except Exception:
                continue

    if not font_regular:
        font_regular = font_bold = font_title = ImageFont.load_default()

    if FONT_BOLD_PATH:
        try:
            font_bold = ImageFont.truetype(FONT_BOLD_PATH, 34)
            font_title = ImageFont.truetype(FONT_BOLD_PATH, 42)
        except Exception:
            pass

    img_temp = Image.new("RGB", (width, 3000), "white")
    draw = ImageDraw.Draw(img_temp)
    
    y = 25

    # هذه الدالة هي الأهم: تقوم بتصغير حجم الخط تلقائياً إذا كان النص طويلاً، وترسم العربي بالشكل الصحيح
    def draw_text(text, font, align="center", fill="black", spacing=46, stroke=0):
        nonlocal y
        text_ar = ar(text)
        # نضبط الحجم تلقائياً لو النص طويل
        while font.size > 10:
            bbox = draw.textbbox((0, 0), text_ar, font=font, stroke_width=stroke)
            w = bbox[2] - bbox[0]
            if w > (width - padding * 2):
                font = font.font_variant(size=font.size - 1)
            else:
                break

        bbox = draw.textbbox((0, 0), text_ar, font=font, stroke_width=stroke)
        w = bbox[2] - bbox[0]
        
        if align == "center":
            x = (width - w) // 2
        elif align == "right":
            x = width - padding - w
        else:
            x = padding

        draw.text((x, y), text_ar, fill=fill, font=font, stroke_width=stroke, stroke_fill=fill)
        y += spacing

    def draw_line(dash=False):
        nonlocal y
        if dash:
            for x in range(padding, width - padding, 14):
                draw.line([(x, y), (x + 7, y)], fill="black", width=2)
        else:
            draw.line([(padding, y), (width - padding, y)], fill="black", width=3)
        y += 20

    logo_path = get_logo_path()
    if logo_path:
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((200, 200))
            logo_x = (width - logo.width) // 2
            img_temp.paste(logo, (logo_x, y), logo)
            y += logo.height + 20
        except Exception as e:
            print(f"خطأ في إضافة اللوجو: {e}")

    draw_text(SHOP_NAME, font_title, align="center", spacing=52)
    draw_text(SHOP_NAME_AR, font_bold, align="center", spacing=46)
    draw_text(SHOP_ADDRESS, font_regular, align="center", spacing=40)
    draw_text(f"واتساب: {SHOP_WHATSAPP}", font_regular, align="center", spacing=40)
    draw_text("مكالمات: " + " - ".join(SHOP_PHONES), font_regular, align="center", spacing=40)
    
    draw_line()

    draw_text(f"رقم الفاتورة: {inv_number}", font_bold, align="right", spacing=46)
    draw_text(f"التاريخ: {date_str}", font_regular, align="right", spacing=40)
    draw_text(f"طريقة الدفع: {payment_type}", font_regular, align="right", spacing=40)
    
    if is_delivery:
        draw_text("نوع الطلب: دليفري", font_regular, align="right", spacing=40)
        if customer_name:
            draw_text(f"العميل: {customer_name}", font_regular, align="right", spacing=40)
        if customer_phone:
            draw_text(f"التليفون: {customer_phone}", font_regular, align="right", spacing=40)
        if customer_address:
            draw_text(f"العنوان: {customer_address}", font_bold, align="right", spacing=46)
    else:
        draw_text("نوع الطلب: استلام من الفرع", font_regular, align="right", spacing=40)
    
    draw_line(dash=True)

    for item in items:
     name = item.get("product_name") or item.get("name", "")
     qty = item.get("quantity") or item.get("qty", 1)
     price = item.get("unit_price") or item.get("price", 0.0)

     unit_str = " كجم" if item.get("unit") == "كيلو" else ""
     line_total = qty * price

     draw_text(name, font_bold, align="right", spacing=42)

     detail_txt = f"{qty:g}{unit_str} × {price:.2f}"
     amount_txt = f"{line_total:.2f} ج.م"

     amount_ar = ar(amount_txt)
     detail_ar = ar(detail_txt)

    # المبلغ على الشمال
     draw.text((padding, y), amount_ar, fill="black", font=font_regular)

    # الكمية × السعر على اليمين
     bbox = draw.textbbox((0, 0), detail_ar, font=font_regular)
     detail_w = bbox[2] - bbox[0]
     draw.text((width - padding - detail_w, y), detail_ar, fill="black", font=font_regular)

     y += 48

    draw_line(dash=True)

    def draw_total_row(label, value, is_bold=False):
        nonlocal y
        f = font_bold if is_bold else font_regular
        val_str = f"{value:.2f} ج.م"
        draw.text((padding, y), ar(val_str), fill="black", font=f)
        
        bbox = draw.textbbox((0, 0), ar(label), font=f)
        draw.text((width - padding - (bbox[2] - bbox[0]), y), ar(label), fill="black", font=f)
        y += 50

    subtotal = sum((it.get("quantity") or it.get("qty", 1)) * (it.get("unit_price") or it.get("price", 0.0)) for it in items)
    draw_total_row("الإجمالي الفرعي", subtotal)
    
    if discount:
        draw_total_row("الخصم", -discount)
    if delivery_fee:
        draw_total_row("رسوم التوصيل", delivery_fee)

    draw_line()
    draw_total_row("الإجمالي النهائي", total, is_bold=True)
    draw_line()

    draw_text("شكرا لتعاملكم معنا", font_bold, align="center", spacing=46)
    draw_text("Aleefy Pets - أليفي بيتس", font_regular, align="center", spacing=40)
    y += 25

    final_img = img_temp.crop((0, 0, width, y))
    
    temp_img_path = os.path.join(tempfile.gettempdir(), f"invoice_{inv_number}.png")
    final_img.save(temp_img_path)
    return temp_img_path, final_img

def send_to_rawbt_wifi(final_img, rawbt_ip="127.0.0.1", port=9100, printer_width=PRINTER_WIDTH_PX):
    try:
        w_percent = printer_width / float(final_img.width)
        h_size = int(float(final_img.height) * float(w_percent))
        resized_img = final_img.resize((printer_width, h_size), Image.Resampling.LANCZOS)

        gray_img = resized_img.convert("L")
        bw_img = gray_img.point(lambda x: 0 if x < BW_THRESHOLD else 255, "1")

        width, height = bw_img.size
        width_bytes = (width + 7) // 8

        pixels = bw_img.load()

        cmd = bytearray([
            0x1B, 0x40,
            0x1D, 0x76, 0x30, 0x00,
            width_bytes % 256, width_bytes // 256,
            height % 256, height // 256
        ])

        for y in range(height):
            for x_byte in range(width_bytes):
                byte_val = 0
                for bit in range(8):
                    x = x_byte * 8 + bit
                    if x < width:
                        if pixels[x, y] == 0:
                            byte_val |= (1 << (7 - bit))
                cmd.append(byte_val)

        cmd.extend([0x1B, 0x64, 0x04])

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect((rawbt_ip, port))
            s.sendall(cmd)
            
        return True, "تمت الطباعة بنجاح! 🖨️"
    except Exception as ex:
        return False, f"تأكد من تفعيل Socket Server في RawBT: {ex}"


def save_invoice_image(page, inv_number, final_img):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"invoice_{inv_number}_{timestamp}.png"
        temp_dir = os.path.join(tempfile.gettempdir(), "Aleefy_Invoices")
        Path(temp_dir).mkdir(parents=True, exist_ok=True)
        temp_path = os.path.join(temp_dir, filename)
        final_img.save(temp_path)

        def save_dialog_result(e):
            if e.path:
                import shutil
                shutil.copy(temp_path, e.path)
                page.pop_dialog()
                snack = ft.SnackBar(ft.Text("✅ تم الحفظ بنجاح!"), bgcolor=ft.Colors.GREEN_700)
                page.overlay.append(snack)
                snack.open = True
                page.update()
            else:
                snack = ft.SnackBar(ft.Text("تم إلغاء الحفظ"), bgcolor=ft.Colors.RED_700)
                page.overlay.append(snack)
                snack.open = True
                page.update()

        page.save_file(dialog_title="اختر مكان حفظ الفاتورة", file_name=filename, allowed_extensions=["png"], on_result=save_dialog_result)
        return temp_path, temp_dir
    except Exception as ex:
        print(f"خطأ في حفظ الصورة: {ex}")
        return None, None

def print_invoice_only(page, dialog):
    try:
        final_img = getattr(page, 'invoice_img', None)
        
        if not final_img:
            snack = ft.SnackBar(ft.Text("⚠️ لا توجد صورة للطباعة"), bgcolor=ft.Colors.RED_700)
            page.overlay.append(snack)
            snack.open = True
            page.update()
            return
        
        # ده بيبعت الصورة لبرنامج RawBT على التلفون
        success, msg = send_to_rawbt_wifi(final_img, rawbt_ip="127.0.0.1")
        
        if success:
            page.pop_dialog() # يقفل نافذة المعاينة بعد نجاح الطباعة
            snack = ft.SnackBar(ft.Text(f"✅ {msg}"), bgcolor=ft.Colors.GREEN_700, duration=3000)
            page.overlay.append(snack)
            snack.open = True
            page.update()
        else:
            snack = ft.SnackBar(
                ft.Text(f"❌ فشل الطباعة: {msg}\n💾 استخدم زر الحفظ بدلاً من ذلك"), 
                bgcolor=ft.Colors.RED_700, duration=5000
            )
            page.overlay.append(snack)
            snack.open = True
            page.update()
            
    except Exception as ex:
        snack = ft.SnackBar(ft.Text(f"❌ خطأ في الطباعة: {ex}"), bgcolor=ft.Colors.RED_700)
        page.overlay.append(snack)
        snack.open = True
        page.update()

def save_image_only(page, dialog):
    try:
        final_img = getattr(page, 'invoice_img', None)
        inv_number = getattr(page, 'invoice_number', '0000')
        if not final_img:
            snack = ft.SnackBar(ft.Text("⚠️ لا توجد صورة للحفظ"), bgcolor=ft.Colors.RED_700)
            page.overlay.append(snack)
            snack.open = True
            page.update()
            return
        saved_path, folder = save_invoice_image(page, inv_number, final_img)
        if not saved_path:
            snack = ft.SnackBar(ft.Text("❌ فشل حفظ الصورة"), bgcolor=ft.Colors.RED_700)
            page.overlay.append(snack)
            snack.open = True
            page.update()
    except Exception as ex:
        snack = ft.SnackBar(ft.Text(f"❌ خطأ: {ex}"), bgcolor=ft.Colors.RED_700)
        page.overlay.append(snack)
        snack.open = True
        page.update()

def close_dialog(dialog, page):
    page.pop_dialog()
    page.update()

def show_invoice_preview_with_actions(page, inv_number, date_str, items, discount, 
                                       delivery_fee, total, payment_type, is_delivery, 
                                       customer_name="", customer_phone="", customer_address="", invoice_view=None):
    print("✅ تم الضغط على زر المعاينة")
    try:
        # استخدام مكتبة الرسم العادية PIL (بتشتغل على أي نسخة وبتظبط حجم الخط)
        temp_path, final_img = generate_invoice_image(
            inv_number, date_str, items, discount, delivery_fee, total, 
            payment_type, is_delivery, customer_name, customer_phone, customer_address
        )

        page.invoice_img = final_img
        page.invoice_number = inv_number
        
        buffered = BytesIO()
        final_img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        img_src = f"data:image/png;base64,{img_str}"
        
        dialog = ft.AlertDialog(
            title=ft.Text("معاينة الفاتورة 🖨️", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    ft.Image(src=img_src, width=400, height=500, fit=ft.BoxFit.CONTAIN),
                    ft.Row([
                        ft.Icon(ft.Icons.INFO, color=ft.Colors.BLUE_400, size=16),
                        ft.Text("تأكد من الصورة قبل الطباعة", size=12, color=ft.Colors.GREY_400)
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=4),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=450, padding=10,
            ),
            actions=[
                ft.TextButton("إغلاق", on_click=lambda e: close_dialog(dialog, page), icon=ft.Icons.CLOSE),
                ft.ElevatedButton("💾 حفظ في التلفون", on_click=lambda e: save_image_only(page, dialog),
                                 bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE, icon=ft.Icons.SAVE),
                ft.ElevatedButton("🖨️ طباعة OTG", on_click=lambda e: print_invoice_only(page, dialog),
                                 bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE, icon=ft.Icons.PRINT),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )
        
        page.show_dialog(dialog)
        page.update()
        
    except Exception as ex:
        print(f"❌ خطأ في المعاينة: {ex}")
        snack = ft.SnackBar(ft.Text(f"❌ خطأ: {ex}"), bgcolor=ft.Colors.RED_700, duration=5000)
        page.overlay.append(snack)
        snack.open = True
        page.update()
CATEGORY_ICONS = {
    "طعام": "🍖", "إكسسوارات": "🎀", "أدوية وعناية": "💊", "ألعاب": "🧸",
    "نظافة": "🧴", "حيوانات": "🐾", "زواحف": "🦎", "طيور": "🐦", "اسماك": "🐟",
}

def category_icon(cat):
    return CATEGORY_ICONS.get(cat, "🐾")


def SalesView(page: ft.Page):
    otg_switch = ft.Switch(label="الطابعة متوصلة (OTG)", value=False)

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
        height=42,
        content_padding=10,
        on_change=lambda e: (state.update(search=e.control.value), refresh_grid()),
    )

    chips_row = ft.Row(spacing=8, scroll=ft.ScrollMode.AUTO)
    products_grid = ft.GridView(expand=True, max_extent=135, child_aspect_ratio=0.85, spacing=10, run_spacing=10)
    cart_list = ft.Column(spacing=6)

    discount_field = ft.TextField(
        hint_text="الخصم (ج.م)", hint_style=ft.TextStyle(color=ft.Colors.GREY_600, size=12),
        value="0", rtl=True, keyboard_type=ft.KeyboardType.NUMBER, width=140,
        border_radius=10, bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK,
        border_color=ft.Colors.ORANGE_400, focused_border_color=ft.Colors.ORANGE_600,
        height=42, content_padding=10, on_change=lambda e: update_totals_only(),
    )

    delivery_fee_field = ft.TextField(
        hint_text="رسوم التوصيل (ج.م)", hint_style=ft.TextStyle(color=ft.Colors.GREY_600, size=12),
        value="0", rtl=True, visible=False, keyboard_type=ft.KeyboardType.NUMBER, width=160,
        border_radius=10, bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK,
        border_color=ft.Colors.GREEN_400, focused_border_color=ft.Colors.GREEN_600,
        height=42, content_padding=10, on_change=lambda e: update_totals_only(),
    )

    subtotal_text = ft.Text("", size=13, color=ft.Colors.WHITE)
    total_text = ft.Text("الإجمالي: 0.00 ج.م", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_400)

    checkout_btn = ft.ElevatedButton(
        "إتمام البيع 💳", icon=ft.Icons.SHOPPING_BAG,
        bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE,
        style=ft.ButtonStyle(padding=15, shape=ft.RoundedRectangleBorder(radius=10)),
        on_click=lambda e: checkout(e), disabled=True,
    )

    is_delivery_switch = ft.Switch(label="طلب دليفري 🛵", value=False, active_color=ft.Colors.GREEN_500, on_change=lambda e: toggle_customer_fields())
    payment_type_radio = ft.RadioGroup(
        content=ft.Row([
            ft.Radio(value="نقدي", label="نقدي 💵", fill_color=ft.Colors.ORANGE_400),
            ft.Radio(value="محفظة", label="محفظة 📱", fill_color=ft.Colors.ORANGE_400),
            ft.Radio(value="آجل", label="آجل 📝", fill_color=ft.Colors.ORANGE_400),
        ], alignment=ft.MainAxisAlignment.START, spacing=15),
        value="نقدي", on_change=lambda e: toggle_customer_fields(),
    )

    customer_name_field = ft.TextField(hint_text="اسم العميل", hint_style=ft.TextStyle(color=ft.Colors.GREY_600, size=12), rtl=True, visible=False, border_radius=10, bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK, border_color=ft.Colors.ORANGE_400, height=42, content_padding=10, expand=True)
    customer_phone_field = ft.TextField(hint_text="رقم التليفون", hint_style=ft.TextStyle(color=ft.Colors.GREY_600, size=12), rtl=True, visible=False, border_radius=10, bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK, border_color=ft.Colors.ORANGE_400, height=42, content_padding=10, keyboard_type=ft.KeyboardType.NUMBER, on_change=lambda e: filter_customers(e.control.value), expand=True)
    customer_sector_field = ft.TextField(hint_text="القطاع / المنطقة", hint_style=ft.TextStyle(color=ft.Colors.GREY_600, size=12), rtl=True, visible=False, border_radius=10, bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK, border_color=ft.Colors.ORANGE_400, height=42, content_padding=10, expand=True)
    customer_building_field = ft.TextField(hint_text="رقم العمارة", hint_style=ft.TextStyle(color=ft.Colors.GREY_600, size=12), rtl=True, visible=False, border_radius=10, bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK, border_color=ft.Colors.ORANGE_400, height=42, content_padding=10, expand=True)
    customer_apartment_field = ft.TextField(hint_text="الشقة / الدور", hint_style=ft.TextStyle(color=ft.Colors.GREY_600, size=12), rtl=True, visible=False, border_radius=10, bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK, border_color=ft.Colors.ORANGE_400, height=42, content_padding=10, expand=True)

    suggestions_list = ft.ListView(expand=True, spacing=2, padding=5)
    suggestions_container = ft.Container(content=suggestions_list, bgcolor=ft.Colors.WHITE, border_radius=8, border=ft.Border.all(1, ft.Colors.ORANGE_400), visible=False, height=100)

    def filter_customers(query):
        query = (query or "").strip()
        if not query or len(query) < 1:
            suggestions_container.visible = False
            suggestions_list.controls.clear()
            suggestions_container.update()
            return

        matched = []
        try:
            if hasattr(db, "search_customers"):
                matched = db.search_customers(query)
        except Exception as ex:
            print(f"DB Search Error: {ex}")

        suggestions_list.controls.clear()
        if matched:
            for c in matched:
                c_name = c["name"] if isinstance(c, dict) else c[1]
                c_phone = c["phone"] if isinstance(c, dict) else c[2]
                c_addr = c["address"] if isinstance(c, dict) else (c[3] if len(c) > 3 else "")

                suggestions_list.controls.append(
                    ft.ListTile(
                        title=ft.Text(f"{c_name} - {c_phone}", size=12, color=ft.Colors.BLACK),
                        subtitle=ft.Text(f"العنوان: {c_addr}", size=10, color=ft.Colors.GREY_700) if c_addr else None,
                        on_click=lambda e, name=c_name, phone=c_phone, addr=c_addr: select_customer(name, phone, addr),
                    )
                )
            suggestions_container.visible = True
        else:
            suggestions_list.controls.append(
                ft.ListTile(
                    title=ft.Text("لا يوجد عميل بهذا الرقم (اضغط للإضافة)", size=12, color=ft.Colors.RED_400),
                    on_click=lambda e: select_customer("", query, ""),
                )
            )
            suggestions_container.visible = True

        suggestions_container.update()
        suggestions_list.update()

    def select_customer(name, phone, address):
        customer_name_field.value = name if name else ""
        customer_phone_field.value = phone if phone else ""

        sector, building, apartment = parse_stored_address(address)
        customer_sector_field.value = sector
        customer_building_field.value = building
        customer_apartment_field.value = apartment

        customer_name_field.visible = True
        customer_phone_field.visible = True
        show_addr = is_delivery_switch.value
        customer_sector_field.visible = show_addr
        customer_building_field.visible = show_addr
        customer_apartment_field.visible = show_addr

        suggestions_container.visible = False
        suggestions_list.controls.clear()

        customer_name_field.update()
        customer_phone_field.update()
        customer_sector_field.update()
        customer_building_field.update()
        customer_apartment_field.update()
        suggestions_container.update()
        suggestions_list.update()

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
                    ft.Container(content=ft.Text(category_icon(p["category"]), size=22), padding=6, bgcolor=ft.Colors.ORANGE_50, border_radius=50),
                    ft.Text(p["name"], size=12, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS, color=ft.Colors.BLACK),
                    ft.Text(f'{p["price"]:.2f} ج.م', size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                    ft.Text("خلص من المخزون" if out_of_stock else f'متاح: {p["stock"]:g} {unit_label}', size=10, weight=ft.FontWeight.W_500, color=ft.Colors.RED_600 if out_of_stock else ft.Colors.GREY_700),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=2,
            ),
            padding=8, border_radius=12, alignment=ft.Alignment.CENTER,
            bgcolor=ft.Colors.GREY_300 if out_of_stock else ft.Colors.WHITE,
            shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK), offset=ft.Offset(0, 2)),
            on_click=None if out_of_stock else (lambda e, p=p: add_to_cart(p)),
        )

    def add_to_cart(p):
        pid = p["id"]
        step = 1.0 if p["unit"] != "كيلو" else 0.25
        if pid in cart:
            new_qty = cart[pid]["qty"] + step
            if new_qty <= p["stock"]:
                cart[pid]["qty"] = new_qty
        else:
            cart[pid] = {"name": p["name"], "price": p["price"], "qty": min(step, p["stock"]), "unit": p["unit"], "stock": p["stock"]}
        refresh_cart()

    def change_qty(pid, delta):
        if pid not in cart:
            return
        cart[pid]["qty"] = round(cart[pid]["qty"] + delta, 3)
        if cart[pid]["qty"] <= 0:
            del cart[pid]
            refresh_cart()
        elif cart[pid]["qty"] > cart[pid]["stock"]:
            cart[pid]["qty"] = cart[pid]["stock"]
            refresh_cart()
        else:
            refresh_cart()

    def get_delivery_fee_value():
        if not is_delivery_switch.value:
            return 0.0
        try:
            return float(delivery_fee_field.value) if delivery_fee_field.value else 0.0
        except ValueError:
            return 0.0

    def update_totals_only():
        subtotal = sum(item["price"] * item["qty"] for item in cart.values())
        try:
            discount = float(discount_field.value) if discount_field.value else 0.0
        except ValueError:
            discount = 0.0
        discount = max(0.0, min(discount, subtotal))

        fee = get_delivery_fee_value()
        total = subtotal - discount + fee

        subtotal_line = f"الإجمالي الفرعي: {subtotal:.2f} ج.م"
        if discount:
            subtotal_line += f"   |   الخصم: {discount:.2f} ج.م"
        if fee:
            subtotal_line += f"   |   التوصيل: {fee:.2f} ج.م"
        subtotal_text.value = subtotal_line

        total_text.value = f"الإجمالي: {total:.2f} ج.م"
        checkout_btn.disabled = len(cart) == 0
        page.update()

    def refresh_cart():
        cart_list.controls.clear()
        for pid, item in cart.items():
            unit_price = item["price"]
            unit_label = "كجم" if item["unit"] == "كيلو" else "قطعة"
            step = 1 if item["unit"] == "قطعة" else 0.25

            line_total = unit_price * item["qty"]

            qty_field = ft.TextField(
                value=f'{item["qty"]:g}', width=70, height=38, text_align=ft.TextAlign.CENTER,
                content_padding=5, color=ft.Colors.BLACK, bgcolor=ft.Colors.GREY_100,
                border_radius=8, text_size=12, keyboard_type=ft.KeyboardType.NUMBER,
                border_color=ft.Colors.GREY_400, focused_border_color=ft.Colors.ORANGE_500,
            )

            price_field = ft.TextField(
                value=f"{line_total:.2f}", width=80, height=38, text_align=ft.TextAlign.CENTER,
                content_padding=5, color=ft.Colors.BLACK, bgcolor=ft.Colors.GREY_100,
                border_radius=8, text_size=12, keyboard_type=ft.KeyboardType.NUMBER,
                border_color=ft.Colors.GREY_400, focused_border_color=ft.Colors.ORANGE_500,
            )

            def make_on_qty_change(p_id, q_field, pr_field, u_price, stock_limit):
                def on_qty_change(e):
                    txt = q_field.value.strip()
                    if not txt: return
                    try:
                        val = float(txt)
                        val = min(val, stock_limit)
                        val = round(val, 3)
                        cart[p_id]["qty"] = val
                        new_line_total = val * u_price
                        pr_field.value = f"{new_line_total:.2f}"
                        pr_field.update()
                        update_totals_only()
                    except ValueError: pass
                return on_qty_change

            def make_on_price_change(p_id, q_field, pr_field, u_price, stock_limit):
                def on_price_change(e):
                    txt = pr_field.value.strip()
                    if not txt: return
                    try:
                        val = float(txt)
                        if u_price > 0:
                            calc_qty = round(val / u_price, 3)
                            calc_qty = min(calc_qty, stock_limit)
                            cart[p_id]["qty"] = calc_qty
                            q_field.value = f"{calc_qty:g}"
                            q_field.update()
                            update_totals_only()
                    except ValueError: pass
                return on_price_change

            qty_field.on_change = make_on_qty_change(pid, qty_field, price_field, unit_price, item["stock"])
            price_field.on_change = make_on_price_change(pid, qty_field, price_field, unit_price, item["stock"])

            cart_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(item["name"], expand=True, size=13, weight=ft.FontWeight.W_600, color=ft.Colors.BLACK),
                        ft.IconButton(ft.Icons.REMOVE_CIRCLE_OUTLINE, icon_size=20, icon_color=ft.Colors.RED_600, on_click=lambda e, pid=pid, s=step: change_qty(pid, -s)),
                        qty_field,
                        ft.Text(unit_label, size=11, color=ft.Colors.GREY_700),
                        ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINE, icon_size=20, icon_color=ft.Colors.GREEN_700, on_click=lambda e, pid=pid, s=step: change_qty(pid, s)),
                        price_field,
                        ft.Text("ج.م", size=11, color=ft.Colors.GREY_700),
                    ], spacing=4),
                    padding=6, bgcolor=ft.Colors.WHITE, border_radius=8,
                )
            )

        update_totals_only()

    def toggle_customer_fields():
        needs_customer = (payment_type_radio.value == "آجل") or is_delivery_switch.value
        customer_name_field.visible = needs_customer
        customer_phone_field.visible = needs_customer
        
        show_addr = is_delivery_switch.value
        customer_sector_field.visible = show_addr
        customer_building_field.visible = show_addr
        customer_apartment_field.visible = show_addr
        delivery_fee_field.visible = show_addr

        if not is_delivery_switch.value:
            delivery_fee_field.value = "0"
        if not needs_customer:
            suggestions_container.visible = False
        update_totals_only()

    def checkout(e):
        status_text.value = ""
        if not cart:
            return

        payment_type = payment_type_radio.value
        is_delivery = is_delivery_switch.value
        needs_customer = (payment_type == "آجل") or is_delivery

        if needs_customer:
            if not customer_name_field.value or not customer_phone_field.value:
                status_text.value = "البيع الآجل والدليفري يتطلبان اسم العميل ورقم تليفونه"
                page.update()
                return
            if is_delivery and (not customer_sector_field.value or not customer_building_field.value):
                status_text.value = "طلب الدليفري يتطلب إدخال المنطقة/القطاع ورقم العمارة على الأقل"
                page.update()
                return

            address_parts = []
            if customer_sector_field.value and customer_sector_field.value.strip():
                address_parts.append(f"القطاع/المنطقة: {customer_sector_field.value.strip()}")
            if customer_building_field.value and customer_building_field.value.strip():
                address_parts.append(f"عمارة: {customer_building_field.value.strip()}")
            if customer_apartment_field.value and customer_apartment_field.value.strip():
                address_parts.append(f"شقة: {customer_apartment_field.value.strip()}")

            full_address = " - ".join(address_parts) if address_parts else None

            db.save_or_update_customer(
                customer_name_field.value.strip(),
                customer_phone_field.value.strip(),
                full_address,
            )
        else:
            full_address = None

        try:
            discount = float(discount_field.value) if discount_field.value else 0.0
        except ValueError:
            discount = 0.0

        delivery_fee = get_delivery_fee_value()

        items = [
            {
                "product_id": pid,
                "product_name": item["name"],
                "quantity": item["qty"],
                "unit": item["unit"],
                "unit_price": item["price"],
            }
            for pid, item in cart.items()
        ]

        c_name = customer_name_field.value.strip() if needs_customer else None
        c_phone = customer_phone_field.value.strip() if needs_customer else None

        sale_id, total = db.create_sale(
            cart_items=items,
            discount=discount,
            payment_type=payment_type,
            customer_name=c_name,
            customer_phone=c_phone,
            delivery_address=full_address,
            delivery_fee=delivery_fee,
        )

        show_invoice(sale_id, items, discount, delivery_fee, total, payment_type, is_delivery, c_name, c_phone, full_address)

        cart.clear()
        discount_field.value = "0"
        delivery_fee_field.value = "0"
        payment_type_radio.value = "نقدي"
        is_delivery_switch.value = False
        customer_name_field.value = ""
        customer_phone_field.value = ""
        customer_sector_field.value = ""
        customer_building_field.value = ""
        customer_apartment_field.value = ""
        suggestions_container.visible = False
        toggle_customer_fields()
        refresh_grid()
        refresh_cart()

    def show_invoice(sale_id, items, discount, delivery_fee, total, payment_type, is_delivery, customer_name="", customer_phone="", customer_address=""):
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

        totals_rows = [
            ft.Row([ft.Text("الخصم", color=ft.Colors.GREY_700), ft.Text(f"{discount:.2f} ج.م", color=ft.Colors.BLACK)]),
        ]
        if delivery_fee:
            totals_rows.append(
                ft.Row([ft.Text("رسوم التوصيل", color=ft.Colors.GREY_700), ft.Text(f"{delivery_fee:.2f} ج.م", color=ft.Colors.BLACK)])
            )

        invoice_info_controls = [
            ft.Row([ft.Text("رقم الفاتورة", color=ft.Colors.GREY_700), ft.Text(serial, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)]),
            ft.Row([ft.Text("التاريخ والوقت", color=ft.Colors.GREY_700), ft.Text(now_str, color=ft.Colors.BLACK)]),
            ft.Row([ft.Text("طريقة الدفع", color=ft.Colors.GREY_700), ft.Text(payment_type, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700)]),
            ft.Row([ft.Text("نوع الطلب", color=ft.Colors.GREY_700), ft.Text("دليفري 🛵" if is_delivery else "استلام من الفرع", weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_700)]),
        ]

        if is_delivery and customer_address:
            invoice_info_controls.extend([
                ft.Row([ft.Text("اسم العميل", color=ft.Colors.GREY_700), ft.Text(customer_name or "-", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)]),
                ft.Row([ft.Text("رقم التليفون", color=ft.Colors.GREY_700), ft.Text(customer_phone or "-", color=ft.Colors.BLACK)]),
                ft.Row([ft.Text("عنوان التوصيل", color=ft.Colors.GREY_700), ft.Text(customer_address, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)]),
            ])

        invoice_view.controls = [
            ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_400, size=30),
                ft.Text("تمت عملية البيع بنجاح 🎉", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ]),
            ft.Container(
                padding=20, border_radius=16, bgcolor=ft.Colors.WHITE,
                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK), offset=ft.Offset(0, 4)),
                content=ft.Column([
                    ft.Row([
                        ft.Image(src=logo_path, height=40, fit=ft.BoxFit.CONTAIN) if logo_path else ft.Icon(ft.Icons.PETS, color=ft.Colors.ORANGE_700, size=30),
                        ft.Column([
                            ft.Text(SHOP_NAME, weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.BLACK),
                            ft.Text(SHOP_ADDRESS, size=10, color=ft.Colors.GREY_700),
                            ft.Text(f"واتساب: {SHOP_WHATSAPP}", size=10, color=ft.Colors.GREY_700),
                            ft.Text(f"مكالمات: {' - '.join(SHOP_PHONES)}", size=10, color=ft.Colors.GREY_700),
                        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END),
                    ], alignment=ft.MainAxisAlignment.END, spacing=10),
                    ft.Divider(),
                    *invoice_info_controls,
                    ft.Divider(),
                    *rows,
                    ft.Divider(),
                    *totals_rows,
                    ft.Row([
                        ft.Text("الإجمالي", weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.BLACK),
                        ft.Text(f"{total:.2f} ج.م", weight=ft.FontWeight.BOLD, size=18, color=ft.Colors.GREEN_800),
                    ]),
                ]),
            ),
            ft.Container(height=10),
            ft.Row(
                [
                    ft.ElevatedButton(
                        "🖨️ معاينة / طباعة",
                        icon=ft.Icons.PREVIEW,
                        bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE,
                        style=ft.ButtonStyle(padding=15, shape=ft.RoundedRectangleBorder(radius=10)),
                     on_click=lambda e: show_invoice_preview_with_actions(
    page, serial, now_str, items, discount, delivery_fee, total, 
    payment_type, is_delivery, customer_name, customer_phone, customer_address, invoice_view
),
                    ),
                    ft.ElevatedButton(
                        "بيع جديد 🛒",
                        icon=ft.Icons.ADD_SHOPPING_CART,
                        bgcolor=ft.Colors.ORANGE_700, color=ft.Colors.WHITE,
                        style=ft.ButtonStyle(padding=15, shape=ft.RoundedRectangleBorder(radius=10)),
                        on_click=lambda e: new_sale(),
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
            ),
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

    header_bar = ft.Row(
        [
            ft.Row([
                ft.Image(src=logo_path, height=60, fit=ft.BoxFit.CONTAIN) if logo_path else ft.Icon(ft.Icons.PETS, color=ft.Colors.ORANGE_400, size=32),
                ft.Text("Aleefy Pets", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Text("نقطة البيع 🐾", size=15, color=ft.Colors.ORANGE_300, weight=ft.FontWeight.W_600),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    pos_view.controls = [
        header_bar,
        search_field,
        chips_row,
        ft.Container(content=products_grid, height=320),
        ft.Divider(color=ft.Colors.WHITE24),
        ft.Text("السلة 🛒", weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.WHITE),
        cart_list,
        ft.Row([discount_field, delivery_fee_field]),
        subtotal_text,
        total_text,
        ft.Container(height=4),
        ft.Row([
            ft.Column([
                ft.Text("طريقة الدفع:", weight=ft.FontWeight.W_600, color=ft.Colors.WHITE, size=13),
                payment_type_radio,
            ]),
            is_delivery_switch,
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
        ft.Row([customer_name_field, customer_phone_field], spacing=10),
        suggestions_container,
        ft.Row([customer_sector_field, customer_building_field, customer_apartment_field], spacing=8),
        ft.Row([otg_switch, checkout_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
    ]

    return ft.Container(
        content=ft.Column([pos_view, invoice_view], expand=True, scroll=ft.ScrollMode.AUTO),
        padding=12,
        expand=True,
    )
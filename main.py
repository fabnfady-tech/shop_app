import flet as ft
import os
import db
from sales_view import SalesView
from products_view import ProductsView
from expenses_view import ExpensesView
from deferred_view import DeferredView
from returns_view import ReturnsView
from monthly_view import MonthlyView
from reports_view import ReportsView
from delivery_view import DeliveryView

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BG_PATH = os.path.join(BASE_DIR, "bg_logo.jpg")
ICON_PATH = os.path.join(BASE_DIR, "assets", "icon.png")

# قائمة الصفحات: (اسم الشاشة, الأيقونة, دالة الشاشة, هل هي محمية بكلمة مرور الأدمن؟)
PAGES = [
    ("بيع", ft.Icons.POINT_OF_SALE, SalesView, False),
    ("طلبات الدليفري", ft.Icons.LOCAL_SHIPPING, DeliveryView, False),
    ("المنتجات", ft.Icons.INVENTORY_2, ProductsView, True),
    ("المصروفات", ft.Icons.ACCOUNT_BALANCE_WALLET, ExpensesView, False),
    ("الإيرادات المؤجلة", ft.Icons.SCHEDULE_SEND, DeferredView, True),
    ("المرتجعات", ft.Icons.UNDO, ReturnsView, True),
    ("جدول الشهر", ft.Icons.TABLE_CHART, MonthlyView, True),
    ("التقرير", ft.Icons.BAR_CHART, ReportsView, True),
]


def main(page: ft.Page):
    page.title = "Aleefy Pets"
    page.rtl = True
    page.padding = 0
    page.bgcolor = "#13162d"

    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            on_surface=ft.Colors.WHITE,
            primary=ft.Colors.ORANGE_400,
        )
    )

    if os.path.exists(ICON_PATH):
        page.window_icon = ICON_PATH

    current_index = {"value": 0}
    auth_state = {"unlocked": False}
   # تخزين حالة فتح الأدمن في page.data لتكون متاحة لجميع الشاشات
    if not hasattr(page, "data") or page.data is None:
        page.data = {}
    page.data["admin_unlocked"] = False

    def set_unlocked(value: bool):
        """تحديث حالة فتح الأدمن"""
        auth_state["unlocked"] = value
        page.data["admin_unlocked"] = value

    body_container = ft.Container(expand=True, padding=8)
    title_text = ft.Text(PAGES[0][0], size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)

    sidebar_content = ft.Column([], expand=True, spacing=5)

    sidebar_container = ft.Container(
        width=280,
        bgcolor=ft.Colors.with_opacity(0.95, "#101226"),
        padding=15,
        content=sidebar_content,
    )

    overlay_bg = ft.Container(
        expand=True,
        bgcolor=ft.Colors.BLACK54,
        on_click=lambda e: hide_sidebar(),
    )

    sidebar_overlay = ft.Stack(
        controls=[
            overlay_bg,
            ft.Row([sidebar_container], alignment=ft.MainAxisAlignment.START, expand=True),
        ],
        visible=False,
        expand=True,
    )

    def hide_sidebar():
        sidebar_overlay.visible = False
        page.update()

    def open_sidebar(e):
        sidebar_overlay.visible = True
        page.update()

    def load_page_view(view_fn):
        body_container.content = ft.Column(
            [view_fn(page)],
            scroll="auto",
            expand=True,
        )

    # ================= نظام الحماية بكلمة مرور الأدمن =================
    auth_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("تنبيه"),
        content=ft.Text("جاري التحميل..."),
    )
    page.overlay.append(auth_dialog)

    def close_auth_dialog(e=None):
        auth_dialog.open = False
        page.update()

    def show_login(pending_index):
        pw = ft.TextField(
            label="كلمة المرور",
            password=True,
            can_reveal_password=True,
            autofocus=True,
            rtl=True,
            on_submit=lambda e: try_login(e),
        )
        status = ft.Text("", color=ft.Colors.RED, size=12)

        def try_login(e):
            if db.verify_admin_password(pw.value or ""):
                set_unlocked(True)
                close_auth_dialog()
                go_to_page(pending_index)
            else:
                status.value = "كلمة المرور غلط، جرب تاني"
                page.update()

        auth_dialog.title = ft.Row([ft.Icon(ft.Icons.LOCK, color=ft.Colors.ORANGE_400), ft.Text("دخول الأدمن")])
        auth_dialog.content = ft.Column(
            [
                ft.Text("الشاشة دي محمية - ادخل كلمة مرور الأدمن عشان تفتحها", size=12, color=ft.Colors.GREY_400),
                pw,
                status,
                ft.TextButton("نسيت كلمة المرور؟", on_click=lambda e: show_forgot_question(pending_index)),
            ],
            tight=True,
            spacing=6,
            width=320,
        )
        auth_dialog.actions = [
            ft.TextButton("إلغاء", on_click=close_auth_dialog),
            ft.ElevatedButton("دخول", icon=ft.Icons.LOGIN, on_click=try_login, bgcolor=ft.Colors.ORANGE_600, color=ft.Colors.WHITE),
        ]
        auth_dialog.actions_alignment = ft.MainAxisAlignment.END
        auth_dialog.open = True
        page.update()

    def show_setup(pending_index):
        pw1 = ft.TextField(label="كلمة مرور الأدمن الجديدة", password=True, can_reveal_password=True, rtl=True)
        pw2 = ft.TextField(label="تأكيد كلمة المرور", password=True, can_reveal_password=True, rtl=True)
        question = ft.TextField(label="سؤال استرجاع (لو نسيت كلمة السر)", rtl=True, hint_text="مثال: اسم أول عميل في المحل؟")
        answer = ft.TextField(label="إجابة السؤال", rtl=True)
        status = ft.Text("", color=ft.Colors.RED, size=12)

        def save_setup(e):
            if not pw1.value or len(pw1.value) < 4:
                status.value = "كلمة المرور لازم تكون 4 حروف/أرقام على الأقل"
                page.update()
                return
            if pw1.value != pw2.value:
                status.value = "كلمة المرور وتأكيدها مش متطابقين"
                page.update()
                return
            if not question.value or not answer.value:
                status.value = "لازم تكتب سؤال وإجابة الاسترجاع عشان تقدر ترجع لو نسيت"
                page.update()
                return
            db.set_admin_password(pw1.value, question.value, answer.value)
            set_unlocked(True)
            close_auth_dialog()
            go_to_page(pending_index)

        auth_dialog.title = ft.Row([ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, color=ft.Colors.ORANGE_400), ft.Text("أول مرة: اعمل كلمة مرور الأدمن")])
        auth_dialog.content = ft.Column(
            [
                ft.Text("هتحمي بيها الشاشات الخاصة. احتفظ بيها كويس.", size=12, color=ft.Colors.GREY_400),
                pw1,
                pw2,
                ft.Divider(),
                question,
                answer,
                status,
            ],
            tight=True,
            spacing=6,
            width=320,
            scroll="auto",
        )
        auth_dialog.actions = [
            ft.TextButton("إلغاء", on_click=close_auth_dialog),
            ft.ElevatedButton("حفظ وفتح", icon=ft.Icons.SAVE, on_click=save_setup, bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE),
        ]
        auth_dialog.actions_alignment = ft.MainAxisAlignment.END
        auth_dialog.open = True
        page.update()

    def show_forgot_question(pending_index):
        q = db.get_security_question() or "-"
        answer = ft.TextField(label="إجابتك", rtl=True, autofocus=True)
        status = ft.Text("", color=ft.Colors.RED, size=12)

        def check_answer(e):
            if db.verify_security_answer(answer.value or ""):
                show_forgot_reset(pending_index)
            else:
                status.value = "الإجابة مش مطابقة، جرب تاني"
                page.update()

        auth_dialog.title = ft.Row([ft.Icon(ft.Icons.HELP_OUTLINE, color=ft.Colors.ORANGE_400), ft.Text("استرجاع كلمة المرور")])
        auth_dialog.content = ft.Column(
            [
                ft.Text(f"سؤال الاسترجاع: {q}", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                answer,
                status,
            ],
            tight=True,
            spacing=8,
            width=320,
        )
        auth_dialog.actions = [
            ft.TextButton("رجوع لتسجيل الدخول", on_click=lambda e: show_login(pending_index)),
            ft.ElevatedButton("تأكيد", icon=ft.Icons.CHECK, on_click=check_answer, bgcolor=ft.Colors.ORANGE_600, color=ft.Colors.WHITE),
        ]
        auth_dialog.actions_alignment = ft.MainAxisAlignment.END
        auth_dialog.open = True
        page.update()

    def show_forgot_reset(pending_index):
        pw1 = ft.TextField(label="كلمة مرور جديدة", password=True, can_reveal_password=True, rtl=True, autofocus=True)
        pw2 = ft.TextField(label="تأكيد كلمة المرور", password=True, can_reveal_password=True, rtl=True)
        status = ft.Text("", color=ft.Colors.RED, size=12)

        def save_new_password(e):
            if not pw1.value or len(pw1.value) < 4:
                status.value = "كلمة المرور لازم تكون 4 حروف/أرقام على الأقل"
                page.update()
                return
            if pw1.value != pw2.value:
                status.value = "كلمة المرور وتأكيدها مش متطابقين"
                page.update()
                return
            db.reset_admin_password(pw1.value)
            set_unlocked(True)
            close_auth_dialog()
            if pending_index is not None:
                go_to_page(pending_index)

        auth_dialog.title = ft.Row([ft.Icon(ft.Icons.LOCK_RESET, color=ft.Colors.ORANGE_400), ft.Text("كلمة مرور جديدة")])
        auth_dialog.content = ft.Column([pw1, pw2, status], tight=True, spacing=8, width=320)
        auth_dialog.actions = [
            ft.TextButton("إلغاء", on_click=close_auth_dialog),
            ft.ElevatedButton("حفظ", icon=ft.Icons.SAVE, on_click=save_new_password, bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE),
        ]
        auth_dialog.actions_alignment = ft.MainAxisAlignment.END
        auth_dialog.open = True
        page.update()

    def show_change_password():
        current_pw = ft.TextField(label="كلمة المرور الحالية", password=True, can_reveal_password=True, rtl=True, autofocus=True)
        pw1 = ft.TextField(label="كلمة مرور جديدة", password=True, can_reveal_password=True, rtl=True)
        pw2 = ft.TextField(label="تأكيد كلمة المرور", password=True, can_reveal_password=True, rtl=True)
        status = ft.Text("", color=ft.Colors.RED, size=12)

        def save_change(e):
            if not db.verify_admin_password(current_pw.value or ""):
                status.value = "كلمة المرور الحالية غلط"
                page.update()
                return
            if not pw1.value or len(pw1.value) < 4:
                status.value = "كلمة المرور الجديدة لازم تكون 4 حروف/أرقام على الأقل"
                page.update()
                return
            if pw1.value != pw2.value:
                status.value = "كلمة المرور وتأكيدها مش متطابقين"
                page.update()
                return
            db.reset_admin_password(pw1.value)
            close_auth_dialog()

        auth_dialog.title = ft.Row([ft.Icon(ft.Icons.PASSWORD, color=ft.Colors.ORANGE_400), ft.Text("تغيير كلمة مرور الأدمن")])
        auth_dialog.content = ft.Column([current_pw, pw1, pw2, status], tight=True, spacing=8, width=320)
        auth_dialog.actions = [
            ft.TextButton("إلغاء", on_click=close_auth_dialog),
            ft.ElevatedButton("حفظ", icon=ft.Icons.SAVE, on_click=save_change, bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE),
        ]
        auth_dialog.actions_alignment = ft.MainAxisAlignment.END
        auth_dialog.open = True
        page.update()

    def request_page_access(index):
        title, icon, view_fn, protected = PAGES[index]
        if not protected or auth_state["unlocked"]:
            go_to_page(index)
            return
        if not db.is_admin_password_set():
            show_setup(index)
        else:
            show_login(index)

    def go_to_page(index):
        current_index["value"] = index
        title, icon, view_fn, protected = PAGES[index]
        load_page_view(view_fn)
        title_text.value = title
        build_menu_items()
        hide_sidebar()

    def lock_screens(e=None):
        set_unlocked(False)
        go_to_page(0)

    # ================= القائمة الجانبية =================
    def build_menu_items():
        items = [
            ft.Container(
                padding=10,
                content=ft.Row([
                    ft.Image(src=BG_PATH, width=32, height=32, fit="contain", border_radius=6)
                    if os.path.exists(BG_PATH) else ft.Icon(ft.Icons.PETS, size=28, color=ft.Colors.ORANGE_400),
                    ft.Text("Aleefy Pets", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ]),
            ),
            ft.Divider(color=ft.Colors.WHITE24),
        ]
        for idx, (label, icon, _, protected) in enumerate(PAGES):
            is_selected = (idx == current_index["value"])
            show_lock_icon = protected and not auth_state["unlocked"]
            items.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(icon, color=ft.Colors.ORANGE_400 if is_selected else ft.Colors.WHITE70),
                        ft.Text(
                            label,
                            weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL,
                            color=ft.Colors.ORANGE_400 if is_selected else ft.Colors.WHITE,
                            expand=True,
                        ),
                        ft.Icon(ft.Icons.LOCK, size=15, color=ft.Colors.WHITE38) if show_lock_icon else ft.Container(),
                    ]),
                    padding=12,
                    border_radius=8,
                    bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.ORANGE_700) if is_selected else None,
                    on_click=lambda e, i=idx: request_page_access(i),
                )
            )
        items.append(ft.Divider(color=ft.Colors.WHITE24))
        if auth_state["unlocked"]:
            items.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.LOCK_OPEN, color=ft.Colors.GREEN_400, size=18),
                        ft.Text("الشاشات مفتوحة - دوس تقفل", color=ft.Colors.WHITE70, size=13)
                    ]),
                    padding=10, border_radius=8, on_click=lock_screens,
                )
            )
            items.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.PASSWORD, color=ft.Colors.WHITE54, size=18),
                        ft.Text("تغيير كلمة مرور الأدمن", color=ft.Colors.WHITE70, size=13)
                    ]),
                    padding=10, border_radius=8, on_click=lambda e: show_change_password(),
                )
            )
        else:
            items.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.LOCK, color=ft.Colors.WHITE38, size=18),
                        ft.Text("باقي الشاشات محمية بكلمة مرور الأدمن", color=ft.Colors.WHITE38, size=12)
                    ]),
                    padding=10,
                )
            )
        sidebar_content.controls = items

    app_bar = ft.Container(
        height=60,
        bgcolor=ft.Colors.with_opacity(0.85, "#181b36"),
        padding=15,
        content=ft.Row([
            ft.IconButton(ft.Icons.MENU, icon_color=ft.Colors.WHITE, on_click=open_sidebar),
            title_text,
        ], alignment=ft.MainAxisAlignment.START),
    )

    load_page_view(PAGES[0][2])
    build_menu_items()

    background_layer = ft.Container(
        expand=True,
        bgcolor="#13162d",
        content=ft.Image(
            src=BG_PATH,
            fit="cover",
            opacity=0.35,
        ) if os.path.exists(BG_PATH) else None,
    )

    main_layout = ft.Column([app_bar, body_container], expand=True, spacing=0)

    page.add(
        ft.Stack(
            controls=[
                background_layer,
                main_layout,
                sidebar_overlay,
            ],
            expand=True,
        )
    )


if __name__ == "__main__":
    db.init_db()
    db.apply_recurring_expenses()
    ft.app(target=main)
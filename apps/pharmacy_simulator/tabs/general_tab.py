"""General tab — patient demographic and contact fields."""

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from apps.pharmacy_simulator.layout.dynamic_layout import (
    clear_layout,
    restore_form_rows,
    shuffle_form_rows,
    shuffle_widgets_in_layout,
)
from apps.pharmacy_simulator.widgets.accessibility import set_accessible

GENDER_OPTIONS = ["", "Male", "Female", "Other", "Unknown"]
DELIVERY_TYPES = ["", "Pickup", "Delivery", "Mail"]
DELIVERY_ROUTES = ["", "Standard", "Express", "Same Day"]
PRICE_GROUPS = ["", "Regular", "Senior", "Employee", "Insurance A", "Insurance B"]
PROVINCES = [
    "",
    "AB",
    "BC",
    "MB",
    "NB",
    "NL",
    "NS",
    "NT",
    "NU",
    "ON",
    "PE",
    "QC",
    "SK",
    "YT",
]


class GeneralTab(QWidget):
    """General patient information tab with full accessibility metadata."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        set_accessible(self, "tab_general", "tab_general")
        self._build_ui()

    def _labeled_field(
        self,
        label_text: str,
        widget: QWidget,
        label_object_name: str,
    ) -> tuple[QLabel, QWidget]:
        label = QLabel(label_text)
        set_accessible(label, label_object_name, label_object_name)
        return label, widget

    def _configure_form(self, form: QFormLayout) -> None:
        form.setVerticalSpacing(10)
        form.setHorizontalSpacing(12)
        form.setContentsMargins(8, 12, 8, 8)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

    def _line_edit(self, object_name: str, read_only: bool = False) -> QLineEdit:
        field = QLineEdit()
        field.setReadOnly(read_only)
        field.setMinimumHeight(28)
        set_accessible(field, object_name, object_name)
        return field

    def _combo(self, object_name: str, options: list[str]) -> QComboBox:
        combo = QComboBox()
        combo.addItems(options)
        combo.setMinimumHeight(28)
        set_accessible(combo, object_name, object_name)
        return combo

    def _date_edit(self, object_name: str) -> QDateEdit:
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDisplayFormat("yyyy-MM-dd")
        date_edit.setDate(QDate.currentDate())
        date_edit.setSpecialValueText("")
        date_edit.setMinimumHeight(28)
        set_accessible(date_edit, object_name, object_name)
        return date_edit

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        set_accessible(scroll, "scroll_general", "scroll_general")

        content = QWidget()
        set_accessible(content, "content_general", "content_general")
        root = QVBoxLayout(content)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(10)

        top_row = QHBoxLayout()

        identity_group = QGroupBox("Patient Identity")
        set_accessible(identity_group, "grp_identity", "grp_identity")
        identity_form = QFormLayout(identity_group)
        self._configure_form(identity_form)

        self.txt_patient_id = self._line_edit("txt_patient_id", read_only=True)
        self.txt_first_name = self._line_edit("txt_first_name")
        self.txt_last_name = self._line_edit("txt_last_name")
        self.txt_middle_name = self._line_edit("txt_middle_name")
        self.txt_dob = self._line_edit("txt_dob")
        self.txt_dob.setPlaceholderText("yyyy-MM-dd")
        self.cmb_gender = self._combo("cmb_gender", GENDER_OPTIONS)

        identity_fields = [
            ("Patient ID:", self.txt_patient_id, "lbl_patient_id"),
            ("First Name:", self.txt_first_name, "lbl_first_name"),
            ("Last Name:", self.txt_last_name, "lbl_last_name"),
            ("Middle Name:", self.txt_middle_name, "lbl_middle_name"),
            ("Date Of Birth:", self.txt_dob, "lbl_dob"),
            ("Gender:", self.cmb_gender, "lbl_gender"),
        ]
        self._identity_rows: list[tuple] = []
        for text, widget, lbl_name in identity_fields:
            label, _ = self._labeled_field(text, widget, lbl_name)
            identity_form.addRow(label, widget)
            self._identity_rows.append((label, widget))

        contact_group = QGroupBox("Contact")
        set_accessible(contact_group, "grp_contact", "grp_contact")
        contact_form = QFormLayout(contact_group)
        self._configure_form(contact_form)

        self.txt_phone = self._line_edit("txt_phone")
        self.txt_email = self._line_edit("txt_email")

        self._contact_rows: list[tuple] = []
        for text, widget, lbl_name in [
            ("Phone:", self.txt_phone, "lbl_phone"),
            ("Email:", self.txt_email, "lbl_email"),
        ]:
            label, _ = self._labeled_field(text, widget, lbl_name)
            contact_form.addRow(label, widget)
            self._contact_rows.append((label, widget))

        top_row.addWidget(identity_group, stretch=1)
        top_row.addWidget(contact_group, stretch=1)
        root.addLayout(top_row)

        address_group = QGroupBox("Address")
        set_accessible(address_group, "grp_address", "grp_address")
        address_form = QFormLayout(address_group)
        self._configure_form(address_form)

        self.txt_address_line1 = self._line_edit("txt_address_line1")
        self.txt_address_line2 = self._line_edit("txt_address_line2")
        self.txt_city = self._line_edit("txt_city")
        self.cmb_province = self._combo("cmb_province", PROVINCES)
        self.txt_postal_code = self._line_edit("txt_postal_code")

        self._address_rows: list[tuple] = []
        for text, widget, lbl_name in [
            ("Address Line 1:", self.txt_address_line1, "lbl_address_line1"),
            ("Address Line 2:", self.txt_address_line2, "lbl_address_line2"),
            ("City:", self.txt_city, "lbl_city"),
            ("Province:", self.cmb_province, "lbl_province"),
            ("Postal Code:", self.txt_postal_code, "lbl_postal_code"),
        ]:
            label, _ = self._labeled_field(text, widget, lbl_name)
            address_form.addRow(label, widget)
            self._address_rows.append((label, widget))

        root.addWidget(address_group)

        bottom_row = QHBoxLayout()

        health_group = QGroupBox("Health & Delivery")
        set_accessible(health_group, "grp_health", "grp_health")
        health_form = QFormLayout(health_group)
        self._configure_form(health_form)

        self.txt_health_card = self._line_edit("txt_health_card")
        self.cmb_delivery_type = self._combo("cmb_delivery_type", DELIVERY_TYPES)
        self.cmb_delivery_route = self._combo("cmb_delivery_route", DELIVERY_ROUTES)
        self.cmb_price_group = self._combo("cmb_price_group", PRICE_GROUPS)

        self._health_rows: list[tuple] = []
        for text, widget, lbl_name in [
            ("Health Card Number:", self.txt_health_card, "lbl_health_card"),
            ("Delivery Type:", self.cmb_delivery_type, "lbl_delivery_type"),
            ("Delivery Route:", self.cmb_delivery_route, "lbl_delivery_route"),
            ("Price Group:", self.cmb_price_group, "lbl_price_group"),
        ]:
            label, _ = self._labeled_field(text, widget, lbl_name)
            health_form.addRow(label, widget)
            self._health_rows.append((label, widget))

        status_group = QGroupBox("Status")
        set_accessible(status_group, "grp_status", "grp_status")
        status_form = QFormLayout(status_group)
        self._configure_form(status_form)

        self.chk_active = QCheckBox("Active")
        set_accessible(self.chk_active, "chk_active", "chk_active")
        self.chk_active.setChecked(True)

        self.chk_animal = QCheckBox("Animal")
        set_accessible(self.chk_animal, "chk_animal", "chk_animal")

        self.txt_deceased_date = self._date_edit("txt_deceased_date")
        self._deceased_empty = QDate(1900, 1, 1)
        self.txt_deceased_date.setMinimumDate(self._deceased_empty)
        self.txt_deceased_date.setDate(self._deceased_empty)
        self.txt_deceased_date.setSpecialValueText("(none)")
        self.chk_active.toggled.connect(self._on_active_toggled)
        self._on_active_toggled(self.chk_active.isChecked())

        self._status_rows: list[tuple] = []
        status_form.addRow(self.chk_active)
        self._status_rows.append((None, self.chk_active))
        status_form.addRow(self.chk_animal)
        self._status_rows.append((None, self.chk_animal))
        deceased_label, _ = self._labeled_field("Deceased Date:", self.txt_deceased_date, "lbl_deceased_date")
        status_form.addRow(deceased_label, self.txt_deceased_date)
        self._status_rows.append((deceased_label, self.txt_deceased_date))

        bottom_row.addWidget(health_group, stretch=1)
        bottom_row.addWidget(status_group, stretch=1)
        root.addLayout(bottom_row)

        comments_group = QGroupBox("Comments")
        set_accessible(comments_group, "grp_comments", "grp_comments")
        comments_layout = QVBoxLayout(comments_group)
        self.txt_comments = QPlainTextEdit()
        self.txt_comments.setMinimumHeight(80)
        self.txt_comments.setMaximumHeight(120)
        set_accessible(self.txt_comments, "txt_comments", "txt_comments")
        comments_layout.addWidget(self.txt_comments)

        root.addWidget(comments_group)

        scroll.setWidget(content)
        outer.addWidget(scroll)

        self._content = content
        self._root_layout = root
        self._grp_identity = identity_group
        self._grp_contact = contact_group
        self._grp_address = address_group
        self._grp_health = health_group
        self._grp_status = status_group
        self._grp_comments = comments_group
        self._form_maps = [
            (identity_form, self._identity_rows),
            (contact_form, self._contact_rows),
            (address_form, self._address_rows),
            (health_form, self._health_rows),
            (status_form, self._status_rows),
        ]
        self._randomized_layout = False

    def set_randomized_layout(self, enabled: bool) -> None:
        """Reorder sections and fields to simulate pharmacy UI customization."""
        if enabled == self._randomized_layout:
            return
        self._randomized_layout = enabled
        if enabled:
            self._apply_random_layout()
        else:
            self._apply_default_layout()

    def _apply_default_layout(self) -> None:
        clear_layout(self._root_layout, self._content)
        top_row = QHBoxLayout()
        top_row.addWidget(self._grp_identity, stretch=1)
        top_row.addWidget(self._grp_contact, stretch=1)
        self._root_layout.addLayout(top_row)
        self._root_layout.addWidget(self._grp_address)
        bottom_row = QHBoxLayout()
        bottom_row.addWidget(self._grp_health, stretch=1)
        bottom_row.addWidget(self._grp_status, stretch=1)
        self._root_layout.addLayout(bottom_row)
        self._root_layout.addWidget(self._grp_comments)
        for form, rows in self._form_maps:
            restore_form_rows(form, rows)

    def _apply_random_layout(self) -> None:
        shuffle_widgets_in_layout(
            self._root_layout,
            [
                self._grp_identity,
                self._grp_contact,
                self._grp_address,
                self._grp_health,
                self._grp_status,
                self._grp_comments,
            ],
            host=self._content,
        )
        for form, rows in self._form_maps:
            shuffle_form_rows(form, rows)

    def _on_active_toggled(self, active: bool) -> None:
        """Deceased date is only editable when patient is not active."""
        if active:
            self.txt_deceased_date.setDate(self._deceased_empty)
            self.txt_deceased_date.setEnabled(False)
        else:
            self.txt_deceased_date.setEnabled(True)

    def _deceased_date_value(self) -> str:
        if self.txt_deceased_date.date() == self._deceased_empty:
            return ""
        return self.txt_deceased_date.date().toString("yyyy-MM-dd")

    def _set_deceased_date(self, value: str) -> None:
        deceased = value.strip()
        if not deceased:
            self.txt_deceased_date.setDate(self._deceased_empty)
            return
        parsed = QDate.fromString(deceased, "yyyy-MM-dd")
        if parsed.isValid():
            self.txt_deceased_date.setDate(parsed)

    def set_patient_id(self, patient_id: str) -> None:
        self.txt_patient_id.setText(patient_id)

    def get_field_values(self) -> dict[str, str | bool]:
        """Return all field values for persistence / automation verification."""
        return {
            "patient_id": self.txt_patient_id.text(),
            "first_name": self.txt_first_name.text(),
            "last_name": self.txt_last_name.text(),
            "middle_name": self.txt_middle_name.text(),
            "dob": self.txt_dob.text().strip(),
            "gender": self.cmb_gender.currentText(),
            "phone": self.txt_phone.text(),
            "email": self.txt_email.text(),
            "address_line1": self.txt_address_line1.text(),
            "address_line2": self.txt_address_line2.text(),
            "city": self.txt_city.text(),
            "province": self.cmb_province.currentText(),
            "postal_code": self.txt_postal_code.text(),
            "health_card": self.txt_health_card.text(),
            "active": self.chk_active.isChecked(),
            "animal": self.chk_animal.isChecked(),
            "deceased_date": self._deceased_date_value(),
            "delivery_type": self.cmb_delivery_type.currentText(),
            "delivery_route": self.cmb_delivery_route.currentText(),
            "price_group": self.cmb_price_group.currentText(),
            "comments": self.txt_comments.toPlainText(),
        }

    def set_field_values(self, data: dict[str, str | bool]) -> None:
        """Populate fields from a data dictionary."""
        self.txt_patient_id.setText(str(data.get("patient_id", "")))
        self.txt_first_name.setText(str(data.get("first_name", "")))
        self.txt_last_name.setText(str(data.get("last_name", "")))
        self.txt_middle_name.setText(str(data.get("middle_name", "")))

        self.txt_dob.setText(str(data.get("dob", "")).strip())

        gender = str(data.get("gender", ""))
        idx = self.cmb_gender.findText(gender)
        if idx >= 0:
            self.cmb_gender.setCurrentIndex(idx)

        self.txt_phone.setText(str(data.get("phone", "")))
        self.txt_email.setText(str(data.get("email", "")))
        self.txt_address_line1.setText(str(data.get("address_line1", "")))
        self.txt_address_line2.setText(str(data.get("address_line2", "")))
        self.txt_city.setText(str(data.get("city", "")))

        province = str(data.get("province", ""))
        idx = self.cmb_province.findText(province)
        if idx >= 0:
            self.cmb_province.setCurrentIndex(idx)

        self.txt_postal_code.setText(str(data.get("postal_code", "")))
        self.txt_health_card.setText(str(data.get("health_card", "")))
        self.chk_active.setChecked(bool(data.get("active", True)))
        self.chk_animal.setChecked(bool(data.get("animal", False)))
        self._set_deceased_date(str(data.get("deceased_date", "")))
        self._on_active_toggled(self.chk_active.isChecked())

        delivery_type = str(data.get("delivery_type", ""))
        idx = self.cmb_delivery_type.findText(delivery_type)
        if idx >= 0:
            self.cmb_delivery_type.setCurrentIndex(idx)

        delivery_route = str(data.get("delivery_route", ""))
        idx = self.cmb_delivery_route.findText(delivery_route)
        if idx >= 0:
            self.cmb_delivery_route.setCurrentIndex(idx)

        price_group = str(data.get("price_group", ""))
        idx = self.cmb_price_group.findText(price_group)
        if idx >= 0:
            self.cmb_price_group.setCurrentIndex(idx)

        self.txt_comments.setPlainText(str(data.get("comments", "")))

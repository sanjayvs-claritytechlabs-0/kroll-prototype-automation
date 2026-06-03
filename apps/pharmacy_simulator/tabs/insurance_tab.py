"""Insurance tab — plan and policy fields."""

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
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

PLAN_TYPES = ["", "Provincial", "Private", "Third Party", "Workers Compensation", "Other"]
RELATIONSHIPS = ["", "Self", "Spouse", "Child", "Parent", "Other"]


class InsuranceTab(QWidget):
    """Patient insurance information for automation PoC."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        set_accessible(self, "tab_insurance", "tab_insurance")
        self._build_ui()

    def _configure_form(self, form: QFormLayout) -> None:
        form.setVerticalSpacing(10)
        form.setHorizontalSpacing(12)
        form.setContentsMargins(8, 12, 8, 8)

    def _line_edit(self, object_name: str) -> QLineEdit:
        field = QLineEdit()
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
        self._expiry_empty = QDate(1900, 1, 1)
        date_edit.setMinimumDate(self._expiry_empty)
        date_edit.setDate(self._expiry_empty)
        date_edit.setSpecialValueText("(none)")
        date_edit.setMinimumHeight(28)
        set_accessible(date_edit, object_name, object_name)
        return date_edit

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        set_accessible(scroll, "scroll_insurance", "scroll_insurance")

        content = QWidget()
        set_accessible(content, "content_insurance", "content_insurance")
        root = QVBoxLayout(content)
        root.setContentsMargins(8, 8, 8, 8)

        plan_group = QGroupBox("Insurance Plan")
        set_accessible(plan_group, "grp_insurance_plan", "grp_insurance_plan")
        plan_form = QFormLayout(plan_group)
        self._configure_form(plan_form)

        self.cmb_plan_type = self._combo("cmb_plan_type", PLAN_TYPES)
        self.txt_carrier = self._line_edit("txt_carrier")
        self.cmb_relationship = self._combo("cmb_relationship", RELATIONSHIPS)
        self.txt_cardholder_name = self._line_edit("txt_cardholder_name")

        self._plan_rows: list[tuple] = []
        for label_text, widget in [
            ("Plan Type:", self.cmb_plan_type),
            ("Carrier:", self.txt_carrier),
            ("Relationship:", self.cmb_relationship),
            ("Cardholder Name:", self.txt_cardholder_name),
        ]:
            label = QLabel(label_text)
            plan_form.addRow(label, widget)
            self._plan_rows.append((label, widget))

        policy_group = QGroupBox("Policy Details")
        set_accessible(policy_group, "grp_insurance_policy", "grp_insurance_policy")
        policy_form = QFormLayout(policy_group)
        self._configure_form(policy_form)

        self.txt_policy_number = self._line_edit("txt_policy_number")
        self.txt_group_number = self._line_edit("txt_group_number")
        self.txt_expiry_date = self._date_edit("txt_expiry_date")

        self._policy_rows: list[tuple] = []
        for label_text, widget in [
            ("Policy Number:", self.txt_policy_number),
            ("Group Number:", self.txt_group_number),
            ("Expiry Date:", self.txt_expiry_date),
        ]:
            label = QLabel(label_text)
            policy_form.addRow(label, widget)
            self._policy_rows.append((label, widget))

        self._root_layout = root
        self._content = content
        self._grp_plan = plan_group
        self._grp_policy = policy_group
        self._plan_form = plan_form
        self._policy_form = policy_form
        self._randomized_layout = False

        root.addWidget(plan_group)
        root.addWidget(policy_group)
        root.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def set_randomized_layout(self, enabled: bool) -> None:
        if enabled == self._randomized_layout:
            return
        self._randomized_layout = enabled
        if enabled:
            shuffle_widgets_in_layout(
                self._root_layout,
                [self._grp_plan, self._grp_policy],
                host=self._content,
            )
            shuffle_form_rows(self._plan_form, self._plan_rows)
            shuffle_form_rows(self._policy_form, self._policy_rows)
        else:
            clear_layout(self._root_layout, self._content)
            self._root_layout.addWidget(self._grp_plan)
            self._root_layout.addWidget(self._grp_policy)
            self._root_layout.addStretch()
            restore_form_rows(self._plan_form, self._plan_rows)
            restore_form_rows(self._policy_form, self._policy_rows)

    def _expiry_value(self) -> str:
        if self.txt_expiry_date.date() == self._expiry_empty:
            return ""
        return self.txt_expiry_date.date().toString("yyyy-MM-dd")

    def _set_expiry(self, value: str) -> None:
        expiry = value.strip()
        if not expiry:
            self.txt_expiry_date.setDate(self._expiry_empty)
            return
        parsed = QDate.fromString(expiry, "yyyy-MM-dd")
        if parsed.isValid():
            self.txt_expiry_date.setDate(parsed)

    def get_field_values(self) -> dict[str, str]:
        return {
            "plan_type": self.cmb_plan_type.currentText(),
            "carrier": self.txt_carrier.text().strip(),
            "policy_number": self.txt_policy_number.text().strip(),
            "group_number": self.txt_group_number.text().strip(),
            "expiry_date": self._expiry_value(),
            "relationship": self.cmb_relationship.currentText(),
            "cardholder_name": self.txt_cardholder_name.text().strip(),
        }

    def set_field_values(self, data: dict[str, str]) -> None:
        plan_type = str(data.get("plan_type", ""))
        idx = self.cmb_plan_type.findText(plan_type)
        if idx >= 0:
            self.cmb_plan_type.setCurrentIndex(idx)

        self.txt_carrier.setText(str(data.get("carrier", "")))
        self.txt_policy_number.setText(str(data.get("policy_number", "")))
        self.txt_group_number.setText(str(data.get("group_number", "")))
        self._set_expiry(str(data.get("expiry_date", "")))

        relationship = str(data.get("relationship", ""))
        idx = self.cmb_relationship.findText(relationship)
        if idx >= 0:
            self.cmb_relationship.setCurrentIndex(idx)

        self.txt_cardholder_name.setText(str(data.get("cardholder_name", "")))

    def clear_fields(self) -> None:
        self.set_field_values({})

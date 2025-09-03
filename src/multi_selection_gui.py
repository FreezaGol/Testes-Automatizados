# src/multi_selection_gui.py
import sys
import json
from PySide6.QtWidgets import (QApplication, QDialog, QTableWidget, QTableWidgetItem, 
                               QVBoxLayout, QPushButton, QHeaderView, QCheckBox, QWidget, QHBoxLayout)
from PySide6.QtCore import Qt

class MultiSelectionDialog(QDialog):
    def __init__(self, title, items, headers):
        super().__init__()
        self.setWindowTitle(title)
        self.selected_codes = []
        self.items = items
        self.headers = headers
        self.resize(800, 600)
        self.layout = QVBoxLayout()
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(len(self.headers))
        self.table_widget.setHorizontalHeaderLabels(self.headers)
        self.table_widget.setRowCount(len(self.items))

        for row, item_data in enumerate(self.items):
            # Coluna 0: Checkbox
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox = QCheckBox()
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_widget.setLayout(checkbox_layout)
            self.table_widget.setCellWidget(row, 0, checkbox_widget)

            # Outras colunas
            for col, header in enumerate(self.headers[1:], 1):
                # O nome da chave no dicionário é o header em minúsculas
                key = header.lower()
                table_item = QTableWidgetItem(str(item_data.get(key, '')))
                table_item.setData(Qt.UserRole, item_data.get('codigo_produto')) # Armazena o código no item
                self.table_widget.setItem(row, col, table_item)

        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ok_button = QPushButton("OK")

        self.layout.addWidget(self.table_widget)
        self.layout.addWidget(self.ok_button)
        self.setLayout(self.layout)
        self.ok_button.clicked.connect(self.on_ok)

    def on_ok(self):
        for row in range(self.table_widget.rowCount()):
            if self.table_widget.cellWidget(row, 0).findChild(QCheckBox).isChecked():
                # Pega o código do produto armazenado no item da segunda coluna
                product_code = self.table_widget.item(row, 1).data(Qt.UserRole)
                self.selected_codes.append(product_code)
        self.accept()

def main():
    data_file = 'temp_gui_data.json'
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        title = data.get('title', 'Selecione os Itens')
        items = data.get('items', [])
        headers = data.get('headers', [])
    except Exception:
        sys.exit(1)

    app = QApplication(sys.argv)
    dialog = MultiSelectionDialog(title, items, headers)
    dialog.exec()

    # Retorna a lista de códigos selecionados como uma string JSON
    print(json.dumps(dialog.selected_codes))
    sys.exit(0)

if __name__ == "__main__":
    main()
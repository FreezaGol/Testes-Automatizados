# src/selection_gui.py
import sys
import json
from PySide6.QtWidgets import QApplication, QDialog, QListWidget, QVBoxLayout, QPushButton
from PySide6.QtCore import Qt

class SelectionDialog(QDialog):
    def __init__(self, title, items):
        super().__init__()
        self.setWindowTitle(title)
        self.selected_code = None
        self.items = items

        self.layout = QVBoxLayout()
        self.list_widget = QListWidget()
        for item in self.items:
            self.list_widget.addItem(item['display'])
        
        self.ok_button = QPushButton("OK")

        self.layout.addWidget(self.list_widget)
        self.layout.addWidget(self.ok_button)
        self.setLayout(self.layout)

        self.ok_button.clicked.connect(self.on_ok)
        self.list_widget.itemDoubleClicked.connect(self.on_ok)
        self.list_widget.setCurrentRow(0)
        self.list_widget.setFocus()

    def on_ok(self):
        selected_item = self.list_widget.currentItem()
        if selected_item:
            for item in self.items:
                if item['display'] == selected_item.text():
                    self.selected_code = item['code']
                    break
        self.accept()

def main():
    data_file = 'temp_gui_data.json'
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        title = data.get('title', 'Selecione um Item')
        items = data.get('items', [])
    except Exception:
        sys.exit(1)

    app = QApplication(sys.argv)
    dialog = SelectionDialog(title, items)
    dialog.exec()

    # --- MUDANÇA PRINCIPAL ---
    # Se um código foi selecionado, imprime ele na saída padrão (stdout)
    if dialog.selected_code:
        print(dialog.selected_code)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
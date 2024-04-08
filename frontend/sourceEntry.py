from PySide6.QtWidgets import QApplication, QDialogButtonBox, QGridLayout, QDialog, QTextEdit
from PySide6.QtCore import Qt

class entryWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        layout = QGridLayout(self)
        
        self.input = QTextEdit(self)
        layout.addWidget(self.input, 0, 0)
        
        layout.addWidget(buttonBox, 1, 0, Qt.AlignCenter)
        
        self.setWindowTitle("Source Entry")
        self.input.setPlaceholderText("Enter source here")
        
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
    
    def getInput(self):
        return self.input.toPlainText()

def main():
    import sys
    QApplication(sys.argv)
    dialog = entryWindow()
    if dialog.exec():
        print(dialog.getInputs())
    exit(0)

if __name__ == '__main__':
    main()
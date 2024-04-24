from PySide6.QtWidgets import(
    QApplication, QDialogButtonBox, QGridLayout, QDialog, 
    QTextEdit, QTabWidget, QWidget, QPushButton,
    QFormLayout, QGroupBox, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal, QObject
from elit_tokenizer import EnglishTokenizer

import path
import sys


directory = path.Path(__file__).abspath()
sys.path.append(directory.parent.parent)

from dataClassDefinitions import sourceWithBigramModel  # noqa: E402

class entryWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        layout = QGridLayout(self)
        
        self.input = QTextEdit(self)
        layout.addWidget(self.input, 0, 0)
        
        layout.addWidget(buttonBox, 1, 0, Qt.AlignCenter)
        
        self.setWindowTitle("Suggest Fix")
        self.input.setPlaceholderText("Sorry, but we can't find an automatic fix, please suggest a fix here.")
        
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
    
    def getInput(self):
        return self.input.toPlainText()

class sourceEntryForm(QDialog):
    def __init__(self):
        super().__init__()
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        
        self.setWindowTitle("Enter Source Info")
        layout = QFormLayout()
        self.sourceName = QTextEdit(self)
        self.sourceName.setPlaceholderText("Enter source name here")
        self.sourceName.setFixedSize(300, 50)
        layout.addRow("Source Name", self.sourceName)
        
        self.parenthetical = QTextEdit(self)
        self.parenthetical.setPlaceholderText("Enter parenthetical citation here")
        self.parenthetical.setFixedSize(300, 50)
        layout.addRow("Parenthetical", self.parenthetical)
        
        self.bibliographic = QTextEdit(self)
        self.bibliographic.setPlaceholderText("Enter bibliographic citation here")
        self.bibliographic.setFixedSize(300, 150)
        layout.addRow("Bibliographic", self.bibliographic)
        
        layout.addRow(buttonBox)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        
        self.setLayout(layout)
        
    def getInput(self) -> sourceWithBigramModel:
        new = sourceWithBigramModel()
        new.sourceName = self.sourceName.toPlainText()
        new.parenthetical = self.parenthetical.toPlainText()
        new.bibliographic = self.bibliographic.toPlainText()
        
        return new


class advancedEntryWindow(QWidget):
    def __init__(self, sources, parent=None):
        super().__init__(parent)
        self.signals = self.mySignals()
        self.editedSources = []
        
        self.setWindowTitle("Sources")
        
        layout = QHBoxLayout()
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        self.newSources = newSources()
        self.tabs.addTab(self.newSources, "New Sources")
        self.newSources.confirmButton.clicked.connect(self.addSource)
        
        for source in sources:
            self.tabs.addTab(Source(source), source.sourceName)
            
        self.setLayout(layout)
            
    def addSource(self):
        sourceText = self.newSources.text.toPlainText()
        getInfo = sourceEntryForm()
        if getInfo.exec():
            sourceInfo = getInfo.getInput()
            
        sourceInfo.sourceLiteralText = sourceText
        sourceInfo.sourceTokenizedText = EnglishTokenizer().tokenize(sourceText)[0]
        
        self.tabs.addTab(Source(sourceInfo), sourceInfo.sourceName)
        self.editedSources.append(sourceInfo)
        self.signals.newSource.emit(sourceInfo)
    
    class mySignals(QObject):
        newSource = Signal(sourceWithBigramModel)


class newSources(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()
        self.layout.setAlignment(Qt.AlignCenter)
        
        self.text = QTextEdit(self)
        self.text.setPlaceholderText("Enter source here")
        self.layout.addWidget(self.text, 0, 0, 1, 1)
        
        buttonBox = QGroupBox()
        buttonLayout = QHBoxLayout()
        
        self.cancelButton = QPushButton("Cancel")
        self.confirmButton = QPushButton("Confirm")
        
        buttonLayout.addWidget(self.cancelButton)
        buttonLayout.addWidget(self.confirmButton)
        
        buttonBox.setLayout(buttonLayout)
        self.layout.addWidget(buttonBox, 1, 0, 1, 1)
        
        self.cancelButton.clicked.connect(self.clear)
        
        self.setLayout(self.layout)
        
    def clear(self):
        self.text.clear()
        
    def getInputs(self):
        return self.text.toPlainText()

     
class Source(newSources):
    def __init__(self, source: sourceWithBigramModel, edited=False):
        super().__init__()
        self.source = source
        self.edited = edited
        self.text.setText(source.sourceLiteralText)
        self.confirmButton.clicked.connect(self.confirm)
        self.text.textChanged.connect(self.pendingEdit)
        
        self.cancelButton.setDisabled(True)
        self.confirmButton.setDisabled(True)
        
    def clear(self):
        self.text.setText(self.source)
        self.editFinalized()
        
    def confirm(self):
        self.source = self.text.toPlainText()
        self.edited = True
        self.editFinalized()

    def pendingEdit(self):
        self.cancelButton.setDisabled(False)
        self.confirmButton.setDisabled(False)
    
    def editFinalized(self):
        self.cancelButton.setDisabled(True)
        self.confirmButton.setDisabled(True)


def main():
    import sys
    QApplication(sys.argv)
    dialog = entryWindow()
    if dialog.exec():
        print(dialog.getInputs())
    exit(0)

if __name__ == '__main__':
    main()
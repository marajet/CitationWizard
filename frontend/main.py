from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QMainWindow, QTextEdit, QToolBar, QSpinBox, QComboBox, QFileDialog, QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel
from PySide6.QtCore import QThreadPool, Qt, QTimer
from PySide6.QtGui import QAction, QPixmap, QFont

from asyncWorker import Worker
from elit_tokenizer import EnglishTokenizer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.threadPool = QThreadPool()
        
        self.text = textWindow(self.threadPool)
        self.issues = issueList()
        
        self.path = ""
        
        font = QFont('Times New Roman', 12)
        self.text.setFont(font)
        
        layout = QHBoxLayout()
        layout.addWidget(self.text)
        layout.addWidget(self.issues)
        
        box = QGroupBox()
        box.setLayout(layout)
        
        self.setCentralWidget(box)
        
        self.showMaximized()
        
        self.tool_bar = toolBar(self)
        self.addToolBar(self.tool_bar)

    def setFontSize(self, size):
        self.text.setFontPointSize(size)
        
    def setFont(self):
        font = self.tool_bar.fontBox.currentText()
        self.text.setCurrentFont(QFont(font))
        
    def saveFile(self):
        if self.path == "":
            self.saveFile_as()
            text = self.text.toPlainText()
        try:
            with open(self.path, 'w') as f:
                f.write(text)
                self.update_title()
        except Exception as e:
            print(e)
    
    def saveFile_as(self):
        self.path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "text documents (*.text); Text documents (*.txt); All files (*.*)")
        if self.path == "":
            return
        
        text = self.text.toPlainText()
        try:
            with open(self.path, 'w') as f:
                f.write(text)
                self.update_title()
        except Exception as e:
            print(e)
            

class textWindow(QTextEdit):
    def __init__(self, threadPool):
        super().__init__()
        self.threadPool = threadPool
        self.typingTimer = QTimer()
        self.typingTimer.setSingleShot(True)
        self.typingTimer.timeout.connect(self.handleNewText)
        
        self.text = ""
        
        self.setAcceptRichText(False)
        
        self.textChanged.connect(self.handleTyping)
        
    def boldText(self):
        if self.fontWeight() == QFont.Bold:
            self.setFontWeight(QFont.Normal)
        else:
            self.setFontWeight(QFont.Bold) 
        
    def italicText(self):
        state = self.fontItalic()
        
        self.setFontItalic(not(state))
    
    def underlineText(self):
        state = self.fontUnderline()
        
        self.setFontUnderline(not(state))

    def handleTyping(self):
        self.typingTimer.start(1000)
    
    def handleNewText(self):
        newText = self.getNewText()
        worker = Worker(parseNewText, newText)
        
        worker.signals.result.connect(self.updateIssues)
        self.threadPool.start(worker)

    def getNewText(self):
        oldText = self.text
        currText = self.toPlainText()

        self.text = currText

        return getNewTextHelper(oldText, currText)
    
    def updateIssues(self, tokens):
        worker = Worker(findIssues, tokens)
        worker.signals.result.connect(self.updateIssuesList)
        self.threadPool.start(worker)
        
    def updateIssuesList(self, issues):
        self.issues.updateIssues(issues)

       
class fontSpinner(QSpinBox):
    def __init__(self):
        super().__init__()
        self.setRange(1, 100)
        self.setValue(12)
        self.setStyleSheet(
            "QSpinBox { color: black; background: white; border: 1px solid black; } "
            "QSpinBox::up-button { background: gray; border-left: 1px solid black; border-right: 1px solid black; border-bottom: 1px solid black;}"
            "QSpinBox::up-arrow { border-left: 3px solid none;"
            "border-right: 3px solid none; border-bottom: 3px solid black; width: 0px; height: 0px; }"
            "QSpinBox::down-button { background: gray; border-left: 1px solid black; border-right: 1px solid black;}"
            "QSpinBox::down-arrow { border-left: 3px solid none;"
            "border-right: 3px solid none; border-top: 3px solid black; width: 0px; height: 0px; }"
        )


class fontBox(QComboBox):
    def __init__(self):
        super().__init__()
        self.addItems(['Times New Roman', 'Comic Sans MS', 'Helvetica'])
        self.setFixedWidth(175)
        self.setStyleSheet(
            "QComboBox { color: black; background: white; border: 1px solid black; } "
            "QComboBox::drop-down { background: gray; border-left: 1px solid black; border-right: 1px solid black; border-bottom: 1px solid black;}"
            "QComboBox::down-arrow { border-left: 3px solid none;"
            "border-right: 3px solid none; border-top: 3px solid black; width: 0px; height: 0px; }"
        )

      
class toolBar(QToolBar):
    def __init__(self, mainWindow):
        super().__init__()
        self.mainWindow = mainWindow
        self.setStyleSheet("background: gray; border: none; spacing: 15px; padding-top: 5px; padding-bottom: 5px;")
        self.setMovable(False)
        
        self.addSeparator()
        
        saveBtn = QAction(QPixmap('frontend/icons/save.png'), 'Save', self)
        saveBtn.setToolTip('Save')
        saveBtn.triggered.connect(self.mainWindow.saveFile)
        self.addAction(saveBtn)
        
        self.addSeparator()
        
        undoBtn = QAction(QPixmap('frontend/icons/undo.png'), 'Undo', self)
        undoBtn.setToolTip('Undo last action')
        undoBtn.triggered.connect(self.mainWindow.text.undo)
        self.addAction(undoBtn)
        
        redoBtn = QAction(QPixmap('frontend/icons/redo.png'), 'Redo', self)
        redoBtn.setToolTip('Redo last action')
        redoBtn.triggered.connect(self.mainWindow.text.redo)
        self.addAction(redoBtn)
        
        self.addSeparator()
        
        self.fontSizeBox = fontSpinner()
        self.fontSizeBox.valueChanged.connect(self.mainWindow.setFontSize)
        self.addWidget(self.fontSizeBox)
        
        self.addSeparator()
        
        self.fontBox = fontBox()
        self.fontBox.activated.connect(self.mainWindow.setFont)
        self.addWidget(self.fontBox)
        
        self.addSeparator()
        
        leftAlign = QAction(QPixmap('frontend/icons/align-left.png'), 'Left Align', self)
        leftAlign.setToolTip('Left Align')
        leftAlign.triggered.connect(lambda: self.mainWindow.text.setAlignment(Qt.AlignLeft))
        self.addAction(leftAlign)
        
        centerAlign = QAction(QPixmap('frontend/icons/align-center.png'), 'Center Align', self)
        centerAlign.setToolTip('Center Align')
        centerAlign.triggered.connect(lambda: self.mainWindow.text.setAlignment(Qt.AlignCenter))
        self.addAction(centerAlign)
        
        rightAlign = QAction(QPixmap('frontend/icons/align-right.png'), 'Right Align', self)
        rightAlign.setToolTip('Right Align')
        rightAlign.triggered.connect(lambda: self.mainWindow.text.setAlignment(Qt.AlignRight))
        self.addAction(rightAlign)
        
        self.addSeparator()
        
        bold = QAction(QPixmap('frontend/icons/bold.png'), 'Bold', self)
        bold.setToolTip('Bold')
        bold.triggered.connect(self.mainWindow.text.boldText)
        self.addAction(bold)
        
        italic = QAction(QPixmap('frontend/icons/italic.png'), 'Italic', self)
        italic.setToolTip('Italic')
        italic.triggered.connect(self.mainWindow.text.italicText)
        self.addAction(italic)
        
        underline = QAction(QPixmap('frontend/icons/underline.png'), 'Underline', self)
        underline.setToolTip('Underline')
        underline.triggered.connect(self.mainWindow.text.underlineText)
        self.addAction(underline)
        

class issueList(QScrollArea):
    def __init__(self):
        super().__init__()
        
        self.box = QGroupBox()
        
        self.boxLayout = QVBoxLayout()
        self.boxLayout.setAlignment(Qt.AlignTop)
        self.boxLayout.setSpacing(0)
        self.boxLayout.setContentsMargins(0, 0, 0, 0)
        
        self.box.setLayout(self.boxLayout)
        
        self.setWidget(self.box)
        
        self.setMaximumWidth(200)
        self.setWidgetResizable(True)
        
        testInfo = {
            'issueTag': 'test',
            'issueColor': 'blue'
        }
        
        self.addIssue(testInfo)
        
        testInfo = {
            'issueTag': 'test',
            'issueColor': 'purple'
        }
        
        self.addIssue(testInfo)
        
    def addIssue(self, issueInfo):
        newIssue = issue(issueInfo)
        self.boxLayout.addWidget(newIssue)
    

class issue(QWidget):
    def __init__(self, issueInfo):
        super().__init__()
        self.issueInfo = issueInfo
        self.layout = QVBoxLayout()
        
        self.layout.setContentsMargins(1, 5, 1, 5)
        
        box = QGroupBox()
        boxLayout = QHBoxLayout()
        
        tag = QLabel(self.issueInfo['issueTag'])
        tag.setStyleSheet("background: transparent;")
        
        boxLayout.addWidget(tag)
        
        box.setStyleSheet("background: " + self.issueInfo['issueColor'] + "; border-radius: 10px")
        
        box.setLayout(boxLayout)
        
        self.layout.addWidget(box)
        
        self.setLayout(self.layout)


def getNewTextHelper(oldText, currText):
    return currText.removeprefix(oldText)

def parseNewText(text):
    tokens = EnglishTokenizer().tokenize(text)[0]
    return tokens

def findIssues(tokens):
    pass

 
def main():
    app = QApplication([])
    loader = QUiLoader()  # noqa: F841
    window = MainWindow()
    window.setWindowTitle("Citation Wizard")
    window.show()
    app.exec()


if __name__ == '__main__':
    main()
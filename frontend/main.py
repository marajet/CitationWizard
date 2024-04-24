from PySide6.QtUiTools import QUiLoader

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QToolBar, 
    QSpinBox, QComboBox, QFileDialog, QScrollArea, 
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
    QLabel, QPushButton
)

from PySide6.QtCore import QThreadPool, Qt, QTimer
from PySide6.QtGui import QAction, QPixmap, QFont, QColor

from asyncWorker import Worker
from elit_tokenizer import EnglishTokenizer
from syntax import Highlighter
from sourceEntry import advancedEntryWindow, entryWindow

import path
import sys

directory = path.Path(__file__).abspath()
sys.path.append(directory.parent.parent)

from backend.quote_matching import find_quote_errors, find_style_matches
from backend.api_requests import copyleaks_login, plagiarism_check
from dataClassDefinitions import inputWithBigramModel, sourceWithBigramModel, defaultFunctionInput



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.threadPool = QThreadPool()
        
        self.text = textWindow(self.threadPool, self)
        self.highlighter = Highlighter(self.text)
        self.issues = issueList(self)
        
        self.path = ""
        
        font = QFont('Times New Roman', 24)
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
            
    def fixIssue(self, issue):
        text = self.text.toPlainText()
        if issue.issueInfo['suggestedFix'] is None:
            entry = entryWindow()
            if entry.exec():
                issue.issueInfo['suggestedFix'] = entry.getInput()
        
        print(issue.issueInfo)
        
        newText = text.replace(issue.issueInfo['issueText'], issue.issueInfo['suggestedFix'])
        self.text.setText(newText)
        
        self.highlighter.removeHighlight(issue.issueInfo['issueText'])
        self.issues.removeIssue(issue.issueInfo)
        self.text.justFixed = True
        self.text.text = self.text.toPlainText()
        
    def newSource(self):
        self.textEntry = advancedEntryWindow(self.text.worksCited)
        self.textEntry.signals.newSource.connect(lambda source: self.text.worksCited.append(source))
        self.textEntry.show()


class textWindow(QTextEdit):
    def __init__(self, threadPool, manager):
        super().__init__()
        self.justFixed = False
        self.worksCited = []
        self.manager = manager
        self.copyleaksToken = copyleaks_login()
        self.possibleColor = [Qt.red, Qt.blue, Qt.green, Qt.darkRed, Qt.darkBlue, Qt.darkGreen, Qt.cyan, Qt.magenta, Qt.yellow, Qt.darkCyan, Qt.darkMagenta, Qt.darkYellow]
        self.possibleColorIndex = 0
        self.issueColors = {
            
        }
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
        if self.justFixed:
            self.justFixed = False
            return
        newText = self.getNewText()
        worker = Worker(parseNewText, newText)
        
        worker.signals.result.connect(self.updateIssues)
        self.threadPool.start(worker)

    def getNewText(self):
        oldText = self.text
        currText = self.toPlainText()

        self.text = currText
        
        newText = getNewTextHelper(oldText, currText)
        
        return newText
    
    def updateIssues(self, info):
        text = info[0]
        tokens = info[1]
        
        worker = Worker(findIssues, text, tokens, self.worksCited, self.copyleaksToken)
        worker.signals.result.connect(self.updateIssuesList)
        
        self.threadPool.start(worker)
        
    def updateIssuesList(self, issues):
        text = self.toPlainText()
        textTokens = EnglishTokenizer().tokenize(text)
        
        for issue in issues:
            issueText = ""
            if isinstance(issue['textToFix'], str):
                issueText = issue['textToFix']
            else:
                index = contains(issue['textToFix'], textTokens[0])
                if index:
                    trueIndex = (textTokens[1][index[0]][0], textTokens[1][index[1] - 1][1])
                    
                    issueText = text[trueIndex[0]:trueIndex[1]]
                
            self.makeIssueColor(issue['typeOfError'])
                
            self.highlightIssue(issueText, self.issueColors[issue['typeOfError']])
            issue['issueText'] = issueText

            self.manager.issues.addIssue(issue)
           
    def highlightIssue(self, text, color):
        self.manager.highlighter.addHighlight(text, color)
        
    def makeIssueColor(self, issue):
        if issue not in self.issueColors.keys():
            self.issueColors[issue] = self.possibleColor[self.possibleColorIndex]
            self.possibleColorIndex += 1
            if self.possibleColorIndex == len(self.possibleColor):
                self.possibleColorIndex = 0


class fontSpinner(QSpinBox):
    def __init__(self):
        super().__init__()
        self.setRange(1, 100)
        self.setValue(24)
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
        self.setStyleSheet("QToolBar { background: gray; border: none; spacing: 15px; padding-top: 5px; padding-bottom: 5px;} QToolButton:pressed { background-color: rgb(255,255,255);}")
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
        
        self.addSeparator()
        
        sourceBtn = QAction(QPixmap('frontend/icons/source.png'), 'Source', self)
        sourceBtn.setToolTip('Press To Enter Source')
        sourceBtn.triggered.connect(self.mainWindow.newSource)
        self.addAction(sourceBtn)


class issueList(QScrollArea):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        
        self.box = QGroupBox()
        
        self.boxLayout = QVBoxLayout()
        self.boxLayout.setAlignment(Qt.AlignTop)
        self.boxLayout.setSpacing(0)
        self.boxLayout.setContentsMargins(0, 0, 0, 0)
        
        self.box.setLayout(self.boxLayout)
        
        self.setWidget(self.box)
        
        self.setMaximumWidth(200)
        self.setWidgetResizable(True)
        
    def addIssue(self, issueInfo):
        for i in range(self.boxLayout.count()):
            if self.boxLayout.itemAt(i).widget().issueInfo == issueInfo:
                return
        newIssue = issue(issueInfo, self.manager)
        self.boxLayout.addWidget(newIssue)
    
    def removeIssue(self, issueInfo):
        for i in range(self.boxLayout.count()):
            if self.boxLayout.itemAt(i).widget().issueInfo == issueInfo:
                self.boxLayout.itemAt(i).widget().deleteLater()
                self.update()


class issue(QWidget):
    def __init__(self, issueInfo, manager):
        super().__init__()
        self.manager = manager
        self.issueInfo = issueInfo
        self.layout = QVBoxLayout()
        
        self.layout.setContentsMargins(1, 5, 1, 5)
        
        box = QGroupBox()
        boxLayout = QHBoxLayout()
        
        tag = QLabel(self.issueInfo['typeOfError'])
        tag.setStyleSheet("background: transparent;")
        boxLayout.addWidget(tag)
        
        fix = QPushButton("fix Issue")
        fix.setStyleSheet("QPushButton { background: rgba(0, 0, 0, 0.5); border-radius: 5px; } QPushButton:Pressed { background-color: rgb(255,255,255);}")
        fix.clicked.connect(lambda: self.manager.fixIssue(self))
        boxLayout.addWidget(fix)
        
        box.setStyleSheet("background: rgba" + str(QColor(self.manager.text.issueColors[self.issueInfo['typeOfError']]).getRgb()) + "; border-radius: 10px")
        
        box.setLayout(boxLayout)
        
        self.layout.addWidget(box)
        
        self.setLayout(self.layout)


def getNewTextHelper(oldText, currText):
    return currText.removeprefix(oldText)


def parseNewText(text):
    tokens = EnglishTokenizer().tokenize(text)
    return text, tokens


def findIssues(text, tokens, worksCited: list[sourceWithBigramModel], copyleaksToken): #TODO update to call others methods
    if len(tokens[0]) < 5:
        return []
    
    totalErrors = []
    
    # textInfo = inputWithBigramModel()
    # textInfo.textInputLiteral = text
    # textInfo.textInputTokens = tokens[0]
    # textInfo.sources = worksCited
    
    
    # newSources, newErrors = find_style_matches(textInfo)
    
    # for item in newErrors:
    #     totalErrors.append(item)
    
    # textInfo = defaultFunctionInput()
    # textInfo.textInputLiteral = text
    # textInfo.textInputTokenized = tokens[0]
    # textInfo.sources = worksCited
    
    # print(textInfo.textInputLiteral, textInfo.textInputTokenized)
    
    # newErrors = find_quote_errors(textInfo)
    
    # for item in newErrors:
    #     totalErrors.append(item)
    
    newErrors = plagiarism_check(text, copyleaksToken)
    
    for item in newErrors:
        totalErrors.append(item)

    return newErrors


def contains(small, big):
    for i in range(len(big)-len(small)+1):
        for j in range(len(small)):
            if big[i+j] != small[j]:
                break
        else:
            return i, i+len(small)
    return False

 
def main():
    app = QApplication([])
    loader = QUiLoader()  # noqa: F841
    window = MainWindow()
    # window = advancedEntryWindow([])
    window.setWindowTitle("Citation Wizard")
    window.show()
    app.exec()


if __name__ == '__main__':
    main()
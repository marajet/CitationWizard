from PySide6.QtCore import Qt
from PySide6.QtCore import QRegularExpression as QRegExp
from PySide6.QtGui import QTextCharFormat, QFont, QSyntaxHighlighter, QBrush

class Highlighter( QSyntaxHighlighter ):

    def __init__( self, parent):
      QSyntaxHighlighter.__init__( self, parent )
      self.parent = parent

      self.highlightingRules = []

    def highlightBlock( self, text ):
        for rule in self.highlightingRules:
            expression = QRegExp( rule[1].pattern )
            info = expression.match( text )
            index = info.capturedStart()
            length = info.capturedLength()
            self.setFormat( index, length, rule[1].format )
        
        self.setCurrentBlockState( 0 )
      
    def addHighlight(self, text, color):
        originalText = text
        toReplace = ['\\', '^', '$', '.', '|', '?', '*', '+', '(', ')', '[', ']', '{', '}', '!', '&', ':', ';']
        for char in text:
            if char in toReplace:
                text = text.replace(char, '\\' + char)
        
        brush = QBrush(color, Qt.SolidPattern)
        format = QTextCharFormat()
        format.setForeground(brush)
        format.setFontWeight(QFont.Bold)
        
        self.highlightingRules.append((originalText, HighlightingRule(text, color)))
    
    def removeHighlight(self, text):
        for rule in self.highlightingRules:
            if rule[0] == text:
                self.highlightingRules.remove(rule)

class HighlightingRule():
  def __init__( self, index, format ):
    self.pattern = index
    self.format = format
from dataclasses import dataclass

@dataclass
class sampleDataclass():
    myText: str
    myList: list
    
    DefaultValueExample: int = 0 # Data fields with default values must come after those without
    
    def to_dict(self): #Make sure to define a to_dict method
        return {
            "myText": self.myText,
            "myList": self.myList,
            "DefaultValueExample": self.DefaultValueExample
        }

@dataclass
class source():
    sourceLiteralText: str = None #Complete text of source
    sourceTokenizedText: list = None #tokenized version of source text
    parenthetical: str = None #Parenthetical citation for this source

@dataclass
class defaultFunctionInput():
    textInputLiteral: str = None #The unprocessed text to search
    textInputTokenized: list = None #Tokenized version of the text
    
    sources: list[source] = None #A list of source objects representing all input sources

@dataclass
class sourceWithBigramModel():
    sourceLiteralText: str = None #Complete text of source
    sourceTokenizedText: list = None #tokenized version of source text
    parenthetical: str = None #Parenthetical citation for this source
    bigramModel: dict = None #The bigram model for the source, if one has been created
                            #Bigram model will be created in backend once and reused if needed again

@dataclass
class inputWithBigramModel():
    textInputLiteral: str = None #The unprocessed text to search
    textInputTokenized: str = None #Tokenized version of the text

    sources: list[sourceWithBigramModel] = None #A list of source objects (pot. including the bigram model)



   
if __name__ == "__main__": #Demo
    myData = sampleDataclass("Hello", myList=[1,2,3,4,5])
    print(myData.to_dict())
    myData2 = sampleDataclass("Hello", [1, 2, 3, 4, 5], 5)
    print(myData2.to_dict())
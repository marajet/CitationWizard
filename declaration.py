#Input a list of tokens generated by the elit_tokenizer we used in class
#Example
#tokens = ["This", "is", "a", "sentence" "."]

#Output of your functions
errors = [] # Should be a list of dictionaries with the keys 'typeOfError', 'textToFix', 'suggestedFix'

errorDict = {
    'typeOfError': '', # A simple label describing the error ex. 'noParenthetical'
    'textToFix': '', # A sub-list of the originally fed list of tokens ex. ["is", "a"]
    'suggestedFix': '' # A string which will replace the textToFix ex. "isn't a"
}
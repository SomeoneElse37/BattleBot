from odf.opendocument import OpenDocumentSpreadsheet
from odf.style import Style, TextProperties, TableColumnProperties, Map, TableRowProperties
from odf.number import NumberStyle, CurrencyStyle, CurrencySymbol,  Number,  Text
from odf.text import P
from odf.table import Table, TableColumn, TableRow, TableCell

#needed for random string generator
import string
import random

def _createAndAddStyle(styleContainer,**args):
    new_style = Style(**args)
    styleContainer.addElement(new_style)
    #good chance you want to edit the object after calling this
    return new_style

def _createAndAddElement(container,func,**args):
    newElement = func(**args)
    container.addElement(newElement)
    #good chance you want to edit the object after calling this
    return newElement

def _easyAddRowsWithCells(table,rowStyle,textCell1,textCell2=False):
    tr = _createAndAddElement(table,TableRow,stylename=rowStyle)
    _addCellsToRow(tr,textCell1,textCell2)
    #good chance you want to edit the object after calling this
    return tr

def _addCellsToRow(tr,textCell1,textCell2=False,addEmpty=False):
    #Cells contain so little that more often then not you don't care about them that much
    #Thus we don't return them
    if addEmpty:
        _createAndAddElement(tr,TableCell,valuetype="string").addElement(P(text=""))
    _createAndAddElement(tr,TableCell,valuetype="string").addElement(P(text=textCell1))
    if textCell2:
        _createAndAddElement(tr,TableCell,valuetype="string").addElement(P(text=textCell2))
#needed to generate a random file name
def _randomStringGen(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))
#Call this with an dictonary of characters, where the keys are their name to generate the Excel sheet
#grid is not yet implemented
#path NEEDS to contain an file extension!
def generateODSFromCharacters(characters,grid=False,path=False):
    doc = OpenDocumentSpreadsheet()
    # lets generate the correct styles first. We start by creating the style for the columns of the grid
    # this to properly make the cells 1 cm wide
    grid_col_style = _createAndAddStyle(doc.automaticstyles,name="grid_col", family = "table-column")
    grid_col_style.addElement(TableColumnProperties(columnwidth="1cm"))
    #this makes the rows 1 cm heigh
    grid_row_style = _createAndAddStyle(doc.automaticstyles,name="grid_row",family="table-row")
    grid_row_style.addElement(TableRowProperties(rowheight="1cm"))
    #this style is used for the column from the character list. 
    character_col_style = _createAndAddStyle(doc.automaticstyles,name="character_col",family="table-column")
    character_col_style.addElement(TableColumnProperties(columnwidth="3cm"))

    #now we have gotten to the "fun part", generating the character list.
    #We start by creating the table that will hold all the data
    table = _createAndAddElement(doc.spreadsheet,Table,name="combined")
    #We then add the collumns that we will need, this sets their style correctly
    table.addElement(TableColumn(stylename=character_col_style))
    table.addElement(TableColumn(stylename=character_col_style))
    #We now are slowly but surely generating more and more table rows, each one nicely stored into this array
    tableRows = []
    #used to more easily loop over the attributes
    atributes = ["HP","ACC","EVA","ATK","DEF","SPD"]
    #make the table header. First field is the characters name
    tableRows.append(
        _easyAddRowsWithCells(
            table,
            grid_row_style,
            "name"
        )
    )
    #Now we put all the names of the stats in the header
    for att in atributes:
        _addCellsToRow(
            tableRows[-1],
            att
        )
    #now its time to process the characters
    for char in characters:
        #make a row for this character and fill his name in
        tableRows.append(
            _easyAddRowsWithCells(
                table,
                grid_row_style,
                characters[char].name
            )
        )
        #Fill in the stats
        for atribute in atributes:
            #get the stat
            if not characters[char].secret:
                insert=characters[char].statPoints[atribute]
            else:
                insert=0
            
            if insert == 0:
                #if insert ==0 it will become "" in the excelsheet. This prevents that from happening
                insert="0"
            #add the stat
            _addCellsToRow(
                tableRows[-1],
                insert
            )
    #its time to save it. Look if a path was given, if not generate one
    if not path:
        path = "./generated/"+_randomStringGen()+".ods"
    doc.save(path)
    #return the path, that way the caller knows where the file can be accessed
    return path




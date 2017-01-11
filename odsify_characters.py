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
    return new_style

def _createAndAddElement(container,func,**args):
    newElement = func(**args)
    container.addElement(newElement)
    return newElement

def _easyAddRowsWithCells(table,rowStyle,textCell1,textCell2):
    tr = _createAndAddElement(table,TableRow,stylename=rowStyle)
    _addCellsToRow(tr,textCell1,textCell2)
    return tr

def _addCellsToRow(tr,textCell1,textCell2,addEmpty=False):
    if addEmpty:
        _createAndAddElement(tr,TableCell,valuetype="string").addElement(P(text=""))
    _createAndAddElement(tr,TableCell,valuetype="string").addElement(P(text=textCell1))
    _createAndAddElement(tr,TableCell,valuetype="string").addElement(P(text=textCell2))

def _randomStringGen(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

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
    tableRows.append(
        _easyAddRowsWithCells(
            table,
            grid_row_style,
            "character",
            ""
        )
    )
    _addCellsToRow(tableRows[-1],"character","",True)
    tableRows.append(
        _easyAddRowsWithCells(
            table,
            grid_row_style,
            "",
            ""
        )
    )
    #used to more easily loop over the attributes
    atributes = ["HP","ACC","EVA","ATK","DEF","SPD"]
    secondLine =False
    #we want to get all the keys so we can easily loop over them.
    #However, because of how it is returned we need to do some extra processing :(
    keys = characters.keys()
    #we need the normal array so we can process 2 characters at the same time
    #this is because we need to know the next key
    #neither an dictonary nor the list you get from .keys() can do that easily
    keyList=[]
    for key in keys:
        keyList.append(key)
    for key in range(0,len(keyList),2):
        tableRows.append(
            _easyAddRowsWithCells(
                table,grid_row_style,
                "name",
                characters[keyList[key]].name
            )
        )
        nextKey=key+1
        extraCharacter = len(keyList)>nextKey
        if extraCharacter:
            _addCellsToRow(
                tableRows[-1],
                "name",
                characters[keyList[nextKey]].name,
                True
            )
        for atribute in atributes:
            insert=characters[keyList[key]].statPoints[atribute]
            if insert == 0:
                #if insert ==0 it will become "" in the excelsheet. This hopefully prevents that from happening
                insert="0"
            tableRows.append(_easyAddRowsWithCells(table,grid_row_style,atribute,insert))
            if extraCharacter:
                insert=characters[keyList[nextKey]].statPoints[atribute]
                if insert == 0:
                    #if insert ==0 it will become "" in the excelsheet. This hopefully prevents that from happening
                    insert="0"
                _addCellsToRow(
                    tableRows[-1],
                    atribute,
                    insert,
                    True
                )
        tableRows.append(
            _easyAddRowsWithCells(
                table,
                grid_row_style,
                "",
                ""
            )
        )
    if not path:
        path = "./generated/"+_randomStringGen()+".ods"
    doc.save(path)
    return path




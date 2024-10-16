import ezsheets

# Create a new Google Sheet
# have to fees data in the sheet
# create new sub sheet
# ss.createSheet("Avengers", 0)


def createSheet(ss, sheetName, index):
    # ss = ezsheets.Spreadsheet("1msIP_wHbNChSufxd3jp9YzGiK66VMlQkEqRzP4cMcs4")

    ss.createSheet(sheetName, index)
    ss.refresh()


def insertData(sheetName, data: list[list[str]]):
    print("Inserting data")
    ss = ezsheets.Spreadsheet("1msIP_wHbNChSufxd3jp9YzGiK66VMlQkEqRzP4cMcs4")
    try:
        print(f"Trying to create sheet {sheetName}")
        createSheet(ss, sheetName, 0)
    except:
        print(f"Sheet {sheetName} already exists")
        pass
    sheet = ss[sheetName]
    for i, j in enumerate(data):
        print(f"Updating row {i + 1}")
        sheet.updateRow(i + 1, j)
    print("Data updated")
    ss.refresh()

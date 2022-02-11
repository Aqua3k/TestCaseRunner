HTMLLinkStr = '<a href="{path}" target="_blank" rel="noopener noreferrer">{string}</a><br>'

cssLink1   = '<link rel="stylesheet" href="https://newcss.net/new.min.css">'
cssLink2   = '<link rel="stylesheet" href="mysrc/SortTable.css">'
scriptLink = '<script type="text/javascript" src="mysrc/Table.js"></script>'

TableHeading     = '<table id="sortTable">{body}</table>'
TableLine        = '<tr>{text}</tr>'
TableCellHeading = '<th cmanSortBtn>{text}</th>'
TableCell        = '<td>{text}</td>'
TableColoredCell = '<td bgcolor={color}>{text}</td>'

HTMLText = '''
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
</head>
<body>
{body}
</body>
</html>
'''

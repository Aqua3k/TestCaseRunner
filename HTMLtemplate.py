HTMLLinkStr = '<a href="{path}">{string}</a><br>'

#後でcssの体裁整えるときのため削除じゃなくてコメントアウト
#cssLink   = '<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/kognise/water.css@latest/dist/light.min.css">'
cssLink    = '<link rel="stylesheet" href="SortTable.css">'
scriptLink = '<script type="text/javascript" src="Table.js"></script>'

TableHeading     = '<table id="sortTable">{body}</table>'
TableLine        = '<tr>{text}</tr>'
TableCellHeading = '<th cmanSortBtn>{text}</th>'
TableCell        = '<td>{text}</td>'
TableColoredCell = '<th bgcolor={color}>{text}</th>'

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

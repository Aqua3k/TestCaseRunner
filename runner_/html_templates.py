html_link_str = '<a href="{path}" target="_blank" rel="noopener noreferrer">{string}</a><br>'

css_link1   = '<link rel="stylesheet" href="https://newcss.net/new.min.css">'
css_link2   = '<link rel="stylesheet" href="../../mysrc/SortTable.css">'
script_link = '<script type="text/javascript" src="../../mysrc/Table.js"></script>'

table_heading     = '<table id="sortTable">{body}</table>'
table_line        = '<tr>{text}</tr>'
table_cell_heading = '<th cmanSortBtn>{text}</th>'
table_cell        = '<td>{text}</td>'
table_colored_cell = '<td bgcolor={color}>{text}</td>'

html_text = '''
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

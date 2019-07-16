import types

def print_table(log, table_list, headers=None):
    if isinstance(table_list, types.GeneratorType):
        table_list = list(table_list)

    if table_list is None or len(table_list) == 0:
        return

    col_list = headers
    if not col_list:
        col_list = list(table_list[0].keys() if table_list else [])
    row_list = [col_list]  # 1st row = header
    for item in table_list:
        row_list.append([str(item.get(col) or '') for col in col_list])
    # maximun size of the col for each element
    col_size = [max(map(len, col)) for col in zip(*row_list)]
    # insert seperating line before every line, and extra one for ending.
    for i in range(0, len(row_list) + 1)[::-1]:
        row_list.insert(i, ['-' * i for i in col_size])
    # two format for each content line and each seperating line
    format_str = ' | '.join(["{{:<{}}}".format(i) for i in col_size])
    format_sep = '-+-'.join(["{{:<{}}}".format(i) for i in col_size])
    for item in row_list:
        if item[0][0] == '-':
            log(format_sep.format(*item))
        else:
            log(format_str.format(*item))

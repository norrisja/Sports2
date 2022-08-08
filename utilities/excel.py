import os.path
import pandas as pd
from pathlib import Path
import re
import string
from xlsxwriter.utility import xl_col_to_name
import xlwings as xw
from xlwings import constants
from utilities import excel_defaults


def build_value_range(start_row, val_col_idx, num_games):
    """ Builds a string containing the ranges of the cells containing the predicted value so that we can conditionally format them."""

    excel_col = xl_col_to_name(val_col_idx + 2)

    xl_range = ''
    row = int(start_row)
    for _ in range(num_games):
        xl_range += f'{excel_col}{str(row+1)}:{excel_col}{str(row+2)},'
        row += 5

    return xl_range.rstrip(',')

class TableRange:
    """ Helper class used to manage the specific sections of a table. """
    def __init__(self, range):
        self.range = range

    def add_formatting(self, **formatting_properties):
        """ Check the formatting properties dictionary to set the formatting properties for this table section. """

        formatting_properties = {k.lower(): v for k,v in formatting_properties.items()}

        self.bold = formatting_properties.get('bold', excel_defaults.bold)
        self.italics = formatting_properties.get('italics', excel_defaults.italics)
        self.color = formatting_properties.get('color', excel_defaults.color)
        self.conditional_format = formatting_properties.get('conditional_format', None)


    def __repr__(self):
        return self.range

    def __str__(self):
        return str(self.range)

class Table:
    """ Class used to convert a pandas dataframe into an excel table """
    def __init__(self, df: pd.DataFrame, starting_cell: str='A1', headers: bool=True, index: bool=True):
        # Convert dataframes to excel values
        self.df = df
        self.starting_cell = starting_cell
        self.headers = headers
        self.index = index

        self._formatting = []

        self._get_table_properties()

    def __get_table_size(self):
        """ Get the size of the dataframe. Add 1 to num rows if
            there's a header and 1 to num cols if there's an index. """

        rows, columns = self.df.shape

        self.num_rows = rows + self.headers
        self.num_cols = columns + self.index

    @staticmethod
    def __col2num(col: str):
        num = 0
        for c in col:
            if c in string.ascii_letters:
                num = num * 26 + (ord(c.upper()) - ord('A'))
        return num

    def __offset_col(self, col: str, offset: int):
        return xl_col_to_name(Table.__col2num(col) + offset)

    def __offset_row(self, row: str, offset: int):
        return str(int(row) + offset)

    def __get_first_column(self):
        self.FC = re.findall(r'[A-Za-z]+|\d+', self.starting_cell)[0]

    def __get_first_row(self):
        self.FR = int(re.findall(r'[A-Za-z]+|\d+', self.starting_cell)[1])

    def __get_last_column(self):
        self.LC = xl_col_to_name(Table.__col2num(self.FC) + self.num_cols - 1)

    def __get_last_row(self):
        self.LR = self.FR + self.num_rows - 1

    def __get_TLC(self):
        """ Get the top left cell excel value """
        self.TLC = self.FC + str(self.FR)
        if self.TLC != self.starting_cell:
            print('WARNING! TOP RIGHT CELL DOES NOT EQUAL THE STARTING CELL!')

    def __get_TRC(self):
        """ Get the top right cell excel value """
        self.TRC = self.LC + str(self.FR)

    def __get_BLC(self):
        """ Get the bottom left cell excel value """
        self.BLC = self.FC + str(self.LR)

    def __get_BRC(self):
        """ Get the bottom right cell excel value """
        self.BRC = self.LC + str(self.LR)

    def __get_TLDC(self):
        """ Get the top left data cell. This is upper-left most cell that is not an index or header. """
        if not self.index and not self.headers:
            self.TLDC = self.TRC
        elif self.index and not self.headers:
            self.TLDC = self.__offset_col(self.FC, 1) + self.FR
        elif not self.index and self.headers:
            self.TLDC = self.FC + self.__offset_row(self.FR, 1)
        else:
            self.TLDC = self.__offset_col(self.FC, 1) + self.__offset_row(self.FR, 1)

    def __get_header_range(self):
        if self.headers:
            self.HeaderRange = ':'.join([self.TLC, self.TRC])
        else:
            self.HeaderRange = None

        self.HeaderRange = TableRange(self.HeaderRange)

    def __get_index_range(self):
        if self.index:
            self.IndexRange = ':'.join([self.TLC, self.BRC])
        else:
            self.IndexRange = None

        self.IndexRange = TableRange(self.IndexRange)

    def __get_data_range(self):
        self.DataRange = ':'.join([self.TLDC, self.BRC])
        self.DataRange = TableRange(self.DataRange)

    def __get_table_range(self):
        self.TableRange = ':'.join([self.TLC, self.BRC])
        self.TableRange = TableRange(self.TableRange)

    def _get_table_properties(self):
        self.__get_table_size()
        self.__get_first_column()
        self.__get_first_row()
        self.__get_last_column()
        self.__get_last_row()

        self.__get_TLC()
        self.__get_TRC()
        self.__get_BLC()
        self.__get_BRC()
        self.__get_TLDC()

        self.__get_index_range()
        self.__get_header_range()
        self.__get_data_range()
        self.__get_table_range()

    def add_formatting_properties(self, range, kwargs):

        range = {'indexrange': self.IndexRange,
                 'headerrange': self.HeaderRange,
                 'datarange': self.DataRange,
                 'tablerange': self.TableRange}.get(range.lower(), range)

        self._formatting.append(TableSectionFormatting(range, **kwargs))

class TableSectionFormatting:
    """ Class used to define and store formatting properties for a specific range """
    def __init__(self, table_range, **kwargs):
        self.table_range = table_range

        self.bold = kwargs.get('bold', excel_defaults.bold)
        self.italics = kwargs.get('italics', excel_defaults.italics)
        self.color = kwargs.get('color', excel_defaults.color)

class Formatter:
    def __init__(self, sheet: xw.Sheet, table: Table):
        self.sheet = sheet
        self.table = table

        # self.section_formatting = section_formatting
        # self.section_range = sheet.range(section_formatting.range)

    @staticmethod
    def __rgb2int(rgb):
        colorInt = rgb[0] + (rgb[1] * 256) + (rgb[2] * 256 * 256)
        return colorInt

    def _set_text_bold(self, range, bold):
        self.sheet.range(range).font.bold = bold

    def _set_text_italics(self, range, italics):
        self.sheet.range(range).font.italics = italics

    def _set_cell_color(self, range, color):
        if isinstance(color, tuple):
            cell_color = color
        if isinstance(color, str):
            # convert string to rgb value
            pass
        self.sheet.range(range).api.Interior.Color = Formatter.__rgb2int(cell_color)


    def _set_text_font(self):
        pass

    def _set_text_color(self):
        pass

    def _set_border(self):
        self.__set_border_color()

    def __set_border_color(self):
        pass





    def apply_formatting(self):

        for section_formatting in self.table._formatting:

            if isinstance(section_formatting.table_range, str):
                range = section_formatting.table_range
            elif isinstance(section_formatting.table_range, TableRange):
                range = section_formatting.table_range.range


            self._set_text_bold(range, section_formatting.bold)
            self._set_text_italics(range, section_formatting.italics)
            if section_formatting.color is not None:
                self._set_cell_color(range, section_formatting.color)

            # if section_formatting.conditional_format is not None:
            #     self.__set_conditional_formatting_databar(range, **section_formatting.conditional_format)
            # self._set_cell_color(section)

    # Take in the desired formatting elements
    # Apply them to the corresponding table ranges

class Writer:
    def __init__(self, filename, subfolder=None, existing=False):
        # Write tables onto sheets
        self.subfolder = subfolder if subfolder is not None else ''
        self.filename = filename

        self.path = os.path.join(f"C:\\Users\\norri\\PycharmProjects\\Sports2\\data\\output\\{self.subfolder}",
                                     self.filename)

        # self.app = xw.App(visible=False)
        # self.wb = self.app.books.active
        # self.app.books.active.name = filename
        self.num_sheets = 1

    def _new_sheet(self, wb, sheetname):
        return wb.sheets.add(sheetname)

    def _update_num_sheets(self, add=1):
        self.num_sheets += add

    def __get_sheet_by_name(self, wb, sheetname):

        sheets = [sheet.name for sheet in wb.sheets]

        if sheetname not in sheets:
            self._new_sheet(wb, sheetname)

        return wb.sheets[sheetname]

    def _get_active_sheet(self, wb):
        return wb.sheets.active

    def write_df(self, df: pd.DataFrame, sheetname: str=None, starting_cell: str='A1', headers: bool=True, index: bool=True, formatting_dict: dict=dict()):

        try:

            with xw.App(visible=False) as app:

                if Path(self.path).is_file():
                    wb = app.books.open(self.path)
                else:
                    wb = app.books.active

                table = Table(df=df, starting_cell=starting_cell, headers=headers, index=index)

                if sheetname is None:
                    sheet = self._get_active_sheet(wb)
                else:
                    sheet = self.__get_sheet_by_name(wb, sheetname)

                sheet.range(starting_cell).options(convert=pd.DataFrame, header=headers, index=index).value = df

                if formatting_dict.keys() is not None:
                    for range in formatting_dict.keys():
                        table.add_formatting_properties(range, formatting_dict.get(range, None))

                f = Formatter(sheet, table)
                f.apply_formatting()


                app.books.active.save(os.path.join(f"C:\\Users\\norri\\PycharmProjects\\Sports2\\data\\output\\{self.subfolder}", self.filename))
                app.quit()

        except Exception:
            app.kill()

class SheetFormatter:
    def __init__(self, path, bookname: str, sheetname: str, range=None, **kwargs):
        self.path = path
        self.bookname = bookname
        self.sheetname = sheetname
        self.range = range
        self.conditional_format = kwargs.get('conditional_format', None)

    def __set_conditional_formatting_databar(self, selection, **conditional_formatting: dict()):
        # """ based on cell value """
        # format_style: style of conditional formatting - 2 or 3 color scale, data bar
        # rule - percentile, min-max, above-below
        # ordered color scale
        # number of conditions - could be derived from number of colors


        selection.api.FormatConditions.AddDatabar()
        selection.api.FormatConditions(selection.api.FormatConditions.Count).ShowValue = True
        selection.api.FormatConditions(selection.api.FormatConditions.Count).SetLastPriority



        selection.api.FormatConditions(1).BarFillType = constants.DataBarFillType.xlDataBarFillGradient
        selection.api.FormatConditions(1).BarBorder.Type = constants.DataBarBorderType.xlDataBarBorderSolid
        selection.api.FormatConditions(1).BarColor.Color = 8700771
        selection.api.FormatConditions(1).BarBorder.Color.Color = 8700771

        selection.api.FormatConditions(1).NegativeBarFormat.ColorType = constants.DataBarNegativeColorType.xlDataBarColor
        selection.api.FormatConditions(1).NegativeBarFormat.BorderColorType = constants.DataBarNegativeColorType.xlDataBarColor
        selection.api.FormatConditions(1).NegativeBarFormat.Color.Color = constants.RgbColor.rgbRed
        selection.api.FormatConditions(1).NegativeBarFormat.BorderColor.Color = constants.RgbColor.rgbRed

        selection.api.FormatConditions(1).AxisPosition = constants.DataBarAxisPosition.xlDataBarAxisAutomatic
        selection.api.FormatConditions(1).Direction = constants.Constants.xlContext

        # selection.api.FormatConditions(1).MinPoint.Value = constants.ConditionValueTypes.xlConditionValueAutomaticMin
        # selection.api.FormatConditions(1).MaxPoint.Value = constants.ConditionValueTypes.xlConditionValueAutomaticax
        # print('test')
        #
        # csc_pos = selection.api.FormatConditions(1).BarColor(1)
        # csc_pos.Color = 8700771
        # csc_pos.TintAndShade = 0
        # print('test')
        #
        # csc_neg = selection.api.FormatConditions(1).NegativeBarFormat(1)
        # csc_neg.Color = 255
        # csc_neg.TintAndShade = 0
        # print('test')

    def apply_sheet_formatting(self):

        try:

            with xw.App() as app:

                # sheet = app.books.open(self.bookname].sheets[self.sheetname]
                if Path(self.path).is_file():
                    wb = app.books.open(self.path)
                else:
                    wb = app.books.active

                sheet = wb.sheets[self.sheetname]

                if self.conditional_format is not None:
                    if self.range is None:
                        print('Must provide range for conditional formatting')
                        raise KeyError
                    selection = sheet.range(self.range)
                    self.__set_conditional_formatting_databar(selection, **self.conditional_format)

                app.books.active.save(self.path)
                app.quit()

        except Exception:
            app.kill()


if __name__ == '__main__':

    t = Table(df=pd.DataFrame({'1': [1, 2],
                               '2': [2, 4],
                               '3': [4, 8]}),
              index=False,
              headers=True)

    print(t.TLC)
    print(t.BRC)
    print(t.TLDC)
    print(t.DataRange)

    df = df = pd.DataFrame({'1': [1, 2],
                            '2': [2, 4],
                            '3': [4, 8]})

    w = Writer('testing2.xlsx')
    w.write_df(df, 'A1', headers=True, index=False)
    w.close()



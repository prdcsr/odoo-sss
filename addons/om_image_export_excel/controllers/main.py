import base64
import io

from odoo.addons.web.controllers.main import ExportXlsxWriter, ExcelExport
from odoo.tools import pycompat
from PIL import Image


class ExportExcelImage(ExcelExport):

    def from_data(self, fields, rows):
        with ExportXlsxWriter(fields, len(rows)) as xlsx_writer:
            for row_index, row in enumerate(rows):
                for cell_index, cell_value in enumerate(row):
                    if isinstance(cell_value, (list, tuple)):
                        cell_value = pycompat.to_text(cell_value)
                    # If we get binary data in export then go to this if condition.
                    if isinstance(cell_value, bytes):
                        xlsx_writer.worksheet.set_row(row_index + 1, 80)

                        # Change the row height
                        row_pixel = xlsx_writer.worksheet.default_row_pixels
                        total_image_height_width = row_pixel * 4

                        # Resize the Image
                        image = Image.open(io.BytesIO(base64.b64decode(cell_value)))
                        image_width = image.width
                        image_height = image.height
                        new_image_size = (300, 300)
                        image.resize(new_image_size)

                        x_scale = total_image_height_width / image_width
                        y_scale = total_image_height_width / image_height

                        # Insert Image into Excel
                        xlsx_writer.worksheet.insert_image(row_index + 1,
                                                           cell_index,
                                                           'export-excel-image.png',
                                                           {
                                                               'image_data': io.BytesIO(base64.b64decode(cell_value)),
                                                               'x_scale': x_scale,
                                                               'y_scale': y_scale
                                                           }
                                                           )
                    else:
                        xlsx_writer.write_cell(row_index + 1, cell_index, cell_value)

        return xlsx_writer.value

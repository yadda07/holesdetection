import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, QProgressBar
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon

class ShapefileProcessorThread(QThread):
    progress_update = pyqtSignal(int)

    def __init__(self, shape_path, output_dir):
        super().__init__()
        self.shape_path = shape_path
        self.output_dir = output_dir

    def run(self):
        def has_holes(geom):
            if geom is None:
                return False
            if isinstance(geom, Polygon):
                return len(geom.interiors) > 0
            elif isinstance(geom, MultiPolygon):
                return any(len(poly.interiors) > 0 for poly in geom.geoms)
            return False

        print('Reading Shapefile...')
        gdf = gpd.read_file(self.shape_path)

        print('Selecting geometries with holes...')
        gdf_holes = gdf[gdf.geometry.apply(has_holes)]

        output_path = os.path.join(self.output_dir, 'ZAPM_XP-FIBRE_with_holes.shp')
        print('Saving to new shapefile...')
        gdf_holes.to_file(output_path)
        print('Done.')

class ShapefileProcessor(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Shapefile Processor')

        QApplication.setStyle("Fusion")

        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        QApplication.setPalette(dark_palette)

        self.label_shape = QLabel('Choisir le fichier Shape :')
        self.button_select_shape = QPushButton('Parcourir...')
        self.button_select_shape.clicked.connect(self.select_shape)

        self.label_output_dir = QLabel('Choisir le répertoire de dépôt :')
        self.button_select_output_dir = QPushButton('Parcourir...')
        self.button_select_output_dir.clicked.connect(self.select_output_dir)

        self.button_process = QPushButton('Traiter')
        self.button_process.clicked.connect(self.process_shapefile)

        self.progress_bar = QProgressBar()

        layout = QVBoxLayout()
        layout.addWidget(self.label_shape)
        layout.addWidget(self.button_select_shape)
        layout.addWidget(self.label_output_dir)
        layout.addWidget(self.button_select_output_dir)
        layout.addWidget(self.button_process)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

    def select_shape(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, 'Choisir le fichier Shape', '', 'Shapefiles (*.shp);;All Files (*)', options=options)
        self.shape_path = file_name

    def select_output_dir(self):
        options = QFileDialog.Options()
        folder_path = QFileDialog.getExistingDirectory(self, 'Choisir le répertoire de dépôt', options=options)
        self.output_dir = folder_path

    def process_shapefile(self):
        if not hasattr(self, 'shape_path') or not hasattr(self, 'output_dir'):
            return

        self.button_process.setEnabled(False)

        self.worker_thread = ShapefileProcessorThread(self.shape_path, self.output_dir)
        self.worker_thread.progress_update.connect(self.update_progress)
        self.worker_thread.finished.connect(self.processing_finished)
        self.worker_thread.start()

    def update_progress(self, progress):
        self.progress_bar.setValue(progress)

    def processing_finished(self):
        self.button_process.setEnabled(True)
        self.progress_bar.setValue(0)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ShapefileProcessor()
    window.show()
    sys.exit(app.exec_())

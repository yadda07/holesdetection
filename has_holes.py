import os
import sys

import geopandas as gpd
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from shapely.geometry import MultiPolygon, Polygon


def _geometry_has_holes(geom) -> bool:
    if geom is None:
        return False
    if isinstance(geom, Polygon):
        return len(geom.interiors) > 0
    if isinstance(geom, MultiPolygon):
        return any(len(poly.interiors) > 0 for poly in geom.geoms)
    return False


class ShapefileProcessorThread(QThread):
    progress_update = pyqtSignal(int)
    error_occurred = pyqtSignal(str)

    def __init__(self, shape_path: str, output_dir: str):
        super().__init__()
        self.shape_path = shape_path
        self.output_dir = output_dir

    def run(self):
        try:
            self.progress_update.emit(20)
            gdf = gpd.read_file(self.shape_path)
            self.progress_update.emit(60)
            gdf_holes = gdf[gdf.geometry.apply(_geometry_has_holes)]
            if gdf_holes.empty:
                self.progress_update.emit(100)
                return
            out_path = os.path.join(self.output_dir, 'sample_zones_with_holes.shp')
            gdf_holes.to_file(out_path)
            self.progress_update.emit(100)
        except Exception as exc:
            self.error_occurred.emit(
                f"has_holes: export failed for '{self.shape_path}': {exc}"
            )


class ShapefileProcessor(QWidget):
    def __init__(self):
        super().__init__()
        self.shape_path = ''
        self.output_dir = ''
        self.worker_thread = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Shapefile Processor')
        QApplication.setStyle('Fusion')

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

        self.label_output_dir = QLabel('Choisir le repertoire de depot :')
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
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            'Choisir le fichier Shape',
            '',
            'Shapefiles (*.shp);;All Files (*)',
        )
        if file_name:
            self.shape_path = file_name

    def select_output_dir(self):
        folder_path = QFileDialog.getExistingDirectory(
            self,
            'Choisir le repertoire de depot',
        )
        if folder_path:
            self.output_dir = folder_path

    def process_shapefile(self):
        if not self.shape_path or not self.output_dir:
            return

        self.button_process.setEnabled(False)
        self.worker_thread = ShapefileProcessorThread(
            self.shape_path,
            self.output_dir,
        )
        self.worker_thread.progress_update.connect(self.update_progress)
        self.worker_thread.error_occurred.connect(self.on_error)
        self.worker_thread.finished.connect(self.processing_finished)
        self.worker_thread.start()

    def update_progress(self, progress: int):
        self.progress_bar.setValue(progress)

    def on_error(self, message: str):
        QMessageBox.critical(self, 'Erreur', message)

    def processing_finished(self):
        self.button_process.setEnabled(True)
        self.progress_bar.setValue(0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ShapefileProcessor()
    window.show()
    sys.exit(app.exec_())
